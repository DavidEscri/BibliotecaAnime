__author__ = "Jose David Escribano Orts"
__subsystem__ = "gui.components"
__module__ = "empty_state.py"
__version__ = "0.1"
__info__ = {"subsystem": __subsystem__, "module_name": __module__, "version": __version__}

"""Estado vacío de una vista: icono, una frase y una acción.

Sustituye al ``CTkLabel`` suelto que cada vista pintaba por su cuenta. Aparte de
unificar el aspecto, resuelve lo que le faltaba a aquellos mensajes: se quedaban
en describir el hueco («Todavía no tienes favoritos») sin ofrecer la salida, así
que la única forma de llenar la pestaña era adivinar por dónde se empieza.

🔴 **Un estado vacío no puede mentir sobre su causa.** No es lo mismo una
biblioteca vacía —que es normal y se llena usando la aplicación— que un proveedor
que no ha respondido, que no es culpa de nadie y no se arregla marcando animes.
De ahí que la portada tenga su propio texto y su propio icono, y que su acción
sea **reintentar** y no «ve a marcar algo».

⚠️ **Y tampoco puede prometer una salida que no existe.** «Prueba con otro
proveedor» sería lo natural cuando una búsqueda no devuelve nada, pero en esta
aplicación el gestor de proveedores **ya los ha probado todos**:
``call_with_fallback()`` recorre el resto del registro cuando el elegido falla *o
devuelve vacío*. Si la rejilla sale vacía es que ninguno lo tiene, y un botón que
repite lo que la aplicación acaba de hacer sola es peor que ningún botón. Por eso
«Buscar» propone lo único que sí cambia el resultado: soltar lo que estreche la
consulta.

El icono se dibuja con PIL en tiempo de ejecución, como las estrellas de la
calificación, el pin del proveedor y los glifos de ``StatusPill``: no depende de
que el sistema tenga una fuente concreta, sale exacto a cualquier tamaño y
—a diferencia de los iconos de la barra lateral— **es nuestro**, así que no
arrastra la deuda B11. Las cuatro vistas de biblioteca no necesitan dibujo nuevo:
reutilizan el glifo de su propio estado (``StatusPill.icon()``), que es además el
que ya llevan sus sellos.
"""

from typing import Callable, Dict, Optional, Tuple

import customtkinter as ctk
from PIL import Image, ImageDraw

from gui.theme import ColorToken, Metrics, Theme

#: Lado del icono del estado vacío.
ICON_SIZE = 44

#: Factor de supermuestreo del dibujo. Mismo motivo que en ``StatusPill``: un
#: trazo curvo o diagonal sin antialias sale dentado.
_SUPERSAMPLE = 8

#: Pixel completamente transparente. Se usa para **borrar**: ``ImageDraw`` escribe
#: los valores tal cual sobre una imagen RGBA, así que pintar con alfa 0 abre un
#: hueco en lo que ya hubiera debajo. Es lo que separa la barra diagonal del
#: cuerpo de la nube sin recortar polígonos a mano.
_ERASE = (0, 0, 0, 0)


def _cloud_off_glyph(draw: ImageDraw.ImageDraw, size: float, color: str) -> None:
    """Una nube tachada: «el sitio no ha respondido».

    La nube va rellena y no en contorno porque un contorno de dos píxeles
    reducido con LANCZOS se queda en un gris lavado, y este icono tiene que
    leerse antes que el texto que hay debajo.
    """
    # Cuerpo: tres círculos y una base recta que los cose por abajo.
    draw.ellipse([size * 0.06, size * 0.42, size * 0.42, size * 0.78], fill=color)
    draw.ellipse([size * 0.26, size * 0.24, size * 0.68, size * 0.66], fill=color)
    draw.ellipse([size * 0.58, size * 0.40, size * 0.94, size * 0.76], fill=color)
    draw.rectangle([size * 0.24, size * 0.58, size * 0.76, size * 0.78], fill=color)

    # La barra: primero se abre un canal transparente y dentro se dibuja el
    # trazo, más fino. Sin el canal, la barra se funde con la nube y no se ve.
    channel = max(2, int(size * 0.20))
    stroke = max(1, int(size * 0.10))
    ends = [(size * 0.14, size * 0.86), (size * 0.86, size * 0.14)]
    draw.line(ends, fill=_ERASE, width=channel)
    draw.line(ends, fill=color, width=stroke)
    # PIL no tiene extremos redondeados: se rematan con un círculo del ancho del
    # trazo, o los dos cabos de la barra salen cortados en recto.
    radius = stroke / 2
    for x, y in ends:
        draw.ellipse([x - radius, y - radius, x + radius, y + radius], fill=color)


def _magnifier_glyph(draw: ImageDraw.ImageDraw, size: float, color: str) -> None:
    """Una lupa: «no hay nada que enseñar para lo que has pedido»."""
    stroke = max(1, int(size * 0.09))
    draw.ellipse([size * 0.10, size * 0.10, size * 0.68, size * 0.68],
                 outline=color, width=stroke)
    handle = [(size * 0.63, size * 0.63), (size * 0.90, size * 0.90)]
    draw.line(handle, fill=color, width=stroke)
    radius = stroke / 2
    for x, y in handle:
        draw.ellipse([x - radius, y - radius, x + radius, y + radius], fill=color)


