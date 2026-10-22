__author__ = "Jose David Escribano Orts"
__subsystem__ = "sidebarButtons"
__module__ = "recentAnimes.py"
__version__ = "0.5"
__info__ = {"subsystem": __subsystem__, "module_name": __module__, "version": __version__}

import os
import threading

from typing import List, Tuple, Union

from APIs.common.animeProviderMgr import AnimeProviderManager, AnimeProviderManagerSingleton
from APIs.common.models import EpisodeInfo
from dataPersistence.animesPersistence import AnimeRecord
from gui.anime_window import AnimeWindowViewer, open_saved_anime, show_anime_info_error
from gui.components.empty_state import EmptyState, glyph as empty_glyph
from gui.components.pager import Pager
from gui.components.poster_grid import PosterGrid, PosterItem
from gui.components.resume_card import ResumeBand
from gui.components.view_header import ViewHeader
from gui.theme import Metrics
from utils.buttons import utilsButtons


class RecentAnimeButton(utilsButtons.SidebarButton):
    """Portada de la aplicación: lo que acaba de salir, y lo que dejaste a medias.

    La vista se compone de arriba abajo: cabecera, banda «Retomar donde lo
    dejaste» (solo si hay algo que retomar), rejilla de seis columnas y
    paginador. Cada pieza es un componente de ``gui/components/``; aquí solo se
    decide qué datos van en cada una.
    """

    #: Filas por página. El tamaño de página sale de multiplicar esto por las
    #: columnas que quepan, así que una página es siempre dos filas llenas.
    ROWS_PER_PAGE = 2

    def __init__(self, main_window, icon_path: str, row: int, column: int):
        icon_path_light = icon_path_dark = os.path.join(icon_path, "recientes.png")
        super().__init__(main_window.sidebar_frame, "Nuevos lanzamientos", row, column, self.__show_animes_recientes, icon_path_light, icon_path_dark)

        self.main_window = main_window
        self.anime_provider_mgr: AnimeProviderManager = AnimeProviderManagerSingleton()
        self.__poster_grid: PosterGrid | None = None
        self.__pager: Pager | None = None

    def show_frame(self):
        """Revela la barra lateral (oculta durante la carga) y pinta esta vista."""
        self.main_window.sidebar_frame.grid(row=0, column=0, rowspan=8, sticky="nsew")

        self.main_window.clear_frame()
        self.__show_animes_recientes()

    # ------------------------------------------------------------------
    # Construcción de la vista
    # ------------------------------------------------------------------
    def __show_animes_recientes(self):
        self.main_window.clear_frame()
        content = self.main_window.content_frame
        content.grid_columnconfigure(0, weight=1)

        header = ViewHeader(content, "Nuevos lanzamientos", self.__subtitle())
        header.grid(row=0, column=0, sticky="ew")

        recent_animes = self.main_window.recent_animes
        if not recent_animes:
            # El hueco no significa "no tienes nada": el catálogo no es del
            # usuario, así que una lista vacía es que ningún proveedor respondió.
            empty_state = EmptyState(
                content,
                "No se han podido cargar los estrenos",
                icon=empty_glyph("offline"),
                hint="Ningún proveedor ha respondido. Comprueba la conexión, "
                     "o prueba con otro desde la barra lateral.",
                action_text="Reintentar",
                on_action=self.main_window.retry_recent_animes
            )
            empty_state.grid(row=1, column=0, pady=(60, 0))
            return

        resume_records = self.__resume_records()
        resume_band = ResumeBand(content, resume_records, on_click=self.__on_saved_anime_click)
        if resume_band.has_content():
            resume_band.grid(row=1, column=0, sticky="ew",
                             padx=Metrics.CONTENT_PAD_X, pady=(0, 28))
            self.__refresh_resume_episodes(resume_band, resume_records)

        self.__poster_grid = PosterGrid(content, columns=6, poster_size=Metrics.GRID6_POSTER,
                                        on_click=self.__on_anime_click,
                                        on_columns_changed=self.__on_columns_changed)
        # sticky="ew" y no "w": es lo que da a la rejilla el ancho de la ventana
        # para que decida cuántas columnas caben.
        self.__poster_grid.grid(row=2, column=0, sticky="ew", padx=(PosterGrid.OUTER_PAD_X, 0))

        self.__pager = Pager(content, page_size=self.__poster_grid.columns * self.ROWS_PER_PAGE,
                             on_page=self.__render_page)
        self.__pager.grid(row=3, column=0, sticky="ew",
                          padx=Metrics.CONTENT_PAD_X, pady=(4, 24))
        self.__pager.set_total(len(recent_animes), page=1)

        self.__render_page(1)

    def __subtitle(self) -> str:
        """«N estrenos · Proveedor». El proveedor se enseña porque el catálogo es suyo."""
        total = len(self.main_window.recent_animes)
        estrenos = "1 estreno" if total == 1 else f"{total} estrenos"
        provider_id = self.anime_provider_mgr.get_default_provider_id()
        if provider_id is None:
            return estrenos
        return f"{estrenos} · {self.anime_provider_mgr.get_provider_name(provider_id)}"

    def __resume_records(self) -> List[AnimeRecord]:
        """Las filas de los últimos animes vistos, en el orden guardado.

        Se descarta en silencio lo que ya no esté en la biblioteca: la
        preferencia recuerda identificadores, no filas, y el usuario pudo quitar
        el anime después de verlo.
        """
        records: List[AnimeRecord] = []
        for anime_id in self.main_window.user_persistence.get_last_watched_ids():
            anime_record = self.main_window.animes_persistence.get_anime_by_anime_id(anime_id)
            if anime_record is not None:
                records.append(anime_record)
        return records

    # ------------------------------------------------------------------
    # Refresco de la banda «Retomar»
    # ------------------------------------------------------------------
    def __refresh_resume_episodes(self, resume_band: ResumeBand, anime_records: List[AnimeRecord]) -> None:
        """Vuelve a preguntar por los episodios de lo que hay en la banda «Retomar».

        Sin esto, un anime en emisión seguiría mostrando el recuento de
        episodios del día que se abrió su ficha por última vez. Se hace al
        entrar en la portada, en un hilo aparte, para no retrasar el arranque.

        :param resume_band: Banda a repintar si cambia algún recuento.
        :param anime_records: Filas de la banda a comprobar.
        """
        if not anime_records:
            return

        def _apply(fresh_episodes: List[Tuple[str, List[EpisodeInfo]]]) -> None:
            """Ya en el hilo de Tkinter: persiste lo que haya cambiado y repinta."""
            if not self.main_window.winfo_exists():
                return
            for anime_id, episodes in fresh_episodes:
                anime_record = self.main_window.animes_persistence.get_anime_by_anime_id(anime_id)
                if anime_record is None or len(anime_record.episodes) == len(episodes):
                    continue
                if not self.main_window.animes_persistence.update_anime_episodes(anime_id, episodes):
                    continue
                print(f"«{anime_record.title}» pasa de {len(anime_record.episodes)} "
                      f"a {len(episodes)} episodios")
                # La banda puede haberse ido mientras se pedían los datos (otra
                # vista, u otra visita a esta). La escritura ya está hecha, así que
                # la próxima visita leerá el dato bueno de todas formas.
                if not resume_band.winfo_exists():
                    continue
                updated_record = self.main_window.animes_persistence.get_anime_by_anime_id(anime_id)
                if updated_record is not None:
                    resume_band.update_record(updated_record)

        def _fetch() -> None:
            fresh_episodes: List[Tuple[str, List[EpisodeInfo]]] = []
            for anime_record in anime_records:
                anime_info, _ = self.anime_provider_mgr.get_anime_info_with_provider(
                    anime_record.anime_id, provider_id=anime_record.provider_id, strict=True)
                # Sin episodios no se toca nada: un corte de red o un cambio en el
                # HTML del sitio no puede vaciar la lista que ya está guardada.
                if anime_info is not None and anime_info.episodes:
                    fresh_episodes.append((anime_record.anime_id, anime_info.episodes))
            if fresh_episodes:
                self.main_window.after(0, _apply, fresh_episodes)

        threading.Thread(target=_fetch, daemon=True).start()

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
            PosterItem(
                key=anime.id,
                title=anime.title,
                poster_path=os.path.join(self.main_window.images_path, f"{anime.id}.jpg")
            )
            for anime in self.main_window.recent_animes[start:end]
        ])

    # ------------------------------------------------------------------
    # Navegación
    # ------------------------------------------------------------------
    def __on_saved_anime_click(self, anime_id: Union[str, int]):
        """Abre la ficha de un anime de la banda «Retomar» por su proveedor de fila."""
        open_saved_anime(self.main_window, anime_id)

    def __on_anime_click(self, anime_id: Union[str, int]):
        """Abre la ficha de un anime del catálogo, completando sus datos si faltan."""
        index = next(idx for idx, recent_anime in enumerate(self.main_window.recent_animes) if recent_anime.id == anime_id)
        anime_clicked = self.main_window.recent_animes[index]
        if anime_clicked.synopsis is None or anime_clicked.genres is None or anime_clicked.episodes is None:
            self.main_window.configure(cursor="watch")
            self.main_window.update_idletasks()

            def _show(anime_info, provider_id):
                if not self.main_window.winfo_exists():
                    return
                self.main_window.configure(cursor="")
                if anime_info is None:
                    # No se cae de vuelta a anime_clicked: su falta de datos es justo lo que trajo hasta aquí.
                    show_anime_info_error(anime_id)
                    return
                self.main_window.recent_animes[index] = anime_info
                anime_viewer = AnimeWindowViewer(self.main_window, anime_info, provider_id)
                anime_viewer.display_anime_info()

            def _load_and_show():
                anime_info, provider_id = self.anime_provider_mgr.get_anime_info_with_provider(anime_id, provider_id=anime_clicked.provider_id)
                self.main_window.after(0, _show, anime_info, provider_id)

            threading.Thread(
                target=_load_and_show,
                daemon=True
            ).start()
            return

        anime_viewer = AnimeWindowViewer(self.main_window, anime_clicked)
        anime_viewer.display_anime_info()
