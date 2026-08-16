__author__ = "Jose David Escribano Orts"
__subsystem__ = "utils.buttons"
__module__ = "utilsButtons.py"
__version__ = "0.2"
__info__ = {"subsystem": __subsystem__, "module_name": __module__, "version": __version__}

import difflib
import threading
from typing import List, Callable, Optional

from APIs.common.animeProviderMgr import AnimeProviderManager
from APIs.common.models import AnimeGenreFilter, AnimeOrderFilter, AnimeInfo
from dataPersistence.animesPersistence import AnimeStatus, AnimesPersistenceSingleton, AnimesPersistence, AnimeRecord
from utils.utils import load_image, refactor_genre_text
import customtkinter as ctk

#: Parecido mínimo para dar por buena una coincidencia que NO es subcadena. Solo
#: sirve para tolerar erratas ("dandandan" → "Dandadan"); lo demás ya lo pilla la
#: subcadena, así que se pone alto para no devolver animes que no vienen a cuento.
TITLE_SEARCH_THRESHOLD = 0.8


def filter_animes_by_title(anime_records: List[AnimeRecord], query: str) -> List[AnimeRecord]:
    """Filtra animes **ya guardados** por su título, sin red y sin mirar el proveedor.

    Buscar dentro de la biblioteca no puede depender de qué sitio esté
    seleccionado.

    Se compara sobre el título normalizado (minúsculas, sin tildes, sin signos),
    con la misma normalización que se usa para reconocer un anime entre sitios
    distintos. Coincide si la consulta aparece **dentro** del título —así "One
    Piece" devuelve también "One Piece Film: Red"— y, si no, se admite un parecido
    alto para tolerar erratas.

    :param anime_records: filas ya filtradas por estado (favoritos, viendo, …).
    :param query: texto tal cual lo escribió el usuario. Vacío devuelve todo.
    :return: las filas que coinciden, en el mismo orden en que llegaron.
    """
    normalized_query = AnimeProviderManager.normalize_title(query)
    if not normalized_query:
        return list(anime_records)

    matches: List[AnimeRecord] = []
    for anime_record in anime_records:
        normalized_title = AnimeProviderManager.normalize_title(anime_record.title)
        if normalized_query in normalized_title:
            matches.append(anime_record)
            continue
        if difflib.SequenceMatcher(None, normalized_query, normalized_title).ratio() >= TITLE_SEARCH_THRESHOLD:
            matches.append(anime_record)
    return matches


def match_animes_from_search(anime_records: List[AnimeRecord],
                             search_results: List[AnimeInfo]) -> List[AnimeRecord]:
    """Traduce resultados de una búsqueda web a los animes guardados que les corresponden.

    Empareja primero por *slug* y, si no, por título normalizado. Hacen falta las
    dos vías: el slug solo coincide cuando la fila la guardó el mismo proveedor
    que acaba de responder, mientras que el título vale entre sitios distintos —es
    el mismo criterio con el que ``resolve_anime_in_provider`` reconoce un anime
    en otro proveedor, y se usa su mismo umbral—.

    :param anime_records: filas guardadas de la pestaña (ya filtradas por estado).
    :param search_results: lo que ha devuelto el proveedor.
    :return: las filas guardadas que corresponden, sin repetidos y en el orden en
        que las devolvió el proveedor. Los resultados que no estén guardados se
        descartan: estas pestañas muestran la biblioteca, no el catálogo.
    """
    if not search_results:
        return []

    records_by_slug = {str(record.anime_id): record for record in anime_records}
    matches: List[AnimeRecord] = []
    already_matched = set()
    for result in search_results:
        record: Optional[AnimeRecord] = records_by_slug.get(str(result.id))
        if record is None:
            normalized_result = AnimeProviderManager.normalize_title(result.title)
            for candidate in anime_records:
                normalized_candidate = AnimeProviderManager.normalize_title(candidate.title)
                if (normalized_candidate == normalized_result
                        or difflib.SequenceMatcher(None, normalized_result, normalized_candidate).ratio() >= AnimeProviderManager.TITLE_MATCH_THRESHOLD):
                    record = candidate
                    break
        if record is not None and record.anime_id not in already_matched:
            already_matched.add(record.anime_id)
            matches.append(record)
    return matches


