import customtkinter as ctk
from client.gui.screens.pairing import PairingScreen
from client.gui.screens.status import StatusScreen
from client.device_token import load_device_token
from client.gui.tray import start_tray
import logging
import sys

ctk.set_appearance_mode("system")
ctk.set_default_color_theme("blue")

class InternMonitorApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Intern Monitor")
        self.geometry("520x340")
        self.resizable(False, False)

        self.protocol("WM_DELETE_WINDOW", self.hide)

        self.container = ctk.CTkFrame(self)
        self.container.pack(fill="both", expand=True)

        start_tray(self.show, self.exit)

        if load_device_token():
            self.show_status()
        else:
            self.show_pairing()

    def clear(self):
        for widget in self.container.winfo_children():
            widget.destroy()

    def show_pairing(self):
        self.deiconify()
        self.clear()
        PairingScreen(self.container, self.show_status).pack(expand=True)

    def show_status(self):
        self.deiconify()
        self.clear()
        StatusScreen(self.container).pack(expand=True)

    def hide(self):
        self.withdraw()

    def show(self):
        self.deiconify()
        self.lift()

    def exit(self):
        self.destroy()
        sys.exit(0)
