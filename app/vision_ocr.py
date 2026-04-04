from google.cloud import vision
import os

# Initialize client (uses GOOGLE_APPLICATION_CREDENTIALS)
vision_client = vision.ImageAnnotatorClient()


def extract_text_from_image_bytes(image_bytes: bytes) -> str:
    """
    Extract text from image using Google Vision API
    """
    image = vision.Image(content=image_bytes)

    response = vision_client.text_detection(image=image, timeout=10)

    if response.error.message:
        raise Exception(f"Vision API error: {response.error.message}")

    texts = response.text_annotations

    if not texts:
        return ""

    return texts[0].description  # full detected text