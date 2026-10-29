__author__ = "Jose David Escribano Orts"
__subsystem__ = "gui.components"
__module__ = "anime_row.py"
__version__ = "0.5"
__info__ = {"subsystem": __subsystem__, "module_name": __module__, "version": __version__}

"""Fila en cascada de una vista de biblioteca: la unidad de «Viendo» y «Pendientes».

Una fila responde a «¿qué es esto y por dónde voy?» sin abrir la ficha: póster,
título, géneros, progreso de episodios y de qué proveedor es la fila. Al pasar el
ratón aparece una acción a la derecha —«Episodio N →» en Viendo, «Empezar» en
Pendientes— para saltar sin dar el rodeo por la ficha.

Estas dos vistas son las que sirven para elegir qué ver ahora, y por eso
enseñan progreso en vez de una miniatura más grande.

Dos cosas que conviene no deshacer:

- ⚠️ **El progreso sale de la fila, nunca de la red.** ``watched_episodes`` y
  ``episodes`` ya están en la BD; pedirlo al proveedor dejaría la vista en blanco
  sin conexión, que es justo cuando más se usa la biblioteca.
- ⚠️ **El hover no puede fiarse de un solo ``<Leave>``.** Tk manda ``Leave`` al
  marco cuando el puntero entra en uno de sus hijos, así que el resaltado
  parpadearía y la acción aparecería y desaparecería sola. Se comprueba la
  posición real del puntero antes de apagar nada (``__pointer_inside()``).
"""
import customtkinter as ctk

from dataclasses import dataclass
from typing import Any, Callable, List, Optional, Tuple

from dataPersistence.animesPersistence import AnimeRecord
from gui.components.resume_card import resume_progress
from gui.theme import Metrics, Theme
from utils.utils import find_cached_poster_path, load_rounded_image, refactor_genre_text


@dataclass
class RowAction:
    """Acción que aparece a la derecha de la fila al pasar el ratón.

    :param text: lo que se lee en la píldora («Episodio 13 →»).
    :param command: recibe el ``AnimeRecord`` de la fila.
    """
    text: str
    command: Callable[[AnimeRecord], None]


