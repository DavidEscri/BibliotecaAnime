__author__ = "Jose David Escribano Orts"
__subsystem__ = "sidebarButtons"
__module__ = "pendingAnimes.py"
__version__ = "0.9"
__info__ = {"subsystem": __subsystem__, "module_name": __module__, "version": __version__}

"""«Pendientes»: la cola de lo que todavía no has empezado.

Es la misma cascada que «Viendo», sin progreso que enseñar: la fila es más
baja y sin barra de progreso, con «N episodios · Proveedor» en su lugar. La
cabecera lleva orden por duración, y la fila una acción «Empezar» que mueve
el anime a «Viendo» y abre su ficha por el primer episodio.

Todo lo que se pinta sale de la biblioteca guardada: la vista funciona sin
conexión y no espera a nadie. Al entrar pide a ``EpisodeRefresher`` que
compruebe sus filas y repinta en el sitio las que cambien, **sin reordenar**:
una fila que salta de sitio bajo el cursor no es un refresco silencioso.
"""

import os
import customtkinter as ctk

from typing import Dict, List, Optional, Union

from APIs.common.animeProviderMgr import AnimeProviderManager, AnimeProviderManagerSingleton
from APIs.common.models import AnimeInfo
from dataPersistence.animesPersistence import AnimesPersistence, AnimesPersistenceSingleton, AnimeStatus, AnimeRecord
from dataPersistence.userPersistence import UserPersistence
from gui.anime_window import open_saved_anime, sync_saved_posters_async
from gui.components.anime_row import AnimeRow, RowAction
from gui.components.empty_state import EmptyState, ICON_SIZE as EMPTY_ICON_SIZE
from gui.components.order_menu import OrderMenu
from gui.components.resume_card import resume_progress
from gui.components.status_pill import StatusPill
from gui.components.view_header import ViewHeader
from gui.theme import Metrics, Theme
from utils.buttons import utilsButtons

#: Texto de cada criterio de orden en el desplegable. La clave es lo que se
#: persiste; así renombrar una opción no invalida la preferencia guardada.
ORDER_LABELS: Dict[str, str] = {
    UserPersistence.PENDING_ORDER_SHORTEST: "Más cortos primero",
    UserPersistence.PENDING_ORDER_LONGEST:  "Más largos primero",
    UserPersistence.PENDING_ORDER_TITLE:    "Título (A-Z)",
}


