import os
import time
import requests
import subprocess
from threading import Thread
import cv2
import signal
import sys
from threading import Lock

batch_lock = Lock()

# --- CONFIG ---
CAPTURE_DIR = "/home/admin/captures"
os.makedirs(CAPTURE_DIR, exist_ok=True)

API_URL = "http://192.168.100.209:8000"
DEVICE_ID = "rspi1001"

CHECK_INTERVAL = 1    # check status every 2 seconds
CAPTURE_INTERVAL = 3    # capture every 2 seconds
HEARTBEAT_INTERVAL = 3  # heartbeat every 5 seconds

capture_paused = False
device_connected = False
cap_running = True
batch_uploaded = False  # ensure batch only happens once


# --- CAPTURE IMAGE ---
def capture_image(filepath):
    try:
        # Capture original image
        subprocess.run(["rpicam-still", "-o", filepath, "-n"], check=True)
        print(f"[DEBUG] Image saved: {filepath}")

        # Preprocess image (lightly)
        preprocess_image(filepath)

        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Failed to capture image: {e}")
        return False

# --- LIGHT PREPROCESSING FUNCTION ---
def preprocess_image(filepath):
    """Load an image, convert to grayscale, resize lightly, and save."""
    try:
        img = cv2.imread(filepath)
        if img is None:
            print(f"[ERROR] Failed to read image for preprocessing: {filepath}")
            return False

        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Optional: resize to width=640 (keep aspect ratio)
        width = 640
        height = int(gray.shape[0] * (width / gray.shape[1]))
        resized = cv2.resize(gray, (width, height))

        # Save preprocessed image (overwrite original)
        cv2.imwrite(filepath, resized)
        print(f"[DEBUG] Preprocessed image saved: {filepath}")
        return True

    except Exception as e:
        print(f"[ERROR] Preprocessing failed: {e}")
        return False

# --- BATCH UPLOAD ---
def batch_upload_images():
    images = sorted([f for f in os.listdir(CAPTURE_DIR) if f.lower().endswith(".jpg")])
    if not images:
        print("[INFO] No images to upload.")
        return

    print(f"[DEBUG] Starting batch upload of {len(images)} images...")

    # Open files using 'with' to ensure proper closure
    files_payload = []
    open_files = []

    try:
        for img_name in images:
            file_path = os.path.join(CAPTURE_DIR, img_name)
            f = open(file_path, "rb")
            open_files.append(f)  # keep reference so they don't get GC'd
            files_payload.append(("files", (img_name, f, "image/jpeg")))

        response = requests.post(
            f"{API_URL}/{DEVICE_ID}/upload_batch",
            files=files_payload,
            timeout=60
        )

        if response.ok:
            print("[SUCCESS] Batch upload completed!")
            print("[DEBUG] Server response:", response.json())
            
            # set idle AFTER upload completes
            set_status_idle()
            # Optional: delete uploaded files
            for f in open_files:
                f.close()  # make sure files are closed before deletion
            for img_name in images:
                file_path = os.path.join(CAPTURE_DIR, img_name)
                os.remove(file_path)
                print(f"[INFO] Deleted {img_name}")

        else:
            print(f"[ERROR] Batch upload failed: {response.status_code}")
            print("[DEBUG] Response:", response.text)

    except Exception as e:
        print(f"[ERROR] Batch upload exception: {e}")

    finally:
        # Ensure all files are closed even if exception occurs
        for f in open_files:
            f.close()

# --- STATUS CHECK ---
def check_status():
    global capture_paused, device_connected, batch_uploaded
    try:
        response = requests.get(f"{API_URL}/{DEVICE_ID}/get_status", timeout=5)
        if response.ok:
            data = response.json()
            status = data.get("status", "idle")

            if status == "start":
                capture_paused = False

                # RESET for new session
                with batch_lock:
                    if batch_uploaded:
                        print("[DEBUG] New session detected → resetting batch_uploaded")
                        batch_uploaded = False

            elif status == "pause":
                capture_paused = True

            elif status == "finish":
                capture_paused = False

                with batch_lock:
                    if not batch_uploaded:
                        print("[DEBUG] Triggering batch upload...")
                        batch_uploaded = True
                        Thread(target=batch_upload_images, daemon=True).start()

            return status

        else:
            print(f"[ERROR] Status HTTP error: {response.status_code}")

    except Exception as e:
        print(f"[ERROR] Status exception: {e}")

    return "idle"

