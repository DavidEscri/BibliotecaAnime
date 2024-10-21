__author__ = "Jose David Escribano Orts"
__subsystem__ = "sidebarButtons"
__module__ = "pendingAnimes.py"
__version__ = "0.1"
__info__ = {"subsystem": __subsystem__, "module_name": __module__, "version": __version__}

from gui.sidebarButtons.sidebarButton import BaseButton


class PendingAnimeButton(BaseButton):
    def __init__(self, main_window):
        super().__init__(main_window.sidebar_frame, "ANIMES PENDIENTES", self.show_pending_animes)
        self.main_window = main_window

    def show_frame(self):
        self.main_window.clear_frame()
        self.show_pending_animes()

    def show_pending_animes(self):
        print("Mostrando animes pendientes")