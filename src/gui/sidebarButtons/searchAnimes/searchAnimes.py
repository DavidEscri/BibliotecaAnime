__author__ = "Jose David Escribano Orts"
__subsystem__ = "sidebarButtons"
__module__ = "searchAnimes.py"
__version__ = "0.1"
__info__ = {"subsystem": __subsystem__, "module_name": __module__, "version": __version__}

import os
import threading
import time

import customtkinter as ctk
from typing import List, Union

from PIL import Image, ImageSequence
from attr import dataclass

from APIs.animeflv.animeflv import AnimeFLV, AnimeGenreFilter, AnimeOrderFilter, AnimeFLVSingleton, AnimeInfo
from gui.anime_window import AnimeWindowViewer
from utils.buttons import utilsButtons
from utils.utils import refactor_genre_text, load_image, get_resource_path, download_animes_poster


@dataclass
class AnimeSearch:
    animes: List[AnimeInfo]
    last_page: int
    current_page: int = 1
    text_query: str = None
    genre_filters: List[AnimeGenreFilter] = None
    order_filter: str = None


class SearchButton(utilsButtons.SidebarButton):
    def __init__(self, main_window, icon_path, row, column):
        icon_path_light = icon_path_dark = os.path.join(icon_path, "buscar.png")
        super().__init__(main_window.sidebar_frame, "BUSCADOR DE ANIMES", row, column, self.__show_buscador,
                         icon_path_light, icon_path_dark)
        self.main_window = main_window
        self.animeflv_api: AnimeFLV = AnimeFLVSingleton()

        self.__episodes_filter_frame: ctk.CTkFrame = None
        self.__pagination_frame: ctk.CTkFrame = None

        # Géneros de ejemplo (debes usar tu enum de géneros reales)
        anime_genres: List[AnimeGenreFilter] = list(AnimeGenreFilter)
        self.selected_genres = []
        self.genre_vars = {genre: ctk.BooleanVar() for genre in anime_genres}

        self.order_options: List[AnimeOrderFilter] = list(AnimeOrderFilter)
        self.selected_order = ctk.StringVar(value=AnimeOrderFilter.POR_DEFECTO.value)
        self.__current_search_thread: threading.Thread = None
        self.__loading_frame: ctk.CTkFrame = None

    def save_anime_search(self, anime_list: List[AnimeInfo], last_page: int, current_page: int, text_query: str):
        self.main_window.last_search_instance = AnimeSearch(
            animes=anime_list,
            last_page=last_page,
            current_page=current_page,
            text_query=text_query,
            genre_filters=self.selected_genres,
            order_filter=self.selected_order.get()
        )

    def show_frame(self):
        self.main_window.clear_frame()
        self.__show_buscador()

    def __show_buscador(self):
        self.main_window.clear_frame()
        time.sleep(0.1)

        # Crear un frame para el buscador
        search_frame = ctk.CTkFrame(self.main_window.content_frame)
        search_frame.grid(row=0, column=0, columnspan=3, pady=10, padx=5)

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

        genre_filter_frame = ctk.CTkFrame(self.main_window.content_frame)
        genre_filter_frame.grid(row=1, column=0, columnspan=2, pady=10, padx=10)
        # Filtro de géneros (multiselección en 4 filas de 10 columnas)
        genre_filter_label = ctk.CTkLabel(
            genre_filter_frame,
            text="Filtrar por género:",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        genre_filter_label.grid(row=0, column=0, columnspan=2, padx=3, pady=5, sticky="w")

        for idx, (genre, var) in enumerate(self.genre_vars.items()):
            row = idx // 10
            col = idx % 10
            genre_checkButton = ctk.CTkCheckBox(
                genre_filter_frame,
                text=refactor_genre_text(genre.value),
                variable=var
            )
            genre_checkButton.grid(row=row+1, column=col, padx=6, pady=2, sticky="w")

        # Filtro de ordenación (opción de multiselección en 1 fila de 3 columnas)
        order_filter_frame = ctk.CTkFrame(self.main_window.content_frame)
        order_filter_frame.grid(row=3, column=0, padx=5, pady=5, sticky="w")

        order_filter_label = ctk.CTkLabel(
            order_filter_frame,
            text="Orden:",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        order_filter_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")

        for idx, order in enumerate(self.order_options):
            row = idx // 10
            col = idx % 10
            order_radioButton = ctk.CTkRadioButton(
                order_filter_frame,
                text=refactor_genre_text(order.name),
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

        if self.main_window.last_search_instance is not None:
            self.selected_genres = self.main_window.last_search_instance.genre_filters
            self.selected_order.set(self.main_window.last_search_instance.order_filter)
            self.__display_animes(
                animes=self.main_window.last_search_instance.animes,
                last_page=self.main_window.last_search_instance.last_page,
                current_page=self.main_window.last_search_instance.current_page,
                text_query=self.main_window.last_search_instance.text_query
            )

    def __search_anime(self, search_entry: ctk.CTkEntry):
        if self.__current_search_thread and self.__current_search_thread.is_alive():
            return
        search_text = search_entry.get()
        self.__show_loading_frame(text_entry=search_text)

    def __apply_filters(self):
        if self.__current_search_thread and self.__current_search_thread.is_alive():
            return
        self.selected_genres = [genre for genre, var in self.genre_vars.items() if var.get()]
        self.__show_loading_frame()

    def __show_loading_frame(self, text_entry: str = None, page: int = 1):
        if self.__loading_frame is not None and self.__loading_frame.winfo_exists():
            self.__loading_frame.grid_forget()
        if self.__episodes_filter_frame is not None and self.__episodes_filter_frame.winfo_exists():
            self.__episodes_filter_frame.grid_forget()
        if self.__pagination_frame is not None and self.__pagination_frame.winfo_exists():
            self.__pagination_frame.grid_forget()

        self.__loading_frame = ctk.CTkFrame(self.main_window.content_frame)
        self.__loading_frame.grid(row=6, column=0, columnspan=3, padx=5, pady=10, sticky="ew")

        # Mostrar el texto de "Cargando biblioteca de anime"
        loading_label = ctk.CTkLabel(
            self.__loading_frame,
            text="Buscando animes...",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        loading_label.pack(pady=20)

        # Cargar y mostrar el GIF con todos los frames
        loading_image_path = get_resource_path("resources/images/utils/loading-image.gif")
        gif_image = Image.open(loading_image_path)
        gif_frames = [ctk.CTkImage(frame.copy(), size=(300, 300)) for frame in ImageSequence.Iterator(gif_image)]
        loading_image_label = ctk.CTkLabel(self.__loading_frame, text="")
        loading_image_label.pack(pady=20)

        def update_gif(frame=0):
            if self.__loading_frame and self.__loading_frame.winfo_exists() and loading_image_label.winfo_exists():
                loading_image_label.configure(image=gif_frames[frame])
                frame = (frame + 1) % len(gif_frames)  # Continuar en bucle
                self.after(100, update_gif, frame)  # Controla la velocidad de cambio de frame (100 ms)

        update_gif()

        if text_entry == "" or text_entry is not None:
            self.__current_search_thread = threading.Thread(
                target=self.__search_anime_by_query,
                args=(text_entry, page,),
                daemon=True
            ).start()
        else:
            self.__current_search_thread = threading.Thread(
                target=self.__search_anime_by_filter,
                args=(page,),
                daemon=True
            ).start()

    def __search_anime_by_query(self, text_entry: str, page: int = 1):
        animes_query, last_page = self.animeflv_api.search_animes_by_query(text_entry, page)
        self.__display_animes(animes_query, last_page, current_page=page, text_query=text_entry)

    def __search_anime_by_filter(self, page: int = 1):
        animes_filter, last_page = self.animeflv_api.search_animes_by_genres_and_order(self.selected_genres, self.selected_order.get(), page)
        self.__display_animes(animes_filter, last_page, current_page=page)

    def __display_animes(self, animes: List[AnimeInfo], last_page: int, current_page: int = 1, text_query: str = None):
        self.save_anime_search(anime_list=animes, last_page=last_page, current_page=current_page, text_query=text_query)

        search_images_path = get_resource_path("resources/images/search")
        download_animes_poster(search_images_path, animes)

        if self.__loading_frame is not None and self.__loading_frame.winfo_exists():
            self.__loading_frame.grid_forget()
        if self.__pagination_frame is not None and self.__pagination_frame.winfo_exists():
            self.__pagination_frame.grid_forget()

        self.__episodes_filter_frame = ctk.CTkFrame(self.main_window.content_frame)
        self.__episodes_filter_frame.grid(row=5, column=0, padx=5, pady=10, sticky="w")

        num_columns = max(1, self.main_window.content_frame.winfo_width() // 150)
        for index, anime in enumerate(animes):
            row = index // num_columns
            column = index % num_columns

            img_file = f"{anime.id}.jpg"
            image = load_image(os.path.join(search_images_path, img_file))

            img_label = ctk.CTkLabel(
                self.__episodes_filter_frame,
                text="",
                image=image
            )
            img_label.grid(row=row * 2, column=column, padx=10, pady=(20, 0), sticky=ctk.NSEW)  # Posicionar con relleno
            img_label.bind("<Button-1>", lambda e, anime_id=anime.id: self.__on_anime_click(anime_id))

            # Título del anime
            title_label = ctk.CTkLabel(
                self.__episodes_filter_frame,
                text=anime.title,
                font=ctk.CTkFont(size=14),
                wraplength=120,
                justify="center"
            )
            title_label.grid(row=(row * 2) + 1, column=column, padx=10, pady=(5, 10), sticky=ctk.N)  # Posicionar con relleno

        self.__display_pagination_buttons(last_page, current_page, text_query)

    def __display_pagination_buttons(self, last_page: int, current_page: int, text_query: str):
        # Frame de paginación
        self.__pagination_frame = ctk.CTkFrame(self.main_window.content_frame)
        self.__pagination_frame.grid(row=6, column=0, columnspan=3, padx=5, pady=5, sticky="ew")

        total_columns = 8  # Anterior (1), Primera pagina (2), Intermedias paginas (3-6), Ultima pagina (7), Siguiente (8)
        for i in range(total_columns):
            self.__pagination_frame.grid_columnconfigure(i, weight=1)

        # Botón de página anterior
        prev_button = ctk.CTkButton(
            self.__pagination_frame,
            text="« Anterior",
            state="disabled" if current_page == 1 else "normal",
            command=lambda: self.__load_page(current_page - 1, text_query)
        )
        prev_button.grid(row=0, column=0, padx=(10, 5), pady=5, sticky="ew")

        # Botón de primera página
        first_page_button = ctk.CTkButton(
            self.__pagination_frame,
            text="1",
            state="disabled" if current_page == 1 else "normal",
            command=lambda: self.__load_page(1, text_query)
        )
        first_page_button.grid(row=0, column=1, padx=(5, 30), pady=5, sticky="ew")

        # Páginas intermedias
        start_page = max(2, current_page)
        end_page = min(start_page + 3, last_page - 1)
        col_index = 2
        for page in range(start_page, end_page + 1):
            page_button = ctk.CTkButton(
                self.__pagination_frame,
                text=str(page),
                state="disabled" if page == current_page else "normal",
                command=lambda p=page: self.__load_page(p, text_query)
            )
            page_button.grid(row=0, column=col_index, padx=5, pady=5, sticky="ew")
            col_index += 1

        # Botón de última página
        last_page_button = ctk.CTkButton(
            self.__pagination_frame,
            text=str(last_page),
            state="disabled" if current_page == last_page else "normal",
            command=lambda: self.__load_page(last_page, text_query)
        )
        last_page_button.grid(row=0, column=6, padx=(30, 5), pady=5, sticky="ew")

        # Botón de página siguiente
        next_button = ctk.CTkButton(
            self.__pagination_frame,
            text="Siguiente »",
            state="disabled" if current_page == last_page else "normal",
            command=lambda: self.__load_page(current_page + 1, text_query)
        )
        next_button.grid(row=0, column=7, padx=(5, 10), pady=5, sticky="ew")

    def __load_page(self, page: int, text_query: str):
        if self.__current_search_thread and self.__current_search_thread.is_alive():
            return
        self.__current_search_thread = threading.Thread(
            target=self.__search_and_display_animes,
            args=(page, text_query),
            daemon=True
        ).start()

    def __search_and_display_animes(self, page, text_query: str = None):
        self.__show_loading_frame(text_entry=text_query, page=page)

    def __on_anime_click(self, anime_id: Union[str, int]):
        # Reemplazar el anime en la lista
        anime_clicked: AnimeInfo = self.animeflv_api.get_anime_info(anime_id)
        anime_viewer = AnimeWindowViewer(self.main_window, anime_clicked)
        anime_viewer.display_anime_info()