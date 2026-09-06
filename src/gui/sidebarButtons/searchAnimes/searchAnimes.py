__author__ = "Jose David Escribano Orts"
__subsystem__ = "sidebarButtons"
__module__ = "searchAnimes.py"
__version__ = "0.4"
__info__ = {"subsystem": __subsystem__, "module_name": __module__, "version": __version__}

"""«Buscar»: la única pestaña que trae cosas de fuera, y la única que puede duplicarte la biblioteca.

Tres piezas propias: el campo grande de arriba (hace de cabecera); las fichas
de género (GenreChips), que muestran el filtro activo sin abrir nada; y el
sello «ya lo tienes» sobre cada resultado guardado.

El sello se resuelve en local y sin petición extra: la biblioteca entera cabe
en memoria y se cruza por slug y, si no, por título normalizado, porque el
slug solo coincide cuando la fila la guardó el mismo proveedor que responde.

La paginación aquí no es la de las otras vistas: quien trocea es el sitio
web, no el paginador. Cada página es una petición nueva, y solo se sabe cuál
es la última, no cuántos resultados hay en total.
"""

import os
import threading
import customtkinter as ctk

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Union

from APIs.common.animeProviderMgr import AnimeProviderManager, AnimeProviderManagerSingleton
from APIs.common.models import AnimeGenreFilter, AnimeOrderFilter, AnimeInfo, AnimeProviderId
from dataPersistence.animesPersistence import (AnimeRecord, AnimeStatus, AnimesPersistence,
                                               AnimesPersistenceSingleton)
from gui.anime_window import AnimeWindowViewer, find_saved_duplicate, show_anime_info_error
from gui.components.empty_state import EmptyState, glyph as empty_glyph
from gui.components.genre_chips import GenreChips
from gui.components.pager import Pager
from gui.components.poster_grid import PosterGrid, PosterItem
from gui.components.status_pill import StatusPill
from gui.theme import Metrics, Theme
from utils.buttons import utilsButtons
from utils.utils import (download_animes_poster, find_cached_poster_path, get_resource_path,
                         load_dual_image, refactor_genre_text)

#: Texto de cada criterio de ordenación. Vive aquí y no en el enum porque es
#: texto de interfaz: renombrar una opción no puede cambiar lo que se le pide al
#: proveedor, que es el `value`.
ORDER_LABELS: Dict[str, str] = {
    AnimeOrderFilter.POR_DEFECTO.value:    "Orden: por defecto",
    AnimeOrderFilter.ALFABÉTICAMENTE.value: "Orden: alfabético",
    AnimeOrderFilter.CALIFICACIÓN.value:   "Orden: calificación",
}


@dataclass
class AnimeSearch:
    """La última búsqueda hecha, para poder volver a la pestaña y encontrarla igual.

    La guarda ``MainWindow.last_search_instance``: es estado del hub, no de la
    vista, porque la vista se destruye entera cada vez que se cambia de pestaña.
    """
    animes: List[AnimeInfo]
    last_page: int
    current_page: int = 1
    text_query: str = None
    genre_filters: List[AnimeGenreFilter] = None
    order_filter: str = None


