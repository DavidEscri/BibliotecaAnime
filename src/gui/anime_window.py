__author__ = "Jose David Escribano Orts"
__subsystem__ = "gui"
__module__ = "anime_window.py"
__version__ = "0.7"
__info__ = {"subsystem": __subsystem__, "module_name": __module__, "version": __version__}

"""Ficha de detalle de un anime: la pantalla desde la que se ve un episodio.

Rediseñada en la fase 8 del plan (`.claude/plan-rediseno/fases/8-ficha.md`). Lo
que cambia es **la disposición y los estados visibles**, no la lógica:

- los cuatro botones de estado dejan de cambiar de texto («Añadir a» / «Eliminar
  de») y pasan a **encenderse y apagarse**, así que el estado entero del anime se
  lee de un golpe;
- las filas de episodio dejan de repetir el título del anime veinticinco veces y
  dicen «Episodio N» con su línea de estado al lado;
- se estrena la **barra de vistos**, el único añadido real: sale de
  ``get_watched_episodes()`` sin tocar la persistencia.

Lo estructural —la identidad congelada, el aviso de identidad partida, el aviso
de duplicado y el marcado acumulativo— ya estaba resuelto y aquí **solo se
recoloca**. Es el fichero donde un error cuesta filas duplicadas en la biblioteca
real: ver las trampas 21 y 22 de `.claude/docs/10-invariantes-y-trampas.md`.
"""

import difflib
import threading
import webbrowser
import customtkinter as ctk

from dataclasses import replace
from tkinter import messagebox
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from APIs.common.models import AnimeInfo, AnimeProviderId, EpisodeInfo, ServerInfo
from APIs.common.animeProviderMgr import AnimeProviderManager, AnimeProviderManagerSingleton
from dataPersistence.animesPersistence import AnimeStatus, AnimeRecord
from gui.components.status_pill import StatusPill
from gui.theme import Metrics, Theme
from utils.utils import refactor_genre_text, get_anime_image, find_cached_poster_path, \
    load_rounded_image, download_anime_poster_by_status, move_anime_poster_by_status, \
    remove_anime_poster_by_status

#: Similitud mínima entre títulos para dar por hecho que un anime que se va a
#: guardar es el mismo que otro que ya está en la biblioteca. Va **muy por
#: encima** del umbral con el que se busca (0.75-0.8) a propósito: aquí un falso
#: positivo interrumpe al usuario con un diálogo por dos animes distintos de la
#: misma saga ("One Piece" y "One Piece Film: Red"), mientras que un falso
#: negativo solo deja pasar el duplicado que ya se colaba antes.
DUPLICATE_TITLE_THRESHOLD = 0.9

#: Cómo se llama cada estado de cara al usuario. En los diálogos hay que nombrar
#: la sección concreta ("tu Biblioteca de Favoritos") y no "tu biblioteca" a
#: secas: es la que el usuario acaba de pulsar y la que va a mirar después.
STATUS_SECTION_NAMES = {
    AnimeStatus.FAVOURITE: "Favoritos",
    AnimeStatus.WATCHING:  "Viendo",
    AnimeStatus.FINISHED:  "Finalizados",
    AnimeStatus.PENDING:   "Pendientes",
}

#: En qué orden salen los cuatro botones de estado, de izquierda a derecha
#: (`DISENO-VISUAL.html#ficha`). El texto y los colores de cada uno los pone
#: ``StatusPill``, que es quien sabe de qué color va un estado.
STATUS_ORDER: Tuple[AnimeStatus, ...] = (
    AnimeStatus.FAVOURITE,
    AnimeStatus.WATCHING,
    AnimeStatus.PENDING,
    AnimeStatus.FINISHED,
)

#: Los tres que se apagan entre sí. ``FAVOURITE`` no está: es independiente y se
#: puede tener a la vez que cualquiera de estos (`_set_status`).
EXCLUSIVE_STATUSES: Tuple[AnimeStatus, ...] = (
    AnimeStatus.WATCHING,
    AnimeStatus.PENDING,
    AnimeStatus.FINISHED,
)

#: Qué método llama cada botón, según esté apagado o encendido: (añadir, quitar).
#: Los seis métodos públicos siguen siendo los de siempre; lo único que cambia es
#: que ahora el botón no cambia de texto para decir cuál de los dos toca.
STATUS_ACTIONS: Dict[AnimeStatus, Tuple[str, str]] = {
    AnimeStatus.FAVOURITE: ("add_to_favorites", "remove_from_favorites"),
    AnimeStatus.WATCHING:  ("add_to_watching",  "remove_from_watching"),
    AnimeStatus.PENDING:   ("add_to_pending",   "remove_from_pending"),
    AnimeStatus.FINISHED:  ("add_to_finished",  "remove_from_finished"),
}

#: Cuántos episodios se pintan. Sigue siendo un corte duro y sigue siendo la
#: trampa 8: con AnimeAV1 (orden ascendente) son los 25 **primeros** y con
#: AnimeFLV los 25 **más recientes**. Para llegar a otro está el buscador.
EPISODES_SHOWN = 25

#: Separación entre el póster y la columna de información (`.sheet`: gap 30).
SHEET_GAP = 30
#: Aire por encima de la ficha y por debajo de la lista de episodios.
SHEET_PAD_TOP = 26
SHEET_PAD_BOTTOM = 24
#: Separación por encima de cada bloque de la columna de información, de arriba
#: abajo: título, sinopsis, géneros, barra de vistos y botones de estado. El
#: bloque de proveedor va el primero y no lleva.
INFO_GAPS = (12, 14, 16, 18, 18)
#: Ancho máximo del bloque de la barra de vistos (`.seen`: max-width 420).
SEEN_W = 420
#: Alto de ese bloque. Un CTkFrame necesita alto explícito o conserva los 200 por
#: defecto como tamaño pedido y estira la fila que lo contenga.
SEEN_H = 22
#: Separación entre la barra y su leyenda (`.seen`: gap 12).
SEEN_GAP = 12
#: Ancho de lectura cómoda de la sinopsis, en caracteres (`.syn`: max-width 74ch).
SYNOPSIS_MAX_CH = 74
#: Fichas de género (`.tags span`: alto 26, hueco 7, relleno lateral 11).
GENRE_CHIP_H = 26
GENRE_CHIP_GAP = 7
GENRE_CHIP_PAD_X = 11
#: Lado del glifo de los botones de estado.
STATUS_ICON_SIZE = 14
#: Alto del botón «Actualizar a …» del bloque de proveedor (`.pv .fix`: alto 30).
FIX_BUTTON_H = 30
#: Cabecera y filas de la lista de episodios.
EPISODES_PAD_TOP = 24
EPISODE_PAD_X = 14
EPISODE_GAP = 16
EPISODE_NUMBER_W = 96
#: Controles de la cabecera de episodios.
EPISODE_CONTROL_H = 32
EPISODE_SEARCH_W = 160
#: Umbral por debajo del cual un `<Configure>` no obliga a recolocar. Sin él,
#: cada redimensionado de la ventana repintaría las fichas decenas de veces.
RELAYOUT_THRESHOLD = 8


# TODO: Al final de la lista de episodios nuevo frame del estilo. "Si te ha gustado One piece, te puede interesar..." y
#  mostrar 4 animes con los mimos generos.

# TODO: Agregar botón para alternar entre el manga y el anime.


def show_anime_info_error(anime_id: Union[str, int]) -> None:
    """
    Avisa al usuario de que no se ha podido recuperar la ficha de un anime.

    `AnimeProviderManager.get_anime_info` nunca propaga excepciones: si fallan
    todos los proveedores devuelve None. Sin este aviso, el clic simplemente no
    hace nada (Tkinter se traga la excepción del callback) y la aplicación
    parece colgada.

    :param anime_id: Identificador del anime que no se ha podido cargar.
    """
    print(f"No se pudo obtener la información del anime {anime_id}: ningún proveedor respondió")
    messagebox.showerror(
        "No se pudo cargar el anime",
        "No se ha podido obtener la información de este anime.\n\n"
        "Comprueba tu conexión a internet e inténtalo de nuevo más tarde."
    )


def find_saved_duplicate(anime_records: List[AnimeRecord], title: str,
                         exclude_anime_id: Optional[str] = None) -> Optional[AnimeRecord]:
    """Busca en la biblioteca un anime que sea **el mismo** que ``title``.

    Sirve para no guardar dos veces el mismo anime cuando se abre desde un
    proveedor distinto al que lo guardó.

    Compara por título normalizado (sin tildes, ni mayúsculas, ni signos), que es
    lo único común entre proveedores. No detecta títulos completamente distintos
    para el mismo anime ("Solo Leveling" y "Ore dake Level Up na Ken"): eso no
    hay forma de saberlo sin preguntar a la red, y esto corre en el hilo de la
    interfaz.

    :param exclude_anime_id: fila que no cuenta como duplicado (normalmente, la
        del propio anime que se está guardando).
    :return: el ``AnimeRecord`` más parecido si supera
        ``DUPLICATE_TITLE_THRESHOLD``, o ``None``.
    """
    normalized_title = AnimeProviderManager.normalize_title(title)
    if not normalized_title:
        return None

    best_record: Optional[AnimeRecord] = None
    best_ratio: float = 0.0
    for anime_record in anime_records:
        if exclude_anime_id is not None and str(anime_record.anime_id) == str(exclude_anime_id):
            continue
        normalized_candidate = AnimeProviderManager.normalize_title(anime_record.title)
        if normalized_candidate == normalized_title:
            return anime_record
        ratio = difflib.SequenceMatcher(None, normalized_title, normalized_candidate).ratio()
        if ratio > best_ratio:
            best_record, best_ratio = anime_record, ratio

    return best_record if best_ratio >= DUPLICATE_TITLE_THRESHOLD else None


