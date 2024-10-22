__author__ = "Jose David Escribano Orts"
__subsystem__ = "sidebarButtons"
__module__ = "searchAnimes.py"
__version__ = "0.1"
__info__ = {"subsystem": __subsystem__, "module_name": __module__, "version": __version__}

import tkinter as tk
from typing import List

from APIs.animeflv.animeflv import AnimeFLV, AnimeGenreFilter, AnimeOrderFilter, AnimeFLVSingleton, AnimeInfo
from gui.sidebarButtons.sidebarButton import SidebarButton
from utils.buttons import utilsButtons


class SearchButton(SidebarButton):
    def __init__(self, main_window):
        super().__init__(main_window.sidebar_frame, "BUSCADOR DE ANIMES", self.__show_buscador)
        self.main_window = main_window
        self.animeflv_api: AnimeFLV = AnimeFLVSingleton()

        # Géneros de ejemplo (debes usar tu enum de géneros reales)
        self.genres = list(AnimeGenreFilter)
        self.selected_genres = []
        self.genre_vars = {genre: tk.BooleanVar() for genre in self.genres}

        self.order_options = list(AnimeOrderFilter)
        self.selected_order = tk.StringVar(value=AnimeOrderFilter.POR_DEFECTO.value)

    def show_frame(self):
        self.main_window.clear_frame()
        self.__show_buscador()

    def __show_buscador(self):
        self.main_window.clear_frame()

        # Crear un frame para el buscador
        search_frame = tk.Frame(self.main_window.content_frame)
        search_frame.grid(row=0, column=0, pady=10, padx=10)

        search_label = tk.Label(
            search_frame,
            text="Buscar Anime:",
            font=("Helvetica", 16, "bold")
        )
        search_label.grid(row=0, column=0, padx=3, pady=5, sticky="w")

        # Barra de búsqueda
        search_entry = tk.Entry(
            search_frame,
            width=90
        )
        search_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        # Botón de buscar
        search_button = utilsButtons.SearchButton(
            parent_frame=search_frame,
            search_command=self.__search_anime,
            search_entry=search_entry
        )
        search_button.grid(row=0, column=2, padx=(10, 5), pady=5, sticky="w")

        genre_filter_frame = tk.Frame(self.main_window.content_frame)
        genre_filter_frame.grid(row=1, column=0, columnspan=2, pady=10, padx=10)
        # Filtro de géneros (multiselección en 4 filas de 10 columnas)
        genre_filter_label = tk.Label(
            genre_filter_frame,
            text="Filtrar por género:",
            font=("Helvetica", 16, "bold")
        )
        genre_filter_label.grid(row=0, column=0, columnspan=2, padx=3, pady=5, sticky="w")

        for idx, (genre, var) in enumerate(self.genre_vars.items()):
            row = idx // 10
            col = idx % 10
            genre_checkButton = tk.Checkbutton(
                genre_filter_frame,
                text=self.__get_display_name(genre),
                variable=var
            )
            genre_checkButton.grid(row=row+1, column=col, padx=0, pady=2, sticky="w")

        # Filtro de ordenación (opción de multiselección en 1 fila de 3 columnas)
        order_filter_frame = tk.Frame(self.main_window.content_frame)
        order_filter_frame.grid(row=3, column=0, padx=5, pady=5, sticky="w")

        order_filter_label = tk.Label(
            order_filter_frame,
            text="Orden:",
            font=("Helvetica", 16, "bold")
        )
        order_filter_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")

        for idx, order in enumerate(self.order_options):
            row = idx // 10
            col = idx % 10
            order_radioButton = tk.Radiobutton(
                order_filter_frame,
                text=self.__get_display_name(order),
                variable=self.selected_order,
                value=order.value
            )
            order_radioButton.grid(row=row+1, column=col, padx=5, pady=2, sticky="w")

        # Botón para aplicar los filtros
        apply_filters_button = utilsButtons.ApplyFiltersButton(
            parent_frame=self.main_window.content_frame,
            apply_filter_command=self.__apply_filters
        )
        apply_filters_button.grid(row=4, column=0, columnspan=2, padx=(10, 15), pady=(10, 20), sticky="ew")


    def __get_display_name(self, enum_value):
        """Genera el nombre para mostrar en la interfaz a partir del nombre del Enum"""
        return enum_value.name.capitalize().replace("_", " ")

    def __search_anime(self, search_entry: tk.Entry):
        # Aquí iría la lógica para buscar por nombre de anime
        search_text = search_entry.get()
        #TODO: Lanzarlo en un hilo paralelo para que no se pare la aplicación
        animes_query = self.animeflv_api.search_animes_by_query(search_text)
        self.__display_animes(animes_query)

    def __apply_filters(self):
        # Obtener los valores reales de los géneros seleccionados y la ordenación
        selected_genres = [genre.value for genre, var in self.genre_vars.items() if var.get()]
        selected_order = self.selected_order.get()
        # TODO: Lanzarlo en un hilo paralelo para que no se pare la aplicación
        animes_filter = self.animeflv_api.search_animes_by_genres_and_order(selected_genres, selected_order)
        self.__display_animes(animes_filter)

    def __display_animes(self, animes: List[AnimeInfo]):
        episodios_filter_frame = tk.Frame(self.main_window.content_frame)
        episodios_filter_frame.grid(row=5, column=0, padx=5, pady=10, sticky="w")

        episodios_filter_label = tk.Label(
            episodios_filter_frame,
            text="Lista de animes:",
            font=("Helvetica", 16, "bold")
        )
        episodios_filter_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")