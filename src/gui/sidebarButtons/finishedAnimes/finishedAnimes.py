__author__ = "Jose David Escribano Orts"
__subsystem__ = "sidebarButtons"
__module__ = "finishedAnimes.py"
__version__ = "0.3"
__info__ = {"subsystem": __subsystem__, "module_name": __module__, "version": __version__}

"""«Finalizados»: el archivo, en rejilla de seis con el sello de completado sobre la carátula.

Vuelve la rejilla —y no la cascada de «Viendo» o «Pendientes»— porque es la única
sección donde **no hay ninguna decisión que tomar**: no hay progreso que
consultar ni cola que ordenar, así que la pantalla puede dedicarse entera a
enseñar carátulas (`DISENO.md` §6).

Lo que estrena la pestaña es el **sello** superpuesto al póster con el recuento
«vistos / totales». Dice algo que no está en ninguna otra parte de la pantalla:
si el anime está completo **de verdad** o solo marcado a mano. Por eso el sello
enseña siempre los números reales de la fila y no los corrige: un «0 / 12» no es
un error de la vista, es que ese anime se marcó como terminado sin ir episodio a
episodio.

Todo lo que se ve sale de la biblioteca guardada, así que la pestaña **funciona
sin conexión**. Solo salen a la red la búsqueda del proveedor —que se **suma** a
la local— y abrir una ficha.
"""

import os
import customtkinter as ctk

from typing import List, Optional, Union

from APIs.common.animeProviderMgr import AnimeProviderManager, AnimeProviderManagerSingleton
from dataPersistence.animesPersistence import AnimesPersistence, AnimesPersistenceSingleton, AnimeRecord, AnimeStatus
from gui.anime_window import open_saved_anime
from gui.components.pager import Pager
from gui.components.poster_grid import PosterGrid, PosterItem
from gui.components.status_pill import StatusPill
from gui.components.view_header import ViewHeader
from gui.theme import Metrics, Theme
from utils.buttons import utilsButtons
from utils.utils import find_cached_poster_path


