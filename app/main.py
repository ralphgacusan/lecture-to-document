

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Body, Request
from fastapi.responses import StreamingResponse, JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from PIL import Image, ImageFilter, ImageOps
import pytesseract
from docx import Document
from fpdf import FPDF
import os
from io import BytesIO
import json
from difflib import SequenceMatcher
import time
import cv2
import numpy as np
from app.vision_ocr import extract_text_from_image_bytes
from app.firebase_db import (
    get_device,
    create_device_if_not_exists,
    update_status,
    update_heartbeat,
    check_connection
)
from pathlib import Path

# local
# Configure Tesseract OCR path (change this if running on Raspberry Pi)
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# dev
pytesseract.pytesseract.tesseract_cmd = os.getenv("TESSERACT_CMD", "tesseract")

app = FastAPI(title="Image to DOCX/PDF API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# # Load allowed devices dynamically from devices.json
# ALLOWED_DEVICES = list(load_devices_db().get("devices", {}).keys())

def validate_device(device_id: str):
    create_device_if_not_exists(device_id)


# --- Serve device-specific static files ---
@app.get("/{device_id}/test/{file_path:path}")
async def serve_test_file(device_id: str, file_path: str):
    validate_device(device_id)
    full_path = os.path.join("app", "test", file_path)
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(full_path)

@app.get("/{device_id}/static/{file_path:path}")
async def serve_static_file(device_id: str, file_path: str):
    validate_device(device_id)
    full_path = os.path.join("app", "static", file_path)
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(full_path)

# Output folder
output_folder = os.getenv("OUTPUT_DIR", "output_docs")
os.makedirs(output_folder, exist_ok=True)

# --- Utility functions ---
def is_similar(line1, line2, threshold=0.85):
    return SequenceMatcher(None, line1, line2).ratio() > threshold

# -----------------------------
# OCR Preprocessing Function
# -----------------------------
def ocr_preprocess_image(image: Image.Image) -> Image.Image:
    """
    Preprocessing optimized for classroom whiteboards and handwriting.
    Expects a PIL Image object.
    """
    # Convert to grayscale
    image = image.convert("L")

    # Convert PIL Image to OpenCV array for advanced processing
    img_cv = np.array(image)

    # Apply Gaussian blur to reduce small noise
    img_cv = cv2.GaussianBlur(img_cv, (3, 3), 0)

    # Adaptive thresholding (binarization)
    # This works well for uneven lighting typical of whiteboards
    img_cv = cv2.adaptiveThreshold(
        img_cv,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        11,
        2
    )

    # Morphological operations (optional but helps handwriting)
    kernel = np.ones((2, 2), np.uint8)
    img_cv = cv2.morphologyEx(img_cv, cv2.MORPH_CLOSE, kernel)  # fills small gaps
    img_cv = cv2.medianBlur(img_cv, 3)  # smooth thin lines

    # Resize if too small (Tesseract reads better with bigger text)
    height, width = img_cv.shape
    if height < 500:
        scale = 500 / height
        img_cv = cv2.resize(img_cv, (int(width * scale), 500), interpolation=cv2.INTER_LINEAR)

    # Convert back to PIL Image
    preprocessed_image = Image.fromarray(img_cv)

    # Slight sharpening for OCR
    preprocessed_image = preprocessed_image.filter(ImageFilter.SHARPEN)

    return preprocessed_image

# -----------------------------
#  Extract text from uploaded images (preview)
# -----------------------------
@app.post("/{device_id}/extract_text")
async def extract_text(device_id: str, files: List[UploadFile] = File(...)):
    validate_device(device_id)
    if not files:
        return {"error": "No files uploaded"}

    extracted_lines = []

    for file in files:
        content = await file.read()

        # Use Google Vision OCR
        try:
            text = extract_text_from_image_bytes(content)
        except Exception:
            # Fallback to local Tesseract
            image = Image.open(BytesIO(content))
            image = ocr_preprocess_image(image)
            text = pytesseract.image_to_string(image, config="--oem 1 --psm 6")

        for line in text.splitlines():
            clean_line = line.strip()
            if clean_line and not any(is_similar(clean_line, l) for l in extracted_lines):
                extracted_lines.append(clean_line)

    preview_text = "\n".join(extracted_lines)
    return JSONResponse({"preview_text": preview_text})


# -----------------------------
# Generate DOCX from edited text
# -----------------------------
@app.post("/{device_id}/generate_docx")
async def generate_docx(device_id: str, text: str = Form(...)):
    validate_device(device_id)
    text = text.strip()
    if not text:
        return {"error": "No text provided."}

    doc = Document()
    for line in text.splitlines():
        clean_line = line.strip()
        if clean_line:
            doc.add_paragraph(clean_line)

    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": "attachment; filename=extracted_text.docx"}
    )
    
