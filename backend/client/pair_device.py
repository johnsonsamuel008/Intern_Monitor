import platform
import requests

from client.config import BACKEND_BASE_URL
from client.device_token import save_device_token

def pair_device(pairing_code: str):
    payload = {
        "pairing_code": pairing_code,
        "device_name": platform.node(),
        "os_type": platform.system(),
    }

    r = requests.post(
        f"{BACKEND_BASE_URL}/devices/pair",
        json=payload,
        timeout=10
    )

    if r.status_code != 200:
        raise RuntimeError(f"Pairing failed: {r.text}")

    save_device_token(r.json()["device_token"])
    