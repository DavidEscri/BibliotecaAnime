__author__ = "Jose David Escribano Orts"
__subsystem__ = "sidebarButtons"
__module__ = "watchingAnimes.py"
__version__ = "0.5"
__info__ = {"subsystem": __subsystem__, "module_name": __module__, "version": __version__}

import os
import customtkinter as ctk

from typing import List, Optional, Union

from APIs.common.animeProviderMgr import AnimeProviderManager, AnimeProviderManagerSingleton
from dataPersistence.animesPersistence import (AnimesPersistence, AnimesPersistenceSingleton, AnimeRecord,
                                               AnimeStatus)
from gui.anime_window import open_saved_anime
from gui.components.anime_row import AnimeRow, RowAction
from gui.components.empty_state import EmptyState, ICON_SIZE as EMPTY_ICON_SIZE
from gui.components.resume_card import resume_progress
from gui.components.side_panel import SidePanel
from gui.components.status_pill import StatusPill
from gui.components.view_header import ViewHeader
from gui.theme import Metrics, Theme
from utils.buttons import utilsButtons


class WatchingAnimeButton(utilsButtons.SidebarButton):
    """«Viendo»: la vista que sirve para seguir por donde ibas.

    Cascada a la izquierda —una AnimeRow por anime, con progreso— y a la
    derecha el panel de 290 px con lo último que estabas viendo. Sin
    paginador: son pocos y caben de una vez.

    Todo lo que se pinta sale de la biblioteca guardada: la vista funciona sin
    conexión. Lo único que sale a la red es la búsqueda del proveedor, que se
    suma a la local y nunca quita resultados, y abrir una ficha.
    """

    def __init__(self, main_window, icon_path, row, column):
        # El icono es bicolor (silueta negra, relleno blanco) y se lee sobre los
        # dos temas; no hay variante clara/oscura porque viendo_light/dark.png
        # son de tinta negra y una de las dos sería invisible según el tema.
        icon_path_light = icon_path_dark = os.path.join(icon_path, "viendo.png")
        super().__init__(main_window.sidebar_frame, "Viendo", row, column, self.show_watching_animes, icon_path_light, icon_path_dark)

        self.main_window = main_window
        self.anime_provider_mgr: AnimeProviderManager = AnimeProviderManagerSingleton()
        self.animes_persistence: AnimesPersistence = AnimesPersistenceSingleton()
        self.__list_frame: Optional[ctk.CTkFrame] = None
        # Buscador de la pestaña: coincidencias locales al instante, completadas
        # después con lo que encuentre el proveedor seleccionado.
        self.__search = utilsButtons.SavedAnimeSearch(
            main_window=main_window,
            anime_provider_mgr=self.anime_provider_mgr,
            get_saved_animes=self.animes_persistence.get_watching_animes,
            display_animes=self.__display_animes,
            is_still_visible=lambda: (self.__list_frame is not None and self.__list_frame.winfo_exists())
        )

    def show_frame(self):
        self.show_watching_animes()

    def show_watching_animes(self):
        self.main_window.clear_frame()
        self.__show_browser()

    # ------------------------------------------------------------------
    # Construcción de la vista
    # ------------------------------------------------------------------
    def __show_browser(self):
        content = self.main_window.content_frame
        content.grid_columnconfigure(0, weight=1)

        watching_animes: List[AnimeRecord] = self.animes_persistence.get_watching_animes()

        header = ViewHeader(content, "Viendo", self.__subtitle(watching_animes))
        header.grid(row=0, column=0, sticky="ew")
        self.__build_search_controls(header)

        if not watching_animes:
            empty_state = EmptyState(
                content,
                "No tienes nada a medias",
                icon=StatusPill.icon(AnimeStatus.WATCHING, EMPTY_ICON_SIZE, Theme.TXT_3, gap=0),
                hint="Marca un anime como «Viendo» desde su ficha y aparecerá aquí.",
                action_text="Ir a Pendientes",
                on_action=lambda: self.main_window.navigate_to("Pendientes")
            )
            empty_state.grid(row=1, column=0, pady=(60, 0))
            return

        body = ctk.CTkFrame(content, height=1, corner_radius=0, fg_color=Theme.TRANSPARENT)
        body.grid(row=1, column=0, sticky="ew", padx=Metrics.CONTENT_PAD_X, pady=(0, 24))
        body.grid_columnconfigure(0, weight=1)
        # El panel no lleva peso: son 290 px fijos y lo que sobra es para la lista.
        body.grid_columnconfigure(1, weight=0, minsize=Metrics.SIDE_PANEL_W)

        self.__list_frame = ctk.CTkFrame(body, height=1, corner_radius=0, fg_color=Theme.TRANSPARENT)
        self.__list_frame.grid(row=0, column=0, sticky="new")
        self.__list_frame.grid_columnconfigure(0, weight=1)

        side_record = self.__side_panel_record(watching_animes)
        if side_record is not None:
            side_panel = SidePanel(
                body,
                side_record,
                provider_name=self.__provider_name(side_record),
                # El botón lleva al episodio; el póster y el título, a la ficha a
                # secas. Es el mismo reparto que en la fila: la acción es la que
                # promete un episodio concreto, y solo ella tiene que cumplirlo.
                on_action=lambda _anime_id, record=side_record: self.__on_row_action(record),
                on_click=self.__on_anime_click
            )
            side_panel.grid(row=0, column=1, sticky="n", padx=(32, 0))

        self.__display_animes(watching_animes)

    def __build_search_controls(self, header: ViewHeader) -> None:
        """Buscador local de la pestaña, en la zona de controles de la cabecera."""
        search_entry = ctk.CTkEntry(
            header.controls_frame,
            placeholder_text="Buscar en viendo…",
            width=260,
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

    def __subtitle(self, watching_animes: List[AnimeRecord]) -> str:
        """«N animes a medias · M episodios pendientes».

        Los dos números salen de las filas guardadas; no se pregunta a nadie.
        """
        total = len(watching_animes)
        animes_text = "1 anime a medias" if total == 1 else f"{total} animes a medias"
        pending = 0
        for anime_record in watching_animes:
            _next_episode, episodes, _fraction = resume_progress(anime_record)
            if episodes:
                pending += episodes - len(set(anime_record.watched_episodes) & set(anime_record.episodes))
        if not pending:
            return animes_text
        return f"{animes_text} · {pending} episodio{'' if pending == 1 else 's'} pendiente{'' if pending == 1 else 's'}"

    def __side_panel_record(self, watching_animes: List[AnimeRecord]) -> Optional[AnimeRecord]:
        """Qué anime va en el panel de la derecha.

        Recorre los últimos vistos guardados y no solo el más reciente: si ese
        ya no está en «Viendo», sigue valiendo el siguiente. Si ninguno cuadra,
        el primero de la lista.

        :param watching_animes: Animes marcados como «Viendo».
        :return: Fila a mostrar en el panel, o None si la lista está vacía.
        """
        if not watching_animes:
            return None
        records_by_id = {str(record.anime_id): record for record in watching_animes}
        for anime_id in self.main_window.user_persistence.get_last_watched_ids():
            anime_record = records_by_id.get(str(anime_id))
            if anime_record is not None:
                return anime_record
        return watching_animes[0]

    def __provider_name(self, anime_record: AnimeRecord) -> str:
        """De qué sitio es la fila. Vacío mientras no se sepa, en vez de «desconocido»."""
        if anime_record.provider_id is None:
            return ""
        return self.anime_provider_mgr.get_provider_name(anime_record.provider_id)

    # ------------------------------------------------------------------
    # Lista
    # ------------------------------------------------------------------
    def __display_animes(self, watching_animes: List[AnimeRecord]):
        """Repinta la cascada. Lo llaman el arranque de la vista y el buscador.

        El panel de la derecha **no** se toca: enseña lo último que veías, que no
        depende de lo que se esté filtrando.
        """
        if self.__list_frame is None or not self.__list_frame.winfo_exists():
            return
        for widget in self.__list_frame.winfo_children():
            widget.destroy()

        if not watching_animes:
            empty_label = ctk.CTkLabel(
                self.__list_frame,
                text="Ningún anime de esta pestaña coincide con la búsqueda",
                font=Theme.font(*Theme.T_UI),
                text_color=Theme.TXT_2,
                anchor="w"
            )
            empty_label.grid(row=0, column=0, sticky="w", pady=(20, 0))
            return

        last_index = len(watching_animes) - 1
        for index, anime_record in enumerate(watching_animes):
            anime_row = AnimeRow(
                self.__list_frame,
                anime_record,
                poster_size=Metrics.ROW_WATCHING_POSTER,
                show_progress=True,
                action=self.__row_action(anime_record),
                on_click=self.__on_anime_click,
                provider_name=self.__provider_name(anime_record),
                show_separator=(index != last_index)
            )
            anime_row.grid(row=index, column=0, sticky="ew")

    def __row_action(self, anime_record: AnimeRecord) -> Optional[RowAction]:
        """La píldora «Episodio N →» que sale al pasar el ratón por la fila.

        No la lleva un anime del que ya has visto todo: ahí no hay siguiente
        episodio al que saltar.
        """
        next_episode, _episodes, _fraction = resume_progress(anime_record)
        if next_episode is None:
            return None
        return RowAction(f"Episodio {next_episode} →", self.__on_row_action)

    # ------------------------------------------------------------------
    # Navegación
    # ------------------------------------------------------------------
    def __search_anime(self, search_entry: ctk.CTkEntry):
        # Las dos búsquedas se suman: la local no depende del proveedor y la
        # del proveedor encuentra alias que el título guardado no conoce
        # ("Solo Leveling" -> "Ore dake Level Up na Ken"). Ver SavedAnimeSearch.
        self.__search.search(search_entry.get())

    def __on_row_action(self, anime_record: AnimeRecord):
        """Abre la ficha del anime con el próximo episodio ya desplegado.

        No fuerza orden ascendente (al revés que «Empezar» en Pendientes): con
        un anime largo servido de mayor a menor, forzarlo dejaría fuera de los
        25 primeros el episodio por el que va el usuario.

        :param anime_record: Fila cuya ficha se abre.
        """
        next_episode, _episodes, _fraction = resume_progress(anime_record)
        open_saved_anime(self.main_window, anime_record.anime_id, focus_episode=next_episode)

    def __on_anime_click(self, anime_id: Union[str, int]):
        """Abre la ficha de un anime de «Viendo» por el proveedor de su fila."""
        open_saved_anime(self.main_window, anime_id)
