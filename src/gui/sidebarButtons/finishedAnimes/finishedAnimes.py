__author__ = "Jose David Escribano Orts"
__subsystem__ = "sidebarButtons"
__module__ = "finishedAnimes.py"
__version__ = "0.1"
__info__ = {"subsystem": __subsystem__, "module_name": __module__, "version": __version__}

import os

from utils.buttons import utilsButtons


class FinishedAnimeButton(utilsButtons.SidebarButton):
    def __init__(self, main_window, icon_path, row, column):
        icon_path_light = icon_path_dark = os.path.join(icon_path, "finalizados.png")
        super().__init__(main_window.sidebar_frame, "ANIMES FINALIZADOS", row, column, self.show_finished_animes,
                         icon_path_light, icon_path_dark)
        self.main_window = main_window

    def show_frame(self):
        self.main_window.clear_frame()
        self.show_finished_animes()

    def show_finished_animes(self):
        print("Mostrando animes finalizados")