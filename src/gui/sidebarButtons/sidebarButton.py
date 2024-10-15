import tkinter as tk


class BaseButton:
    def __init__(self, parent_frame, text, command):
        self.button = tk.Button(parent_frame, text=text, command=command, bg="#34495E", fg="white", padx=20, pady=5)
        self.button.pack(fill=tk.X, padx=20, pady=10)

    def show_frame(self):
        raise NotImplementedError("Subclasses must implement this method")