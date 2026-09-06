__author__ = "Jose David Escribano Orts"
__subsystem__ = "sidebarButtons"
__module__ = "favouriteAnimes.py"
__version__ = "0.4"
__info__ = {"subsystem": __subsystem__, "module_name": __module__, "version": __version__}

"""«Favoritos»: rejilla de cinco con la calificación personal debajo de cada título.

Rejilla y no cascada porque a favoritos se entra a mirar, con el póster más
grande de las tres rejillas. La calificación (estrellas con medios puntos) se
guarda en la columna rating de ANIMES y se puede ordenar por ella.

Sin calificar no es cero: esas filas van al final del orden por calificación,
nunca las primeras. Y calificar no reordena la rejilla al vuelo: el orden se
aplica al pintar la vista o al cambiar el criterio, no en cada clic.

Todo sale de la biblioteca guardada, así que la pestaña funciona sin conexión;
solo salen a la red la búsqueda del proveedor (que se suma a la local) y abrir
una ficha.
"""

import os
import customtkinter as ctk

from typing import Any, Dict, List, Optional, Union

from APIs.common.animeProviderMgr import AnimeProviderManager, AnimeProviderManagerSingleton
from dataPersistence.animesPersistence import (AnimesPersistence, AnimesPersistenceSingleton, AnimeRecord,
                                               AnimeStatus)
from dataPersistence.userPersistence import UserPersistence
from gui.anime_window import open_saved_anime
from gui.components.empty_state import EmptyState, ICON_SIZE as EMPTY_ICON_SIZE
from gui.components.pager import Pager
from gui.components.poster_grid import PosterGrid, PosterItem
from gui.components.rating_stars import RatingStars
from gui.components.status_pill import StatusPill
from gui.components.view_header import ViewHeader
from gui.theme import Metrics, Theme
from utils.buttons import utilsButtons
from utils.utils import find_cached_poster_path

#: Texto de cada criterio de orden en el desplegable. La clave es lo que se
#: persiste; así renombrar una opción no invalida la preferencia guardada.
ORDER_LABELS: Dict[str, str] = {
    UserPersistence.FAVOURITES_ORDER_RATING: "Mi calificación",
    UserPersistence.FAVOURITES_ORDER_TITLE:  "Título (A-Z)",
}


