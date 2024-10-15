from gui.sidebarButtons.sidebarButton import BaseButton


class SearchButton(BaseButton):
    def __init__(self, main_window):
        super().__init__(main_window.sidebar_frame, "BUSCADOR DE ANIMES", self.show_buscador)
        self.main_window = main_window

    def show_frame(self):
        self.main_window.clear_frame()
        self.show_buscador()

    def show_buscador(self):
        print("Mostrando buscador de animes")