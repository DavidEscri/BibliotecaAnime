__author__ = "Jose David Escribano Orts"
__subsystem__ = "gui.components"
__module__ = "poster_grid.py"
__version__ = "0.1"
__info__ = {"subsystem": __subsystem__, "module_name": __module__, "version": __version__}

"""Rejilla de pósters: el componente que comparten nuevos, favoritos, finalizados y buscar.

Una celda son hasta cuatro piezas: el póster, un sello opcional superpuesto en la
esquina, el título a dos líneas y un pie opcional (el proveedor, en las vistas de
biblioteca). El número de columnas y el tamaño del póster son parámetros, así que
la rejilla de 6 de `Nuevos lanzamientos` y la de 5 de `Favoritos` son **la misma
clase con otros argumentos**: si una vista necesita una variante se añade un
parámetro, nunca una copia (`DISENO.md` §5).

Dos decisiones de construcción que conviene no deshacer:

- **Cada celda es un ``CTkFrame`` propio**, y en la rejilla ocupa **una sola fila**.
  Las vistas de hoy pintan póster y título como dos widgets sueltos en filas
  ``row*2`` y ``row*2+1`` de la rejilla del contenedor, y las de estado necesitaron
  una tercera fila para el proveedor: ``row*3``, ``row*3+1``, ``row*3+2``. Con la
  celda como marco, añadir o quitar una línea no toca ningún índice.
- ⚠️ El marco de la rejilla nace con ``height=1``. Un ``CTkFrame`` **sin hijos**
  conserva su alto por defecto (200) como tamaño pedido, así que una rejilla
  todavía vacía estiraría la fila que la contiene. En cuanto se pinta una celda
  crece hasta su contenido.
"""

from dataclasses import dataclass
from typing import Any, Callable, List, Optional, Tuple

import customtkinter as ctk

from gui.theme import ColorToken, Metrics, Theme
from utils.utils import load_rounded_image


@dataclass
class PosterItem:
    """Una celda de la rejilla.

    :param key: lo que recibe ``on_click``. Normalmente el ``anime_id``.
    :param title: título del anime, a dos líneas.
    :param poster_path: ruta del JPG cacheado. Si no existe, se pinta el
        placeholder gris de ``load_rounded_image()``.
    :param badge: texto del sello superpuesto (el «Finalizado» de la fase 6, el
        «Ya lo tienes» de la 7). ``None`` no pinta nada.
    :param badge_colors: ``(color_de_texto, color_de_fondo)`` del sello, con los
        pares de ``Theme``. Sin él, el sello usa el acento.
    :param footer: línea de apoyo bajo el título (el proveedor). ``None`` la omite
        y la celda queda más baja.
    """
    key: Any
    title: str
    poster_path: Optional[str] = None
    badge: Optional[str] = None
    badge_colors: Optional[Tuple[ColorToken, ColorToken]] = None
    footer: Optional[str] = None


