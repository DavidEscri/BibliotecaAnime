__author__ = "Jose David Escribano Orts"
__subsystem__ = "gui"
__module__ = "main_window.py"
__version__ = "0.5"
__info__ = {"subsystem": __subsystem__, "module_name": __module__, "version": __version__}

import threading
import customtkinter as ctk

from tkinter import messagebox
from typing import List, Tuple
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
from gui.theme import Theme

from utils.utils import get_resource_path, download_images_progress, download_animes_poster


class MainWindow(ctk.CTk):
    MAIN_WINDOW_ANCHO = 1440
    MAIN_WINDOW_LARGO = 910

    def __init__(self):
        # https://www.youtube.com/watch?v=p3tSLatmGvU&ab_channel=PythonSimplified
        super().__init__()
        self.__config_main_window()
        self.__config_main_frames()

        self.animes_persistence: AnimesPersistence = AnimesPersistenceSingleton()
        self.anime_provider_mgr: AnimeProviderManager = AnimeProviderManagerSingleton()
        # El orden de registro es el orden del fallback. JKAnime va antes que
        self.anime_provider_mgr.register(AnimeAV1Singleton(), default=True)
        self.anime_provider_mgr.register(JKAnimeSingleton())
        self.anime_provider_mgr.register(AnimeFLVSingleton()) # AnimeFLV porque este último lleva tiempo sin servir datos utilizables.

        # Las preferencias se leen aquí, de forma síncrona, y no en load_animes():
        # el desplegable de proveedor tiene que nacer ya con el valor guardado, y el
        # predeterminado tiene que estar aplicado antes del primer get_recent_animes().
        # Es SQLite local, no red: son milisegundos.
        self.user_persistence: UserPersistence = UserPersistenceSingleton()
        self.user_persistence.start()
        # Proveedor fijado con el pin. None = sin preferencia guardada, en cuyo
        # caso manda el predeterminado del registro (AnimeAV1).
        self.__pinned_provider_id: AnimeProviderId | None = None
        # Predeterminado del registro ANTES de aplicar ninguna preferencia. Hay que
        # capturarlo aquí porque __apply_saved_provider_preference() lo pisa con
        # set_default(): es el último escalón del orden de prioridad y, sin pin, la
        # referencia contra la que se decide si el desplegable está desviado.
        self.__registry_default_provider_id: AnimeProviderId | None = self.anime_provider_mgr.get_default_provider_id()
        self.__apply_saved_provider_preference()

        # El desplegable de proveedor, el pin y sus iconos los construye y los
        # mantiene la barra lateral (gui/components/sidebar.py). Este hub solo le
        # dice cuándo repintar el pin.
        # Guarda para que dos cambios seguidos de proveedor no lancen dos hilos que
        # se pisen al escribir self.recent_animes.
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

        self.load_sidebar_buttons()

        # Inicia mostrando pantalla de carga
        self.show_loading_screen()

    def __config_main_window(self):
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
        # La barra lateral se construye más tarde, en load_sidebar_buttons(): necesita
        # el gestor de proveedores y las preferencias, que todavía no existen aquí. Las
        # seis vistas se instancian antes que ella y leen este atributo, así que tiene
        # que estar declarado ya (SidebarButton lo guarda sin usarlo).
        self.sidebar_frame: Sidebar | None = None
        self.content_frame: ctk.CTkScrollableFrame = self.create_content_frame()

    def clear_frame(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def create_content_frame(self) -> ctk.CTkScrollableFrame:
        # Crear una barra de desplazamiento
        main_frame = ctk.CTkScrollableFrame(
            self,
            corner_radius=0,
            fg_color=Theme.BG
        )
        main_frame.grid(row=0, column=1, rowspan=8, sticky=ctk.NSEW)

        # Establecer grid en el main_frame
        main_frame.grid_rowconfigure(0, weight=1)  # Permitir que la primera fila se expanda
        main_frame.grid_columnconfigure(0, weight=1)  # Permitir que la primera columna se expanda
        return main_frame

    def load_sidebar_buttons(self) -> None:
        """Instancia las seis vistas y construye la barra lateral con ellas.

        El orden de esta lista **es** el orden en que se ven en la barra
        (`DISENO.md`); no coincide con el que había antes, donde finalizados iba
        delante de viendo y pendientes.
        """
        icon_path = get_resource_path("resources/images/utils")
        # row y column ya no significan nada: SidebarButton dejó de pintarse a sí
        # mismo y ahora solo describe el destino. Se conservan en la firma para no
        # tocar las seis vistas.
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
        # Los contadores salen de las listas que ya cachea este hub, no de la BD:
        # son len() sobre memoria y se pueden refrescar en cada guardado sin coste.
        # Buscar no lleva contador, así que no figura aquí.
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
        """Aplica el proveedor predeterminado guardado en DB_user.db, si lo hay.
        """
        saved_value = self.user_persistence.get_default_provider_id()
        if saved_value is None:
            current_provider_id = self.anime_provider_mgr.get_default_provider_id()
            print(f"Sin proveedor fijado, se usa "
                  f"{current_provider_id.value if current_provider_id else 'ninguno'}")
            return
        try:
            # ValueError si el texto guardado ya no corresponde a ningún miembro
            # del enum; UnknownProviderError si el miembro existe pero no está
            # registrado. Los dos casos acaban igual: se ignora la preferencia.
            saved_provider_id = AnimeProviderId(saved_value)
            self.anime_provider_mgr.set_default(saved_provider_id)
            self.__pinned_provider_id = saved_provider_id
            print(f"Proveedor fijado por el usuario: {saved_provider_id.value}")
        except Exception as e:
            # Preferencia obsoleta (p.ej. un proveedor retirado del código): se
            # deja el predeterminado del registro y el pin sale sin marcar, así
            # que la siguiente pulsación la reescribe con algo válido.
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

        Implementa el orden de prioridad acordado (`docs/13 §8`):

          1. **Selección del desplegable**, si difiere de la de referencia. Que el
             usuario se haya desviado es una acción deliberada y manda sobre todo
             lo demás; si no, un anime guardado no podría verse nunca desde otro
             sitio, que es justo para lo que existe el desplegable.
          2. **`provider_id` de la fila**, si la fila lo declara.
          3. La de referencia (pin, o predeterminado del registro).

        :param record_provider_id: proveedor guardado en la fila, o None si la fila
            no existe o es anterior a la columna.
        :return: ``(proveedor, hay_desviación)``. La desviación se devuelve porque
            obliga a **re-resolver el anime por título** (el slug guardado es el de
            otro sitio), y eso cuesta dos peticiones más.
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
        pintar desde aquí, que es lo que hace el arranque y lo que provoca el
        riesgo descrito en docs/07 (A6/R3).
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
        """Cambia el tema. Una línea, y no un recorrido de widgets.

        Antes había que recorrer los hijos de la barra reconfigurando fondo,
        hover, color de texto e icono uno a uno, porque los botones se habían
        construido con literales. Ahora todo el color sale de ``Theme`` en tuplas
        ``(claro, oscuro)`` y del cambio se encarga CustomTkinter.
        """
        ctk.set_appearance_mode(new_appearance_mode)

    def show_loading_screen(self):
        self.sidebar_frame.grid_forget()
        loading_frame = ctk.CTkFrame(self, corner_radius=0, fg_color=Theme.BG)
        loading_frame.place(relx=0, rely=0, relwidth=1, relheight=1)

        loading_content = ctk.CTkFrame(loading_frame, fg_color=Theme.TRANSPARENT)
        loading_content.place(relx=0.5, rely=0.5, anchor=ctk.CENTER)

        # Mostrar el texto de "Cargando biblioteca de anime"
        loading_label = ctk.CTkLabel(
            loading_content,
            text="Cargando biblioteca de anime",
            font=Theme.font(*Theme.T_VIEW),
            text_color=Theme.TXT
        )
        loading_label.pack(pady=20)

        # Cargar y mostrar el GIF con todos los frames
        loading_image_path = get_resource_path("resources/images/utils/loading-image.gif")
        gif_image = Image.open(loading_image_path)
        gif_frames = [ctk.CTkImage(frame.copy(), size=(400, 400)) for frame in ImageSequence.Iterator(gif_image)]
        loading_image_label = ctk.CTkLabel(loading_content, text="")
        loading_image_label.pack(pady=20)

        # Crear y mostrar la barra de progreso
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
            frame = (frame + 1) % len(gif_frames)  # Continuar en bucle
            self.after(100, update_gif, frame)  # Controla la velocidad de cambio de frame (100 ms)

        update_gif()  # Iniciar la animación

        # Iniciar la descarga de imágenes en un hilo
        threading.Thread(target=self.download_images_and_show_animes, args=(progress_bar, progress_label, loading_frame, ), daemon=True).start()

    def download_images_and_show_animes(self, progress_bar: ctk.CTkProgressBar, progress_label: ctk.CTkLabel,
                                        loading_frame: ctk.CTkFrame):
        self.load_animes(progress_bar, progress_label)
        self.recent_animes = self.anime_provider_mgr.get_recent_animes()
        if len(self.recent_animes) == 0:
            # 🔴 La pantalla de carga se retira **también aquí**. Hasta la fase 9
            # solo se quitaba en la rama de éxito, así que un arranque sin red
            # dejaba el GIF tapando la portada para siempre y el estado vacío de
            # «Nuevos lanzamientos» no llegaba a verse nunca.
            loading_frame.destroy()
            messagebox.showwarning("Aviso!",
                                   "La conexión con los proveedores de anime es muy lenta, por lo que no se "
                                   "pudieron obtener los animes recientes.")
            self.refresh_sidebar_counts()
            self.set_active_sidebar_destination(self.__recent_animes_button)
            self.__recent_animes_button.show_frame()
            return
        progress_bar.set(0.9)
        progress_label.configure(text="90 %")
        download_images_progress(self.images_path, self.recent_animes, progress_bar, progress_label)  # Descargar imágenes
        # `destroy()` y no `place_forget()`: la pantalla de carga no se vuelve a
        # usar, y mientras siga viva su animación se sigue reprogramando.
        loading_frame.destroy()
        self.refresh_sidebar_counts()
        self.set_active_sidebar_destination(self.__recent_animes_button)
        self.__recent_animes_button.show_frame()  # Mostrar animes recientes al finalizar la descarga

        # Precargar el detalle de cada anime reciente en segundo plano para que
        # el clic del usuario sea instantáneo en lugar de bloquear la UI.
        threading.Thread(
            target=self.__preload_recent_animes_info,
            args=(self.__recent_animes_generation,),
            daemon=True
        ).start()

    def __preload_recent_animes_info(self, generation: int):
        """Rellena synopsis, géneros y episodios de los animes recientes en segundo plano.

        Se ejecuta en un hilo daemon tras mostrar la pantalla principal.
        Escribe cada resultado directamente en self.recent_animes[index]; la
        asignación de un elemento de lista es atómica en CPython (GIL), por lo
        que no se necesita Lock.

        ``generation`` es el número de recarga con el que arrancó esta precarga: si
        el usuario cambia de proveedor por medio, self.recent_animes pasa a ser
        otra lista y los índices de esta ya no significan nada, así que se aborta
        en vez de escribir el anime equivocado en la posición equivocada.
        """
        recent_animes = self.recent_animes
        for index, anime in enumerate(recent_animes):
            if generation != self.__recent_animes_generation:
                print("Precarga de animes recientes abortada: la lista ha cambiado")
                return
            if anime.synopsis is not None and anime.genres is not None and anime.episodes is not None:
                # Ya precargado (p.ej. segunda apertura en la misma sesión)
                continue
            try:
                anime_info = self.anime_provider_mgr.get_anime_info(anime.id)
                if anime_info is not None and generation == self.__recent_animes_generation:
                    self.recent_animes[index] = anime_info
            except Exception as e:
                print(f"Error al precargar info del anime {anime.id}: {e}")

    def load_animes(self, progress_bar: ctk.CTkProgressBar, progress_label: ctk.CTkLabel):
        self.animes_persistence.start()
        self.favourite_animes = self.animes_persistence.get_favourite_animes()
        progress_bar.set(0.1)
        progress_label.configure(text="10 %")
        self.finished_animes = self.animes_persistence.get_finished_animes()
        progress_bar.set(0.2)
        progress_label.configure(text="20 %")
        self.watching_animes = self.animes_persistence.get_watching_animes()
        progress_bar.set(0.3)
        progress_label.configure(text="30 %")
        self.pending_animes = self.animes_persistence.get_pending_animes()
        progress_bar.set(0.4)
        progress_label.configure(text="40 %")
        # Ya hay números que enseñar en la barra lateral, aunque siga oculta tras
        # la pantalla de carga: cuando se revele, saldrá con los contadores puestos.
        self.refresh_sidebar_counts()
