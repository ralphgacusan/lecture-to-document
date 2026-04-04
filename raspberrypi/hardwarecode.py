# import os
# import time
# import requests
# from threading import Thread
# import cv2
# import signal
# from threading import Lock
# from picamera2 import Picamera2

# batch_lock = Lock()

# # --- CONFIG ---
# CAPTURE_DIR = "/home/admin/captures"
# os.makedirs(CAPTURE_DIR, exist_ok=True)

# API_URL = "https://lecture-to-document.onrender.com"
# DEVICE_ID = "rspi1001"

# CHECK_INTERVAL = 3   # check status every 2 seconds
# HEARTBEAT_INTERVAL = 8  # heartbeat every 8 seconds

# capture_paused = False
# device_connected = False
# cap_running = True
# batch_uploaded = False  # ensure batch only happens once

# # --- GLOBAL ---
# last_motion_time = time.time()  # last time motion was detected
# MOTION_THRESHOLD = 20000  # moderate sensitivity
# NO_MOTION_SECONDS = 8  # capture when board is still for ~8 seconds


# # --- LIGHT PREPROCESSING FUNCTION ---
# def preprocess_image(filepath):
#     """Load an image, convert to grayscale, resize lightly, and save."""
#     try:
#         img = cv2.imread(filepath)
#         if img is None:
#             print(f"[ERROR] Failed to read image for preprocessing: {filepath}")
#             return False

#         # Convert to grayscale
#         gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

#         # Optional: resize to width=640 (keep aspect ratio)
#         width = 640
#         height = int(gray.shape[0] * (width / gray.shape[1]))
#         resized = cv2.resize(gray, (width, height))

#         # Save preprocessed image (overwrite original)
#         cv2.imwrite(filepath, resized)
#         print(f"[DEBUG] Preprocessed image saved: {filepath}")
#         return True

#     except Exception as e:
#         print(f"[ERROR] Preprocessing failed: {e}")
#         return False

# # --- CAPTURE IMAGE ---
# def capture_image(filepath, frame=None):
#     """
#     Save a frame to disk and preprocess it.
#     If frame is None, do nothing.
#     """
#     if frame is None:
#         print(f"[ERROR] No frame provided to save: {filepath}")
#         return False

#     try:
#         # Save the frame directly
#         cv2.imwrite(filepath, frame)
#         print(f"[DEBUG] Image saved: {filepath}")

#         # Preprocess image (lightly)
#         preprocess_image(filepath)

#         return True
#     except Exception as e:
#         print(f"[ERROR] Failed to save/preprocess image: {e}")
#         return False


# # --- CAPTURE LOOP WITH MOTION DETECTION ---
# def capture_loop():
#     global last_motion_time, capture_paused
#     last_capture = 0

#     picam2 = Picamera2()
#     picam2.configure(picam2.create_preview_configuration(main={"size": (640, 480)}))
#     picam2.start()
#     time.sleep(2)  # allow camera to warm up

#     prev_frame = picam2.capture_array()
#     prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
#     prev_gray = cv2.GaussianBlur(prev_gray, (21, 21), 0)

#     # Wait until status is 'start' before capturing
#     while cap_running and capture_paused:
#         status = check_status()
#         if status == "start":
#             capture_paused = False
#             print("[DEBUG] Capture starting as status is 'start'.")
#             break
#         else:
#             print(f"[DEBUG] Waiting to start capture, current status: {status}")
#         time.sleep(CHECK_INTERVAL)

#     while cap_running:
#         # Only capture if not paused
#         if capture_paused:
#             time.sleep(CHECK_INTERVAL)
#             continue

#         frame = picam2.capture_array()
#         gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
#         gray = cv2.GaussianBlur(gray, (21, 21), 0)

#         frame_delta = cv2.absdiff(prev_gray, gray)
#         thresh = cv2.threshold(frame_delta, 25, 255, cv2.THRESH_BINARY)[1]
#         motion_score = cv2.countNonZero(thresh)

#         if motion_score > MOTION_THRESHOLD:
#             last_motion_time = time.time()
#         else:
#             if (time.time() - last_motion_time) >= NO_MOTION_SECONDS:
#                 current_time = time.time()
#                 if not capture_paused and (current_time - last_capture >= CHECK_INTERVAL):
#                     filename = os.path.join(CAPTURE_DIR, f"capture_{int(current_time)}.jpg")
#                     Thread(target=capture_image, args=(filename, frame.copy()), daemon=True).start()
#                     last_capture = current_time
#                     last_motion_time = time.time()

