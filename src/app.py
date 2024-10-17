import tkinter as tk
from gui.main_window import MainWindow


def main():
    root = tk.Tk()
    root.title("Mi Biblioteca de Anime")
    root.geometry("1200x850")

    # Crear ventana principal
    app = MainWindow(root)

    # Iniciar bucle principal de Tkinter
    root.mainloop()


if __name__ == "__main__":
    main()
