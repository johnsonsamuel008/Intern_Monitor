import customtkinter as ctk
import threading
import logging
import sys
from pathlib import Path

from client.pair_device import pair_device


def resource_path(relative: str) -> str:
    if getattr(sys, "frozen", False):
        return str(Path(sys._MEIPASS) / relative)
    return relative


class PairingScreen(ctk.CTkFrame):
    CODE_LENGTH = 8
    EXPIRATION_SECONDS = 300

    def __init__(self, master, on_success):
        super().__init__(master)
        self.on_success = on_success
        self.entries = []
        self.remaining_time = self.EXPIRATION_SECONDS
        self._active = True

        self._build_ui()
        self._setup_bindings()
        self._start_countdown()

    def _build_ui(self):
        self.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            self,
            text="Intern Monitor",
            font=ctk.CTkFont(size=26, weight="bold")
        ).pack(pady=(30, 6))

        ctk.CTkLabel(
            self,
            text="Device Pairing",
            font=ctk.CTkFont(size=19, weight="bold")
        ).pack(pady=(0, 6))

        ctk.CTkLabel(
            self,
            text="Enter the 8-digit code from your dashboard",
            font=ctk.CTkFont(size=13),
            text_color="gray"
        ).pack(pady=(0, 20))

        entry_frame = ctk.CTkFrame(self, fg_color="transparent")
        entry_frame.pack(pady=10)

        for i in range(self.CODE_LENGTH):
            e = ctk.CTkEntry(
                entry_frame,
                width=45,
                height=50,
                justify="center",
                font=ctk.CTkFont(size=18, weight="bold")
            )
            e.grid(row=0, column=i, padx=4)
            e.bind("<KeyRelease>", lambda ev, idx=i: self._handle_keypress(ev, idx))
            self.entries.append(e)

        self.entries[0].focus_set()

        self.status_label = ctk.CTkLabel(self, text="", font=ctk.CTkFont(size=12))
        self.status_label.pack(pady=(10, 0))

        self.timer_label = ctk.CTkLabel(self, text="", text_color="gray", font=ctk.CTkFont(size=11))
        self.timer_label.pack(pady=(0, 10))

        self.pair_btn = ctk.CTkButton(
            self,
            text="Pair Device",
            font=ctk.CTkFont(weight="bold"),
            command=self._submit
        )
        self.pair_btn.pack(pady=10)

    def _setup_bindings(self):
        top = self.winfo_toplevel()
        top.bind("<Return>", lambda _: self._submit())
        top.bind("<Escape>", lambda _: self._cancel())

    def _handle_keypress(self, event, idx):
        val = self.entries[idx].get()

        # Numeric only
        if not val.isdigit():
            self.entries[idx].delete(0, "end")
            return

        if len(val) == 1 and idx < self.CODE_LENGTH - 1:
            self.entries[idx + 1].focus_set()

        if event.keysym == "BackSpace" and val == "" and idx > 0:
            self.entries[idx - 1].focus_set()

    def _start_countdown(self):
        if not self._active:
            return

        if self.remaining_time <= 0:
            self._set_status("Pairing code expired", "red")
            self.pair_btn.configure(state="disabled")
            return

        mins, secs = divmod(self.remaining_time, 60)
        self.timer_label.configure(text=f"Code expires in {mins:02d}:{secs:02d}")
        self.remaining_time -= 1
        self.after(1000, self._start_countdown)

    def _set_status(self, text, color):
        self.status_label.configure(text=text, text_color=color)

    def _submit(self):
        code = "".join(e.get() for e in self.entries)

        if len(code) != self.CODE_LENGTH:
            self._set_status("Invalid code length", "red")
            return

        self._set_status("Connecting…", "orange")
        self.pair_btn.configure(state="disabled")

        threading.Thread(
            target=self._run_pairing,
            args=(code,),
            daemon=True
        ).start()

    def _run_pairing(self, code):
        try:
            pair_device(code)
            self.after(0, self._handle_success)
        except Exception as e:
            self.after(0, lambda: self._handle_failure(str(e)))

    def _handle_success(self):
        self._active = False
        self._set_status("Paired successfully", "green")
        self.after(800, self.on_success)

    def _handle_failure(self, msg):
        self._set_status(msg, "red")
        self.pair_btn.configure(state="normal")

    def _cancel(self):
        self._active = False
        self.destroy()