def open_saved_anime(main_window, anime_id: Union[str, int]) -> None:
    """Abre la ficha de un anime **ya guardado** en la biblioteca.

    Punto de entrada único de las cuatro vistas de estado (favoritos, viendo,
    finalizados y pendientes), que repetían estas mismas líneas una por una.

    El fallback sigue activo a propósito: la propiedad de un slug caduca (hay
    animes guardados que AnimeAV1 servía y hoy devuelven 404), así que fijar el
    proveedor de la fila con ``strict=True`` convertiría un anime que hoy se abre
    despacio en uno que no se abre.

    En el hilo secundario va **solo la petición**. El repintado vuelve al hilo de
    Tkinter con ``after(0, ...)``, que es la regla del proyecto y no una
    formalidad: ``display_anime_info()`` empieza destruyendo los widgets de la
    vista anterior.

    :param main_window: hub de la aplicación (`MainWindow`).
    :param anime_id: ``anime_id`` de la fila, es decir, el slug del proveedor que
        la guardó.
    """
    anime_record: AnimeRecord = main_window.animes_persistence.get_anime_by_anime_id(anime_id)
    provider_id, is_deviation = main_window.provider_for_saved_anime(anime_record.provider_id if anime_record is not None else None)

    main_window.configure(cursor="watch")
    # update_idletasks(): así un segundo clic no puede reentrar aquí y lanzar un segundo hilo.
    main_window.update_idletasks()

    def _show(anime_info, served_by):
        """Ya en el hilo de Tkinter: aquí se toca la interfaz, y solo aquí."""
        if not main_window.winfo_exists():
            return
        main_window.configure(cursor="")
        if anime_info is None:
            show_anime_info_error(anime_id)
            return
        # anime_record va aparte del AnimeInfo y no es redundante: cuando el
        # usuario se ha desviado de proveedor, `anime_info` es la ficha del sitio
        # elegido y su `id` es OTRO slug, así que sin la fila la ficha escribiría
        # con el identificador equivocado y duplicaría el anime.
        AnimeWindowViewer(main_window, anime_info, served_by,
                          anime_record=anime_record).display_anime_info()

    def _load_and_show():
        anime_info = served_by = None
        if is_deviation and anime_record is not None:
            # El usuario se ha desviado en el desplegable. El slug guardado es el
            # del proveedor que lo guardó, así que en el elegido no vale: hay que
            # volver a localizar el anime por su título.
            reference = AnimeInfo(
                id=anime_record.anime_id,
                title=anime_record.title,
                poster=anime_record.poster_url
            )
            resolved = main_window.anime_provider_mgr.resolve_anime_in_provider(reference, provider_id)
            if resolved is not None:
                anime_info, served_by = resolved, provider_id
            else:
                # Que el proveedor elegido no lo tenga provoca que se sigue por la vía normal y la ficha mostrará
                # quién lo ha servido de verdad.
                print(f"[{provider_id.value}] no tiene {anime_record.title!r}; "
                      f"se abre con el proveedor habitual")

        if anime_info is None:
            anime_info, served_by = main_window.anime_provider_mgr.get_anime_info_with_provider(anime_id, provider_id=None if is_deviation else provider_id)

        main_window.after(0, _show, anime_info, served_by)

    threading.Thread(target=_load_and_show, daemon=True).start()


class EpisodeRow(ctk.CTkFrame):
    """Una fila de la lista de episodios.

    Sustituyó al ``utilsButtons.EpisodeButton`` —retirado ya en el paso 9.4—, que
    era un botón de ancho completo con el texto «<título del anime> - Episodio N»
    repetido veinticinco veces. Ahora la fila dice solo **«Episodio N»** —el título del anime está
    justo encima, en la cabecera de la ficha— y reparte el resto del ancho entre
    una línea de estado y el interruptor «Visto» (`DISENO-VISUAL.html#ficha`).

    La fila entera es pulsable y despliega los servidores debajo. El interruptor
    **no** hereda ese clic: los eventos de Tk no burbujean, así que marcar un
    episodio no abre sus servidores sin querer.
    """

    def __init__(self, parent, episode_info: EpisodeInfo, watched: bool, state_text: str,
                 on_click: Callable[[EpisodeInfo], None],
                 on_toggle: Callable[[int], None], **kwargs):
        """
        :param episode_info: episodio que representa la fila.
        :param watched: si ya está marcado como visto.
        :param state_text: la línea de apoyo («Siguiente para ti», «Sin ver»…).
        :param on_click: se llama con el episodio al pulsar la fila.
        :param on_toggle: se llama con el ``id`` del episodio al mover el
            interruptor. Quien marca es la ficha, no la fila: el marcado es
            **acumulativo** y toca a las demás.
        """
        super().__init__(parent, corner_radius=8, fg_color=Theme.TRANSPARENT, **kwargs)
        self.episode_info = episode_info
        self.__on_click = on_click
        self.__expanded = False

        # minsize y no `height=` + grid_propagate(False): esa combinación deja el
        # marco al alto pedido pero su rejilla interna sigue centrando los hijos
        # como si midiera los 200 por defecto de CTkFrame, y el contenido acaba
        # fuera de la parte visible (misma lección que en ViewHeader).
        self.grid_rowconfigure(0, minsize=Metrics.EPISODE_ROW_H)
        self.grid_columnconfigure(1, weight=1)

        self.number_label = ctk.CTkLabel(
            self,
            text=f"Episodio {episode_info.id}",
            width=EPISODE_NUMBER_W,
            anchor="w",
            font=Theme.font(Theme.T_UI[0], True),
            text_color=Theme.TXT
        )
        self.number_label.grid(row=0, column=0, sticky="w", padx=(EPISODE_PAD_X, 0))

        self.state_label = ctk.CTkLabel(
            self,
            text=state_text,
            anchor="w",
            font=Theme.font(*Theme.T_META),
            text_color=Theme.TXT_3
        )
        self.state_label.grid(row=0, column=1, sticky="w", padx=(EPISODE_GAP, 0))

        self.switch = ctk.CTkSwitch(
            self,
            text="Visto",
            switch_width=36,
            switch_height=20,
            corner_radius=10,
            font=Theme.font(*Theme.T_UI),
            text_color=Theme.TXT_3,
            fg_color=Theme.LINE,
            progress_color=Theme.ACCENT,
            command=lambda: on_toggle(episode_info.id)
        )
        self.switch.grid(row=0, column=2, sticky="e", padx=(EPISODE_GAP, EPISODE_PAD_X))

        # El separador va con place() y no en una fila propia: la fila mide 52 px
        # justos y una segunda fila de rejilla la haría crecer.
        #
        # ⚠️ El alto se le da al CONSTRUIRLO: CustomTkinter rechaza `width=` y
        # `height=` dentro de place() con un ValueError, al revés que Tk pelado.
        self.__separator = ctk.CTkFrame(self, height=1, corner_radius=0, fg_color=Theme.LINE_SOFT)
        self.__separator.place(relx=0, rely=1.0, anchor="sw", relwidth=1.0)

        self.set_watched(watched)
        self.__bind_interactions()

    # ------------------------------------------------------------------
    # Estado visible
    # ------------------------------------------------------------------
    def set_watched(self, watched: bool) -> None:
        """Pone el interruptor **sin** disparar su ``command``.

        ``select()`` y ``deselect()`` de CustomTkinter no lo llaman, que es justo
        lo que hace falta para el marcado acumulativo: la ficha ya sabe lo que
        tiene que persistir y no quiere veinticinco callbacks encadenados.
        """
        if watched:
            self.switch.select()
        else:
            self.switch.deselect()
        # El botón del interruptor cambia de color con el estado, como en el
        # diseño: gris sobre la pista apagada, y el color de "sobre acento"
        # cuando está encendida.
        self.switch.configure(button_color=Theme.ACCENT_INK if watched else Theme.TXT_3)

    def set_state_text(self, text: str) -> None:
        self.state_label.configure(text=text)

    def set_expanded(self, expanded: bool) -> None:
        """Resalta la fila mientras sus servidores están desplegados."""
        self.__expanded = expanded
        self.configure(fg_color=Theme.CARD if expanded else Theme.TRANSPARENT)
        self.number_label.configure(text_color=Theme.ACCENT if expanded else Theme.TXT)

    # ------------------------------------------------------------------
    # Interacción
    # ------------------------------------------------------------------
    def __bind_interactions(self) -> None:
        """Ata hover y clic a la fila y a sus etiquetas.

        Los eventos de Tk no burbujean: sin recorrer los hijos, pulsar justo
        encima del número no haría nada. El interruptor se queda fuera a
        propósito — tiene su propio comando.
        """
        for widget in (self, self.number_label, self.state_label):
            widget.bind("<Enter>", self.__handle_enter)
            widget.bind("<Leave>", self.__handle_leave)
            widget.bind("<Button-1>", self.__handle_click)
            widget.configure(cursor="hand2")

    def __handle_click(self, _event=None) -> None:
        self.__on_click(self.episode_info)

    def __handle_enter(self, _event=None) -> None:
        if not self.__expanded:
            self.configure(fg_color=Theme.CARD_HOVER)

    def __handle_leave(self, _event=None) -> None:
        # Tk manda Leave también al pasar del marco a uno de sus hijos, así que
        # apagar el resaltado sin mirar dónde está el puntero hace parpadear la
        # fila (misma trampa que en AnimeRow).
        if self.__expanded or self.__pointer_inside():
            return
        self.configure(fg_color=Theme.TRANSPARENT)

    def __pointer_inside(self) -> bool:
        """``True`` si el puntero sigue dentro de la fila."""
        if not self.winfo_exists():
            return False
        pointer_x, pointer_y = self.winfo_pointerxy()
        left, top = self.winfo_rootx(), self.winfo_rooty()
        return (left <= pointer_x < left + self.winfo_width()
                and top <= pointer_y < top + self.winfo_height())