class PosterGrid(ctk.CTkFrame):
    """Rejilla de pósters de N columnas.

    Uso típico::

        grid = PosterGrid(main_window.content_frame, columns=6, on_click=self.__on_click)
        grid.grid(row=2, column=0, sticky="w", padx=(PosterGrid.OUTER_PAD_X, 0))
        grid.show([PosterItem(key=a.id, title=a.title, poster_path=...) for a in animes])
    """

    #: Padding izquierdo con el que la vista debe colocar la rejilla para que el
    #: borde del primer póster caiga en los 28 px de margen del diseño. La celda
    #: ya aporta media separación por lado, así que hay que descontarla.
    OUTER_PAD_X: int = Metrics.CONTENT_PAD_X - Metrics.GRID_GAP_X // 2

    #: Alto reservado para el título. Dos líneas de `T_UI` más el interlineado:
    #: fijarlo es lo que mantiene alineadas las celdas de una misma fila cuando
    #: unos títulos ocupan una línea y otros dos.
    TITLE_H: int = 38

    def __init__(self, parent, columns: int = 6,
                 poster_size: Tuple[int, int] = Metrics.GRID6_POSTER,
                 on_click: Optional[Callable[[Any], None]] = None, **kwargs):
        """
        :param parent: normalmente ``main_window.content_frame``.
        :param columns: número de columnas. 6 en nuevos, finalizados y buscar; 5
            en favoritos.
        :param poster_size: tamaño **pintado** del póster. La caché en disco está
            a 248 x 372 y se reduce desde ahí.
        :param on_click: recibe el ``key`` del ítem pulsado.
        """
        super().__init__(parent, height=1, corner_radius=0, fg_color=Theme.TRANSPARENT, **kwargs)

        self.columns = columns
        self.poster_size = poster_size
        self.__on_click = on_click
        #: Las imágenes hay que guardarlas: Tk no mantiene referencia a la imagen
        #: de un widget y el recolector se la llevaría, dejando la celda en blanco.
        self.__images: List[ctk.CTkImage] = []

    # ------------------------------------------------------------------
    # Pintado
    # ------------------------------------------------------------------
    def show(self, items: List[PosterItem]) -> None:
        """Repinta la rejilla entera con estos ítems. Sustituye a los anteriores."""
        self.clear()
        for index, item in enumerate(items):
            self.__build_cell(item, index // self.columns, index % self.columns)

    def clear(self) -> None:
        """Destruye las celdas y suelta las imágenes."""
        for widget in self.winfo_children():
            widget.destroy()
        self.__images.clear()

    def __build_cell(self, item: PosterItem, row: int, column: int) -> None:
        gap_x = Metrics.GRID_GAP_X // 2
        cell = ctk.CTkFrame(self, fg_color=Theme.TRANSPARENT)
        cell.grid(row=row, column=column, padx=gap_x, pady=(0, Metrics.GRID_GAP_Y), sticky="n")
        cell.grid_columnconfigure(0, minsize=self.poster_size[0])

        image = load_rounded_image(item.poster_path or "", self.poster_size, Metrics.RADIUS_POSTER)
        self.__images.append(image)
        poster_label = ctk.CTkLabel(cell, text="", image=image)
        poster_label.grid(row=0, column=0)

        if item.badge:
            text_color, fg_color = item.badge_colors or (Theme.ACCENT_INK, Theme.ACCENT)
            badge_h = 20
            badge_label = ctk.CTkLabel(
                poster_label,
                text=item.badge,
                height=badge_h,
                corner_radius=Metrics.pill_radius(badge_h),
                font=Theme.font(*Theme.T_META),
                fg_color=fg_color,
                text_color=text_color
            )
            # place() y no grid: el sello se superpone al póster, no ocupa sitio.
            badge_label.place(relx=1.0, rely=0.0, x=-8, y=8, anchor="ne")

        # ellipsize() y no solo wraplength: wraplength envuelve todas las líneas
        # que haga falta y el CTkLabel crece por encima de su `height`, así que un
        # título de tres líneas desnivelaba la fila entera.
        title_font = Theme.font(*Theme.T_UI)
        title_label = ctk.CTkLabel(
            cell,
            text=Theme.ellipsize(item.title, title_font, self.poster_size[0], 2),
            font=title_font,
            text_color=Theme.TXT_2,
            wraplength=self.poster_size[0],
            height=self.TITLE_H,
            justify="center",
            anchor="n"
        )
        title_label.grid(row=1, column=0, sticky="ew", pady=(8, 0))

        clickable = [cell, poster_label, title_label]
        if item.footer:
            footer_label = ctk.CTkLabel(
                cell,
                text=item.footer,
                font=Theme.font(*Theme.T_META),
                text_color=Theme.TXT_3,
                anchor="n"
            )
            footer_label.grid(row=2, column=0, sticky="ew")
            clickable.append(footer_label)

        if self.__on_click is None:
            return
        # Los eventos de Tk no burbujean desde los hijos: hay que atar el clic a
        # cada pieza de la celda, no solo al marco.
        for widget in clickable:
            widget.bind("<Button-1>", lambda _event, key=item.key: self.__on_click(key))
            widget.configure(cursor="hand2")
