import psutil
import time
from client.sqlite_db import store_log
import json

# Global variable to store previous network counters to calculate delta
_last_net_io = None

def collect_system():
    global _last_net_io
    try:
        # Calculate network usage delta since last run
        current_net_io = psutil.net_io_counters()
        download_mb = 0
        upload_mb = 0

        if _last_net_io:
            # Convert bytes delta to Megabytes (1024*1024)
            download_mb = round((current_net_io.bytes_recv - _last_net_io.bytes_recv) / 1048576, 2)
            upload_mb = round((current_net_io.bytes_sent - _last_net_io.bytes_sent) / 1048576, 2)
        
        _last_net_io = current_net_io # Update counter for next loop

        payload = {
            "cpu": psutil.cpu_percent(),
            "ram": psutil.virtual_memory().percent,
            "disk": psutil.disk_usage("/").percent,
            # SRS 3.4: Add network metrics for bandwidth alerts
            "net_download_mb": download_mb,
            "net_upload_mb": upload_mb,
            # "timestamp": time.time() <-- Removed: Handled by store_log
        }
        store_log("system", payload)
    except Exception as e:
        print("System collector error:", e)