class SearchButton(utilsButtons.SidebarButton):
    """El buscador: catálogo del proveedor, con aviso de lo que ya es tuyo."""

    #: Ancho del campo de búsqueda.
    QUERY_W: int = 620
    #: Alto del campo de búsqueda.
    QUERY_H: int = 46
    #: Radio del campo. No es una píldora: el diseño le pone 10.
    QUERY_RADIUS: int = 10
    #: Tamaño de página del paginador. En esta vista **no se usa para cortar
    #: nada** —quien trocea es el proveedor—, pero `Pager` lo pide en el
    #: constructor; se deja el 12 de las rejillas de seis columnas.
    PAGE_SIZE: int = 12

    def __init__(self, main_window, icon_path, row, column):
        icon_path_light = icon_path_dark = os.path.join(icon_path, "buscar.png")
        super().__init__(main_window.sidebar_frame, "Buscar", row, column, self.show_frame, icon_path_light, icon_path_dark)

        self.main_window = main_window
        self.anime_provider_mgr: AnimeProviderManager = AnimeProviderManagerSingleton()
        self.animes_persistence: AnimesPersistence = AnimesPersistenceSingleton()
        self.__icon_path = icon_path

        # --- Estado de la búsqueda en curso -------------------------------
        self.__query: str = ""
        self.__genres: List[AnimeGenreFilter] = []
        self.__order: str = AnimeOrderFilter.POR_DEFECTO.value
        #: Cada petición lleva su número. Solo pinta la última: sin esto, una
        #: búsqueda lenta repintaría encima de otra más reciente ya en pantalla.
        self.__generation: int = 0
        #: Lo que hay pintado ahora, por clave de celda. De aquí sale el
        #: `AnimeInfo` y el `AnimeRecord` al abrir una ficha.
        self.__displayed: Dict[str, Tuple[AnimeInfo, Optional[AnimeRecord]]] = {}

        # --- Widgets de la vista ------------------------------------------
        self.__query_entry: Optional[ctk.CTkEntry] = None
        self.__chips: Optional[GenreChips] = None
        self.__order_menu: Optional[ctk.CTkOptionMenu] = None
        self.__results_label: Optional[ctk.CTkLabel] = None
        self.__poster_grid: Optional[PosterGrid] = None
        self.__pager: Optional[Pager] = None
        #: Estado vacío de «sin resultados». Se construye y se destruye en cada
        #: búsqueda porque su frase nombra la consulta, que cambia.
        self.__empty_state: Optional[EmptyState] = None

    # ------------------------------------------------------------------
    # Construcción de la vista
    # ------------------------------------------------------------------
    def show_frame(self):
        self.main_window.clear_frame()
        self.__show_browser()

    def __show_browser(self):
        content = self.main_window.content_frame
        content.grid_columnconfigure(0, weight=1)

        self.__build_query_box(content)
        self.__build_filters(content)

        self.__results_label = ctk.CTkLabel(
            content,
            text="Busca por título, o elige un género para explorar el catálogo",
            font=Theme.font(*Theme.T_SUB),
            text_color=Theme.TXT_3,
            anchor="w"
        )
        self.__results_label.grid(row=2, column=0, sticky="w",
                                  padx=Metrics.CONTENT_PAD_X, pady=(16, 14))

        # Sin on_columns_changed, al revés que las vistas de rejilla paginadas:
        # aquí el contenido de una página lo decide el proveedor, no el ancho,
        # así que la rejilla solo se recoloca con los resultados que ya tiene.
        self.__poster_grid = PosterGrid(content, columns=6, poster_size=Metrics.GRID6_POSTER,
                                        on_click=self.__on_anime_click)
        self.__poster_grid.grid(row=3, column=0, sticky="ew", padx=(PosterGrid.OUTER_PAD_X, 0))

        # La fila 4 la ocupa el estado vacío cuando hace falta; el paginador baja
        # a la 5 para que no tengan que compartir celda.
        self.__pager = Pager(content, page_size=self.PAGE_SIZE, on_page=self.__on_page_changed)
        self.__pager.grid(row=5, column=0, sticky="ew",
                          padx=Metrics.CONTENT_PAD_X, pady=(4, 24))
        # Nace escondido: un paginador recién colocado no se ha repintado todavía
        # y se quedaría ocupando su fila, vacío, hasta la primera búsqueda.
        self.__pager.set_pages(1, 1)

        self.__restore_last_search()

    def __build_query_box(self, content: ctk.CTkFrame) -> None:
        """El campo grande de arriba: marco con borde de acento, lupa y entrada.

        Es un marco y no un ``CTkEntry`` suelto porque el diseño mete la lupa
        **dentro** de la caja, y una entrada de Tk no admite adornos interiores.
        """
        query_row = ctk.CTkFrame(content, height=1, fg_color=Theme.TRANSPARENT)
        query_row.grid(row=0, column=0, sticky="w",
                       padx=Metrics.CONTENT_PAD_X, pady=(22, 0))

        query_frame = ctk.CTkFrame(
            query_row,
            width=self.QUERY_W,
            height=self.QUERY_H,
            corner_radius=self.QUERY_RADIUS,
            fg_color=Theme.CARD,
            border_width=1,
            border_color=Theme.ACCENT
        )
        query_frame.grid(row=0, column=0, sticky="w")
        # Sin esto el marco encoge hasta el tamaño de sus hijos y la caja pierde
        # los 620 x 46 del diseño.
        query_frame.grid_propagate(False)
        query_frame.grid_columnconfigure(1, weight=1)
        query_frame.grid_rowconfigure(0, weight=1)

        search_icon = load_dual_image(
            os.path.join(self.__icon_path, "buscar.png"),
            os.path.join(self.__icon_path, "buscar.png"),
            (16, 16)
        )
        icon_label = ctk.CTkLabel(query_frame, text="", image=search_icon)
        icon_label.grid(row=0, column=0, padx=(16, 11))
        icon_label.bind("<Button-1>", lambda _event: self.__on_query_submitted())
        icon_label.configure(cursor="hand2")

        self.__query_entry = ctk.CTkEntry(
            query_frame,
            placeholder_text="Buscar un anime…",
            border_width=0,
            fg_color=Theme.TRANSPARENT,
            font=Theme.font(*Theme.T_BODY),
            text_color=Theme.TXT,
            placeholder_text_color=Theme.TXT_3
        )
        self.__query_entry.grid(row=0, column=1, sticky="ew", padx=(0, 16))
        self.__query_entry.bind("<Return>", lambda _event: self.__on_query_submitted())

        # El botón no está en el diseño, que enseña la caja sola con el cursor
        # dentro. Se conserva porque quitarlo dejaría la búsqueda accesible solo
        # con Enter, y eso sí sería una función menos que hoy.
        search_button = ctk.CTkButton(
            query_row,
            text="Buscar",
            width=96,
            height=self.QUERY_H,
            corner_radius=self.QUERY_RADIUS,
            font=Theme.font(*Theme.T_UI),
            fg_color=Theme.ACCENT,
            hover_color=Theme.ACCENT,
            text_color=Theme.ACCENT_INK,
            command=self.__on_query_submitted
        )
        search_button.grid(row=0, column=1, sticky="w", padx=(12, 0))

    def __build_filters(self, content: ctk.CTkFrame) -> None:
        """Fila de fichas de género a la izquierda y control de orden a la derecha."""
        filters_frame = ctk.CTkFrame(content, height=1, fg_color=Theme.TRANSPARENT)
        filters_frame.grid(row=1, column=0, sticky="ew",
                           padx=Metrics.CONTENT_PAD_X, pady=(16, 0))
        filters_frame.grid_columnconfigure(0, weight=1)

        # El ancho de envuelto se descuenta del que ocupa el control de orden: si
        # las fichas ocuparan la fila entera, la última de cada línea se metería
        # debajo del desplegable.
        self.__chips = GenreChips(filters_frame, on_change=self.__on_genres_changed)
        self.__chips.grid(row=0, column=0, sticky="ew", padx=(0, 200))

        self.__order_menu = ctk.CTkOptionMenu(
            filters_frame,
            values=list(ORDER_LABELS.values()),
            width=186,
            height=GenreChips.CHIP_H,
            corner_radius=Metrics.pill_radius(GenreChips.CHIP_H),
            font=Theme.font(*Theme.T_META),
            dropdown_font=Theme.font(*Theme.T_UI),
            fg_color=Theme.CARD,
            button_color=Theme.CARD,
            button_hover_color=Theme.CARD_HOVER,
            text_color=Theme.TXT_2,
            dropdown_fg_color=Theme.CARD,
            dropdown_hover_color=Theme.CARD_HOVER,
            dropdown_text_color=Theme.TXT,
            command=self.__on_order_changed
        )
        self.__order_menu.set(ORDER_LABELS[self.__order])
        self.__order_menu.grid(row=0, column=1, sticky="ne")

    def __restore_last_search(self) -> None:
        """Repinta la última búsqueda al volver a entrar en la pestaña.

        No se relanza la petición: lo que se guardó son los resultados, así que
        volver a «Buscar» no vuelve a molestar al sitio.
        """
        last_search: Optional[AnimeSearch] = self.main_window.last_search_instance
        if last_search is None:
            return
        self.__query = last_search.text_query or ""
        self.__genres = list(last_search.genre_filters or [])
        self.__order = last_search.order_filter or AnimeOrderFilter.POR_DEFECTO.value

        if self.__query:
            self.__query_entry.insert(0, self.__query)
        self.__chips.set_selected(self.__genres)
        self.__order_menu.set(ORDER_LABELS.get(self.__order, ORDER_LABELS[AnimeOrderFilter.POR_DEFECTO.value]))
        self.__display_results(last_search.animes, last_search.last_page,
                               last_search.current_page, self.__generation)

    # ------------------------------------------------------------------
    # Gestos del usuario
    # ------------------------------------------------------------------
    def __on_query_submitted(self) -> None:
        """Buscar por texto. Vacía los géneros: el contrato no combina las dos búsquedas.

        ``search_animes_by_query`` y ``search_animes_by_genres_and_order`` son dos
        métodos distintos y ninguno acepta lo del otro, así que dejar las fichas
        encendidas mientras se busca por texto enseñaría un filtro que no se está
        aplicando. Manda el último gesto.
        """
        self.__query = self.__query_entry.get().strip()
        if self.__query and self.__chips.selected():
            self.__genres = []
            self.__chips.set_selected([])
        self.__launch_search(page=1)

    def __on_genres_changed(self, genres: List[AnimeGenreFilter]) -> None:
        """Filtrar por género. Vacía el texto, por el mismo motivo que el de arriba."""
        self.__genres = genres
        if self.__query:
            self.__query = ""
            self.__query_entry.delete(0, "end")
        self.__launch_search(page=1)

    def __on_order_changed(self, label: str) -> None:
        """Cambia el criterio de orden y relanza la búsqueda por género."""
        for order_value, order_label in ORDER_LABELS.items():
            if order_label == label:
                self.__order = order_value
                break
        # El orden es del catálogo, no de una búsqueda por texto: el contrato solo
        # lo acepta en `search_animes_by_genres_and_order`.
        if self.__query:
            self.__query = ""
            self.__query_entry.delete(0, "end")
        self.__launch_search(page=1)

    def __on_page_changed(self, page: int) -> None:
        """Cada página es una petición nueva: quien trocea es el sitio."""
        self.__launch_search(page=page)

    # ------------------------------------------------------------------
    # Búsqueda
    # ------------------------------------------------------------------
    def __launch_search(self, page: int = 1) -> None:
        """Saca la petición del hilo de Tkinter y vuelve con ``after(0, …)``."""
        self.__generation += 1
        generation = self.__generation
        query, genres, order = self.__query, list(self.__genres), self.__order

        self.__set_status("Buscando animes…")
        self.__poster_grid.clear()
        self.__displayed.clear()
        self.__pager.set_pages(1, 1)
        # Si no, el «Sin resultados» de la búsqueda anterior se queda debajo del
        # «Buscando animes…» de la nueva.
        self.__clear_empty_state()

        def _search():
            if query:
                animes, last_page = self.anime_provider_mgr.search_animes_by_query(query, page)
            else:
                animes, last_page = self.anime_provider_mgr.search_animes_by_genres_and_order(
                    genres, order, page)
            # Las carátulas se bajan aquí, que ya es el hilo secundario: son
            # peticiones HTTP y no pueden ir en el de la interfaz.
            download_animes_poster(get_resource_path("resources/images/search"), animes)
            self.main_window.after(0, self.__display_results, animes, last_page, page, generation)

        threading.Thread(target=_search, daemon=True).start()

    def __display_results(self, animes: List[AnimeInfo], last_page: int,
                          page: int, generation: int) -> None:
        """Pinta una página de resultados. **Ya en el hilo de Tkinter.**"""
        # Dos guardas, y las dos hacen falta: la primera descarta respuestas de
        # búsquedas que ya no son la actual; la segunda, respuestas que llegan
        # cuando el usuario ya se ha ido a otra pestaña y la rejilla no existe
        # (es lo que reventaba con `invalid command name ...!ctkcanvas`).
        if generation != self.__generation:
            return
        if self.__poster_grid is None or not self.__poster_grid.winfo_exists():
            return

        self.__save_anime_search(animes, last_page, page)

        saved_by_slug, saved_records = self.__saved_index()
        items: List[PosterItem] = []
        self.__displayed = {}
        for anime in animes:
            anime_record = self.__saved_record(anime, saved_by_slug, saved_records)
            key = str(anime.id)
            self.__displayed[key] = (anime, anime_record)
            items.append(self.__poster_item(key, anime, anime_record))

        self.__poster_grid.show(items)
        self.__pager.set_pages(last_page, page)
        self.__set_status(self.__results_text(animes, items))
        self.__refresh_empty_state(animes)

    def __save_anime_search(self, animes: List[AnimeInfo], last_page: int, page: int) -> None:
        self.main_window.last_search_instance = AnimeSearch(
            animes=animes,
            last_page=last_page,
            current_page=page,
            text_query=self.__query,
            genre_filters=list(self.__genres),
            order_filter=self.__order
        )

    def __results_text(self, animes: List[AnimeInfo], items: List[PosterItem]) -> str:
        """«34 resultados en AnimeAV1 · 2 ya están en tu biblioteca».

        El proveedor sale de los propios resultados y no del desplegable: el
        manager estampa en cada ``AnimeInfo`` quién respondió, así que cuando
        entra el fallback la línea dice el sitio de verdad y no el que se pidió.
        """
        if not animes:
            # Sin resultados quien habla es el estado vacío; repetirlo aquí sería dato duplicado.
            return ""

        provider_name = self.__serving_provider_name(animes)

        total = len(animes)
        results = "1 resultado" if total == 1 else f"{total} resultados"
        text = f"{results} en {provider_name}"
        saved = sum(1 for item in items if item.badge)
        if saved:
            text += (" · 1 ya está en tu biblioteca" if saved == 1
                     else f" · {saved} ya están en tu biblioteca")
        if self.__genres:
            text += " · " + ", ".join(refactor_genre_text(genre.name) for genre in self.__genres)
        return text

    def __serving_provider_name(self, animes: List[AnimeInfo]) -> str:
        """Quién ha servido estos resultados. Sin resultados, el seleccionado."""
        provider_id: Optional[AnimeProviderId] = next(
            (anime.provider_id for anime in animes if anime.provider_id is not None), None)
        if provider_id is None:
            provider_id = self.anime_provider_mgr.get_default_provider_id()
        return self.anime_provider_mgr.get_provider_name(provider_id)

    def __set_status(self, text: str) -> None:
        if self.__results_label is not None and self.__results_label.winfo_exists():
            self.__results_label.configure(text=text)

    # ------------------------------------------------------------------
    # Estado vacío
    # ------------------------------------------------------------------
    def __refresh_empty_state(self, animes: List[AnimeInfo]) -> None:
        """Pone o quita el estado vacío según haya resultados o no.

        Se reconstruye en vez de reconfigurarse porque la frase nombra la
        consulta y la acción depende de si lo que estrecha la búsqueda es el
        texto o los géneros.
        """
        self.__clear_empty_state()
        if animes:
            return

        # No se ofrece "probar con otro proveedor": call_with_fallback() ya
        # recorrió el registro entero, así que llegar aquí significa que todos
        # han respondido vacío. Lo único que puede cambiar el resultado es
        # soltar lo que estrecha la consulta.
        if self.__query:
            message = f"Sin resultados para «{self.__query}»"
            action_text = "Borrar la búsqueda"
        elif self.__genres:
            genres = ", ".join(refactor_genre_text(genre.name) for genre in self.__genres)
            message = f"Sin resultados para {genres}"
            action_text = "Quitar los filtros"
        else:
            message = "Sin resultados"
            action_text = None

        providers = len(self.anime_provider_mgr.list_providers_info())
        empty_state = EmptyState(
            self.main_window.content_frame,
            message,
            icon=empty_glyph("search"),
            hint=(f"Han respondido los {providers} proveedores y ninguno lo tiene."
                  if providers > 1 else "El proveedor no tiene nada que encaje."),
            action_text=action_text,
            on_action=self.__clear_search
        )
        empty_state.grid(row=4, column=0, pady=(28, 0))
        self.__empty_state = empty_state

    def __clear_empty_state(self) -> None:
        """Quita el estado vacío, si lo hay."""
        if self.__empty_state is not None and self.__empty_state.winfo_exists():
            self.__empty_state.destroy()
        self.__empty_state = None

    def __clear_search(self) -> None:
        """Deja la pestaña como recién abierta: sin texto, sin géneros y sin rejilla."""
        self.__query = ""
        self.__genres = []
        if self.__query_entry is not None and self.__query_entry.winfo_exists():
            self.__query_entry.delete(0, "end")
        self.__chips.set_selected([])
        # Se incrementa la generación para que una respuesta en vuelo no repinte
        # la rejilla que se acaba de vaciar.
        self.__generation += 1
        self.__poster_grid.clear()
        self.__displayed.clear()
        self.__pager.set_pages(1, 1)
        self.main_window.last_search_instance = None
        # Sin estado vacío: la pestaña recién abierta no es «no hay resultados»,
        # es «todavía no has pedido nada». Lo que invita a pedirlo es el campo de
        # arriba, y la línea de estado ya lo dice.
        self.__clear_empty_state()
        self.__set_status("Busca por título, o elige un género para explorar el catálogo")

    # ------------------------------------------------------------------
    # El sello «ya lo tienes»
    # ------------------------------------------------------------------
    def __saved_index(self) -> Tuple[Dict[str, AnimeRecord], List[AnimeRecord]]:
        """La biblioteca entera, indexada para cruzarla con los resultados.

        Una sola consulta a SQLite por página pintada y **ninguna petición de
        red**: la biblioteca son decenas de filas y cabe de sobra en memoria.
        """
        anime_records = self.animes_persistence.get_all_animes()
        return {str(record.anime_id): record for record in anime_records}, anime_records

    def __saved_record(self, anime: AnimeInfo, saved_by_slug: Dict[str, AnimeRecord],
                       saved_records: List[AnimeRecord]) -> Optional[AnimeRecord]:
        """La fila con la que este resultado está guardado, si lo está.

        Primero por *slug*, que es exacto pero solo acierta si la fila la guardó
        el mismo proveedor que ha respondido; después por título normalizado, que
        es lo único común entre sitios. La comparación por título es la de
        ``find_saved_duplicate()`` —misma función y mismo umbral— para que el
        sello y el aviso de duplicado de la ficha no puedan decir cosas distintas.
        """
        record = saved_by_slug.get(str(anime.id))
        if record is not None:
            return record
        return find_saved_duplicate(saved_records, anime.title)

    def __poster_item(self, key: str, anime: AnimeInfo,
                      anime_record: Optional[AnimeRecord]) -> PosterItem:
        """Traduce un resultado a una celda, con su sello si ya es tuyo."""
        status = self.__saved_status(anime_record)
        return PosterItem(
            key=key,
            title=anime.title,
            poster_path=self.__poster_path(anime),
            badge=StatusPill.text(status) if status is not None else None,
            badge_icon=StatusPill.icon(status) if status is not None else None
        )

    @staticmethod
    def __saved_status(anime_record: Optional[AnimeRecord]) -> Optional[AnimeStatus]:
        """Qué dice el sello: el estado excluyente de la fila y, si no tiene, «Favorito».

        :param anime_record: Fila guardada del resultado, o None si no está en la biblioteca.
        :return: Estado a mostrar, o None si no está guardado.
        """
        if anime_record is None:
            return None
        status = StatusPill.other_status(anime_record)
        if status is not None:
            return status
        return AnimeStatus.FAVOURITE if anime_record.is_favourite else None

    @staticmethod
    def __poster_path(anime: AnimeInfo) -> Optional[str]:
        """La carátula recién bajada a `search/`, o la que ya hubiera cacheada."""
        search_path = os.path.join(get_resource_path("resources/images/search"), f"{anime.id}.jpg")
        if os.path.exists(search_path):
            return search_path
        return find_cached_poster_path(anime.id)

    # ------------------------------------------------------------------
    # Navegación
    # ------------------------------------------------------------------
    def __on_anime_click(self, key: Union[str, int]):
        """Abre la ficha de un resultado de búsqueda.

        No usa open_saved_anime(): aquí el proveedor ya se sabe, es el que
        sirvió la búsqueda. Cuando el resultado ya está guardado se pasa
        también su anime_record, para que la ficha use la identidad de la
        fila y no cree una duplicada si el slug del resultado es de otro sitio.

        :param key: Clave de la celda pulsada, tal y como se guardó en __displayed.
        """
        anime, anime_record = self.__displayed.get(str(key), (None, None))
        if anime is None:
            return
        anime_id, provider_id = anime.id, anime.provider_id

        self.main_window.configure(cursor="watch")
        self.main_window.update_idletasks()

        def _show(anime_clicked, served_by):
            if not self.main_window.winfo_exists():
                return
            # Restaurar el cursor antes de cualquier salida, incluida la de error.
            self.main_window.configure(cursor="")
            if anime_clicked is None:
                show_anime_info_error(anime_id)
                return
            AnimeWindowViewer(self.main_window, anime_clicked, served_by,
                              anime_record=anime_record).display_anime_info()

        def _load_and_show():
            anime_clicked, served_by = self.anime_provider_mgr.get_anime_info_with_provider(
                anime_id, provider_id=provider_id)
            self.main_window.after(0, _show, anime_clicked, served_by)

        threading.Thread(
            target=_load_and_show,
            daemon=True
        ).start()
