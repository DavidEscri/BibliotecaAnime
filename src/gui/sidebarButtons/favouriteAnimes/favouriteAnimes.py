__author__ = "Jose David Escribano Orts"
__subsystem__ = "sidebarButtons"
__module__ = "favouriteAnimes.py"
__version__ = "0.2"
__info__ = {"subsystem": __subsystem__, "module_name": __module__, "version": __version__}

import os
import time
import customtkinter as ctk

from typing import List, Union

from APIs.common.animeProviderMgr import AnimeProviderManager, AnimeProviderManagerSingleton
from dataPersistence.animesPersistence import AnimesPersistence, AnimesPersistenceSingleton, AnimeStatus, AnimeRecord
from gui.anime_window import open_saved_anime
from utils.buttons import utilsButtons
from utils.utils import load_image, get_resource_path


class FavouritesButton(utilsButtons.SidebarButton):
    def __init__(self, main_window, icon_path, row, column):
        icon_path_light = icon_path_dark = os.path.join(icon_path, "favoritos.png")
        super().__init__(main_window.sidebar_frame, "ANIMES FAVORITOS", row, column, self.__show_favorites, icon_path_light, icon_path_dark)

        self.main_window = main_window
        self.anime_provider_mgr: AnimeProviderManager = AnimeProviderManagerSingleton()
        self.animes_persistence: AnimesPersistence = AnimesPersistenceSingleton()
        self.__episodes_frame: ctk.CTkFrame = None
        # Buscador de la pestaña: coincidencias locales al instante, completadas
        # después con lo que encuentre el proveedor seleccionado.
        self.__search = utilsButtons.SavedAnimeSearch(
            main_window=main_window,
            anime_provider_mgr=self.anime_provider_mgr,
            get_saved_animes=self.animes_persistence.get_favourite_animes,
            display_animes=self.__display_animes,
            is_still_visible=lambda: (self.__episodes_frame is not None and self.__episodes_frame.winfo_exists())
        )

    def show_frame(self):
        self.main_window.clear_frame()
        self.__show_favorites()

    def __show_favorites(self):
        self.main_window.clear_frame()
        time.sleep(0.1)
        self.__show_browser()

    def __show_browser(self):
        search_frame = ctk.CTkFrame(self.main_window.content_frame)
        search_frame.grid(row=0, column=0, columnspan=3, pady=(10, 5), padx=5)

        search_label = ctk.CTkLabel(
            search_frame,
            text="Buscar Anime:",
            font=ctk.CTkFont(size=20, weight="bold"),
            anchor=ctk.W
        )
        search_label.grid(row=0, column=0, padx=3, pady=5, sticky=ctk.W)

        # Barra de búsqueda
        search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="Buscar mi anime favorito...",
            width=self.main_window.content_frame.winfo_width() - 340,
        )
        search_entry.grid(row=0, column=1, padx=5, pady=5, sticky=ctk.W)

        # Botón de buscar
        search_button = utilsButtons.SearchButton(
            parent_frame=search_frame,
            search_command=self.__search_anime,
            search_entry=search_entry
        )
        search_button.grid(row=0, column=2, padx=(10, 5), pady=5, sticky=ctk.W)

        accordion_filter_button: utilsButtons.AccordionFilterButton = utilsButtons.AccordionFilterButton(
            status=AnimeStatus.FAVOURITE,
            parent_frame=self.main_window.content_frame,
            title="Abrir filtro de animes",
            cb_display_anime=self.__display_animes
        )

        self.__display_animes(self.animes_persistence.get_favourite_animes())

    def __search_anime(self, search_entry: ctk.CTkEntry):
        # Las dos búsquedas se suman: la local no depende del proveedor y la
        # del proveedor encuentra alias que el título guardado no conoce
        # ("Solo Leveling" -> "Ore dake Level Up na Ken"). Ver SavedAnimeSearch.
        self.__search.search(search_entry.get())

    def __display_animes(self, favourite_animes: List[AnimeRecord]):
        if self.__episodes_frame is not None and self.__episodes_frame.winfo_exists():
            for widget in self.__episodes_frame.winfo_children():
                widget.destroy()
            self.__episodes_frame.destroy()
        self.__episodes_frame = ctk.CTkFrame(self.main_window.content_frame)
        self.__episodes_frame.grid(row=5, column=0, padx=10, pady=10, sticky=ctk.EW)

        num_columns = max(1, self.main_window.content_frame.winfo_width() // 150)
        for index, anime_record in enumerate(favourite_animes):
            row = index // num_columns
            column = index % num_columns

            image = load_image(get_resource_path(f"resources/images/favourite/{anime_record.anime_id}.jpg"))

            img_label = ctk.CTkLabel(
                self.__episodes_frame,
                text="",
                image=image
            )
            img_label.grid(row=row * 3, column=column, padx=10, pady=(20, 0), sticky=ctk.NSEW)
            img_label.bind("<Button-1>", lambda e, anime_id=anime_record.anime_id: self.__on_anime_click(anime_id))

            # Título del anime
            title_label = ctk.CTkLabel(
                self.__episodes_frame,
                text=anime_record.title,
                font=ctk.CTkFont(size=14),
                wraplength=120,
                justify="center"
            )
            title_label.grid(row=(row * 3) + 1, column=column, padx=10, pady=(5, 0), sticky=ctk.N)

            provider_label = ctk.CTkLabel(
                self.__episodes_frame,
                text=(self.anime_provider_mgr.get_provider_name(anime_record.provider_id) if anime_record.provider_id is not None else ""),
                font=ctk.CTkFont(size=11),
                text_color=("gray45", "gray60"),
                justify="center"
            )
            provider_label.grid(row=(row * 3) + 2, column=column, padx=10, pady=(0, 10), sticky=ctk.N)

    def __on_anime_click(self, anime_id: Union[str, int]):
        # Es un anime de la biblioteca: el proveedor sale de su fila y la petición
        # va en un hilo aparte. Ambas cosas viven en open_saved_anime() porque las
        # cuatro vistas de estado hacen exactamente esto mismo.
        open_saved_anime(self.main_window, anime_id)