class FavouritesButton(utilsButtons.SidebarButton):
    """La estantería de lo que más te gusta, ordenada por lo que tú le has puesto."""

    #: Filas por página. El tamaño de página sale de multiplicar esto por las
    #: columnas que quepan, así que una página es siempre dos filas llenas.
    ROWS_PER_PAGE: int = 2

    def __init__(self, main_window, icon_path, row, column):
        icon_path_light = icon_path_dark = os.path.join(icon_path, "favoritos.png")
        super().__init__(main_window.sidebar_frame, "Favoritos", row, column, self.show_favourite_animes, icon_path_light, icon_path_dark)

        self.main_window = main_window
        self.anime_provider_mgr: AnimeProviderManager = AnimeProviderManagerSingleton()
        self.animes_persistence: AnimesPersistence = AnimesPersistenceSingleton()
        self.__poster_grid: Optional[PosterGrid] = None
        self.__pager: Optional[Pager] = None
        self.__message_label: Optional[ctk.CTkLabel] = None
        #: Última lista recibida, sin ordenar: cambiar el orden reordena lo que
        #: hay en pantalla sin deshacer la búsqueda.
        self.__displayed_animes: List[AnimeRecord] = []
        #: Esa misma lista ya ordenada. Es de donde corta el paginador, así que
        #: página y orden no pueden discrepar.
        self.__sorted_animes: List[AnimeRecord] = []
        #: Criterio elegido; se persiste entre sesiones.
        self.__order: str = UserPersistence.FAVOURITES_ORDER_RATING
        # Buscador de la pestaña: coincidencias locales al instante, completadas
        # después con lo que encuentre el proveedor seleccionado.
        self.__search = utilsButtons.SavedAnimeSearch(
            main_window=main_window,
            anime_provider_mgr=self.anime_provider_mgr,
            get_saved_animes=self.animes_persistence.get_favourite_animes,
            display_animes=self.__display_animes,
            is_still_visible=lambda: (self.__poster_grid is not None and self.__poster_grid.winfo_exists())
        )

    def show_frame(self):
        self.show_favourite_animes()

    def show_favourite_animes(self):
        self.main_window.clear_frame()
        self.__show_browser()

    # ------------------------------------------------------------------
    # Construcción de la vista
    # ------------------------------------------------------------------
    def __show_browser(self):
        content = self.main_window.content_frame
        content.grid_columnconfigure(0, weight=1)

        self.__order = self.main_window.user_persistence.get_favourites_order()
        favourite_animes: List[AnimeRecord] = self.animes_persistence.get_favourite_animes()

        header = ViewHeader(content, "Favoritos", self.__subtitle(favourite_animes))
        header.grid(row=0, column=0, sticky="ew")
        self.__build_controls(header)

        if not favourite_animes:
            empty_state = EmptyState(
                content,
                "Todavía no has marcado ningún favorito",
                icon=StatusPill.icon(AnimeStatus.FAVOURITE, EMPTY_ICON_SIZE, Theme.TXT_3, gap=0),
                hint="Marca uno con el corazón desde su ficha y aparecerá aquí.",
                action_text="Ir a Nuevos lanzamientos",
                on_action=lambda: self.main_window.navigate_to("Nuevos lanzamientos")
            )
            empty_state.grid(row=1, column=0, pady=(60, 0))
            return

        self.__poster_grid = PosterGrid(content, columns=5, poster_size=Metrics.GRID5_POSTER,
                                        on_click=self.__on_anime_click,
                                        extra_builder=self.__build_rating,
                                        on_columns_changed=self.__on_columns_changed)
        # sticky="ew" y no "w": es lo que da a la rejilla el ancho de la ventana
        # para que decida cuántas columnas caben.
        self.__poster_grid.grid(row=1, column=0, sticky="ew", padx=(PosterGrid.OUTER_PAD_X, 0))

        # Mensaje de «la búsqueda no encontró nada». Nace escondido: aparece y
        # desaparece con grid()/grid_remove(), que conserva dónde iba colocado.
        self.__message_label = ctk.CTkLabel(
            content,
            text="Ningún anime de esta pestaña coincide con la búsqueda",
            font=Theme.font(*Theme.T_UI),
            text_color=Theme.TXT_2,
            anchor="w"
        )
        self.__message_label.grid(row=2, column=0, sticky="w",
                                  padx=Metrics.CONTENT_PAD_X, pady=(20, 0))
        self.__message_label.grid_remove()

        self.__pager = Pager(content, page_size=self.__poster_grid.columns * self.ROWS_PER_PAGE,
                             on_page=self.__render_page)
        self.__pager.grid(row=3, column=0, sticky="ew",
                          padx=Metrics.CONTENT_PAD_X, pady=(4, 24))

        self.__display_animes(favourite_animes)

    def __build_controls(self, header: ViewHeader) -> None:
        """Orden y buscador local, en la zona de controles de la cabecera."""
        order_optionmenu = ctk.CTkOptionMenu(
            header.controls_frame,
            values=list(ORDER_LABELS.values()),
            width=180,
            height=34,
            corner_radius=Metrics.RADIUS_CONTROL,
            font=Theme.font(*Theme.T_UI),
            dropdown_font=Theme.font(*Theme.T_UI),
            fg_color=Theme.CARD,
            button_color=Theme.CARD,
            button_hover_color=Theme.CARD_HOVER,
            text_color=Theme.TXT,
            dropdown_fg_color=Theme.CARD,
            dropdown_hover_color=Theme.CARD_HOVER,
            dropdown_text_color=Theme.TXT,
            command=self.__on_order_changed
        )
        order_optionmenu.set(ORDER_LABELS[self.__order])
        order_optionmenu.grid(row=0, column=0, padx=(0, 14))

        search_entry = ctk.CTkEntry(
            header.controls_frame,
            placeholder_text="Buscar en favoritos…",
            width=240,
            height=34,
            corner_radius=Metrics.RADIUS_CONTROL,
            font=Theme.font(*Theme.T_UI),
            fg_color=Theme.CARD,
            border_width=1,
            border_color=Theme.LINE,
            text_color=Theme.TXT,
            placeholder_text_color=Theme.TXT_3
        )
        search_entry.grid(row=0, column=1)
        # Enter además del botón: el buscador es local y responder a la tecla que
        # todo el mundo pulsa no cuesta nada.
        search_entry.bind("<Return>", lambda _event: self.__search_anime(search_entry))

        search_button = ctk.CTkButton(
            header.controls_frame,
            text="Buscar",
            width=80,
            height=34,
            corner_radius=Metrics.RADIUS_CONTROL,
            font=Theme.font(*Theme.T_UI),
            fg_color=Theme.ACCENT,
            hover_color=Theme.ACCENT,
            text_color=Theme.ACCENT_INK,
            command=lambda: self.__search_anime(search_entry)
        )
        search_button.grid(row=0, column=2, padx=(9, 0))

    def __subtitle(self, favourite_animes: List[AnimeRecord]) -> str:
        """«N animes · M calificados». La segunda mitad solo aparece si hay alguno."""
        total = len(favourite_animes)
        animes_text = "1 anime" if total == 1 else f"{total} animes"
        rated = sum(1 for anime_record in favourite_animes if anime_record.rating is not None)
        if not rated:
            return animes_text
        return f"{animes_text} · {rated} calificado{'' if rated == 1 else 's'}"

    # ------------------------------------------------------------------
    # Orden
    # ------------------------------------------------------------------
    def __on_order_changed(self, label: str) -> None:
        """Guarda el criterio y reordena lo que ya está en pantalla."""
        for order, order_label in ORDER_LABELS.items():
            if order_label == label:
                self.__order = order
                break
        self.main_window.user_persistence.set_favourites_order(self.__order)
        self.__display_animes(self.__displayed_animes)

    def __sort_animes(self, favourite_animes: List[AnimeRecord]) -> List[AnimeRecord]:
        """Ordena por el criterio elegido.

        Sin calificar no es cero: una fila con rating a None va al final,
        detrás incluso de la que tiene media estrella. A igualdad de
        calificación desempata el título.

        :param favourite_animes: Favoritos a ordenar.
        :return: Lista ordenada.
        """
        by_title = lambda record: AnimeProviderManager.normalize_title(record.title)
        if self.__order == UserPersistence.FAVOURITES_ORDER_TITLE:
            return sorted(favourite_animes, key=by_title)
        # -rating ordena de mayor a menor; el `0 if ... else 1` mete a las filas
        # sin calificar en un grupo posterior a todas las calificadas.
        return sorted(
            favourite_animes,
            key=lambda record: (1 if record.rating is None else 0,
                                -(record.rating or 0),
                                by_title(record))
        )

    # ------------------------------------------------------------------
    # Rejilla
    # ------------------------------------------------------------------
    def __display_animes(self, favourite_animes: List[AnimeRecord]):
        """Reordena, repagina y repinta. Lo llaman el arranque, el buscador y el orden."""
        if self.__poster_grid is None or not self.__poster_grid.winfo_exists():
            return

        self.__displayed_animes = favourite_animes
        self.__sorted_animes = self.__sort_animes(favourite_animes)
        self.__pager.set_total(len(self.__sorted_animes), page=1)

        if self.__message_label is not None:
            if favourite_animes:
                self.__message_label.grid_remove()
            else:
                self.__message_label.grid()

        self.__render_page(1)

    def __on_columns_changed(self, columns: int) -> None:
        """La ventana ha cambiado de ancho y ahora cabe otro número de columnas.

        Repintar es cosa de la vista y no de la rejilla porque el ancho no cambia
        solo cómo se coloca la página: cambia **qué animes entran en ella**. El
        paginador conserva el primero que se estaba viendo.
        """
        if self.__pager is None or not self.__pager.winfo_exists():
            return
        self.__pager.set_page_size(columns * self.ROWS_PER_PAGE)
        self.__render_page(self.__pager.page())

    def __render_page(self, page: int) -> None:
        """Repinta la rejilla con la página pedida. Lo llama el paginador."""
        if self.__poster_grid is None or not self.__poster_grid.winfo_exists():
            return
        start, end = self.__pager.slice_bounds(page)
        self.__poster_grid.show([
            self.__poster_item(anime_record) for anime_record in self.__sorted_animes[start:end]
        ])

    def __poster_item(self, anime_record: AnimeRecord) -> PosterItem:
        """Traduce una fila de la biblioteca a una celda de la rejilla."""
        # El sello dice qué más es este anime aparte de favorito, para no
        # repetir el mismo dato en las diez celdas.
        status = StatusPill.other_status(anime_record)
        # Colores por defecto de PosterGrid (fondo oscuro opaco, texto blanco,
        # color del estado solo en el glifo): el par pastel de la píldora no se
        # lee bien sobre una carátula clara.
        return PosterItem(
            key=anime_record.anime_id,
            title=anime_record.title,
            poster_path=find_cached_poster_path(anime_record.anime_id),
            badge=StatusPill.text(status) if status is not None else None,
            badge_icon=StatusPill.icon(status) if status is not None else None,
            footer=self.__provider_name(anime_record),
            data=anime_record
        )

    def __provider_name(self, anime_record: AnimeRecord) -> Optional[str]:
        """De qué sitio es la fila. ``None`` mientras no se sepa, en vez de «desconocido»."""
        if anime_record.provider_id is None:
            return None
        return self.anime_provider_mgr.get_provider_name(anime_record.provider_id)

    def __build_rating(self, cell: ctk.CTkFrame, item: PosterItem) -> Optional[ctk.CTkBaseClass]:
        """Construye la fila de estrellas de una celda. Lo llama ``PosterGrid``."""
        anime_record: Any = item.data
        if not isinstance(anime_record, AnimeRecord):
            return None
        return RatingStars(
            cell,
            value=anime_record.rating,
            on_change=lambda rating, record=anime_record: self.__on_rating_changed(record, rating)
        )

    # ------------------------------------------------------------------
    # Navegación y acciones
    # ------------------------------------------------------------------
    def __on_rating_changed(self, anime_record: AnimeRecord, rating: Optional[int]) -> None:
        """Persiste la calificación y la deja también en la fila que ya está en memoria.

        No repinta: las estrellas ya se han actualizado solas y **la celda no se
        mueve de sitio** aunque el orden sea por calificación. Reordenar aquí
        cambiaría el anime que hay bajo el cursor entre dos clics.

        La lista en memoria se actualiza para que el siguiente orden —o la
        siguiente búsqueda— use el valor nuevo sin volver a la BD.
        """
        if not self.animes_persistence.update_anime_rating(anime_record.anime_id, rating):
            print(f"No se pudo guardar la calificación de {anime_record.title!r}")
            return
        anime_record.rating = rating

    def __search_anime(self, search_entry: ctk.CTkEntry):
        # Las dos búsquedas se suman: la local no depende del proveedor y la
        # del proveedor encuentra alias que el título guardado no conoce
        # ("Solo Leveling" -> "Ore dake Level Up na Ken"). Ver SavedAnimeSearch.
        self.__search.search(search_entry.get())

    def __on_anime_click(self, anime_id: Union[str, int]):
        """Abre la ficha de un favorito por el proveedor de su fila."""
        open_saved_anime(self.main_window, anime_id)
