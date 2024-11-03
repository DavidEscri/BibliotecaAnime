__author__ = "Jose David Escribano Orts"
__subsystem__ = "sidebarButtons"
__module__ = "recentAnimes.py"
__version__ = "0.1"
__info__ = {"subsystem": __subsystem__, "module_name": __module__, "version": __version__}

import os
import time

import customtkinter as ctk
from typing import Union

from APIs.animeflv.animeflv import AnimeInfo, AnimeFLV, AnimeFLVSingleton
from gui.anime_window import AnimeWindowViewer
from utils.buttons import utilsButtons
from utils.utils import load_image


class RecentAnimeButton(utilsButtons.SidebarButton):
    def __init__(self, main_window, row: int, column: int):
        super().__init__(main_window.sidebar_frame, "ANIMES RECIENTES", row, column, self.__show_animes_recientes)
        self.main_window = main_window
        self.animeflv_api: AnimeFLV = AnimeFLVSingleton()

    def show_frame(self):
        self.main_window.loading_frame.place_forget()  # Usar place_forget para ocultar el frame

        # Mostrar el sidebar ahora que ha terminado la descarga
        self.main_window.sidebar_frame.grid(row=0, column=0, rowspan=8, sticky="nsew")

        self.main_window.clear_frame()
        self.__show_animes_recientes()

    def __show_animes_recientes(self):
        self.main_window.clear_frame()
        time.sleep(0.1)
        num_columns = max(1, self.main_window.content_frame.winfo_width() // 150)  # Calcula el número de columnas

        # Configurar que las columnas tengan el mismo peso y estén centradas
        for col in range(num_columns):
            self.main_window.content_frame.grid_columnconfigure(col, weight=1)

        if len(self.main_window.recent_animes) == 0:
            message_label = ctk.CTkLabel(
                self.main_window.content_frame,
                text="No se pudo obtener la lista de animes recientes",
                font=ctk.CTkFont(size=26, weight="bold"),
                justify="center",
            )
            message_label.grid(row=0, column=num_columns//2, sticky=ctk.NSEW, pady=(10, 0))
            return

        for index, anime in enumerate(self.main_window.recent_animes):
            row = index // num_columns
            column = index % num_columns

            # Cargar la imagen desde el archivo en lugar de la URL
            img_file = f"{anime.id}.jpg"
            image = load_image(os.path.join(self.main_window.images_path, img_file))

            img_label = ctk.CTkLabel(
                self.main_window.content_frame,
                text="",
                image=image
            )
            img_label.image = image  # Mantener una referencia a la imagen
            img_label.grid(row=row * 2, column=column, padx=10, pady=(20, 0), sticky=ctk.NSEW)  # Posicionar con relleno
            img_label.bind("<Button-1>", lambda e, anime_id=anime.id: self.__on_anime_click(anime_id))

            # Título del anime
            title_label = ctk.CTkLabel(
                self.main_window.content_frame,
                text=anime.title,
                font=ctk.CTkFont(size=14),
                wraplength=120,
                justify="center"
            )
            title_label.grid(row=(row * 2) + 1, column=column, padx=10, pady=(5, 10), sticky=ctk.N)  # Posicionar con relleno

    def __on_anime_click(self, anime_id: Union[str, int]):
        index = next(idx for idx, recent_anime in enumerate(self.main_window.recent_animes) if recent_anime.id == anime_id)
        # Reemplazar el anime en la lista
        anime_clicked = self.main_window.recent_animes[index]
        if anime_clicked.synopsis is None or anime_clicked.genres is None or anime_clicked.episodes is None:
            anime_clicked: AnimeInfo = self.animeflv_api.get_anime_info(anime_id)
            self.main_window.recent_animes[index] = anime_clicked
        anime_viewer = AnimeWindowViewer(self.main_window, anime_clicked)
        anime_viewer.display_anime_info()