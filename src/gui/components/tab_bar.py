__author__ = "Jose David Escribano Orts"
__subsystem__ = "gui.components"
__module__ = "tab_bar.py"
__version__ = "0.2"
__info__ = {"subsystem": __subsystem__, "module_name": __module__, "version": __version__}

"""Barra de pestañas con cuerpo perezoso.

Resuelve que una pantalla con varias secciones no pague al abrirse el coste de
todas: cada pestaña se construye la primera vez que se abre, y lo que pida a la
red lo pide entonces. Crear widgets de CustomTkinter es justo lo caro.

Cada pestaña tiene además una zona de herramientas a la derecha de la barra
(orden, buscador…) que solo se ve mientras está activa.
"""

from dataclasses import dataclass
from typing import Callable, Dict, List, Optional

import customtkinter as ctk
import tkinter

from gui.theme import Theme

#: Relleno del texto de cada pestaña y separación entre pestañas.
TAB_PAD_X = 14
TAB_PAD_TOP = 11
TAB_PAD_BOTTOM = 9
TAB_GAP = 4
#: Grosor de la raya de la pestaña activa. Las demás enseñan 1 px de la raya de la barra.
UNDERLINE_H = 2
#: Burbuja con el número de elementos de la pestaña.
COUNT_H = 18
COUNT_PAD_X = 6
COUNT_GAP = 8
#: Separación entre la barra y el cuerpo.
BODY_PAD_TOP = 10
#: Columna de la barra donde van las herramientas, a la derecha de cualquier número de pestañas.
TOOLS_COLUMN = 99

#: Construye el contenido de una pestaña: recibe su cuerpo y su zona de herramientas.
TabBuilder = Callable[[ctk.CTkFrame, ctk.CTkFrame], None]


@dataclass
class _Tab:
    """Una pestaña: su botón en la barra y, una vez abierta, su cuerpo y sus herramientas."""
    key: str
    builder: TabBuilder
    button: ctk.CTkFrame
    label: ctk.CTkLabel
    count_label: Optional[ctk.CTkLabel]
    underline: ctk.CTkFrame
    body: Optional[ctk.CTkFrame] = None
    tools: Optional[ctk.CTkFrame] = None


