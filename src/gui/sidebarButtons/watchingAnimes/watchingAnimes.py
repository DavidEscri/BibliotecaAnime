__author__ = "Jose David Escribano Orts"
__subsystem__ = "sidebarButtons"
__module__ = "watchingAnimes.py"
__version__ = "0.1"
__info__ = {"subsystem": __subsystem__, "module_name": __module__, "version": __version__}

from utils.buttons import utilsButtons


class WatchingAnimeButton(utilsButtons.SidebarButton):
    def __init__(self, main_window, row, column):
        super().__init__(main_window.sidebar_frame, "ANIMES VIENDO", row, column, self.show_watching_animes)
        self.main_window = main_window

    def show_frame(self):
        self.main_window.clear_frame()
        self.show_watching_animes()

    def show_watching_animes(self):
        print("Mostrando animes viendo")