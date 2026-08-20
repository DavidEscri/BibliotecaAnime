__author__ = "Jose David Escribano Orts"
__subsystem__ = "gui.components"
__module__ = "rating_stars.py"
__version__ = "0.1"
__info__ = {"subsystem": __subsystem__, "module_name": __module__, "version": __version__}

"""Calificación personal: cinco estrellas con medios puntos y su valor en cifra.

Es lo que estrena la pestaña «Favoritos» (`DISENO.md` §7). La escala que se
guarda es un **entero de 0 a 10** —dos puntos por estrella—, así que el medio
punto se representa sin decimales y ni SQLite ni la comparación del orden tienen
que lidiar con flotantes.

Tres decisiones de construcción que conviene no deshacer:

- **Las estrellas se dibujan con PIL**, no con una fuente ni con iconos en disco.
  Una estrella es un polígono de diez vértices y el medio punto es un rectángulo
  de relleno recortado con la máscara de ese polígono: pintarlo es exacto a
  cualquier tamaño y no depende de que el sistema tenga un glifo concreto ni de
  añadir PNG al repositorio. Se dibuja a 8x y se reduce con LANCZOS.
- **El medio punto sale de dónde se pulsa**, no de un control aparte: mitad
  izquierda de una estrella = medio punto, mitad derecha = punto entero. Por eso
  cada estrella ocupa un hueco más ancho que su dibujo (``STAR_SLOT``): el aire
  entre estrellas también es zona pulsable, o las mitades quedarían en 7 px.
- ⚠️ La mitad se calcula con ``event.widget.winfo_width()`` y no con el ancho
  pedido al construir. ``CTkLabel.bind()`` no ata al widget que creas, sino a su
  etiqueta interna **y** a su canvas, y no tienen por qué medir lo mismo; medir
  el que recibe el evento es lo único que da la misma respuesta en los dos casos.
"""

import math
from typing import Callable, Dict, List, Optional, Tuple

import customtkinter as ctk
from PIL import Image, ImageDraw

from gui.theme import Theme

#: Imágenes ya construidas, indexadas por (relleno, tamaño). Un CTkImage se
#: puede compartir entre widgets: con 5 estrellas por celda y 10 celdas por
#: página, generarlas una vez ahorra 50 dibujos por repintado.
_IMAGE_CACHE: Dict[Tuple[float, int], ctk.CTkImage] = {}

#: Factor de supermuestreo. La estrella se dibuja a 8x y se reduce con LANCZOS
#: porque un polígono a 14 px sin antialias sale con los picos dentados.
_SUPERSAMPLE = 8

#: Relación entre el radio interior y el exterior de la estrella. La estrella
#: "matemática" de cinco puntas usa 0.382 y sale muy afilada; los iconos de
#: interfaz rondan 0.48, que es lo que se lee bien a 14 px.
_INNER_RATIO = 0.48


def _star_points(size: int) -> List[Tuple[float, float]]:
    """Los diez vértices de una estrella de cinco puntas inscrita en ``size``."""
    center = size / 2
    outer = size / 2
    inner = outer * _INNER_RATIO
    points: List[Tuple[float, float]] = []
    for index in range(10):
        radius = outer if index % 2 == 0 else inner
        angle = math.radians(-90 + index * 36)
        points.append((center + radius * math.cos(angle), center + radius * math.sin(angle)))
    return points


def _star_layer(fill: float, size: int, on_color: str, off_color: str) -> Image.Image:
    """Una estrella rellena de ``on_color`` hasta la fracción ``fill``, y de ``off_color`` el resto."""
    big = size * _SUPERSAMPLE
    mask = Image.new("L", (big, big), 0)
    ImageDraw.Draw(mask).polygon(_star_points(big), fill=255)

    layer = Image.new("RGBA", (big, big), off_color)
    if fill > 0:
        ImageDraw.Draw(layer).rectangle([0, 0, int(big * fill), big], fill=on_color)
    # La máscara del polígono se aplica como alfa: lo de fuera de la estrella
    # queda transparente y deja ver el fondo de la celda, sea cual sea.
    layer.putalpha(mask)
    return layer.resize((size, size), Image.LANCZOS)


def star_image(fill: float, size: int) -> ctk.CTkImage:
    """Devuelve (y cachea) la estrella rellena a la fracción ``fill`` (0.0, 0.5 o 1.0).

    Construye las dos variantes de la imagen —clara y oscura— a partir de los
    tokens del tema, así que ``CTkImage`` cambia de una a otra al cambiar la
    apariencia **sin que nadie tenga que reconfigurar el widget**.
    """
    key = (fill, size)
    cached = _IMAGE_CACHE.get(key)
    if cached is not None:
        return cached
    image = ctk.CTkImage(
        light_image=_star_layer(fill, size, Theme.ACCENT[0], Theme.LINE[0]),
        dark_image=_star_layer(fill, size, Theme.ACCENT[1], Theme.LINE[1]),
        size=(size, size)
    )
    _IMAGE_CACHE[key] = image
    return image


