__author__ = "Jose David Escribano Orts"
__subsystem__ = "gui.components"
__module__ = "view_header.py"
__version__ = "0.1"
__info__ = {"subsystem": __subsystem__, "module_name": __module__, "version": __version__}

"""Cabecera común a todas las vistas: título, subtítulo y zona de controles.

Alto fijo de 80 px (``Metrics.VIEW_HEADER_H``). A la izquierda el título y su
subtítulo; a la derecha, un contenedor vacío donde cada vista mete lo suyo
—buscador, orden, paginación— usando ``controls_frame`` como padre.
"""

from typing import Optional

import customtkinter as ctk

from gui.theme import Metrics, Theme


class ViewHeader(ctk.CTkFrame):
    """Cabecera de una vista: título, subtítulo opcional y zona de controles a la derecha."""

    def __init__(self, parent, title: str, subtitle: Optional[str] = None, **kwargs):
        """Construye la cabecera.

        :param parent: Normalmente main_window.content_frame.
        :param title: Título de la vista.
        :param subtitle: Línea de apoyo; None la omite y centra el título solo.
        """
        super().__init__(
            parent,
            corner_radius=0,
            fg_color=Theme.TRANSPARENT,
            **kwargs
        )
        # El alto se fija con minsize, no con height= + grid_propagate(False): esa
        # combinación deja la rejilla interna centrando los hijos como si aún
        # midiera el alto por defecto de CTkFrame, y el texto queda fuera de vista.
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, minsize=Metrics.VIEW_HEADER_H)

        self.__text_frame = ctk.CTkFrame(self, fg_color=Theme.TRANSPARENT)
        self.__text_frame.grid(row=0, column=0, sticky="w", padx=(Metrics.CONTENT_PAD_X, 0))

        self.title_label = ctk.CTkLabel(
            self.__text_frame,
            text=title,
            font=Theme.font(*Theme.T_VIEW),
            text_color=Theme.TXT,
            anchor="w"
        )
        self.title_label.grid(row=0, column=0, sticky="w")

        self.subtitle_label = ctk.CTkLabel(
            self.__text_frame,
            text=subtitle or "",
            font=Theme.font(*Theme.T_SUB),
            text_color=Theme.TXT_3,
            anchor="w"
        )
        if subtitle:
            self.subtitle_label.grid(row=1, column=0, sticky="w", pady=(2, 0))

        # Zona derecha donde cada vista mete sus controles. height=1 evita que un
        # CTkFrame sin hijos conserve su alto por defecto (200px) como tamaño pedido.
        self.controls_frame = ctk.CTkFrame(self, height=1, fg_color=Theme.TRANSPARENT)
        self.controls_frame.grid(row=0, column=1, sticky="e", padx=(0, Metrics.CONTENT_PAD_X))

    def set_title(self, title: str) -> None:
        """Cambia el título de la cabecera."""
        self.title_label.configure(text=title)

    def set_subtitle(self, subtitle: Optional[str]) -> None:
        """Cambia el subtítulo. ``None`` o cadena vacía lo esconde."""
        self.subtitle_label.configure(text=subtitle or "")
        if subtitle:
            self.subtitle_label.grid(row=1, column=0, sticky="w", pady=(2, 0))
        else:
            self.subtitle_label.grid_remove()