class FinishedAnimeButton(utilsButtons.SidebarButton):
    """El estante de lo terminado, con el recuento de episodios sobre cada carátula."""

    #: Animes por página. 12 y no 10 en las rejillas de seis columnas: dos filas
    #: llenas en vez de una llena y otra coja (`DISENO.md` §6).
    PAGE_SIZE: int = 12

    def __init__(self, main_window, icon_path, row, column):
        icon_path_light = icon_path_dark = os.path.join(icon_path, "finalizados.png")
        super().__init__(main_window.sidebar_frame, "Finalizados", row, column, self.show_finished_animes, icon_path_light, icon_path_dark)

        self.main_window = main_window
        self.anime_provider_mgr: AnimeProviderManager = AnimeProviderManagerSingleton()
        self.animes_persistence: AnimesPersistence = AnimesPersistenceSingleton()
        self.__poster_grid: Optional[PosterGrid] = None
        self.__pager: Optional[Pager] = None
        self.__message_label: Optional[ctk.CTkLabel] = None
        #: Lo que hay ahora en la rejilla. Es de donde corta el paginador, así que
        #: página y contenido no pueden discrepar.
        self.__displayed_animes: List[AnimeRecord] = []
        # Buscador de la pestaña: coincidencias locales al instante, completadas
        # después con lo que encuentre el proveedor seleccionado.
        self.__search = utilsButtons.SavedAnimeSearch(
            main_window=main_window,
            anime_provider_mgr=self.anime_provider_mgr,
            get_saved_animes=self.animes_persistence.get_finished_animes,
            display_animes=self.__display_animes,
            is_still_visible=lambda: (self.__poster_grid is not None and self.__poster_grid.winfo_exists())
        )

    def show_frame(self):
        self.show_finished_animes()

    def show_finished_animes(self):
        self.main_window.clear_frame()
        # Sin `time.sleep(0.1)`: solo existía para que `winfo_width()` devolviera
        # algo distinto de 1, porque de ahí salía el número de columnas. Ahora
        # son seis fijas y no se mide nada.
        self.__show_browser()

    # ------------------------------------------------------------------
    # Construcción de la vista
    # ------------------------------------------------------------------
    def __show_browser(self):
        content = self.main_window.content_frame
        content.grid_columnconfigure(0, weight=1)

        finished_animes: List[AnimeRecord] = self.animes_persistence.get_finished_animes()

        header = ViewHeader(content, "Finalizados", self.__subtitle(finished_animes))
        header.grid(row=0, column=0, sticky="ew")
        self.__build_controls(header)

        if not finished_animes:
            empty_label = ctk.CTkLabel(
                content,
                text="Todavía no has terminado ningún anime.\n"
                     "Los que marques como finalizados desde su ficha se archivan aquí.",
                font=Theme.font(*Theme.T_ROW),
                text_color=Theme.TXT_2,
                justify="center"
            )
            empty_label.grid(row=1, column=0, pady=(40, 0))
            return

        self.__poster_grid = PosterGrid(content, columns=6, poster_size=Metrics.GRID6_POSTER,
                                        on_click=self.__on_anime_click)
        self.__poster_grid.grid(row=1, column=0, sticky="w", padx=(PosterGrid.OUTER_PAD_X, 0))

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

        self.__pager = Pager(content, page_size=self.PAGE_SIZE, on_page=self.__render_page)
        self.__pager.grid(row=3, column=0, sticky="ew",
                          padx=Metrics.CONTENT_PAD_X, pady=(4, 24))

        self.__display_animes(finished_animes)

    def __build_controls(self, header: ViewHeader) -> None:
        """Solo el buscador local: aquí no hay nada que ordenar ni que filtrar.

        Sin acordeón de géneros, como en las otras tres vistas de estado: filtrar
        por género lo que ya es tuyo no aporta, y si el filtrado vuelve el sitio
        es `GenreChips` (fase 7), no un acordeón por pestaña.
        """
        search_entry = ctk.CTkEntry(
            header.controls_frame,
            placeholder_text="Buscar en finalizados…",
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
        search_entry.grid(row=0, column=0)
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
        search_button.grid(row=0, column=1, padx=(9, 0))

    def __subtitle(self, finished_animes: List[AnimeRecord]) -> str:
        """«N animes · M episodios vistos».

        El total de episodios sale de lo que hay **marcado**, no de la suma de
        listas de episodios: es el mismo número que confirma cada sello, así que
        la cabecera y las carátulas no pueden contradecirse.
        """
        total = len(finished_animes)
        animes_text = "1 anime" if total == 1 else f"{total} animes"
        watched = sum(len(anime_record.watched_episodes) for anime_record in finished_animes)
        if not watched:
            return animes_text
        return f"{animes_text} · {watched} episodio{'' if watched == 1 else 's'} visto{'' if watched == 1 else 's'}"

    # ------------------------------------------------------------------
    # Rejilla
    # ------------------------------------------------------------------
    def __display_animes(self, finished_animes: List[AnimeRecord]):
        """Repagina y repinta. Lo llaman el arranque y el buscador."""
        if self.__poster_grid is None or not self.__poster_grid.winfo_exists():
            return

        self.__displayed_animes = finished_animes
        self.__pager.set_total(len(finished_animes), page=1)

        if self.__message_label is not None:
            if finished_animes:
                self.__message_label.grid_remove()
            else:
                self.__message_label.grid()

        self.__render_page(1)

    def __render_page(self, page: int) -> None:
        """Repinta la rejilla con la página pedida. Lo llama el paginador."""
        if self.__poster_grid is None or not self.__poster_grid.winfo_exists():
            return
        start, end = self.__pager.slice_bounds(page)
        self.__poster_grid.show([
            self.__poster_item(anime_record) for anime_record in self.__displayed_animes[start:end]
        ])

    def __poster_item(self, anime_record: AnimeRecord) -> PosterItem:
        """Traduce una fila de la biblioteca a una celda de la rejilla."""
        return PosterItem(
            key=anime_record.anime_id,
            title=anime_record.title,
            poster_path=find_cached_poster_path(anime_record.anime_id),
            badge=self.__badge_text(anime_record),
            badge_icon=StatusPill.icon(AnimeStatus.FINISHED),
            footer=self.__provider_name(anime_record)
        )

    def __badge_text(self, anime_record: AnimeRecord) -> str:
        """«vistos / totales», **sin corregir el dato**.

        Un anime marcado como finalizado al que le falten episodios por marcar
        enseña sus números reales: es información sobre tu biblioteca, no un
        error que tapar.

        Cuando la fila no tiene lista de episodios —se guardó sin llegar a abrir
        su ficha— no hay «totales» que enseñar, y un «0 / 0» parecería un fallo
        de la vista. Ahí el sello dice el estado y ya está.
        """
        total = len(anime_record.episodes)
        if not total:
            return StatusPill.text(AnimeStatus.FINISHED)
        return f"{len(anime_record.watched_episodes)} / {total}"

    def __provider_name(self, anime_record: AnimeRecord) -> Optional[str]:
        """De qué sitio es la fila. ``None`` mientras no se sepa, en vez de «desconocido»."""
        if anime_record.provider_id is None:
            return None
        return self.anime_provider_mgr.get_provider_name(anime_record.provider_id)

    # ------------------------------------------------------------------
    # Navegación y acciones
    # ------------------------------------------------------------------
    def __search_anime(self, search_entry: ctk.CTkEntry):
        # Las dos búsquedas se suman: la local no depende del proveedor y la
        # del proveedor encuentra alias que el título guardado no conoce
        # ("Solo Leveling" -> "Ore dake Level Up na Ken"). Ver SavedAnimeSearch.
        self.__search.search(search_entry.get())

    def __on_anime_click(self, anime_id: Union[str, int]):
        # Es un anime de la biblioteca: el proveedor sale de su fila y la petición
        # va en un hilo aparte. Ambas cosas viven en open_saved_anime() porque las
        # cuatro vistas de estado hacen exactamente esto mismo.
        open_saved_anime(self.main_window, anime_id)
