import os
from typing import List

from PIL import Image

from APIs.animeflv.animeflv import AnimeGenreFilter, AnimeOrderFilter, AnimeInfo
from dataPersistence.animesPersistence import AnimeStatus, AnimesPersistenceSingleton, AnimesPersistence
from utils.utils import load_image, refactor_genre_text
import customtkinter as ctk

class BaseButton(ctk.CTkButton):
    def __init__(self, parent_frame, text, command, **kwargs):
        super().__init__(
            parent_frame,
            text=text,
            command=command,
            **kwargs
        )


class EpisodeButton(BaseButton):
    def __init__(self, parent_frame, anime_title, episode_info, servers_frame, index, toggle_servers_command):
        super().__init__(
            parent_frame,
            text=f"{anime_title} - Episodio {episode_info.id}",
            command=lambda: toggle_servers_command(episode_info, servers_frame, index),
            height=40,
            font=ctk.CTkFont(size=14),
            anchor=ctk.W,
            border_spacing=20
        )


class SearchButton(BaseButton):
    def __init__(self, parent_frame, search_command, search_entry):
        super().__init__(
            parent_frame,
            text="Buscar",
            command=lambda: search_command(search_entry),
            font=ctk.CTkFont(size=14)
        )


class ApplyFiltersButton(BaseButton):
    def __init__(self, parent_frame, apply_filter_command):
        super().__init__(
            parent_frame,
            text="Aplicar Filtros",
            command=apply_filter_command,
            font=ctk.CTkFont(size=14)
        )


class SidebarButton(BaseButton):
    def __init__(self, parent_frame, text, row, column, command, icon_path_light, icon_path_dark):
        self.icon_light = load_image(icon_path_light, image_size=(24, 24))
        self.icon_dark = load_image(icon_path_dark, image_size=(24, 24))
        current_icon = self.icon_dark if ctk.get_appearance_mode() == "Dark" else self.icon_light
        super().__init__(
            parent_frame,
            text=" " + text,
            font=ctk.CTkFont(size=14),
            width=parent_frame.winfo_width(),
            height=parent_frame.winfo_height() - 150,
            fg_color=parent_frame.cget("fg_color"),
            text_color="black",
            image=current_icon,
            compound="left",
            corner_radius=0,
            hover_color="white",
            command=command,
        )
        self.grid(row=row, column=column, sticky="nsew")

    def update_icon(self, mode):
        new_icon = self.icon_dark if mode == "Dark" else self.icon_light
        self.configure(image=new_icon)

    def show_frame(self):
        raise NotImplementedError("Subclasses must implement this method")

class AccordionFilterButton:
    def __init__(self, parent_frame, title, status: AnimeStatus, cb_display_anime: callable):
        self.animes_persistence: AnimesPersistence = AnimesPersistenceSingleton()
        self.parent_frame = parent_frame
        self.anime_status: AnimeStatus = status
        self.display_animes_callback = cb_display_anime
        self.is_expanded = False

        anime_genres: List[AnimeGenreFilter] = list(AnimeGenreFilter)
        self.selected_genres = []
        self.genre_vars = {genre: ctk.BooleanVar() for genre in anime_genres}
        self.order_options: List[AnimeOrderFilter] = list(AnimeOrderFilter)
        self.selected_order = ctk.StringVar(value=AnimeOrderFilter.POR_DEFECTO.value)

        self.__toggle_button = ctk.CTkButton(
            self.parent_frame,
            text=title,
            command=self.toggle_content,
            font=ctk.CTkFont(size=16, weight="bold"),
            width=self.parent_frame.winfo_width()
        )
        self.__toggle_button.grid(row=1, column=0, padx=18, pady=(15, 0), sticky=ctk.EW)
        self.filter_frame: ctk.CTkFrame = None

    def toggle_content(self):
        if self.is_expanded:
            self.__toggle_button.configure(text="Abrir filtro de animes")
            self.__collapse_content()
        else:
            self.__toggle_button.configure(text="Cerrar filtro de animes")
            self.__expand_content()

    def __collapse_content(self):
        """Colapsa el contenido."""
        self.filter_frame.grid_forget()
        self.is_expanded = False

    def __expand_content(self):
        self.filter_frame = ctk.CTkFrame(
            self.parent_frame,
            width=self.parent_frame.winfo_width()
        )
        # self.filter_frame.grid_propagate(False) # Evitar que cambie de tamaño con el contenido
        self.filter_frame.grid(row=2, column=0, padx=18, pady=(0, 10), sticky=ctk.EW)

        genre_filter_frame = ctk.CTkFrame(self.filter_frame)
        genre_filter_frame.grid(row=0, column=0, columnspan=2)
        # Filtro de géneros (multiselección en 4 filas de 10 columnas)
        genre_filter_label = ctk.CTkLabel(
            genre_filter_frame,
            text="Filtrar por género:",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        genre_filter_label.grid(row=0, column=0, columnspan=2, padx=3, pady=5, sticky=ctk.W)

        for idx, (genre, var) in enumerate(self.genre_vars.items()):
            row = idx // 10
            col = idx % 10
            genre_checkButton = ctk.CTkCheckBox(
                genre_filter_frame,
                text=refactor_genre_text(genre.value),
                variable=var
            )
            genre_checkButton.grid(row=row + 1, column=col, padx=(3, 8), pady=2, sticky=ctk.W)

        # Filtro de ordenación (opción de multiselección en 1 fila de 3 columnas)
        order_filter_frame = ctk.CTkFrame(self.filter_frame)
        order_filter_frame.grid(row=3, column=0, columnspan=2, sticky=ctk.EW)

        order_filter_label = ctk.CTkLabel(
            order_filter_frame,
            text="Orden:",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        order_filter_label.grid(row=0, column=0, padx=5, pady=5, sticky=ctk.W)

        for idx, order in enumerate(self.order_options):
            row = idx // 10
            col = idx % 10
            order_radioButton = ctk.CTkRadioButton(
                order_filter_frame,
                text=refactor_genre_text(order.name),
                variable=self.selected_order,
                value=order.value
            )
            order_radioButton.grid(row=row + 1, column=col, padx=5, pady=(2, 4), sticky=ctk.EW)

        apply_filters_button = ctk.CTkButton(
            self.filter_frame,
            text="Aplicar Filtros",
            command=self.__apply_filters,
            font=ctk.CTkFont(size=14),
        )
        apply_filters_button.grid(row=4, column=0, columnspan=2, pady=(0, 5), sticky=ctk.EW)

        self.is_expanded = True

    def __apply_filters(self):
        self.selected_genres = [genre for genre, var in self.genre_vars.items() if var.get()]
        res, filter_animes = self.animes_persistence.get_anime_by_genre_and_order(
            self.anime_status,
            self.selected_genres,
            self.selected_order.get()
        )
        if not res or len(filter_animes) == 0:
            print("No se encontró ningún anime")
            return
        for anime in filter_animes:
            print(f"{anime['title']} encontrado entre mis animes {self.anime_status.name}")
        self.__display_animes(filter_animes)

    def __display_animes(self, anime_list: List[AnimeInfo]):
        self.display_animes_callback(anime_list)