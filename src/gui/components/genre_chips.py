__author__ = "Jose David Escribano Orts"
__subsystem__ = "gui.components"
__module__ = "genre_chips.py"
__version__ = "0.2"
__info__ = {"subsystem": __subsystem__, "module_name": __module__, "version": __version__}

"""Fichas de género: la fila de filtros con lo elegido siempre a la vista.

Tres reglas de comportamiento:

- las seleccionadas van delante, con ``ACCENT_SOFT`` y borde ``ACCENT``, y
  llevan una ✕ para quitarlas de un clic;
- de las no seleccionadas se ven las primeras (``VISIBLE_GENRES``) y las demás
  aparecen tras la ficha «Más géneros»;
- el ancho no se reparte en columnas fijas: las fichas se envuelven midiendo
  el texto, porque «Recuentos de la vida» y «Magia» no miden lo mismo.

Los dos glifos —la ✕ y el chevrón— se dibujan con PIL en tiempo de ejecución,
como el resto de iconos propios de la interfaz.
"""

from typing import Callable, Dict, List, Optional, Tuple

import customtkinter as ctk
from PIL import Image, ImageDraw

from APIs.common.models import AnimeGenreFilter
from gui.theme import ColorToken, Metrics, Theme
from utils.utils import refactor_genre_text

#: Factor de supermuestreo del dibujo de los glifos. Mismo motivo que en las
#: estrellas y en los sellos: un trazo diagonal de 9 px sin antialias sale
#: dentado.
_SUPERSAMPLE = 8

#: Hueco transparente que el dibujo reserva a su **izquierda**. Tk pega la imagen
#: al texto cuando una etiqueta o un botón llevan las dos cosas y ``CTkButton`` no
#: expone el padding interno, así que la separación tiene que venir dentro del
#: propio icono.
_ICON_GAP = 5

#: Lado del glifo de una ficha, en píxeles.
_ICON_SIZE = 9

#: Glifos ya construidos, indexados por (clase, color). Un ``CTkImage`` se puede
#: compartir entre widgets y en esta fila hay cuarenta fichas.
_ICON_CACHE: Dict[Tuple[str, ColorToken], ctk.CTkImage] = {}

#: ``borderwidth`` de la etiqueta del texto, a cada lado. La crea CustomTkinter
#: con ``padx=0, pady=0, borderwidth=1``.
_LABEL_BORDER = 1

#: ``borderwidth`` de la etiqueta del icono, a cada lado. Esa la crea sin
#: argumentos, así que se queda con el 2 por defecto de Tk. Su ``padx`` no
#: cuenta: Tk solo se lo suma al texto, y esta etiqueta no lleva.
_IMAGE_LABEL_BORDER = 2

#: ``CTkButton._image_label_spacing``: el hueco que la rejilla interna deja
#: entre el texto y la imagen cuando el botón lleva las dos cosas.
_IMAGE_LABEL_SPACING = 6


def _cross_glyph(draw: ImageDraw.ImageDraw, size: float, color: str, offset: float) -> None:
    """Una ✕: dos diagonales cruzadas."""
    width = max(1, int(size * 0.16))
    draw.line([(offset + size * 0.1, size * 0.1), (offset + size * 0.9, size * 0.9)],
              fill=color, width=width)
    draw.line([(offset + size * 0.9, size * 0.1), (offset + size * 0.1, size * 0.9)],
              fill=color, width=width)


def _chevron_glyph(draw: ImageDraw.ImageDraw, size: float, color: str, offset: float) -> None:
    """Un chevrón hacia abajo: dos trazos en «v», sin cerrar."""
    width = max(1, int(size * 0.16))
    draw.line([(offset + size * 0.1, size * 0.3), (offset + size * 0.5, size * 0.72),
               (offset + size * 0.9, size * 0.3)], fill=color, width=width, joint="curve")


