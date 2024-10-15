import os
import tkinter as tk
import webbrowser

from APIs.animeflv.animeflv import ServerInfo, EpisodeInfo, AnimeInfo
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
            img_label.bind("<Button-1>", lambda e, anime_id=anime.id: self.on_anime_click(anime_id))

            # Título del anime
            title_label = tk.Label(self.main_window.content_frame, text=anime.title, font=("Helvetica", 10, "bold"), wraplength=130,
                                   justify="center")
            title_label.grid(row=(row * 2) + 1, column=column, padx=10, pady=(0, 10),
                             sticky="n")  # Posicionar con relleno

            title_label.bind("<Button-2>", lambda e, anime_id=anime.id: self.on_anime_click(anime_id))

    def on_anime_click(self, anime_id: AnimeInfo.id):
        anime_info: AnimeInfo = self.main_window.animeflv_api.get_anime_info(anime_id)

        # Limpiar el main_frame
        self.main_window.clear_frame()

        # Cargar la portada del anime
        image_path = os.path.join(self.main_window.images_path, f"{anime_info.id}.jpg")
        anime_image = load_image(image_path)

        # Crear un frame para la imagen y la información
        info_frame = tk.Frame(self.main_window.content_frame)
        info_frame.pack(pady=10)

        # Mostrar la portada en la parte superior izquierda
        image_label = tk.Label(info_frame, image=anime_image)
        image_label.image = anime_image  # Evitar que el garbage collector elimine la imagen
        image_label.grid(row=0, column=0, rowspan=3, padx=10)

        # Título centrado a la derecha de la imagen
        title_label = tk.Label(
            info_frame,
            text=anime_info.title,
            font=("Helvetica", 24, "bold"),
            wraplength=self.main_window.content_frame.winfo_width() - 200
        )
        title_label.grid(row=0, column=1, sticky="w", padx=(10, 50))

        # Géneros debajo del título
        genres_label = tk.Label(
            info_frame,
            text="Géneros: " + ", ".join(anime_info.genres),
            font=("Helvetica", 14)
        )
        genres_label.grid(row=1, column=1, sticky="w", padx=10)

        # Sinopsis en el frame principal, ocupando todo el ancho
        description_title_label = tk.Label(
            self.main_window.content_frame,
            text="Descripción",
            font=("Helvetica", 16, "bold")
        )
        description_title_label.pack(anchor="w", pady=(30, 5), padx=10)

        description_label = tk.Label(
            self.main_window.content_frame,
            text=anime_info.synopsis,
            font=("Helvetica", 14),
            wraplength=self.main_window.content_frame.winfo_width() - 25,
            justify="left",
            anchor="w"
        )
        description_label.pack(pady=5, padx=10)

        # Episodios debajo de la sinopsis, alineados a la izquierda
        episodes_label = tk.Label(
            self.main_window.content_frame,
            text="Lista de episodios",
            font=("Helvetica", 16, "bold")
        )
        episodes_label.pack(anchor="w", pady=(30, 5), padx=10)

        servers_frames = {}

        for episode in anime_info.episodes:
            episode_frame = tk.Frame(self.main_window.content_frame)
            episode_frame.pack(fill=tk.X, pady=5, padx=20)

            episode_button = tk.Button(
                episode_frame,
                text=f"{anime_info.title} episodio {episode.id}",
                font=("Helvetica", 14),
                command=lambda episode_info=episode: self.toggle_servers_frame(episode_info, episode_frame, servers_frames),
            )
            episode_button.pack(pady=5, padx=20)

    def toggle_servers_frame(self, episode_info: EpisodeInfo, episode_frame: tk.Frame, servers_frames: dict):
        """Muestra u oculta el frame de los servidores para un episodio."""
        if episode_info.id in servers_frames:
            # Si el frame ya existe, simplemente lo mostramos u ocultamos
            servers_frame = servers_frames[episode_info.id]
            if servers_frame.winfo_ismapped():
                servers_frame.pack_forget()
            else:
                servers_frame.pack(fill=tk.X)
        else:
            # Si el frame no existe, lo creamos y mostramos
            servers_frame = tk.Frame(episode_frame, bg='grey')  # Puedes quitar el color de fondo
            servers_frames[episode_info.id] = servers_frame

            servers_info = self.main_window.animeflv_api.get_anime_episode_video_servers(episode_info.anime, episode_info.id)
            self.create_server_buttons(servers_info, servers_frame)

            servers_frame.pack(fill=tk.X)

    def create_server_buttons(self, servers_info, servers_frame):
        """Crea y empaqueta los botones de servidores en el centro del servers_frame."""
        for server_info in servers_info:
            server_button = tk.Button(
                servers_frame,
                text=server_info.server,
                command=lambda url=server_info.url: self.play_video(url)
            )
            server_button.pack(side=tk.LEFT, padx=10)  # Agrega un poco de espacio entre los botones

        # Centrar los botones horizontalmente en el servers_frame
        servers_frame.pack_configure(anchor='center')

    def open_episode(self, episode_button, episode_info):
        """Función para abrir un popup de selección de servidor y reproducir el video."""
        servers_info = self.main_window.animeflv_api.get_anime_episode_video_servers(episode_info.anime, episode_info.id)
        for widget in episode_button.winfo_children():
            if widget.winfo_name() == "server_button_frame":
                widget.destroy()

            # Obtener la lista de servidores para el episodio

        # Crear un marco para los botones de los servidores
        server_button_frame = tk.Frame(episode_button, name="server_button_frame")
        server_button_frame.pack(pady=5)

        # Crear botones para cada servidor
        for server_info in servers_info:
            server_button = tk.Button(
                server_button_frame,
                text=server_info.server,
                command=lambda url=server_info.url: self.play_video(url)
            )
            server_button.pack(side=tk.LEFT, padx=5)  # Agregar el botón al marco

    def play_video(self, url):
        """Función para reproducir un video embebido en el frame de Tkinter."""
        webbrowser.open(url)