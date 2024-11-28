__author__ = "Jose David Escribano Orts"
__subsystem__ = "sidebarButtons"
__module__ = "finishedAnimes.py"
__version__ = "0.1"
__info__ = {"subsystem": __subsystem__, "module_name": __module__, "version": __version__}

import os
import time
from typing import List, Union

import customtkinter as ctk

from APIs.animeflv.animeflv import AnimeFLV, AnimeFLVSingleton, AnimeInfo
from dataPersistence.animesPersistence import AnimesPersistence, AnimesPersistenceSingleton, AnimeStatus
from gui.anime_window import AnimeWindowViewer
from utils.buttons import utilsButtons
from utils.utils import load_image, get_resource_path


class FinishedAnimeButton(utilsButtons.SidebarButton):
    def __init__(self, main_window, icon_path, row, column):
        icon_path_light = icon_path_dark = os.path.join(icon_path, "finalizados.png")
        super().__init__(main_window.sidebar_frame, "ANIMES FINALIZADOS", row, column, self.show_finished_animes,
                         icon_path_light, icon_path_dark)
        self.main_window = main_window
        self.animeflv_api: AnimeFLV = AnimeFLVSingleton()
        self.animes_persistence: AnimesPersistence = AnimesPersistenceSingleton()
        self.__episodes_frame: ctk.CTkFrame = None

    def show_frame(self):
        self.main_window.clear_frame()
        self.show_finished_animes()

    def show_finished_animes(self):
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
            placeholder_text="Buscar entre mis animes terminados...",
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
            status=AnimeStatus.FINISHED,
            parent_frame=self.main_window.content_frame,
            title="Abrir filtro de animes",
            cb_display_anime=self.__display_animes
        )

        self.__display_animes(self.animes_persistence.get_finished_animes())

    def __search_anime(self, search_entry: ctk.CTkEntry):
        search_text = search_entry.get()
        if len(search_text) == 0:
            self.__display_animes(self.animes_persistence.get_finished_animes())
            return
        query_animes: List[AnimeInfo] = self.animeflv_api.search_animes_by_query(search_text)[0]
        if len(query_animes) == 0:
            print("No se encontró ningún anime")
            return
        list_finished_animes = []
        for anime in query_animes:
            res, finished_anime = self.animes_persistence.get_anime_by_anime_id(anime.id)
            if not res or len(finished_anime) == 0:
                continue
            if not finished_anime[0]["is_finished"]:
                continue
            print(f"{finished_anime[0]['title']} encontrado entre mis animes terminados")
            list_finished_animes.append(finished_anime[0])
        self.__display_animes(list_finished_animes)

    def __display_animes(self, finished_animes: List[dict]):
        if self.__episodes_frame is not None and self.__episodes_frame.winfo_exists():
            for widget in self.__episodes_frame.winfo_children():
                widget.destroy()
            self.__episodes_frame.destroy()
        self.__episodes_frame = ctk.CTkFrame(self.main_window.content_frame)
        self.__episodes_frame.grid(row=5, column=0, padx=10, pady=10, sticky=ctk.EW)

        num_columns = max(1, self.main_window.content_frame.winfo_width() // 150)
        for index, anime in enumerate(finished_animes):
            row = index // num_columns
            column = index % num_columns

            image = load_image(get_resource_path(f"resources/images/finished/{anime['anime_id']}.jpg"))

            img_label = ctk.CTkLabel(
                self.__episodes_frame,
                text="",
                image=image
            )
            img_label.grid(row=row * 2, column=column, padx=10, pady=(20, 0), sticky=ctk.NSEW)
            img_label.bind("<Button-1>", lambda e, anime_id=anime['anime_id']: self.__on_anime_click(anime_id))

            # Título del anime
            title_label = ctk.CTkLabel(
                self.__episodes_frame,
                text=anime["title"],
                font=ctk.CTkFont(size=14),
                wraplength=120,
                justify="center"
            )
            title_label.grid(row=(row * 2) + 1, column=column, padx=10, pady=(5, 10), sticky=ctk.N)

    def __on_anime_click(self, anime_id: Union[str, int]):
        anime_clicked: AnimeInfo = self.animeflv_api.get_anime_info(anime_id)
        anime_viewer = AnimeWindowViewer(self.main_window, anime_clicked)
        anime_viewer.display_anime_info()