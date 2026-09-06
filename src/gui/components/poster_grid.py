__author__ = "Jose David Escribano Orts"
__subsystem__ = "gui.components"
__module__ = "poster_grid.py"
__version__ = "0.4"
__info__ = {"subsystem": __subsystem__, "module_name": __module__, "version": __version__}

"""Rejilla de pósters: el componente que comparten nuevos, favoritos, finalizados y buscar.

Una celda son hasta cinco piezas: el póster, un sello opcional superpuesto en la
esquina, el título a dos líneas, una **fila libre** que construye la vista
(las estrellas de «Favoritos») y un pie opcional (el proveedor, en las vistas de
biblioteca). El tamaño del póster es un parámetro, así que la rejilla de
`Nuevos lanzamientos` y la de `Favoritos` son **la misma clase con otros
argumentos**: si una vista necesita una variante se añade un parámetro, nunca una
copia (`DISENO.md` §5).

El **sello** es de la rejilla, no de ninguna vista: llega desde fuera con su
texto, su glifo y —si hace falta— sus colores, así que el «12 / 12» de
finalizados y el «Viendo» de los resultados de búsqueda son el mismo widget con
otros argumentos. Por defecto se pinta con la superficie oscura de ``BADGE_BG``,
que es lo que lo hace legible sobre cualquier carátula en los dos temas.

🔴 **El número de columnas se calcula del ancho disponible** (desde el
2026-09-02). Hasta entonces era un número fijo —6 y 5— y la vista la colocaba con
``sticky="w"``, así que maximizar la ventana no añadía columnas: dejaba una franja
muerta de casi 500 px a la derecha. Ahora:

- ``columns_that_fit()`` divide el ancho de la rejilla entre ``póster + hueco``.
  A 1440 devuelve exactamente los 6 y 5 del diseño —la ventana por defecto se ve
  igual que antes—; a 1920 maximizado devuelve 8 y 7.
- Las columnas llevan ``weight=1`` y el mismo grupo ``uniform``, y la celda va con
  ``sticky="n"``: lo que sobra del reparto entero se distribuye a partes iguales
  entre todas y cada celda queda centrada en la suya. Es el equivalente en Tk de
  ``repeat(auto-fill, minmax(póster, 1fr))``.
- 🔴 Por eso **la vista tiene que colocarla con ``sticky="ew"``**. Con ``sticky="w"``
  la rejilla mide su propio contenido, así que el cálculo sería un punto fijo que
  nunca cambiaría de columnas y el arreglo entero no haría nada.
- ⚠️ Los pesos de columna **sobreviven a destruir las celdas** (trampa 32), así que
  al bajar de 8 a 3 columnas hay que quitarles el peso a las cinco que sobran o
  seguirían reclamando su parte del ancho.
- El ``<Configure>`` va con ``add="+"``: ``CTkBaseClass`` ya tiene el suyo atado y
  un ``bind()`` sin ``add`` lo sustituiría (trampa 40).

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

from gui.theme import Metrics, Theme
from utils.utils import load_rounded_image


@dataclass
class PosterItem:
    """Una celda de la rejilla.

    :param key: lo que recibe ``on_click``. Normalmente el ``anime_id``.
    :param title: título del anime, a dos líneas.
    :param poster_path: ruta del JPG cacheado. Si no existe, se pinta el
        placeholder gris de ``load_rounded_image()``.
    :param badge: texto del sello superpuesto (el «12 / 12» de finalizados, el
        «Ya lo tienes» de la fase 7). ``None`` no pinta nada.
    :param badge_icon: glifo que va delante de ese texto, normalmente el de
        ``StatusPill.icon()``. El hueco que lo separa del texto viene dentro del
        propio dibujo. ``None`` deja el sello con texto solo.

    El sello es **siempre** el del diseño: superficie oscura opaca y texto
    blanco, con el color del estado únicamente en el glifo. No se puede elegir
    otro par de colores, y es a propósito: va sobre la carátula, no sobre el
    fondo de la aplicación, y los pares pastel de ``StatusPill`` no se leen sobre
    un póster claro. «Favoritos» lo intentó hasta el paso 9.2 y era justo el
    punto que el repaso de claro/oscuro tenía que corregir.
    :param footer: línea de apoyo bajo el título (el proveedor). ``None`` la omite
        y la celda queda más baja.
    :param data: lo que la vista necesite recuperar en ``extra_builder`` sin
        volver a buscarlo por ``key`` (en «Favoritos», el ``AnimeRecord``). La
        rejilla no lo mira: solo lo transporta.
    """
    key: Any
    title: str
    poster_path: Optional[str] = None
    badge: Optional[str] = None
    badge_icon: Optional[ctk.CTkImage] = None
    footer: Optional[str] = None
    data: Any = None


class PosterGrid(ctk.CTkFrame):
    """Rejilla de pósters que ajusta sus columnas al ancho disponible.

    Uso típico::

        grid = PosterGrid(main_window.content_frame, columns=6, on_click=self.__on_click)
        grid.grid(row=2, column=0, sticky="ew", padx=(PosterGrid.OUTER_PAD_X, 0))
        grid.show([PosterItem(key=a.id, title=a.title, poster_path=...) for a in animes])
    """

    #: Padding izquierdo con el que la vista debe colocar la rejilla para que el
    #: borde del primer póster caiga en los 28 px de margen del diseño. La celda
    #: ya aporta media separación por lado, así que hay que descontarla.
    OUTER_PAD_X: int = Metrics.CONTENT_PAD_X - Metrics.GRID_GAP_X // 2

    #: Alto del sello superpuesto. El radio es la mitad (píldora = alto / 2).
    BADGE_H: int = 20

    #: Separación del sello a las dos esquinas del póster. Arriba a la
    #: **izquierda**, que es donde lo pone el diseño: es la esquina por la que se
    #: empieza a leer y la que menos tapa de una carátula.
    BADGE_INSET: int = 8

    #: Alto reservado para el título. Dos líneas de `T_UI` más el interlineado:
    #: fijarlo es lo que mantiene alineadas las celdas de una misma fila cuando
    #: unos títulos ocupan una línea y otros dos.
    TITLE_H: int = 38

    #: Grupo ``uniform`` de Tk al que se apuntan todas las columnas para que
    #: repartan el ancho sobrante a partes iguales. El nombre solo tiene que ser
    #: único dentro de este contenedor.
    UNIFORM_GROUP: str = "poster"

    #: Espera antes de repintar tras un cambio de ancho, en milisegundos.
    #: ✅ Medido: repintar 16 celdas cuesta ~350 ms **en el hilo de la interfaz**,
    #: porque cada una abre su JPG y lo reescala con PIL. Arrastrar el borde de la
    #: ventana justo por encima de un límite de columna repintaría a cada tirón y
    #: se notaría. Con esta espera un arrastre entero cuesta **un** repintado, el
    #: de cuando el usuario suelta, y 75 ms no se ven. Solo afecta al
    #: redimensionado: entrar en una vista pinta de inmediato.
    RELAYOUT_DELAY_MS: int = 75

    def __init__(self, parent, columns: int = 6,
                 poster_size: Tuple[int, int] = Metrics.GRID6_POSTER,
                 on_click: Optional[Callable[[Any], None]] = None,
                 extra_builder: Optional[Callable[[ctk.CTkFrame, PosterItem],
                                                  Optional[ctk.CTkBaseClass]]] = None,
                 on_columns_changed: Optional[Callable[[int], None]] = None,
                 **kwargs):
        """
        :param parent: normalmente ``main_window.content_frame``.
        :param columns: columnas **de referencia**, las que el diseño pide a 1440
            (6 en nuevos, finalizados y buscar; 5 en favoritos). Ya no fija el
            número real —ese sale del ancho—, pero se sigue usando mientras la
            rejilla todavía no se puede medir, y de él sale el tamaño de página
            inicial de la vista.
        :param poster_size: tamaño **pintado** del póster, y con él la anchura de
            columna a partir de la cual se decide cuántas caben. La caché en disco
            está a 248 x 372 y se reduce desde ahí.
        :param on_click: recibe el ``key`` del ítem pulsado.
        :param extra_builder: construye la fila libre que va bajo el título.
            Recibe la celda (que es su padre) y el ítem, y devuelve el widget ya
            creado —la rejilla lo coloca— o ``None`` para no poner nada en esa
            celda. Es lo que usa «Favoritos» para las estrellas.

            ⚠️ Ese widget **no hereda el clic de la celda**: los eventos de Tk no
            burbujean, así que un control pulsable ahí dentro (las estrellas) se
            queda con su clic y no abre la ficha. Es justo lo que se busca.
        :param on_columns_changed: aviso de que el ancho da ahora para otro número
            de columnas. **Quien lo pasa se compromete a repintar**: la rejilla no
            vuelve a pintar por su cuenta, porque en las vistas paginadas el número
            de columnas cambia también el tamaño de página y pintar aquí sería
            pintar dos veces. Sin él, la rejilla se recoloca sola con los últimos
            ítems que recibió, que es lo que necesita «Buscar» (allí quien pagina
            es el proveedor, y qué animes trae una página no depende del ancho).
        """
        super().__init__(parent, height=1, corner_radius=0, fg_color=Theme.TRANSPARENT, **kwargs)

        #: Columnas del diseño. Solo se usan cuando no hay ancho que medir.
        self.reference_columns = max(1, columns)
        #: Columnas que se están pintando ahora mismo.
        self.columns = self.reference_columns
        self.poster_size = poster_size
        self.__on_click = on_click
        self.__extra_builder = extra_builder
        self.__on_columns_changed = on_columns_changed
        #: Lo último que se pintó. Hace falta para recolocarlo al cambiar el ancho
        #: sin obligar a la vista a reconstruir los ítems.
        self.__items: List[PosterItem] = []
        #: Cuántas columnas llevan peso puesto. Los pesos sobreviven a destruir las
        #: celdas, así que hay que saber a cuáles quitárselo al encoger.
        self.__weighted_columns: int = 0
        #: Repintado pendiente por un cambio de ancho, o None si no hay ninguno.
        self.__relayout_job: Optional[str] = None
        #: Las imágenes hay que guardarlas: Tk no mantiene referencia a la imagen
        #: de un widget y el recolector se la llevaría, dejando la celda en blanco.
        self.__images: List[ctk.CTkImage] = []

        # add="+" y no un bind a secas: CTkBaseClass ya tiene atado su propio
        # <Configure> (mantiene _current_width / _current_height) y sustituirlo es
        # la trampa 40.
        self.bind("<Configure>", self.__on_configure, add="+")

        # Se resuelve ya, antes de que la vista siga construyendo: el paginador se
        # crea justo después y su tamaño de página sale de estas columnas.
        self.columns = self.columns_that_fit()

    # ------------------------------------------------------------------
    # Columnas
    # ------------------------------------------------------------------
    def columns_that_fit(self) -> int:
        """Cuántas columnas caben en el ancho que la rejilla tiene ahora mismo.

        Una columna ocupa el póster más el hueco entre pósters. El margen
        izquierdo del contenido no entra en la cuenta: la vista coloca la rejilla
        con ``padx=(OUTER_PAD_X, 0)`` y ``winfo_width()`` ya lo deja fuera.

        Nunca devuelve menos de 1: con la ventana muy estrecha es preferible que
        la rejilla se salga por la derecha —como ya hacía— a que no pinte nada.
        """
        available = self.__available_width()
        if available <= 0:
            return self.reference_columns
        return max(1, available // (self.poster_size[0] + Metrics.GRID_GAP_X))

    def __available_width(self) -> int:
        """Ancho útil, o 0 si todavía no hay nada que medir.

        Mientras el widget no está mapeado ``winfo_width()`` vale 1. En ese caso el
        ancho sale del contenedor menos el hueco con el que esta misma clase obliga
        a colocarla: así una vista construida con la ventana ya maximizada nace con
        sus columnas en vez de pintar seis y repintar ocho acto seguido.
        """
        width = self.winfo_width()
        if width > 1:
            return width
        parent_width = self.master.winfo_width() if self.master is not None else 1
        if parent_width <= 1:
            return 0
        return parent_width - self.OUTER_PAD_X

    def __on_configure(self, _event=None) -> None:
        """Anota que hay que repintar, pero solo si cambia el número de columnas.

        Redimensionar la ventana dispara decenas de ``<Configure>``. Filtrar por
        columnas descarta casi todos —el reparto del ancho sobrante lo resuelve Tk
        solo, con los pesos— y la espera de ``RELAYOUT_DELAY_MS`` junta los que
        quedan cuando el arrastre cruza un límite de columna.
        """
        if not self.winfo_exists():
            return
        if self.columns_that_fit() == self.columns:
            return
        if self.__relayout_job is not None:
            self.after_cancel(self.__relayout_job)
        self.__relayout_job = self.after(self.RELAYOUT_DELAY_MS, self.__relayout)

    def __relayout(self) -> None:
        """Repinta con el número de columnas que quepa ahora. Va tras la espera."""
        self.__relayout_job = None
        # La rejilla puede haberse destruido durante la espera (otra vista). Un
        # `after` no se cancela solo al destruir el widget: pintar aquí es lo que
        # revienta con `invalid command name ...!ctkcanvas`.
        if not self.winfo_exists():
            return
        columns = self.columns_that_fit()
        if columns == self.columns:
            return
        self.columns = columns
        if self.__on_columns_changed is not None:
            # Quien puso el contenido es quien lo repinta (ver el constructor).
            self.__on_columns_changed(columns)
            return
        self.__render(self.__items)

    def __configure_columns(self, columns: int) -> None:
        """Da peso a las columnas en uso y se lo quita a las que dejaron de estarlo."""
        for column in range(columns):
            self.grid_columnconfigure(column, weight=1, uniform=self.UNIFORM_GROUP)
        # ⚠️ trampa 32: la configuración de rejilla sobrevive a destruir los hijos, y
        # una columna con peso y sin widgets sigue reclamando su parte del ancho.
        for column in range(columns, self.__weighted_columns):
            self.grid_columnconfigure(column, weight=0, uniform="")
        self.__weighted_columns = columns

    # ------------------------------------------------------------------
    # Pintado
    # ------------------------------------------------------------------
    def show(self, items: List[PosterItem]) -> None:
        """Repinta la rejilla entera con estos ítems. Sustituye a los anteriores."""
        self.columns = self.columns_that_fit()
        self.__render(items)

    def clear(self) -> None:
        """Destruye las celdas y suelta las imágenes."""
        self.__clear_cells()
        self.__items = []

    def __render(self, items: List[PosterItem]) -> None:
        self.__clear_cells()
        self.__items = items
        self.__configure_columns(self.columns)
        for index, item in enumerate(items):
            self.__build_cell(item, index // self.columns, index % self.columns)

    def __clear_cells(self) -> None:
        # winfo_children() de un CTkFrame no incluye su canvas interno —CustomTkinter
        # lo filtra—, así que esto destruye las celdas y nada más. Si lo incluyera se
        # llevaría por delante el <Configure> de arriba, que va atado a ese canvas.
        for widget in self.winfo_children():
            widget.destroy()
        self.__images.clear()

    def __build_cell(self, item: PosterItem, row: int, column: int) -> None:
        gap_x = Metrics.GRID_GAP_X // 2
        cell = ctk.CTkFrame(self, fg_color=Theme.TRANSPARENT)
        # sticky="n" y no "nw": con las columnas repartiéndose el ancho sobrante,
        # dejar la celda centrada en la suya es lo que convierte ese sobrante en
        # huecos iguales en vez de acumularlo entero al final de la fila.
        cell.grid(row=row, column=column, padx=gap_x, pady=(0, Metrics.GRID_GAP_Y), sticky="n")
        cell.grid_columnconfigure(0, minsize=self.poster_size[0])

        image = load_rounded_image(item.poster_path or "", self.poster_size, Metrics.RADIUS_POSTER)
        self.__images.append(image)
        poster_label = ctk.CTkLabel(cell, text="", image=image)
        poster_label.grid(row=0, column=0)

        if item.badge:
            badge_label = ctk.CTkLabel(
                poster_label,
                text=item.badge,
                image=item.badge_icon,
                # Con imagen y texto a la vez hay que decir dónde va cada uno:
                # por defecto CTkLabel los superpone (compound="center") y el
                # glifo saldría debajo de la cifra.
                compound="left",
                height=self.BADGE_H,
                corner_radius=Metrics.pill_radius(self.BADGE_H),
                font=Theme.font(*Theme.T_META),
                fg_color=Theme.BADGE_BG,
                text_color=Theme.BADGE_INK
            )
            if item.badge_icon is not None:
                self.__images.append(item.badge_icon)
            # place() y no grid: el sello se superpone al póster, no ocupa sitio.
            # Mezclar los dos gestores en el mismo contenedor es lo que produce
            # widgets que no aparecen o que se comen a sus hermanos.
            badge_label.place(relx=0.0, rely=0.0, x=self.BADGE_INSET, y=self.BADGE_INSET,
                              anchor="nw")

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

        # La fila libre y el pie se numeran sobre la marcha: si una vista no pone
        # fila libre, el pie sube a la fila 2 y la celda no deja un hueco vacío.
        next_row = 2
        if self.__extra_builder is not None:
            extra_widget = self.__extra_builder(cell, item)
            if extra_widget is not None:
                extra_widget.grid(row=next_row, column=0, pady=(7, 0))
                next_row += 1

        if item.footer:
            footer_label = ctk.CTkLabel(
                cell,
                text=item.footer,
                font=Theme.font(*Theme.T_META),
                text_color=Theme.TXT_3,
                anchor="n"
            )
            footer_label.grid(row=next_row, column=0, sticky="ew", pady=(4, 0))
            clickable.append(footer_label)

        if self.__on_click is None:
            return
        # Los eventos de Tk no burbujean desde los hijos: hay que atar el clic a
        # cada pieza de la celda, no solo al marco.
        for widget in clickable:
            widget.bind("<Button-1>", lambda _event, key=item.key: self.__on_click(key))
            widget.configure(cursor="hand2")
