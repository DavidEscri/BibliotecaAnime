__author__ = "Jose David Escribano Orts"
__subsystem__ = "gui.components"
__module__ = "status_pill.py"
__version__ = "0.4"
__info__ = {"subsystem": __subsystem__, "module_name": __module__, "version": __version__}

"""Píldora de estado: «Viendo», «Pendiente», «Finalizado» o «Favorito».

Los cuatro pares de color en un solo sitio, para que ninguna vista decida por su
cuenta de qué color va un estado. Se usa como widget completo, o como par de
colores con ``colors()`` y ``text()`` cuando quien pinta es otro componente
(p.ej. el sello superpuesto de ``PosterGrid``).

``other_status()`` responde a "¿qué más es este anime, aparte de estar en esta
pestaña?": un favorito puede estar a la vez en curso, en la cola o terminado.

``icon()`` dibuja el glifo de cada estado con PIL en tiempo de ejecución, como
el resto de iconos propios de la interfaz.
"""

from typing import Callable, Dict, Optional, Tuple

import customtkinter as ctk
from PIL import Image, ImageDraw

from dataPersistence.animesPersistence import AnimeRecord, AnimeStatus
from gui.theme import ColorToken, Metrics, Theme

#: Texto y colores (texto, fondo) de cada estado. Los estados excluyentes entre
#: sí —viendo, finalizado y pendiente— comparten forma a propósito: lo que
#: distingue a uno de otro es el color, no el tamaño ni la posición.
_STYLES = {
    AnimeStatus.FAVOURITE: ("Favorito",   Theme.FAV_TXT, Theme.FAV_BG),
    AnimeStatus.WATCHING:  ("Viendo",     Theme.SEE_TXT, Theme.SEE_BG),
    AnimeStatus.FINISHED:  ("Finalizado", Theme.FIN_TXT, Theme.FIN_BG),
    AnimeStatus.PENDING:   ("Pendiente",  Theme.PEN_TXT, Theme.PEN_BG),
}

#: Factor de supermuestreo del dibujo de los glifos. Mismo motivo que en las
#: estrellas: un trazo diagonal de 12 px sin antialias sale dentado.
_SUPERSAMPLE = 8

#: Hueco transparente que el propio dibujo reserva a su derecha. Tk pega la
#: imagen al texto cuando una etiqueta lleva las dos cosas (``compound="left"``)
#: y ``CTkLabel`` no expone el padding interno, así que la separación tiene que
#: venir dentro del icono o el sello sale con el glifo tocando la cifra.
_ICON_GAP = 5

#: Lado del glifo del sello, en píxeles.
ICON_SIZE = 12


def _check_glyph(draw: ImageDraw.ImageDraw, size: float, color: str) -> None:
    """Un ✓: tres puntos en polilínea, con los extremos redondeados a mano."""
    width = max(1, int(size * 0.15))
    points = [(size * 0.17, size * 0.53), (size * 0.40, size * 0.76), (size * 0.83, size * 0.26)]
    draw.line(points, fill=color, width=width, joint="curve")
    # PIL no tiene extremos redondeados: se rematan con un círculo del ancho del
    # trazo. Sin esto los dos cabos del ✓ salen cortados en recto.
    radius = width / 2
    for x, y in (points[0], points[-1]):
        draw.ellipse([x - radius, y - radius, x + radius, y + radius], fill=color)


def _eye_glyph(draw: ImageDraw.ImageDraw, size: float, color: str) -> None:
    """Un ojo: la lente como elipse achatada y la pupila rellena."""
    width = max(1, int(size * 0.12))
    draw.ellipse([size * 0.04, size * 0.22, size * 0.96, size * 0.78], outline=color, width=width)
    draw.ellipse([size * 0.39, size * 0.39, size * 0.61, size * 0.61], fill=color)


def _list_glyph(draw: ImageDraw.ImageDraw, size: float, color: str) -> None:
    """Una lista: tres renglones con su viñeta."""
    width = max(1, int(size * 0.13))
    # La viñeta se queda por debajo de medio renglón de separación: con un
    # círculo más gordo los tres se tocan y la columna de puntos se lee como una
    # barra vertical en vez de como una lista.
    bullet = width * 0.7
    center_x = size * 0.12
    for index in range(3):
        y = size * (0.18 + index * 0.32)
        draw.line([(size * 0.36, y), (size * 0.96, y)], fill=color, width=width)
        draw.ellipse([center_x - bullet, y - bullet, center_x + bullet, y + bullet], fill=color)


def _heart_glyph(draw: ImageDraw.ImageDraw, size: float, color: str) -> None:
    """Un corazón: los dos lóbulos como círculos y la punta como triángulo."""
    # El triángulo arranca en el centro vertical de los lóbulos, no debajo: si
    # empieza más abajo queda un escalón visible entre el círculo y el pico.
    lobe = size * 0.27
    top = size * 0.32
    draw.ellipse([size * 0.02, top - lobe, size * 0.02 + 2 * lobe, top + lobe], fill=color)
    draw.ellipse([size * 0.98 - 2 * lobe, top - lobe, size * 0.98, top + lobe], fill=color)
    draw.polygon([(size * 0.02, top), (size * 0.98, top), (size * 0.5, size * 0.94)], fill=color)