#         prev_gray = gray
#         time.sleep(0.3)

# # --- BATCH UPLOAD ---
# def batch_upload_images():
#     with batch_lock:
#         images = sorted([f for f in os.listdir(CAPTURE_DIR) if f.lower().endswith(".jpg")])
#         if not images:
#             print("[INFO] No images to upload.")
#             return

#         print(f"[DEBUG] Uploading {len(images)} images...")
#         open_files = []
#         try:
#             files_payload = []
#             for img_name in images:
#                 f = open(os.path.join(CAPTURE_DIR, img_name), "rb")
#                 open_files.append(f)
#                 files_payload.append(("files", (img_name, f, "image/jpeg")))

#             response = requests.post(f"{API_URL}/{DEVICE_ID}/upload_batch", files=files_payload, timeout=60)
#             if response.ok:
#                 print("[SUCCESS] Batch upload completed!")
#                 set_status_idle()
#                 for img_name in images:
#                     os.remove(os.path.join(CAPTURE_DIR, img_name))
#                     print(f"[INFO] Deleted {img_name}")
#             else:
#                 print(f"[ERROR] Batch upload failed HTTP {response.status_code}")
#         except Exception as e:
#             print(f"[ERROR] Batch upload exception: {e}")
#         finally:
#             for f in open_files:
#                 try:
#                     f.close()
#                 except:
#                     pass

# # --- STATUS CHECK ---
# def check_status():
#     global capture_paused, batch_uploaded
#     try:
#         response = requests.get(f"{API_URL}/{DEVICE_ID}/get_status", timeout=10)
#         if response.ok:
#             data = response.json()
#             status = data.get("status", "idle")

#             if status == "start":
#                 capture_paused = False
#                 with batch_lock:
#                     if batch_uploaded:
#                         batch_uploaded = False
#                         print("[DEBUG] Reset batch_uploaded for new session")
#             elif status == "pause":
#                 capture_paused = True
#             elif status == "finish":
#                 capture_paused = False
#                 with batch_lock:
#                     if not batch_uploaded:
#                         batch_uploaded = True
#                         Thread(target=batch_upload_images, daemon=True).start()
#             return status
#     except Exception as e:
#         print(f"[WARNING] Status check failed: {e}")
#     return "idle"

# # --- HEARTBEAT LOOP ---
# def heartbeat_loop():
#     global device_connected, heartbeat_failures
#     MAX_HEARTBEAT_FAILURES = 6
#     heartbeat_failures = 0

#     while cap_running:
#         try:
#             response = requests.post(f"{API_URL}/{DEVICE_ID}/heartbeat", timeout=15)
#             if response.ok:
#                 data = response.json()
#                 heartbeat_failures = 0
#                 device_connected = data.get("connected", True)
#             else:
#                 heartbeat_failures += 1
#                 print(f"[WARNING] Heartbeat HTTP {response.status_code}, failures={heartbeat_failures}")
#         except Exception as e:
#             heartbeat_failures += 1
#             print(f"[WARNING] Heartbeat exception: {e}, failures={heartbeat_failures}")

#         # Only mark disconnected after more failures
#         if heartbeat_failures >= MAX_HEARTBEAT_FAILURES:
#             device_connected = False

#         time.sleep(HEARTBEAT_INTERVAL)


# # --- DELETE ALL UPLOADS ---
# def delete_all_uploads():
#     """Call backend to delete all uploaded images for this device."""
#     try:
#         response = requests.delete(f"{API_URL}/{DEVICE_ID}/delete_all_uploads", timeout=10)
#         if response.ok:
#             data = response.json()
#             deleted_count = len(data.get("deleted_files", []))
#             print(f"[DEBUG] Deleted {deleted_count} files on backend.")
#         else:
#             print(f"[ERROR] Failed to delete uploads: HTTP {response.status_code}")
#     except Exception as e:
#         print(f"[ERROR] Exception while deleting uploads: {e}")


# # --- SET STATUS TO IDLE ---
# def set_status_idle():
#     """Set device status to 'idle' on backend."""
#     try:
#         response = requests.post(f"{API_URL}/{DEVICE_ID}/set_status", data={"status": "idle"}, timeout=10)
#         if response.ok:
#             print("[DEBUG] Status set to 'idle' on backend.")
#         else:
#             print(f"[ERROR] Failed to set status to idle: HTTP {response.status_code}")
#     except Exception as e:
#         print(f"[ERROR] Exception while setting status to idle: {e}")