class TabBar(ctk.CTkFrame):
    """Pestañas con contador opcional, herramientas a la derecha y cuerpo que se construye al abrirse.

    La vista lo coloca con ``sticky="ew"``. Cada pestaña pinta su propio tramo de
    la raya inferior de la barra, porque un marco transparente encima de una raya
    común la taparía.

    Las rayas son de 2 px aunque se vean de 1: un CTkFrame de 1 px de alto no
    pinta nada. Para enseñar solo 1 px se coloca medio fuera de su marco, que lo recorta.
    """

    def __init__(self, parent, on_change: Optional[Callable[[str], None]] = None, **kwargs):
        """
        :param on_change: Se llama con la clave de la pestaña cada vez que cambia la activa.
        """
        super().__init__(parent, height=1, fg_color=Theme.TRANSPARENT, **kwargs)
        self.__on_change = on_change
        self.__tabs: Dict[str, _Tab] = {}
        self.__order: List[str] = []
        self.__selected: Optional[str] = None
        self.__hovered: Optional[str] = None

        self.grid_columnconfigure(0, weight=1)
        self.__bar = ctk.CTkFrame(self, height=1, fg_color=Theme.TRANSPARENT)
        self.__bar.grid(row=0, column=0, sticky="ew")
        # La raya de la barra entera va primero: lo que se crea después queda por
        # encima, así que las pestañas la tapan con su propio pie.
        self.__rule = ctk.CTkFrame(self.__bar, width=1, height=UNDERLINE_H, corner_radius=0, fg_color=Theme.LINE)
        self.__rule.place(relx=0, rely=1.0, y=1, anchor="sw", relwidth=1.0)
        # Las pestañas ocupan las columnas desde la 0; el hueco con peso empuja las
        # herramientas al borde derecho por muchas pestañas que se añadan.
        self.__bar.grid_columnconfigure(TOOLS_COLUMN - 1, weight=1)


    # ------------------------------------------------------------------
    # API
    # ------------------------------------------------------------------
    def add_tab(self, key: str, text: str, builder: TabBuilder, count: Optional[int] = None) -> None:
        """Añade una pestaña al final de la barra, sin construir su contenido.

        :param key: Identificador de la pestaña.
        :param text: Lo que se lee en la barra.
        :param builder: Construye el contenido la primera vez que se abre.
        :param count: Número que acompaña al texto, o None para no ponerlo.
        """
        column = len(self.__order)
        button = ctk.CTkFrame(self.__bar, height=1, corner_radius=0, fg_color=Theme.TRANSPARENT,
                              cursor="hand2")
        button.grid(row=0, column=column, sticky="s", padx=(0 if column == 0 else TAB_GAP, 0))

        label = ctk.CTkLabel(button, text=text, font=Theme.font(*Theme.T_TAB),
                             text_color=Theme.TXT_3, height=COUNT_H + 2)
        label.grid(row=0, column=0, padx=(TAB_PAD_X, 0 if count is not None else TAB_PAD_X),
                   pady=(TAB_PAD_TOP, TAB_PAD_BOTTOM + UNDERLINE_H))
        count_label = None
        if count is not None:
            count_label = ctk.CTkLabel(button, text=str(count), height=COUNT_H,
                                       corner_radius=COUNT_H // 2, font=Theme.font(*Theme.T_LABEL),
                                       fg_color=Theme.LINE_SOFT, text_color=Theme.TXT_2)
            count_label.grid(row=0, column=1, padx=(COUNT_GAP, TAB_PAD_X),
                             pady=(TAB_PAD_TOP, TAB_PAD_BOTTOM + UNDERLINE_H))
            self.__fit_count(count_label)

        # width=1: sin él, un CTkFrame pide 200 px de ancho y ensancha la pestaña.
        underline = ctk.CTkFrame(button, width=1, height=UNDERLINE_H, corner_radius=0, fg_color=Theme.LINE)

        tab = _Tab(key=key, builder=builder, button=button, label=label, count_label=count_label,
                   underline=underline)
        self.__tabs[key] = tab
        self.__order.append(key)
        self.__bind_tab(tab)

        if self.__selected is None:
            self.select(key)
        else:
            self.__paint(tab)

    def select(self, key: str) -> None:
        """Activa una pestaña, construyéndola si es la primera vez que se abre."""
        tab = self.__tabs.get(key)
        if tab is None or key == self.__selected:
            return
        previous = self.__tabs.get(self.__selected) if self.__selected is not None else None
        if previous is not None:
            if previous.body is not None:
                previous.body.grid_remove()
            if previous.tools is not None:
                previous.tools.grid_remove()
        self.__selected = key

        if tab.body is None:
            # Los cuerpos comparten la celda de debajo de la barra; solo se ve el de la activa.
            tab.body = ctk.CTkFrame(self, height=1, fg_color=Theme.TRANSPARENT)
            tab.body.grid(row=1, column=0, sticky="ew", pady=(BODY_PAD_TOP, 0))
            tab.body.grid_columnconfigure(0, weight=1)
            tab.tools = ctk.CTkFrame(self.__bar, height=1, fg_color=Theme.TRANSPARENT)
            tab.tools.grid(row=0, column=TOOLS_COLUMN, sticky="e", pady=(0, 6))
            tab.builder(tab.body, tab.tools)
        else:
            tab.body.grid()
            tab.tools.grid()

        for other in self.__tabs.values():
            self.__paint(other)
        if self.__on_change is not None:
            self.__on_change(key)

    @property
    def selected(self) -> Optional[str]:
        """:return: Clave de la pestaña activa."""
        return self.__selected

    def has_tab(self, key: str) -> bool:
        return key in self.__tabs

    # ------------------------------------------------------------------
    # Pintado e interacción
    # ------------------------------------------------------------------
    @staticmethod
    def __fit_count(count_label: ctk.CTkLabel) -> None:
        """Ajusta el ancho de la burbuja al número: CTkLabel no encoge por debajo de su width."""
        text_width = Theme.font(*Theme.T_LABEL).measure(count_label.cget("text"))
        count_label.configure(width=max(COUNT_H + 2, text_width + 2 * COUNT_PAD_X))

    def __paint(self, tab: _Tab) -> None:
        """Colores de una pestaña según esté activa, bajo el puntero o en reposo."""
        active = tab.key == self.__selected
        hovered = tab.key == self.__hovered
        tab.label.configure(text_color=Theme.TXT if active or hovered else Theme.TXT_3)
        tab.underline.configure(fg_color=Theme.ACCENT if active else Theme.LINE)
        tab.underline.place(relx=0, rely=1.0, y=0 if active else 1, anchor="sw", relwidth=1.0)
        if tab.count_label is not None:
            tab.count_label.configure(fg_color=Theme.ACCENT_SOFT if active else Theme.LINE_SOFT,
                                      text_color=Theme.ACCENT if active else Theme.TXT_2)

    def __bind_tab(self, tab: _Tab) -> None:
        """Ata clic y hover a cada widget de Tk de la pestaña, ya que los eventos no burbujean.

        Con el ``bind`` de Tk y no con el de CustomTkinter, que reenvía a los
        hijos internos y ataría dos veces lo que este recorrido ya visita.
        """
        def walk(widget):
            yield widget
            # El winfo_children de Tk: el de CTkFrame oculta su lienzo, que es el fondo de la pestaña.
            for child in tkinter.Misc.winfo_children(widget):
                yield from walk(child)

        for widget in walk(tab.button):
            tkinter.Misc.bind(widget, "<Button-1>", lambda _e, key=tab.key: self.select(key), "+")
            tkinter.Misc.bind(widget, "<Enter>", lambda _e, key=tab.key: self.__set_hover(key), "+")
            tkinter.Misc.bind(widget, "<Leave>", lambda _e, key=tab.key: self.__leave(key), "+")

    def __set_hover(self, key: Optional[str]) -> None:
        previous, self.__hovered = self.__hovered, key
        for changed in {previous, key} - {None}:
            if changed in self.__tabs:
                self.__paint(self.__tabs[changed])

    def __leave(self, key: str) -> None:
        """Apaga el hover solo si el puntero ha salido de verdad de la pestaña.

        Tk manda ``<Leave>`` también al pasar del marco a uno de sus hijos.
        """
        button = self.__tabs[key].button
        if not button.winfo_exists():
            return
        pointer_x, pointer_y = button.winfo_pointerxy()
        left, top = button.winfo_rootx(), button.winfo_rooty()
        if left <= pointer_x < left + button.winfo_width() and top <= pointer_y < top + button.winfo_height():
            return
        if self.__hovered == key:
            self.__set_hover(None)