#: Cómo se dibuja el glifo de cada estado: los tres excluyentes que puede
#: devolver ``other_status()``, más «Favorito» para el sello de «Buscar».
_GLYPHS: Dict[AnimeStatus, Callable[[ImageDraw.ImageDraw, float, str], None]] = {
    AnimeStatus.FAVOURITE: _heart_glyph,
    AnimeStatus.WATCHING:  _eye_glyph,
    AnimeStatus.FINISHED:  _check_glyph,
    AnimeStatus.PENDING:   _list_glyph,
}

#: Glifos ya construidos, indexados por (estado, tamaño). Un ``CTkImage`` se
#: puede compartir entre widgets: con doce celdas por página, dibujarlo una vez
#: ahorra once dibujos por repintado.
_ICON_CACHE: Dict[Tuple[AnimeStatus, int, Optional[ColorToken], int], ctk.CTkImage] = {}


class StatusPill(ctk.CTkLabel):
    """Píldora de un estado de la biblioteca."""

    #: Alto de la píldora. El radio es la mitad.
    HEIGHT: int = 20

    def __init__(self, parent, status: AnimeStatus, text: Optional[str] = None, **kwargs):
        """Construye la píldora.

        :param status: Estado que representa; de él salen texto y colores.
        :param text: Texto alternativo, para cuando el estado se acompaña de un
            dato («12 / 12» en finalizados); por defecto, el nombre del estado.
        """
        text_color, fg_color = self.colors(status)
        super().__init__(
            parent,
            text=text if text is not None else self.text(status),
            height=self.HEIGHT,
            corner_radius=Metrics.pill_radius(self.HEIGHT),
            font=Theme.font(*Theme.T_META),
            fg_color=fg_color,
            text_color=text_color,
            **kwargs
        )

    # ------------------------------------------------------------------
    # Uso sin widget
    # ------------------------------------------------------------------
    @staticmethod
    def text(status: AnimeStatus) -> str:
        """El nombre del estado tal y como se lee en la interfaz."""
        return _STYLES[status][0]

    @staticmethod
    def colors(status: AnimeStatus) -> Tuple[ColorToken, ColorToken]:
        """``(color_de_texto, color_de_fondo)`` del estado, en pares (claro, oscuro)."""
        _, text_color, fg_color = _STYLES[status]
        return text_color, fg_color

    @staticmethod
    def icon(status: AnimeStatus, size: int = ICON_SIZE,
             color: Optional[ColorToken] = None,
             gap: int = _ICON_GAP) -> Optional[ctk.CTkImage]:
        """Glifo del estado, listo para ponerlo delante de un texto.

        Sin ``color``, se tiñe con la variante oscura del color del estado en
        los dos temas: es lo que necesita un sello sobre ``Theme.BADGE_BG``,
        una superficie siempre oscura. Con ``color``, se dibuja una vez por
        tema y CustomTkinter resuelve el cambio de apariencia.

        :param status: Estado del que se quiere el glifo.
        :param size: Lado del dibujo.
        :param color: Par (claro, oscuro) con el que teñirlo; None usa la variante oscura del estado.
        :param gap: Hueco transparente a la derecha; 0 para un dibujo cuadrado y centrado.
        :return: El icono, o None si el estado no tiene glifo.
        """
        draw_glyph = _GLYPHS.get(status)
        if draw_glyph is None:
            return None

        key = (status, size, color, gap)
        cached = _ICON_CACHE.get(key)
        if cached is not None:
            return cached

        if color is None:
            dark_variant = StatusPill.colors(status)[0][1]
            tones = (dark_variant, dark_variant)
        else:
            tones = color
        light_glyph, dark_glyph = (StatusPill.__draw(draw_glyph, size, tone, gap) for tone in tones)

        image = ctk.CTkImage(light_image=light_glyph, dark_image=dark_glyph,
                             size=(size + gap, size))
        _ICON_CACHE[key] = image
        return image

    @staticmethod
    def __draw(draw_glyph: Callable[[ImageDraw.ImageDraw, float, str], None],
               size: int, color: str, gap: int = _ICON_GAP) -> Image.Image:
        """Dibuja un glifo supermuestreado y lo reduce al tamaño pedido."""
        big = size * _SUPERSAMPLE
        big_gap = gap * _SUPERSAMPLE
        glyph = Image.new("RGBA", (big + big_gap, big), (0, 0, 0, 0))
        draw_glyph(ImageDraw.Draw(glyph), big, color)
        return glyph.resize((size + gap, size), Image.LANCZOS)

    @staticmethod
    def other_status(anime_record: AnimeRecord,
                     besides: Optional[AnimeStatus] = None) -> Optional[AnimeStatus]:
        """Qué **más** es este anime, aparte del estado de la pestaña en la que se ve.

        Devuelve el único de los tres estados excluyentes —viendo, finalizado,
        pendiente— que tenga la fila, o ``None`` si no tiene ninguno o si es
        justo el que se pide ignorar con ``besides``.

        No hay que desempatar: ``_set_status`` apaga los otros dos al activar
        uno, así que una fila coherente tiene como mucho uno.
        """
        for status, active in ((AnimeStatus.WATCHING, anime_record.is_watching),
                               (AnimeStatus.FINISHED, anime_record.is_finished),
                               (AnimeStatus.PENDING, anime_record.is_pending)):
            if active and status != besides:
                return status
        return None