class SavedAnimeSearch:
    """Buscador de una pestaña de la biblioteca: local al instante, web al llegar.

    Las dos búsquedas resuelven cosas distintas y por eso se suman en vez de
    elegir una:

    - La **local** compara con los títulos ya guardados. Es instantánea, funciona
      sin conexión y no depende del proveedor seleccionado, que es lo que impedía
      encontrar One Piece por estar guardado con el slug de AnimeFLV.
    - La **web** pregunta al proveedor y encuentra lo que un título guardado no
      puede saber: que "Solo Leveling" es "Ore dake Level Up na Ken".

    La búsqueda web va **sin fallback** (``strict=True``): manda el proveedor
    seleccionado en ese momento y, si no encuentra nada, no se disimula con otro.

    Lo local se pinta antes de salir a la red y lo de la web se añade después, ya
    en el hilo de Tkinter: así el buscador responde al instante y **nunca quita**
    resultados, solo puede añadirlos.
    """

    def __init__(self, main_window, anime_provider_mgr: AnimeProviderManager,
                 get_saved_animes: Callable[[], List[AnimeRecord]],
                 display_animes: Callable[[List[AnimeRecord]], None],
                 is_still_visible: Callable[[], bool]):
        """
        :param main_window: hub, solo para devolver el resultado con ``after()``.
        :param get_saved_animes: devuelve las filas de esta pestaña (ya por estado).
        :param display_animes: repinta la rejilla con la lista que se le pase.
        :param is_still_visible: si la pestaña sigue en pantalla. Sin esto, una
            búsqueda lenta repintaría encima de la vista a la que ya has cambiado.
        """
        self.__main_window = main_window
        self.__anime_provider_mgr = anime_provider_mgr
        self.__get_saved_animes = get_saved_animes
        self.__display_animes = display_animes
        self.__is_still_visible = is_still_visible
        self.__generation = 0

    def search(self, search_text: str) -> None:
        saved_animes = self.__get_saved_animes()
        local_matches = filter_animes_by_title(saved_animes, search_text)
        self.__display_animes(local_matches)

        self.__generation += 1
        generation = self.__generation
        if not AnimeProviderManager.normalize_title(search_text):
            return                      # sin texto ya se muestra todo: nada que buscar

        def _merge(extra_animes: List[AnimeRecord]):
            """Ya en el hilo de Tkinter."""
            if generation != self.__generation or not self.__is_still_visible():
                return
            known = {record.anime_id for record in local_matches}
            merged = local_matches + [record for record in extra_animes if record.anime_id not in known]
            if len(merged) == len(local_matches):
                return                  # la web no ha aportado nada nuevo
            print(f"La búsqueda en el proveedor añade {len(merged) - len(local_matches)} "
                  f"anime(s) que el título guardado no encontraba")
            self.__display_animes(merged)

        def _search_online():
            search_results, _ = self.__anime_provider_mgr.search_animes_by_query(search_text, strict=True)
            self.__main_window.after(0, _merge, match_animes_from_search(saved_animes, search_results))

        threading.Thread(target=_search_online, daemon=True).start()


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
    def __init__(self, parent_frame, title, status: AnimeStatus, cb_display_anime: Callable):
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
            genre_check_button = ctk.CTkCheckBox(
                genre_filter_frame,
                text=refactor_genre_text(genre.value),
                variable=var
            )
            genre_check_button.grid(row=row + 1, column=col, padx=(3, 8), pady=2, sticky=ctk.W)

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
            order_radio_button = ctk.CTkRadioButton(
                order_filter_frame,
                text=refactor_genre_text(order.name),
                variable=self.selected_order,
                value=order.value
            )
            order_radio_button.grid(row=row + 1, column=col, padx=5, pady=(2, 4), sticky=ctk.EW)

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
        filter_animes: List[AnimeRecord] = self.animes_persistence.get_anime_by_genre_and_order(
            self.anime_status,
            self.selected_genres,
            self.selected_order.get()
        )
        if len(filter_animes) == 0:
            print("No se encontró ningún anime")
            return
        for anime_register in filter_animes:
            print(f"{anime_register.title} encontrado entre mis animes {self.anime_status.name}")
        self.__display_animes(filter_animes)

    def __display_animes(self, anime_list: List[AnimeRecord]):
        self.display_animes_callback(anime_list)