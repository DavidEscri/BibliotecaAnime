__author__ = "Jose David Escribano Orts"
__subsystem__ = "gui.components"
__module__ = "pager.py"
__version__ = "0.1"
__info__ = {"subsystem": __subsystem__, "module_name": __module__, "version": __version__}

"""Paginador: «Mostrando A-B de N» a la izquierda y los botones de página a la derecha.

Regla del diseño (``DISENO.md`` §6): **se muestra solo si hace falta**. Con
``total <= page_size`` el paginador se esconde él solo, sin que la vista tenga que
acordarse; así una pestaña con seis animes no enseña un «página 1 de 1» que no
lleva a ninguna parte.

Esconderse es ``grid_remove()`` y no ``destroy()``: conserva las opciones de
``grid`` con las que lo colocó la vista, así que volver a aparecer es un ``grid()``
sin argumentos cuando la lista crece.
"""

from typing import Callable, List, Optional, Tuple

import customtkinter as ctk

from gui.theme import Metrics, Theme


class Pager(ctk.CTkFrame):
    """Paginador de una vista.

    Uso típico::

        pager = Pager(main_window.content_frame, page_size=12, on_page=self.__go_to_page)
        pager.grid(row=3, column=0, sticky="ew", padx=Metrics.CONTENT_PAD_X)
        pager.set_total(len(animes), page=1)
    """

    #: Cuántos botones numerados caben antes de empezar a resumir con puntos
    #: suspensivos. Impar a propósito: así la página actual queda centrada.
    __MAX_PAGE_BUTTONS = 7

    def __init__(self, parent, page_size: int, on_page: Callable[[int], None], **kwargs):
        """
        :param page_size: elementos por página. **12** en las rejillas de 6
            columnas y 10 en el resto (``DISENO.md`` §6).
        :param on_page: recibe el número de página pedido, empezando en 1. La
            vista es quien repinta; el paginador no sabe qué hay debajo.
        """
        super().__init__(parent, height=1, corner_radius=0, fg_color=Theme.TRANSPARENT, **kwargs)

        self.page_size = page_size
        self.__on_page = on_page
        self.__total = 0
        self.__page = 1

        self.grid_columnconfigure(0, weight=1)

        self.__range_label = ctk.CTkLabel(
            self,
            text="",
            font=Theme.font(*Theme.T_NUM),
            text_color=Theme.TXT_3,
            anchor="w"
        )
        self.__range_label.grid(row=0, column=0, sticky="w")

        # El height=1 es el de siempre: un CTkFrame sin hijos conserva su alto por
        # defecto (200) y estiraría la fila del paginador antes de que se pinte
        # ningún botón.
        self.__buttons_frame = ctk.CTkFrame(self, height=1, fg_color=Theme.TRANSPARENT)
        self.__buttons_frame.grid(row=0, column=1, sticky="e")
        self.__buttons: List[ctk.CTkBaseClass] = []

    # ------------------------------------------------------------------
    # Estado
    # ------------------------------------------------------------------
    def page(self) -> int:
        """Página actual, empezando en 1."""
        return self.__page

    def total_pages(self) -> int:
        if self.__total <= 0:
            return 1
        return (self.__total + self.page_size - 1) // self.page_size

    def slice_bounds(self, page: Optional[int] = None) -> Tuple[int, int]:
        """Devuelve ``(inicio, fin)`` para cortar la lista de la página pedida.

        Lo expone el paginador y no cada vista para que el corte y el texto
        «Mostrando A-B de N» no puedan discrepar.
        """
        current = self.__page if page is None else page
        start = (current - 1) * self.page_size
        return start, min(start + self.page_size, self.__total)

    def set_total(self, total: int, page: int = 1) -> None:
        """Fija cuántos elementos hay y en qué página estamos. **No** llama a ``on_page``."""
        self.__total = max(0, total)
        self.__page = min(max(1, page), self.total_pages())
        self.__repaint()

    # ------------------------------------------------------------------
    # Pintado
    # ------------------------------------------------------------------
    def __repaint(self) -> None:
        if self.__total <= self.page_size:
            self.grid_remove()
            return
        self.grid()

        start, end = self.slice_bounds()
        self.__range_label.configure(text=f"Mostrando {start + 1}-{end} de {self.__total}")

        for widget in self.__buttons:
            widget.destroy()
        self.__buttons.clear()

        column = self.__add_arrow("‹", self.__page - 1, self.__page > 1, 0)
        for page_number in self.__page_numbers():
            if page_number is None:
                column = self.__add_ellipsis(column)
            else:
                column = self.__add_page_button(page_number, column)
        self.__add_arrow("›", self.__page + 1, self.__page < self.total_pages(), column)

    def __page_numbers(self) -> List[Optional[int]]:
        """Números a pintar. ``None`` es un hueco de puntos suspensivos."""
        total_pages = self.total_pages()
        if total_pages <= self.__MAX_PAGE_BUTTONS:
            return list(range(1, total_pages + 1))

        # Ventana centrada en la página actual, sin salirse por ningún extremo.
        window = self.__MAX_PAGE_BUTTONS - 4  # descuenta primera, última y dos huecos
        first = max(2, self.__page - window // 2)
        last = min(total_pages - 1, first + window - 1)
        first = max(2, last - window + 1)

        numbers: List[Optional[int]] = [1]
        if first > 2:
            numbers.append(None)
        numbers.extend(range(first, last + 1))
        if last < total_pages - 1:
            numbers.append(None)
        numbers.append(total_pages)
        return numbers

    def __add_page_button(self, page_number: int, column: int) -> int:
        is_current = page_number == self.__page
        button = ctk.CTkButton(
            self.__buttons_frame,
            text=str(page_number),
            width=30,
            height=28,
            corner_radius=Metrics.RADIUS_CONTROL,
            font=Theme.font(*Theme.T_NUM),
            fg_color=Theme.ACCENT if is_current else Theme.CARD,
            hover_color=Theme.ACCENT if is_current else Theme.CARD_HOVER,
            text_color=Theme.ACCENT_INK if is_current else Theme.TXT_2,
            border_width=0 if is_current else 1,
            border_color=Theme.LINE,
            command=(lambda: None) if is_current else (lambda p=page_number: self.__go(p))
        )
        button.grid(row=0, column=column, padx=2)
        self.__buttons.append(button)
        return column + 1

    def __add_arrow(self, text: str, target_page: int, enabled: bool, column: int) -> int:
        button = ctk.CTkButton(
            self.__buttons_frame,
            text=text,
            width=30,
            height=28,
            corner_radius=Metrics.RADIUS_CONTROL,
            font=Theme.font(*Theme.T_UI),
            fg_color=Theme.CARD,
            hover_color=Theme.CARD_HOVER,
            text_color=Theme.TXT_2 if enabled else Theme.TXT_3,
            border_width=1,
            border_color=Theme.LINE,
            state="normal" if enabled else "disabled",
            command=lambda p=target_page: self.__go(p)
        )
        button.grid(row=0, column=column, padx=2)
        self.__buttons.append(button)
        return column + 1

    def __add_ellipsis(self, column: int) -> int:
        label = ctk.CTkLabel(
            self.__buttons_frame,
            text="…",
            width=14,
            font=Theme.font(*Theme.T_UI),
            text_color=Theme.TXT_3
        )
        label.grid(row=0, column=column, padx=2)
        self.__buttons.append(label)
        return column + 1

    def __go(self, page_number: int) -> None:
        page_number = min(max(1, page_number), self.total_pages())
        if page_number == self.__page:
            return
        self.__page = page_number
        self.__repaint()
        self.__on_page(page_number)
