import firebase_admin
from firebase_admin import credentials, db
import time


cred = credentials.Certificate("app/firebase_key.json")
firebase_admin.initialize_app(cred, {
    "databaseURL": "https://lecture-to-document-c4f7e-default-rtdb.asia-southeast1.firebasedatabase.app/"
})


def get_device_ref(device_id: str):
    return db.reference(f"devices/{device_id}")


def get_device(device_id: str):
    return get_device_ref(device_id).get()


def create_device_if_not_exists(device_id: str):
    ref = get_device_ref(device_id)
    if not ref.get():
        ref.set({
            "status": "idle",
            "connected": False,
            "last_seen": 0
        })


def update_status(device_id: str, status: str):
    create_device_if_not_exists(device_id)
    get_device_ref(device_id).update({
        "status": status
    })


def update_heartbeat(device_id: str):
    create_device_if_not_exists(device_id)
    get_device_ref(device_id).update({
        "connected": True,
        "last_seen": int(time.time())
    })


def check_connection(device: dict, timeout=15):
    if not device or not device.get("last_seen"):
        return False

    return (time.time() - device["last_seen"]) <= timeout