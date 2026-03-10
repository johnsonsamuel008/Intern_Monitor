import sys
import os
import time
import threading
import logging

from client.config import DATA_DIR, SYNC_INTERVAL
from client.sqlite_db import init_db
from client.device_token import load_device_token
from client.uploader import start_uploader
from client.gui.app import InternMonitorApp
from client.gui.autostart import enable_autostart

# -------------------------
# SAFETY FOR --NOCONSOLE
# -------------------------
if getattr(sys, "frozen", False) and sys.platform == "win32":
    sys.stdin = open(os.devnull, "r")
    sys.stdout = open(os.devnull, "w")
    sys.stderr = open(os.devnull, "w")

# -------------------------
# LOGGING
# -------------------------
LOG_PATH = DATA_DIR / "client.log"
logging.basicConfig(
    filename=LOG_PATH,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# -------------------------
# BACKGROUND LOOP
# -------------------------
def background_loop():
    while True:
        try:
            start_uploader()
        except Exception:
            logging.exception("Uploader failure")
        time.sleep(SYNC_INTERVAL)

# -------------------------
# MAIN
# -------------------------
def main():
    logging.info("InternMonitor starting")

    init_db()

    # Start background thread
    threading.Thread(
        target=background_loop,
        daemon=True
    ).start()

    app = InternMonitorApp()

    # Enable autostart AFTER first successful pairing
    if load_device_token():
        enable_autostart()
        app.withdraw()  # start hidden
    else:
        app.deiconify()  # show pairing UI

    app.mainloop()

if __name__ == "__main__":
    main()
