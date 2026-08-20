__author__ = "Jose David Escribano Orts"
__subsystem__ = "gui.components"
__module__ = "view_header.py"
__version__ = "0.1"
__info__ = {"subsystem": __subsystem__, "module_name": __module__, "version": __version__}

"""Cabecera común a todas las vistas: título, subtítulo y zona de controles.

Alto fijo de 80 px (``Metrics.VIEW_HEADER_H``). A la izquierda el título y su
subtítulo; a la derecha, un contenedor vacío donde cada vista mete lo suyo
—buscador, orden, paginación— usando ``controls_frame`` como padre.

La cabecera **no** repite contadores: viven en la barra lateral y duplicarlos es
justo lo que prohíbe la regla de composición del diseño (`DISENO.md` §6).
"""

from typing import Optional

import customtkinter as ctk

from gui.theme import Metrics, Theme


class ViewHeader(ctk.CTkFrame):
    """Cabecera de una vista.

    Uso típico desde una vista::

        header = ViewHeader(main_window.content_frame, "Viendo", "3 animes en curso")
        header.grid(row=0, column=0, columnspan=6, sticky="ew")
        mi_boton = ctk.CTkButton(header.controls_frame, ...)
        mi_boton.grid(row=0, column=0)
    """

    def __init__(self, parent, title: str, subtitle: Optional[str] = None, **kwargs):
        """
        :param parent: normalmente ``main_window.content_frame``.
        :param title: título de la vista, en ``T_VIEW``.
        :param subtitle: línea de apoyo en ``T_SUB`` y ``TXT_3``. ``None`` la
            omite y el título queda centrado verticalmente él solo.
        """
        super().__init__(
            parent,
            corner_radius=0,
            fg_color=Theme.TRANSPARENT,
            **kwargs
        )
        # El alto se fija con `minsize` y no con `height=` + `grid_propagate(False)`:
        # esa combinación deja el marco al alto pedido pero su rejilla interna
        # sigue centrando los hijos como si midiera los 200 por defecto de
        # CTkFrame, y el texto acaba fuera de la parte visible. Con minsize la
        # fila mide 80 de verdad y la cabecera se ajusta a ella, sin encoger hasta
        # el alto de sus etiquetas.
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

        #: Zona derecha. Cada vista mete aquí sus controles con este frame como
        #: padre; la cabecera no sabe ni le importa cuáles son.
        #:
        #: ⚠️ Nace con `height=1` porque un CTkFrame **sin hijos** conserva su alto
        #: por defecto (200) como tamaño pedido, y eso estiraría la cabecera a 200
        #: px en toda vista que no le meta controles. En cuanto una vista añade
        #: algo, el frame crece hasta su contenido él solo.
        self.controls_frame = ctk.CTkFrame(self, height=1, fg_color=Theme.TRANSPARENT)
        self.controls_frame.grid(row=0, column=1, sticky="e", padx=(0, Metrics.CONTENT_PAD_X))

    def set_title(self, title: str) -> None:
        self.title_label.configure(text=title)

    def set_subtitle(self, subtitle: Optional[str]) -> None:
        """Cambia el subtítulo. ``None`` o cadena vacía lo esconde."""
        self.subtitle_label.configure(text=subtitle or "")
        if subtitle:
            self.subtitle_label.grid(row=1, column=0, sticky="w", pady=(2, 0))
        else:
            self.subtitle_label.grid_remove()