def format_rating(rating: Optional[int]) -> str:
    """Pasa la escala entera a lo que se lee: 9 → ``"4,5"``; ``None`` → ``"Sin calificar"``."""
    if rating is None:
        return "Sin calificar"
    return f"{rating / 2:.1f}".replace(".", ",")


class RatingStars(ctk.CTkFrame):
    """Fila de cinco estrellas pulsables con la calificación en cifra al lado.

    Uso típico::

        stars = RatingStars(cell, value=anime_record.rating, on_change=self.__on_rate)
        stars.grid(row=2, column=0)

    ``on_change`` recibe la calificación nueva: un entero de 0 a 10, o ``None``
    si el usuario ha borrado la suya. Sin ``on_change`` la fila es solo de
    lectura y no responde al ratón.
    """

    #: Lado del dibujo de la estrella. El diseño pide 13 px (`.ic.xs`); se usa 14
    #: porque es par y el medio punto cae en un píxel exacto.
    STAR_PX: int = 14
    #: Ancho del hueco de cada estrella, dibujo incluido. Los 3 px de más son la
    #: separación del diseño, y son pulsables: si no, cada mitad mediría 7 px.
    STAR_SLOT: int = 17
    #: Cuántas estrellas, y cuántos puntos vale cada una.
    STARS: int = 5
    POINTS_PER_STAR: int = 2

    def __init__(self, parent, value: Optional[int] = None,
                 on_change: Optional[Callable[[Optional[int]], None]] = None, **kwargs):
        """
        :param parent: normalmente la celda de ``PosterGrid``.
        :param value: calificación actual, de 0 a 10, o ``None`` si no la hay.
        :param on_change: se llama con la calificación nueva **después** de
            repintar. La vista es quien persiste; el widget no toca la BD.
        """
        super().__init__(parent, height=1, corner_radius=0, fg_color=Theme.TRANSPARENT, **kwargs)

        self.__value = value
        self.__on_change = on_change
        self.__star_labels: List[ctk.CTkLabel] = []

        for index in range(self.STARS):
            star_label = ctk.CTkLabel(self, text="", width=self.STAR_SLOT, height=self.STAR_PX)
            star_label.grid(row=0, column=index)
            if on_change is not None:
                star_label.configure(cursor="hand2")
                star_label.bind("<Button-1>", lambda event, i=index: self.__on_star_click(event, i))
            self.__star_labels.append(star_label)

        self.__value_label = ctk.CTkLabel(
            self,
            text="",
            font=Theme.font(*Theme.T_META),
            text_color=Theme.TXT_3,
            anchor="w"
        )
        self.__value_label.grid(row=0, column=self.STARS, padx=(5, 0))

        self.__repaint()

    # ------------------------------------------------------------------
    # Estado
    # ------------------------------------------------------------------
    def value(self) -> Optional[int]:
        """Calificación actual, de 0 a 10, o ``None`` si no la hay."""
        return self.__value

    def set_value(self, value: Optional[int]) -> None:
        """Cambia la calificación mostrada. **No** llama a ``on_change``."""
        self.__value = value
        self.__repaint()

    # ------------------------------------------------------------------
    # Pintado
    # ------------------------------------------------------------------
    def __repaint(self) -> None:
        points = self.__value or 0
        for index, star_label in enumerate(self.__star_labels):
            # Cuántos de los dos puntos de esta estrella están cubiertos.
            covered = min(max(points - index * self.POINTS_PER_STAR, 0), self.POINTS_PER_STAR)
            star_label.configure(image=star_image(covered / self.POINTS_PER_STAR, self.STAR_PX))
        self.__value_label.configure(text=format_rating(self.__value))

    # ------------------------------------------------------------------
    # Interacción
    # ------------------------------------------------------------------
    def __on_star_click(self, event, index: int) -> None:
        """Traduce el clic a una calificación y avisa a quien la persiste.

        Mitad izquierda de la estrella, medio punto; mitad derecha, entero.
        Volver a pulsar la calificación que ya estaba la **borra**: es la única
        forma de dejar un anime sin calificar una vez calificado, y repetir el
        gesto es lo que uno prueba antes de buscar un botón de deshacer.
        """
        width = event.widget.winfo_width()
        half = width > 1 and event.x < width / 2
        new_value = index * self.POINTS_PER_STAR + (1 if half else self.POINTS_PER_STAR)
        if new_value == self.__value:
            new_value = None

        self.__value = new_value
        self.__repaint()
        if self.__on_change is not None:
            self.__on_change(new_value)
