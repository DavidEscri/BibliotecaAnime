from gui.sidebarButtons.sidebarButton import BaseButton


class FinishedAnimeButton(BaseButton):
    def __init__(self, main_window):
        super().__init__(main_window.sidebar_frame, "ANIMES FINALIZADOS", self.show_finished_animes)
        self.main_window = main_window

    def show_frame(self):
        self.main_window.clear_frame()
        self.show_finished_animes()

    def show_finished_animes(self):
        print("Mostrando animes finalizados")