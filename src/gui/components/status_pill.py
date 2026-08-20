__author__ = "Jose David Escribano Orts"
__subsystem__ = "gui.components"
__module__ = "status_pill.py"
__version__ = "0.2"
__info__ = {"subsystem": __subsystem__, "module_name": __module__, "version": __version__}

"""Píldora de estado: «Viendo», «Pendiente», «Finalizado» o «Favorito».

Los cuatro pares de color de `DISENO.md` §1 en un solo sitio, para que ninguna
vista vuelva a decidir de qué color va un estado. Se usa de dos formas:

- como **widget**, cuando la píldora es una pieza más del layout;
- como **par de colores**, con ``colors()`` y ``text()``, cuando quien pinta es
  otro componente. Es lo que hace la rejilla de «Favoritos»: el sello superpuesto
  al póster ya lo sabe pintar ``PosterGrid`` (`badge` + `badge_colors`), así que
  la píldora solo aporta el texto y los colores.

``other_status()`` responde a la pregunta que hace falta en la biblioteca: además
de estar donde está, **¿qué más es este anime?** Un favorito puede estar a la vez
en curso, en la cola o terminado, y ese es el dato que no se ve en ninguna otra
parte de la pantalla.

``icon()`` completa el juego con el **glifo** de cada estado, que es lo que el
sello del diseño pone delante del texto. Se dibuja con PIL en tiempo de
ejecución, igual que las estrellas de la calificación y el pin del proveedor: son
tres formas de dos trazos, no dependen de que el sistema tenga un glifo concreto,
salen exactas a cualquier tamaño y —a diferencia de los iconos de la barra
lateral— **son nuestros**, así que no arrastran la deuda B11.
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


#: Cómo se dibuja el glifo de cada estado. Solo están los **tres excluyentes**:
#: son exactamente los que puede devolver ``other_status()`` y los únicos que el
#: sello llega a enseñar. «Favorito» no tiene glifo a propósito — la pestaña de
#: favoritos no se sella a sí misma (`DISENO.md` §6: ningún dato repetido).
_GLYPHS: Dict[AnimeStatus, Callable[[ImageDraw.ImageDraw, float, str], None]] = {
    AnimeStatus.WATCHING: _eye_glyph,
    AnimeStatus.FINISHED: _check_glyph,
    AnimeStatus.PENDING:  _list_glyph,
}

#: Glifos ya construidos, indexados por (estado, tamaño). Un ``CTkImage`` se
#: puede compartir entre widgets: con doce celdas por página, dibujarlo una vez
#: ahorra once dibujos por repintado.
_ICON_CACHE: Dict[Tuple[AnimeStatus, int], ctk.CTkImage] = {}


class StatusPill(ctk.CTkLabel):
    """Píldora de un estado de la biblioteca.

    Uso típico::

        pill = StatusPill(parent, AnimeStatus.WATCHING)
        pill.grid(row=0, column=1)
    """

    #: Alto de la píldora. El radio es la mitad (`DISENO.md` §3: píldora = alto / 2).
    HEIGHT: int = 20

    def __init__(self, parent, status: AnimeStatus, text: Optional[str] = None, **kwargs):
        """
        :param status: estado que representa; de él salen texto y colores.
        :param text: texto alternativo, para cuando el estado se acompaña de un
            dato («12 / 12» en finalizados). Por defecto, el nombre del estado.
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
    def icon(status: AnimeStatus, size: int = ICON_SIZE) -> Optional[ctk.CTkImage]:
        """Glifo del estado, listo para ponerlo delante del texto de un **sello**.

        Devuelve ``None`` para los estados sin glifo —hoy solo «Favorito»—, así
        que quien lo pinte tiene que tolerarlo: una etiqueta sin ``image`` sale
        con el texto solo, que es exactamente lo que se quiere.

        ⚠️ **Se tiñe con la variante oscura del color del estado, en los dos
        temas.** El sello va sobre ``Theme.BADGE_BG``, que es una superficie
        oscura tanto en claro como en oscuro porque se superpone a la carátula y
        no al fondo de la aplicación; usar ahí la variante clara (``FIN_TXT[0]``
        es un verde oscuro) dejaría el glifo casi invisible justo en el tema en
        el que el diseño pide comprobar la legibilidad.

        :param status: estado del que se quiere el glifo.
        :param size: lado del dibujo. El ancho de la imagen es ``size`` más el
            hueco que la separa del texto.
        """
        draw_glyph = _GLYPHS.get(status)
        if draw_glyph is None:
            return None

        key = (status, size)
        cached = _ICON_CACHE.get(key)
        if cached is not None:
            return cached

        color = StatusPill.colors(status)[0][1]
        big = size * _SUPERSAMPLE
        gap = _ICON_GAP * _SUPERSAMPLE
        glyph = Image.new("RGBA", (big + gap, big), (0, 0, 0, 0))
        draw_glyph(ImageDraw.Draw(glyph), big, color)
        glyph = glyph.resize((size + _ICON_GAP, size), Image.LANCZOS)

        # La misma imagen en los dos temas: el fondo del sello no cambia con la
        # apariencia, así que el glifo tampoco tiene por qué.
        image = ctk.CTkImage(light_image=glyph, dark_image=glyph, size=(size + _ICON_GAP, size))
        _ICON_CACHE[key] = image
        return image

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
