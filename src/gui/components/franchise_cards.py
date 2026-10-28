__author__ = "Jose David Escribano Orts"
__subsystem__ = "gui.components"
__module__ = "franchise_cards.py"
__version__ = "0.2"
__info__ = {"subsystem": __subsystem__, "module_name": __module__, "version": __version__}

"""Piezas con las que la ficha enseña la franquicia de un anime.

- ``SeasonLink``: la temporada anterior o la siguiente, en la cabecera.
- ``SeasonCarousel``: la línea principal, con un número fijo de temporadas a la
  vista y flechas que avanzan de una en una.
- ``RelatedGrid`` y ``RelatedCard``: el resto de relacionados, en tarjetas que
  se reparten el ancho.
- ``format_chip()``: el formato (Serie, Película…), con el borde continuo si lo
  dice un proveedor, discontinuo si se ha deducido del título y punteado
  mientras no se sabe. CustomTkinter no dibuja bordes discontinuos, así que el
  borde es una imagen hecha con PIL.

No saben de dónde salen los datos ni piden nada a la red: los pósters los
entrega quien las compone, con ``set_poster()``.
"""

import tkinter

from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Tuple

import customtkinter as ctk
from PIL import Image, ImageDraw

from dataPersistence.animesPersistence import AnimeStatus
from gui.components.status_pill import StatusPill
from gui.theme import ColorToken, Metrics, Theme
from utils.utils import round_image

#: Alto de la ficha de formato y relleno lateral de su texto.
CHIP_H = 18
CHIP_PAD_X = 6
CHIP_RADIUS = 4
#: Supermuestreo del borde de la ficha: un trazo de 1 px sin antialias sale dentado.
_CHIP_SCALE = 4
#: Trazo y hueco del borde discontinuo y del punteado, en píxeles finales.
_DASH = (4, 3)
_DOT = (1, 2)

#: Póster de cada temporada del carrusel y de cada tarjeta de relacionado.
CAROUSEL_POSTER: Tuple[int, int] = Metrics.GRID6_POSTER
RELATED_POSTER: Tuple[int, int] = (48, 72)
#: Relleno de las tarjetas del carrusel y separación entre ellas.
CAROUSEL_CARD_PAD = 8
CAROUSEL_GAP = 12
#: Flechas del carrusel.
ARROW_SIZE = 34
#: Sello «Estás aquí» / «T3» sobre el póster.
ORDER_BADGE_H = 20
ORDER_BADGE_INSET = 8
#: Tarjetas de relacionado: ancho mínimo de columna y separación.
RELATED_MIN_W = 300
RELATED_GAP = 8
RELATED_PAD = 8
#: Enlace de temporada de la cabecera: ancho máximo del título.
LINK_TITLE_W = 260

#: Dibujos ya hechos del borde de la ficha. Se guarda el dibujo y no el CTkImage:
#: un CTkImage compartido retiene todos los widgets que lo han usado.
_chip_drawings: Dict[Tuple[int, int, str, str], Image.Image] = {}


