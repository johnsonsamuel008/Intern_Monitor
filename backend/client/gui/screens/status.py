import customtkinter as ctk
import threading
import logging

class StatusScreen(ctk.CTkFrame):
    started = False

    def __init__(self, master):
        super().__init__(master)

        ctk.CTkLabel(
            self,
            text="Device Status",
            font=("Segoe UI", 16, "bold")
        ).pack(pady=10)

        ctk.CTkLabel(
            self,
            text="Monitoring Active",
            text_color="green"
        ).pack(pady=5)

        if not StatusScreen.started:
            from client.uploader import start_uploader
            uploader_thread = threading.Thread(
                target=start_uploader,
                daemon=True
            )
            uploader_thread.start()
            logging.info("Starting uploader thread")
            StatusScreen.started = True