# def shutdown_handler(signum, frame):
#     global cap_running, batch_uploaded
#     print(f"\n[DEBUG] Received shutdown signal: {signum}")

#     cap_running = False

#     # Upload remaining images if not uploaded yet
#     with batch_lock:
#         if not batch_uploaded:
#             print("[DEBUG] Uploading remaining images before exit...")
#             batch_uploaded = True
#             batch_upload_images()

#     # Delete all images from backend
#     print("[DEBUG] Deleting all uploaded images on backend...")
#     delete_all_uploads()

#     # Set status to idle
#     print("[DEBUG] Setting status to 'idle' on backend...")
#     set_status_idle()

#     print("[DEBUG] Cleanup done. Exiting.")
#     return


# # --- MAIN ---
# if __name__ == "__main__":
#     print(f"[DEBUG] Starting device: {DEVICE_ID}")

#     signal.signal(signal.SIGTERM, shutdown_handler)
#     signal.signal(signal.SIGINT, shutdown_handler)

#     heartbeat_thread = Thread(target=heartbeat_loop)
#     capture_thread = Thread(target=capture_loop)

#     heartbeat_thread.start()
#     capture_thread.start()

#     while cap_running:
#         time.sleep(1)

#     heartbeat_thread.join()
#     capture_thread.join()

#     print("[DEBUG] Program exited cleanly.")

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

API_URL = "https://lecture-to-document.onrender.com"
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
    with batch_lock:
        images = sorted([f for f in os.listdir(CAPTURE_DIR) if f.lower().endswith(".jpg")])
        if not images:
            print("[INFO] No images to upload.")
            return

        print(f"[DEBUG] Uploading {len(images)} images...")
        open_files = []
        try:
            files_payload = []
            for img_name in images:
                f = open(os.path.join(CAPTURE_DIR, img_name), "rb")
                open_files.append(f)
                files_payload.append(("files", (img_name, f, "image/jpeg")))

            response = requests.post(f"{API_URL}/{DEVICE_ID}/upload_batch", files=files_payload, timeout=60)
            if response.ok:
                print("[SUCCESS] Batch upload completed!")
                set_status_idle()
                for img_name in images:
                    os.remove(os.path.join(CAPTURE_DIR, img_name))
                    print(f"[INFO] Deleted {img_name}")
            else:
                print(f"[ERROR] Batch upload failed HTTP {response.status_code}")
        except Exception as e:
            print(f"[ERROR] Batch upload exception: {e}")
        finally:
            for f in open_files:
                try:
                    f.close()
                except:
                    pass

# --- STATUS CHECK ---
def check_status():
    global capture_paused, batch_uploaded
    try:
        response = requests.get(f"{API_URL}/{DEVICE_ID}/get_status", timeout=5)
        if response.ok:
            data = response.json()
            status = data.get("status", "idle")

            if status == "start":
                capture_paused = False
                with batch_lock:
                    if batch_uploaded:
                        batch_uploaded = False
                        print("[DEBUG] Reset batch_uploaded for new session")
            elif status == "pause":
                capture_paused = True
            elif status == "finish":
                capture_paused = False
                with batch_lock:
                    if not batch_uploaded:
                        batch_uploaded = True
                        Thread(target=batch_upload_images, daemon=True).start()
            return status
    except Exception as e:
        print(f"[WARNING] Status check failed: {e}")
    return "idle"

# --- HEARTBEAT LOOP ---
def heartbeat_loop():
    global device_connected
    while cap_running:
        try:
            response = requests.post(f"{API_URL}/{DEVICE_ID}/heartbeat", timeout=5)
            if response.ok:
                try:
                    data = response.json()
                    device_connected = data.get("connected", True)
                except:
                    device_connected = True
            else:
                print(f"[WARNING] Heartbeat returned HTTP {response.status_code}, ignoring")
                device_connected = True
        except Exception as e:
            print(f"[WARNING] Heartbeat failed: {e}, retrying...")
            device_connected = True
        time.sleep(HEARTBEAT_INTERVAL)

# --- CAPTURE LOOP ---
def capture_loop():
    last_capture = 0
    while cap_running:
        try:
            status = check_status()
        except:
            status = "idle"

        current_time = time.time()
        if not capture_paused and status == "start" and (current_time - last_capture >= CAPTURE_INTERVAL):
            filename = os.path.join(CAPTURE_DIR, f"capture_{int(current_time)}.jpg")
            Thread(target=capture_image, args=(filename,), daemon=True).start()
            last_capture = current_time

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