class PendingAnimeButton(utilsButtons.SidebarButton):
    """La cola de pendientes: qué tienes por ver y cuánto dura cada cosa."""

    #: Ancho al que se recorta el título. Esta vista no tiene panel lateral, así
    #: que le sobra sitio comparada con «Viendo» (que se queda en los 420 por
    #: defecto de ``AnimeRow``).
    TITLE_W: int = 660

    def __init__(self, main_window, icon_path, row, column):
        # pendientes_light/dark.png son los dos de tinta negra, así que no sirven
        # como par (claro, oscuro); se usa el icono único, que es bicolor.
        icon_path_light = icon_path_dark = os.path.join(icon_path, "pendientes.png")
        super().__init__(main_window.sidebar_frame, "Pendientes", row, column, self.__show_pending_animes, icon_path_light, icon_path_dark)

        self.main_window = main_window
        self.anime_provider_mgr: AnimeProviderManager = AnimeProviderManagerSingleton()
        self.animes_persistence: AnimesPersistence = AnimesPersistenceSingleton()
        self.__list_frame: Optional[ctk.CTkFrame] = None
        #: Criterio elegido; se persiste entre sesiones.
        self.__order: str = UserPersistence.PENDING_ORDER_SHORTEST
        #: Última lista pintada, sin ordenar. Hace falta para que cambiar el
        #: orden reordene **lo que hay en pantalla** y no deshaga la búsqueda.
        self.__displayed_animes: List[AnimeRecord] = []
        self.__header: Optional[ViewHeader] = None
        #: Filas de la cascada en pantalla, por ``anime_id``.
        self.__rows: Dict[str, AnimeRow] = {}
        #: Todo «Pendientes», no solo lo filtrado: de aquí sale el subtítulo.
        self.__pending_animes: List[AnimeRecord] = []
        main_window.episode_refresher.subscribe(self.__on_episodes_refreshed)
        # Buscador de la pestaña: coincidencias locales al instante, completadas
        # después con lo que encuentre el proveedor seleccionado.
        self.__search = utilsButtons.SavedAnimeSearch(
            main_window=main_window,
            anime_provider_mgr=self.anime_provider_mgr,
            get_saved_animes=self.animes_persistence.get_pending_animes,
            display_animes=self.__display_animes,
            is_still_visible=lambda: (self.__list_frame is not None and self.__list_frame.winfo_exists())
        )

    def show_frame(self):
        self.__show_pending_animes()

    def __show_pending_animes(self):
        self.main_window.clear_frame()
        self.__show_browser()

    # ------------------------------------------------------------------
    # Construcción de la vista
    # ------------------------------------------------------------------
    def __show_browser(self):
        content = self.main_window.content_frame
        content.grid_columnconfigure(0, weight=1)

        self.__order = self.main_window.user_persistence.get_pending_order()
        pending_animes: List[AnimeRecord] = self.animes_persistence.get_pending_animes()
        self.__pending_animes = pending_animes
        self.__rows = {}

        header = ViewHeader(content, "Pendientes", self.__subtitle(pending_animes))
        header.grid(row=0, column=0, sticky="ew")
        self.__header = header
        self.__build_controls(header)

        if not pending_animes:
            empty_state = EmptyState(
                content,
                "No tienes nada en la cola",
                icon=StatusPill.icon(AnimeStatus.PENDING, EMPTY_ICON_SIZE, Theme.TXT_3, gap=0),
                hint="Marca un anime como «Pendiente» desde su ficha y aparecerá aquí.",
                action_text="Buscar un anime",
                on_action=lambda: self.main_window.navigate_to("Buscar")
            )
            empty_state.grid(row=1, column=0, pady=(60, 0))
            return

        self.__list_frame = ctk.CTkFrame(content, height=1, corner_radius=0, fg_color=Theme.TRANSPARENT)
        self.__list_frame.grid(row=1, column=0, sticky="new", padx=Metrics.CONTENT_PAD_X, pady=(0, 24))
        self.__list_frame.grid_columnconfigure(0, weight=1)

        self.__display_animes(pending_animes)
        self.main_window.episode_refresher.refresh(self.__sort_animes(pending_animes), urgent=True)

    def __build_controls(self, header: ViewHeader) -> None:
        """Orden y buscador local, en la zona de controles de la cabecera."""
        order_optionmenu = OrderMenu(header.controls_frame, values=list(ORDER_LABELS.values()),
                                     command=self.__on_order_changed)
        order_optionmenu.set(ORDER_LABELS[self.__order])
        order_optionmenu.grid(row=0, column=0, padx=(0, 14))

        search_entry = ctk.CTkEntry(
            header.controls_frame,
            placeholder_text="Buscar en pendientes…",
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

    def __subtitle(self, pending_animes: List[AnimeRecord]) -> str:
        """«N animes en cola · M episodios».

        Los dos números salen de las filas guardadas; no se pregunta a nadie. Los
        episodios se suman solo de las filas que los tengan: una guardada sin
        abrir su ficha no aporta ninguno, y prometer un total inventado sería
        peor que quedarse corto.
        """
        total = len(pending_animes)
        animes_text = "1 anime en cola" if total == 1 else f"{total} animes en cola"
        episodes = sum(len(anime_record.episodes or []) for anime_record in pending_animes)
        if not episodes:
            return animes_text
        return f"{animes_text} · {episodes} episodio{'' if episodes == 1 else 's'}"

    def __provider_name(self, anime_record: AnimeRecord) -> str:
        """De qué sitio es la fila. Vacío mientras no se sepa, en vez de «desconocido»."""
        if anime_record.provider_id is None:
            return ""
        return self.anime_provider_mgr.get_provider_name(anime_record.provider_id)

    def __meta_text(self, anime_record: AnimeRecord) -> str:
        """«N episodios · Proveedor», el texto de la derecha de la fila.

        Sustituye a la barra de progreso: es el dato con el que se elige qué
        empezar. Cada mitad se cae sola si no se sabe, sin dejar el separador
        colgando.
        """
        parts: List[str] = []
        episodes = len(anime_record.episodes or [])
        if episodes:
            parts.append(f"{episodes} episodio{'' if episodes == 1 else 's'}")
        provider_name = self.__provider_name(anime_record)
        if provider_name:
            parts.append(provider_name)
        return " · ".join(parts)

    # ------------------------------------------------------------------
    # Orden
    # ------------------------------------------------------------------
    def __on_order_changed(self, label: str) -> None:
        """Guarda el criterio y reordena lo que ya está en pantalla, sin deshacer la búsqueda."""
        for order, order_label in ORDER_LABELS.items():
            if order_label == label:
                self.__order = order
                break
        self.main_window.user_persistence.set_pending_order(self.__order)
        self.__display_animes(self.__displayed_animes)

    def __sort_animes(self, pending_animes: List[AnimeRecord]) -> List[AnimeRecord]:
        """Ordena por el criterio elegido en la cabecera.

        Una fila sin lista de episodios no es "corta", es desconocida: va al
        final en los dos sentidos de la duración.

        :param pending_animes: Pendientes a ordenar.
        :return: Lista ordenada.
        """
        if self.__order == UserPersistence.PENDING_ORDER_TITLE:
            return sorted(pending_animes, key=lambda record: AnimeProviderManager.normalize_title(record.title))

        known = [record for record in pending_animes if record.episodes]
        unknown = [record for record in pending_animes if not record.episodes]
        known.sort(key=lambda record: len(record.episodes), reverse=(self.__order == UserPersistence.PENDING_ORDER_LONGEST))
        return known + unknown

    # ------------------------------------------------------------------
    # Lista
    # ------------------------------------------------------------------
    def __display_animes(self, pending_animes: List[AnimeRecord]):
        """Repinta la cascada. Lo llaman el arranque de la vista, el buscador y el orden."""
        if self.__list_frame is None or not self.__list_frame.winfo_exists():
            return
        for widget in self.__list_frame.winfo_children():
            widget.destroy()
        self.__rows = {}

        self.__displayed_animes = pending_animes

        if not pending_animes:
            empty_label = ctk.CTkLabel(
                self.__list_frame,
                text="Ningún anime de esta pestaña coincide con la búsqueda",
                font=Theme.font(*Theme.T_UI),
                text_color=Theme.TXT_2,
                anchor="w"
            )
            empty_label.grid(row=0, column=0, sticky="w", pady=(20, 0))
            return

        sorted_animes = self.__sort_animes(pending_animes)
        last_index = len(sorted_animes) - 1
        for index, anime_record in enumerate(sorted_animes):
            anime_row = AnimeRow(
                self.__list_frame,
                anime_record,
                poster_size=Metrics.ROW_PENDING_POSTER,
                show_progress=False,
                action=self.__row_action(),
                on_click=self.__on_anime_click,
                meta_text=self.__meta_text(anime_record),
                text_width=self.TITLE_W,
                show_separator=(index != last_index)
            )
            anime_row.grid(row=index, column=0, sticky="ew")
            self.__rows[str(anime_record.anime_id)] = anime_row

    def __row_action(self) -> RowAction:
        """:return: La píldora «Empezar», la misma para todas las filas."""
        return RowAction("Empezar", self.__on_start_watching)

    def __on_episodes_refreshed(self, anime_record: AnimeRecord) -> None:
        """Repinta en el sitio la duración de la fila y el subtítulo, si el anime está en la cola.

        No reordena: la fila se moverá a su sitio en la siguiente visita.

        :param anime_record: Fila ya releída de la BD.
        """
        anime_id = str(anime_record.anime_id)
        if not any(str(record.anime_id) == anime_id for record in self.__pending_animes):
            return

        def _replace(records: List[AnimeRecord]) -> List[AnimeRecord]:
            return [anime_record if str(record.anime_id) == anime_id else record for record in records]

        self.__pending_animes = _replace(self.__pending_animes)
        self.__displayed_animes = _replace(self.__displayed_animes)

        if self.__header is not None and self.__header.winfo_exists():
            self.__header.set_subtitle(self.__subtitle(self.__pending_animes))
        anime_row = self.__rows.get(anime_id)
        if anime_row is not None and anime_row.winfo_exists():
            anime_row.update_record(anime_record, action=self.__row_action(),
                                    meta_text=self.__meta_text(anime_record))

    # ------------------------------------------------------------------
    # Navegación y acciones
    # ------------------------------------------------------------------
    def __search_anime(self, search_entry: ctk.CTkEntry):
        # Las dos búsquedas se suman: la local no depende del proveedor y la
        # del proveedor encuentra alias que el título guardado no conoce
        # ("Solo Leveling" -> "Ore dake Level Up na Ken"). Ver SavedAnimeSearch.
        self.__search.search(search_entry.get())

    def __on_start_watching(self, anime_record: AnimeRecord):
        """«Empezar»: mueve el anime a «Viendo» y abre su ficha por el primer episodio.

        El AnimeInfo se construye desde la fila guardada, no desde datos del
        proveedor: su anime_id es el slug del sitio que la guardó, y usar otro
        insertaría una fila nueva en vez de mover ésta.

        :param anime_record: Fila a mover de pendientes a viendo.
        """
        anime_info = AnimeInfo(
            id=anime_record.anime_id,
            title=anime_record.title,
            poster=anime_record.poster_url,
            synopsis=anime_record.synopsis,
            genres=anime_record.genres,
            provider_id=anime_record.provider_id
        )
        if not self.animes_persistence.update_anime_to_watching(anime_info):
            print(f"No se pudo mover {anime_record.title!r} a «Viendo»")
            return
        print(f"{anime_record.title} movido de pendientes a viendo.")

        sync_saved_posters_async(self.animes_persistence, anime_info)
        self.__refresh_library_counts()
        # El episodio sale de resume_progress() y no de un 1 fijo: si el anime
        # volvió a la cola a medias, "empezar" sigue por donde se dejó.
        # force_ascending garantiza que detrás vayan el 2 y el 3 aunque el
        # proveedor sirva la lista al revés.
        next_episode, _episodes, _fraction = resume_progress(anime_record)
        open_saved_anime(self.main_window, anime_record.anime_id,
                         focus_episode=next_episode, force_ascending=True)

    def __refresh_library_counts(self) -> None:
        """Repone los dos contadores que cambian al empezar un anime.

        Las listas del hub solo se llenan al arrancar la aplicación; sin
        releerlas, la barra lateral seguiría diciendo que hay un pendiente más y
        un «viendo» menos hasta el siguiente arranque.
        """
        self.main_window.pending_animes = self.animes_persistence.get_pending_animes()
        self.main_window.watching_animes = self.animes_persistence.get_watching_animes()
        self.main_window.refresh_sidebar_counts()

    def __on_anime_click(self, anime_id: Union[str, int]):
        """Abre la ficha de un pendiente por el proveedor de su fila."""
        open_saved_anime(self.main_window, anime_id)
