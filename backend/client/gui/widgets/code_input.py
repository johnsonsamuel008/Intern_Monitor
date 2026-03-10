import customtkinter as ctk

class CodeInput(ctk.CTkFrame):
    def __init__(self, master, length=8):
        super().__init__(master)
        self.entries = []

        for i in range(length):
            e = ctk.CTkEntry(self, width=35, justify="center")
            e.grid(row=0, column=i, padx=4)
            e.bind("<KeyRelease>", lambda ev, idx=i: self._on_key(ev, idx))
            self.entries.append(e)

        self.entries[0].focus_set()

    def _on_key(self, event, index):
        if event.keysym == "BackSpace" and index > 0 and not self.entries[index].get():
            self.entries[index-1].focus_set()
        elif self.entries[index].get() and index < len(self.entries)-1:
            self.entries[index+1].focus_set()

    def get_code(self):
        return "".join(e.get().strip() for e in self.entries)