# ----------------------------------------------------------------------
# Ficha de formato
# ----------------------------------------------------------------------
def _dashed_segments(start: float, end: float, dash: int, gap: int) -> List[Tuple[float, float]]:
    """Tramos de trazo entre dos coordenadas, centrados para que los extremos queden simétricos."""
    length = end - start
    period = dash + gap
    count = max(1, int((length + gap) // period))
    used = count * period - gap
    offset = start + (length - used) / 2
    return [(offset + i * period, offset + i * period + dash) for i in range(count)]


def _chip_drawing(width: int, height: int, style: str, color: str) -> Image.Image:
    """El borde de la ficha, a tamaño final, con fondo transparente.

    :param style: ``"solid"``, ``"dashed"`` o ``"dotted"``.
    :param color: Color del trazo, en hexadecimal.
    """
    key = (width, height, style, color)
    cached = _chip_drawings.get(key)
    if cached is not None:
        return cached
    scale = _CHIP_SCALE
    image = Image.new("RGBA", (width * scale, height * scale), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    half = scale / 2
    box = (half, half, width * scale - half - 1, height * scale - half - 1)
    radius = CHIP_RADIUS * scale
    if style == "solid":
        draw.rounded_rectangle(box, radius=radius, outline=color, width=scale)
    else:
        dash, gap = (_DASH if style == "dashed" else _DOT)
        dash, gap = dash * scale, gap * scale
        left, top, right, bottom = box
        # Esquinas siempre continuas: un hueco en la curva deja la ficha sin forma.
        for corner, start in (((left, top), 180), ((right - 2 * radius, top), 270),
                              ((right - 2 * radius, bottom - 2 * radius), 0), ((left, bottom - 2 * radius), 90)):
            x, y = corner
            draw.arc((x, y, x + 2 * radius, y + 2 * radius), start, start + 90, fill=color, width=scale)
        for a, b in _dashed_segments(left + radius, right - radius, dash, gap):
            draw.line((a, top, b, top), fill=color, width=scale)
            draw.line((a, bottom, b, bottom), fill=color, width=scale)
        for a, b in _dashed_segments(top + radius, bottom - radius, dash, gap):
            draw.line((left, a, left, b), fill=color, width=scale)
            draw.line((right, a, right, b), fill=color, width=scale)
    drawing = image.resize((width, height), Image.LANCZOS)
    _chip_drawings[key] = drawing
    return drawing


def format_chip(parent, text: str, style: str = "solid", text_color: Optional[ColorToken] = None) -> ctk.CTkLabel:
    """Ficha pequeña con el formato de un anime.

    :param text: Lo que dice la ficha («Serie», «…»).
    :param style: ``"solid"`` si lo da un proveedor, ``"dashed"`` si se ha
        deducido del título, ``"dotted"`` si todavía no se sabe.
    :param text_color: Color del texto; por defecto, el secundario.
    :return: La etiqueta, sin colocar.
    """
    font = Theme.font(*Theme.T_LABEL)
    width = font.measure(text) + 2 * CHIP_PAD_X
    border = Theme.LINE if style == "solid" else Theme.TXT_3
    image = ctk.CTkImage(light_image=_chip_drawing(width, CHIP_H, style, border[0]),
                         dark_image=_chip_drawing(width, CHIP_H, style, border[1]),
                         size=(width, CHIP_H))
    text_color = text_color or (Theme.TXT_3 if style == "dotted" else Theme.TXT_2)
    # compound="center" pone el texto encima del borde dibujado.
    return ctk.CTkLabel(parent, text=text, image=image, compound="center", width=width, height=CHIP_H,
                        font=font, fg_color=Theme.TRANSPARENT, text_color=text_color)


# ----------------------------------------------------------------------
# Tarjeta pulsable
# ----------------------------------------------------------------------
def _walk(widget):
    """El widget y todos sus descendientes de Tk, internos de CustomTkinter incluidos."""
    yield widget
    for child in widget.winfo_children():
        yield from _walk(child)


class ClickableCard(ctk.CTkFrame):
    """Marco que se ilumina bajo el puntero y responde al clic en cualquier parte.

    Los eventos de Tk no burbujean, así que clic y hover se atan a cada widget
    de Tk que contiene. Quien herede llama a ``bind_card()`` al terminar de
    construir sus hijos. Solo una tarjeta a la vez puede estar iluminada.
    """

    __hovered: Optional["ClickableCard"] = None

    def __init__(self, parent, on_click: Optional[Callable[[], None]],
                 fg_color: ColorToken | str = Theme.TRANSPARENT,
                 hover_color: ColorToken | str = Theme.CARD_HOVER,
                 border_color: Optional[ColorToken] = None,
                 hover_border_color: Optional[ColorToken] = None, **kwargs):
        """
        :param on_click: Acción del clic; None la deja como tarjeta inerte.
        :param fg_color: Fondo en reposo.
        :param hover_color: Fondo bajo el puntero.
        :param border_color: Borde en reposo; None para no ponerlo.
        :param hover_border_color: Borde bajo el puntero; por defecto, el de reposo.
        """
        if border_color is not None:
            kwargs.setdefault("border_width", 1)
            kwargs["border_color"] = border_color
        super().__init__(parent, fg_color=fg_color, **kwargs)
        self.__on_click = on_click
        self.__colors = (fg_color, hover_color)
        self.__borders = (border_color, hover_border_color or border_color)

    def bind_card(self) -> None:
        """Ata clic y hover a la tarjeta y a todo lo que lleva dentro.

        Con el ``bind`` de Tk y no con el de CustomTkinter, que reenvía a los
        hijos internos y ataría dos veces lo que este recorrido ya visita.
        """
        if self.__on_click is None:
            return
        for widget in _walk(self):
            tkinter.Misc.bind(widget, "<Button-1>", self.__handle_click, "+")
            tkinter.Misc.bind(widget, "<Enter>", self.__handle_enter, "+")
            tkinter.Misc.bind(widget, "<Leave>", self.__handle_leave, "+")
            try:
                tkinter.Misc.configure(widget, cursor="hand2")
            except tkinter.TclError:
                pass

    def __handle_click(self, _event=None) -> None:
        self.__on_click()

    def __handle_enter(self, _event=None) -> None:
        previous = ClickableCard.__hovered
        if previous is not None and previous is not self:
            previous.__paint(False)
        ClickableCard.__hovered = self
        self.__paint(True)

    def __handle_leave(self, _event=None) -> None:
        # Tk manda Leave también al pasar del marco a uno de sus hijos.
        if self.__pointer_inside():
            return
        if ClickableCard.__hovered is self:
            ClickableCard.__hovered = None
        self.__paint(False)

    def __paint(self, hovered: bool) -> None:
        if not self.winfo_exists():
            return
        options = {"fg_color": self.__colors[1] if hovered else self.__colors[0]}
        if self.__borders[0] is not None:
            options["border_color"] = self.__borders[1] if hovered else self.__borders[0]
        self.configure(**options)

    def __pointer_inside(self) -> bool:
        if not self.winfo_exists():
            return False
        pointer_x, pointer_y = self.winfo_pointerxy()
        left, top = self.winfo_rootx(), self.winfo_rooty()
        return left <= pointer_x < left + self.winfo_width() and top <= pointer_y < top + self.winfo_height()


def _poster_slot(parent, size: Tuple[int, int], radius: int) -> ctk.CTkLabel:
    """Hueco de póster del tamaño final, en gris hasta que llegue la imagen."""
    # font= aunque no lleve texto: el CTkFont propio que crearía sin él muere en el
    # hilo que recoja la basura y puede bloquearlo contra el de Tk (ver PosterGrid).
    return ctk.CTkLabel(parent, text="", width=size[0], height=size[1], corner_radius=radius,
                        font=Theme.font(*Theme.T_UI), fg_color=Theme.LINE_SOFT)


def _show_poster(slot: ctk.CTkLabel, image: Image.Image, size: Tuple[int, int], radius: int) -> None:
    """Pone el póster en su hueco. Un CTkImage nuevo por widget, nunca compartido."""
    if slot.winfo_exists():
        slot.configure(image=round_image(image, size, radius), fg_color=Theme.TRANSPARENT)


def _status_pill(parent, status: Optional[AnimeStatus]) -> Optional[StatusPill]:
    return StatusPill(parent, status) if status is not None else None


# ----------------------------------------------------------------------
# Cabecera: temporada anterior y siguiente
# ----------------------------------------------------------------------
class SeasonLink(ClickableCard):
    """«◀ Temporada anterior» o «Temporada siguiente ▶», con el título y el estado de la fila."""

    def __init__(self, parent, title: str, forward: bool, status: Optional[AnimeStatus],
                 on_click: Callable[[], None]):
        """
        :param title: Título de la temporada a la que lleva.
        :param forward: True para la siguiente (flecha a la derecha), False para la anterior.
        :param status: Estado de esa temporada en la biblioteca, o None si no está.
        """
        super().__init__(parent, on_click, fg_color=Theme.CARD, hover_color=Theme.CARD_HOVER,
                         border_color=Theme.LINE, hover_border_color=Theme.ACCENT,
                         corner_radius=9, height=1)
        # Todo en la rejilla de la tarjeta, sin marcos intermedios: cada widget de
        # CustomTkinter cuesta al abrir la ficha, que es donde va esta tarjeta.
        arrow = ctk.CTkLabel(self, text="▶" if forward else "◀", font=Theme.font(13), text_color=Theme.ACCENT,
                             width=14)
        sticky = "e" if forward else "w"
        caption = ctk.CTkLabel(self, text="TEMPORADA SIGUIENTE" if forward else "TEMPORADA ANTERIOR",
                               font=Theme.font(*Theme.T_LABEL), text_color=Theme.TXT_3, height=14, anchor=sticky)
        title_font = Theme.font(Theme.T_UI[0], True)
        title_label = ctk.CTkLabel(self, text=Theme.ellipsize(title, title_font, LINK_TITLE_W, 1),
                                   font=title_font, text_color=Theme.TXT, height=18, anchor=sticky)
        pill = _status_pill(self, status)

        columns = [arrow, None] + ([pill] if pill is not None else [])
        if forward:
            columns.reverse()
        for column, widget in enumerate(columns):
            first, last = column == 0, column == len(columns) - 1
            padx = (12 if first else 10, 12 if last else 0)
            if widget is None:
                caption.grid(row=0, column=column, sticky=sticky, padx=padx, pady=(7, 0))
                title_label.grid(row=1, column=column, sticky=sticky, padx=padx, pady=(0, 7))
            else:
                widget.grid(row=0, column=column, rowspan=2, padx=padx)
        self.bind_card()


# ----------------------------------------------------------------------
# Carrusel de la línea principal
# ----------------------------------------------------------------------
@dataclass
class CarouselItem:
    """Una temporada del carrusel.

    :ivar order_text: Lo que dice el sello del póster («T3», «Estás aquí»).
    :ivar format_style: Estilo de la ficha de formato, como en ``format_chip()``.
    """
    key: str
    title: str
    order_text: str
    current: bool = False
    year: Optional[int] = None
    format_text: Optional[str] = None
    format_style: str = "solid"
    status: Optional[AnimeStatus] = None


class SeasonCarousel(ctk.CTkFrame):
    """Línea principal de una franquicia: un número fijo de temporadas a la vista y flechas.

    Las flechas avanzan de una en una y se apagan en su extremo; si todo cabe,
    no hay flechas. Al enseñar una línea, la temporada actual queda lo más
    centrada posible. Una posición ``None`` es un hueco: una temporada que se
    sabe que existe pero todavía no se conoce.
    """

    def __init__(self, parent, on_open: Callable[[str], None], visible: int = 5):
        """
        :param on_open: Se llama con la clave de la temporada pulsada.
        :param visible: Temporadas a la vista.
        """
        super().__init__(parent, height=1, fg_color=Theme.TRANSPARENT)
        self.__on_open = on_open
        self.__visible = visible
        self.__items: List[Optional[CarouselItem]] = []
        self.__start = 0
        self.__browsable = True
        self.__posters: Dict[str, Image.Image] = {}
        self.__slots: Dict[str, ctk.CTkLabel] = {}

        self.grid_columnconfigure(0, weight=1)
        header = ctk.CTkFrame(self, height=1, fg_color=Theme.TRANSPARENT)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        header.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(header, text="LÍNEA PRINCIPAL", font=Theme.font(*Theme.T_LABEL), text_color=Theme.TXT_3,
                     height=16).grid(row=0, column=0, sticky="w")
        self.__hint_label = ctk.CTkLabel(header, text="", font=Theme.font(*Theme.T_META), text_color=Theme.TXT_3,
                                         height=16)
        self.__hint_label.grid(row=0, column=1, sticky="w", padx=(8, 0))
        self.__counter_label = ctk.CTkLabel(header, text="", font=Theme.font(*Theme.T_NUM), text_color=Theme.TXT_3,
                                            height=16)
        self.__counter_label.grid(row=0, column=2, sticky="e")

        row = ctk.CTkFrame(self, height=1, fg_color=Theme.TRANSPARENT)
        row.grid(row=1, column=0, sticky="ew")
        row.grid_columnconfigure(1, weight=1)
        self.__previous_button = self.__arrow(row, "◀", -1)
        self.__next_button = self.__arrow(row, "▶", 1)
        self.__previous_button.grid(row=0, column=0, padx=(0, 6))
        self.__next_button.grid(row=0, column=2, padx=(6, 0))
        self.__window = ctk.CTkFrame(row, height=1, fg_color=Theme.TRANSPARENT)
        self.__window.grid(row=0, column=1, sticky="ew")
        self.__window.grid_columnconfigure(tuple(range(visible)), weight=1, uniform="carousel")

        self.__note_label = ctk.CTkLabel(self, text="", font=Theme.font(*Theme.T_META), text_color=Theme.TXT_3,
                                         height=16, anchor="w")

    # ------------------------------------------------------------------
    # API
    # ------------------------------------------------------------------
    def show(self, items: List[Optional[CarouselItem]], current_index: int, hint: Optional[str] = None,
             note: Optional[str] = None, browsable: bool = True) -> None:
        """Enseña una línea con la temporada actual lo más centrada posible.

        :param items: Temporadas en orden; None es un hueco.
        :param current_index: Posición de la temporada actual.
        :param hint: Texto gris junto al título del bloque, o None.
        :param note: Línea gris debajo del carrusel, o None.
        :param browsable: False apaga las flechas aunque haya más de las que caben.
        """
        self.__items = list(items)
        self.__browsable = browsable
        self.__start = max(0, min(current_index - self.__visible // 2, len(items) - self.__visible))
        self.__hint_label.configure(text=f"· {hint}" if hint else "")
        if note:
            self.__note_label.configure(text=note)
            self.__note_label.grid(row=2, column=0, sticky="w", pady=(8, 0))
        else:
            self.__note_label.grid_remove()
        self.__render()

    def set_poster(self, key: str, image: Image.Image) -> None:
        """Pone el póster de una temporada, esté a la vista o no."""
        self.__posters[key] = image
        slot = self.__slots.get(key)
        if slot is not None:
            _show_poster(slot, image, CAROUSEL_POSTER, Metrics.RADIUS_POSTER)

    # ------------------------------------------------------------------
    # Pintado
    # ------------------------------------------------------------------
    def __arrow(self, parent, text: str, step: int) -> ctk.CTkButton:
        return ctk.CTkButton(parent, text=text, width=ARROW_SIZE, height=ARROW_SIZE, corner_radius=ARROW_SIZE // 2,
                             font=Theme.font(12), fg_color=Theme.CARD, hover_color=Theme.ACCENT_SOFT,
                             text_color=Theme.ACCENT, text_color_disabled=Theme.LINE, border_width=1,
                             border_color=Theme.LINE, command=lambda: self.__move(step))

    def __move(self, step: int) -> None:
        start = max(0, min(self.__start + step, len(self.__items) - self.__visible))
        if start != self.__start:
            self.__start = start
            self.__render()

    def __render(self) -> None:
        for child in self.__window.winfo_children():
            child.destroy()
        self.__slots.clear()

        total = len(self.__items)
        needs_arrows = total > self.__visible
        if needs_arrows:
            self.__previous_button.grid()
            self.__next_button.grid()
            can_go_back = self.__browsable and self.__start > 0
            can_go_on = self.__browsable and self.__start + self.__visible < total
            self.__set_arrow(self.__previous_button, can_go_back)
            self.__set_arrow(self.__next_button, can_go_on)
            end = min(self.__start + self.__visible, total)
            self.__counter_label.configure(text=f"{self.__start + 1}–{end} de {total}" if self.__browsable else "")
        else:
            self.__previous_button.grid_remove()
            self.__next_button.grid_remove()
            self.__counter_label.configure(text="")

        for column, item in enumerate(self.__items[self.__start:self.__start + self.__visible]):
            card = self.__skeleton() if item is None else self.__card(item)
            card.grid(row=0, column=column, sticky="n", padx=(0 if column == 0 else CAROUSEL_GAP // 2,
                                                             0 if column == self.__visible - 1 else CAROUSEL_GAP // 2))

    @staticmethod
    def __set_arrow(button: ctk.CTkButton, enabled: bool) -> None:
        button.configure(state="normal" if enabled else "disabled",
                         fg_color=Theme.CARD if enabled else Theme.TRANSPARENT,
                         border_color=Theme.LINE)

    def __card(self, item: CarouselItem) -> ctk.CTkFrame:
        """Tarjeta de una temporada: póster con su sello, título y la línea de año, formato y estado."""
        if item.current:
            card = ClickableCard(self.__window, None, fg_color=Theme.CARD, border_color=Theme.ACCENT,
                                 border_width=2, corner_radius=10, height=1)
        else:
            card = ClickableCard(self.__window, lambda key=item.key: self.__on_open(key), corner_radius=10,
                                 height=1)

        slot = _poster_slot(card, CAROUSEL_POSTER, Metrics.RADIUS_POSTER)
        slot.grid(row=0, column=0, sticky="w", padx=CAROUSEL_CARD_PAD, pady=(CAROUSEL_CARD_PAD, 0))
        self.__slots[item.key] = slot
        if item.key in self.__posters:
            _show_poster(slot, self.__posters[item.key], CAROUSEL_POSTER, Metrics.RADIUS_POSTER)
        badge = ctk.CTkLabel(slot, text=item.order_text, height=ORDER_BADGE_H, corner_radius=5,
                             font=Theme.font(10, True, True),
                             fg_color=Theme.ACCENT if item.current else Theme.BADGE_BG,
                             text_color=Theme.ACCENT_INK if item.current else Theme.BADGE_INK)
        # place() y no grid: el sello se superpone al póster, no ocupa sitio.
        badge.place(relx=1.0, rely=0.0, x=-ORDER_BADGE_INSET, y=ORDER_BADGE_INSET, anchor="ne")

        title_font = Theme.font(Theme.T_UI[0], True)
        ctk.CTkLabel(card, text=Theme.ellipsize(item.title, title_font, CAROUSEL_POSTER[0], 2), font=title_font,
                     text_color=Theme.TXT, justify="left", anchor="w").grid(
            row=1, column=0, sticky="w", padx=CAROUSEL_CARD_PAD, pady=(7, 0))

        meta = ctk.CTkFrame(card, height=1, fg_color=Theme.TRANSPARENT)
        meta.grid(row=2, column=0, sticky="w", padx=CAROUSEL_CARD_PAD, pady=(5, CAROUSEL_CARD_PAD))
        parts = []
        if item.year is not None:
            parts.append(ctk.CTkLabel(meta, text=str(item.year), font=Theme.font(*Theme.T_META),
                                      text_color=Theme.TXT_3, height=CHIP_H))
        if item.format_text:
            parts.append(format_chip(meta, item.format_text, item.format_style))
        pill = _status_pill(meta, item.status)
        if pill is not None:
            parts.append(pill)
        for column, part in enumerate(parts):
            part.grid(row=0, column=column, padx=(0 if column == 0 else 6, 0))
        card.bind_card()
        return card

    def __skeleton(self) -> ctk.CTkFrame:
        """Hueco de una temporada que todavía no se conoce."""
        card = ctk.CTkFrame(self.__window, height=1, fg_color=Theme.TRANSPARENT)
        _poster_slot(card, CAROUSEL_POSTER, Metrics.RADIUS_POSTER).grid(
            row=0, column=0, sticky="w", padx=CAROUSEL_CARD_PAD, pady=(CAROUSEL_CARD_PAD, 0))
        ctk.CTkFrame(card, width=int(CAROUSEL_POSTER[0] * 0.7), height=10, corner_radius=5,
                     fg_color=Theme.LINE_SOFT).grid(row=1, column=0, sticky="w", padx=CAROUSEL_CARD_PAD, pady=(9, 0))
        return card


# ----------------------------------------------------------------------
# Relacionados
# ----------------------------------------------------------------------
class RelatedCard(ClickableCard):
    """Un relacionado: póster pequeño si lo hay, título y la línea de tipo, año, formato y estado."""

    def __init__(self, parent, title: str, kind: str, on_click: Callable[[], None],
                 year: Optional[int] = None, format_text: Optional[str] = None, format_style: str = "solid",
                 source: Optional[str] = None,
                 status: Optional[AnimeStatus] = None, with_poster: bool = True):
        """
        :param kind: Tipo de relación tal como se lee («Otro», «Versión alternativa»).
        :param format_text: Formato, o None para no poner ficha.
        :param format_style: Estilo de la ficha, como en ``format_chip()``.
        :param source: Siglas del proveedor que dio el formato, si no es el de la ficha.
        :param status: Estado en la biblioteca, o None si no está.
        :param with_poster: False para la tarjeta de solo texto (el proveedor no da póster).
        """
        super().__init__(parent, on_click, fg_color=Theme.CARD, hover_color=Theme.CARD,
                         border_color=Theme.LINE_SOFT, hover_border_color=Theme.ACCENT, corner_radius=9, height=1)
        self.__title = title
        self.__slot: Optional[ctk.CTkLabel] = None
        self.grid_columnconfigure(1, weight=1)
        if with_poster:
            self.__slot = _poster_slot(self, RELATED_POSTER, 6)
            self.__slot.grid(row=0, column=0, padx=(RELATED_PAD, 0), pady=RELATED_PAD)

        texts = ctk.CTkFrame(self, height=1, fg_color=Theme.TRANSPARENT)
        texts.grid(row=0, column=1, sticky="w", padx=12, pady=RELATED_PAD + (0 if with_poster else 2))
        self.__title_font = Theme.font(Theme.T_UI[0], True)
        self.__title_label = ctk.CTkLabel(texts, text=title, font=self.__title_font, text_color=Theme.TXT,
                                          justify="left", anchor="w")
        self.__title_label.grid(row=0, column=0, sticky="w")

        meta = ctk.CTkFrame(texts, height=1, fg_color=Theme.TRANSPARENT)
        meta.grid(row=1, column=0, sticky="w", pady=(5, 0))
        caption = kind if year is None else f"{kind} · {year}"
        parts = [ctk.CTkLabel(meta, text=caption, font=Theme.font(*Theme.T_META), text_color=Theme.TXT_3,
                              height=CHIP_H)]
        if format_text:
            parts.append(format_chip(meta, format_text, format_style))
        if source:
            parts.append(ctk.CTkLabel(meta, text=source, font=Theme.font(10, True), text_color=Theme.ACCENT,
                                      height=CHIP_H))
        pill = _status_pill(meta, status)
        if pill is not None:
            parts.append(pill)
        for column, part in enumerate(parts):
            part.grid(row=0, column=column, padx=(0 if column == 0 else 6, 0))
        self.bind_card()

    def set_poster(self, image: Image.Image) -> None:
        if self.__slot is not None:
            _show_poster(self.__slot, image, RELATED_POSTER, 6)

    def set_text_width(self, width: int) -> None:
        """Recorta el título a dos líneas del ancho dado."""
        if self.__title_label.winfo_exists():
            self.__title_label.configure(text=Theme.ellipsize(self.__title, self.__title_font, max(80, width), 2))

    @property
    def has_poster(self) -> bool:
        return self.__slot is not None


class RelatedGrid(ctk.CTkFrame):
    """Tarjetas de relacionado repartidas en tantas columnas como quepan.

    La vista lo coloca con ``sticky="ew"`` para que mida el ancho de su padre y
    no el de su contenido. Las tarjetas se crean con este marco como padre y se
    entregan con ``set_cards()``.
    """

    def __init__(self, parent, min_card_width: int = RELATED_MIN_W, gap: int = RELATED_GAP):
        super().__init__(parent, height=1, fg_color=Theme.TRANSPARENT)
        self.__min_card_width = min_card_width
        self.__gap = gap
        self.__cards: List[RelatedCard] = []
        self.__columns = 0
        self.bind("<Configure>", self.__on_configure, add="+")

    def set_cards(self, cards: List[RelatedCard], width_hint: int) -> None:
        """Coloca las tarjetas.

        :param width_hint: Ancho a usar mientras el marco no se ha medido.
        """
        self.__cards = cards
        self.__layout(width_hint)

    def __on_configure(self, event) -> None:
        if self.__columns_for(event.width) != self.__columns:
            self.__layout(event.width)

    def __columns_for(self, width: int) -> int:
        return max(1, (width + self.__gap) // (self.__min_card_width + self.__gap))

    def __layout(self, width: int) -> None:
        columns = self.__columns_for(width)
        for column in range(max(columns, self.__columns)):
            self.grid_columnconfigure(column, weight=1 if column < columns else 0,
                                      uniform="related" if column < columns else "")
        self.__columns = columns
        card_width = (width - (columns - 1) * self.__gap) // columns
        for index, card in enumerate(self.__cards):
            row, column = divmod(index, columns)
            card.grid(row=row, column=column, sticky="nsew",
                      padx=(0 if column == 0 else self.__gap // 2, 0 if column == columns - 1 else self.__gap // 2),
                      pady=(0 if row == 0 else self.__gap, 0))
            text_width = card_width - 24 - 2 * RELATED_PAD - (RELATED_POSTER[0] + RELATED_PAD if card.has_poster else 0)
            card.set_text_width(text_width)
