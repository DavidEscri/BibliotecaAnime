__author__ = "Jose David Escribano Orts"
__subsystem__ = "gui"
__module__ = "anime_wnidow.py"
__version__ = "0.1"
__info__ = {"subsystem": __subsystem__, "module_name": __module__, "version": __version__}

import json
import time
import webbrowser

import customtkinter as ctk
from typing import List

from APIs.animeflv.animeflv import AnimeFLV, AnimeInfo, AnimeFLVSingleton, EpisodeInfo, ServerInfo
from dataPersistence.animesPersistence import AnimeStatus
from utils import utils
from utils.buttons import utilsButtons
from utils.utils import refactor_genre_text, get_resource_path, get_anime_image, download_anime_poster_by_status, \
    remove_anime_poster_by_status


# TODO: Al final de la lista de episodios nuevo frame del estilo. "Si te ha gustado One piece, te puede interesar..." y
#  mostrar 4 animes con los mimos generos.

class AnimeWindowViewer:
    def __init__(self, main_window, anime_info: AnimeInfo):
        self.main_window = main_window
        self.anime_info: AnimeInfo = anime_info
        self.animeflv_api: AnimeFLV = AnimeFLVSingleton()
        self.episode_switches: list = []
        self.watched_status = {episode.id: False for episode in self.anime_info.episodes}
        self.sort_descending: bool = True
        self.__anime_status_frame = None
        self.__list_episodes_frame = None
        self.__anime_is_favourite: bool = False
        self.__anime_is_finished: bool = False
        self.__anime_is_watching: bool = False
        self.__anime_is_pending: bool = False

    def display_anime_info(self):
        self.main_window.clear_frame()
        self.__load_anime_status()
        self.__display_anime_info()

    def __load_anime_status(self):
        res, anime = self.main_window.animes_persistence.get_anime_by_anime_id(self.anime_info.id)
        if not res:
            return
        if len(anime) == 0:
            return
        if len(json.loads(anime[0]["episodes"])) != len(self.anime_info.episodes):
            self.main_window.animes_persistence.update_anime_episodes(self.anime_info.id, self.anime_info.episodes)
        self.__anime_is_favourite = anime[0]["is_favourite"]
        self.__anime_is_finished = anime[0]["is_finished"]
        self.__anime_is_watching = anime[0]["is_watching"]
        self.__anime_is_pending = anime[0]["is_pending"]

    def __display_anime_info(self):
        self.main_window.clear_frame()
        time.sleep(0.1)
        # Configuración inicial del layout en content_frame
        self.main_window.content_frame.grid_rowconfigure(0, weight=1)
        self.main_window.content_frame.grid_rowconfigure(1, weight=1)
        self.main_window.content_frame.grid_rowconfigure(2, weight=1)
        self.main_window.content_frame.grid_columnconfigure(0, weight=1)
        self.main_window.content_frame.grid_columnconfigure(1, weight=4)  # Espacio más amplio para el título, sinopsis, y géneros
        self.main_window.content_frame.grid_columnconfigure(2, weight=1)  # Añadir espacio para los botones
        self.main_window.content_frame.grid_columnconfigure(3, weight=1)  # Añadir espacio para los botones

        # Cargar la imagen del póster
        anime_image = get_anime_image(self.anime_info)

        # Crear el frame para contener el póster y la información
        info_frame = ctk.CTkFrame(self.main_window.content_frame, fg_color="white")
        info_frame.grid(row=0, column=0, rowspan=3, sticky=ctk.NW, padx=10, pady=10)

        # Etiqueta para mostrar la imagen (póster)
        poster_label = ctk.CTkLabel(
            info_frame,
            text="",
            image=anime_image
        )
        #poster_label.image = anime_image  # Mantener referencia de la imagen
        poster_label.grid(row=0, column=0, rowspan=3, sticky=ctk.NW, padx=10, pady=10)

        # Etiqueta para el título del anime
        title_label = ctk.CTkLabel(
            self.main_window.content_frame,
            text=self.anime_info.title,
            font=ctk.CTkFont(size=28, weight="bold"),
            justify="left",
            anchor="w",
        )
        title_label.grid(row=0, column=1, sticky=ctk.NW, padx=5, pady=(5, 0))

        # Etiqueta para la sinopsis del anime
        synopsis_label = ctk.CTkLabel(
            self.main_window.content_frame,
            text=f"{self.anime_info.synopsis if self.anime_info.synopsis else ''}",
            font=ctk.CTkFont(size=18),
            width=self.main_window.content_frame.winfo_width() - 275,
            wraplength=self.main_window.content_frame.winfo_width() - 275,  # Mayor ancho para ocupar el espacio disponible
            justify="left",
            anchor="w"
        )
        synopsis_label.grid(row=1, column=1, sticky=ctk.NW, padx=(5, 10), pady=(10, 0))

        # Etiqueta para los géneros del anime
        genres_text = ', '.join(refactor_genre_text(genre) for genre in self.anime_info.genres)
        genres_label = ctk.CTkLabel(
            self.main_window.content_frame,
            text=f"Géneros: {genres_text}",
            font=ctk.CTkFont(size=14),
            width=self.main_window.content_frame.winfo_width() - 275,
            wraplength=self.main_window.content_frame.winfo_width() - 275,  # Mayor ancho para ocupar el espacio disponible
            justify="left",
            anchor="w"
        )
        genres_label.grid(row=2, column=1, sticky=ctk.EW, padx=(5, 10), pady=(20, 0))

        self.__show_anime_status()

    def __show_anime_status(self):
        self.__anime_status_frame = ctk.CTkFrame(self.main_window.content_frame)
        self.__anime_status_frame.grid(row=3, column=0, columnspan=4, sticky=ctk.NSEW, padx=10, pady=10)
        self.__anime_status_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.__display_anime_status()

    def __display_anime_status(self):
        for widget in self.__anime_status_frame.winfo_children():
            widget.destroy()
        favourite_button_img = utils.load_image(get_resource_path("resources/images/utils/favoritos.png"), image_size=(24, 24))
        non_favourite_button_img = utils.load_image(get_resource_path("resources/images/utils/no_favoritos.png"), image_size=(24, 24))
        favorite_botton = ctk.CTkButton(
            self.__anime_status_frame,
            text=f"Añadir a favoritos" if not self.__anime_is_favourite else f"Eliminar de favoritos",
            font=ctk.CTkFont(size=14),
            anchor="center",
            border_spacing=10,
            image=non_favourite_button_img if not self.__anime_is_favourite else favourite_button_img,
            command=self.add_to_favorites if not self.__anime_is_favourite else self.remove_from_favorites,
        )
        favorite_botton.grid(row=0, column=0, sticky=ctk.EW, padx=(5, 10), pady=(0, 5))

        finished_button_img = utils.load_image(get_resource_path("resources/images/utils/finalizados.png"), image_size=(24, 24))
        finished_button = ctk.CTkButton(
            self.__anime_status_frame,
            text=f"Añadir a finalizados" if not self.__anime_is_finished else f"Eliminar de finalizados",
            font=ctk.CTkFont(size=14),
            anchor="center",
            border_spacing=10,
            image=finished_button_img,
            command=self.add_to_finished if not self.__anime_is_finished else self.remove_from_finished,
        )
        finished_button.grid(row=0, column=1, sticky=ctk.EW, padx=(5, 10), pady=(0, 5))

        watching_button_img = utils.load_image(get_resource_path("resources/images/utils/viendo.png"), image_size=(24, 24))
        watching_button = ctk.CTkButton(
            self.__anime_status_frame,
            text=f"Añadir a viendo" if not self.__anime_is_watching else f"Eliminar de viendo",
            font=ctk.CTkFont(size=14),
            anchor="center",
            border_spacing=10,
            image=watching_button_img,
            command=self.add_to_watching if not self.__anime_is_watching else self.remove_from_watching,
        )
        watching_button.grid(row=0, column=2, sticky=ctk.EW, padx=(5, 10), pady=(0, 5))

        watching_button_img = utils.load_image(get_resource_path("resources/images/utils/pendientes.png"), image_size=(24, 24))
        pending_button = ctk.CTkButton(
            self.__anime_status_frame,
            text=f"Añadir a pendiente" if not self.__anime_is_pending else f"Eliminar de pendiente",
            font=ctk.CTkFont(size=14),
            anchor="center",
            border_spacing=10,
            image=watching_button_img,
            command=self.add_to_pending if not self.__anime_is_pending else self.remove_from_pending,
        )
        pending_button.grid(row=0, column=3, sticky=ctk.EW, padx=(5, 10), pady=(0, 5))

        self.__show_anime_episodes()

    def add_to_favorites(self):
        self.main_window.animes_persistence.update_anime_to_favourite(self.anime_info)
        download_anime_poster_by_status(AnimeStatus.FAVOURITE, self.anime_info)
        print(f"{self.anime_info.title} añadido a favoritos.")
        self.__anime_is_favourite = True
        self.__display_anime_status()

    def remove_from_favorites(self):
        self.main_window.animes_persistence.update_anime_to_not_favourite(self.anime_info.id)
        remove_anime_poster_by_status(AnimeStatus.FAVOURITE, self.anime_info)
        print(f"{self.anime_info.title} eliminado de favoritos.")
        self.__anime_is_favourite = False
        self.__display_anime_status()

    def add_to_finished(self):
        self.main_window.animes_persistence.update_anime_to_finished(self.anime_info)
        download_anime_poster_by_status(AnimeStatus.FINISHED, self.anime_info)
        print(f"{self.anime_info.title} añadido a finalizados.")
        self.__anime_is_finished = True
        self.__anime_is_watching = False
        self.__anime_is_pending = False
        self.__display_anime_status()

    def remove_from_finished(self):
        self.main_window.animes_persistence.update_anime_to_not_finished(self.anime_info.id)
        remove_anime_poster_by_status(AnimeStatus.FINISHED, self.anime_info)
        print(f"{self.anime_info.title} eliminado de finalizados.")
        self.__anime_is_finished = False
        self.__anime_is_pending = True
        self.__display_anime_status()

    def add_to_watching(self):
        self.main_window.animes_persistence.update_anime_to_watching(self.anime_info)
        download_anime_poster_by_status(AnimeStatus.WATCHING, self.anime_info)
        print(f"{self.anime_info.title} añadido a viendo.")
        self.__anime_is_finished = False
        self.__anime_is_watching = True
        self.__anime_is_pending = False
        self.__display_anime_status()

    def remove_from_watching(self):
        self.main_window.animes_persistence.update_anime_to_not_watching(self.anime_info.id)
        remove_anime_poster_by_status(AnimeStatus.WATCHING, self.anime_info)
        print(f"{self.anime_info.title} eliminado de viendo.")
        self.__anime_is_watching = False
        self.__display_anime_status()

    def add_to_pending(self):
        self.main_window.animes_persistence.update_anime_to_pending(self.anime_info)
        download_anime_poster_by_status(AnimeStatus.PENDING, self.anime_info)
        print(f"{self.anime_info.title} añadido a pendientes.")
        self.__anime_is_finished = False
        self.__anime_is_watching = False
        self.__anime_is_pending = True
        self.__display_anime_status()

    def remove_from_pending(self):
        self.main_window.animes_persistence.update_anime_to_not_pending(self.anime_info.id)
        remove_anime_poster_by_status(AnimeStatus.PENDING, self.anime_info)
        print(f"{self.anime_info.title} eliminado de pendientes.")
        self.__anime_is_pending = False
        self.__display_anime_status()

    def __show_anime_episodes(self):
        self.__list_episodes_frame = ctk.CTkFrame(self.main_window.content_frame)
        self.__list_episodes_frame.grid(row=4, column=0, columnspan=4, sticky=ctk.NSEW, pady=(10, 5), padx=10)
        self.__list_episodes_frame.grid_columnconfigure(0, weight=1)
        self.__list_episodes_frame.grid_columnconfigure(1, weight=1)
        self.__list_episodes_frame.grid_columnconfigure(2, weight=3)
        self.__list_episodes_frame.grid_columnconfigure(3, weight=1)

        self.__display_episodes()

    def __display_episodes(self, episodes_to_show: List[EpisodeInfo] = None):
        episodes_to_show = self.anime_info.episodes[:25] if episodes_to_show is None else episodes_to_show
        for widget in self.__list_episodes_frame.winfo_children():
            widget.destroy()

        self.episode_switches.clear()

        # Episodios debajo de la sinopsis, alineados a la izquierda
        episodes_label = ctk.CTkLabel(
            self.__list_episodes_frame,
            text="Lista de episodios",
            font=ctk.CTkFont(size=18, weight="bold"),
        )
        episodes_label.grid(row=0, column=0, columnspan=2, sticky=ctk.W, pady=(10, 5))

        # Botón de ordenación
        sort_button = ctk.CTkButton(
            self.__list_episodes_frame,
            text="Mayor a menor  ↓",
            font=ctk.CTkFont(size=14),
            command=lambda: self.__toggle_sort_order(sort_button)
        )
        sort_button.grid(row=0, column=3, sticky=ctk.E, padx=(5, 10), pady=(10, 5))

        # Campo de búsqueda de episodios
        self.search_entry = ctk.CTkEntry(
            self.__list_episodes_frame,
            placeholder_text="Buscar episodio...",
            font=ctk.CTkFont(size=14),
            width=150
        )
        self.search_entry.grid(row=0, column=4, sticky=ctk.E, padx=(5, 10), pady=(10, 5))
        self.search_entry.bind("<Return>", self.__search_episodes)

        servers_frames = {}

        # Solo se muestran los 24 primeros episodios
        for index, episode_info in enumerate(episodes_to_show):
            episode_button = utilsButtons.EpisodeButton(
                parent_frame=self.__list_episodes_frame,
                anime_title=self.anime_info.title,
                episode_info=episode_info,
                servers_frame=servers_frames,
                index=index,
                toggle_servers_command=self.__toggle_servers_frame
            )
            episode_button.grid(row=index + 1, column=0, sticky=ctk.W, pady=(10, 5))

            watched_episode_switch = ctk.CTkSwitch(
                self.__list_episodes_frame,
                text="Visto",
                width=80,
                command=lambda ep_id=episode_info.id: self.__toggle_episode_switch(ep_id)
            )
            watched_episode_switch.grid(row=index + 1, column=1, sticky=ctk.W, padx=(5, 10), pady=(10, 5))
            # Restaurar el estado del switch
            if self.watched_status.get(episode_info.id, False):
                watched_episode_switch.select()
            else:
                watched_episode_switch.deselect()

            # Agregar el switch a la lista de switches
            self.episode_switches.append(watched_episode_switch)

    def __display_previous_and_next_episodes(self, episode_info: EpisodeInfo):
        previous_episode_button = ctk.CTkButton(
            self.__list_episodes_frame,
            text="← Episodio anterior",
            font=ctk.CTkFont(size=14),
            anchor=ctk.W,
            border_spacing=10,
            command=lambda: self.__previous_episode(episode_info)
        )
        previous_episode_button.grid(row=2, column=1, sticky=ctk.W, pady=(30, 5))

        next_episode_button = ctk.CTkButton(
            self.__list_episodes_frame,
            text="Episodio siguiente →",
            font=ctk.CTkFont(size=14),
            anchor=ctk.E,
            border_spacing=10,
            command=lambda: self.__next_episode(episode_info)
        )
        next_episode_button.grid(row=2, column=2, sticky=ctk.E, padx=(5, 10), pady=(30, 5))

    def __toggle_sort_order(self, sort_button):
        # Cambiar el estado de orden y actualizar la lista de episodios
        self.sort_descending = not self.sort_descending
        self.anime_info.episodes.sort(
            key=lambda episode: episode.id,
            reverse=self.sort_descending
        )
        # Cambiar el texto del botón según el estado
        text = "Mayor a menor  ↓" if self.sort_descending else "Menor a mayor  ↑"
        sort_button.configure(text=text)
        self.__display_episodes()

    def __search_episodes(self, event=None):
        # Obtener el valor de búsqueda y filtrar episodios por ID
        query = self.search_entry.get().strip()
        if query.isdigit():
            query_id = int(query)
            # Filtrar la lista según el ID del episodio
            filtered_episode = [next((ep for ep in self.anime_info.episodes if ep.id == query_id), None)]
            if filtered_episode[0] is None:
                self.__display_episodes([])
            else:
                self.__display_episodes(filtered_episode)
                self.__display_previous_and_next_episodes(filtered_episode[0])
        else:
            # Mostrar todos los episodios si no se ingresa un número válido
            self.__display_episodes(self.anime_info.episodes[:25])

    def __previous_episode(self, episode_info: EpisodeInfo):
        current_index = next(i for i, ep in enumerate(self.anime_info.episodes) if ep.id == episode_info.id)
        previous_index = current_index + 1 if self.sort_descending else current_index - 1

        # Verificar que el siguiente episodio está en el rango
        if 0 <= previous_index < len(self.anime_info.episodes):
            previous_episode = self.anime_info.episodes[previous_index]
            self.__display_episodes([previous_episode])
            self.__display_previous_and_next_episodes(previous_episode)

    def __next_episode(self, episode_info: EpisodeInfo):
        current_index = next(i for i, ep in enumerate(self.anime_info.episodes) if ep.id == episode_info.id)
        next_index = current_index - 1 if self.sort_descending else current_index + 1

        # Verificar que el siguiente episodio está en el rango
        if 0 <= next_index < len(self.anime_info.episodes):
            next_episode = self.anime_info.episodes[next_index]
            self.__display_episodes([next_episode])
            self.__display_previous_and_next_episodes(next_episode)

    def __toggle_episode_switch(self, episode_id: int):
        # Encontrar el índice del episodio en anime_info.episodes usando su ID
        try:
            index = next(i for i, ep in enumerate(self.anime_info.episodes) if ep.id == episode_id)
        except StopIteration:
            print(f"Error: Episodio con ID {episode_id} no encontrado.")
            return

        # Obtener el estado actual del switch de este episodio
        current_state = self.watched_status[episode_id]

        # Cambiar el estado del episodio actual en el diccionario
        self.watched_status[episode_id] = not current_state

        # Control de switches en función del orden de clasificación
        if self.sort_descending:
            if not current_state:  # Si el episodio se marcó como "no visto"
                for i in range(index, len(self.episode_switches)):
                    ep_id = self.anime_info.episodes[i].id
                    self.watched_status[ep_id] = True
                    self.episode_switches[i].select()
            else:  # Si el episodio se marcó como "visto"
                for i in range(index + 1):
                    ep_id = self.anime_info.episodes[i].id
                    self.watched_status[ep_id] = False
                    self.episode_switches[i].deselect()
        else:
            if not current_state:  # Si el episodio se marcó como "no visto"
                for i in range(0, index):
                    ep_id = self.anime_info.episodes[i].id
                    self.watched_status[ep_id] = True
                    self.episode_switches[i].select()
            else:  # Si el episodio se marcó como "visto"
                for i in range(index + 1, len(self.episode_switches)):
                    ep_id = self.anime_info.episodes[i].id
                    self.watched_status[ep_id] = False
                    self.episode_switches[i].deselect()

    def __toggle_servers_frame(self, episode_info: EpisodeInfo, servers_frames, current_row: int):
        if episode_info.id in servers_frames:
            servers_frames[episode_info.id].destroy()
            del servers_frames[episode_info.id]
        else:
            servers_info: List[ServerInfo] = self.animeflv_api.get_anime_episode_servers(episode_info.anime,
                                                                                         episode_info.id)
            # Crear un nuevo frame solo para los servidores
            new_server_frame = ctk.CTkFrame(
                self.__list_episodes_frame,
                fg_color="transparent"
            )
            new_server_frame.grid(row=current_row + 1, column=2, columnspan=3, sticky=ctk.NSEW, padx=(5, 10), pady=(10, 5))
            # Guardar el frame de servidores en el diccionario para poder ocultarlo después
            servers_frames[episode_info.id] = new_server_frame

            server_url_map = {server.server: server.url for server in servers_info}
            server_button = ctk.CTkSegmentedButton(
                new_server_frame,
                values=list(server_url_map.keys()),
            )
            server_button.grid(row=0, column=0, sticky=ctk.EW, pady=(15, 5))
            server_button.set(None)
            server_button.configure(command=lambda selected: self.__play_video(server_url_map[selected]))

            new_server_frame.grid_columnconfigure(0, weight=1)

    def __play_video(self, url):
        webbrowser.open(url)

