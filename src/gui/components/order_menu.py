__author__ = "Jose David Escribano Orts"
__subsystem__ = "gui.components"
__module__ = "order_menu.py"
__version__ = "0.1"
__info__ = {"subsystem": __subsystem__, "module_name": __module__, "version": __version__}

"""Desplegable de orden de las vistas: el mismo control en Favoritos, Pendientes y Buscar.

Las vistas lo destruyen cada vez que se cambia de pestaña, y ``CTkOptionMenu``
no borra su menú interno del registro de escalado de CustomTkinter al
destruirse: ese registro lo retendría para siempre, con todo su árbol de widgets.
"""

from typing import Callable, List

import customtkinter as ctk

from gui.theme import Metrics, Theme


class OrderMenu(ctk.CTkOptionMenu):
    """Desplegable con los colores del tema que se libera entero al destruirse."""

    def __init__(self, parent, values: List[str], command: Callable[[str], None], **kwargs):
        """Construye el desplegable.

        :param values: Textos de las opciones, en el orden en que se ven.
        :param command: Recibe el texto de la opción elegida.
        :param kwargs: Medidas, fuente o color de texto que cambien; por defecto, los de una cabecera de vista.
        """
        kwargs.setdefault("width", 180)
        kwargs.setdefault("height", 34)
        kwargs.setdefault("corner_radius", Metrics.RADIUS_CONTROL)
        kwargs.setdefault("font", Theme.font(*Theme.T_UI))
        kwargs.setdefault("text_color", Theme.TXT)
        super().__init__(
            parent,
            values=values,
            command=command,
            dropdown_font=Theme.font(*Theme.T_UI),
            fg_color=Theme.CARD,
            button_color=Theme.CARD,
            button_hover_color=Theme.CARD_HOVER,
            dropdown_fg_color=Theme.CARD,
            dropdown_hover_color=Theme.CARD_HOVER,
            dropdown_text_color=Theme.TXT,
            **kwargs
        )

    def destroy(self) -> None:
        """Destruye el desplegable y saca su menú del registro de escalado, que no lo hace solo."""
        ctk.ScalingTracker.remove_widget(self._dropdown_menu._set_scaling, self._dropdown_menu)
        super().destroy()
