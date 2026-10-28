__author__ = "Jose David Escribano Orts"
__subsystem__ = "gui"
__module__ = "anime_window.py"
__version__ = "0.13"
__info__ = {"subsystem": __subsystem__, "module_name": __module__, "version": __version__}

"""Ficha de detalle de un anime: la pantalla desde la que se ve un episodio.

Los cuatro botones de estado se encienden y se apagan en vez de cambiar de
texto, y las filas de episodio muestran solo «Episodio N» con su línea de
estado al lado. La ficha se puede abrir **por un episodio** (``focus_episode``):
sale con esa fila desplegada, sus servidores a la vista y la ventana desplazada
hasta ella.

Pulsar un servidor abre el reproductor acoplado **encima** de la ficha, que se
queda debajo tal cual. Si el hoster no se puede resolver o el vídeo no arranca,
el episodio se abre en el navegador y el panel lo dice.

Es el fichero donde confundir la identidad de visualización con la de
persistencia (ver ``AnimeWindowViewer``) duplica filas en la biblioteca real.
"""

import re
import threading
import webbrowser
import customtkinter as ctk

from collections import OrderedDict
from dataclasses import dataclass, replace
from tkinter import messagebox
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from PIL import Image

from APIs.common.models import AnimeFormat, AnimeInfo, AnimeProviderId, AnimeRelationType, EpisodeInfo, \
    RelatedAnime, ServerInfo
from APIs.common.animeProviderMgr import AnimeProviderManager, AnimeProviderManagerSingleton
from APIs.resolvers import registry
from APIs.resolvers.base import MediaSource
from dataPersistence.animesPersistence import AnimeStatus, AnimeRecord
from gui.components.franchise_cards import CAROUSEL_POSTER, CarouselItem, RelatedCard, RelatedGrid, \
    SeasonCarousel, SeasonLink, format_chip
from gui.components.status_pill import StatusPill
from gui.components.tab_bar import TabBar
from gui.components.video_player import VideoPlayer, player_icon
from gui.franchise_service import FormatHint, FranchiseLine, closest_related, deduce_format_from_title
from gui.theme import Metrics, Theme
from utils.utils import refactor_genre_text, download_poster, find_cached_poster_path, \
    load_rounded_image, round_image, download_anime_poster_by_status, move_anime_poster_by_status, \
    sync_status_posters

_POSTER_SYNC_LOCK = threading.Lock()

#: Pósters de temporadas y relacionados ya bajados en la sesión, reducidos al
#: mayor tamaño en que se pintan. Se guarda la imagen PIL, nunca el CTkImage.
_RELATED_POSTERS: "OrderedDict[str, Image.Image]" = OrderedDict()
_RELATED_POSTERS_LOCK = threading.Lock()
_RELATED_POSTERS_MAX = 120

#: Similitud mínima entre títulos para avisar de que un anime que se va a
#: guardar puede ser el mismo que otro ya guardado. Por encima del umbral con el
#: que se busca (0.75-0.8) a propósito: aquí un falso positivo interrumpe al
#: usuario por dos animes distintos de la misma saga, mientras que un falso
#: negativo solo deja pasar el duplicado.
DUPLICATE_TITLE_THRESHOLD = 0.9

#: Cómo se llama cada estado de cara al usuario, para nombrar la sección
#: concreta en los diálogos ("tu Biblioteca de Favoritos").
STATUS_SECTION_NAMES = {
    AnimeStatus.FAVOURITE: "Favoritos",
    AnimeStatus.WATCHING:  "Viendo",
    AnimeStatus.FINISHED:  "Finalizados",
    AnimeStatus.PENDING:   "Pendientes",
}

#: Orden de los cuatro botones de estado, de izquierda a derecha. El texto y
#: los colores de cada uno los pone ``StatusPill``.
STATUS_ORDER: Tuple[AnimeStatus, ...] = (
    AnimeStatus.FAVOURITE,
    AnimeStatus.WATCHING,
    AnimeStatus.PENDING,
    AnimeStatus.FINISHED,
)

#: Los tres que se apagan entre sí. ``FAVOURITE`` no está: es independiente y se
#: puede tener a la vez que cualquiera de estos.
EXCLUSIVE_STATUSES: Tuple[AnimeStatus, ...] = (
    AnimeStatus.WATCHING,
    AnimeStatus.PENDING,
    AnimeStatus.FINISHED,
)

#: Qué método llama cada botón, según esté apagado o encendido: (añadir, quitar).
STATUS_ACTIONS: Dict[AnimeStatus, Tuple[str, str]] = {
    AnimeStatus.FAVOURITE: ("add_to_favorites", "remove_from_favorites"),
    AnimeStatus.WATCHING:  ("add_to_watching",  "remove_from_watching"),
    AnimeStatus.PENDING:   ("add_to_pending",   "remove_from_pending"),
    AnimeStatus.FINISHED:  ("add_to_finished",  "remove_from_finished"),
}

#: Cuántos episodios se pintan. Corte duro: con AnimeAV1 (orden ascendente) son
#: los 25 **primeros** y con AnimeFLV los 25 **más recientes**. Para llegar a
#: otro está el buscador.
EPISODES_SHOWN = 25

#: Separación entre el póster y la columna de información.
SHEET_GAP = 30
#: Aire por encima de la ficha y por debajo de la lista de episodios.
SHEET_PAD_TOP = 26
SHEET_PAD_BOTTOM = 24
#: Separación por encima de cada bloque de la columna de información, de arriba
#: abajo: título, sinopsis, géneros, temporada anterior y siguiente, barra de
#: vistos y botones de estado. El bloque de proveedor va el primero y no lleva.
INFO_GAPS = (12, 14, 16, 16, 18, 18)
#: «← Volver a …» encima de la ficha y su separación con ella.
BACK_PAD_TOP = 16
BACK_GAP = 10
BACK_TITLE_W = 520
#: Ancho máximo del bloque de la barra de vistos.
SEEN_W = 420
#: Alto de ese bloque. Un CTkFrame necesita alto explícito o conserva los 200 por
#: defecto como tamaño pedido y estira la fila que lo contenga.
SEEN_H = 22
#: Separación entre la barra y su leyenda.
SEEN_GAP = 12
#: Fichas de género.
GENRE_CHIP_H = 26
GENRE_CHIP_GAP = 7
GENRE_CHIP_PAD_X = 11
#: Lado del glifo de los botones de estado.
STATUS_ICON_SIZE = 14
#: Alto del botón «Actualizar a …» del bloque de proveedor.
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

#: Espera antes de desplegar el episodio por el que se ha abierto la ficha y
#: desplazarse hasta él: le da un turno al bucle de eventos para que la ficha se
#: pinte entera antes de medir dónde ha caído la fila.
FOCUS_DELAY_MS = 50
#: Aire que se deja por encima de la fila a la que se desplaza la ficha. Pegarla
#: al borde superior escondería que hay lista antes de ella.
FOCUS_SCROLL_MARGIN = 24

#: Columna de información del reproductor: separaciones entre bloques y el
#: alto de las fichas de servidor y del botón «Siguiente episodio».
PLAYER_BLOCK_GAP = 24
PLAYER_CHIP_H = 30
PLAYER_CHIP_GAP = 8
PLAYER_NEXT_H = 44
#: Qué dice la columna, y la fila del episodio que suena, en cada estado del reproductor.
PLAYER_STATUS_LABELS = {
    "loading": "Cargando",
    "playing": "Reproduciendo",
    "browser": "En el navegador",
    "ended": "Terminado",
    "unavailable": "Sin servidores",
}
#: Ancho máximo del título de la temporada siguiente en el botón de la tarjeta de fin.
END_CARD_TITLE_W = 150

#: Claves de las pestañas de la ficha.
TAB_EPISODES = "episodes"
TAB_RELATIONS = "relations"
#: Separación entre los bloques de la pestaña de relacionados.
RELATIONS_BLOCK_GAP = 26
RELATIONS_GROUP_GAP = 20

#: Cómo se lee cada formato y cada tipo de relación.
FORMAT_LABELS: Dict[AnimeFormat, str] = {
    AnimeFormat.SERIES: "Serie",
    AnimeFormat.MOVIE: "Película",
    AnimeFormat.OVA: "OVA",
    AnimeFormat.SPECIAL: "Especial",
    AnimeFormat.ONA: "ONA",
}
RELATION_LABELS: Dict[AnimeRelationType, str] = {
    AnimeRelationType.PREQUEL: "Precuela",
    AnimeRelationType.SEQUEL: "Secuela",
    AnimeRelationType.ALTERNATIVE: "Versión alternativa",
    AnimeRelationType.OTHER: "Otro",
}
#: Grupos de la pestaña de relacionados, en el orden en que se pintan.
GROUP_MOVIES = "Películas"
GROUP_SERIES = "Series y ONA"
GROUP_OVAS = "OVAs y especiales"
GROUP_ALTERNATIVES = "Versiones alternativas"
GROUP_UNKNOWN = "Sin formato"
RELATION_GROUPS = (GROUP_MOVIES, GROUP_SERIES, GROUP_OVAS, GROUP_ALTERNATIVES, GROUP_UNKNOWN)


@dataclass(frozen=True)
class SheetVisit:
    """Una ficha de la que se ha salido abriendo un relacionado, para poder volver a ella sin red.

    :ivar anime_info: La ficha tal como estaba en pantalla.
    :ivar provider_id: Proveedor que la sirvió.
    :ivar anime_record: Fila guardada con la que se abrió, para conservar su identidad de persistencia.
    """
    anime_info: AnimeInfo
    provider_id: Optional[AnimeProviderId]
    anime_record: Optional[AnimeRecord]


# TODO: Al final de la lista de episodios nuevo frame del estilo. "Si te ha gustado One piece, te puede interesar..." y
#  mostrar 4 animes con los mimos generos.

# TODO: Agregar botón para alternar entre el manga y el anime.


#: Fin de línea al estilo Windows o Mac clásico, normalizado a ``\n`` antes que
#: nada: ninguno de los dos patrones de abajo lo reconocería.
_CARRIAGE_RETURN = re.compile(r"\r\n?")
#: Un salto de línea con espacios o tabuladores alrededor, sin otro salto pegado:
#: es un corte de renglón del sitio de origen, no una separación de párrafos.
_SOFT_BREAK = re.compile(r"(?<!\n)[ \t]*\n[ \t]*(?!\n)")
#: Dos o más saltos seguidos, con lo que haya entre medias: eso sí es un párrafo.
_PARAGRAPH_BREAK = re.compile(r"[ \t]*\n[ \t\n]*\n[ \t]*")


