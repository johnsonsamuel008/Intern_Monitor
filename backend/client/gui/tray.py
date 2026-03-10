import pystray
from PIL import Image
import threading
import sys

def start_tray(show_window, on_exit):
    image = Image.new("RGB", (64, 64), (0, 120, 215))

    def restore(icon, item):
        show_window()

    def quit_app(icon, item):
        on_exit()
        icon.stop()
        sys.exit(0)

    menu = pystray.Menu(
        pystray.MenuItem("Open", restore),
        pystray.MenuItem("Exit", quit_app)
    )

    icon = pystray.Icon("InternMonitor", image, "Intern Monitor", menu)

    threading.Thread(target=icon.run, daemon=True).start()
