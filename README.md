<a id="readme-top"></a>

<!-- PROJECT SHIELDS -->

[![Python][python-shield]][python-url]
[![FastAPI][fastapi-shield]][fastapi-url]
[![Raspberry Pi][raspberrypi-shield]][raspberrypi-url]
[![Firebase][firebase-shield]][firebase-url]
[![Google Cloud Vision][vision-shield]][vision-url]

<!-- PROJECT LOGO -->

<br />
<div align="center">
  <h1 align="center">Lecture-to-Document</h1>

  <p align="center">
    A Raspberry Pi and cloud-based OCR system for converting classroom lecture content into editable digital documents.
    <br />
    <br />
    <a href="#about-the-project">About</a>
    &middot;
    <a href="#getting-started">Getting Started</a>
    &middot;
    <a href="#usage">Usage</a>
  </p>
</div>

---

## Table of Contents

<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
      <ul>
        <li><a href="#system-workflow">System Workflow</a></li>
        <li><a href="#built-with">Built With</a></li>
      </ul>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
        <li><a href="#environment-variables">Environment Variables</a></li>
      </ul>
    </li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#api-endpoints">API Endpoints</a></li>
    <li><a href="#system-architecture">System Architecture</a></li>
    <li><a href="#roadmap">Roadmap</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
    <li><a href="#acknowledgments">Acknowledgments</a></li>
  </ol>
</details>

---

## About The Project

**Lecture-to-Document** is an edge-to-cloud system designed to simplify the process of capturing and digitizing classroom lecture content.

The system uses a **Raspberry Pi with Camera Module 3** to automatically capture images of whiteboards, handwritten notes, and lecture materials. Images are lightly preprocessed on the device before being uploaded to a **FastAPI backend** for Optical Character Recognition (OCR).

The system uses **Google Vision AI** as its primary OCR engine and **PyTesseract** as a fallback. Extracted text can then be reviewed, edited, and converted into **DOCX or PDF documents**.

This reduces manual transcription effort while preserving lecture materials in an organized and editable format.

### Key Features

- Automatic image capture using Raspberry Pi
- Edge-level image preprocessing
- Backend-controlled device states
- Batch image uploading
- Google Vision AI OCR
- PyTesseract OCR fallback
- Editable OCR text preview
- DOCX document generation
- PDF document generation
- Real-time Raspberry Pi monitoring
- Firebase-based device status synchronization
- Heartbeat monitoring for device connectivity

### System Workflow

```text
Raspberry Pi Camera
        │
        ▼
Image Capture
        │
        ▼
Edge Preprocessing
        │
        ▼
Temporary Image Storage
        │
        ▼
Batch Upload
        │
        ▼
FastAPI Backend
        │
        ├──────────────► Firebase
        │                Device Monitoring
        │
        ▼
Google Vision AI
        │
        │ (Fallback)
        ▼
PyTesseract
        │
        ▼
Extracted Text
        │
        ▼
Preview & Editing
        │
        ├──────────────► DOCX
        │
        └──────────────► PDF
```

---

## Built With

The project uses the following technologies and libraries:

### Raspberry Pi / Edge

- Raspberry Pi 4
- Raspberry Pi Camera Module 3
- Raspberry Pi OS
- `rpicam-still`
- Python
- OpenCV
- Pillow
- Requests

### Backend

- FastAPI
- Python
- Uvicorn
- Firebase Admin SDK

### OCR

- Google Cloud Vision AI
- PyTesseract
- Tesseract OCR

### Document Generation

- python-docx
- FPDF

### Cloud Services

- Firebase Realtime Database
- Render

---

## Getting Started

Follow the steps below to set up the project locally.

### Prerequisites

Make sure the following are installed before running the system.

#### Backend

- Python 3.x
- pip
- Tesseract OCR
- Google Cloud Vision API credentials
- Firebase project and service account credentials

#### Raspberry Pi

- Raspberry Pi 4
- Raspberry Pi Camera Module 3
- Raspberry Pi OS
- Python 3
- Camera utilities
- Internet connection

---

### Installation

#### 1. Clone the Repository

