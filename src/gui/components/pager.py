__author__ = "Jose David Escribano Orts"
__subsystem__ = "gui.components"
__module__ = "pager.py"
__version__ = "0.3"
__info__ = {"subsystem": __subsystem__, "module_name": __module__, "version": __version__}

"""Paginador: «Mostrando A-B de N» a la izquierda y los botones de página a la derecha.

Se muestra solo si hace falta: con ``total <= page_size`` se esconde él solo
con ``grid_remove()`` (no ``destroy()``, para conservar las opciones de grid).

Hay dos formas de decirle cuántas páginas hay, y no son intercambiables:

- ``set_total(n)`` — la vista tiene la lista entera en memoria y el paginador
  la trocea él mismo con ``slice_bounds()``. Su ``page_size`` no es constante:
  las rejillas lo derivan del número de columnas que quepan (``set_page_size()``).
- ``set_pages(u, p)`` — quien trocea es el proveedor: la búsqueda pide una
  página y el sitio devuelve esos resultados y cuál es la última página. El
  total no se conoce, así que el texto pasa a ser «Página P de U».
"""

from typing import Callable, List, Optional, Tuple

import customtkinter as ctk

from gui.theme import Metrics, Theme


class Pager(ctk.CTkFrame):
    """Paginador de una vista."""

    #: Cuántos botones numerados caben antes de empezar a resumir con puntos
    #: suspensivos. Impar a propósito: así la página actual queda centrada.
    __MAX_PAGE_BUTTONS = 7

    def __init__(self, parent, page_size: int, on_page: Callable[[int], None], **kwargs):
        """Construye el paginador.

        :param page_size: Elementos por página.
        :param on_page: Recibe el número de página pedido, empezando en 1; la
            vista es quien repinta, el paginador no sabe qué hay debajo.
        """
        super().__init__(parent, height=1, corner_radius=0, fg_color=Theme.TRANSPARENT, **kwargs)

        self.page_size = page_size
        self.__on_page = on_page
        self.__total = 0
        self.__page = 1
        #: Número de páginas cuando las cuenta el proveedor. ``None`` es el modo
        #: normal, en el que se deducen de ``__total`` y ``page_size``.
        self.__provider_pages: Optional[int] = None

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
        """:return: Número total de páginas en el modo actual."""
        if self.__provider_pages is not None:
            return self.__provider_pages
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
        """Fija cuántos elementos hay y en qué página estamos; no llama a on_page.

        Modo normal: la vista tiene la lista entera y el corte lo hace slice_bounds().

        :param total: Número total de elementos.
        :param page: Página a mostrar.
        """
        self.__provider_pages = None
        self.__total = max(0, total)
        self.__page = min(max(1, page), self.total_pages())
        self.__repaint()

    def set_pages(self, total_pages: int, page: int = 1) -> None:
        """Fija las páginas cuando las cuenta el proveedor; no llama a on_page.

        Lo usa «Buscar»: cada página es una petición al sitio, así que aquí no
        hay lista que trocear y el total de resultados no se conoce.

        :param total_pages: Última página que dice el proveedor.
        :param page: Página que se está viendo.
        """
        self.__provider_pages = max(1, total_pages)
        self.__total = 0
        self.__page = min(max(1, page), self.__provider_pages)
        self.__repaint()

    def set_page_size(self, page_size: int) -> None:
        """Cambia cuántos elementos entran en una página; no llama a on_page.

        Se conserva el primer elemento que se estaba viendo, no el número de
        página, para no saltar a un anime que no estaba en pantalla. Solo
        tiene efecto en el modo set_total(); en set_pages() solo guarda el valor.

        :param page_size: Nuevos elementos por página.
        """
        page_size = max(1, page_size)
        if page_size == self.page_size:
            return
        if self.__provider_pages is not None:
            self.page_size = page_size
            return
        first_index = (self.__page - 1) * self.page_size
        self.page_size = page_size
        self.__page = min(max(1, first_index // page_size + 1), self.total_pages())
        self.__repaint()

    # ------------------------------------------------------------------
    # Pintado
    # ------------------------------------------------------------------
    def __repaint(self) -> None:
        # Con una sola página no hay nada que paginar. Sirve para los dos modos:
        # una lista más corta que la página da total_pages() == 1 igual que un
        # proveedor que responde que su última página es la primera.
        if self.total_pages() <= 1:
            self.grid_remove()
            return
        self.grid()

        if self.__provider_pages is not None:
            self.__range_label.configure(text=f"Página {self.__page} de {self.__provider_pages}")
        else:
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
        """Pinta el botón de una página numerada y devuelve la siguiente columna libre."""
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
        """Pinta la flecha de anterior/siguiente y devuelve la siguiente columna libre."""
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
        """Pinta los puntos suspensivos y devuelve la siguiente columna libre."""
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
        """Cambia de página, repinta y avisa a on_page."""
        page_number = min(max(1, page_number), self.total_pages())
        if page_number == self.__page:
            return
        self.__page = page_number
        self.__repaint()
        self.__on_page(page_number)
