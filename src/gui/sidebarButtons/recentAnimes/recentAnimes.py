__author__ = "Jose David Escribano Orts"
__subsystem__ = "sidebarButtons"
__module__ = "recentAnimes.py"
__version__ = "0.1"
__info__ = {"subsystem": __subsystem__, "module_name": __module__, "version": __version__}

import os
import tkinter as tk
from typing import Union

from APIs.animeflv.animeflv import AnimeInfo, AnimeFLV, AnimeFLVSingleton
from gui.anime_window import AnimeWindowViewer
from utils.buttons import utilsButtons
from utils.utils import load_image


class RecentAnimeButton(utilsButtons.SidebarButton):
    def __init__(self, main_window):
        super().__init__(main_window.sidebar_frame, "ANIMES RECIENTES", self.__show_animes_recientes)
        self.main_window = main_window
        self.animeflv_api: AnimeFLV = AnimeFLVSingleton()

    def show_frame(self):
        self.main_window.loading_frame.place_forget()  # Usar place_forget para ocultar el frame

        # Mostrar el sidebar ahora que ha terminado la descarga
        self.main_window.sidebar_frame.pack(side=tk.LEFT, fill=tk.Y)

        self.main_window.clear_frame()
        self.__show_animes_recientes()

    def __show_animes_recientes(self):
        self.main_window.clear_frame()
        num_columns = max(1, (self.main_window.root.winfo_width() - 250) // 150)  # Calcula el número de columnas

        # Configurar que las columnas tengan el mismo peso y estén centradas
        for col in range(num_columns):
            self.main_window.content_frame.grid_columnconfigure(col, weight=1)

        for index, anime in enumerate(self.main_window.recent_animes):
            row = index // num_columns
            column = index % num_columns

            # Cargar la imagen desde el archivo en lugar de la URL
            img_file = f"{anime.id}.jpg"
            image = load_image(os.path.join(self.main_window.images_path, img_file))

            img_label = tk.Label(self.main_window.content_frame, image=image)
            img_label.image = image  # Mantener una referencia a la imagen
            img_label.grid(row=row * 2, column=column, padx=10, pady=(20, 0), sticky="nsew")  # Posicionar con relleno
            img_label.bind("<Button-1>", lambda e, anime_id=anime.id: self.__on_anime_click(anime_id))

            # Título del anime
            title_label = tk.Label(self.main_window.content_frame, text=anime.title, font=("Helvetica", 10, "bold"), wraplength=130,
                                   justify="center")
            title_label.grid(row=(row * 2) + 1, column=column, padx=10, pady=(0, 10),
                             sticky="n")  # Posicionar con relleno

            title_label.bind("<Button-2>", lambda e, anime_id=anime.id: self.__on_anime_click(anime_id))

    def __on_anime_click(self, anime_id: Union[str, int]):
        anime_info: AnimeInfo = self.animeflv_api.get_anime_info(anime_id)
        anime_viewer = AnimeWindowViewer(self.main_window, anime_info)
        anime_viewer.display_anime_info()