# --- HEARTBEAT ---
def heartbeat_loop():
    global device_connected
    while cap_running:
        try:
            response = requests.post(f"{API_URL}/{DEVICE_ID}/heartbeat", timeout=5)
            
            # Check HTTP status first
            print(f"[DEBUG] Heartbeat HTTP status: {response.status_code}")  # for debugging

            if response.ok:
                try:
                    data = response.json()
                    # Fallback: default to True if server doesn't send 'connected'
                    device_connected = data.get("connected", True)
                    print(f"[DEBUG] Heartbeat JSON connected: {device_connected}")
                except Exception as e:
                    print(f"[WARNING] Heartbeat JSON parse failed: {e}")
                    device_connected = True  # fallback to True
            else:
                print(f"[WARNING] Heartbeat returned non-OK status {response.status_code}")
                device_connected = True  # fallback to True

        except Exception as e:
            print(f"[ERROR] Heartbeat exception: {e}")
            device_connected = False  # only set False on real exceptions

        time.sleep(HEARTBEAT_INTERVAL)

# --- CAPTURE LOOP ---
def capture_loop():
    global cap_running, batch_uploaded
    last_capture = 0

    while cap_running:
        status = check_status()
        current_time = time.time()

        if not capture_paused and status == "start" and (current_time - last_capture >= CAPTURE_INTERVAL):
            filename = os.path.join(CAPTURE_DIR, f"capture_{int(current_time)}.jpg")
            print(f"[DEBUG] Capturing image to: {filename}")
            if capture_image(filename):
                last_capture = current_time
            else:
                print("[WARNING] Capture failed, will retry")

        time.sleep(CHECK_INTERVAL)

# --- DELETE ALL UPLOADS ---
def delete_all_uploads():
    """Call backend to delete all uploaded images for this device."""
    try:
        response = requests.delete(f"{API_URL}/{DEVICE_ID}/delete_all_uploads", timeout=10)
        if response.ok:
            data = response.json()
            deleted_count = len(data.get("deleted_files", []))
            print(f"[DEBUG] Deleted {deleted_count} files on backend.")
        else:
            print(f"[ERROR] Failed to delete uploads: HTTP {response.status_code}")
    except Exception as e:
        print(f"[ERROR] Exception while deleting uploads: {e}")


# --- SET STATUS TO IDLE ---
def set_status_idle():
    """Set device status to 'idle' on backend."""
    try:
        response = requests.post(f"{API_URL}/{DEVICE_ID}/set_status", data={"status": "idle"}, timeout=5)
        if response.ok:
            print("[DEBUG] Status set to 'idle' on backend.")
        else:
            print(f"[ERROR] Failed to set status to idle: HTTP {response.status_code}")
    except Exception as e:
        print(f"[ERROR] Exception while setting status to idle: {e}")


def shutdown_handler(signum, frame):
    global cap_running, batch_uploaded
    print(f"\n[DEBUG] Received shutdown signal: {signum}")

    cap_running = False

    # Upload remaining images if not uploaded yet
    with batch_lock:
        if not batch_uploaded:
            print("[DEBUG] Uploading remaining images before exit...")
            batch_uploaded = True
            batch_upload_images()

    # Delete all images from backend
    print("[DEBUG] Deleting all uploaded images on backend...")
    delete_all_uploads()

    # Set status to idle
    print("[DEBUG] Setting status to 'idle' on backend...")
    set_status_idle()

    print("[DEBUG] Cleanup done. Exiting.")
    return


# --- MAIN ---
if __name__ == "__main__":
    print(f"[DEBUG] Starting device: {DEVICE_ID}")

    signal.signal(signal.SIGTERM, shutdown_handler)
    signal.signal(signal.SIGINT, shutdown_handler)

    heartbeat_thread = Thread(target=heartbeat_loop)
    capture_thread = Thread(target=capture_loop)

    heartbeat_thread.start()
    capture_thread.start()

    while cap_running:
        time.sleep(1)

    heartbeat_thread.join()
    capture_thread.join()

    print("[DEBUG] Program exited cleanly.")

