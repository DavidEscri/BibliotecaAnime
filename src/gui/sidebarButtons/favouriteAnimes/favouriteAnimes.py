__author__ = "Jose David Escribano Orts"
__subsystem__ = "sidebarButtons"
__module__ = "favouriteAnimes.py"
__version__ = "0.1"
__info__ = {"subsystem": __subsystem__, "module_name": __module__, "version": __version__}

import os

from utils.buttons import utilsButtons

class FavouritesButton(utilsButtons.SidebarButton):
    def __init__(self, main_window, icon_path, row, column):
        icon_path_light = icon_path_dark = os.path.join(icon_path, "favoritos.png")
        super().__init__(main_window.sidebar_frame, "ANIMES FAVORITOS", row, column, self.show_favorites,
                         icon_path_light, icon_path_dark)
        self.main_window = main_window

    def show_frame(self):
        self.main_window.clear_frame()
        self.show_favorites()

    def show_favorites(self):
        print("Mostrando animes favoritos")