def wrap_synopsis(synopsis: Optional[str]) -> Optional[str]:
    """Normaliza los saltos de línea de la sinopsis para que envuelva bien al pintarla.

    ``wraplength`` no puede deshacer un ``\\n`` explícito, así que un salto
    suelto del proveedor se convierte en espacio y dos seguidos (un párrafo) se
    conservan. Se hace al pintar, no al raspar, para que también beneficie a las
    filas ya guardadas en BD sin migrar nada.

    :param synopsis: Sinopsis tal como la da el proveedor; admite None.
    :return: Sinopsis normalizada, o None si no había ninguna.
    """
    if not synopsis:
        return synopsis
    # Primero los párrafos, a un marcador que el texto no puede contener: si se
    # colapsaran antes los saltos sueltos, el patrón de párrafo no encontraría nada.
    marker = "\x00"
    text = _PARAGRAPH_BREAK.sub(marker, _CARRIAGE_RETURN.sub("\n", synopsis).strip())
    text = _SOFT_BREAK.sub(" ", text)
    return text.replace(marker, "\n\n")


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

    Compara con title_similarity(), que es lo único común entre proveedores y no
    confunde dos temporadas del mismo anime. No detecta títulos completamente distintos
    para el mismo anime ("Solo Leveling" y "Ore dake Level Up na Ken"): eso no
    hay forma de saberlo sin preguntar a la red, y esto corre en el hilo de la
    interfaz.

    :param exclude_anime_id: fila que no cuenta como duplicado (normalmente, la
        del propio anime que se está guardando).
    :return: el ``AnimeRecord`` más parecido si supera
        ``DUPLICATE_TITLE_THRESHOLD``, o ``None``.
    """
    best_record: Optional[AnimeRecord] = None
    best_ratio: float = 0.0
    for anime_record in anime_records:
        if exclude_anime_id is not None and str(anime_record.anime_id) == str(exclude_anime_id):
            continue
        ratio = AnimeProviderManager.title_similarity(title, anime_record.title)
        if ratio == 1.0:
            return anime_record
        if ratio > best_ratio:
            best_record, best_ratio = anime_record, ratio

    return best_record if best_ratio >= DUPLICATE_TITLE_THRESHOLD else None


def sync_saved_posters_async(animes_persistence, anime_info: AnimeInfo) -> None:
    """Pone en un hilo el póster del anime en las carpetas de los estados que tiene su fila.

    Los estados los dice la fila releída y no el botón pulsado, porque la BD mueve
    otros por su cuenta (quitar de «Finalizados» lo pasa a «Pendientes»). El cerrojo
    hace que, con dos clics seguidos, el último en correr deje el disco como la BD.

    :param animes_persistence: Persistencia de donde se relee la fila.
    :param anime_info: Anime con la identidad de la fila guardada; se leen ``.id`` y ``.poster``.
    """
    def _sync():
        with _POSTER_SYNC_LOCK:
            try:
                record = animes_persistence.get_anime_by_anime_id(str(anime_info.id))
                statuses = {status: record is not None and bool(getattr(record, status.value))
                            for status in AnimeStatus}
                sync_status_posters(anime_info, statuses)
            except Exception as e:
                print(f"No se pudieron poner al día los pósters de {anime_info.id}: {e}")

    threading.Thread(target=_sync, daemon=True).start()


def _related_poster(url: Optional[str], disk_id: Optional[str]) -> Optional[Image.Image]:
    """Póster de una temporada o un relacionado: del disco, de lo bajado en la sesión o de la red.

    Sale a la red: solo desde un hilo daemon.

    :param url: URL del póster, o None si el proveedor no la da.
    :param disk_id: anime_id con el que buscarlo entre los pósters ya guardados.
    :return: La imagen reducida al tamaño del carrusel, o None si no hay forma.
    """
    if disk_id:
        path = find_cached_poster_path(disk_id)
        if path is not None:
            try:
                with Image.open(path) as image:
                    return image.convert("RGB").resize(CAROUSEL_POSTER, Image.LANCZOS)
            except Exception as e:
                print(f"No se pudo leer el póster {path}: {e}")
    if not url:
        return None
    with _RELATED_POSTERS_LOCK:
        cached = _RELATED_POSTERS.get(url)
        if cached is not None:
            _RELATED_POSTERS.move_to_end(url)
            return cached
    image = download_poster(url)
    if image is None:
        return None
    image = image.convert("RGB").resize(CAROUSEL_POSTER, Image.LANCZOS)
    with _RELATED_POSTERS_LOCK:
        _RELATED_POSTERS[url] = image
        while len(_RELATED_POSTERS) > _RELATED_POSTERS_MAX:
            _RELATED_POSTERS.popitem(last=False)
    return image


def library_status(anime_record: Optional[AnimeRecord]) -> Optional[AnimeStatus]:
    """Qué estado se enseña de una fila: el excluyente que tenga y, si no tiene, «Favorito».

    Es la misma regla que el sello de «Buscar».

    :param anime_record: Fila guardada, o None si el anime no está en la biblioteca.
    :return: Estado a mostrar, o None si no hay ninguno.
    """
    if anime_record is None:
        return None
    status = StatusPill.other_status(anime_record)
    if status is not None:
        return status
    return AnimeStatus.FAVOURITE if anime_record.is_favourite else None


def open_saved_anime(main_window, anime_id: Union[str, int],
                     focus_episode: Optional[int] = None,
                     force_ascending: bool = False,
                     history: Optional[List[SheetVisit]] = None) -> None:
    """Abre la ficha de un anime ya guardado en la biblioteca.

    Punto de entrada único de las cuatro vistas de estado. El fallback sigue
    activo a propósito: fijar el proveedor de la fila impediría abrir animes
    cuyo slug ya no responde en el proveedor que los guardó. Si el refresco de
    episodios acaba de traer la ficha de ese proveedor, se abre sin salir a la red.

    :param main_window: Hub de la aplicación.
    :param anime_id: anime_id de la fila, el slug del proveedor que la guardó.
    :param focus_episode: Episodio por el que abrir la ficha, ya desplegado y a
        la vista; None abre la ficha normal.
    :param force_ascending: Fuerza el orden ascendente, para que el episodio de
        entrada quede primero en vez de al final de la lista.
    :param history: Fichas de las que se viene, para «← Volver a …»; None si se
        abre desde una vista.
    """
    anime_record: AnimeRecord = main_window.animes_persistence.get_anime_by_anime_id(anime_id)
    provider_id, is_deviation = main_window.provider_for_saved_anime(anime_record.provider_id if anime_record is not None else None)

    cached_info = None if is_deviation else main_window.episode_refresher.cached_info(anime_id, provider_id)
    if cached_info is not None:
        # after() y no una llamada directa: la ficha destruye la vista, y con ella
        # el widget cuyo clic se está atendiendo ahora mismo.
        main_window.after(0, lambda: AnimeWindowViewer(main_window, cached_info, provider_id,
                                                       anime_record=anime_record,
                                                       focus_episode=focus_episode,
                                                       force_ascending=force_ascending,
                                                       history=history).display_anime_info())
        return

    main_window.configure(cursor="watch")
    # Evita que un segundo clic reentre aquí y lance un segundo hilo.
    main_window.update_idletasks()

    def _show(anime_info, served_by):
        # Repintar vuelve siempre al hilo de Tkinter: display_anime_info() destruye
        # los widgets de la vista anterior y eso no es seguro desde el hilo secundario.
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
                          anime_record=anime_record,
                          focus_episode=focus_episode,
                          force_ascending=force_ascending,
                          history=history).display_anime_info()

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
    """Una fila de la lista de episodios: número, línea de estado e interruptor «Visto».

    La fila entera es pulsable y despliega los servidores debajo. El
    interruptor no hereda ese clic: los eventos de Tk no burbujean, así que
    marcar un episodio no abre sus servidores sin querer.
    """

    __hovered: Optional["EpisodeRow"] = None

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
        self.__current = False

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
        self.__paint_highlight()

    def set_current(self, current: bool) -> None:
        """Resalta la fila del episodio que está en el reproductor, esté desplegada o no."""
        self.__current = current
        self.__paint_highlight()

    def __is_lit(self) -> bool:
        return self.__expanded or self.__current

    def __paint_highlight(self) -> None:
        if self.__is_lit():
            self.configure(fg_color=Theme.CARD)
        else:
            self.configure(fg_color=Theme.CARD_HOVER if self.__pointer_inside() else Theme.TRANSPARENT)
        self.number_label.configure(text_color=Theme.ACCENT if self.__is_lit() else Theme.TXT)

    # ------------------------------------------------------------------
    # Interacción
    # ------------------------------------------------------------------
    def __bind_interactions(self) -> None:
        """Ata hover y clic a la fila y a sus hijos, ya que los eventos de Tk no burbujean.

        El clic se queda en la fila y sus dos etiquetas (el interruptor tiene su
        propio comando); el hover se ata a todos los hijos, interruptor incluido,
        para no perder el resaltado al pasar sobre ellos. Si se añade un hijo, hay que atarlo.
        """
        for widget in (self, self.number_label, self.state_label, self.switch):
            widget.bind("<Enter>", self.__handle_enter)
            widget.bind("<Leave>", self.__handle_leave)
        for widget in (self, self.number_label, self.state_label):
            widget.bind("<Button-1>", self.__handle_click)
            widget.configure(cursor="hand2")

    def __handle_click(self, _event=None) -> None:
        self.__on_click(self.episode_info)

    def __handle_enter(self, _event=None) -> None:
        previous = EpisodeRow.__hovered
        if previous is not None and previous is not self:
            previous.__release_hover()
        EpisodeRow.__hovered = self
        if not self.__is_lit():
            self.configure(fg_color=Theme.CARD_HOVER)

    def __handle_leave(self, _event=None) -> None:
        # Tk manda Leave también al pasar del marco a uno de sus hijos, así que
        # apagar el resaltado sin mirar dónde está el puntero hace parpadear la fila.
        if self.__pointer_inside():
            return
        self.__release_hover()

    def __release_hover(self) -> None:
        """Apaga el resaltado, lo pida esta fila o la que se enciende después."""
        if EpisodeRow.__hovered is self:
            EpisodeRow.__hovered = None
        if not self.__is_lit() and self.winfo_exists():
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

    Maneja dos identidades del mismo anime, y confundirlas duplica filas en la
    biblioteca: la de **visualización** (``self.anime_info``, ``self.provider_id``,
    de donde salen título, sinopsis, episodios y servidores) es la del proveedor
    que sirvió la ficha; la de **persistencia** (``self.persistence_anime_id``,
    ``self.persistence_poster_url``, ``self.persistence_provider_id``) es la de la
    fila guardada, no cambia mientras la ficha está en pantalla, y es la única
    que debe usarse en operaciones de BD y de póster.

    ``AnimeInfo.id`` es el slug del sitio, no un identificador universal: el
    mismo anime es "one-piece" en AnimeAV1 y "one-piece-tv" en AnimeFLV, así que
    persistir con el id de visualización en vez de con el de apertura insertaría
    una fila nueva. Las dos identidades pueden separarse (fallback a otro
    proveedor, o desplegable desviado de la sidebar); cuando lo hacen, la ficha
    lo avisa y ofrece reapuntar la fila al proveedor actual
    (``__repair_to_target_provider``).

    Se compone de dos bloques dentro del ``content_frame``: la cabecera (póster,
    proveedor, título, sinopsis, géneros, temporada anterior y siguiente, barra
    de vistos y botones de estado) y las pestañas, que abren siempre en
    Episodios. Las demás no se construyen ni piden nada a la red hasta que se
    abren. Abrir un relacionado deja esta ficha en el historial de la siguiente.
    """

    def __init__(self, main_window, anime_info: AnimeInfo, provider_id: AnimeProviderId | None = None,
                 anime_record: AnimeRecord | None = None,
                 focus_episode: Optional[int] = None, force_ascending: bool = False,
                 history: Optional[List[SheetVisit]] = None):
        """Construye la ficha. anime_record es obligatorio cuando la ficha puede
        venir de un proveedor distinto al que guardó el anime: sin él se asume
        que anime_info es también lo guardado.

        :param anime_info: Ficha del anime; no puede ser None.
        :param provider_id: Proveedor que sirvió esa ficha; por defecto el que
            traiga el propio AnimeInfo, o el predeterminado.
        :param anime_record: Fila con la que está guardado este anime, si lo está.
        :param focus_episode: Episodio por el que abrir la ficha, ya desplegado.
        :param force_ascending: Fuerza el orden ascendente pase lo que pase.
        :param history: Fichas de las que se viene abriendo relacionados, la más
            reciente al final. Vive solo en la cadena de fichas: cambiar de vista la olvida.
        """
        if anime_info is None:
            raise ValueError("AnimeWindowViewer requiere un AnimeInfo; se recibió None")
        self.main_window = main_window
        self.__anime_record: Optional[AnimeRecord] = anime_record
        self.__history: List[SheetVisit] = list(history or [])
        self.anime_provider_mgr: AnimeProviderManager = AnimeProviderManagerSingleton()
        self.anime_info: AnimeInfo = self.__with_episodes(anime_info)

        self.provider_id: AnimeProviderId | None = (provider_id or anime_info.provider_id or self.anime_provider_mgr.get_default_provider_id())

        # Identidad de persistencia: se congela aquí y no se vuelve a tocar. Solo se
        # separa de la de visualización cuando el slug guardado no es el que se está
        # viendo (la ficha se localizó por título en otro proveedor); si coinciden,
        # manda el de visualización aunque haya entrado el fallback.
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
        #: Orden en que llega la lista del proveedor, que no es el mismo en todos
        #: (AnimeAV1 ascendente, AnimeFLV descendente). La lista no se reordena al
        #: abrir: el corte de 25 sigue siendo el que era.
        self.sort_descending: bool = self.__incoming_order_is_descending()
        if force_ascending and self.sort_descending:
            self.anime_info = replace(
                self.anime_info,
                episodes=sorted(self.anime_info.episodes, key=lambda episode: episode.id)
            )
            self.sort_descending = False
        self.__focus_episode: Optional[int] = focus_episode
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
        #: Despliegue en vuelo de cada episodio (número que se compara al llegar la
        #: respuesta) y la línea de apoyo que lleva mientras está desplegado.
        self.__servers_requests: Dict[Any, int] = {}
        self.__servers_states: Dict[Any, str] = {}
        self.__servers_request_seq: int = 0
        self.search_entry: Optional[ctk.CTkEntry] = None

        # --- Pestañas y franquicia -----------------------------------------
        self.__tabs: Optional[TabBar] = None
        self.__carousel: Optional[SeasonCarousel] = None
        self.__others_frame: Optional[ctk.CTkFrame] = None
        #: Relacionados de la pestaña que no están en la línea principal.
        self.__others: List[RelatedAnime] = []
        self.__format_hints: Dict[str, FormatHint] = {}
        self.__formats_pending: bool = False
        self.__related_cards: Dict[str, RelatedCard] = {}
        #: Pósters ya llegados de la pestaña, por id: repintar las tarjetas no los vuelve a pedir.
        self.__related_posters: Dict[str, Image.Image] = {}
        #: Última apertura de un relacionado: una respuesta con otro número llega tarde.
        self.__open_request_seq: int = 0
        #: Título de cada temporada del carrusel, para buscarla en la biblioteca al abrirla.
        self.__line_titles: Dict[str, str] = {}

        # --- Reproductor acoplado ------------------------------------------
        self.__player: Optional[VideoPlayer] = None
        self.__player_info: Optional[ctk.CTkFrame] = None
        self.__player_status_label: Optional[ctk.CTkLabel] = None
        self.__player_episode_label: Optional[ctk.CTkLabel] = None
        self.__player_detail_label: Optional[ctk.CTkLabel] = None
        self.__player_servers_frame: Optional[ctk.CTkFrame] = None
        self.__player_seen_frame: Optional[ctk.CTkFrame] = None
        self.__player_next_frame: Optional[ctk.CTkFrame] = None
        self.__player_next_label: Optional[ctk.CTkLabel] = None
        self.__player_next_number: Optional[ctk.CTkLabel] = None
        #: Servidores y elegido con los que se pintaron las fichas de la columna.
        self.__player_servers_key: Optional[Tuple[Tuple[Tuple[str, str], ...], Optional[str]]] = None
        #: Episodio que está en el reproductor, sus servidores (etiqueta → URL),
        #: el servidor elegido y el estado: loading, playing, browser o ended.
        self.__playing_episode: Optional[EpisodeInfo] = None
        self.__playing_servers: Dict[str, str] = {}
        self.__playing_label: Optional[str] = None
        self.__playing_status: Optional[str] = None
        #: Servidores de este episodio que ya han acabado en el navegador.
        self.__failed_servers: set = set()
        #: Número de la última resolución pedida: una respuesta con otro número llega tarde.
        self.__play_request_seq: int = 0
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
        # content_frame lo comparten todas las vistas y su configuración de rejilla
        # sobrevive a clear_frame(): una columna o fila con peso y sin widgets
        # también recibe el espacio sobrante, así que hay que devolverlas a cero.
        for column in range(1, 4):
            content.grid_columnconfigure(column, weight=0)
        for row in range(1, 6):
            content.grid_rowconfigure(row, weight=0)

        self.__build_sheet(content)
        self.__build_tabs(content)

        if self.__focus_episode is not None:
            # Con after y no aquí: desplazarse hasta la fila exige medirla, y eso
            # solo es fiable con la ficha ya colocada.
            self.main_window.after(FOCUS_DELAY_MS, self.__focus_on_episode)

    def __build_sheet(self, content: ctk.CTkFrame) -> None:
        """«← Volver a …» si se viene de otra ficha, y debajo el póster y la columna de información."""
        if self.__history:
            # Un marco más solo cuando hace falta: cada widget cuenta al abrir la ficha.
            head = ctk.CTkFrame(content, height=1, fg_color=Theme.TRANSPARENT)
            head.grid(row=0, column=0, sticky="ew", padx=Metrics.CONTENT_PAD_X)
            head.grid_columnconfigure(0, weight=1)
            self.__build_back_button(head)
            sheet = ctk.CTkFrame(head, fg_color=Theme.TRANSPARENT)
            sheet.grid(row=1, column=0, sticky="ew", pady=(BACK_GAP, 0))
        else:
            sheet = ctk.CTkFrame(content, fg_color=Theme.TRANSPARENT)
            sheet.grid(row=0, column=0, sticky="ew", padx=Metrics.CONTENT_PAD_X, pady=(SHEET_PAD_TOP, 0))
        sheet.grid_columnconfigure(1, weight=1)
        # El póster fija el alto del bloque, para que los botones de estado queden
        # alineados con su borde inferior.
        sheet.grid_rowconfigure(0, minsize=Metrics.SHEET_POSTER[1])

        self.__build_poster(sheet)

        info = ctk.CTkFrame(sheet, fg_color=Theme.TRANSPARENT)
        info.grid(row=0, column=1, sticky="nsew", padx=(SHEET_GAP, 0))
        info.grid_columnconfigure(0, weight=1)
        # La fila vacía con peso es la que empuja los botones de estado abajo. Una
        # fila con peso recibe el espacio sobrante aunque no tenga ningún hijo.
        info.grid_rowconfigure(6, weight=1)
        self.__info_column = info

        self.__build_provider_block(info)
        self.__build_title(info)
        self.__build_season_links(info)
        self.__build_seen_bar(info)
        self.__build_status_buttons(info)

        # El ancho de esta columna cambia al plegar la barra lateral, y de él
        # dependen el envuelto de la sinopsis y el de las fichas de género.
        info.bind("<Configure>", self.__on_info_configure)

    def __build_poster(self, sheet: ctk.CTkFrame) -> None:
        """El póster a 248 x 372, con las esquinas redondeadas.

        Si todavía no está en disco se pinta el cuadro gris y se descarga en un
        hilo. La identidad usada es la de persistencia: el fichero se llama como
        la fila guardada, no como el slug que sirvió esta ficha.

        :param sheet: Bloque de la ficha donde va el póster.
        """
        cached_path = find_cached_poster_path(self.persistence_anime_id)
        poster_label = ctk.CTkLabel(sheet, text="", image=load_rounded_image(
            cached_path, Metrics.SHEET_POSTER, Metrics.RADIUS_SHEET_POSTER))
        poster_label.grid(row=0, column=0, sticky="nw")
        if cached_path is not None:
            return

        def _show(poster: Image.Image):
            if poster_label.winfo_exists():
                poster_label.configure(image=round_image(poster, Metrics.SHEET_POSTER,
                                                         Metrics.RADIUS_SHEET_POSTER))

        def _download():
            poster = download_poster(self.persistence_poster_url)
            if poster is not None and self.main_window.winfo_exists():
                self.main_window.after(0, _show, poster)

        threading.Thread(target=_download, daemon=True).start()

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
            text=(wrap_synopsis(self.anime_info.synopsis)
                  or "Este proveedor no ha dado sinopsis de este anime."),
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

        Los tres usan todo el ancho de la columna. Envolver es cosa de
        wraplength, y para que sirva de algo el texto no puede traer saltos
        propios: de eso se encarga wrap_synopsis() al construir la etiqueta.
        """
        self.__laid_out_width = available
        if self.__title_label is not None:
            self.__title_label.configure(wraplength=available)
        if self.__synopsis_label is not None:
            self.__synopsis_label.configure(wraplength=available)
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
            # El borde lo pinta un CTkFrame y el texto va encima: CTkLabel no tiene
            # border_width. El relleno es BG y no transparent porque un CTkFrame
            # transparente no dibuja su rectángulo y se pierde también el borde.
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
                # Más baja que la ficha a propósito: un CTkLabel transparente pinta
                # el fondo del padre, y a su alto por defecto borraría los tramos
                # rectos del borde.
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
        """Re-envuelve el texto cuando la columna cambia de ancho de verdad (p.ej. al plegar la sidebar)."""
        if abs(event.width - self.__laid_out_width) <= RELAYOUT_THRESHOLD:
            return
        self.__relayout_text(event.width)

    # ------------------------------------------------------------------
    # Barra de vistos
    # ------------------------------------------------------------------
    def __build_seen_bar(self, info: ctk.CTkFrame) -> None:
        """«N de M vistos», calculado sin tocar la persistencia."""
        self.__seen_frame = ctk.CTkFrame(info, height=1, fg_color=Theme.TRANSPARENT)
        self.__seen_frame.grid(row=5, column=0, sticky="w", pady=(INFO_GAPS[4], 0))
        self.__refresh_seen_bar()

    def __refresh_seen_bar(self) -> None:
        """Repinta la barra de la ficha, y la de la columna del reproductor si está abierto."""
        self.__paint_seen_bar(self.__seen_frame, SEEN_W)
        self.__paint_seen_bar(self.__player_seen_frame, Metrics.PLAYER_INFO_W)

    def __paint_seen_bar(self, frame: Optional[ctk.CTkFrame], block_width: int) -> None:
        """Pinta «N de M vistos» con lo que hay marcado ahora mismo.

        :param frame: Hueco donde va la barra; sin efecto si no existe.
        :param block_width: Ancho del bloque entero, barra y leyenda.
        """
        if frame is None or not frame.winfo_exists():
            return
        for widget in frame.winfo_children():
            widget.destroy()

        total = len(self.anime_info.episodes)
        if not total:
            return
        watched = sum(1 for episode in self.anime_info.episodes
                      if self.watched_status.get(episode.id, False))

        caption_text = f"{watched} de {total} vistos"
        caption_font = Theme.font(*Theme.T_SUB)
        # El ancho de la barra se calcula, no se estira: el texto se queda con lo que necesita.
        bar_width = max(120, block_width - caption_font.measure(caption_text) - SEEN_GAP)

        progress = ctk.CTkProgressBar(
            frame,
            width=bar_width,
            height=Metrics.PROGRESS_H,
            corner_radius=Metrics.PROGRESS_RADIUS,
            fg_color=Theme.LINE,
            progress_color=Theme.ACCENT
        )
        progress.set(watched / total)
        progress.grid(row=0, column=0, sticky="w")

        caption = ctk.CTkLabel(
            frame,
            text=caption_text,
            font=caption_font,
            text_color=Theme.TXT_3,
            anchor="w"
        )
        caption.grid(row=0, column=1, sticky="w", padx=(SEEN_GAP, 0))
        frame.configure(height=SEEN_H)

    # ------------------------------------------------------------------
    # Proveedor de la ficha
    # ------------------------------------------------------------------
    def __build_provider_block(self, info: ctk.CTkFrame) -> None:
        """Indica quién sirvió realmente esta ficha, quién guarda la fila, y ofrece unificarlas si difieren.

        Hace visible el fallback silencioso: puedes tener un proveedor
        seleccionado y estar viendo datos de otro porque el primero falló.
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
        """A qué proveedor se ofrece pasar esta fila, o None si no hay nada que hacer.

        Dos orígenes: quien está sirviendo la ficha, si no es el de la fila
        (migrar no cuesta ni una petición); o si no, el proveedor seleccionado
        en la sidebar cuando difiere del de la fila (hay que localizar el
        anime allí antes de migrar, porque el slug es distinto en cada sitio).

        :return: Proveedor destino, o None si la fila ya coincide con ambos.
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
    # Botones de estado — todos usan __persistence_anime_info() y
    # persistence_anime_id, nunca self.anime_info: si no, cambiar de proveedor y
    # pulsar un botón crearía una fila nueva en ANIMES para el mismo anime.
    # ------------------------------------------------------------------
    def __build_status_buttons(self, info: ctk.CTkFrame) -> None:
        """Los cuatro botones, en una fila que reparte el ancho a partes iguales."""
        actions_frame = ctk.CTkFrame(info, height=1, fg_color=Theme.TRANSPARENT)
        actions_frame.grid(row=7, column=0, sticky="ew", pady=(INFO_GAPS[5], 0))
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
        Apagado: fondo de tarjeta, borde y texto secundario.
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
        """Alterna el estado pulsado, llamando a add_to_* o remove_from_* según cómo esté la fila."""
        actions = STATUS_ACTIONS[status]
        getattr(self, actions[1] if self.__status_state[status] else actions[0])()

    def __after_status_change(self) -> None:
        """Repinta los botones, pone al día los pósters en disco y refresca los contadores de la sidebar."""
        sync_saved_posters_async(self.main_window.animes_persistence, self.__persistence_anime_info())
        self.__refresh_status_buttons()
        self.__refresh_hub_lists()

    def __refresh_hub_lists(self) -> None:
        """Relee de la BD las listas cacheadas del hub y repinta los contadores de la sidebar."""
        animes_persistence = self.main_window.animes_persistence
        self.main_window.favourite_animes = animes_persistence.get_favourite_animes()
        self.main_window.watching_animes = animes_persistence.get_watching_animes()
        self.main_window.pending_animes = animes_persistence.get_pending_animes()
        self.main_window.finished_animes = animes_persistence.get_finished_animes()
        self.main_window.refresh_sidebar_counts()

    def __set_exclusive_status(self, status: Optional[AnimeStatus]) -> None:
        """Enciende uno de los tres estados excluyentes y apaga los otros dos. FAVOURITE no entra aquí."""
        for candidate in EXCLUSIVE_STATUSES:
            self.__status_state[candidate] = (candidate == status)

    def __confirm_save(self, status: AnimeStatus) -> bool:
        """Avisa antes de crear una fila nueva de un anime que ya está guardado con otro slug.

        La comprobación por anime_id no basta: el mismo anime tiene un slug
        distinto en cada sitio. Se consulta la BD en vez de __is_saved porque el
        usuario puede haber guardado el anime pulsando otro estado en esta misma
        pantalla.

        :param status: Sección a la que se está añadiendo, para nombrarla en el aviso.
        :return: True si se puede guardar (no hay duplicado, o el usuario lo acepta).
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
        # Dónde está el duplicado sale de sus propios flags, no de la sección que se
        # acaba de pulsar: puede estar en otra, o en ninguna.
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
        print(f"{self.anime_info.title} añadido a favoritos.")
        self.__status_state[AnimeStatus.FAVOURITE] = True
        self.__after_status_change()

    def remove_from_favorites(self):
        self.main_window.animes_persistence.update_anime_to_not_favourite(self.persistence_anime_id)
        print(f"{self.anime_info.title} eliminado de favoritos.")
        self.__status_state[AnimeStatus.FAVOURITE] = False
        self.__after_status_change()

    def add_to_finished(self):
        if not self.__confirm_save(AnimeStatus.FINISHED):
            return
        anime_info = self.__persistence_anime_info()
        self.main_window.animes_persistence.update_anime_to_finished(anime_info)
        print(f"{self.anime_info.title} añadido a finalizados.")
        self.__set_exclusive_status(AnimeStatus.FINISHED)
        self.__after_status_change()

    def remove_from_finished(self):
        self.main_window.animes_persistence.update_anime_to_not_finished(self.persistence_anime_id)
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
        print(f"{self.anime_info.title} añadido a viendo.")
        self.__set_exclusive_status(AnimeStatus.WATCHING)
        self.__after_status_change()

    def remove_from_watching(self):
        self.main_window.animes_persistence.update_anime_to_not_watching(self.persistence_anime_id)
        print(f"{self.anime_info.title} eliminado de viendo.")
        self.__status_state[AnimeStatus.WATCHING] = False
        self.__after_status_change()

    def add_to_pending(self):
        if not self.__confirm_save(AnimeStatus.PENDING):
            return
        anime_info = self.__persistence_anime_info()
        self.main_window.animes_persistence.update_anime_to_pending(anime_info)
        print(f"{self.anime_info.title} añadido a pendientes.")
        self.__set_exclusive_status(AnimeStatus.PENDING)
        self.__after_status_change()

    def remove_from_pending(self):
        self.main_window.animes_persistence.update_anime_to_not_pending(self.persistence_anime_id)
        print(f"{self.anime_info.title} eliminado de pendientes.")
        self.__status_state[AnimeStatus.PENDING] = False
        self.__after_status_change()

    # ------------------------------------------------------------------
    # Navegación entre fichas
    # ------------------------------------------------------------------
    def __build_back_button(self, head: ctk.CTkFrame) -> None:
        """«← Volver a <título>» de la ficha de la que se viene."""
        font = Theme.font(Theme.T_UI[0], True)
        title = Theme.ellipsize(self.__history[-1].anime_info.title or "", font, BACK_TITLE_W, 1)
        back_button = ctk.CTkButton(
            head,
            text=f"← Volver a {title}",
            width=1,
            height=26,
            corner_radius=Metrics.RADIUS_CONTROL,
            font=font,
            fg_color=Theme.TRANSPARENT,
            hover_color=Theme.ACCENT_SOFT,
            text_color=Theme.ACCENT,
            command=self.__go_back
        )
        back_button.grid(row=0, column=0, sticky="w", pady=(BACK_PAD_TOP, 0))

    def __go_back(self) -> None:
        """Vuelve a la ficha anterior tal como estaba, en Episodios y sin salir a la red."""
        if not self.__history:
            return
        visit, rest = self.__history[-1], self.__history[:-1]
        # after() y no una llamada directa: la ficha nueva destruye el botón cuyo clic se está atendiendo.
        self.main_window.after(0, lambda: AnimeWindowViewer(
            self.main_window, visit.anime_info, visit.provider_id, anime_record=visit.anime_record,
            history=rest).display_anime_info())

    def __is_on_screen(self) -> bool:
        """Si esta ficha sigue en pantalla: el usuario puede haberse ido a otra vista o a otra ficha."""
        return self.__tabs is not None and self.__tabs.winfo_exists()

    def __open_related(self, anime_id: Union[str, int], title: str, focus_episode: Optional[int] = None,
                       force_ascending: bool = False) -> None:
        """Abre la ficha de un relacionado y deja esta en el historial.

        Si ya está en la biblioteca, por slug o por título, se abre su fila como
        desde «Viendo»: sin ella, marcar un estado crearía otra fila del mismo anime.
        Si no, se pide en un hilo al proveedor de esta ficha, que es de quien es el slug.

        :param anime_id: Slug del relacionado en el proveedor de esta ficha.
        :param title: Su título, para buscarlo en la biblioteca.
        :param focus_episode: Episodio por el que abrirla, ya desplegado.
        :param force_ascending: Fuerza el orden ascendente de sus episodios.
        """
        history = self.__history + [SheetVisit(self.anime_info, self.provider_id, self.__anime_record)]
        animes_persistence = self.main_window.animes_persistence
        anime_record = animes_persistence.get_anime_by_anime_id(str(anime_id))
        if anime_record is None:
            anime_record = find_saved_duplicate(animes_persistence.get_all_animes(), title,
                                                exclude_anime_id=self.persistence_anime_id)
        if anime_record is not None:
            # after() porque la ficha nueva destruye el widget cuyo clic se está atendiendo.
            self.main_window.after(0, lambda: open_saved_anime(self.main_window, anime_record.anime_id,
                                                               focus_episode=focus_episode,
                                                               force_ascending=force_ascending,
                                                               history=history))
            return

        self.__open_request_seq += 1
        request = self.__open_request_seq
        provider_id = self.provider_id
        self.main_window.configure(cursor="watch")

        def _show(anime_info: Optional[AnimeInfo], served_by: Optional[AnimeProviderId]):
            if not self.main_window.winfo_exists():
                return
            self.main_window.configure(cursor="")
            if request != self.__open_request_seq or not self.__is_on_screen():
                return
            if anime_info is None:
                show_anime_info_error(anime_id)
                return
            AnimeWindowViewer(self.main_window, anime_info, served_by, focus_episode=focus_episode,
                              force_ascending=force_ascending, history=history).display_anime_info()

        def _load():
            # strict=True: el slug es de este proveedor; en otro podría ser otro anime.
            anime_info, served_by = self.anime_provider_mgr.get_anime_info_with_provider(
                anime_id, provider_id=provider_id, strict=True)
            try:
                self.main_window.after(0, _show, anime_info, served_by)
            except RuntimeError:
                pass

        threading.Thread(target=_load, daemon=True).start()

    # ------------------------------------------------------------------
    # Temporadas y relacionados
    # ------------------------------------------------------------------
    def __library_records(self) -> List[AnimeRecord]:
        """Filas con algún estado, de las listas del hub: bastan para los sellos y no leen la BD."""
        seen, records = set(), []
        for anime_record in (self.main_window.favourite_animes + self.main_window.watching_animes
                             + self.main_window.pending_animes + self.main_window.finished_animes):
            if anime_record.anime_id not in seen:
                seen.add(anime_record.anime_id)
                records.append(anime_record)
        return records

    def __related_status(self, anime_id: Union[str, int], title: str,
                         records: List[AnimeRecord]) -> Optional[AnimeStatus]:
        """Estado en la biblioteca de un relacionado, buscado por slug y luego por título."""
        anime_record = next((record for record in records if str(record.anime_id) == str(anime_id)), None)
        if anime_record is None:
            anime_record = find_saved_duplicate(records, title, exclude_anime_id=self.persistence_anime_id)
        return library_status(anime_record)

    def __own_status(self) -> Optional[AnimeStatus]:
        """Estado de este anime con lo que dicen ahora sus botones, con la regla de ``library_status()``."""
        for status in EXCLUSIVE_STATUSES:
            if self.__status_state[status]:
                return status
        return AnimeStatus.FAVOURITE if self.__status_state[AnimeStatus.FAVOURITE] else None

    def __build_season_links(self, info: ctk.CTkFrame) -> None:
        """«◀ Temporada anterior» y «Temporada siguiente ▶», con lo que ya trae la ficha. Sin ninguna, nada."""
        related = self.anime_info.related or []
        prequel = closest_related(related, AnimeRelationType.PREQUEL)
        sequel = closest_related(related, AnimeRelationType.SEQUEL)
        if prequel is None and sequel is None:
            return
        links = ctk.CTkFrame(info, height=1, fg_color=Theme.TRANSPARENT)
        links.grid(row=4, column=0, sticky="ew", pady=(INFO_GAPS[3], 0))
        links.grid_columnconfigure(1, weight=1)
        records = self.__library_records()
        for column, related_anime, forward in ((0, prequel, False), (2, sequel, True)):
            if related_anime is None:
                continue
            link = SeasonLink(links, related_anime.title, forward,
                              self.__related_status(related_anime.id, related_anime.title, records),
                              on_click=lambda chosen=related_anime: self.__open_related(chosen.id, chosen.title))
            link.grid(row=0, column=column, sticky="e" if forward else "w")

    def __build_relations_tab(self, body: ctk.CTkFrame, _tools: ctk.CTkFrame) -> None:
        """Línea principal en carrusel y el resto de relacionados agrupados por formato.

        Es aquí, al abrir la pestaña, y no al abrir la ficha, donde se pide a la
        red: el recorrido de la franquicia, el formato que falte y los pósters.
        """
        related = self.anime_info.related or []
        prequel = closest_related(related, AnimeRelationType.PREQUEL)
        sequel = closest_related(related, AnimeRelationType.SEQUEL)
        line_ids = {str(item.id) for item in (prequel, sequel) if item is not None}
        self.__others = [item for item in related if str(item.id) not in line_ids]
        service = self.main_window.franchise_service
        can_ask = self.provider_id is not None

        row = 0
        if line_ids:
            self.__carousel = SeasonCarousel(body, on_open=self.__open_line_entry)
            self.__carousel.grid(row=0, column=0, sticky="ew")
            self.__show_known_line(prequel, sequel, walking=can_ask)
            row = 1
        if self.__others:
            self.__others_frame = ctk.CTkFrame(body, height=1, fg_color=Theme.TRANSPARENT)
            self.__others_frame.grid(row=row, column=0, sticky="ew", pady=(RELATIONS_BLOCK_GAP if row else 0, 0))
            self.__others_frame.grid_columnconfigure(0, weight=1)
            self.__format_hints = {str(item.id): self.__instant_format_hint(item) for item in self.__others}
            self.__formats_pending = can_ask
            self.__paint_others()
            self.__load_posters([(str(item.id), item.poster, str(item.id)) for item in self.__others],
                                self.__on_related_poster)
            if can_ask:
                service.request_formats(self.anime_info, self.provider_id, self.__on_format_hints)
        if line_ids and can_ask:
            service.request_franchise(self.anime_info, self.provider_id, self.__on_franchise_line)

    # --- Línea principal --------------------------------------------------
    def __carousel_item(self, anime_id: Union[str, int], title: str, order_text: str, year: Optional[int],
                        anime_format: Optional[AnimeFormat], records: List[AnimeRecord],
                        current: bool = False) -> CarouselItem:
        """Una temporada del carrusel; sin formato del proveedor, el deducido del título."""
        style = "solid"
        if anime_format is None:
            anime_format = deduce_format_from_title(title)
            style = "dashed"
        status = self.__own_status() if current else self.__related_status(anime_id, title, records)
        return CarouselItem(key=str(anime_id), title=title, order_text=order_text, current=current, year=year,
                            format_text=FORMAT_LABELS.get(anime_format), format_style=style, status=status)

    def __current_poster_job(self) -> Tuple[str, Optional[str], Optional[str]]:
        """Póster de esta ficha para el carrusel: el que ya hay en disco con el nombre de la fila."""
        return str(self.anime_info.id), self.persistence_poster_url, self.persistence_anime_id

    def __show_known_line(self, prequel: Optional[RelatedAnime], sequel: Optional[RelatedAnime],
                          walking: bool) -> None:
        """Lo que se sabe sin red: la temporada anterior, esta y la siguiente, y un hueco más allá de cada una."""
        records = self.__library_records()
        items: List[Optional[CarouselItem]] = []
        if prequel is not None:
            items += [None, self.__carousel_item(prequel.id, prequel.title, "Anterior", prequel.year,
                                                 prequel.format, records)]
        current_index = len(items)
        items.append(self.__carousel_item(self.anime_info.id, self.anime_info.title, "Estás aquí", None,
                                          self.anime_info.format, records, current=True))
        if sequel is not None:
            items += [self.__carousel_item(sequel.id, sequel.title, "Siguiente", sequel.year, sequel.format, records),
                      None]
        if not walking:
            items = [item for item in items if item is not None]
            current_index = next(index for index, item in enumerate(items) if item.current)
        self.__line_titles = {item.key: item.title for item in items if item is not None}
        self.__carousel.show(items, current_index,
                             hint="recorriendo la franquicia…" if walking else None,
                             note="Recorriendo la franquicia en segundo plano. La pestaña ya se puede usar."
                             if walking else None,
                             browsable=not walking)
        self.__load_posters([(str(item.id), item.poster, str(item.id)) for item in (prequel, sequel)
                             if item is not None] + [self.__current_poster_job()], self.__on_carousel_poster)

    def __on_franchise_line(self, line: FranchiseLine) -> None:
        """Pinta la línea principal recorrida. Llega en el hilo de Tk, y puede llegar tarde."""
        if self.__carousel is None or not self.__carousel.winfo_exists():
            return
        records = self.__library_records()
        items = []
        for index, entry in enumerate(line.entries):
            current = index == line.current_index
            items.append(self.__carousel_item(entry.id, entry.title, "Estás aquí" if current else f"T{index + 1}",
                                              entry.year, entry.format, records, current=current))
        hint = None
        if line.truncated:
            hint = f"se muestran {len(line.entries)} temporadas; la franquicia sigue"
        elif line.interrupted:
            hint = "no se ha podido recorrer entera"
        self.__line_titles = {item.key: item.title for item in items}
        self.__carousel.show(items, line.current_index, hint=hint)
        jobs = [(entry.id, entry.poster, entry.id) for index, entry in enumerate(line.entries)
                if index != line.current_index]
        self.__load_posters(jobs + [self.__current_poster_job()], self.__on_carousel_poster)

    def __open_line_entry(self, anime_id: str) -> None:
        self.__open_related(anime_id, self.__line_titles.get(anime_id, ""))

    def __on_carousel_poster(self, key: str, image: Image.Image) -> None:
        if self.__carousel is not None and self.__carousel.winfo_exists():
            self.__carousel.set_poster(key, image)

    # --- Resto de relacionados --------------------------------------------
    @staticmethod
    def __instant_format_hint(related: RelatedAnime) -> FormatHint:
        """El formato que se sabe sin red: el del proveedor o, si no, el deducido del título."""
        if related.format is not None:
            return FormatHint(related.format)
        deduced = deduce_format_from_title(related.title)
        return FormatHint(deduced, deduced=True) if deduced is not None else FormatHint(None)

    def __on_format_hints(self, hints: Dict[str, FormatHint]) -> None:
        """Repinta los relacionados con los formatos completos. Llega en el hilo de Tk."""
        if self.__others_frame is None or not self.__others_frame.winfo_exists():
            return
        for related in self.__others:
            hint = hints.get(str(related.id))
            if hint is not None and hint.format is not None:
                self.__format_hints[str(related.id)] = hint
        self.__formats_pending = False
        self.__paint_others()

    def __group_of(self, related: RelatedAnime) -> str:
        """En qué grupo de la pestaña va un relacionado: por formato, y las versiones alternativas aparte."""
        if related.relation == AnimeRelationType.ALTERNATIVE:
            return GROUP_ALTERNATIVES
        hint = self.__format_hints.get(str(related.id))
        anime_format = hint.format if hint is not None else None
        if anime_format == AnimeFormat.MOVIE:
            return GROUP_MOVIES
        if anime_format in (AnimeFormat.SERIES, AnimeFormat.ONA):
            return GROUP_SERIES
        if anime_format in (AnimeFormat.OVA, AnimeFormat.SPECIAL):
            return GROUP_OVAS
        return GROUP_UNKNOWN

    def __paint_others(self) -> None:
        """Pinta los relacionados que no son de la línea principal, por grupos, y la leyenda."""
        frame = self.__others_frame
        for child in frame.winfo_children():
            child.destroy()
        self.__related_cards.clear()

        records = self.__library_records()
        groups: Dict[str, List[RelatedAnime]] = {name: [] for name in RELATION_GROUPS}
        for related in self.__others:
            groups[self.__group_of(related)].append(related)
        width_hint = self.__tabs.winfo_width() if self.__tabs.winfo_width() > 1 else \
            Metrics.WINDOW_W - Metrics.SIDEBAR_W - 2 * Metrics.CONTENT_PAD_X

        row = 0
        for name in RELATION_GROUPS:
            if not groups[name]:
                continue
            ctk.CTkLabel(frame, text=name.upper(), font=Theme.font(*Theme.T_LABEL), text_color=Theme.TXT_3,
                         height=16, anchor="w").grid(row=row, column=0, sticky="w",
                                                     pady=(RELATIONS_GROUP_GAP if row else 0, 10))
            grid = RelatedGrid(frame)
            grid.grid(row=row + 1, column=0, sticky="ew")
            grid.set_cards([self.__related_card(grid, related, records) for related in groups[name]], width_hint)
            row += 2
        self.__paint_relations_legend(frame, row)

    def __related_card(self, parent: RelatedGrid, related: RelatedAnime, records: List[AnimeRecord]) -> RelatedCard:
        """Tarjeta de un relacionado, con su formato, de dónde sale ese formato y su estado."""
        related_id = str(related.id)
        hint = self.__format_hints.get(related_id) or FormatHint(None)
        if hint.format is not None:
            format_text, format_style = FORMAT_LABELS[hint.format], "dashed" if hint.deduced else "solid"
        else:
            format_text, format_style = ("…" if self.__formats_pending else "¿?"), "dotted"
        card = RelatedCard(
            parent,
            related.title,
            RELATION_LABELS.get(related.relation, "Otro"),
            on_click=lambda: self.__open_related(related.id, related.title),
            year=related.year,
            format_text=format_text,
            format_style=format_style,
            source=hint.short_name,
            status=self.__related_status(related.id, related.title, records),
            with_poster=related.poster is not None or find_cached_poster_path(related_id) is not None
        )
        poster = self.__related_posters.get(related_id)
        if poster is not None:
            card.set_poster(poster)
        self.__related_cards[related_id] = card
        return card

    def __paint_relations_legend(self, frame: ctk.CTkFrame, row: int) -> None:
        """Leyenda de los formatos: de qué proveedor salen, cuáles se han deducido y si aún falta alguno."""
        hints = [self.__format_hints.get(str(related.id)) for related in self.__others]
        short_names = sorted({hint.short_name for hint in hints if hint is not None and hint.short_name})
        any_deduced = any(hint is not None and hint.deduced for hint in hints)
        any_missing = any(hint is None or hint.format is None for hint in hints)
        if not (short_names or any_deduced or (any_missing and self.__formats_pending)):
            return
        legend = ctk.CTkFrame(frame, height=1, fg_color=Theme.TRANSPARENT)
        legend.grid(row=row, column=0, sticky="w", pady=(14, 0))
        meta_font = Theme.font(*Theme.T_META)
        parts: List[ctk.CTkBaseClass] = []
        if any_missing and self.__formats_pending:
            parts.append(ctk.CTkLabel(legend, text="Buscando el formato que falta…", font=meta_font,
                                      text_color=Theme.TXT_3, height=18))
        providers = {self.anime_provider_mgr.get_provider_info(provider_id).short_name: provider_id
                     for provider_id in self.anime_provider_mgr.list_providers()}
        for short_name in short_names:
            parts.append(ctk.CTkLabel(legend, text=short_name, font=Theme.font(10, True), text_color=Theme.ACCENT,
                                      height=18))
            parts.append(ctk.CTkLabel(
                legend, text=f"formato facilitado por "
                             f"{self.anime_provider_mgr.get_provider_name(providers.get(short_name))}",
                font=meta_font, text_color=Theme.TXT_3, height=18))
        if any_deduced:
            parts.append(format_chip(legend, "OVA", "dashed"))
            parts.append(ctk.CTkLabel(legend, text="deducido del título", font=meta_font, text_color=Theme.TXT_3,
                                      height=18))
        for column, part in enumerate(parts):
            part.grid(row=0, column=column, padx=(0 if column == 0 else 6, 0))

    def __on_related_poster(self, key: str, image: Image.Image) -> None:
        self.__related_posters[key] = image
        card = self.__related_cards.get(key)
        if card is not None and card.winfo_exists():
            card.set_poster(image)

    # --- Pósters ----------------------------------------------------------
    def __load_posters(self, jobs: List[Tuple[str, Optional[str], Optional[str]]],
                       deliver: Callable[[str, Image.Image], None]) -> None:
        """Busca en un hilo los pósters, uno detrás de otro, y los entrega en el hilo de Tk.

        :param jobs: (clave con la que se entrega, URL o None, id con el que buscarlo en disco).
        :param deliver: Recibe (clave, imagen); comprueba él si su widget sigue vivo.
        """
        jobs = [job for job in jobs if job[1] or job[2]]
        if not jobs:
            return
        main_window = self.main_window

        def _work():
            for key, url, disk_id in jobs:
                image = _related_poster(url, disk_id)
                if image is None:
                    continue
                try:
                    main_window.after(0, deliver, key, image)
                except RuntimeError:
                    return

        threading.Thread(target=_work, daemon=True).start()

    # ------------------------------------------------------------------
    # Lista de episodios
    # ------------------------------------------------------------------
    def __build_tabs(self, content: ctk.CTkFrame) -> None:
        """Pestañas debajo de la ficha. Solo se construye la de Episodios; las demás, al abrirlas."""
        self.__tabs = TabBar(content)
        self.__tabs.grid(row=1, column=0, sticky="ew", padx=Metrics.CONTENT_PAD_X,
                         pady=(EPISODES_PAD_TOP, SHEET_PAD_BOTTOM))
        self.__tabs.add_tab(TAB_EPISODES, "Episodios", self.__build_episodes_tab,
                            count=len(self.anime_info.episodes))
        if self.anime_info.related:
            self.__tabs.add_tab(TAB_RELATIONS, "Temporadas y relacionados", self.__build_relations_tab)

    def __build_episodes_tab(self, body: ctk.CTkFrame, tools: ctk.CTkFrame) -> None:
        """Orden y buscador en la zona de herramientas, y las filas de episodio en el cuerpo."""
        self.__sort_button = ctk.CTkButton(
            tools,
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
        self.__sort_button.grid(row=0, column=0, sticky="e")

        self.search_entry = ctk.CTkEntry(
            tools,
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
        self.search_entry.grid(row=0, column=1, sticky="e", padx=(9, 0))
        self.search_entry.bind("<Return>", self.__search_episodes)

        self.__episodes_body = body
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
        self.__servers_requests.clear()
        self.__servers_states.clear()

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
            row.set_current(self.__is_playing(episode_info.id))
            self.__episode_rows[episode_info.id] = row

        if showing_all and len(self.anime_info.episodes) > EPISODES_SHOWN:
            # Se anuncia el corte para que el buscador de al lado sea la salida evidente.
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
        """La línea de apoyo de una fila. Un episodio visto no dice nada: ya lo cuenta el interruptor."""
        if self.__is_playing(episode_info.id):
            return self.__playing_row_text()
        servers_state = self.__servers_states.get(episode_info.id)
        if servers_state:
            return servers_state
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
            row.set_current(self.__is_playing(episode_id))

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

    def __focus_on_episode(self) -> None:
        """Deja la ficha abierta por el episodio con el que se entró.

        Si el episodio queda fuera del corte de EPISODES_SHOWN, se muestra él
        solo con navegación anterior/siguiente; después se despliegan sus
        servidores y se desplaza la ventana hasta la fila. Se llama una vez y
        consume ``__focus_episode``.
        """
        episode_id, self.__focus_episode = self.__focus_episode, None
        # La ficha puede haberse ido en estos 50 ms: cambiar de pestaña destruye
        # el cuerpo de la lista y `after` no cancela nada por su cuenta.
        if self.__episodes_body is None or not self.__episodes_body.winfo_exists():
            return

        episode_info = next((episode for episode in self.anime_info.episodes
                             if episode.id == episode_id), None)
        if episode_info is None:
            provider_name = self.anime_provider_mgr.get_provider_name(self.provider_id)
            print(f"[{provider_name}] no lista el episodio {episode_id} de "
                  f"{self.anime_info.id}; la ficha se abre sin desplegar nada")
            return

        self.__ensure_episode_row(episode_info)
        if episode_info.id not in self.__servers_frames:
            self.__toggle_servers_frame(episode_info, scroll_into_view=True)
        self.__scroll_to_episode(episode_info.id)

    def __ensure_episode_row(self, episode_info: EpisodeInfo) -> None:
        """Si el episodio no tiene fila en la lista, la deja con él solo y la navegación anterior/siguiente.

        Es lo que pasa con los episodios fuera del corte de EPISODES_SHOWN, como
        al buscarlos en «Ir al episodio…».
        """
        if episode_info.id in self.__episode_rows:
            return
        self.__display_episodes([episode_info])
        self.__display_previous_and_next_episodes(episode_info)
        if self.search_entry is not None and self.search_entry.winfo_exists():
            self.search_entry.delete(0, "end")
            self.search_entry.insert(0, str(episode_info.id))

    def __scroll_to_episode(self, episode_id: Any) -> None:
        """Desplaza el content_frame solo si la fila y sus servidores no caben ya en lo que se ve.

        Desplazar siempre sería igual de malo que no hacerlo nunca: con el
        primer episodio la fila ya es visible, y subir la ventana solo taparía
        el póster y los botones de estado sin necesidad.
        """
        row = self.__episode_rows.get(episode_id)
        content = self.main_window.content_frame
        canvas = getattr(content, "_parent_canvas", None)
        if canvas is None or row is None or not row.winfo_exists():
            return
        # Con otra pestaña delante la fila no está colocada y medirla daría cualquier cosa.
        if self.__tabs is None or self.__tabs.selected != TAB_EPISODES:
            return

        # La fila acaba de nacer y los servidores de debajo también: sin esto,
        # `winfo_rooty()` devuelve la posición que tenían antes de colocarse.
        content.update_idletasks()
        total_height = content.winfo_height()
        if total_height <= 0:
            return

        block_height = row.winfo_height()
        servers_frame = self.__servers_frames.get(episode_id)
        if servers_frame is not None and servers_frame.winfo_exists():
            block_height += servers_frame.winfo_height()
        visible_top = row.winfo_rooty() - canvas.winfo_rooty()
        if visible_top >= 0 and visible_top + block_height <= canvas.winfo_height():
            return

        offset = row.winfo_rooty() - content.winfo_rooty() - FOCUS_SCROLL_MARGIN
        canvas.yview_moveto(min(max(offset, 0) / total_height, 1.0))

    def __toggle_sort_order(self):
        self.sort_descending = not self.sort_descending
        self.anime_info.episodes.sort(
            key=lambda episode: episode.id,
            reverse=self.sort_descending
        )
        self.__sort_button.configure(text=self.__sort_text())
        self.__display_episodes()

    def __search_episodes(self, event=None):
        query = self.search_entry.get().strip()
        if query.isdigit():
            query_id = int(query)
            filtered_episode = next((ep for ep in self.anime_info.episodes if ep.id == query_id), None)
            if filtered_episode is None:
                self.__display_episodes([])
            else:
                self.__display_episodes([filtered_episode])
                self.__display_previous_and_next_episodes(filtered_episode)
        else:
            self.__display_episodes()

    def __previous_episode(self, episode_info: EpisodeInfo):
        current_index = next(i for i, ep in enumerate(self.anime_info.episodes) if ep.id == episode_info.id)
        previous_index = current_index + 1 if self.sort_descending else current_index - 1
        if 0 <= previous_index < len(self.anime_info.episodes):
            previous_episode = self.anime_info.episodes[previous_index]
            self.__display_episodes([previous_episode])
            self.__display_previous_and_next_episodes(previous_episode)

    def __next_episode(self, episode_info: EpisodeInfo):
        current_index = next(i for i, ep in enumerate(self.anime_info.episodes) if ep.id == episode_info.id)
        next_index = current_index - 1 if self.sort_descending else current_index + 1
        if 0 <= next_index < len(self.anime_info.episodes):
            next_episode = self.anime_info.episodes[next_index]
            self.__display_episodes([next_episode])
            self.__display_previous_and_next_episodes(next_episode)

    def __toggle_episode_switch(self, episode_id: int):
        """Marca o desmarca un episodio desde su interruptor.

        :param episode_id: Episodio sobre el que actúa el interruptor.
        """
        self.__set_episode_watched(episode_id, not self.watched_status.get(episode_id, False))

    def __set_episode_watched(self, episode_id: int, marking_as_watched: bool) -> bool:
        """Marca o desmarca un episodio. Marcar es acumulativo; desmarcar, no.

        Marcar el 5 marca del 1 al 5 y conserva los posteriores que ya estuvieran
        vistos; desmarcar el 3 desmarca solo el 3.

        :param episode_id: Episodio que se marca o desmarca.
        :param marking_as_watched: True para marcarlo, False para desmarcarlo.
        :return: Si se guardó en la BD; False si el anime no tiene fila.
        """
        # Índice en orden real ascendente, no en el de la lista de la ficha (que
        # depende del botón de orden): "todos los anteriores" no puede depender
        # de cómo se esté mirando la lista.
        all_episodes_sorted = sorted(self.anime_info.episodes, key=lambda ep: ep.id)
        try:
            ep_index_asc = next(i for i, ep in enumerate(all_episodes_sorted) if ep.id == episode_id)
        except StopIteration:
            print(f"Error: Episodio con ID {episode_id} no encontrado.")
            return False

        # IDs de todos los episodios hasta el marcado (inclusive) en orden real.
        episodes_up_to = {ep.id for ep in all_episodes_sorted[:ep_index_asc + 1]}

        if marking_as_watched:
            for ep_id in episodes_up_to:
                self.watched_status[ep_id] = True
        else:
            self.watched_status[episode_id] = False
        self.__refresh_episode_states()
        self.__refresh_seen_bar()

        bd_watched = self.main_window.animes_persistence.get_watched_episodes(self.persistence_anime_id)

        if marking_as_watched:
            # Todo hasta episode_id se marca visto, salvo lo que el usuario haya
            # desmarcado explícitamente por delante; lo posterior no se toca.
            episodes_after = {ep_id for ep_id in bd_watched if ep_id > episode_id}
            merged = episodes_up_to | episodes_after
        else:
            merged = bd_watched - {episode_id}

        saved = self.main_window.animes_persistence.update_watched_episodes(self.persistence_anime_id, merged)

        # «Retomar donde lo dejaste» de la portada sale de aquí. Se apunta solo al
        # marcar (desmarcar no es «seguir viendo») y solo si el UPDATE encontró la
        # fila, para no guardar en la banda el identificador de un anime que no
        # está en la biblioteca. Usa persistence_anime_id y no anime_info.id: con
        # el desplegable desviado son slugs distintos.
        if saved and marking_as_watched:
            self.main_window.user_persistence.push_last_watched_id(self.persistence_anime_id)
        return saved

    def __toggle_servers_frame(self, episode_info: EpisodeInfo, scroll_into_view: bool = False):
        """Despliega o repliega los servidores de un episodio, bajo su fila.

        Desplegar abre el hueco al momento con «Buscando servidores…» y pide la
        lista en un hilo daemon; plegar es instantáneo y no sale a la red.
        :param episode_info: Episodio de la fila pulsada.
        :param scroll_into_view: Si al llegar los servidores hay que desplazar la
            ficha para que se vean, como al abrirla por un episodio.
        """
        episode_id = episode_info.id
        row = self.__episode_rows.get(episode_id)
        if episode_id in self.__servers_frames:
            self.__servers_frames.pop(episode_id).destroy()
            # Sin su marca, la respuesta que siga en vuelo se descarta al llegar.
            self.__servers_requests.pop(episode_id, None)
            self.__servers_states.pop(episode_id, None)
            if row is not None and row.winfo_exists():
                row.set_expanded(False)
                row.set_state_text(self.__episode_state_text(episode_info,
                                                             self.__next_unwatched_episode_id()))
            return

        request = self.__open_servers_frame(episode_info)
        provider_id = self.provider_id

        def _fetch():
            servers_info = self.__fetch_servers(episode_info, provider_id)
            self.main_window.after(0, self.__show_servers, episode_info, request, servers_info,
                                   scroll_into_view)

        threading.Thread(target=_fetch, daemon=True).start()

    def __open_servers_frame(self, episode_info: EpisodeInfo) -> int:
        """Abre bajo la fila el hueco de servidores con «Buscando servidores…», sin salir a la red.

        :param episode_info: Episodio cuya fila se despliega.
        :return: Número del despliegue, que hay que pasar a ``__show_servers``.
        """
        episode_id = episode_info.id
        row = self.__episode_rows.get(episode_id)
        # La fila impar que hay justo debajo de la del episodio, reservada al
        # construir la lista: `grid_info()` dice en cuál cayó esta.
        grid_row = int(row.grid_info()["row"]) + 1 if row is not None else 1
        servers_frame = ctk.CTkFrame(self.__episodes_body, fg_color=Theme.CARD, corner_radius=8)
        servers_frame.grid(row=grid_row, column=0, sticky="ew", pady=(0, 8))
        servers_frame.grid_columnconfigure(0, weight=1)
        self.__servers_frames[episode_id] = servers_frame
        self.__show_servers_message(servers_frame, "Buscando servidores…")

        # Cada despliegue lleva su número: si el episodio se pliega, se vuelve a
        # desplegar o la lista se repinta antes de que llegue la respuesta, su
        # número deja de coincidir y la respuesta no pinta nada.
        self.__servers_request_seq += 1
        request = self.__servers_request_seq
        self.__servers_requests[episode_id] = request
        self.__servers_states[episode_id] = "Buscando servidores…"
        if row is not None and row.winfo_exists():
            row.set_expanded(True)
            row.set_state_text(self.__episode_state_text(episode_info, None))
        return request

    def __fetch_servers(self, episode_info: EpisodeInfo,
                        provider_id: AnimeProviderId | None) -> Optional[List[ServerInfo]]:
        """Pide al proveedor los servidores de un episodio. Sale a la red: solo desde un hilo daemon.

        strict=True y provider_id explícito: episode_info.anime es el slug del
        proveedor que sirvió esta ficha, así que pedir los servidores a otro
        sitio con ese slug no devolvería nada útil.
        :return: Los servidores, o None si la petición falló.
        """
        try:
            return self.anime_provider_mgr.get_anime_episode_servers(
                episode_info.anime,
                episode_info.id,
                provider_id=provider_id,
                strict=True
            )
        except Exception as exc:
            print(f"Error al pedir los servidores del episodio {episode_info.id} "
                  f"de {episode_info.anime}: {exc}")
            return None

    def __show_servers(self, episode_info: EpisodeInfo, request: int,
                       servers_info: Optional[List[ServerInfo]], scroll_into_view: bool) -> None:
        """Pinta en el hueco del episodio los servidores que acaban de llegar, o por qué no hay.

        :param episode_info: Episodio cuyos servidores se pidieron.
        :param request: Número del despliegue que hizo la petición.
        :param servers_info: Servidores recibidos; vacío o ``None`` si no hay o falló.
        :param scroll_into_view: Si hay que desplazar la ficha hasta el episodio.
        """
        episode_id = episode_info.id
        if self.__servers_requests.get(episode_id) != request:
            return
        del self.__servers_requests[episode_id]
        # La ficha puede haberse ido mientras cargaba: cambiar de pestaña destruye
        # el hueco, y tocarlo reventaría con `invalid command name`.
        servers_frame = self.__servers_frames.get(episode_id)
        if servers_frame is None or not servers_frame.winfo_exists():
            return
        for child in servers_frame.winfo_children():
            child.destroy()

        if servers_info:
            self.__servers_states[episode_id] = "Servidores disponibles"
            server_url_map = self.__server_url_map(servers_info)
            # Los que no se pueden ver aquí llevan ↗ antes de pulsarlos; se sabe sin red.
            labels_by_text = {self.__server_text(label, url): label for label, url in server_url_map.items()}
            server_button = ctk.CTkSegmentedButton(
                servers_frame,
                values=list(labels_by_text.keys()),
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
            server_button.configure(command=lambda selected: self.__play_video(
                episode_info, server_url_map, labels_by_text[selected]))
        else:
            # El gestor no distingue «no hay» de «ha fallado»: los dos llegan vacíos.
            provider_name = self.anime_provider_mgr.get_provider_name(self.provider_id)
            print(f"[{provider_name}] Sin servidores para el episodio "
                  f"{episode_info.id} de {episode_info.anime}")
            self.__servers_states[episode_id] = "Sin servidores"
            self.__show_servers_message(
                servers_frame,
                f"{provider_name} no ha devuelto servidores para este episodio · "
                f"prueba con otro proveedor en el desplegable de la barra lateral"
            )

        row = self.__episode_rows.get(episode_id)
        if row is not None and row.winfo_exists():
            row.set_state_text(self.__episode_state_text(episode_info, None))
        if scroll_into_view:
            self.__scroll_to_episode(episode_id)

    @staticmethod
    def __show_servers_message(servers_frame: ctk.CTkFrame, text: str) -> None:
        """Una línea de texto en el hueco de servidores, a la altura de los botones que sustituye."""
        message = ctk.CTkLabel(
            servers_frame,
            text=text,
            font=Theme.font(*Theme.T_UI),
            text_color=Theme.TXT_3,
            anchor="w",
            justify="left"
        )
        message.grid(row=0, column=0, sticky="w", padx=EPISODE_PAD_X, pady=14)

    @staticmethod
    def __server_url_map(servers_info: List[ServerInfo]) -> Dict[str, str]:
        """Asocia cada servidor a su URL, numerando los nombres repetidos («Desu 2»).

        Un mismo episodio puede ofrecer varios servidores con el mismo nombre; con el
        nombre tal cual como clave, el dict se quedaría solo con el último.
        :param servers_info: Servidores del episodio, en el orden del proveedor.
        :return: Diccionario etiqueta visible → URL, sin etiquetas repetidas.
        """
        server_url_map = {}
        for server in servers_info:
            label, number = server.server, 1
            while label in server_url_map:
                number += 1
                label = f"{server.server} {number}"
            server_url_map[label] = server.url
        return server_url_map

    @staticmethod
    def __server_text(label: str, url: str) -> str:
        """:return: La etiqueta del servidor, con ↗ si se abrirá en el navegador."""
        return label if registry.has_resolver(url) else f"{label} ↗"

    # ------------------------------------------------------------------
    # Reproductor acoplado
    # ------------------------------------------------------------------
    def __is_playing(self, episode_id: Any) -> bool:
        return self.__playing_episode is not None and self.__playing_episode.id == episode_id

    def __playing_row_text(self) -> str:
        """La línea de apoyo de la fila del episodio que está en el reproductor."""
        if self.__playing_status == "browser":
            return "↗ Abierto en el navegador"
        if self.__playing_status == "ended":
            return "Terminado"
        if self.__playing_status == "unavailable":
            return "Sin servidores"
        status = PLAYER_STATUS_LABELS.get(self.__playing_status, "Cargando")
        return f"▮ {status} · {self.__playing_label}" if self.__playing_label else f"▮ {status}"

    def __play_video(self, episode_info: EpisodeInfo, servers: Dict[str, str], label: str) -> None:
        """Reproduce un episodio por un servidor, encima de la ficha; si no se puede, en el navegador.

        Resuelve el medio en un hilo daemon. Mientras tanto el panel enseña «Cargando»,
        y una respuesta que llegue después de pedir otra cosa se descarta.
        :param episode_info: Episodio que se quiere ver.
        :param servers: Servidores del episodio, etiqueta visible → URL de embed.
        :param label: Servidor elegido.
        """
        url = servers.get(label)
        if not url:
            return
        if self.__player is None and not self.__open_player():
            webbrowser.open(url)
            return

        if not self.__is_playing(episode_info.id):
            self.__failed_servers = set()
        self.__playing_episode = episode_info
        self.__playing_servers = dict(servers)
        self.__playing_label = label
        self.__play_request_seq += 1
        request = self.__play_request_seq

        self.__player.stop_media()
        self.__set_playing_status("loading")
        provider_name = self.anime_provider_mgr.get_provider_name(self.provider_id)
        self.__player.show_loading(f"Cargando el episodio {episode_info.id}", f"{label} · {provider_name}")
        self.main_window.after(FOCUS_DELAY_MS, self.__scroll_to_episode, episode_info.id)

        def _resolve():
            try:
                source = registry.resolve(url)
            except Exception as exc:
                print(f"Error al resolver {url}: {exc}")
                source = None
            self.main_window.after(0, self.__on_media_resolved, request, source)

        threading.Thread(target=_resolve, daemon=True).start()

    def __on_media_resolved(self, request: int, source: Optional[MediaSource]) -> None:
        """Carga el medio resuelto, o cae al navegador si no hubo forma."""
        if request != self.__play_request_seq or self.__player is None:
            return
        if source is None:
            self.__fall_back_to_browser()
            return
        self.__player.play(source)

    def __play_adjacent(self, step: int) -> None:
        """Pasa al episodio anterior (``-1``) o al siguiente (``1``) del que está en el reproductor."""
        if self.__playing_episode is None:
            return
        target = self.__adjacent_episode(self.__playing_episode.id, step)
        if target is not None:
            self.__play_episode(target)

    def __play_episode(self, episode_info: EpisodeInfo) -> None:
        """Cambia el reproductor a otro episodio, por el mismo servidor si lo tiene.

        Pide los servidores del episodio y resuelve el medio en un hilo daemon: la
        misma respuesta rellena el hueco de su fila en la lista y elige servidor.
        Si no se resuelve ninguno, cae al navegador.
        :param episode_info: Episodio que se quiere ver.
        """
        if self.__player is None:
            return
        previous_episode, preferred_label = self.__playing_episode, self.__playing_label
        self.__failed_servers = set()
        self.__playing_episode = episode_info
        self.__playing_servers = {}
        self.__play_request_seq += 1
        request = self.__play_request_seq

        self.__player.stop_media()
        self.__set_playing_status("loading")
        provider_name = self.anime_provider_mgr.get_provider_name(self.provider_id)
        self.__player.show_loading(f"Cargando el episodio {episode_info.id}",
                                   f"{preferred_label} · {provider_name}" if preferred_label else provider_name)

        # La lista de debajo acompaña al reproductor: se pliega el episodio que
        # sonaba y se despliega el nuevo, que es el que se verá al volver.
        if (previous_episode is not None and previous_episode.id != episode_info.id
                and previous_episode.id in self.__servers_frames):
            self.__toggle_servers_frame(previous_episode)
        self.__ensure_episode_row(episode_info)
        servers_request = (None if episode_info.id in self.__servers_frames
                           else self.__open_servers_frame(episode_info))
        self.__refresh_episode_states()
        self.main_window.after(FOCUS_DELAY_MS, self.__scroll_to_episode, episode_info.id)

        provider_id = self.provider_id

        def _load():
            servers_info = self.__fetch_servers(episode_info, provider_id)
            if servers_request is not None:
                self.main_window.after(0, self.__show_servers, episode_info, servers_request, servers_info, True)
            servers = self.__server_url_map(servers_info or [])
            # El mismo servidor primero, y después los que se pueden ver aquí, en el
            # orden del proveedor. Una petición por servidor, sin reintentos.
            ordered = ([preferred_label] if preferred_label in servers else []) + \
                      [label for label in servers if label != preferred_label]
            candidates = [label for label in ordered if registry.has_resolver(servers[label])]
            chosen, source = None, None
            for label in candidates:
                try:
                    source = registry.resolve(servers[label])
                except Exception as exc:
                    print(f"Error al resolver {servers[label]}: {exc}")
                    source = None
                if source is not None:
                    chosen = label
                    break
            self.main_window.after(0, self.__on_episode_resolved, request, servers, ordered, candidates,
                                   chosen, source)

        threading.Thread(target=_load, daemon=True).start()

    def __on_episode_resolved(self, request: int, servers: Dict[str, str], ordered: List[str],
                              tried: List[str], chosen: Optional[str], source: Optional[MediaSource]) -> None:
        """Carga el episodio al que se ha navegado, o dice por qué no se puede ver aquí.

        :param request: Número de la petición; si ya no es la última, no se hace nada.
        :param servers: Servidores del episodio, etiqueta visible → URL.
        :param ordered: Etiquetas en orden de preferencia.
        :param tried: Las que se intentaron resolver.
        :param chosen: La que se resolvió, o None.
        :param source: El medio resuelto, o None.
        """
        if request != self.__play_request_seq or self.__player is None or self.__playing_episode is None:
            return
        self.__playing_servers = servers
        if not servers:
            self.__playing_label = None
            self.__player.stop_media()
            self.__set_playing_status("unavailable")
            provider_name = self.anime_provider_mgr.get_provider_name(self.provider_id)
            self.__player.show_message(
                f"No hay servidores para el episodio {self.__playing_episode.id}",
                f"{provider_name} no ha devuelto servidores para este episodio. Prueba con otro "
                f"proveedor en el desplegable de la barra lateral.",
                [("Volver a la ficha", self.main_window.close_player, False)],
                icon="external"
            )
            return
        if source is None:
            # Se abre en el navegador el que se habría preferido; los ya intentados
            # no se ofrecen como alternativa.
            self.__playing_label = ordered[0]
            self.__failed_servers.update(tried)
            self.__fall_back_to_browser()
            return
        self.__playing_label = chosen
        self.__refresh_player_info()
        self.__player.play(source)

    def __adjacent_episode(self, episode_id: Any, step: int) -> Optional[EpisodeInfo]:
        """El episodio de al lado en orden real de número, entre todos los que lista el proveedor.

        No se limita al corte de EPISODES_SHOWN: el que queda fuera se pinta solo en la lista.
        :param episode_id: Episodio de referencia.
        :param step: ``1`` para el siguiente, ``-1`` para el anterior.
        :return: El episodio, o None si no hay ninguno en esa dirección.
        """
        if step > 0:
            later = [episode for episode in self.anime_info.episodes if episode.id > episode_id]
            return min(later, key=lambda episode: episode.id) if later else None
        earlier = [episode for episode in self.anime_info.episodes if episode.id < episode_id]
        return max(earlier, key=lambda episode: episode.id) if earlier else None

    def __on_player_started(self) -> None:
        self.__set_playing_status("playing")

    def __on_player_ended(self) -> None:
        """Fin de episodio: lo marca como visto si el anime está guardado y saca el aviso con las dos salidas."""
        episode_info = self.__playing_episode
        if self.__player is None or episode_info is None:
            return
        marked = self.__mark_finished_episode(episode_info.id)
        self.__set_playing_status("ended")

        provider_name = self.anime_provider_mgr.get_provider_name(self.provider_id)
        subtitle = " · ".join(part for part in (self.anime_info.title, provider_name, self.__playing_label) if part)
        check_note = None
        if marked:
            total = len(self.anime_info.episodes)
            watched = sum(1 for episode in self.anime_info.episodes if self.watched_status.get(episode.id, False))
            check_note = f"Marcado como visto · {watched} de {total}"
        buttons = [("Volver a la ficha", self.main_window.close_player, False)]
        body = ""
        following = self.__adjacent_episode(episode_info.id, 1)
        sequel = closest_related(self.anime_info.related or [], AnimeRelationType.SEQUEL) if following is None else None
        if following is not None:
            buttons.append((f"Ver el episodio {following.id}", lambda: self.__play_episode(following), True))
        elif sequel is not None:
            # Último episodio de una temporada con secuela: se ofrece empezarla por el 1,
            # por el mismo camino que abrir un relacionado.
            body = f"Era el último episodio. Sigue con «{sequel.title}»."
            title_font = Theme.font(Theme.T_UI[0], True)
            buttons.append((f"Empezar {Theme.ellipsize(sequel.title, title_font, END_CARD_TITLE_W, 1)}",
                            lambda: self.__open_related(sequel.id, sequel.title, focus_episode=1,
                                                        force_ascending=True), True))
        self.__player.show_message(f"Has terminado el episodio {episode_info.id}", body, buttons,
                                   subtitle=subtitle, check_note=check_note, closable=True)

    def __mark_finished_episode(self, episode_id: Any) -> bool:
        """Marca como visto el episodio que acaba de terminar, con la semántica acumulativa de siempre.

        Solo si el anime ya tiene fila en la biblioteca: terminar un episodio de
        algo que no es tuyo no lo guarda. Usa la identidad de persistencia.
        :param episode_id: Episodio que ha llegado al final.
        :return: Si el episodio queda marcado en la BD.
        """
        persistence = self.main_window.animes_persistence
        if persistence.get_anime_by_anime_id(self.persistence_anime_id) is None:
            return False
        # Lo que manda es la fila, no la memoria: si ya estaba visto, no se reescribe.
        if episode_id in persistence.get_watched_episodes(self.persistence_anime_id):
            return True
        if not self.__set_episode_watched(episode_id, True):
            return False
        self.__refresh_hub_lists()
        return True

    def __on_player_error(self, reason: str) -> None:
        print(f"[reproductor] {self.__playing_label}: {reason}; se abre en el navegador")
        self.__fall_back_to_browser()

    def __fall_back_to_browser(self) -> None:
        """Abre el servidor en el navegador y lo dice en el recuadro del vídeo, con otro servidor que sí se ve aquí."""
        episode_info, label = self.__playing_episode, self.__playing_label
        if self.__player is None or episode_info is None or label is None:
            return
        url = self.__playing_servers.get(label, "")
        had_resolver = registry.has_resolver(url)
        self.__failed_servers.add(label)
        webbrowser.open(url)
        self.__player.stop_media()
        self.__set_playing_status("browser")

        servers = self.__playing_servers
        alternatives = [other for other, other_url in servers.items()
                        if other not in self.__failed_servers and registry.has_resolver(other_url)]
        body = (f"Este servidor no se puede ver dentro de la aplicación, así que el episodio "
                f"{episode_info.id} se ha abierto en una pestaña nueva."
                if not had_resolver else
                f"No se ha podido cargar aquí, así que el episodio {episode_info.id} se ha abierto "
                f"en una pestaña nueva.")
        if alternatives:
            names = (alternatives[0] if len(alternatives) == 1
                     else ", ".join(alternatives[:-1]) + " y " + alternatives[-1])
            body += f" También está en {names}, que sí se {'ve' if len(alternatives) == 1 else 'ven'} aquí."
        buttons = []
        if alternatives:
            buttons.append((f"Ver aquí con {alternatives[0]}",
                            lambda: self.__play_video(episode_info, servers, alternatives[0]), True))
        buttons.append(("Seguir en el navegador", self.main_window.close_player, False))
        self.__player.show_message(f"{label} se abre en tu navegador", body, buttons, icon="external")

    def __set_playing_status(self, status: str) -> None:
        """Pone el estado del reproductor en la columna de información y en la fila de la lista."""
        self.__playing_status = status
        if self.__player_status_label is not None and self.__player_status_label.winfo_exists():
            self.__player_status_label.configure(text=PLAYER_STATUS_LABELS[status].upper())
        self.__refresh_player_info()
        self.__refresh_episode_states()

    def __open_player(self) -> bool:
        """Monta el panel encima de la ficha: la columna de información y el reproductor.

        :return: False si no se pudo montar; quien llama cae al navegador.
        """
        try:
            frame = self.main_window.show_player_frame(self)
            frame.grid_columnconfigure(0, weight=0, minsize=Metrics.PLAYER_INFO_W)
            frame.grid_columnconfigure(1, weight=1)
            frame.grid_rowconfigure(0, weight=0)
            self.__player_info = self.__build_player_info(frame)
            self.__player_info.grid(row=0, column=0, sticky="ns")
            self.__player = VideoPlayer(
                frame,
                on_error=self.__on_player_error,
                on_started=self.__on_player_started,
                on_end=self.__on_player_ended,
                on_fullscreen_request=self.__set_player_fullscreen,
                on_previous=lambda: self.__play_adjacent(-1),
                on_next=lambda: self.__play_adjacent(1)
            )
            self.__player.grid(row=0, column=1, sticky="new", padx=(Metrics.PLAYER_GAP, 0))
        except Exception as exc:
            print(f"No se pudo abrir el reproductor: {exc}")
            self.main_window.close_player()
            return False
        return True

    def close_player(self) -> None:
        """Para el reproductor y olvida el episodio que sonaba. El hub retira después el panel."""
        self.__play_request_seq += 1
        player, self.__player = self.__player, None
        if player is not None:
            player.close()
        self.__player_info = None
        self.__player_status_label = self.__player_episode_label = self.__player_detail_label = None
        self.__player_servers_frame = self.__player_seen_frame = self.__player_next_number = None
        self.__player_next_frame = self.__player_next_label = None
        self.__player_servers_key = None
        self.__playing_episode = None
        self.__playing_status = None
        self.__playing_label = None
        self.__refresh_episode_states()

    def relayout_player(self) -> None:
        if self.__player is not None and self.__player.winfo_exists():
            self.__player.relayout()

    def __set_player_fullscreen(self, fullscreen: bool) -> None:
        """Deja solo el vídeo a pantalla completa, o vuelve al panel acoplado encima de la ficha."""
        if self.__player is None or self.__player_info is None:
            return
        frame = self.main_window.player_frame
        if fullscreen:
            self.__player_info.grid_remove()
            frame.grid_columnconfigure(0, minsize=0)
            frame.grid_rowconfigure(0, weight=1)
            self.__player.grid_configure(sticky="nsew", padx=0)
            self.main_window.enter_player_fullscreen()
            self.__player.set_fullscreen(True)
            return
        self.__player.set_fullscreen(False)
        self.main_window.exit_player_fullscreen()
        frame.grid_rowconfigure(0, weight=0)
        frame.grid_columnconfigure(0, minsize=Metrics.PLAYER_INFO_W)
        self.__player.grid_configure(sticky="new", padx=(Metrics.PLAYER_GAP, 0))
        self.__player_info.grid()
        if self.__playing_episode is not None:
            self.main_window.after(FOCUS_DELAY_MS, self.__scroll_to_episode, self.__playing_episode.id)

    def __build_player_info(self, parent: ctk.CTkFrame) -> ctk.CTkFrame:
        """La columna de la izquierda del vídeo: volver, qué suena, servidores, progreso y siguiente."""
        info = ctk.CTkFrame(parent, width=Metrics.PLAYER_INFO_W, fg_color=Theme.TRANSPARENT)
        info.grid_columnconfigure(0, weight=1, minsize=Metrics.PLAYER_INFO_W)
        info.grid_rowconfigure(8, weight=1)

        back_button = ctk.CTkButton(
            info,
            text="Volver a la ficha",
            image=player_icon("left", 16),
            width=1,
            height=EPISODE_CONTROL_H,
            corner_radius=Metrics.RADIUS_CONTROL,
            font=Theme.font(*Theme.T_UI),
            fg_color=Theme.CARD,
            hover_color=Theme.CARD_HOVER,
            text_color=Theme.TXT_2,
            border_width=1,
            border_color=Theme.LINE,
            command=self.main_window.close_player
        )
        back_button.grid(row=0, column=0, sticky="w")

        self.__player_status_label = ctk.CTkLabel(
            info, text=PLAYER_STATUS_LABELS["loading"].upper(),
            font=Theme.font(*Theme.T_LABEL), text_color=Theme.TXT_3, anchor="w", height=16
        )
        self.__player_status_label.grid(row=1, column=0, sticky="w", pady=(PLAYER_BLOCK_GAP, 6))

        title_font = Theme.font(22, True)
        title = ctk.CTkLabel(
            info,
            text=Theme.ellipsize(self.anime_info.title or "", title_font, Metrics.PLAYER_INFO_W),
            font=title_font, text_color=Theme.TXT, anchor="w", justify="left"
        )
        title.grid(row=2, column=0, sticky="w")

        meta = ctk.CTkFrame(info, height=1, fg_color=Theme.TRANSPARENT)
        meta.grid(row=3, column=0, sticky="w", pady=(6, 0))
        self.__player_episode_label = ctk.CTkLabel(meta, text="", font=Theme.font(Theme.T_SUB[0], True),
                                                   text_color=Theme.TXT, height=18)
        self.__player_episode_label.grid(row=0, column=0, sticky="w")
        self.__player_detail_label = ctk.CTkLabel(meta, text="", font=Theme.font(*Theme.T_SUB),
                                                  text_color=Theme.TXT_2, height=18)
        self.__player_detail_label.grid(row=0, column=1, sticky="w")

        provider_label = ctk.CTkLabel(info, text=self.__player_provider_text(),
                                      font=Theme.font(12), text_color=Theme.TXT_3, anchor="w", height=16)
        provider_label.grid(row=4, column=0, sticky="w", pady=(3, 0))

        servers_caption = ctk.CTkLabel(info, text="SERVIDOR", font=Theme.font(*Theme.T_LABEL),
                                       text_color=Theme.TXT_3, anchor="w", height=16)
        servers_caption.grid(row=5, column=0, sticky="w", pady=(PLAYER_BLOCK_GAP, 8))
        self.__player_servers_frame = ctk.CTkFrame(info, height=1, fg_color=Theme.TRANSPARENT)
        self.__player_servers_frame.grid(row=6, column=0, sticky="w")

        progress_block = ctk.CTkFrame(info, height=1, fg_color=Theme.TRANSPARENT)
        progress_block.grid(row=7, column=0, sticky="ew", pady=(PLAYER_BLOCK_GAP, 0))
        ctk.CTkLabel(progress_block, text="TU PROGRESO", font=Theme.font(*Theme.T_LABEL),
                     text_color=Theme.TXT_3, anchor="w", height=16).grid(row=0, column=0, sticky="w", pady=(0, 8))
        self.__player_seen_frame = ctk.CTkFrame(progress_block, height=1, fg_color=Theme.TRANSPARENT)
        self.__player_seen_frame.grid(row=1, column=0, sticky="w")

        # Un frame con dos etiquetas y no un CTkButton, porque el número va a la
        # derecha. El clic se ata a los tres: los eventos de Tk no burbujean.
        next_frame = ctk.CTkFrame(info, height=PLAYER_NEXT_H, corner_radius=9, fg_color=Theme.LINE)
        next_frame.grid(row=9, column=0, sticky="ew", pady=(PLAYER_BLOCK_GAP, 0))
        next_frame.grid_propagate(False)
        next_frame.grid_rowconfigure(0, weight=1)
        next_frame.grid_columnconfigure(0, weight=1)
        self.__player_next_label = ctk.CTkLabel(next_frame, text="  Siguiente episodio",
                                                image=player_icon("next", 16, Theme.TXT_3),
                                                compound="left", font=Theme.font(Theme.T_UI[0], True),
                                                text_color=Theme.TXT_3, fg_color=Theme.LINE)
        self.__player_next_label.grid(row=0, column=0, sticky="w", padx=(16, 0))
        self.__player_next_number = ctk.CTkLabel(next_frame, text="", font=Theme.font(12),
                                                 text_color=Theme.TXT_3, fg_color=Theme.LINE)
        self.__player_next_number.grid(row=0, column=1, sticky="e", padx=(0, 16))
        for widget in (next_frame, self.__player_next_label, self.__player_next_number):
            widget.bind("<Button-1>", lambda _event: self.__play_adjacent(1), add="+")
        self.__player_next_frame = next_frame
        return info

    def __refresh_player_navigation(self) -> None:
        """Enciende o apaga anterior/siguiente de la barra y «Siguiente episodio» de la columna."""
        episode_info = self.__playing_episode
        has_previous = episode_info is not None and self.__adjacent_episode(episode_info.id, -1) is not None
        following = self.__adjacent_episode(episode_info.id, 1) if episode_info is not None else None
        if self.__player is not None and self.__player.winfo_exists():
            self.__player.set_navigation(has_previous, following is not None)

        frame = self.__player_next_frame
        if frame is None or not frame.winfo_exists():
            return
        enabled = following is not None
        background = Theme.ACCENT if enabled else Theme.LINE
        ink = Theme.ACCENT_INK if enabled else Theme.TXT_3
        cursor = "hand2" if enabled else ""
        frame.configure(fg_color=background, cursor=cursor)
        self.__player_next_label.configure(fg_color=background, text_color=ink, cursor=cursor,
                                           image=player_icon("next", 16, ink))
        self.__player_next_number.configure(fg_color=background, text_color=ink, cursor=cursor,
                                            text=str(following.id) if enabled else "")

    def __player_provider_text(self) -> str:
        """«AnimeAV1 · en tu biblioteca»: quién sirve lo que se ve y, si está guardado, de quién es la fila."""
        provider_name = self.anime_provider_mgr.get_provider_name(self.provider_id)
        if not self.__is_saved:
            return provider_name
        if self.__has_split_identity():
            saved_name = (self.anime_provider_mgr.get_provider_name(self.__saved_provider_id)
                          if self.__saved_provider_id is not None else "sin proveedor anotado")
            return f"{provider_name} · tu fila es de {saved_name}"
        return f"{provider_name} · en tu biblioteca"

    def __refresh_player_info(self) -> None:
        """Repinta en la columna el episodio, el servidor, las fichas de servidores y el progreso."""
        episode_info = self.__playing_episode
        if episode_info is None or self.__player_info is None or not self.__player_info.winfo_exists():
            return
        self.__player_episode_label.configure(text=f"Episodio {episode_info.id}")
        server_text = f" · servidor {self.__playing_label}" if self.__playing_label else ""
        self.__player_detail_label.configure(text=f" de {len(self.anime_info.episodes)}{server_text}")
        self.__refresh_player_navigation()
        self.__build_player_servers()
        self.__refresh_seen_bar()

    def __build_player_servers(self) -> None:
        """Fichas de los servidores del episodio que suena, repartidas en líneas de 330 px."""
        frame = self.__player_servers_frame
        if frame is None or not frame.winfo_exists():
            return
        key = (tuple(self.__playing_servers.items()), self.__playing_label)
        if key == self.__player_servers_key:
            return
        self.__player_servers_key = key
        for child in frame.winfo_children():
            child.destroy()

        font = Theme.font(*Theme.T_UI)
        bold = Theme.font(Theme.T_UI[0], True)
        line: Optional[ctk.CTkFrame] = None
        used = 0
        for label, url in self.__playing_servers.items():
            active = label == self.__playing_label
            resolvable = registry.has_resolver(url)
            text = label if resolvable else f"{label} ↗"
            # Estimación del ancho que pinta CTkButton: texto, relleno y borde.
            width = (bold if active else font).measure(text) + 26
            if line is None or used + PLAYER_CHIP_GAP + width > Metrics.PLAYER_INFO_W:
                first_line = line is None
                line = ctk.CTkFrame(frame, height=1, fg_color=Theme.TRANSPARENT)
                line.pack(anchor="w", pady=(0 if first_line else PLAYER_CHIP_GAP, 0))
                used = 0
            chip = ctk.CTkButton(
                line,
                text=text,
                width=1,
                height=PLAYER_CHIP_H,
                corner_radius=Metrics.RADIUS_CONTROL,
                font=bold if active else font,
                fg_color=Theme.ACCENT_SOFT if active else Theme.CARD,
                hover_color=Theme.ACCENT_SOFT if active else Theme.CARD_HOVER,
                text_color=Theme.ACCENT if active else (Theme.TXT_2 if resolvable else Theme.TXT_3),
                border_width=1,
                border_color=Theme.ACCENT if active else Theme.LINE,
                command=lambda chosen=label: self.__play_video(self.__playing_episode, self.__playing_servers, chosen)
            )
            chip.pack(side="left", padx=(0 if used == 0 else PLAYER_CHIP_GAP, 0))
            used += width + (0 if used == 0 else PLAYER_CHIP_GAP)