#: Cómo se dibuja cada glifo. La clave es la que se pasa a ``_glyph_image()``.
_GLYPHS: Dict[str, Callable[[ImageDraw.ImageDraw, float, str, float], None]] = {
    "cross": _cross_glyph,
    "chevron": _chevron_glyph,
}


def _glyph_image(name: str, color: ColorToken, size: int = _ICON_SIZE) -> ctk.CTkImage:
    """Devuelve el glifo pedido, teñido con un par de colores (claro, oscuro).

    A diferencia de los sellos, estos glifos van sobre el fondo de la aplicación
    y no sobre una carátula, así que **sí** cambian con el tema: el ``CTkImage``
    lleva las dos variantes y CustomTkinter elige.
    """
    key = (name, color)
    cached = _ICON_CACHE.get(key)
    if cached is not None:
        return cached

    draw_glyph = _GLYPHS[name]
    big = size * _SUPERSAMPLE
    gap = _ICON_GAP * _SUPERSAMPLE
    variants: List[Image.Image] = []
    for variant_color in color:
        glyph = Image.new("RGBA", (big + gap, big), (0, 0, 0, 0))
        # El hueco va a la izquierda: el glifo de una ficha se pinta detrás del
        # texto (compound="right"), al revés que el de un sello.
        draw_glyph(ImageDraw.Draw(glyph), big, variant_color, gap)
        variants.append(glyph.resize((size + _ICON_GAP, size), Image.LANCZOS))

    image = ctk.CTkImage(light_image=variants[0], dark_image=variants[1],
                         size=(size + _ICON_GAP, size))
    _ICON_CACHE[key] = image
    return image


