import time
import logging
import threading
import json
import requests
from datetime import datetime, timezone

from client.config import BACKEND_BASE_URL, SYNC_INTERVAL
from client.device_token import load_device_token
# fetch_pending now returns (id, type, payload, timestamp)
from client.sqlite_db import fetch_pending, mark_uploaded

_uploader_started = False

def upload_logs_once():
    token = load_device_token()
    if not token:
        logging.warning("Uploader: No device token found.")
        return

    # fetch_pending now provides a 4th value: timestamp
    rows = fetch_pending()
    if not rows:
        return

    payload_batch = []
    ids = []

    for log_id, log_type, payload_raw, timestamp_iso in rows:
        try:
            data_dict = json.loads(payload_raw) if isinstance(payload_raw, str) else payload_raw
        except Exception:
            data_dict = {"raw": payload_raw}
        
        # CRITICAL UPDATE: Construct payload to match FastAPI 'IncomingLog' schema
        payload_batch.append({
            "type": log_type,
            "data": data_dict,
            "timestamp": timestamp_iso # Use the ISO timestamp from the DB
        })
        ids.append(log_id)

    try:
        # CRITICAL UPDATE: Use the correct backend endpoint URL
        r = requests.post(
            f"{BACKEND_BASE_URL}/activity-logs/", 
            json=payload_batch,
            headers={"Authorization": f"Device {token}"},
            timeout=10
        )
        if r.status_code == 201: # Endpoint returns 201 Created on success
            mark_uploaded(ids)
            logging.info(f"Successfully uploaded {len(ids)} logs.")
        else:
            logging.error(f"Uploader server error: {r.status_code} - {r.text}")
    except Exception as e:
        logging.error(f"Uploader connection error: {e}")

def _uploader_loop():
    while True:
        try:
            upload_logs_once()
        except Exception as e:
            logging.error(f"Uploader unexpected loop error: {e}")
        time.sleep(SYNC_INTERVAL)

def start_uploader():
    global _uploader_started
    if _uploader_started:
        return

    logging.info("Uploader service starting...")
    thread = threading.Thread(target=_uploader_loop, daemon=True)
    thread.start()
    _uploader_started = True
