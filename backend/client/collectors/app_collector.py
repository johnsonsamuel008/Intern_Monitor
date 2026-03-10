import pygetwindow as gw
from client.sqlite_db import store_log
from datetime import datetime, timezone

def collect_app():
    try:
        window = gw.getActiveWindow()
        if window:
            # 2026 Standard: Generate UTC timestamp here
            current_time = datetime.now(timezone.utc)

            payload = {
                "app_name": window.title,
                # Timestamp is now handled by store_log function itself
                # or passed as an ISO string if your store_log expects it
            }
            # The store_log function was updated previously to handle the timestamp generation
            store_log("application", payload)
            
    except Exception as e:
        print("App collector error:", e)