class GenreChips(ctk.CTkFrame):
    """Fila de fichas de género seleccionables."""

    #: Alto de una ficha. El radio es la mitad (píldora = alto / 2).
    CHIP_H: int = 29
    #: Relleno horizontal dentro de la ficha, a cada lado.
    CHIP_PAD_X: int = 12
    #: Separación entre fichas, en los dos ejes.
    CHIP_GAP: int = 8
    #: Cuántas fichas de género se ven en total antes de «Más géneros». Las
    #: seleccionadas **cuentan**: el diseño enseña siete fichas, dos activas y
    #: cinco por elegir, no siete además de las activas.
    VISIBLE_GENRES: int = 7
    #: Ancho de reserva mientras el contenedor todavía no está mapeado y
    #: ``winfo_width()`` devuelve 1: la ventana entera menos la barra lateral
    #: desplegada y los márgenes del contenido.
    FALLBACK_WIDTH: int = Metrics.WINDOW_W - Metrics.SIDEBAR_W - 2 * Metrics.CONTENT_PAD_X

    def __init__(self, parent, on_change: Optional[Callable[[List[AnimeGenreFilter]], None]] = None,
                 max_width: Optional[int] = None, **kwargs):
        """Construye la fila de fichas.

        :param parent: Normalmente main_window.content_frame.
        :param on_change: Recibe la lista de géneros seleccionados cada vez que cambia.
        :param max_width: Ancho en el que envolver; si se omite, se mide el
            contenedor al pintar y se re-envuelve cuando cambie de tamaño.
        """
        # height=1 por lo de siempre: un CTkFrame sin hijos conserva su alto por
        # defecto (200) como tamaño pedido y estiraría la fila que lo contiene.
        super().__init__(parent, height=1, corner_radius=0, fg_color=Theme.TRANSPARENT, **kwargs)

        self.__on_change = on_change
        self.__max_width = max_width
        self.__selected: List[AnimeGenreFilter] = []
        self.__expanded = False
        self.__chips: List[ctk.CTkButton] = []
        #: Ancho con el que se hizo el último envuelto. Sirve para no repintar
        #: cuarenta fichas en cada `<Configure>`, que llegan a decenas por
        #: redimensionado.
        self.__laid_out_width = 0

        if max_width is None:
            self.bind("<Configure>", self.__on_configure)

        # Se pinta ya: una fila de fichas recién creada y vacía no es un estado
        # que le sirva a nadie, y la vista no tiene por qué acordarse de pedirlo.
        self.show()

    # ------------------------------------------------------------------
    # Estado
    # ------------------------------------------------------------------
    def selected(self) -> List[AnimeGenreFilter]:
        """Géneros seleccionados, en el orden del enum. Copia: modificarla no afecta."""
        return list(self.__selected)

    def set_selected(self, genres: Optional[List[AnimeGenreFilter]]) -> None:
        """Fija la selección y repinta. **No** llama a ``on_change``.

        Lo usa la vista al volver a entrar en la pestaña para recuperar el filtro
        de la última búsqueda sin relanzarla.
        """
        chosen = set(genres or [])
        self.__selected = [genre for genre in AnimeGenreFilter if genre in chosen]
        self.show()

    # ------------------------------------------------------------------
    # Pintado
    # ------------------------------------------------------------------
    def show(self) -> None:
        """Repinta la fila entera: seleccionadas delante, el resto detrás."""
        for chip in self.__chips:
            chip.destroy()
        self.__chips.clear()

        available = self.__available_width()
        self.__laid_out_width = available

        hidden = self.__hidden_genres()
        row, used = 0, 0
        for genre in self.__visible_genres():
            is_selected = genre in self.__selected
            chip = self.__build_chip(
                text=refactor_genre_text(genre.name),
                selected=is_selected,
                icon=_glyph_image("cross", Theme.ACCENT) if is_selected else None,
                command=lambda chosen=genre: self.__toggle(chosen)
            )
            row, used = self.__place_chip(chip, row, used, available)

        if hidden or self.__expanded:
            chip = self.__build_chip(
                text="Menos géneros" if self.__expanded else f"Más géneros ({len(hidden)})",
                selected=False,
                icon=_glyph_image("chevron", Theme.TXT_2),
                command=self.__toggle_expanded
            )
            row, _ = self.__place_chip(chip, row, used, available)

        # Con los hijos colocados por place() el marco no pide alto ninguno: hay
        # que decírselo, o la fila de fichas mide cero y la vista se solapa.
        self.configure(width=available,
                       height=(row + 1) * (self.CHIP_H + self.CHIP_GAP) - self.CHIP_GAP)

    def __visible_genres(self) -> List[AnimeGenreFilter]:
        """Las seleccionadas primero; después, las que toque enseñar.

        Las seleccionadas se quedan **siempre** a la vista aunque estén plegadas
        las demás: son el motivo por el que la lista de resultados es la que es.
        """
        rest = [genre for genre in AnimeGenreFilter if genre not in self.__selected]
        if not self.__expanded:
            rest = rest[:max(0, self.VISIBLE_GENRES - len(self.__selected))]
        return self.__selected + rest

    def __hidden_genres(self) -> List[AnimeGenreFilter]:
        """Las que no se están viendo ahora mismo."""
        if self.__expanded:
            return []
        rest = [genre for genre in AnimeGenreFilter if genre not in self.__selected]
        return rest[max(0, self.VISIBLE_GENRES - len(self.__selected)):]

    def __build_chip(self, text: str, selected: bool, icon: Optional[ctk.CTkImage],
                     command: Callable[[], None]) -> ctk.CTkButton:
        # La seleccionada va en negrita, y la negrita mide más: la ficha se mide
        # con la fuente con la que se va a pintar, no con la normal, o el texto
        # se sale por la derecha justo en las que están activas.
        chip_font = Theme.font(Theme.T_META[0], selected)
        return ctk.CTkButton(
            self,
            text=text,
            image=icon,
            # El glifo va detrás del texto, como en el diseño. Sin decirlo, un
            # CTkButton con imagen y texto los superpone.
            compound="right",
            width=self.__chip_width(text, chip_font, icon),
            height=self.CHIP_H,
            corner_radius=Metrics.pill_radius(self.CHIP_H),
            font=chip_font,
            fg_color=Theme.ACCENT_SOFT if selected else Theme.CARD,
            hover_color=Theme.ACCENT_SOFT if selected else Theme.CARD_HOVER,
            text_color=Theme.ACCENT if selected else Theme.TXT_2,
            border_width=1,
            border_color=Theme.ACCENT if selected else Theme.LINE,
            command=command
        )

    def __chip_width(self, text: str, font: ctk.CTkFont, icon: Optional[ctk.CTkImage]) -> int:
        """Ancho real de una ficha, tal y como la mide CTkButton al pintarse.

        Sin ``width``, CTkButton se queda con 140 px por defecto: hay que sumar
        a mano el margen que reserva su rejilla interna, el borde de la etiqueta
        de texto y, con icono, el hueco y el borde de la etiqueta de imagen.

        :param text: Texto de la ficha.
        :param font: Fuente con la que se va a pintar (la seleccionada, en negrita).
        :param icon: Icono de la ficha, si lleva.
        :return: Ancho en píxeles que hay que pedir explícitamente.
        """
        # El relleno efectivo es el mayor de los dos: el del diseño y el que el
        # botón impone por su radio de esquina (columnas de extremo = minsize del radio).
        side = max(self.CHIP_PAD_X, Metrics.pill_radius(self.CHIP_H))
        width = 2 * side + font.measure(text) + 2 * _LABEL_BORDER
        if icon is not None:
            # El CTkImage ya incluye el _ICON_GAP transparente en su size(), no se vuelve a sumar.
            width += _IMAGE_LABEL_SPACING + icon.cget("size")[0] + 2 * _IMAGE_LABEL_BORDER
        return width

    def __place_chip(self, chip: ctk.CTkButton, row: int, used: int,
                     available: int) -> Tuple[int, int]:
        """Coloca una ficha envolviendo por ancho.

        Usa ``place()`` y no ``grid()``: las columnas de una rejilla son comunes
        a todas las filas, así que fichas de distinta fila y misma columna
        compartirían el ancho de la más larga.

        :return: Tupla (fila, ancho usado) tras colocar esta ficha.
        """
        width = chip.cget("width")
        if used and used + width > available:
            row, used = row + 1, 0
        chip.place(x=used, y=row * (self.CHIP_H + self.CHIP_GAP))
        self.__chips.append(chip)
        return row, used + width + self.CHIP_GAP

    def __available_width(self) -> int:
        if self.__max_width is not None:
            return self.__max_width
        width = self.winfo_width()
        if width <= 1:
            width = self.master.winfo_width()
        # Un margen de seguridad: si el envuelto pide exactamente el ancho
        # disponible, la fila estira el marco contenedor y aparece la barra de
        # desplazamiento horizontal.
        return max(240, width - self.CHIP_GAP) if width > 1 else self.FALLBACK_WIDTH

    def __on_configure(self, event) -> None:
        """Re-envuelve cuando el contenedor cambia de ancho de verdad.

        Sin el umbral, cada redimensionado de la ventana repintaría cuarenta
        fichas decenas de veces; y sin re-envolver, plegar la barra lateral
        dejaría media fila desaprovechada.
        """
        if abs(event.width - self.__laid_out_width) <= self.CHIP_GAP:
            return
        self.show()

    # ------------------------------------------------------------------
    # Interacción
    # ------------------------------------------------------------------
    def __toggle(self, genre: AnimeGenreFilter) -> None:
        """Añade o quita un género de la selección, repinta y avisa a on_change."""
        if genre in self.__selected:
            self.__selected.remove(genre)
        else:
            # Se mantiene el orden del enum y no el de pulsación: así la fila no
            # baila cuando quitas una ficha de en medio y vuelves a ponerla.
            self.__selected = [candidate for candidate in AnimeGenreFilter
                               if candidate in self.__selected or candidate == genre]
        self.show()
        if self.__on_change is not None:
            self.__on_change(self.selected())

    def __toggle_expanded(self) -> None:
        """Alterna entre mostrar todos los géneros o solo los visibles."""
        self.__expanded = not self.__expanded
        self.show()
