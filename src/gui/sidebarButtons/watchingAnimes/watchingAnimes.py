__author__ = "Jose David Escribano Orts"
__subsystem__ = "sidebarButtons"
__module__ = "watchingAnimes.py"
__version__ = "0.1"
__info__ = {"subsystem": __subsystem__, "module_name": __module__, "version": __version__}

import os

from utils.buttons import utilsButtons


class WatchingAnimeButton(utilsButtons.SidebarButton):
    def __init__(self, main_window, icon_path, row, column):
        # icon_path_light = os.path.join(icon_path, "viendo_light.png")
        # icon_path_dark = os.path.join(icon_path, "viendo_dark.png")
        icon_path_light = icon_path_dark = os.path.join(icon_path, "viendo.png")
        super().__init__(main_window.sidebar_frame, "ANIMES VIENDO", row, column, self.show_watching_animes,
                         icon_path_light, icon_path_dark)
        self.main_window = main_window

    def show_frame(self):
        self.main_window.clear_frame()
        self.show_watching_animes()

    def show_watching_animes(self):
        print("Mostrando animes viendo")