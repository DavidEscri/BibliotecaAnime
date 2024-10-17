import os
import tkinter as tk
import webbrowser
from typing import Union

from APIs.animeflv.animeflv import EpisodeInfo, AnimeInfo
from gui.sidebarButtons.sidebarButton import BaseButton
from utils.utils import load_image


class RecentAnimeButton(BaseButton):
    def __init__(self, main_window):
        super().__init__(main_window.sidebar_frame, "ANIMES RECIENTES", self.__show_animes_recientes)
        self.main_window = main_window

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
        anime_info: AnimeInfo = self.main_window.animeflv_api.get_anime_info(anime_id)

        # Limpiar el main_frame
        self.main_window.clear_frame()

        # Cargar la portada del anime
        image_path = os.path.join(self.main_window.images_path, f"{anime_info.id}.jpg")
        anime_image = load_image(image_path)

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
            text=anime_info.title,
            font=("Helvetica", 24, "bold"),
            wraplength=self.main_window.content_frame.winfo_width() - 200,
            justify="left",
            anchor="w",
        )
        title_label.grid(row=0, column=1, sticky="nw", padx=10, pady=5)

        # Géneros debajo del título
        genres_label = tk.Label(
            info_frame,
            text="Géneros: " + ", ".join(anime_info.genres),
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
            text=anime_info.synopsis,
            font=("Helvetica", 14),
            wraplength=self.main_window.content_frame.winfo_width() - 25,
            justify="left",
            anchor="w"
        )
        description_label.grid(row=3, column=0, columnspan=2, sticky="w", padx=10)

        self.__show_anime_episodes(info_frame, anime_info)

    def __show_anime_episodes(self, info_frame, anime_info):
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

        for index, episode_info in enumerate(anime_info.episodes):
            episode_button = tk.Button(
                list_episodes_frame,
                text=f"{anime_info.title}\n\nEpisodio {episode_info.id}",
                font=("Helvetica", 14),
                height=5,  # Ajusta la altura del botón
                width=50,  # Ajusta el ancho del botón del episodio
                anchor="w",
                justify="left",
                command=lambda ep_info=episode_info, ep_index=index: self.__toggle_servers_frame(
                    list_episodes_frame, servers_frames, ep_info, ep_index
                ),
            )
            episode_button.grid(row=index + 1, column=0, sticky="w", pady=(10, 5))

            list_episodes_frame.grid_columnconfigure(0, weight=1)

    def __toggle_servers_frame(self, list_episodes_frame, servers_frames, episode_info, current_row):
        if episode_info.id in servers_frames:
            servers_frames[episode_info.id].destroy()
            del servers_frames[episode_info.id]
        else:
            servers_info = self.main_window.animeflv_api.get_anime_episode_video_servers(episode_info.anime,
                                                                                         episode_info.id)
            # Crear un nuevo frame solo para los servidores
            new_server_frame = tk.Frame(list_episodes_frame)
            new_server_frame.grid(row=current_row + 1, column=1, padx=(15, 10), pady=(10, 5), sticky="nsew")

            # Guardar el frame de servidores en el diccionario para poder ocultarlo después
            servers_frames[episode_info.id] = new_server_frame
            num_columns = 3
            for index, server in enumerate(servers_info):
                server_button = tk.Button(
                    new_server_frame,
                    text=server.server,
                    font=("Helvetica", 12),
                    width=10,  # Ancho fijo para todos los botones de servidor
                    command=lambda url=server.url: self.__play_video(url)
                )
                server_button.grid(row=index // num_columns, column=index % num_columns, padx=5, pady=5, sticky="ew")

            for col in range(num_columns):
                new_server_frame.grid_columnconfigure(col, weight=1)

    def __play_video(self, url):
        """Función para reproducir un video embebido en el frame de Tkinter."""
        webbrowser.open(url)