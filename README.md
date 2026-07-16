<a id="readme-top"></a>

<!-- PROJECT SHIELDS -->

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Firebase](https://img.shields.io/badge/Firebase-Realtime%20Database-FFCA28?style=for-the-badge&logo=firebase&logoColor=black)](https://firebase.google.com/)
[![Google Vision AI](https://img.shields.io/badge/Google-Vision%20AI-4285F4?style=for-the-badge&logo=googlecloud&logoColor=white)](https://cloud.google.com/vision)
[![Raspberry Pi](https://img.shields.io/badge/Raspberry%20Pi-Edge%20Computing-C51A4A?style=for-the-badge&logo=raspberrypi&logoColor=white)](https://www.raspberrypi.com/)

<br>

<div align="center">

# Lecture-to-Document System

### Raspberry Pi Image Acquisition and Cloud-Based OCR System

An end-to-end edge-to-cloud document digitization system that captures lecture materials using Raspberry Pi, performs cloud-based Optical Character Recognition (OCR), and generates editable DOCX and PDF documents through a FastAPI backend.

</div>

---

## Table of Contents

- About The Project
- Features
- System Architecture
- Workflow
- Technologies
- Project Structure
- Installation
- Configuration
- Running the System
- API Endpoints
- Design Highlights
- Future Improvements
- Author

---

# About The Project

The **Lecture-to-Document System** is an edge-to-cloud document digitization platform developed to automate the conversion of classroom lecture materials into editable digital documents.

Using a Raspberry Pi equipped with a Camera Module 3, the system captures lecture boards, handwritten notes, or presentation slides, performs lightweight image preprocessing on the edge device, uploads images to a FastAPI backend, extracts text using Google Vision AI with PyTesseract fallback OCR, and exports professional DOCX and PDF documents.

The project demonstrates distributed computing, computer vision, cloud services, and backend engineering through a modular architecture suitable for educational environments.

---

# Features

## Raspberry Pi Edge Processing

- Automatic image capture
- Camera Module 3 integration
- Lightweight OpenCV preprocessing
- Remote backend-controlled operation
- Batch image uploading
- Graceful shutdown handling

## Cloud Backend

- FastAPI REST API
- Google Vision AI OCR
- PyTesseract fallback OCR
- Firebase Realtime Database integration
- Device heartbeat monitoring
- Multi-device management

## Document Generation

- OCR text preview
- Editable extracted text
- DOCX export
- PDF export
- Professional document formatting

---

# System Architecture

```text
                 Raspberry Pi
              Camera Module 3
                     │
                     ▼
           Image Acquisition
                     │
                     ▼
          OpenCV Preprocessing
                     │
                     ▼
            Batch Image Upload
                     │
                     ▼
          FastAPI REST Backend
                     │
      ┌──────────────┼──────────────┐
      ▼              ▼              ▼
Firebase      Google Vision AI   PyTesseract
Realtime DB      (Primary OCR)   (Fallback OCR)
      │              │
      └───────┬──────┘
              ▼
      OCR Text Extraction
              │
              ▼
      Text Preview & Editing
              │
              ▼
      DOCX / PDF Generation
```

---

# Workflow

1. Raspberry Pi powers on and starts automatically.
2. Backend controls device state through Firebase.
3. Raspberry Pi captures lecture images.
4. Images are preprocessed locally using OpenCV.
5. Images are uploaded in batches.
6. FastAPI performs OCR using Google Vision AI.
7. PyTesseract acts as fallback OCR.
8. Users preview and edit extracted text.
9. Documents are generated as DOCX or PDF.

---

# Technologies

## Hardware

- Raspberry Pi 4
- Raspberry Pi Camera Module 3

## Backend

- FastAPI
- Uvicorn

## Computer Vision

- OpenCV
- Pillow

## OCR

- Google Vision AI
- PyTesseract

## Database

- Firebase Realtime Database

## Document Generation

- python-docx
- FPDF

## Cloud Deployment

- Render

## Utilities

- Requests
- Threading
- Subprocess
- Python Logging

---

# Project Structure

```text
lecture-to-document/

├── backend/
│   ├── main.py
│   ├── firebase.py
│   ├── vision.py
│   ├── document_generator.py
│   └── utils.py
│
├── raspberry_pi/
│   ├── capture.py
│   ├── preprocess.py
│   ├── upload.py
│   └── heartbeat.py
│
├── uploads/
├── outputs/
├── requirements.txt
├── README.md
└── .env
```

---

# Installation

Clone the repository

```bash
git clone https://github.com/yourusername/lecture-to-document.git
```

```bash
cd lecture-to-document
```

Create a virtual environment

```bash
python -m venv .venv
```

Activate

**Windows**

```bash
.venv\Scripts\activate
```

**Linux/macOS**

```bash
source .venv/bin/activate
```

Install dependencies

```bash
pip install -r requirements.txt
```

---

# Configuration

Create a `.env` file.

```env
GOOGLE_APPLICATION_CREDENTIALS=

FIREBASE_CREDENTIALS=

FIREBASE_DB_URL=

UPLOAD_DIR=

OUTPUT_DIR=

TESSERACT_CMD=
```

---

# Running the System

## Start FastAPI

```bash
uvicorn main:app --reload
```

---

## Raspberry Pi

The Raspberry Pi is configured as a system service.

Once powered on, it will:

- Connect to Wi-Fi
- Start automatically
- Send heartbeat signals
- Wait for backend commands
- Capture images automatically
- Upload image batches

No manual execution is required.

---

# API Endpoints

| Endpoint | Description |
|----------|-------------|
| POST `/device_id/upload_batch` | Upload image batches |
| POST `/device_id/extract_text` | Extract text using OCR |
| POST `/device_id/generate_docx` | Generate Microsoft Word document |
| POST `/device_id/generate_pdf` | Generate PDF document |
| POST `/device_id/set_status` | Control Raspberry Pi state |
| GET `/device_id/get_status` | Retrieve current device status |
| POST `/device_id/heartbeat` | Update device heartbeat |

---

# Design Highlights

## Edge-to-Cloud Computing

Image preprocessing is executed on the Raspberry Pi while computationally intensive OCR is delegated to the FastAPI cloud backend.

---

## Hybrid OCR Strategy

**Primary OCR**

- Google Vision AI

**Fallback OCR**

- PyTesseract

This architecture combines high OCR accuracy with reliable fallback processing.

---

## Batch Upload Strategy

Instead of transmitting images individually, the Raspberry Pi uploads captured images in batches to reduce:

- Network overhead
- API requests
- Upload latency

---

## Real-Time Device Monitoring

Firebase Realtime Database enables:

- Device heartbeat monitoring
- Remote start, pause, finish, and idle commands
- Online/offline tracking
- Scalable multi-device management

---

## Fault Tolerance

The system includes:

- Automatic OCR fallback
- Graceful shutdown handling
- Retry mechanisms
- Exception handling
- Safe cleanup routines

---

# Future Improvements

- Multi-camera support
- AI handwriting recognition
- Automatic document summarization
- Real-time streaming OCR
- Mobile application
- User authentication and authorization
- Docker deployment
- Kubernetes orchestration

---

# Author

**Ralph Jayrell Gacusan**

Backend Developer • Python Developer • Data & AI Enthusiast

GitHub: https://github.com/ralphgacusan

---

<p align="right">(<a href="#readme-top">back to top</a>)</p>