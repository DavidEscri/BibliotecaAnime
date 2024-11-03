__author__ = "Jose David Escribano Orts"
__subsystem__ = "main"
__module__ = "app.py"
__version__ = "0.1"
__info__ = {"subsystem": __subsystem__, "module_name": __module__, "version": __version__}

from gui.main_window import MainWindow

def main():
    #TODO: Añadir licencia GPL
    # Crear ventana principal
    app = MainWindow()

    # Iniciar bucle principal de customTkinter
    app.mainloop()

if __name__ == "__main__":
    main()
