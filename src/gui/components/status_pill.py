__author__ = "Jose David Escribano Orts"
__subsystem__ = "gui.components"
__module__ = "status_pill.py"
__version__ = "0.1"
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
"""

from typing import Optional, Tuple

import customtkinter as ctk

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
