__author__ = "Jose David Escribano Orts"
__subsystem__ = "gui"
__module__ = "main_window.py"
__version__ = "0.1"
__info__ = {"subsystem": __subsystem__, "module_name": __module__, "version": __version__}

import threading
from tkinter import messagebox

import customtkinter as ctk
from typing import List

from PIL import Image, ImageSequence, ImageTk

from APIs.animeflv.animeflv import AnimeFLVSingleton, AnimeFLV, AnimeInfo
from dataPersistence.animesPersistence import AnimesPersistenceSingleton
from gui.sidebarButtons.favouriteAnimes.favouriteAnimes import FavouritesButton
from gui.sidebarButtons.finishedAnimes.finishedAnimes import FinishedAnimeButton
from gui.sidebarButtons.pendingAnimes.pendingAnimes import PendingAnimeButton
from gui.sidebarButtons.recentAnimes.recentAnimes import RecentAnimeButton
from gui.sidebarButtons.searchAnimes.searchAnimes import SearchButton
from gui.sidebarButtons.watchingAnimes.watchingAnimes import WatchingAnimeButton

from utils.utils import download_images, get_resource_path


class MainWindow(ctk.CTk):
    def __init__(self):
        # https://github.com/TomSchimansky/CustomTkinter/blob/master/examples/example_background_image.py
        # https://www.youtube.com/watch?v=iM3kjbbKHQU&ab_channel=NeuralNine
        # https://www.youtube.com/watch?v=p3tSLatmGvU&ab_channel=PythonSimplified
        super().__init__()
        self.title("Mi Biblioteca de Anime")
        self.geometry("1440x910")
        self.animes_persistence = AnimesPersistenceSingleton()

        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure((0, 1, 2), weight=1)

        self.__recent_animes_button: RecentAnimeButton = None
        self.__favourites_animes_button: FavouritesButton = None
        self.__finished_animes_button: FinishedAnimeButton = None
        self.__watching_animes_button: WatchingAnimeButton = None
        self.__pending_animes_button: PendingAnimeButton = None
        self.__search_animes_button: SearchButton = None

        # Crear los frames
        self.loading_frame: ctk.CTkFrame | None = None
        self.sidebar_frame: ctk.CTkFrame = self.create_sidebar()
        self.content_frame: ctk.CTkScrollableFrame = self.create_content_frame()

        self.animeflv_api: AnimeFLV = AnimeFLVSingleton()
        self.recent_animes: List[AnimeInfo] = []
        self.favourites_animes: List[AnimeInfo] = []
        self.finished_animes: List[AnimeInfo] = []
        self.watching_animes: List[AnimeInfo] = []
        self.pending_animes: List[AnimeInfo] = []
        self.images_path = get_resource_path("resources/images/recent_animes")

        self.load_buttons()

        # Inicia mostrando pantalla de carga
        self.show_loading_screen()

    def clear_frame(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def create_sidebar(self) -> ctk.CTkFrame:
        #TODO: Me molan las sidebars: https://youtu.be/Miydkti_QVE?t=3
        sidebar_frame = ctk.CTkFrame(self, width=300)
        sidebar_frame.grid(row=0, column=0, rowspan=8, sticky="nsew")
        sidebar_frame.grid_rowconfigure(8, weight=1)

        sidebar_title_label = ctk.CTkLabel(
            sidebar_frame,
            text="Biblioteca de Anime",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        sidebar_title_label.grid(row=1, column=0, padx=10, pady=20)

        return sidebar_frame

    def load_buttons(self) -> None:
        # Instanciar los botones
        sidebar_button_row = 1
        sidebar_button_column = 0
        self.__recent_animes_button: RecentAnimeButton = RecentAnimeButton(self, sidebar_button_row + 1, sidebar_button_column)
        self.__favourites_animes_button: FavouritesButton = FavouritesButton(self, sidebar_button_row + 2, sidebar_button_column)
        self.__finished_animes_button: FinishedAnimeButton = FinishedAnimeButton(self, sidebar_button_row + 3, sidebar_button_column)
        self.__watching_animes_button: WatchingAnimeButton = WatchingAnimeButton(self, sidebar_button_row + 4, sidebar_button_column)
        self.__pending_animes_button: PendingAnimeButton = PendingAnimeButton(self, sidebar_button_row + 5, sidebar_button_column)
        self.__search_animes_button: SearchButton = SearchButton(self, sidebar_button_row + 6, sidebar_button_column)

        appearance_mode_label = ctk.CTkLabel(
            self.sidebar_frame,
            text="Appearance Mode:",
            anchor="w"
        )
        appearance_mode_label.grid(row=sidebar_button_row + 8, column=sidebar_button_column, padx=20, pady=(10, 0))

        appearance_mode_optionemenu = ctk.CTkOptionMenu(
            self.sidebar_frame,
            values=["Light", "Dark", "System"],
            command=self.change_appearance_mode_event
        )
        appearance_mode_optionemenu.grid(row=sidebar_button_row + 9, column=sidebar_button_column, padx=20, pady=(10, 20))

    def change_appearance_mode_event(self, new_appearance_mode):
        ctk.set_appearance_mode(new_appearance_mode)

    def create_content_frame(self) -> ctk.CTkScrollableFrame:
        # Crear una barra de desplazamiento
        main_frame = ctk.CTkScrollableFrame(self, corner_radius=20)
        main_frame.grid(row=0, column=1, rowspan=8, sticky=ctk.NSEW)

        # Establecer grid en el main_frame
        main_frame.grid_rowconfigure(0, weight=1)  # Permitir que la primera fila se expanda
        main_frame.grid_columnconfigure(0, weight=1)  # Permitir que la primera columna se expanda
        return main_frame

    def show_loading_screen(self):
        self.sidebar_frame.grid_forget()
        self.loading_frame = ctk.CTkFrame(self,corner_radius=0)  # Tamaño fijo para centrarlo

        # Centrar el frame
        x_position = (self.winfo_width() * 2.5)
        y_position = (self.winfo_height() / 1.5)
        self.loading_frame.place(x=x_position, y=y_position)

        # Mostrar el texto de "Cargando biblioteca de anime"
        loading_label = ctk.CTkLabel(
            self.loading_frame,
            text="Cargando biblioteca de anime",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        loading_label.pack(pady=20)

        # Cargar y mostrar el GIF con todos los frames
        loading_image_path = get_resource_path("resources/images/utils/loading-image.gif")
        gif_image = Image.open(loading_image_path)
        gif_frames = [ctk.CTkImage(frame.copy(), size=(400, 400)) for frame in ImageSequence.Iterator(gif_image)]
        loading_image_label = ctk.CTkLabel(self.loading_frame, text="")
        loading_image_label.pack(pady=20)

        # Crear y mostrar la barra de progreso
        progress_bar = ctk.CTkProgressBar(self.loading_frame, width=400)
        progress_bar.set(0)
        progress_bar.pack(pady=10)
        progress_label = ctk.CTkLabel(self.loading_frame, text="0 %")
        progress_label.pack(pady=5)

        def update_gif(frame=0):
            loading_image_label.configure(image=gif_frames[frame])
            frame = (frame + 1) % len(gif_frames)  # Continuar en bucle
            self.after(100, update_gif, frame)  # Controla la velocidad de cambio de frame (100 ms)

        update_gif()  # Iniciar la animación

        # Iniciar la descarga de imágenes en un hilo
        threading.Thread(target=self.download_images_and_show_animes, args=(progress_bar, progress_label, ), daemon=True).start()

    def download_images_and_show_animes(self, progress_bar: ctk.CTkProgressBar, progress_label: ctk.CTkLabel):
        self.load_animes(progress_bar, progress_label)
        self.recent_animes = self.animeflv_api.get_recent_animes()
        if len(self.recent_animes) == 0:
            messagebox.showwarning("Aviso!",
                                   "La conexión con https://www3.animeflv.net/ es muy lenta, por lo que no se "
                                   "pudieron obtener los animes recientes.")
            self.__recent_animes_button.show_frame()
            return
        progress_bar.set(0.9)
        progress_label.configure(text="90 %")
        download_images(self.images_path, self.recent_animes, progress_bar, progress_label)  # Descargar imágenes
        self.__recent_animes_button.show_frame()  # Mostrar animes recientes al finalizar la descarga

    def load_animes(self, progress_bar: ctk.CTkProgressBar, progress_label: ctk.CTkLabel):
        self.animes_persistence.start()
        self.favourites_animes = self.animes_persistence.get_favourite_animes()
        progress_bar.set(0.1)
        progress_label.configure(text="10 %")
        self.finished_animes = self.animes_persistence.get_finished_animes()
        progress_bar.set(0.2)
        progress_label.configure(text="20 %")
        self.watching_animes = self.animes_persistence.get_watching_animes()
        progress_bar.set(0.3)
        progress_label.configure(text="30 %")
        self.pending_animes = self.animes_persistence.get_pending_animes()
        progress_bar.set(0.4)
        progress_label.configure(text="40 %")
