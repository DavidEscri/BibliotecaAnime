__author__ = "Jose David Escribano Orts"
__subsystem__ = "gui"
__module__ = "anime_wnidow.py"
__version__ = "0.1"
__info__ = {"subsystem": __subsystem__, "module_name": __module__, "version": __version__}

import os
import tkinter as tk
import webbrowser
from typing import List

from APIs.animeflv.animeflv import AnimeFLV, AnimeInfo, AnimeFLVSingleton, EpisodeInfo, ServerInfo
from utils import utils
from utils.buttons import utilsButtons


class AnimeWindowViewer:
    def __init__(self, main_window, anime_info: AnimeInfo):
        self.main_window = main_window
        self.anime_info: AnimeInfo = anime_info
        self.animeflv_api: AnimeFLV = AnimeFLVSingleton()
        self.servers_frames: dict = {}

    def display_anime_info(self):
        self.main_window.clear_frame()
        self.__display_anime_info()

    def __display_anime_info(self):
        # Cargar la portada del anime
        image_path = os.path.join(self.main_window.images_path, f"{self.anime_info.id}.jpg")
        anime_image = utils.load_image(image_path)

        # Crear un frame para la imagen y la información
        info_frame = tk.Frame(self.main_window.content_frame)
        info_frame.grid(row=0, column=0, pady=10, padx=10)

        # Mostrar la portada en la parte superior izquierda
        image_label = tk.Label(
            info_frame,
            image=anime_image
        )
        image_label.image = anime_image  # Evitar que el garbage collector elimine la imagen
        image_label.grid(row=0, column=0, rowspan=2, sticky="nw", padx=10, pady=10)

        # Título centrado a la derecha de la imagen
        title_label = tk.Label(
            info_frame,
            text=self.anime_info.title,
            font=("Helvetica", 24, "bold"),
            wraplength=self.main_window.content_frame.winfo_width() - 200,
            justify="left",
            anchor="w",
        )
        title_label.grid(row=0, column=1, sticky="nw", padx=10, pady=5)

        # Géneros debajo del título
        genres_label = tk.Label(
            info_frame,
            text="Géneros: " + ", ".join(self.anime_info.genres),
            font=("Helvetica", 14),
            justify="left",
            anchor="w",
        )
        genres_label.grid(row=1, column=1, sticky="nw", padx=10, pady=5)

        # Sinopsis en el frame principal, ocupando todo el ancho
        description_title_label = tk.Label(
            info_frame,
            text="Descripción",
            font=("Helvetica", 16, "bold")
        )
        description_title_label.grid(row=2, column=0, columnspan=2, sticky="w", pady=(10, 5), padx=10)

        description_label = tk.Label(
            info_frame,
            text=self.anime_info.synopsis,
            font=("Helvetica", 14),
            wraplength=self.main_window.content_frame.winfo_width() - 25,
            justify="left",
            anchor="w"
        )
        description_label.grid(row=3, column=0, columnspan=2, sticky="w", padx=10)

        self.__show_anime_episodes(info_frame)

    def __show_anime_episodes(self, info_frame):
        list_episodes_frame = tk.Frame(info_frame)
        list_episodes_frame.grid(row=4, column=0, columnspan=2, sticky="nsew", pady=(10, 5), padx=10)

        # Episodios debajo de la sinopsis, alineados a la izquierda
        episodes_label = tk.Label(
            list_episodes_frame,
            text="Lista de episodios",
            font=("Helvetica", 16, "bold")
        )
        episodes_label.grid(row=0, column=0, sticky="w", pady=(10, 5))

        servers_frames = {}

        for index, episode_info in enumerate(self.anime_info.episodes):
            episode_button = utilsButtons.EpisodeButton(
                parent_frame=list_episodes_frame,
                anime_title=self.anime_info.title,
                episode_info=episode_info,
                servers_frame=servers_frames,
                index=index,
                toggle_servers_command=self.__toggle_servers_frame
            )
            episode_button.grid(row=index + 1, column=0, sticky="w", pady=(10, 5))

            list_episodes_frame.grid_columnconfigure(0, weight=1)

    def __toggle_servers_frame(self, list_episodes_frame, episode_info: EpisodeInfo, servers_frames, current_row: int):
        episode_button = list_episodes_frame.grid_slaves(row=current_row + 1, column=0)[0]
        if episode_info.id in servers_frames:
            servers_frames[episode_info.id].destroy()
            del servers_frames[episode_info.id]
        else:
            servers_info: List[ServerInfo] = self.animeflv_api.get_anime_episode_servers(episode_info.anime,
                                                                                         episode_info.id)
            # Crear un nuevo frame solo para los servidores
            new_server_frame = tk.Frame(list_episodes_frame)
            new_server_frame.grid(row=current_row + 1, column=1, padx=(15, 10), pady=(10, 5), sticky="nsew")

            # Guardar el frame de servidores en el diccionario para poder ocultarlo después
            servers_frames[episode_info.id] = new_server_frame
            num_columns = 3
            for index, server in enumerate(servers_info):
                server_button = utilsButtons.ServerButton(
                    parent_frame=new_server_frame,
                    server_info=server,
                    episode_button=episode_button
                )
                server_button.grid(row=index // num_columns, column=index % num_columns, padx=5, pady=5, sticky="ew")

            for col in range(num_columns):
                new_server_frame.grid_columnconfigure(col, weight=1)