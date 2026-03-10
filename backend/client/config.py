import os
import sys
import platform
from pathlib import Path

APP_NAME = "InternMonitoringSystem"

def get_data_dir():
    """Returns OS-specific standard data directory for 2026 systems."""
    if getattr(sys, "frozen", False):
        if platform.system() == "Windows":
            return Path(os.environ.get('LOCALAPPDATA', Path.home())) / APP_NAME
        elif platform.system() == "Darwin": # macOS
            return Path.home() / "Library/Application Support" / APP_NAME
        else: # Linux
            return Path.home() / ".local/share" / APP_NAME
    return Path(__file__).parent / "data"

DATA_DIR = get_data_dir()
DATA_DIR.mkdir(parents=True, exist_ok=True)

# REMOVED: CHROME_PATH, FIREFOX_ROOT, etc. (No longer needed with browser-history)

BACKEND_BASE_URL = "https://lorenza-nudicaul-eulah.ngrok-free.dev"
SYNC_INTERVAL = 300 
DB_PATH = DATA_DIR / "iams_client.db"