```sh
git clone https://github.com/your-username/lecture-to-document.git
cd lecture-to-document
```

#### 2. Create a Virtual Environment

```sh
python -m venv venv
```

Activate the environment:

**Windows**

```sh
venv\Scripts\activate
```

**Linux / Raspberry Pi**

```sh
source venv/bin/activate
```

#### 3. Install Dependencies

```sh
pip install -r requirements.txt
```

#### 4. Configure Environment Variables

Create a `.env` file in the backend directory.

```env
GOOGLE_APPLICATION_CREDENTIALS=
TESSERACT_CMD=
UPLOAD_DIR=
OUTPUT_DIR=
DEJAVU_FONT=

FIREBASE_CREDENTIALS=
FIREBASE_DB_URL=
```

Do not commit credentials or service-account JSON files to the repository.

#### 5. Start the FastAPI Backend

```sh
uvicorn main:app --reload
```

The API will be available locally through the configured host and port.

FastAPI also provides interactive API documentation through Swagger UI.

---

## Raspberry Pi Configuration

Configure the Raspberry Pi capture script with the backend URL and device information.

Example:

```python
CAPTURE_DIR = "/home/admin/captures"
API_URL = "https://lecture-to-document.onrender.com"
DEVICE_ID = "rspi1001"

CHECK_INTERVAL = 1
CAPTURE_INTERVAL = 3
HEARTBEAT_INTERVAL = 3
```

### Device States

The Raspberry Pi responds to the following backend-controlled states:

| State    | Description                             |
| -------- | --------------------------------------- |
| `start`  | Starts automatic image capture          |
| `pause`  | Temporarily stops image capture         |
| `finish` | Stops capture and triggers batch upload |
| `idle`   | Default inactive state                  |

The device periodically sends heartbeat signals to allow the backend to monitor its connectivity.

---

## Environment Variables

| Variable                         | Description                                       |
| -------------------------------- | ------------------------------------------------- |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to Google Vision service-account credentials |
| `TESSERACT_CMD`                  | Path to the Tesseract OCR executable              |
| `UPLOAD_DIR`                     | Directory for temporarily storing uploaded images |
| `OUTPUT_DIR`                     | Directory for generated documents                 |
| `DEJAVU_FONT`                    | Optional font used for PDF generation             |
| `FIREBASE_CREDENTIALS`           | Firebase Admin SDK credentials                    |
| `FIREBASE_DB_URL`                | Firebase Realtime Database URL                    |

Environment variables are used to prevent sensitive credentials and deployment-specific paths from being hardcoded into the application.

---

## Usage

### 1. Start the System

Power on the Raspberry Pi and ensure it has an active network connection.

The capture process can run automatically as a system service.

### 2. Start Image Acquisition

Set the device status to:

```text
start
```

The Raspberry Pi begins capturing images at the configured interval.

### 3. Capture Lecture Content

The Camera Module captures images of:

- Whiteboard notes
- Handwritten lecture materials
- Printed lecture slides
- Other classroom content

Images are converted to grayscale and resized before being stored locally.

### 4. Finish the Capture Session

Set the device status to:

```text
finish
```

The Raspberry Pi collects the captured images and uploads them to the backend in a single batch.

### 5. Extract Text

The backend processes the uploaded images using:

```text
Google Vision AI
        ↓
If unsuccessful
        ↓
PyTesseract
```

The extracted text is returned as a preview that can be reviewed and edited.

### 6. Generate a Document

The edited text can be exported as either:

- DOCX
- PDF

The generated document can then be downloaded for further use.

---

## API Endpoints

The FastAPI backend provides endpoints for device management, image handling, OCR, and document generation.

### Device Management

| Method | Endpoint                  | Purpose                       |
| ------ | ------------------------- | ----------------------------- |
| `POST` | `/{device_id}/set_status` | Change device state           |
| `GET`  | `/{device_id}/get_status` | Retrieve current device state |
| `POST` | `/{device_id}/heartbeat`  | Update device connectivity    |

### Image Management