#: Cómo se dibuja cada icono propio de este módulo. Los de las cuatro vistas de
#: biblioteca no están aquí: salen de ``StatusPill.icon()``.
_GLYPHS: Dict[str, Callable[[ImageDraw.ImageDraw, float, str], None]] = {
    "offline": _cloud_off_glyph,
    "search": _magnifier_glyph,
}

#: Iconos ya construidos, indexados por (nombre, tamaño, color).
_ICON_CACHE: Dict[Tuple[str, int, ColorToken], ctk.CTkImage] = {}


def glyph(name: str, size: int = ICON_SIZE,
          color: ColorToken = Theme.TXT_3) -> Optional[ctk.CTkImage]:
    """Icono de estado vacío propio de este módulo.

    Se dibuja **dos veces**, una por tema, y del cambio de apariencia se encarga
    CustomTkinter: va sobre el fondo de la aplicación, no sobre una carátula.

    :param name: ``"offline"`` o ``"search"``.
    :param size: lado del dibujo, en píxeles.
    :param color: par ``(claro, oscuro)`` con el que teñirlo.
    :return: el icono, o ``None`` si el nombre no existe. Quien lo pinte tiene
        que tolerarlo: un ``EmptyState`` sin icono sale con el texto solo.
    """
    draw_glyph = _GLYPHS.get(name)
    if draw_glyph is None:
        return None

    key = (name, size, color)
    cached = _ICON_CACHE.get(key)
    if cached is not None:
        return cached

    light_glyph, dark_glyph = (_draw(draw_glyph, size, tone) for tone in color)
    image = ctk.CTkImage(light_image=light_glyph, dark_image=dark_glyph, size=(size, size))
    _ICON_CACHE[key] = image
    return image


def _draw(draw_glyph: Callable[[ImageDraw.ImageDraw, float, str], None],
          size: int, color: str) -> Image.Image:
    """Dibuja un icono supermuestreado y lo reduce al tamaño pedido."""
    big = size * _SUPERSAMPLE
    canvas = Image.new("RGBA", (big, big), _ERASE)
    draw_glyph(ImageDraw.Draw(canvas), big, color)
    return canvas.resize((size, size), Image.LANCZOS)


class EmptyState(ctk.CTkFrame):
    """El hueco de una vista, explicado y con una salida.

    Uso típico desde una vista::

        empty = EmptyState(
            content,
            "No tienes nada en la cola",
            icon=StatusPill.icon(AnimeStatus.PENDING, ICON_SIZE, Theme.TXT_3, gap=0),
            hint="Marca un anime como «Pendiente» desde su ficha y aparecerá aquí.",
            action_text="Buscar un anime",
            on_action=lambda: main_window.navigate_to("Buscar")
        )
        empty.grid(row=1, column=0, pady=(60, 0))

    Se coloca centrado porque la columna 0 del ``content_frame`` lleva peso, que
    es como iba el ``CTkLabel`` al que sustituye.
    """

    #: Alto del botón de acción. Es el de un control de una línea, no el de los
    #: botones de estado de la ficha: aquí no hay cuatro en fila que alinear.
    ACTION_H: int = 36

    def __init__(self, parent, message: str, *,
                 icon: Optional[ctk.CTkImage] = None,
                 hint: Optional[str] = None,
                 action_text: Optional[str] = None,
                 on_action: Optional[Callable[[], None]] = None,
                 **kwargs):
        """
        :param message: la frase. Dice **qué** pasa, en una línea.
        :param icon: icono ya construido, de ``glyph()`` o de ``StatusPill.icon()``.
            ``None`` lo omite.
        :param hint: línea de apoyo opcional, en ``TXT_3``. Dice **por qué** pasa
            o **cómo** se llena el hueco.
        :param action_text: texto del botón. Sin él —o sin ``on_action``— no hay
            botón: es preferible a uno que no lleve a ninguna parte.
        :param on_action: qué hace el botón.
        """
        super().__init__(parent, corner_radius=0, fg_color=Theme.TRANSPARENT, **kwargs)
        self.grid_columnconfigure(0, weight=1)

        row = 0
        if icon is not None:
            icon_label = ctk.CTkLabel(self, text="", image=icon)
            icon_label.grid(row=row, column=0, pady=(0, 16))
            row += 1

        message_label = ctk.CTkLabel(
            self,
            text=message,
            font=Theme.font(*Theme.T_ROW),
            text_color=Theme.TXT,
            justify="center"
        )
        message_label.grid(row=row, column=0)
        row += 1

        if hint:
            hint_label = ctk.CTkLabel(
                self,
                text=hint,
                font=Theme.font(*Theme.T_SUB),
                text_color=Theme.TXT_3,
                justify="center"
            )
            hint_label.grid(row=row, column=0, pady=(8, 0))
            row += 1

        #: El botón, o ``None`` si este estado vacío no ofrece acción.
        self.action_button: Optional[ctk.CTkButton] = None
        if action_text and on_action is not None:
            self.action_button = ctk.CTkButton(
                self,
                text=action_text,
                height=self.ACTION_H,
                corner_radius=Metrics.RADIUS_CONTROL,
                font=Theme.font(*Theme.T_UI),
                fg_color=Theme.ACCENT,
                hover_color=Theme.ACCENT,
                # Blanco en claro y casi negro en oscuro: es el token que existe
                # justo para el texto que va encima de ACCENT.
                text_color=Theme.ACCENT_INK,
                command=on_action
            )
            self.action_button.grid(row=row, column=0, pady=(22, 0))
