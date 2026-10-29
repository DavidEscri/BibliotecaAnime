__author__ = "Jose David Escribano Orts"
__subsystem__ = "gui"
__module__ = "main_window.py"
__version__ = "0.10"
__info__ = {"subsystem": __subsystem__, "module_name": __module__, "version": __version__}

import copy
import ctypes
import threading
import tkinter
import customtkinter as ctk

from tkinter import messagebox
from ctypes import wintypes
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple
from PIL import Image, ImageSequence

from APIs.animeav1.animeav1 import AnimeAV1Singleton
from APIs.animeflv.animeflv import AnimeFLVSingleton
from APIs.jkanime.jkanime import JKAnimeSingleton
from APIs.common.animeProviderMgr import AnimeProviderManagerSingleton, AnimeProviderManager
from APIs.common.models import AnimeInfo, AnimeProviderId
from dataPersistence.animesPersistence import AnimesPersistenceSingleton, AnimesPersistence, AnimeRecord
from dataPersistence.userPersistence import UserPersistenceSingleton, UserPersistence
from gui.sidebarButtons.favouriteAnimes.favouriteAnimes import FavouritesButton
from gui.sidebarButtons.finishedAnimes.finishedAnimes import FinishedAnimeButton
from gui.sidebarButtons.pendingAnimes.pendingAnimes import PendingAnimeButton
from gui.sidebarButtons.recentAnimes.recentAnimes import RecentAnimeButton
from gui.sidebarButtons.searchAnimes.searchAnimes import SearchButton, AnimeSearch
from gui.sidebarButtons.watchingAnimes.watchingAnimes import WatchingAnimeButton
from gui.components.sidebar import Sidebar
from gui.episode_refresher import EpisodeRefresher
from gui.franchise_service import FranchiseService
from gui.theme import Metrics, Theme

from utils.utils import get_resource_path, download_images_progress, download_animes_poster


@dataclass
class ViewPage:
    """Página conservada de una vista: su marco y la firma de lo que tiene pintado."""

    frame: ctk.CTkFrame
    signature: Any