| Method   | Endpoint                    | Purpose                    |
| -------- | --------------------------- | -------------------------- |
| `POST`   | `/{device_id}/upload_batch` | Upload multiple images     |
| `GET`    | `/list_uploads`             | List uploaded images       |
| `GET`    | `/get_upload/{filename}`    | Retrieve an uploaded image |
| `DELETE` | `/delete_all_uploads`       | Delete all uploaded images |
| `DELETE` | `/delete_uploads`           | Delete selected images     |

### OCR

| Method | Endpoint                    | Purpose                           |
| ------ | --------------------------- | --------------------------------- |
| `POST` | `/{device_id}/extract_text` | Extract text from uploaded images |

### Document Generation

| Method | Endpoint                     | Purpose                  |
| ------ | ---------------------------- | ------------------------ |
| `POST` | `/{device_id}/generate_docx` | Generate a DOCX document |
| `POST` | `/{device_id}/generate_pdf`  | Generate a PDF document  |

---

## System Architecture

The system follows an **edge-to-cloud architecture**.

### Edge Layer

The Raspberry Pi is responsible for:

- Image acquisition
- Lightweight preprocessing
- Temporary image storage
- Backend communication
- Heartbeat monitoring

### Cloud / Backend Layer

The FastAPI backend handles:

- Device validation
- Image uploads
- OCR processing
- Text extraction
- Document generation
- Device state management

### Real-Time Monitoring Layer

Firebase Realtime Database stores device information such as:

```json
{
  "status": "idle",
  "connected": false,
  "last_seen": 0
}
```

Each device is organized under:

```text
devices/{device_id}
```

### OCR Layer

The system uses a hybrid OCR strategy:

```text
Image
  │
  ▼
Google Vision AI
  │
  ├── Success ──► Extracted Text
  │
  └── Failure
          │
          ▼
     PyTesseract
          │
          ▼
     Extracted Text
```

Using two OCR engines improves system reliability while allowing the primary processing workload to remain in the cloud.

---

## Roadmap

- [x] Raspberry Pi image acquisition
- [x] Camera Module 3 integration
- [x] Edge-level preprocessing
- [x] Backend-controlled device states
- [x] Batch image upload
- [x] Firebase device monitoring
- [x] Heartbeat monitoring
- [x] Google Vision AI OCR
- [x] PyTesseract OCR fallback
- [x] Editable OCR text preview
- [x] DOCX generation
- [x] PDF generation
- [ ] Improve OCR accuracy for difficult handwriting
- [ ] Improve document formatting
- [ ] Expand multi-device management
- [ ] Add additional document export formats

---

## Contributing

Contributions are welcome and appreciated.

1. Fork the Project
2. Create your Feature Branch

```sh
git checkout -b feature/AmazingFeature
```

3. Commit your Changes

```sh
git commit -m "Add AmazingFeature"
```

4. Push to the Branch

```sh
git push origin feature/AmazingFeature
```

5. Open a Pull Request

---

## License

Distributed under the MIT License. See `LICENSE` for more information.

---

## Contact

**Project:** Lecture-to-Document

**Project Repository:**

```text
https://github.com/your-username/lecture-to-document
```

---

## Acknowledgments

- Raspberry Pi Foundation
- Google Cloud Vision AI
- FastAPI
- Firebase
- PyTesseract
- OpenCV
- Pillow
- python-docx
- FPDF
- Render
- GitHub

---

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- MARKDOWN LINKS & IMAGES -->

[python-shield]: https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white
[python-url]: https://www.python.org/
[fastapi-shield]: https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white
[fastapi-url]: https://fastapi.tiangolo.com/
[raspberrypi-shield]: https://img.shields.io/badge/Raspberry%20Pi-A22846?style=for-the-badge&logo=raspberrypi&logoColor=white
[raspberrypi-url]: https://www.raspberrypi.com/
[firebase-shield]: https://img.shields.io/badge/Firebase-FFCA28?style=for-the-badge&logo=firebase&logoColor=black
[firebase-url]: https://firebase.google.com/
[vision-shield]: https://img.shields.io/badge/Google%20Cloud%20Vision-4285F4?style=for-the-badge&logo=googlecloud&logoColor=white
[vision-url]: https://cloud.google.com/vision