class AnimeRow(ctk.CTkFrame):
    """Una fila de la cascada.

    «Pendientes» la reutiliza con ``poster_size=Metrics.ROW_PENDING_POSTER``,
    ``show_progress=False`` —un anime pendiente no tiene progreso que enseñar— y
    ``meta_text`` para poner «N episodios · Proveedor» donde iría el proveedor.
    """

    #: Ancho de la barra de progreso. El diseño deja el conjunto en 340 px
    #: contando la etiqueta de al lado; aquí son dos widgets y se separan.
    PROGRESS_W: int = 210
    #: Ancho reservado al nombre del proveedor y al hueco de la acción. Son anchos
    #: fijos para que las dos columnas queden alineadas de una fila a otra: si no,
    #: «Episodio 9 →» y «Episodio 1164 →» corren el proveedor de sitio.
    PROVIDER_W: int = 90
    #: Ancho de la columna derecha cuando lleva ``meta_text`` en vez del
    #: proveedor a secas: «1163 episodios · AnimeAV1» no cabe en 90 px, y el
    #: ancho tiene que ser el mismo en todas las filas o los textos dejan de
    #: alinearse por la derecha.
    META_W: int = 170
    ACTION_W: int = 130
    #: Ancho con el que se mide el título para recortarlo. Sale del reparto de la
    #: vista Viendo (1216 menos márgenes, panel lateral, póster y columna derecha);
    #: se puede afinar por parámetro si otra vista reparte distinto.
    TEXT_W: int = 420

    #: Alto de la píldora de acción. Su radio es la mitad (píldora).
    ACTION_H: int = 30

    def __init__(self, parent, anime_record: AnimeRecord,
                 poster_size: Tuple[int, int] = Metrics.ROW_WATCHING_POSTER,
                 show_progress: bool = True,
                 action: Optional[RowAction] = None,
                 on_click: Optional[Callable[[Any], None]] = None,
                 provider_name: Optional[str] = None,
                 meta_text: Optional[str] = None,
                 text_width: Optional[int] = None,
                 show_separator: bool = True,
                 **kwargs):
        """Construye la fila.

        :param anime_record: fila de la biblioteca. Todo lo que se pinta sale de
            aquí; la fila no consulta la BD ni la red.
        :param poster_size: 70 x 100 en Viendo, 56 x 80 en Pendientes.
        :param show_progress: barra + «N de M episodios». Pendientes la apaga.
        :param action: píldora que aparece en hover. ``None`` deja la fila sin
            acción y no reserva su hueco.
        :param on_click: recibe el ``anime_id`` al pulsar en cualquier parte de la
            fila que no sea la acción.
        :param provider_name: nombre legible del proveedor de la fila. ``None`` o
            cadena vacía no pinta nada: mejor un hueco que la palabra
            «desconocido» repetida seis veces.
        :param meta_text: texto que **sustituye** al proveedor en la columna
            derecha cuando la fila tiene algo más que contar. Pendientes lo usa
            para «N episodios · Proveedor»: sin barra de progreso, el dato que
            hace útil una cola es la duración, y el proveedor cabe en la misma
            línea.
        :param text_width: ancho al que se recorta el título. Por defecto ``TEXT_W``.
        :param show_separator: línea ``LINE_SOFT`` bajo la fila. La última de la
            lista puede quitarla.
        """
        super().__init__(parent, height=1, corner_radius=0, fg_color=Theme.TRANSPARENT, **kwargs)

        self.anime_record = anime_record
        self.__on_click = on_click
        self.__action = action
        self.__text_width = text_width or self.TEXT_W
        self.__show_progress = show_progress
        self.__progress_frame: Optional[ctk.CTkFrame] = None
        self.__progress_bar: Optional[ctk.CTkProgressBar] = None
        self.__caption_label: Optional[ctk.CTkLabel] = None
        self.__right: Optional[ctk.CTkFrame] = None
        self.__provider_label: Optional[ctk.CTkLabel] = None
        self.__meta_width: int = self.PROVIDER_W
        self.__action_holder: Optional[ctk.CTkFrame] = None
        self.__action_button: Optional[ctk.CTkButton] = None
        #: ``True`` desde que se atan los eventos: lo que se cree después hay que atarlo a mano.
        self.__interactive: bool = False
        #: Tk no guarda referencia a la imagen de un widget: sin esto el recolector
        #: se la lleva y la fila sale sin póster.
        self.__image: Optional[ctk.CTkImage] = None

        self.grid_columnconfigure(0, weight=1)

        # El cuerpo es lo que se resalta; el separador queda fuera para que la
        # línea no cambie de color con el hover.
        self.__body = ctk.CTkFrame(self, corner_radius=Metrics.RADIUS_POSTER, fg_color=Theme.TRANSPARENT)
        self.__body.grid(row=0, column=0, sticky="ew")
        self.__body.grid_columnconfigure(1, weight=1)

        self.__build_poster(poster_size)
        self.__build_middle(show_progress)
        self.__build_right(provider_name, meta_text)

        if show_separator:
            separator = ctk.CTkFrame(self, height=1, corner_radius=0, fg_color=Theme.LINE_SOFT)
            separator.grid(row=1, column=0, sticky="ew")

        self.__bind_interactions()

    # ------------------------------------------------------------------
    # Construcción
    # ------------------------------------------------------------------
    def __build_poster(self, poster_size: Tuple[int, int]) -> None:
        poster_path = find_cached_poster_path(self.anime_record.anime_id) or ""
        self.__image = load_rounded_image(poster_path, poster_size, Metrics.RADIUS_CONTROL)
        poster_label = ctk.CTkLabel(self.__body, text="", font=Theme.font(*Theme.T_UI), image=self.__image)
        poster_label.grid(row=0, column=0, padx=(12, 18), pady=16)

    def __build_middle(self, show_progress: bool) -> None:
        middle = ctk.CTkFrame(self.__body, fg_color=Theme.TRANSPARENT)
        middle.grid(row=0, column=1, sticky="ew")
        middle.grid_columnconfigure(0, weight=1)

        title_font = Theme.font(*Theme.T_ROW)
        title_label = ctk.CTkLabel(
            middle,
            # Una sola línea: en una cascada el título compite con el progreso y
            # dos líneas descuadran la fila entera.
            text=Theme.ellipsize(self.anime_record.title, title_font, self.__text_width, 1),
            font=title_font,
            text_color=Theme.TXT,
            anchor="w"
        )
        title_label.grid(row=0, column=0, sticky="w")

        genres_font = Theme.font(*Theme.T_META)
        genres_label = ctk.CTkLabel(
            middle,
            text=Theme.ellipsize(self.__genres_text(), genres_font, self.__text_width, 1),
            font=genres_font,
            text_color=Theme.TXT_3,
            anchor="w"
        )
        genres_label.grid(row=1, column=0, sticky="w", pady=(7, 0))

        if not show_progress:
            return

        self.__progress_frame = ctk.CTkFrame(middle, height=1, fg_color=Theme.TRANSPARENT)
        self.__progress_frame.grid(row=2, column=0, sticky="w", pady=(11, 0))

        self.__caption_label = ctk.CTkLabel(
            self.__progress_frame,
            text="",
            font=Theme.font(*Theme.T_META),
            text_color=Theme.TXT_3,
            anchor="w"
        )
        self.__caption_label.grid(row=0, column=1, padx=(11, 0))
        self.__apply_progress()

    def __apply_progress(self) -> None:
        """Vuelca en la barra y en su texto lo que dice ``resume_progress()``.

        La barra se crea la primera vez que hay un total que enseñar: una fila
        sin lista de episodios no la lleva, y puede ganarla al refrescarse.
        """
        _next_episode, total, fraction = resume_progress(self.anime_record)
        if not total:
            last_watched = self.anime_record.last_watched_episode or 0
            self.__caption_label.configure(
                text=f"Último visto: episodio {last_watched}" if last_watched else "Sin episodios registrados")
            return

        if self.__progress_bar is None:
            self.__progress_bar = ctk.CTkProgressBar(
                self.__progress_frame,
                width=self.PROGRESS_W,
                height=Metrics.PROGRESS_H,
                corner_radius=Metrics.PROGRESS_RADIUS,
                fg_color=Theme.LINE,
                progress_color=Theme.ACCENT
            )
            self.__progress_bar.grid(row=0, column=0)
            if self.__interactive:
                for widget in self.__descendants(self.__progress_bar):
                    self.__bind_widget(widget, clickable=True)
        self.__progress_bar.set(fraction)
        watched = len(set(self.anime_record.watched_episodes) & set(self.anime_record.episodes))
        self.__caption_label.configure(text=f"{watched} de {total} episodios")

    def __build_right(self, provider_name: Optional[str], meta_text: Optional[str]) -> None:
        self.__right = ctk.CTkFrame(self.__body, height=1, fg_color=Theme.TRANSPARENT)
        self.__right.grid(row=0, column=2, padx=(18, 12), sticky="e")

        # `meta_text` manda si viene: ya incluye el proveedor, así que no se
        # pintan los dos. El ancho es fijo en los dos casos para que la columna
        # quede a plomo de una fila a otra, y se recorta antes que desbordarlo.
        self.__meta_width = self.META_W if meta_text else self.PROVIDER_W
        self.__provider_label = ctk.CTkLabel(
            self.__right,
            text=Theme.ellipsize(meta_text or provider_name or "", Theme.font(*Theme.T_META), self.__meta_width, 1),
            width=self.__meta_width,
            font=Theme.font(*Theme.T_META),
            text_color=Theme.TXT_3,
            anchor="e"
        )
        self.__provider_label.grid(row=0, column=0, sticky="e")

        if self.__action is not None:
            self.__build_action()

    def __action_width(self) -> int:
        """:return: Ancho del hueco de la acción: el mínimo del diseño o lo que pida su texto."""
        return max(self.ACTION_W, Theme.font(12, True, False).measure(self.__action.text) + 30)

    def __build_action(self) -> None:
        """Crea la píldora de acción, oculta, en su hueco de la columna derecha."""
        # El hueco de la acción se reserva siempre para que la fila no se mueva
        # cuando aparece la píldora: el marco lleva tamaño propio y no encoge.
        self.__action_holder = ctk.CTkFrame(
            self.__right,
            width=self.__action_width(),
            height=self.ACTION_H,
            fg_color=Theme.TRANSPARENT
        )
        self.__action_holder.grid(row=0, column=1, padx=(14, 0))
        self.__action_holder.grid_propagate(False)
        self.__action_holder.grid_columnconfigure(0, weight=1)
        self.__action_holder.grid_rowconfigure(0, weight=1)

        self.__action_button = ctk.CTkButton(
            self.__action_holder,
            text=self.__action.text,
            height=self.ACTION_H,
            corner_radius=Metrics.pill_radius(self.ACTION_H),
            font=Theme.font(12, True, False),
            fg_color=Theme.TRANSPARENT,
            hover_color=Theme.ACCENT_SOFT,
            text_color=Theme.ACCENT,
            border_width=1,
            border_color=Theme.ACCENT,
            command=self.__handle_action
        )
        self.__action_button.grid(row=0, column=0, sticky="nsew")
        self.__action_button.grid_remove()

    def __genres_text(self) -> str:
        """Géneros en MAYÚSCULAS separados por ` · `, como en el diseño."""
        genres: List[str] = self.anime_record.genres or []
        return " · ".join(refactor_genre_text(genre).upper() for genre in genres)

    # ------------------------------------------------------------------
    # Actualización
    # ------------------------------------------------------------------
    def update_record(self, anime_record: AnimeRecord, action: Optional[RowAction],
                      meta_text: Optional[str] = None) -> None:
        """Repinta en el sitio lo que depende de los episodios, con una fila recién leída.

        Título, géneros y póster no cambian, así que la fila no se recrea: eso
        releería el póster del disco y la haría parpadear.

        :param anime_record: Fila releída de la BD.
        :param action: Acción que corresponde ahora; ``None`` la quita.
        :param meta_text: Texto nuevo de la columna derecha; ``None`` lo deja como está.
        """
        self.anime_record = anime_record
        if self.__show_progress:
            self.__apply_progress()
        if meta_text is not None:
            self.__provider_label.configure(
                text=Theme.ellipsize(meta_text, Theme.font(*Theme.T_META), self.__meta_width, 1))
        self.__set_action(action)

    def __set_action(self, action: Optional[RowAction]) -> None:
        """Cambia, crea o quita la píldora de acción según ``action``."""
        self.__action = action
        if action is None:
            if self.__action_holder is not None:
                self.__action_holder.destroy()
                self.__action_holder = self.__action_button = None
            return

        if self.__action_holder is not None:
            self.__action_button.configure(text=action.text)
            self.__action_holder.configure(width=self.__action_width())
            return

        self.__build_action()
        action_widgets = self.__descendants(self.__action_button)
        for widget in self.__descendants(self.__action_holder):
            self.__bind_widget(widget, clickable=widget not in action_widgets)
        if self.__pointer_inside():
            self.__action_button.grid()

    def refresh_hover(self) -> None:
        """Enciende o apaga el resaltado según dónde está de verdad el puntero.

        Para cuando la vista vuelve a enseñar una página conservada: esconderla
        no manda ``<Leave>``, así que la fila que se pulsó seguiría encendida.
        """
        if self.__pointer_inside():
            self.__handle_enter()
        else:
            self.__clear_hover()

    # ------------------------------------------------------------------
    # Interacción
    # ------------------------------------------------------------------
    def __bind_interactions(self) -> None:
        """Ata hover y clic a la fila y a todos sus hijos, ya que los eventos de Tk no burbujean.

        La píldora de acción queda fuera del clic, incluidos su canvas y su
        label internos (que no son el botón).
        """
        action_widgets = (self.__descendants(self.__action_button)
                          if self.__action_button is not None else [])
        for widget in self.__descendants(self.__body):
            self.__bind_widget(widget, clickable=widget not in action_widgets)
        self.__interactive = True

    def __bind_widget(self, widget, clickable: bool) -> None:
        """Ata a un widget el hover de la fila y, si ``clickable``, su clic.

        :param widget: Widget de la fila.
        :param clickable: ``False`` para las piezas de la píldora de acción.
        """
        # add="+": dentro de la píldora hay manejadores de CustomTkinter que
        # no son nuestros y que no se pueden perder.
        widget.bind("<Enter>", self.__handle_enter, add="+")
        widget.bind("<Leave>", self.__handle_leave, add="+")
        if self.__on_click is not None and clickable:
            widget.bind("<Button-1>", self.__handle_click)
            widget.configure(cursor="hand2")

    def __descendants(self, widget) -> List[Any]:
        """:return: El widget y todos sus descendientes, recursivamente."""
        found = [widget]
        for child in widget.winfo_children():
            found.extend(self.__descendants(child))
        return found

    def __handle_click(self, _event=None) -> None:
        """Delega en on_click con el anime_id de la fila."""
        self.__on_click(self.anime_record.anime_id)

    def __handle_action(self) -> None:
        """Ejecuta el command de la acción con el anime_record de la fila."""
        self.__action.command(self.anime_record)

    def __handle_enter(self, _event=None) -> None:
        """Resalta la fila y muestra la píldora de acción."""
        self.__body.configure(fg_color=Theme.CARD_HOVER)
        if self.__action_button is not None:
            self.__action_button.grid()

    def __handle_leave(self, _event=None) -> None:
        # Tk manda Leave también al pasar del marco a uno de sus hijos. Se
        # comprueba dónde está el puntero de verdad antes de apagar el resaltado;
        # si no, la píldora parpadearía justo al intentar pulsarla.
        if self.__pointer_inside():
            return
        self.__clear_hover()

    def __clear_hover(self) -> None:
        """Apaga el resaltado y esconde la píldora."""
        self.__body.configure(fg_color=Theme.TRANSPARENT)
        if self.__action_button is not None:
            self.__action_button.grid_remove()

    def __pointer_inside(self) -> bool:
        """``True`` si el puntero sigue dentro del cuerpo de la fila."""
        if not self.__body.winfo_exists():
            return False
        pointer_x, pointer_y = self.__body.winfo_pointerxy()
        left, top = self.__body.winfo_rootx(), self.__body.winfo_rooty()
        return (left <= pointer_x < left + self.__body.winfo_width()
                and top <= pointer_y < top + self.__body.winfo_height())
