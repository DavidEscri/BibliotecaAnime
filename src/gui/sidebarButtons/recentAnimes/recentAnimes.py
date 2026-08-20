__author__ = "Jose David Escribano Orts"
__subsystem__ = "sidebarButtons"
__module__ = "recentAnimes.py"
__version__ = "0.3"
__info__ = {"subsystem": __subsystem__, "module_name": __module__, "version": __version__}

import os
import threading
import customtkinter as ctk

from typing import List, Union

from APIs.common.animeProviderMgr import AnimeProviderManager, AnimeProviderManagerSingleton
from dataPersistence.animesPersistence import AnimeRecord
from gui.anime_window import AnimeWindowViewer, open_saved_anime, show_anime_info_error
from gui.components.pager import Pager
from gui.components.poster_grid import PosterGrid, PosterItem
from gui.components.resume_card import ResumeBand
from gui.components.view_header import ViewHeader
from gui.theme import Metrics, Theme
from utils.buttons import utilsButtons


class RecentAnimeButton(utilsButtons.SidebarButton):
    """Portada de la aplicación: lo que acaba de salir, y lo que dejaste a medias.

    La vista se compone de arriba abajo: cabecera, banda «Retomar donde lo
    dejaste» (solo si hay algo que retomar), rejilla de seis columnas y
    paginador. Cada pieza es un componente de ``gui/components/``; aquí solo se
    decide qué datos van en cada una.
    """

    #: Animes por página. 12 y no 10 en las rejillas de seis columnas: dos filas
    #: llenas en vez de una llena y otra coja (`DISENO.md` §6).
    PAGE_SIZE = 12

    def __init__(self, main_window, icon_path: str, row: int, column: int):
        icon_path_light = icon_path_dark = os.path.join(icon_path, "recientes.png")
        super().__init__(main_window.sidebar_frame, "Nuevos lanzamientos", row, column, self.__show_animes_recientes, icon_path_light, icon_path_dark)

        self.main_window = main_window
        self.anime_provider_mgr: AnimeProviderManager = AnimeProviderManagerSingleton()
        self.__poster_grid: PosterGrid | None = None
        self.__pager: Pager | None = None

    def show_frame(self):
        # Mostrar el sidebar ahora que ha terminado la descarga
        self.main_window.sidebar_frame.grid(row=0, column=0, rowspan=8, sticky="nsew")

        self.main_window.clear_frame()
        self.__show_animes_recientes()

    # ------------------------------------------------------------------
    # Construcción de la vista
    # ------------------------------------------------------------------
    def __show_animes_recientes(self):
        self.main_window.clear_frame()
        # Ya no hace falta el time.sleep(0.1) que llevaba aquí desde siempre: solo
        # estaba para dejar que Tk mapeara el frame y `winfo_width()` devolviera
        # algo distinto de 1, porque el número de columnas se calculaba de ahí.
        # Ahora son seis fijas y no se mide nada.
        content = self.main_window.content_frame
        content.grid_columnconfigure(0, weight=1)

        header = ViewHeader(content, "Nuevos lanzamientos", self.__subtitle())
        header.grid(row=0, column=0, sticky="ew")

        recent_animes = self.main_window.recent_animes
        if not recent_animes:
            empty_label = ctk.CTkLabel(
                content,
                text="No se pudo obtener la lista de novedades del proveedor seleccionado",
                font=Theme.font(*Theme.T_ROW),
                text_color=Theme.TXT_2,
                justify="center"
            )
            empty_label.grid(row=1, column=0, pady=(40, 0))
            return

        resume_band = ResumeBand(content, self.__resume_records(), on_click=self.__on_saved_anime_click)
        if resume_band.has_content():
            resume_band.grid(row=1, column=0, sticky="ew",
                             padx=Metrics.CONTENT_PAD_X, pady=(0, 28))

        self.__poster_grid = PosterGrid(content, columns=6, poster_size=Metrics.GRID6_POSTER,
                                        on_click=self.__on_anime_click)
        self.__poster_grid.grid(row=2, column=0, sticky="w", padx=(PosterGrid.OUTER_PAD_X, 0))

        self.__pager = Pager(content, page_size=self.PAGE_SIZE, on_page=self.__render_page)
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
        # Las tarjetas de «Retomar» son animes de la biblioteca: el proveedor sale
        # de su fila y la petición va en un hilo aparte, igual que en las cuatro
        # vistas de estado.
        open_saved_anime(self.main_window, anime_id)

    def __on_anime_click(self, anime_id: Union[str, int]):
        index = next(idx for idx, recent_anime in enumerate(self.main_window.recent_animes) if recent_anime.id == anime_id)
        # Reemplazar el anime en la lista
        anime_clicked = self.main_window.recent_animes[index]
        if anime_clicked.synopsis is None or anime_clicked.genres is None or anime_clicked.episodes is None:
            self.main_window.configure(cursor="watch")
            self.main_window.update_idletasks()

            def _show(anime_info, provider_id):
                if not self.main_window.winfo_exists():
                    return
                # Restaurar el cursor antes de cualquier salida, incluida la de error.
                self.main_window.configure(cursor="")
                if anime_info is None:
                    # No se puede caer de vuelta a `anime_clicked`: su falta de episodios/sinopsis es justo lo que nos ha traído hasta aquí.
                    show_anime_info_error(anime_id)
                    return
                self.main_window.recent_animes[index] = anime_info
                anime_viewer = AnimeWindowViewer(self.main_window, anime_info, provider_id)
                anime_viewer.display_anime_info()

            def _load_and_show():
                # La ficha necesita saber quién sirvió los datos  para pedir los servidores de vídeo al sitio correcto.
                anime_info, provider_id = self.anime_provider_mgr.get_anime_info_with_provider(anime_id, provider_id=anime_clicked.provider_id)
                self.main_window.after(0, _show, anime_info, provider_id)

            # Ejecutar en hilo secundario para no congelar la UI durante la petición HTTP
            threading.Thread(
                target=_load_and_show,
                daemon=True
            ).start()
            return

        anime_viewer = AnimeWindowViewer(self.main_window, anime_clicked)
        anime_viewer.display_anime_info()
