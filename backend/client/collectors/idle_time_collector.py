import ctypes, time
from client.sqlite_db import store_log
import json

def get_idle_time():
    class LASTINPUTINFO(ctypes.Structure):
        _fields_ = [("cbSize", ctypes.c_uint), ("dwTime", ctypes.c_uint)]
    lii = LASTINPUTINFO()
    lii.cbSize = ctypes.sizeof(LASTINPUTINFO)
    ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lii))
    millis = ctypes.windll.kernel32.GetTickCount() - lii.dwTime
    return millis / 1000.0

def collect_idle():
    try:
        idle_sec = get_idle_time()
        payload = {
            "idle_seconds": idle_sec, 
            # "timestamp": time.time() <-- Removed: Handled by store_log
        }
        # Note: Your backend ingest logic should handle 'idle_seconds' > some threshold 
        # to mark the user as 'offline' for the supervisor dashboard analytics.
        store_log("idle", payload)
    except Exception as e:
        print("Idle collector error:", e)