class MainWindow(ctk.CTk):
    """Ventana principal y hub compartido de la aplicación.

    Mantiene el contenido, la barra lateral, las listas de animes cacheadas,
    la persistencia y el gestor de proveedores; cada vista recibe la instancia
    y muta ese estado directamente.
    """

    MAIN_WINDOW_ANCHO = 1440
    MAIN_WINDOW_LARGO = 910

    def __init__(self):
        super().__init__()
        self.__config_main_window()
        self.__config_main_frames()

        self.animes_persistence: AnimesPersistence = AnimesPersistenceSingleton()
        self.anime_provider_mgr: AnimeProviderManager = AnimeProviderManagerSingleton()
        # El orden de registro es el orden del fallback.
        self.anime_provider_mgr.register(AnimeAV1Singleton(), default=True)
        self.anime_provider_mgr.register(JKAnimeSingleton())
        self.anime_provider_mgr.register(AnimeFLVSingleton())

        # Se leen aquí, de forma síncrona (SQLite local, no red), porque el
        # desplegable de proveedor y el predeterminado deben estar listos antes
        # de la primera llamada a get_recent_animes().
        self.user_persistence: UserPersistence = UserPersistenceSingleton()
        self.user_persistence.start()
        # Proveedor fijado con el pin. None = sin preferencia guardada, en cuyo
        # caso manda el predeterminado del registro.
        self.__pinned_provider_id: AnimeProviderId | None = None
        # Predeterminado del registro antes de aplicar ninguna preferencia: es la
        # referencia contra la que se decide si el desplegable está desviado, y
        # hay que capturarlo antes de que __apply_saved_provider_preference() lo
        # sobrescriba con set_default().
        self.__registry_default_provider_id: AnimeProviderId | None = self.anime_provider_mgr.get_default_provider_id()
        self.__apply_saved_provider_preference()

        # Evita que dos cambios de proveedor seguidos lancen hilos que se pisen
        # al escribir self.recent_animes.
        self.__reloading_recent_animes: bool = False
        # Se incrementa en cada recarga: la precarga en segundo plano comprueba que
        # su generación sigue vigente antes de escribir en la lista.
        self.__recent_animes_generation: int = 0

        self.__recent_animes_button: RecentAnimeButton | None = None
        self.__favourites_animes_button: FavouritesButton | None = None
        self.__finished_animes_button: FinishedAnimeButton | None = None
        self.__watching_animes_button: WatchingAnimeButton | None = None
        self.__pending_animes_button: PendingAnimeButton | None = None
        self.__search_animes_button: SearchButton | None = None

        self.recent_animes: List[AnimeRecord | AnimeInfo] = []
        self.favourite_animes: List[AnimeRecord] = []
        self.finished_animes: List[AnimeRecord] = []
        self.watching_animes: List[AnimeRecord] = []
        self.pending_animes: List[AnimeRecord] = []
        self.last_search_instance: AnimeSearch | None = None
        self.images_path = get_resource_path("resources/images/recent_animes")
        # Antes que las vistas: se suscriben a él al construirse.
        self.episode_refresher: EpisodeRefresher = EpisodeRefresher(self, self.anime_provider_mgr,
                                                                    self.animes_persistence)
        self.franchise_service: FranchiseService = FranchiseService(self, self.anime_provider_mgr)

        self.load_sidebar_buttons()
        self.protocol("WM_DELETE_WINDOW", self.__on_close)
        self.__bind_window_configure()
        self.show_loading_screen()

    def __config_main_window(self):
        """Configura tamaño, posición e icono de la ventana principal."""
        self.title("Mi Biblioteca")
        pantalla_ancho = self.winfo_screenwidth()
        pantalla_largo = self.winfo_screenheight()
        x = int((pantalla_ancho / 2) - (self.MAIN_WINDOW_ANCHO / 2))
        y = int((pantalla_largo / 2) - (self.MAIN_WINDOW_LARGO / 2))
        self.geometry(f"{self.MAIN_WINDOW_ANCHO}x{self.MAIN_WINDOW_LARGO}+{x}+{y}")
        self.iconbitmap(get_resource_path("resources/images/utils/app_icon.ico"))
        self.configure(fg_color=Theme.BG)

        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure((0, 1, 2), weight=1)

    def __config_main_frames(self):
        """Prepara el contenedor de contenido; la barra lateral se construye después.

        sidebar_frame se declara ya a None porque las seis vistas se instancian
        antes que la barra y guardan una referencia a este atributo.
        """
        self.sidebar_frame: Sidebar | None = None
        self.content_frame: ctk.CTkScrollableFrame = self.create_content_frame()
        # Hermano de content_frame y no hijo: una superficie nativa dentro de un
        # CTkScrollableFrame se desplaza con el lienzo. Nace oculto y con alto
        # explícito, porque un CTkFrame vacío pide 200 × 200 y estiraría la fila.
        self.player_frame: ctk.CTkFrame = ctk.CTkFrame(
            self,
            height=Metrics.PLAYER_VIDEO_H + Metrics.PLAYER_BAR_H,
            corner_radius=0,
            fg_color=Theme.BG
        )
        #: Quien tiene el reproductor abierto; su close() lo para y lo retira.
        self.__player_owner: Optional[Any] = None
        #: Geometría, maximizado y ancho mínimo de la barra lateral de antes de
        #: la pantalla completa; None fuera de ella.
        self.__fullscreen_restore: Optional[Tuple[str, bool, int]] = None
        #: Página de cada vista de la barra lateral, por vista. Viven toda la sesión.
        self.__view_pages: Dict[Any, ViewPage] = {}

    def clear_frame(self):
        """Vacía el content_frame: esconde las páginas de las vistas y destruye lo demás.

        Lo demás es la ficha, que se rehace cada vez. Cambiar de vista pasa
        siempre por aquí, así que también cierra el reproductor si estaba
        abierto: si no, mpv seguiría sonando debajo.
        """
        self.close_player()
        page_frames = [page.frame for page in self.__view_pages.values()]
        for widget in self.content_frame.winfo_children():
            if any(widget is frame for frame in page_frames):
                widget.grid_remove()
            else:
                widget.destroy()

    def show_view(self, view: Any, signature: Any) -> Optional[ctk.CTkFrame]:
        """Enseña la página de una vista: la que ya tenía si sus datos no han cambiado.

        Reconstruir una vista cuesta cientos de milisegundos de widgets nuevos.
        La firma es lo que la vista pinta, sacado de lo que ya lee al entrar:
        si coincide con la de la última vez, la página se vuelve a colocar tal
        cual; si no, se vacía para que la vista construya encima.

        :param view: Vista de la barra lateral que se quiere enseñar.
        :param signature: Datos de los que depende lo pintado, comparables con ``==``.
            Se guarda una copia: la vista puede modificar sus filas en memoria.
        :return: ``None`` si se ha reutilizado la página, o la página vacía donde construir.
        """
        self.clear_frame()
        page = self.__view_pages.get(view)
        reused = page is not None and page.signature == signature
        if page is None:
            frame = ctk.CTkFrame(self.content_frame, width=1, height=1, corner_radius=0,
                                 fg_color=Theme.TRANSPARENT)
            frame.grid_columnconfigure(0, weight=1)
            page = ViewPage(frame, copy.deepcopy(signature))
            self.__view_pages[view] = page
        elif not reused:
            for widget in page.frame.winfo_children():
                widget.destroy()
            page.signature = copy.deepcopy(signature)
        page.frame.grid(row=0, column=0, sticky=ctk.NSEW)
        # Toda vista entra arriba, venga de donde venga el desplazamiento.
        self.content_frame._parent_canvas.yview_moveto(0)
        if reused:
            return None
        if page.frame.winfo_width() <= 1:
            # Recién creada no mide nada todavía, y las rejillas sacan sus columnas
            # del ancho de la página: sin esto pintarían las del diseño y repintarían.
            page.frame.update_idletasks()
        return page.frame

    def create_content_frame(self) -> ctk.CTkScrollableFrame:
        """:return: CTkScrollableFrame compartido por todas las vistas, ya en el grid."""
        main_frame = ctk.CTkScrollableFrame(
            self,
            corner_radius=0,
            fg_color=Theme.BG
        )
        main_frame.grid(row=0, column=1, rowspan=8, sticky=ctk.NSEW)

        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        return main_frame

    # ------------------------------------------------------------------
    # Reproductor acoplado encima de la ficha
    # ------------------------------------------------------------------
    def show_player_frame(self, owner: Any) -> ctk.CTkFrame:
        """Muestra el panel del reproductor en la fila de encima de content_frame.

        content_frame no se destruye: encoge y la ficha sigue debajo tal y como
        estaba. Si otro dueño tenía el panel, se le cierra primero.

        :param owner: Objeto con ``close_player()``, que para el reproductor, y
            ``relayout_player()``, que lo reajusta al cambiar el tamaño de la ventana.
        :return: El frame donde el dueño compone el panel.
        """
        if self.__player_owner is not None and self.__player_owner is not owner:
            self.close_player()
        self.__player_owner = owner
        self.grid_rowconfigure(0, weight=0)
        self.player_frame.grid(row=0, column=1, sticky="ew",
                               padx=Metrics.CONTENT_PAD_X, pady=(Metrics.PLAYER_PAD_TOP, Metrics.PLAYER_PAD_BOTTOM))
        self.content_frame.grid(row=1, column=1, rowspan=7, sticky=ctk.NSEW)
        return self.player_frame

    def hide_player_frame(self) -> None:
        """Retira el panel del reproductor y devuelve a content_frame toda la columna.

        La fila 0 recupera su peso: la configuración de rejilla sobrevive a que
        se quiten sus widgets.
        """
        if self.__fullscreen_restore is not None:
            self.exit_player_fullscreen()
        self.__player_owner = None
        for widget in self.player_frame.winfo_children():
            widget.destroy()
        self.player_frame.grid_remove()
        self.content_frame.grid(row=0, column=1, rowspan=8, sticky=ctk.NSEW)
        self.grid_rowconfigure(0, weight=1)

    def close_player(self) -> None:
        """Cierra el reproductor si hay uno abierto y retira su panel. Sin efecto si no lo hay."""
        owner, self.__player_owner = self.__player_owner, None
        if owner is not None:
            try:
                owner.close_player()
            except Exception as exc:
                print(f"Error al cerrar el reproductor: {exc}")
        if self.player_frame.winfo_manager():
            self.hide_player_frame()

    def is_player_fullscreen(self) -> bool:
        """:return: True mientras el reproductor ocupa la pantalla entera."""
        return self.__fullscreen_restore is not None

    def enter_player_fullscreen(self) -> None:
        """Deja solo el panel del reproductor, a pantalla completa en el monitor de la ventana.

        No usa ``-fullscreen``, que con dos monitores lleva la ventana al
        principal: quita el marco y ocupa el rectángulo del monitor donde está.
        """
        if self.__fullscreen_restore is not None:
            return
        left, top, right, bottom = self.__monitor_rect()
        was_zoomed = self.state() == "zoomed"
        if was_zoomed:
            self.state("normal")
            self.update_idletasks()
        # tkinter.Tk y no CTk: la de CTk aplica el escalado de DPI y el
        # rectángulo del monitor ya viene en píxeles físicos.
        saved_geometry = tkinter.Tk.wm_geometry(self)
        sidebar_minsize = int(self.grid_columnconfigure(0).get("minsize", 0))
        self.__fullscreen_restore = (saved_geometry, was_zoomed, sidebar_minsize)

        if self.sidebar_frame is not None:
            self.sidebar_frame.grid_remove()
        self.content_frame.grid_remove()
        # El minsize de la columna de la barra sobrevive a quitarla: sin esto
        # quedaría una franja del ancho de la barra a la izquierda del vídeo.
        self.grid_columnconfigure(0, minsize=0)
        self.grid_rowconfigure(0, weight=1)
        self.player_frame.grid(row=0, column=0, columnspan=2, rowspan=8, sticky="nsew", padx=0, pady=0)

        self.overrideredirect(True)
        tkinter.Tk.wm_geometry(self, f"{right - left}x{bottom - top}+{left}+{top}")
        self.update_idletasks()

    def exit_player_fullscreen(self) -> None:
        """Vuelve de la pantalla completa a la ventana y la disposición de antes.

        La barra lateral vuelve plegada o desplegada como estaba: ese estado es
        suyo y aquí no se toca.
        """
        if self.__fullscreen_restore is None:
            return
        saved_geometry, was_zoomed, sidebar_minsize = self.__fullscreen_restore
        self.__fullscreen_restore = None

        self.overrideredirect(False)
        tkinter.Tk.wm_geometry(self, saved_geometry)
        if was_zoomed:
            self.state("zoomed")

        self.grid_columnconfigure(0, minsize=sidebar_minsize)
        self.grid_rowconfigure(0, weight=0)
        self.player_frame.grid(row=0, column=1, columnspan=1, rowspan=1, sticky="ew",
                               padx=Metrics.CONTENT_PAD_X, pady=(Metrics.PLAYER_PAD_TOP, Metrics.PLAYER_PAD_BOTTOM))
        self.content_frame.grid(row=1, column=1, rowspan=7, sticky=ctk.NSEW)
        if self.sidebar_frame is not None:
            self.sidebar_frame.grid()
        self.update_idletasks()

    def __monitor_rect(self) -> Tuple[int, int, int, int]:
        """:return: (izquierda, arriba, derecha, abajo) del monitor donde está la ventana."""

        class MonitorInfo(ctypes.Structure):
            _fields_ = [("cbSize", wintypes.DWORD), ("rcMonitor", wintypes.RECT),
                        ("rcWork", wintypes.RECT), ("dwFlags", wintypes.DWORD)]

        try:
            user32 = ctypes.windll.user32
            user32.MonitorFromWindow.restype = wintypes.HANDLE
            user32.MonitorFromWindow.argtypes = [wintypes.HWND, wintypes.DWORD]
            # 2 = MONITOR_DEFAULTTONEAREST: el monitor que más ventana tiene.
            monitor = user32.MonitorFromWindow(wintypes.HWND(int(self.wm_frame(), 16)), 2)
            info = MonitorInfo()
            info.cbSize = ctypes.sizeof(MonitorInfo)
            if user32.GetMonitorInfoW(monitor, ctypes.byref(info)):
                rect = info.rcMonitor
                return rect.left, rect.top, rect.right, rect.bottom
        except Exception as exc:
            print(f"No se pudo leer el monitor de la ventana: {exc}")
        return 0, 0, self.winfo_screenwidth(), self.winfo_screenheight()

    def __bind_window_configure(self) -> None:
        """Ata el <Configure> de la raíz descartando en Tcl el de los demás widgets.

        Por los bindtags, el <Configure> de cualquier widget llega también a la raíz,
        cientos de veces por cambio de vista. Sustituye al de CTk, que tiene el mismo
        coste, y lo conserva dentro del filtro.
        """
        ctk_command = self.register(self._update_dimensions_event)
        own_command = self.register(self.__on_window_configure)
        self.tk.call("bind", self._w, "<Configure>",
                     f'if {{"%W" eq "{self._w}"}} {{{ctk_command}; {own_command}}}')

    def __on_window_configure(self) -> None:
        """Reajusta el reproductor al cambiar el tamaño de la ventana, también solo en alto."""
        if self.__player_owner is not None:
            self.__player_owner.relayout_player()

    def __on_close(self) -> None:
        """Cierra la aplicación parando antes el reproductor, para no dejar mpv vivo."""
        self.close_player()
        self.destroy()

    def load_sidebar_buttons(self) -> None:
        """Instancia las seis vistas y construye la barra lateral con ellas.

        El orden de la lista es el orden en que se ven en la barra.
        """
        icon_path = get_resource_path("resources/images/utils")
        # row y column ya no se usan para pintar: SidebarButton solo describe el
        # destino y se conservan en la firma para no tocar las seis vistas.
        self.__recent_animes_button: RecentAnimeButton = RecentAnimeButton(self, icon_path, 0, 0)
        self.__favourites_animes_button: FavouritesButton = FavouritesButton(self, icon_path, 0, 0)
        self.__watching_animes_button: WatchingAnimeButton = WatchingAnimeButton(self, icon_path, 0, 0)
        self.__pending_animes_button: PendingAnimeButton = PendingAnimeButton(self, icon_path, 0, 0)
        self.__finished_animes_button: FinishedAnimeButton = FinishedAnimeButton(self, icon_path, 0, 0)
        self.__search_animes_button: SearchButton = SearchButton(self, icon_path, 0, 0)

        destinations = [
            self.__recent_animes_button,
            self.__favourites_animes_button,
            self.__watching_animes_button,
            self.__pending_animes_button,
            self.__finished_animes_button,
            self.__search_animes_button,
        ]
        # Los contadores salen de las listas cacheadas del hub, no de la BD.
        counter_providers = {
            self.__recent_animes_button.sidebar_text:     lambda: len(self.recent_animes),
            self.__favourites_animes_button.sidebar_text: lambda: len(self.favourite_animes),
            self.__watching_animes_button.sidebar_text:   lambda: len(self.watching_animes),
            self.__pending_animes_button.sidebar_text:    lambda: len(self.pending_animes),
            self.__finished_animes_button.sidebar_text:   lambda: len(self.finished_animes),
        }

        self.sidebar_frame = Sidebar(self, destinations, counter_providers)
        self.sidebar_frame.grid(row=0, column=0, rowspan=8, sticky="nsew")
        self.sidebar_frame.set_active(self.__recent_animes_button)
        self.__refresh_pin_provider_button()
        ctk.set_appearance_mode("System")

    def refresh_sidebar_counts(self) -> None:
        """Repinta los contadores de la barra lateral.

        Punto de entrada para las fases siguientes: se llama después de guardar o
        de quitar un anime, cuando las listas cacheadas del hub ya se han
        actualizado. Tolera que la barra aún no exista (arranque).
        """
        if self.sidebar_frame is not None:
            self.sidebar_frame.refresh_counts()

    def navigate_to(self, sidebar_text: str) -> bool:
        """Abre otra vista por su etiqueta de barra lateral.

        Es lo que usan los botones de los estados vacíos («Ir a Pendientes»,
        «Buscar un anime»): navegar desde el contenido tiene que dejar la barra
        marcando el destino igual que si se hubiera pulsado allí.

        :return: ``False`` si no hay barra todavía o la etiqueta no existe.
        """
        if self.sidebar_frame is None:
            return False
        return self.sidebar_frame.navigate_to(sidebar_text)

    def retry_recent_animes(self) -> None:
        """Vuelve a pedir los estrenos al proveedor. Lo llama «Reintentar».

        Es el mismo camino que recorre el cambio de proveedor —hilo daemon,
        descarga de pósters y repintado de la portada—, porque el problema es el
        mismo: la lista está vacía y hay que ir a buscarla otra vez.
        """
        self.__reload_recent_animes()

    def set_active_sidebar_destination(self, destination) -> None:
        """Marca qué destino está activo cuando la navegación no viene de un clic.

        El arranque y la recarga de proveedor llaman a ``show_frame()``
        directamente, y sin esto la barra se quedaría señalando otra vista.
        """
        if self.sidebar_frame is not None:
            self.sidebar_frame.set_active(destination)

    # ------------------------------------------------------------------
    # Proveedor de anime
    # ------------------------------------------------------------------
    def __apply_saved_provider_preference(self) -> None:
        """Aplica el proveedor predeterminado guardado en DB_user.db, si lo hay."""
        saved_value = self.user_persistence.get_default_provider_id()
        if saved_value is None:
            current_provider_id = self.anime_provider_mgr.get_default_provider_id()
            print(f"Sin proveedor fijado, se usa "
                  f"{current_provider_id.value if current_provider_id else 'ninguno'}")
            return
        try:
            # ValueError (enum ya no existe) o UnknownProviderError (existe pero no
            # está registrado) acaban igual: se ignora la preferencia guardada.
            saved_provider_id = AnimeProviderId(saved_value)
            self.anime_provider_mgr.set_default(saved_provider_id)
            self.__pinned_provider_id = saved_provider_id
            print(f"Proveedor fijado por el usuario: {saved_provider_id.value}")
        except Exception as e:
            print(f"El proveedor fijado ({saved_value}) no es válido: {e}")

    def change_anime_provider_event(self, new_provider_name: str) -> None:
        """Cambia el proveedor **solo para esta sesión** y recarga los recientes.

        No escribe en DB_user.db: fijar el predeterminado es una acción aparte
        (el pin). Así se puede probar otro proveedor sin tocar la configuración.
        """
        provider_info = self.anime_provider_mgr.get_provider_info_by_name(new_provider_name)
        if provider_info is None:
            print(f"Proveedor no reconocido: {new_provider_name!r}")
            return
        if provider_info.id == self.anime_provider_mgr.get_default_provider_id():
            return

        self.anime_provider_mgr.set_default(provider_info.id)
        print(f"Proveedor de anime cambiado a {new_provider_name} (solo esta sesión)")
        self.__refresh_pin_provider_button()
        self.__reload_recent_animes()

    def toggle_pinned_provider_event(self) -> None:
        """Fija el proveedor seleccionado como predeterminado, o lo desfija.

        Fijado significa «este es el que quiero al arrancar». Al desfijar no hace
        falta borrar la fila: ``get_setting()`` ya devuelve el valor por defecto
        cuando ``setting_value`` es NULL, y sin preferencia manda el
        predeterminado del registro.
        """
        current_provider_id = self.anime_provider_mgr.get_default_provider_id()
        if current_provider_id is None:
            return

        pin_it = current_provider_id != self.__pinned_provider_id
        new_pinned_id = current_provider_id if pin_it else None
        # Frontera hacia la BD: se persiste el valor del enum, no el miembro.
        if not self.user_persistence.set_default_provider_id(new_pinned_id.value if new_pinned_id is not None else None):
            # La sesión sigue siendo válida; lo único que falla es recordarlo.
            print(f"No se pudo guardar el proveedor fijado ({new_pinned_id})")
            messagebox.showwarning(
                "Aviso!",
                "No se ha podido guardar la preferencia de proveedor.\n\n"
                "El proveedor seleccionado sigue en uso durante esta sesión."
            )
            return

        self.__pinned_provider_id = new_pinned_id
        print(f"Proveedor {current_provider_id.value} {'fijado' if pin_it else 'desfijado'}")
        self.__refresh_pin_provider_button()

    def __refresh_pin_provider_button(self) -> None:
        """Sincroniza el icono del pin con la selección actual.

        Marcado (azul) significa «lo que estás usando es tu predeterminado»; en
        gris, que te has desviado solo para esta sesión. El icono lo cambia la
        barra lateral; aquí solo se decide **cuál** de los dos estados toca.
        """
        if self.sidebar_frame is None:
            return
        is_pinned = (self.__pinned_provider_id is not None
                     and self.__pinned_provider_id == self.anime_provider_mgr.get_default_provider_id())
        self.sidebar_frame.refresh_pin_button(is_pinned)

    def reference_provider_id(self) -> AnimeProviderId | None:
        """Proveedor «de referencia»: el pin, o el predeterminado del registro si no hay.

        Es contra este valor —y no contra el predeterminado vivo del manager, que
        el desplegable va cambiando— contra el que se mide si el usuario se ha
        desviado a propósito en esta sesión.
        """
        return (self.__pinned_provider_id if self.__pinned_provider_id is not None
                else self.__registry_default_provider_id)

    def provider_for_saved_anime(self, record_provider_id: AnimeProviderId | None
                                 ) -> Tuple[AnimeProviderId | None, bool]:
        """Decide con qué proveedor abrir un anime de la biblioteca.

        Orden de prioridad: 1) la selección del desplegable, si difiere de la
        de referencia (una desviación deliberada manda); 2) el provider_id de
        la fila; 3) la de referencia (pin, o predeterminado del registro).

        :param record_provider_id: Proveedor guardado en la fila, o None si no lo declara.
        :return: Tupla (proveedor, hay_desviación). La desviación obliga a
            re-resolver el anime por título, porque el slug guardado es de otro sitio.
        """
        selected_provider_id = self.anime_provider_mgr.get_default_provider_id()
        reference_provider_id = self.reference_provider_id()
        if selected_provider_id is not None and selected_provider_id != reference_provider_id:
            return selected_provider_id, True
        if record_provider_id is not None:
            return record_provider_id, False
        return reference_provider_id, False

    def __reload_recent_animes(self) -> None:
        """Vuelve a pedir los animes recientes al proveedor recién elegido.

        Sin esto el selector parecería no hacer nada: la portada seguiría mostrando
        el catálogo del proveedor anterior hasta reiniciar la aplicación.
        """
        if self.__reloading_recent_animes:
            print("Ya hay una recarga de animes recientes en curso, se ignora el cambio")
            return
        self.__reloading_recent_animes = True
        self.__recent_animes_generation += 1
        self.configure(cursor="watch")
        threading.Thread(
            target=self.__reload_recent_animes_worker,
            args=(self.__recent_animes_generation,),
            daemon=True
        ).start()

    def __reload_recent_animes_worker(self, generation: int) -> None:
        """Parte de red de la recarga. Corre en un hilo daemon: no toca widgets.

        El resultado se devuelve al hilo de Tkinter con after(0, ...) en vez de
        pintar directamente desde aquí.

        :param generation: Generación de recarga con la que se lanzó este hilo.
        """
        recent_animes: List[AnimeInfo] = []
        try:
            recent_animes = self.anime_provider_mgr.get_recent_animes()
            if recent_animes:
                download_animes_poster(self.images_path, recent_animes)
        except Exception as e:
            print(f"Error al recargar los animes recientes: {e}")
            recent_animes = []
        self.after(0, self.__on_recent_animes_reloaded, recent_animes, generation)

    def __on_recent_animes_reloaded(self, recent_animes: List[AnimeInfo], generation: int) -> None:
        """Parte de UI de la recarga. Corre en el hilo de Tkinter."""
        self.__reloading_recent_animes = False
        self.configure(cursor="")
        if generation != self.__recent_animes_generation:
            # Llegó tarde: hubo otro cambio de proveedor por medio.
            return
        if not recent_animes:
            messagebox.showwarning(
                "Aviso!",
                "No se pudieron obtener los animes recientes del proveedor seleccionado.\n\n"
                "El proveedor queda cambiado para las próximas búsquedas."
            )
            return
        self.recent_animes = recent_animes
        self.refresh_sidebar_counts()
        self.set_active_sidebar_destination(self.__recent_animes_button)
        self.__recent_animes_button.show_frame()
        threading.Thread(
            target=self.__preload_recent_animes_info,
            args=(generation,),
            daemon=True
        ).start()

    def change_appearance_mode_event(self, new_appearance_mode):
        """Cambia el tema claro/oscuro; CustomTkinter repinta todos los widgets."""
        ctk.set_appearance_mode(new_appearance_mode)

    def show_loading_screen(self):
        """Pinta la pantalla de carga (GIF + barra de progreso) y lanza el arranque en un hilo daemon."""
        self.sidebar_frame.grid_forget()
        loading_frame = ctk.CTkFrame(self, corner_radius=0, fg_color=Theme.BG)
        loading_frame.place(relx=0, rely=0, relwidth=1, relheight=1)

        loading_content = ctk.CTkFrame(loading_frame, fg_color=Theme.TRANSPARENT)
        loading_content.place(relx=0.5, rely=0.5, anchor=ctk.CENTER)

        loading_label = ctk.CTkLabel(
            loading_content,
            text="Cargando biblioteca de anime",
            font=Theme.font(*Theme.T_VIEW),
            text_color=Theme.TXT
        )
        loading_label.pack(pady=20)

        loading_image_path = get_resource_path("resources/images/utils/loading-image.gif")
        gif_image = Image.open(loading_image_path)
        gif_frames = [ctk.CTkImage(frame.copy(), size=(400, 400)) for frame in ImageSequence.Iterator(gif_image)]
        loading_image_label = ctk.CTkLabel(loading_content, text="", font=Theme.font(*Theme.T_UI))
        loading_image_label.pack(pady=20)

        progress_bar = ctk.CTkProgressBar(
            loading_content,
            width=400,
            fg_color=Theme.LINE,
            progress_color=Theme.ACCENT
        )
        progress_bar.set(0)
        progress_bar.pack(pady=10)
        progress_label = ctk.CTkLabel(
            loading_content,
            text="0 %",
            font=Theme.font(*Theme.T_UI),
            text_color=Theme.TXT_2
        )
        progress_label.pack(pady=5)

        def update_gif(frame=0):
            if not loading_image_label.winfo_exists():
                return
            loading_image_label.configure(image=gif_frames[frame])
            frame = (frame + 1) % len(gif_frames)
            self.after(100, update_gif, frame)

        update_gif()

        def paint_progress(fraction: float) -> None:
            if progress_bar.winfo_exists():
                progress_bar.set(fraction)
                progress_label.configure(text=f"{int(fraction * 100)} %")

        def set_progress(fraction: float) -> None:
            # Llega desde el hilo de arranque y desde los de descarga: la barra se pinta en el de Tk.
            self.after(0, paint_progress, fraction)

        threading.Thread(target=self.download_images_and_show_animes, args=(set_progress, loading_frame),
                         daemon=True).start()

    def download_images_and_show_animes(self, on_progress: Callable[[float], None],
                                        loading_frame: ctk.CTkFrame):
        """Parte lenta del arranque: carga la BD, pide los estrenos y baja sus pósters.

        Corre en un hilo daemon y no toca widgets: la portada la revela
        __on_startup_loaded() en el hilo de Tkinter.

        :param on_progress: Recibe la fracción completada, de 0 a 1.
        :param loading_frame: Pantalla de carga que hay que retirar al terminar.
        """
        self.load_animes(on_progress)
        recent_animes = self.anime_provider_mgr.get_recent_animes()
        if recent_animes:
            on_progress(0.9)
            download_images_progress(self.images_path, recent_animes, on_progress)
        self.after(0, self.__on_startup_loaded, recent_animes, loading_frame)

    def __on_startup_loaded(self, recent_animes: List[AnimeInfo], loading_frame: ctk.CTkFrame) -> None:
        """Parte de UI del arranque: retira la pantalla de carga y revela la portada.

        La pantalla de carga se retira también cuando no hay estrenos, para no
        dejarla tapando la ventana para siempre.

        :param recent_animes: Estrenos obtenidos; vacío si ningún proveedor respondió.
        :param loading_frame: Pantalla de carga que hay que retirar.
        """
        self.recent_animes = recent_animes
        # destroy() y no place_forget(): la pantalla de carga no se reutiliza, y
        # mientras siga viva su animación se sigue reprogramando con after().
        loading_frame.destroy()
        if not recent_animes:
            messagebox.showwarning("Aviso!",
                                   "La conexión con los proveedores de anime es muy lenta, por lo que no se "
                                   "pudieron obtener los animes recientes.")
        self.refresh_sidebar_counts()
        self.set_active_sidebar_destination(self.__recent_animes_button)
        self.__recent_animes_button.show_frame()
        if not recent_animes:
            return

        # Precarga el detalle de cada anime en segundo plano para que el clic
        # del usuario sea instantáneo en vez de bloquear la UI.
        threading.Thread(
            target=self.__preload_recent_animes_info,
            args=(self.__recent_animes_generation,),
            daemon=True
        ).start()
        # Con la portada ya pintada no retrasa el arranque, y así «Viendo» y
        # «Pendientes» encuentran el recuento al día cuando el usuario entra.
        self.episode_refresher.refresh(self.watching_animes + self.pending_animes)

    def __preload_recent_animes_info(self, generation: int):
        """Rellena synopsis, géneros y episodios de los animes recientes, en segundo plano.

        :param generation: Generación de recarga con la que arrancó esta precarga; si
            no coincide con la actual, self.recent_animes ya es otra lista y se aborta.
        """
        recent_animes = self.recent_animes
        for index, anime in enumerate(recent_animes):
            if generation != self.__recent_animes_generation:
                print("Precarga de animes recientes abortada: la lista ha cambiado")
                return
            if anime.synopsis is not None and anime.genres is not None and anime.episodes is not None:
                continue
            try:
                anime_info = self.anime_provider_mgr.get_anime_info(anime.id)
                if anime_info is not None and generation == self.__recent_animes_generation:
                    self.recent_animes[index] = anime_info
            except Exception as e:
                print(f"Error al precargar info del anime {anime.id}: {e}")

    def load_animes(self, on_progress: Callable[[float], None]):
        """Carga desde BD las cuatro listas de biblioteca, avisando del progreso.

        :param on_progress: Recibe la fracción completada, de 0,1 a 0,4.
        """
        self.animes_persistence.start()
        self.favourite_animes = self.animes_persistence.get_favourite_animes()
        on_progress(0.1)
        self.finished_animes = self.animes_persistence.get_finished_animes()
        on_progress(0.2)
        self.watching_animes = self.animes_persistence.get_watching_animes()
        on_progress(0.3)
        self.pending_animes = self.animes_persistence.get_pending_animes()
        on_progress(0.4)