class AnimeWindowViewer:
    """Ficha de detalle de un anime. No es una ventana: reemplaza el contenido de
    ``main_window.content_frame``.

    **Maneja dos identidades distintas del mismo anime**, y confundirlas duplica
    datos en la biblioteca del usuario:

    - *Identidad de visualización* (``self.anime_info``, ``self.provider_id``): la
      del proveedor que sirvió la ficha, que es el que muestra la etiqueta
      «Proveedor:». De aquí salen título, sinopsis, géneros, episodios y servidores.
    - *Identidad de persistencia* (``self.persistence_anime_id``,
      ``self.persistence_poster_url`` y ``self.persistence_provider_id``): la de la
      **fila guardada** (el ``anime_record`` del constructor) y, si no está
      guardado, la del ``AnimeInfo`` con el que se abrió la ficha. **Nunca cambia
      mientras la ficha está en pantalla.** Es la que se usa en toda operación de
      BD y en todo fichero de póster.

    El motivo es que ``AnimeInfo.id`` es el *slug* del sitio, no un identificador
    universal: el mismo anime es "one-piece" en AnimeAV1 y
    "one-piece-tv" en AnimeFLV. Si se persistiera con el id del proveedor que sirvió
    la ficha en vez de con el de apertura, «añadir a favoritos» insertaría una
    **fila nueva** en ANIMES y el mismo anime aparecería dos veces.

    Las dos identidades **siguen sin poder fundirse** aunque la ficha ya no
    permita cambiar de proveedor: el fallback puede servirla desde un proveedor
    distinto al que guardó la fila, y desviarse en el desplegable de la sidebar
    la abre directamente con el slug de otro sitio.

    Cuando se separan, la ficha lo dice y ofrece juntarlas de la única forma que
    no pierde datos: reapuntar la fila a otro proveedor
    (``__repair_to_target_provider``), que también sirve para llevártela al
    proveedor que estés usando aunque no haya nada partido.

    Ver .claude/docs/13-selector-de-proveedor.md (decisión D5).

    **Disposición** (`DISENO-VISUAL.html#ficha`), dos bloques dentro del
    ``content_frame``: la *cabecera* —póster de 248 x 372 a la izquierda y, a la
    derecha, proveedor, título, sinopsis, géneros, barra de vistos y los cuatro
    botones de estado— y la *lista de episodios*.
    """

    def __init__(self, main_window, anime_info: AnimeInfo, provider_id: AnimeProviderId | None = None,
                 anime_record: AnimeRecord | None = None):
        """
        :param anime_info: ficha del anime. No puede ser ``None``.
        :param provider_id: proveedor que sirvió esa ficha. Si se omite se usa el
            que traiga el propio ``AnimeInfo`` (lo estampa el manager al responder)
            y, en último caso, el predeterminado.
        :param anime_record: fila con la que está guardado este anime en la
            biblioteca, si lo está. **Obligatorio cuando la ficha puede venir de
            un proveedor distinto al que la guardó**: es de donde sale la
            identidad de persistencia. Sin él se asume que ``anime_info`` es
            también lo guardado, que es cierto al abrir desde recientes o desde
            una búsqueda, pero no al abrir un anime de la biblioteca con el
            desplegable desviado.
        """
        if anime_info is None:
            raise ValueError("AnimeWindowViewer requiere un AnimeInfo; se recibió None")
        self.main_window = main_window
        self.anime_provider_mgr: AnimeProviderManager = AnimeProviderManagerSingleton()
        self.anime_info: AnimeInfo = self.__with_episodes(anime_info)

        self.provider_id: AnimeProviderId | None = (provider_id or anime_info.provider_id or self.anime_provider_mgr.get_default_provider_id())

        # Identidad de persistencia: se congela aquí y no se vuelve a tocar.
        #
        # Solo se separa de la de visualización cuando el slug que se está viendo
        # NO es el guardado, es decir, cuando la ficha se ha localizado por título
        # en otro proveedor. Si los dos slugs coinciden manda el de visualización
        # aunque haya entrado el fallback: ahí el proveedor que respondió sí sirve
        # ese slug, y es la respuesta correcta para el autorrelleno de la columna.
        is_split_identity = (anime_record is not None and str(anime_record.anime_id) != str(anime_info.id))
        self.persistence_anime_id: str = (str(anime_record.anime_id) if is_split_identity else str(anime_info.id))
        self.persistence_poster_url: str = anime_info.poster
        self.persistence_provider_id: AnimeProviderId | None = (
            anime_record.provider_id if is_split_identity else self.provider_id)

        # Proveedor que consta en la fila de la biblioteca. Lo rellena
        # __load_anime_status() y sirve para avisar cuando no coincide con quien
        # está sirviendo la ficha; None mientras no se sepa o si no está guardado.
        self.__saved_provider_id: AnimeProviderId | None = None
        # Si este anime tiene fila en la tabla ANIMES de DB_Animes.db. No se deduce de __saved_provider_id,
        # que también es None en las filas anteriores a la columna.
        self.__is_saved: bool = False

        self.watched_status: Dict[Any, bool] = {episode.id: False for episode in self.anime_info.episodes}
        #: En qué orden llega la lista del proveedor, que **no es el mismo en
        #: todos**: AnimeAV1 la sirve ascendente y AnimeFLV descendente. El botón
        #: de orden decía siempre «Mayor a menor» aunque en pantalla se estuviera
        #: viendo lo contrario; ahora arranca diciendo lo que hay. La lista no se
        #: reordena al abrir: el corte de 25 sigue siendo el que era.
        self.sort_descending: bool = self.__incoming_order_is_descending()
        #: Los cuatro estados de la fila. Sustituye a los cuatro booleanos
        #: sueltos: los botones se pintan recorriendo este diccionario, así que
        #: encender uno y apagar los excluyentes es una vuelta de bucle.
        self.__status_state: Dict[AnimeStatus, bool] = {status: False for status in STATUS_SECTION_NAMES}

        # --- Widgets de la ficha ------------------------------------------
        self.__info_column: Optional[ctk.CTkFrame] = None
        self.__title_label: Optional[ctk.CTkLabel] = None
        self.__synopsis_label: Optional[ctk.CTkLabel] = None
        self.__tags_frame: Optional[ctk.CTkFrame] = None
        self.__tags: List[ctk.CTkBaseClass] = []
        self.__seen_frame: Optional[ctk.CTkFrame] = None
        self.__status_buttons: Dict[AnimeStatus, ctk.CTkButton] = {}
        self.__episodes_body: Optional[ctk.CTkFrame] = None
        self.__sort_button: Optional[ctk.CTkButton] = None
        self.__episode_rows: Dict[Any, EpisodeRow] = {}
        self.__servers_frames: Dict[Any, ctk.CTkFrame] = {}
        self.search_entry: Optional[ctk.CTkEntry] = None
        #: Ancho con el que se midieron por última vez la sinopsis y las fichas de
        #: género. Sin esto, cada `<Configure>` las recolocaría otra vez.
        self.__laid_out_width: int = 0

    def __incoming_order_is_descending(self) -> bool:
        """Si la lista de episodios llega de mayor a menor.

        Se mira el primer par de episodios que no empate. Con la lista vacía o de
        un solo episodio da igual lo que se conteste: se devuelve ``True``, que es
        lo que había antes.
        """
        episodes = self.anime_info.episodes
        for previous, current in zip(episodes, episodes[1:]):
            if current.id != previous.id:
                return current.id < previous.id
        return True

    @staticmethod
    def __with_episodes(anime_info: AnimeInfo) -> AnimeInfo:
        """Normaliza ``episodes=None`` a lista vacía, **sobre una copia**.

        No se muta el original porque puede ser el objeto cacheado en
        ``main_window.recent_animes``, donde ese ``None`` es justo lo que marca que
        aún le falta la precarga.
        """
        if anime_info.episodes is None:
            return replace(anime_info, episodes=[])
        return anime_info

    def __persistence_anime_info(self) -> AnimeInfo:
        """Copia de la ficha actual con la **identidad de persistencia**.

        Es lo que hay que pasar a `animes_persistence` y a los helpers de póster,
        que leen ``.id`` y ``.poster`` del ``AnimeInfo`` que reciben. Sin esto, un
        cambio de proveedor duplicaría la fila en ANIMES.
        """
        return replace(
            self.anime_info,
            id=self.persistence_anime_id,
            poster=self.persistence_poster_url,
            provider_id=self.persistence_provider_id
        )

    # ------------------------------------------------------------------
    # Cabecera de la ficha
    # ------------------------------------------------------------------
    def display_anime_info(self):
        """Punto de entrada: vacía el contenido, lee el estado guardado y pinta."""
        self.main_window.clear_frame()
        self.__load_anime_status()
        self.__display_anime_info()

    def __load_anime_status(self):
        anime_record: AnimeRecord = self.main_window.animes_persistence.get_anime_by_anime_id(
            self.persistence_anime_id)
        if anime_record is None:
            return
        self.__is_saved = True
        self.__saved_provider_id = anime_record.provider_id
        if anime_record.provider_id is None and self.persistence_provider_id is not None:
            if self.main_window.animes_persistence.update_anime_provider_id(self.persistence_anime_id, self.persistence_provider_id):
                print(f"Anotado el proveedor {self.persistence_provider_id.value} "
                      f"para {self.persistence_anime_id}")
                self.__saved_provider_id = self.persistence_provider_id
        if len(anime_record.episodes) != len(self.anime_info.episodes):
            self.main_window.animes_persistence.update_anime_episodes(self.persistence_anime_id, self.anime_info.episodes)
        for status in self.__status_state:
            self.__status_state[status] = bool(getattr(anime_record, status.value))

        # Restaurar episodios vistos desde la BD
        watched_ids = self.main_window.animes_persistence.get_watched_episodes(self.persistence_anime_id)
        for episode in self.anime_info.episodes:
            self.watched_status[episode.id] = episode.id in watched_ids

    def __display_anime_info(self):
        """Monta los dos bloques de la ficha en el ``content_frame``."""
        content = self.main_window.content_frame
        content.grid_columnconfigure(0, weight=1)
        # El ``content_frame`` lo comparten las siete vistas y su configuración de
        # rejilla sobrevive al `clear_frame()`. La ficha anterior repartía peso
        # entre cuatro columnas y cuatro filas, y ese peso se quedaba puesto al
        # cambiar de pestaña: una columna con peso y **sin widgets** también
        # recibe el espacio sobrante, así que la vista siguiente pintaba en una
        # columna 0 estrecha. Se devuelven a cero.
        for column in range(1, 4):
            content.grid_columnconfigure(column, weight=0)
        for row in range(1, 6):
            content.grid_rowconfigure(row, weight=0)

        self.__build_sheet(content)
        self.__build_episodes(content)

    def __build_sheet(self, content: ctk.CTkFrame) -> None:
        """Póster a la izquierda y columna de información a la derecha."""
        sheet = ctk.CTkFrame(content, fg_color=Theme.TRANSPARENT)
        sheet.grid(row=0, column=0, sticky="ew",
                   padx=Metrics.CONTENT_PAD_X, pady=(SHEET_PAD_TOP, 0))
        sheet.grid_columnconfigure(1, weight=1)
        # El póster fija el alto del bloque: es lo que permite que los botones de
        # estado queden alineados con su borde inferior (`.acts`: margin-top auto).
        sheet.grid_rowconfigure(0, minsize=Metrics.SHEET_POSTER[1])

        poster_label = ctk.CTkLabel(sheet, text="", image=self.__poster_image())
        poster_label.grid(row=0, column=0, sticky="nw")

        info = ctk.CTkFrame(sheet, fg_color=Theme.TRANSPARENT)
        info.grid(row=0, column=1, sticky="nsew", padx=(SHEET_GAP, 0))
        info.grid_columnconfigure(0, weight=1)
        # La fila vacía con peso es la que empuja los botones de estado abajo. Una
        # fila con peso recibe el espacio sobrante aunque no tenga ningún hijo.
        info.grid_rowconfigure(5, weight=1)
        self.__info_column = info

        self.__build_provider_block(info)
        self.__build_title(info)
        self.__build_seen_bar(info)
        self.__build_status_buttons(info)

        # El ancho de esta columna cambia al plegar la barra lateral, y de él
        # dependen el envuelto de la sinopsis y el de las fichas de género.
        info.bind("<Configure>", self.__on_info_configure)

    def __poster_image(self) -> ctk.CTkImage:
        """El póster a 248 x 372, con las esquinas redondeadas.

        Se prefiere el fichero cacheado —``load_rounded_image()`` reduce con
        LANCZOS y recorta las esquinas, que ``CTkImage`` no sabe hacer— y solo se
        sale a la red cuando el anime todavía no tiene póster en disco, que es
        exactamente lo que hacía ``get_anime_image()`` hasta ahora.

        ⚠️ La identidad es la de **persistencia**: el fichero en disco se llama
        como la fila guardada, no como el slug que sirvió esta ficha.
        """
        cached_path = find_cached_poster_path(self.persistence_anime_id)
        if cached_path is not None:
            return load_rounded_image(cached_path, Metrics.SHEET_POSTER,
                                      Metrics.RADIUS_SHEET_POSTER)
        return get_anime_image(self.__persistence_anime_info(), Metrics.SHEET_POSTER)

    def __build_title(self, info: ctk.CTkFrame) -> None:
        """Título, sinopsis y fichas de género."""
        self.__title_label = ctk.CTkLabel(
            info,
            text=self.anime_info.title,
            font=Theme.font(*Theme.T_SHEET),
            text_color=Theme.TXT,
            justify="left",
            anchor="w"
        )
        self.__title_label.grid(row=1, column=0, sticky="w", pady=(INFO_GAPS[0], 0))

        self.__synopsis_label = ctk.CTkLabel(
            info,
            text=self.anime_info.synopsis or "Este proveedor no ha dado sinopsis de este anime.",
            font=Theme.font(*Theme.T_BODY),
            text_color=Theme.TXT_2,
            justify="left",
            anchor="w"
        )
        self.__synopsis_label.grid(row=2, column=0, sticky="ew", pady=(INFO_GAPS[1], 0))

        # height=1 por lo de siempre: un CTkFrame sin hijos conserva sus 200 px
        # por defecto como tamaño pedido y estiraría la fila que lo contiene.
        self.__tags_frame = ctk.CTkFrame(info, height=1, fg_color=Theme.TRANSPARENT)
        self.__tags_frame.grid(row=3, column=0, sticky="ew", pady=(INFO_GAPS[2], 0))

        self.__relayout_text(self.__available_width())

    def __available_width(self) -> int:
        """Ancho útil de la columna de información.

        Mientras el marco no está mapeado ``winfo_width()`` devuelve 1, así que se
        reserva el ancho de la ventana menos la barra lateral desplegada, el
        póster y los márgenes: es el peor caso, y en cuanto llegue el primer
        `<Configure>` se recalcula con el real.
        """
        width = self.__info_column.winfo_width() if self.__info_column is not None else 1
        if width > 1:
            return width
        return (Metrics.WINDOW_W - Metrics.SIDEBAR_W - 2 * Metrics.CONTENT_PAD_X
                - Metrics.SHEET_POSTER[0] - SHEET_GAP)

    def __relayout_text(self, available: int) -> None:
        """Reparte el ancho disponible entre título, sinopsis y fichas de género.

        La sinopsis no ocupa todo lo que hay: el diseño la corta a 74 caracteres
        (`.syn`: `max-width:74ch`) porque una línea de 1 300 px es incómoda de
        leer. Un «ch» es lo que mide el cero de la fuente.
        """
        self.__laid_out_width = available
        if self.__title_label is not None:
            self.__title_label.configure(wraplength=available)
        if self.__synopsis_label is not None:
            body_font = Theme.font(*Theme.T_BODY)
            self.__synopsis_label.configure(
                wraplength=min(available, body_font.measure("0") * SYNOPSIS_MAX_CH))
        self.__place_genre_tags(available)

    def __place_genre_tags(self, available: int) -> None:
        """Pinta los géneros como fichas, envolviendo por ancho.

        Con ``place()`` y no con ``grid()``: las columnas de una rejilla son
        comunes a todas las filas, así que la tercera ficha de cada fila acabaría
        compartiendo ancho —el de la más larga— y la fila se abriría en huecos.
        Es la misma razón por la que ``GenreChips`` lo hace así.
        """
        for tag in self.__tags:
            tag.destroy()
        self.__tags.clear()
        if self.__tags_frame is None:
            return

        genres = self.anime_info.genres or []
        tag_font = Theme.font(*Theme.T_META)
        row, used = 0, 0
        for genre in genres:
            text = refactor_genre_text(genre)
            width = tag_font.measure(text) + 2 * GENRE_CHIP_PAD_X
            if used and used + width > available:
                row, used = row + 1, 0
            y = row * (GENRE_CHIP_H + GENRE_CHIP_GAP)
            # El borde lo pinta un CTkFrame y el texto va encima: un CTkLabel no
            # tiene `border_width`, y el contorno es lo que distingue una ficha de
            # una palabra suelta (`.tags span`: borde LINE, radio 13).
            #
            # ⚠️ El relleno es BG y no `transparent`: un CTkFrame transparente no
            # dibuja su rectángulo, y con él se va **también el borde**. Los
            # géneros salían como texto suelto, sin contorno, en los dos temas.
            chip = ctk.CTkFrame(
                self.__tags_frame,
                width=width,
                height=GENRE_CHIP_H,
                corner_radius=Metrics.pill_radius(GENRE_CHIP_H),
                fg_color=Theme.BG,
                border_width=1,
                border_color=Theme.LINE
            )
            chip.place(x=used, y=y)
            # La etiqueta va DENTRO de la ficha, no al lado. Como hermana suya y
            # del mismo tamaño la tapaba entera —incluido el borde—, porque un
            # CTkLabel transparente sigue pintando su fondo encima.
            label = ctk.CTkLabel(
                chip,
                text=text,
                # Más baja que la ficha a propósito: un CTkLabel transparente
                # pinta el fondo del padre, y con el alto por defecto (28 > 26)
                # borraba los tramos rectos del borde y solo quedaban las
                # esquinas redondeadas.
                width=tag_font.measure(text) + 2,
                height=GENRE_CHIP_H - 8,
                font=tag_font,
                fg_color=Theme.TRANSPARENT,
                text_color=Theme.TXT_2
            )
            # Con place() el hijo no arrastra el tamaño del marco, así que la
            # ficha conserva sus 26 px de alto sin tocar grid_propagate.
            label.place(relx=0.5, rely=0.5, anchor="center")
            self.__tags.append(chip)
            used += width + GENRE_CHIP_GAP

        # Con los hijos colocados por place() el marco no pide alto: hay que
        # dárselo o las fichas se solapan con lo que venga debajo.
        height = 0 if not genres else (row + 1) * (GENRE_CHIP_H + GENRE_CHIP_GAP) - GENRE_CHIP_GAP
        self.__tags_frame.configure(width=available, height=max(1, height))

    def __on_info_configure(self, event) -> None:
        """Re-envuelve el texto cuando la columna cambia de ancho de verdad.

        Pasa al plegar la barra lateral, que es justo el caso que la ficha de la
        fase señala: sin esto la sinopsis se queda con el ``wraplength`` del ancho
        anterior y se corta por la derecha (trampa 22).
        """
        if abs(event.width - self.__laid_out_width) <= RELAYOUT_THRESHOLD:
            return
        self.__relayout_text(event.width)

    # ------------------------------------------------------------------
    # Barra de vistos
    # ------------------------------------------------------------------
    def __build_seen_bar(self, info: ctk.CTkFrame) -> None:
        """«N de M vistos»: el único añadido real de la fase.

        Sale de ``get_watched_episodes()`` y de la lista de episodios que ya
        tiene la ficha, sin tocar la persistencia.
        """
        self.__seen_frame = ctk.CTkFrame(info, height=1, fg_color=Theme.TRANSPARENT)
        self.__seen_frame.grid(row=4, column=0, sticky="w", pady=(INFO_GAPS[3], 0))
        self.__refresh_seen_bar()

    def __refresh_seen_bar(self) -> None:
        """Repinta la barra con lo que hay marcado ahora mismo."""
        if self.__seen_frame is None or not self.__seen_frame.winfo_exists():
            return
        for widget in self.__seen_frame.winfo_children():
            widget.destroy()

        total = len(self.anime_info.episodes)
        if not total:
            # Sin lista de episodios no hay total que prometer: mismo criterio que
            # el sello de «Finalizados» de la fase 6, que ahí dice «Finalizado» en
            # vez de «0 / 0».
            return
        watched = sum(1 for episode in self.anime_info.episodes
                      if self.watched_status.get(episode.id, False))

        caption_text = f"{watched} de {total} vistos"
        caption_font = Theme.font(*Theme.T_SUB)
        # El ancho de la barra se calcula, no se estira: el bloque entero mide 420
        # (`.seen`: max-width 420) y el texto se queda con lo que necesita.
        bar_width = max(120, SEEN_W - caption_font.measure(caption_text) - SEEN_GAP)

        progress = ctk.CTkProgressBar(
            self.__seen_frame,
            width=bar_width,
            height=Metrics.PROGRESS_H,
            corner_radius=Metrics.PROGRESS_RADIUS,
            fg_color=Theme.LINE,
            progress_color=Theme.ACCENT
        )
        progress.set(watched / total)
        progress.grid(row=0, column=0, sticky="w")

        caption = ctk.CTkLabel(
            self.__seen_frame,
            text=caption_text,
            font=caption_font,
            text_color=Theme.TXT_3,
            anchor="w"
        )
        caption.grid(row=0, column=1, sticky="w", padx=(SEEN_GAP, 0))
        self.__seen_frame.configure(height=SEEN_H)

    # ------------------------------------------------------------------
    # Proveedor de la ficha
    #
    # Las tres líneas del bloque son un dato distinto cada una y hay que leerlas
    # juntas: "Proveedor: X" es de dónde vienen los datos que ves, "En tu
    # biblioteca: Y" es de quién es tu fila, y el botón ofrece juntarlas. El ⚠
    # ámbar compara las dos primeras (docs/13 §14).
    # ------------------------------------------------------------------
    def __build_provider_block(self, info: ctk.CTkFrame) -> None:
        """Indica **quién sirvió realmente** esta ficha, no el predeterminado.

        Es lo único que hace visible el fallback silencioso de
        ``call_with_fallback``: puedes tener AnimeAV1 seleccionado y estar viendo
        datos de otro porque el primero falló.

        El proveedor se elige en la sidebar.
        """
        provider_frame = ctk.CTkFrame(info, height=1, fg_color=Theme.TRANSPARENT)
        provider_frame.grid(row=0, column=0, sticky="ew")
        provider_frame.grid_columnconfigure(0, weight=1)

        who_frame = ctk.CTkFrame(provider_frame, height=1, fg_color=Theme.TRANSPARENT)
        who_frame.grid(row=0, column=0, sticky="w")

        provider_title = ctk.CTkLabel(
            who_frame,
            text="Proveedor:",
            font=Theme.font(*Theme.T_SUB),
            text_color=Theme.TXT_3,
            anchor="w"
        )
        provider_title.grid(row=0, column=0, sticky="w")

        provider_value = ctk.CTkLabel(
            who_frame,
            text=self.anime_provider_mgr.get_provider_name(self.provider_id),
            font=Theme.font(Theme.T_SUB[0], True),
            text_color=Theme.TXT,
            anchor="w"
        )
        provider_value.grid(row=0, column=1, sticky="w", padx=(5, 0))

        # Aviso de identidad partida: estos datos vienen de un sitio y la fila de
        # la biblioteca es de otro.
        if self.__is_saved:
            # De quién es la FILA, que es un dato distinto del de arriba y se
            # muestra siempre que el anime esté guardado.
            is_split = self.__has_split_identity()
            saved_name = (self.anime_provider_mgr.get_provider_name(self.__saved_provider_id)
                          if self.__saved_provider_id is not None
                          else "sin proveedor anotado")
            # La advertencia se reserva para la discrepancia de verdad: lo que
            # estás viendo no lo sirve el proveedor de tu fila, así que los
            # botones de estado y el póster escriben en algo distinto de lo que
            # tienes delante.
            library_label = ctk.CTkLabel(
                who_frame,
                text=f"{'⚠ ' if is_split else ''}En tu biblioteca: {saved_name}",
                font=Theme.font(*Theme.T_META),
                text_color=Theme.WARN if is_split else Theme.TXT_3,
                anchor="w"
            )
            library_label.grid(row=1, column=0, columnspan=2, sticky="w", pady=(5, 0))

        target_provider_id = self.__repair_target_provider_id()
        if target_provider_id is None:
            return
        # Pasar la fila a otro proveedor. Se ofrece aquí, pegado a la etiqueta que
        # dice de dónde salen los datos, porque es la misma pregunta vista desde
        # los dos lados: "esto viene de X" / "guárdalo desde Y".
        migrate_button = ctk.CTkButton(
            provider_frame,
            text=f"Actualizar a {self.anime_provider_mgr.get_provider_name(target_provider_id)}",
            font=Theme.font(Theme.T_META[0], True),
            height=FIX_BUTTON_H,
            width=1,
            corner_radius=Metrics.RADIUS_CONTROL,
            fg_color=Theme.ACCENT,
            hover_color=Theme.ACCENT,
            text_color=Theme.ACCENT_INK,
            command=self.__repair_to_target_provider
        )
        migrate_button.grid(row=0, column=1, sticky="e", padx=(16, 0))

    def __has_split_identity(self) -> bool:
        """Si la fila guardada y la ficha que se está viendo no son la misma cosa.

        Dos formas de que ocurra, y las dos se arreglan igual: el slug guardado es
        de otro sitio (el usuario se desvió y la ficha se localizó por título), o
        es el mismo slug pero lo está sirviendo un proveedor distinto del que
        consta en la fila (fallback).
        """
        if not self.__is_saved:
            return False
        if self.persistence_anime_id != str(self.anime_info.id):
            return True
        return (self.__saved_provider_id is not None and self.provider_id is not None
                and self.__saved_provider_id != self.provider_id)

    def __repair_target_provider_id(self) -> AnimeProviderId | None:
        """A qué proveedor se ofrece pasar esta fila, o ``None`` si no hay nada que hacer.

        Dos orígenes, en este orden:

        1. **Quien está sirviendo la ficha**, cuando no es el de la fila. Es lo que
           tienes delante, así que migrar no cuesta ni una petición.
        2. **El proveedor seleccionado en la sidebar**, cuando la ficha la sirve el
           de la fila pero tú estás usando otro. Este es el caso corriente —«tengo
           One Piece guardado desde AnimeFLV y quiero pasarlo a AnimeAV1»— y hay
           que localizar el anime allí antes de migrar, porque el slug es distinto
           en cada sitio.

        Atarlo solo al caso 1, como estaba, dejaba la acción fuera de alcance
        justo cuando más falta hace: al abrir un anime guardado sin desviar el
        desplegable lo sirve **el proveedor de su propia fila**, así que nunca
        había nada "partido" que reparar y el botón no llegaba a aparecer.
        """
        if not self.__is_saved:
            return None
        if self.__has_split_identity():
            return self.provider_id
        selected_provider_id = self.anime_provider_mgr.get_default_provider_id()
        if (selected_provider_id is not None and self.__saved_provider_id is not None and selected_provider_id != self.__saved_provider_id):
            return selected_provider_id
        return None

    def __repair_to_target_provider(self):
        """Punto de entrada del botón «Actualizar a …».

        Si el proveedor destino es el que ya está sirviendo la ficha, se migra con
        lo que hay en pantalla. Si es otro —el seleccionado en la sidebar—, primero
        hay que **localizar el anime allí**, porque su ``anime_id`` es un slug
        propio de cada sitio y el guardado no vale. Eso cuesta dos peticiones, así
        que va en un hilo aparte con el cursor de espera.
        """
        target_provider_id = self.__repair_target_provider_id()
        if target_provider_id is None:
            return

        if target_provider_id == self.provider_id:
            # Ya la tenemos delante: ni una petición.
            self.__confirm_and_migrate(self.anime_info, target_provider_id)
            return

        self.main_window.configure(cursor="watch")
        self.main_window.update_idletasks()

        def _resolved(resolved_anime_info: AnimeInfo | None):
            """Vuelta al hilo de Tkinter: aquí se abren los diálogos, no en el hilo."""
            if not self.main_window.winfo_exists():
                return
            self.main_window.configure(cursor="")
            provider_name = self.anime_provider_mgr.get_provider_name(target_provider_id)
            if resolved_anime_info is None:
                messagebox.showinfo(
                    f"{provider_name} no tiene este anime",
                    f"No se ha encontrado «{self.anime_info.title}» en {provider_name}, "
                    f"así que no se puede pasar tu biblioteca a ese proveedor.\n\n"
                    f"El anime sigue guardado como estaba."
                )
                return
            self.__confirm_and_migrate(resolved_anime_info, target_provider_id)

        def _resolve():
            reference = AnimeInfo(
                id=self.persistence_anime_id,
                title=self.anime_info.title,
                poster=self.persistence_poster_url
            )
            resolved_anime_info = self.anime_provider_mgr.resolve_anime_in_provider(reference, target_provider_id)
            self.main_window.after(0, _resolved, resolved_anime_info)

        threading.Thread(target=_resolve, daemon=True).start()

    def __confirm_and_migrate(self, anime_info: AnimeInfo, target_provider_id: AnimeProviderId):
        """Reescribe la fila guardada para que sea la de ``target_provider_id``.

        Es la única acción de la aplicación que reescribe la identidad de una fila
        de la biblioteca, así que se pide confirmación enumerando lo que cambia y
        lo que se conserva. Lo que se conserva es lo importante: los episodios
        vistos, que no se pueden recuperar de ningún sitio.

        :param anime_info: ficha **del proveedor destino**, de donde salen el
            identificador, el título y el póster nuevos.
        """
        animes_persistence = self.main_window.animes_persistence
        anime_record: AnimeRecord = animes_persistence.get_anime_by_anime_id(self.persistence_anime_id)
        if anime_record is None:
            # La fila puede haber desaparecido desde que se pintó la ficha.
            messagebox.showinfo(
                "Este anime ya no está guardado",
                "Este anime ya no consta en tu biblioteca, así que no hay nada que actualizar."
            )
            return

        new_anime_id = str(anime_info.id)
        provider_name = self.anime_provider_mgr.get_provider_name(target_provider_id)
        if (new_anime_id != self.persistence_anime_id
                and animes_persistence.get_anime_by_anime_id(new_anime_id) is not None):
            # Migrar dejaría dos filas del mismo anime, cada una con sus episodios
            # vistos. Se para aquí y no en la capa de persistencia para poder
            # explicarlo; migrate_anime_identity() lo comprueba igualmente.
            messagebox.showwarning(
                "No se puede actualizar",
                f"En tu biblioteca ya hay otra entrada de este anime en {provider_name}.\n\n"
                f"Elimina una de las dos antes de actualizar, o se quedarían duplicadas."
            )
            return

        changes = [f"  · proveedor: "
                   f"{self.anime_provider_mgr.get_provider_name(self.__saved_provider_id)} → {provider_name}"]
        if new_anime_id != self.persistence_anime_id:
            changes.append(f"  · identificador: {self.persistence_anime_id} → {new_anime_id}")
        if anime_info.title and anime_info.title != anime_record.title:
            changes.append(f"  · título: «{anime_record.title}» → «{anime_info.title}»")

        if not messagebox.askyesno(
            "Actualizar el anime guardado",
            f"«{anime_record.title}» pasará a guardarse desde {provider_name}:\n\n"
            + "\n".join(changes) +
            f"\n\nSe conservan los {len(anime_record.watched_episodes)} episodios vistos y "
            f"las categorías en las que está.\n\n¿Actualizarlo?"
        ):
            return

        old_anime_id = self.persistence_anime_id
        self.main_window.configure(cursor="watch")
        self.main_window.update_idletasks()

        def _done(migrated: bool):
            """Vuelta al hilo de Tkinter: aquí, y solo aquí, se toca la interfaz."""
            if not self.main_window.winfo_exists():
                return
            self.main_window.configure(cursor="")
            if not migrated:
                messagebox.showerror(
                    "No se pudo actualizar",
                    "No se ha podido actualizar el anime en tu biblioteca.\n\n"
                    "No se ha cambiado nada; revisa la consola para ver el detalle."
                )
                return
            # Ficha nueva en vez de retocar esta: así la identidad de persistencia
            # se vuelve a congelar a partir del anime ya migrado, en lugar de
            # mutar unos atributos que el resto de la clase da por inmutables. De
            # paso, la ficha pasa a mostrar los datos del proveedor nuevo.
            AnimeWindowViewer(self.main_window, anime_info, target_provider_id).display_anime_info()

        def _migrate():
            migrated = animes_persistence.migrate_anime_identity(
                old_anime_id, anime_info, target_provider_id)
            if migrated:
                self.__move_posters(anime_record, old_anime_id, new_anime_id, anime_info)
            self.main_window.after(0, _done, migrated)

        # En hilo aparte porque, si el póster no estaba cacheado, hay que bajarlo.
        threading.Thread(target=_migrate, daemon=True).start()

    def __move_posters(self, anime_record: AnimeRecord, old_anime_id: str, new_anime_id: str,
                       anime_info: AnimeInfo):
        """Lleva los pósters cacheados al nombre de fichero del ``anime_id`` nuevo.

        Solo en las categorías en las que está el anime, que son las únicas
        carpetas donde se guarda su imagen. Un fallo aquí no revierte la
        migración: el peor caso es un recuadro gris hasta la próxima descarga.
        """
        if old_anime_id == new_anime_id:
            return
        active_statuses = [
            (AnimeStatus.FAVOURITE, anime_record.is_favourite),
            (AnimeStatus.WATCHING,  anime_record.is_watching),
            (AnimeStatus.FINISHED,  anime_record.is_finished),
            (AnimeStatus.PENDING,   anime_record.is_pending),
        ]
        for status, is_active in active_statuses:
            if not is_active:
                continue
            try:
                if not move_anime_poster_by_status(status, old_anime_id, new_anime_id):
                    download_anime_poster_by_status(status, anime_info)
            except Exception as e:
                print(f"No se pudo actualizar el póster de {new_anime_id} "
                      f"en {status.name.lower()}: {e}")

    # ------------------------------------------------------------------
    # Botones de estado
    #
    # Dejan de cambiar de texto («Añadir a favoritos» / «Eliminar de favoritos»)
    # y pasan a **encenderse y apagarse**: los cuatro dicen siempre lo mismo y el
    # estado entero del anime se lee de un golpe (`DISENO.md` §7).
    #
    # Todos usan __persistence_anime_info() y persistence_anime_id, nunca
    # self.anime_info directamente: si no, cambiar de proveedor y pulsar uno de
    # estos botones crearía una fila nueva en ANIMES para el mismo anime.
    # ------------------------------------------------------------------
    def __build_status_buttons(self, info: ctk.CTkFrame) -> None:
        """Los cuatro botones, en una fila que reparte el ancho a partes iguales."""
        actions_frame = ctk.CTkFrame(info, height=1, fg_color=Theme.TRANSPARENT)
        actions_frame.grid(row=6, column=0, sticky="ew", pady=(INFO_GAPS[4], 0))
        actions_frame.grid_columnconfigure(tuple(range(len(STATUS_ORDER))), weight=1, uniform="status")

        self.__status_buttons.clear()
        for column, status in enumerate(STATUS_ORDER):
            # width=1 y sticky="ew": sin decirle un ancho, un CTkButton se queda
            # con los 140 px de la librería y los cuatro dejan de repartirse la
            # fila a partes iguales.
            button = ctk.CTkButton(
                actions_frame,
                text=StatusPill.text(status),
                width=1,
                height=Metrics.STATUS_BUTTON_H,
                corner_radius=Metrics.STATUS_BUTTON_RADIUS,
                compound="left",
                command=lambda chosen=status: self.__toggle_status(chosen)
            )
            padx = (0 if column == 0 else Metrics.STATUS_BUTTON_GAP, 0)
            button.grid(row=0, column=column, sticky="ew", padx=padx)
            self.__status_buttons[status] = button

        self.__refresh_status_buttons()

    def __refresh_status_buttons(self) -> None:
        """Enciende o apaga cada botón según el estado que tenga la fila.

        Encendido: fondo pastel del estado y texto de su color, sin borde.
        Apagado: fondo de tarjeta, borde ``LINE`` y texto secundario.

        El glifo se pide teñido del mismo color que el texto (``StatusPill.icon``
        con ``color=``): estos botones van sobre el fondo de la aplicación, no
        sobre una carátula, así que necesitan las dos variantes de tema.
        """
        for status, button in self.__status_buttons.items():
            if not button.winfo_exists():
                continue
            is_on = self.__status_state[status]
            text_color, background = StatusPill.colors(status)
            ink = text_color if is_on else Theme.TXT_2
            button.configure(
                font=Theme.font(Theme.T_UI[0], is_on),
                image=StatusPill.icon(status, STATUS_ICON_SIZE, color=ink),
                fg_color=background if is_on else Theme.CARD,
                hover_color=background if is_on else Theme.CARD_HOVER,
                text_color=ink,
                border_width=0 if is_on else 1,
                border_color=Theme.LINE
            )

    def __toggle_status(self, status: AnimeStatus) -> None:
        """Alterna el estado pulsado.

        El ``command`` de los botones ya no cambia: es siempre este, y decide
        entre ``add_to_*`` y ``remove_from_*`` mirando cómo está la fila. Los seis
        métodos públicos siguen existiendo y haciendo exactamente lo de antes.
        """
        actions = STATUS_ACTIONS[status]
        getattr(self, actions[1] if self.__status_state[status] else actions[0])()

    def __after_status_change(self) -> None:
        """Lo que hay que repintar después de tocar un estado.

        Los contadores de la barra lateral salen de las listas cacheadas del hub,
        y esas listas solo se llenan al arrancar: sin releerlas, la barra seguiría
        diciendo lo de antes hasta el siguiente arranque. Es la misma receta que
        usa «Empezar» en la vista de pendientes.
        """
        self.__refresh_status_buttons()
        animes_persistence = self.main_window.animes_persistence
        self.main_window.favourite_animes = animes_persistence.get_favourite_animes()
        self.main_window.watching_animes = animes_persistence.get_watching_animes()
        self.main_window.pending_animes = animes_persistence.get_pending_animes()
        self.main_window.finished_animes = animes_persistence.get_finished_animes()
        self.main_window.refresh_sidebar_counts()

    def __set_exclusive_status(self, status: Optional[AnimeStatus]) -> None:
        """Enciende uno de los tres excluyentes y apaga los otros dos.

        En pantalla igual que en BD: ``_set_status`` pone a 0 los otros dos al
        activar uno, así que dejar dos encendidos sería mentir. ``FAVOURITE`` es
        independiente y no entra aquí.
        """
        for candidate in EXCLUSIVE_STATUSES:
            self.__status_state[candidate] = (candidate == status)

    def __confirm_save(self, status: AnimeStatus) -> bool:
        """Avisa antes de crear una fila nueva de un anime que ya está guardado.

        La comprobación por ``anime_id`` no basta: el mismo anime tiene un slug
        distinto en cada sitio, así que abrirlo desde otro proveedor y pulsar un
        estado inserta una **segunda fila** del mismo anime, con sus propios
        episodios vistos y su propia entrada en las listas. Hasta ahora eso pasaba
        en silencio.

        Se consulta la BD en vez de mirar ``__is_saved``, que se calculó al pintar
        la ficha: si el usuario ya ha pulsado otro estado en esta misma pantalla,
        la fila existe desde entonces y no hay nada que avisar.

        :param status: sección a la que se está añadiendo, para nombrarla en el
            aviso en vez de hablar de «tu biblioteca» en abstracto.
        :return: ``True`` si se puede guardar (no hay duplicado, o el usuario lo
            ha aceptado a sabiendas).
        """
        animes_persistence = self.main_window.animes_persistence
        if animes_persistence.get_anime_by_anime_id(self.persistence_anime_id) is not None:
            return True

        duplicate = find_saved_duplicate(animes_persistence.get_all_animes(), self.anime_info.title,
                                         exclude_anime_id=self.persistence_anime_id)
        if duplicate is None:
            return True

        duplicate_provider = self.anime_provider_mgr.get_provider_name(duplicate.provider_id)
        provider_name = self.anime_provider_mgr.get_provider_name(self.provider_id)
        section_name = STATUS_SECTION_NAMES.get(status, "tu biblioteca")
        # Dónde está el duplicado se saca de sus propios flags y no de la sección
        # que se acaba de pulsar: puede estar en otra, o en ninguna si se quitó de
        # todas. Decir "ya está en Favoritos" cuando está en Pendientes sería
        # mentir justo en el dato por el que el usuario decide.
        duplicate_sections = [name for duplicate_status, name in STATUS_SECTION_NAMES.items()
                              if getattr(duplicate, duplicate_status.value)]
        location = f", en {' y '.join(duplicate_sections)}," if duplicate_sections else ""
        print(f"{self.anime_info.title!r} se parece a {duplicate.title!r} "
              f"({duplicate.anime_id}), ya guardado desde {duplicate_provider}")
        return messagebox.askyesno(
            "Puede que ya lo tengas guardado",
            f"Vas a añadir «{self.anime_info.title}» a tu Biblioteca de {section_name}.\n\n"
            f"«{duplicate.title}» ya está en tu biblioteca{location} guardado desde "
            f"{duplicate_provider}.\n\n"
            f"Si lo añades ahora tendrás el mismo anime dos veces, cada copia con sus "
            f"propios episodios vistos.\n\n"
            f"Para tenerlo en {provider_name} sin duplicarlo, ábrelo desde tu biblioteca "
            f"y usa «Actualizar a {provider_name}».\n\n"
            f"¿Añadirlo de todas formas?"
        )

    def add_to_favorites(self):
        if not self.__confirm_save(AnimeStatus.FAVOURITE):
            return
        anime_info = self.__persistence_anime_info()
        self.main_window.animes_persistence.update_anime_to_favourite(anime_info)
        download_anime_poster_by_status(AnimeStatus.FAVOURITE, anime_info)
        print(f"{self.anime_info.title} añadido a favoritos.")
        self.__status_state[AnimeStatus.FAVOURITE] = True
        self.__after_status_change()

    def remove_from_favorites(self):
        self.main_window.animes_persistence.update_anime_to_not_favourite(self.persistence_anime_id)
        remove_anime_poster_by_status(AnimeStatus.FAVOURITE, self.__persistence_anime_info())
        print(f"{self.anime_info.title} eliminado de favoritos.")
        self.__status_state[AnimeStatus.FAVOURITE] = False
        self.__after_status_change()

    def add_to_finished(self):
        if not self.__confirm_save(AnimeStatus.FINISHED):
            return
        anime_info = self.__persistence_anime_info()
        self.main_window.animes_persistence.update_anime_to_finished(anime_info)
        download_anime_poster_by_status(AnimeStatus.FINISHED, anime_info)
        print(f"{self.anime_info.title} añadido a finalizados.")
        self.__set_exclusive_status(AnimeStatus.FINISHED)
        self.__after_status_change()

    def remove_from_finished(self):
        self.main_window.animes_persistence.update_anime_to_not_finished(self.persistence_anime_id)
        remove_anime_poster_by_status(AnimeStatus.FINISHED, self.__persistence_anime_info())
        print(f"{self.anime_info.title} eliminado de finalizados.")
        # Quitarlo de finalizados no lo deja en el limbo: update_anime_to_not_finished
        # lo mueve a pendientes, y el botón de pendiente tiene que encenderse.
        self.__set_exclusive_status(AnimeStatus.PENDING)
        self.__after_status_change()

    def add_to_watching(self):
        if not self.__confirm_save(AnimeStatus.WATCHING):
            return
        anime_info = self.__persistence_anime_info()
        self.main_window.animes_persistence.update_anime_to_watching(anime_info)
        download_anime_poster_by_status(AnimeStatus.WATCHING, anime_info)
        print(f"{self.anime_info.title} añadido a viendo.")
        self.__set_exclusive_status(AnimeStatus.WATCHING)
        self.__after_status_change()

    def remove_from_watching(self):
        self.main_window.animes_persistence.update_anime_to_not_watching(self.persistence_anime_id)
        remove_anime_poster_by_status(AnimeStatus.WATCHING, self.__persistence_anime_info())
        print(f"{self.anime_info.title} eliminado de viendo.")
        self.__status_state[AnimeStatus.WATCHING] = False
        self.__after_status_change()

    def add_to_pending(self):
        if not self.__confirm_save(AnimeStatus.PENDING):
            return
        anime_info = self.__persistence_anime_info()
        self.main_window.animes_persistence.update_anime_to_pending(anime_info)
        download_anime_poster_by_status(AnimeStatus.PENDING, anime_info)
        print(f"{self.anime_info.title} añadido a pendientes.")
        self.__set_exclusive_status(AnimeStatus.PENDING)
        self.__after_status_change()

    def remove_from_pending(self):
        self.main_window.animes_persistence.update_anime_to_not_pending(self.persistence_anime_id)
        remove_anime_poster_by_status(AnimeStatus.PENDING, self.__persistence_anime_info())
        print(f"{self.anime_info.title} eliminado de pendientes.")
        self.__status_state[AnimeStatus.PENDING] = False
        self.__after_status_change()

    # ------------------------------------------------------------------
    # Lista de episodios
    # ------------------------------------------------------------------
    def __build_episodes(self, content: ctk.CTkFrame) -> None:
        """Cabecera de la lista (título, orden y buscador) y el cuerpo de filas."""
        episodes_frame = ctk.CTkFrame(content, fg_color=Theme.TRANSPARENT)
        episodes_frame.grid(row=1, column=0, sticky="ew", padx=Metrics.CONTENT_PAD_X,
                            pady=(EPISODES_PAD_TOP, SHEET_PAD_BOTTOM))
        episodes_frame.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(episodes_frame, height=1, fg_color=Theme.TRANSPARENT)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        header.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            header,
            text="Episodios",
            font=Theme.font(*Theme.T_ROW),
            text_color=Theme.TXT,
            anchor="w"
        )
        title.grid(row=0, column=0, sticky="w")

        self.__sort_button = ctk.CTkButton(
            header,
            text=self.__sort_text(),
            width=1,
            height=EPISODE_CONTROL_H,
            corner_radius=Metrics.RADIUS_CONTROL,
            font=Theme.font(*Theme.T_UI),
            fg_color=Theme.CARD,
            hover_color=Theme.CARD_HOVER,
            text_color=Theme.TXT_2,
            border_width=1,
            border_color=Theme.LINE,
            command=self.__toggle_sort_order
        )
        self.__sort_button.grid(row=0, column=1, sticky="e", padx=(9, 0))

        self.search_entry = ctk.CTkEntry(
            header,
            placeholder_text="Ir al episodio…",
            width=EPISODE_SEARCH_W,
            height=EPISODE_CONTROL_H,
            corner_radius=Metrics.RADIUS_CONTROL,
            font=Theme.font(*Theme.T_UI),
            fg_color=Theme.CARD,
            border_width=1,
            border_color=Theme.LINE,
            text_color=Theme.TXT,
            placeholder_text_color=Theme.TXT_3
        )
        self.search_entry.grid(row=0, column=2, sticky="e", padx=(9, 0))
        self.search_entry.bind("<Return>", self.__search_episodes)

        self.__episodes_body = ctk.CTkFrame(episodes_frame, height=1, fg_color=Theme.TRANSPARENT)
        self.__episodes_body.grid(row=1, column=0, sticky="ew")
        self.__episodes_body.grid_columnconfigure(0, weight=1)

        self.__display_episodes()

    def __sort_text(self) -> str:
        return "Mayor a menor  ↓" if self.sort_descending else "Menor a mayor  ↑"

    def __display_episodes(self, episodes_to_show: List[EpisodeInfo] | None = None):
        """Pinta las filas de episodio, o el corte de la lista que se le pase."""
        showing_all = episodes_to_show is None
        episodes_to_show = self.anime_info.episodes[:EPISODES_SHOWN] if showing_all else episodes_to_show
        for widget in self.__episodes_body.winfo_children():
            widget.destroy()
        self.__episode_rows.clear()
        self.__servers_frames.clear()

        # Lo que hay marcado manda la BD, no lo que quedó en pantalla: si la ficha
        # lleva abierta un rato, esto la vuelve a poner de acuerdo con la fila.
        bd_watched = self.main_window.animes_persistence.get_watched_episodes(self.persistence_anime_id)
        for episode_info in episodes_to_show:
            self.watched_status[episode_info.id] = episode_info.id in bd_watched

        if not episodes_to_show:
            empty_text = ("Este proveedor no ha listado episodios de este anime."
                          if not self.anime_info.episodes else "No hay ningún episodio con ese número.")
            empty_label = ctk.CTkLabel(
                self.__episodes_body,
                text=empty_text,
                font=Theme.font(*Theme.T_SUB),
                text_color=Theme.TXT_3,
                anchor="w"
            )
            empty_label.grid(row=0, column=0, sticky="w", pady=(10, 0))
            self.__refresh_seen_bar()
            return

        next_episode_id = self.__next_unwatched_episode_id()
        for index, episode_info in enumerate(episodes_to_show):
            row = EpisodeRow(
                self.__episodes_body,
                episode_info=episode_info,
                watched=self.watched_status.get(episode_info.id, False),
                state_text=self.__episode_state_text(episode_info, next_episode_id),
                on_click=self.__toggle_servers_frame,
                on_toggle=self.__toggle_episode_switch
            )
            # Las filas van en las posiciones pares y los servidores de cada una en
            # la impar de debajo: así desplegarlos no empuja nada ni obliga a
            # repintar la lista, y la fila impar mide cero mientras está vacía.
            row.grid(row=index * 2, column=0, sticky="ew")
            self.__episode_rows[episode_info.id] = row

        if showing_all and len(self.anime_info.episodes) > EPISODES_SHOWN:
            # El corte de 25 es viejo y sigue en pie (trampa 8). Decirlo aquí es
            # lo que convierte el buscador de al lado en la salida evidente.
            note = ctk.CTkLabel(
                self.__episodes_body,
                text=f"Se muestran {EPISODES_SHOWN} de {len(self.anime_info.episodes)} episodios · "
                     f"usa «Ir al episodio…» para llegar a los demás",
                font=Theme.font(*Theme.T_META),
                text_color=Theme.TXT_3,
                anchor="w"
            )
            note.grid(row=len(episodes_to_show) * 2, column=0, sticky="w",
                      padx=EPISODE_PAD_X, pady=(12, 0))

        self.__refresh_seen_bar()

    def __next_unwatched_episode_id(self) -> Optional[Any]:
        """El primer episodio que le queda por ver, en orden real ascendente."""
        for episode_info in sorted(self.anime_info.episodes, key=lambda episode: episode.id):
            if not self.watched_status.get(episode_info.id, False):
                return episode_info.id
        return None

    def __episode_state_text(self, episode_info: EpisodeInfo, next_episode_id: Optional[Any]) -> str:
        """La línea de apoyo de una fila.

        Un episodio visto no dice nada: el interruptor de la derecha ya lo cuenta,
        y repetirlo veinticinco veces es el dato duplicado que prohíbe
        `DISENO.md` §6.
        """
        if episode_info.id in self.__servers_frames:
            return "Servidores disponibles"
        if self.watched_status.get(episode_info.id, False):
            return ""
        if next_episode_id is not None and episode_info.id == next_episode_id:
            return "Siguiente para ti"
        return "Sin ver"

    def __refresh_episode_states(self) -> None:
        """Repasa la línea de apoyo y el interruptor de las filas en pantalla."""
        next_episode_id = self.__next_unwatched_episode_id()
        for episode_id, row in self.__episode_rows.items():
            if not row.winfo_exists():
                continue
            row.set_watched(self.watched_status.get(episode_id, False))
            row.set_state_text(self.__episode_state_text(row.episode_info, next_episode_id))

    def __display_previous_and_next_episodes(self, episode_info: EpisodeInfo):
        """Los dos botones de navegación que salen al buscar un episodio suelto."""
        navigation = ctk.CTkFrame(self.__episodes_body, height=1, fg_color=Theme.TRANSPARENT)
        navigation.grid(row=2, column=0, sticky="ew", padx=EPISODE_PAD_X, pady=(14, 0))
        navigation.grid_columnconfigure(1, weight=1)

        previous_button = ctk.CTkButton(
            navigation,
            text="← Episodio anterior",
            width=1,
            height=EPISODE_CONTROL_H,
            corner_radius=Metrics.RADIUS_CONTROL,
            font=Theme.font(*Theme.T_UI),
            fg_color=Theme.CARD,
            hover_color=Theme.CARD_HOVER,
            text_color=Theme.TXT_2,
            border_width=1,
            border_color=Theme.LINE,
            command=lambda: self.__previous_episode(episode_info)
        )
        previous_button.grid(row=0, column=0, sticky="w")

        next_button = ctk.CTkButton(
            navigation,
            text="Episodio siguiente →",
            width=1,
            height=EPISODE_CONTROL_H,
            corner_radius=Metrics.RADIUS_CONTROL,
            font=Theme.font(*Theme.T_UI),
            fg_color=Theme.CARD,
            hover_color=Theme.CARD_HOVER,
            text_color=Theme.TXT_2,
            border_width=1,
            border_color=Theme.LINE,
            command=lambda: self.__next_episode(episode_info)
        )
        next_button.grid(row=0, column=2, sticky="e")

    def __toggle_sort_order(self):
        # Cambiar el estado de orden y actualizar la lista de episodios
        self.sort_descending = not self.sort_descending
        self.anime_info.episodes.sort(
            key=lambda episode: episode.id,
            reverse=self.sort_descending
        )
        self.__sort_button.configure(text=self.__sort_text())
        self.__display_episodes()

    def __search_episodes(self, event=None):
        # Obtener el valor de búsqueda y filtrar episodios por ID
        query = self.search_entry.get().strip()
        if query.isdigit():
            query_id = int(query)
            # Filtrar la lista según el ID del episodio
            filtered_episode = next((ep for ep in self.anime_info.episodes if ep.id == query_id), None)
            if filtered_episode is None:
                self.__display_episodes([])
            else:
                self.__display_episodes([filtered_episode])
                self.__display_previous_and_next_episodes(filtered_episode)
        else:
            # Mostrar todos los episodios si no se ingresa un número válido
            self.__display_episodes()

    def __previous_episode(self, episode_info: EpisodeInfo):
        current_index = next(i for i, ep in enumerate(self.anime_info.episodes) if ep.id == episode_info.id)
        previous_index = current_index + 1 if self.sort_descending else current_index - 1

        # Verificar que el siguiente episodio está en el rango
        if 0 <= previous_index < len(self.anime_info.episodes):
            previous_episode = self.anime_info.episodes[previous_index]
            self.__display_episodes([previous_episode])
            self.__display_previous_and_next_episodes(previous_episode)

    def __next_episode(self, episode_info: EpisodeInfo):
        current_index = next(i for i, ep in enumerate(self.anime_info.episodes) if ep.id == episode_info.id)
        next_index = current_index - 1 if self.sort_descending else current_index + 1

        # Verificar que el siguiente episodio está en el rango
        if 0 <= next_index < len(self.anime_info.episodes):
            next_episode = self.anime_info.episodes[next_index]
            self.__display_episodes([next_episode])
            self.__display_previous_and_next_episodes(next_episode)

    def __toggle_episode_switch(self, episode_id: int):
        """Marca o desmarca un episodio. **Marcar es acumulativo; desmarcar, no.**

        Marcar el 5 marca del 1 al 5 y **conserva** los posteriores que ya
        estuvieran vistos; desmarcar el 3 desmarca solo el 3. Esa es la lógica que
        la fase no toca: aquí solo se le ha cambiado el envoltorio, de una lista
        de interruptores indexada por posición a las filas por identificador.
        """
        # Encontrar el índice del episodio en la lista COMPLETA del anime, en
        # orden real ascendente: el de la lista de la ficha depende del botón de
        # orden, y "todos los anteriores" no puede depender de cómo se esté
        # mirando la lista.
        all_episodes_sorted = sorted(self.anime_info.episodes, key=lambda ep: ep.id)
        try:
            ep_index_asc = next(i for i, ep in enumerate(all_episodes_sorted) if ep.id == episode_id)
        except StopIteration:
            print(f"Error: Episodio con ID {episode_id} no encontrado.")
            return

        marking_as_watched = not self.watched_status.get(episode_id, False)
        # IDs de todos los episodios hasta el marcado (inclusive) en orden real.
        episodes_up_to = {ep.id for ep in all_episodes_sorted[:ep_index_asc + 1]}

        # --- 1. Actualizar lo que se ve ---------------------------------
        if marking_as_watched:
            for ep_id in episodes_up_to:
                self.watched_status[ep_id] = True
        else:
            # Unitario: solo este episodio
            self.watched_status[episode_id] = False
        self.__refresh_episode_states()
        self.__refresh_seen_bar()

        # --- 2. Calcular el conjunto COMPLETO a persistir ----------------
        bd_watched = self.main_window.animes_persistence.get_watched_episodes(self.persistence_anime_id)

        if marking_as_watched:
            # Al marcar como visto: todos los episodios desde el inicio hasta
            # episode_id (en orden real ascendente) se consideran vistos,
            # salvo los que el usuario haya desmarcado explícitamente en BD.
            # Los episodios posteriores no se tocan.
            episodes_after = {ep_id for ep_id in bd_watched if ep_id > episode_id}
            merged = episodes_up_to | episodes_after
        else:
            # Al desmarcar: eliminar solo este episodio, el resto se preserva intacto
            merged = bd_watched - {episode_id}

        saved = self.main_window.animes_persistence.update_watched_episodes(self.persistence_anime_id, merged)

        # «Retomar donde lo dejaste» de la portada sale de aquí. Se apunta solo al
        # marcar (desmarcar no es «seguir viendo») y solo si el UPDATE encontró la
        # fila: update_watched_episodes() devuelve False cuando el anime no está en
        # la biblioteca, y guardar entonces su identificador dejaría en la banda una
        # tarjeta sin fila que pintar.
        # ⚠️ El identificador es persistence_anime_id, nunca anime_info.id: con el
        # desplegable desviado son slugs distintos (trampa 21).
        if saved and marking_as_watched:
            self.main_window.user_persistence.push_last_watched_id(self.persistence_anime_id)

    def __toggle_servers_frame(self, episode_info: EpisodeInfo):
        """Despliega o repliega los servidores de un episodio, bajo su fila."""
        row = self.__episode_rows.get(episode_info.id)
        if episode_info.id in self.__servers_frames:
            self.__servers_frames.pop(episode_info.id).destroy()
            if row is not None and row.winfo_exists():
                row.set_expanded(False)
                row.set_state_text(self.__episode_state_text(episode_info,
                                                             self.__next_unwatched_episode_id()))
            return

        # strict=True y provider_id explícito: `episode_info.anime` es el slug del
        # proveedor que sirvió esta ficha, así que pedir los servidores a otro
        # sitio con ese slug no devolvería nada útil. Sin esto, el bloque de
        # proveedor mentiría: diría "AnimeFLV" y abriría servidores de AnimeAV1.
        #
        # La petición va en el hilo de Tkinter, como hasta ahora. El cursor de
        # espera es lo único que se ha añadido: sin él, la ventana se queda quieta
        # un par de segundos sin explicar por qué.
        self.main_window.configure(cursor="watch")
        self.main_window.update_idletasks()
        try:
            servers_info: List[ServerInfo] = self.anime_provider_mgr.get_anime_episode_servers(
                episode_info.anime,
                episode_info.id,
                provider_id=self.provider_id,
                strict=True
            )
        finally:
            self.main_window.configure(cursor="")

        if not servers_info:
            provider_name = self.anime_provider_mgr.get_provider_name(self.provider_id)
            print(f"[{provider_name}] Sin servidores para el episodio "
                  f"{episode_info.id} de {episode_info.anime}")
            messagebox.showinfo(
                "Sin servidores disponibles",
                f"{provider_name} no ofrece servidores para el episodio "
                f"{episode_info.id}.\n\nPrueba a cambiar de proveedor en el "
                f"desplegable de la barra lateral y vuelve a abrir el anime."
            )
            return

        # La fila impar que hay justo debajo de la del episodio, reservada al
        # construir la lista: `grid_info()` dice en cuál cayó esta.
        grid_row = int(row.grid_info()["row"]) + 1 if row is not None else 1
        servers_frame = ctk.CTkFrame(self.__episodes_body, fg_color=Theme.CARD, corner_radius=8)
        servers_frame.grid(row=grid_row, column=0, sticky="ew", pady=(0, 8))
        servers_frame.grid_columnconfigure(0, weight=1)
        self.__servers_frames[episode_info.id] = servers_frame

        if row is not None and row.winfo_exists():
            row.set_expanded(True)
            row.set_state_text(self.__episode_state_text(episode_info, None))

        server_url_map = {server.server: server.url for server in servers_info}
        server_button = ctk.CTkSegmentedButton(
            servers_frame,
            values=list(server_url_map.keys()),
            font=Theme.font(*Theme.T_UI),
            fg_color=Theme.BG,
            selected_color=Theme.ACCENT,
            selected_hover_color=Theme.ACCENT,
            unselected_color=Theme.BG,
            unselected_hover_color=Theme.CARD_HOVER,
            text_color=Theme.TXT_2
        )
        server_button.grid(row=0, column=0, sticky="w", padx=EPISODE_PAD_X, pady=14)
        server_button.set(None)
        server_button.configure(command=lambda selected: self.__play_video(server_url_map[selected]))

    def __play_video(self, url):
        webbrowser.open(url)