# -----------------------------
# Generate PDF from edited text (robust version)
# -----------------------------
@app.post("/{device_id}/generate_pdf")
async def generate_pdf(device_id: str, request: Request, text: str = Form(None)):
    try:
        # --- Get text from Form or JSON ---
        if text is None:
            try:
                data = await request.json()
                text = data.get("text", "")
            except:
                text = ""
        text = text.strip()
        if not text:
            return JSONResponse({"error": "No text provided."}, status_code=400)

        # --- Validate device ---
        validate_device(device_id)

        # --- PDF setup ---
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()

        # --- Use absolute path to font relative to this Python file ---
        BASE_DIR = Path(__file__).resolve().parent
        font_path = BASE_DIR / "fonts" / "DejaVuSans.ttf"

        if font_path.exists():
            pdf.add_font("DejaVu", "", str(font_path), uni=True)
            pdf.set_font("DejaVu", size=12)
        else:
            print(f"⚠️ Font not found at {font_path}, using default font")
            pdf.set_font("Arial", size=12)

        # --- Add text line by line ---
        for line in text.splitlines():
            if line.strip():
                pdf.multi_cell(0, 10, line.strip())

        # --- Return PDF ---
        buffer = BytesIO(pdf.output(dest='S').encode('latin1'))
        buffer.seek(0)
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=extracted_text.pdf"}
        )

    except Exception as e:
        print("PDF GENERATION ERROR:", e)
        return JSONResponse({"error": str(e)}, status_code=500)
    
    

# -----------------------------
# Capture status endpoints (devices.json)
# -----------------------------
@app.post("/{device_id}/set_status")
async def set_status(device_id: str, status: str = Form(...)):
    validate_device(device_id)
    if status not in ["idle", "start", "pause", "finish", "delete"]:
        return JSONResponse({"error": "Invalid status"}, status_code=400)

    update_status(device_id, status)


    return JSONResponse({"device_id": device_id, "status": status})

@app.get("/{device_id}/get_status")
async def get_status(device_id: str):
    validate_device(device_id)

    device = get_device(device_id)

    if not device:
        return {"status": "idle", "connected": False}

    device["connected"] = check_connection(device)

    return device

@app.post("/{device_id}/heartbeat")
async def heartbeat(device_id: str):
    """Raspberry Pi sends a heartbeat to mark itself as connected"""
    validate_device(device_id)
    update_heartbeat(device_id)
    return {"device_id": device_id, "connected": True}


# -----------------------------
# Raspberry Pi batch upload endpoints
# -----------------------------

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/{device_id}/upload_batch")
async def upload_batch(device_id: str, files: List[UploadFile] = File(...)):
    """
    Raspberry Pi sends batch of images here.
    Just store them for preview later.
    """
    validate_device(device_id)
    if not files:
        return {"error": "No files uploaded."}

    device_folder = os.path.join(UPLOAD_DIR, device_id)
    os.makedirs(device_folder, exist_ok=True)

    saved_files = []
    for file in files:
        file_path = os.path.join(device_folder, file.filename)
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        saved_files.append(file.filename)

    return JSONResponse({"message": f"{len(saved_files)} files uploaded.", "files": saved_files})


@app.get("/{device_id}/list_uploads")
async def list_uploads(device_id: str):
    """List all uploaded images for frontend preview"""
    validate_device(device_id)
    device_folder = os.path.join(UPLOAD_DIR, device_id)
    if not os.path.exists(device_folder):
        return {"files": []}

    files = sorted(os.listdir(device_folder))
    return {"files": files}


@app.get("/{device_id}/get_upload/{filename}")
async def get_upload(device_id: str, filename: str):
    """Serve specific uploaded image for frontend preview"""
    validate_device(device_id)
    device_folder = os.path.join(UPLOAD_DIR, device_id)
    file_path = os.path.join(device_folder, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path)

@app.delete("/{device_id}/delete_all_uploads")
async def delete_all_uploads(device_id: str):
    """Delete all uploaded images for the specified device"""
    validate_device(device_id)
    
    device_folder = os.path.join(UPLOAD_DIR, device_id)
    if not os.path.exists(device_folder):
        return JSONResponse({"message": "No uploads found to delete."})

    deleted_files = []
    for filename in os.listdir(device_folder):
        file_path = os.path.join(device_folder, filename)
        try:
            os.remove(file_path)
            deleted_files.append(filename)
        except Exception as e:
            print(f"[ERROR] Failed to delete {filename}: {e}")

    return JSONResponse({
        "message": f"Deleted {len(deleted_files)} files.",
        "deleted_files": deleted_files
    })

@app.delete("/{device_id}/delete_uploads")
async def delete_selected_uploads(device_id: str, files: list[str] = Body(...)):
    """Delete specific uploaded images for the device"""
    device_folder = os.path.join(UPLOAD_DIR, device_id)
    if not os.path.exists(device_folder):
        return JSONResponse({"message": "Device folder not found.", "deleted_files": []})

    deleted_files = []
    for filename in files:
        file_path = os.path.join(device_folder, filename)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                deleted_files.append(filename)
            except Exception as e:
                print(f"[ERROR] Failed to delete {filename}: {e}")

    return JSONResponse({
        "message": f"Deleted {len(deleted_files)} file(s).",
        "deleted_files": deleted_files
    })
