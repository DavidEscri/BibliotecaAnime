__author__ = "Jose David Escribano Orts"
__subsystem__ = "gui"
__module__ = "theme.py"
__version__ = "0.1"
__info__ = {"subsystem": __subsystem__, "module_name": __module__, "version": __version__}

"""Tokens visuales del rediseño: **la única fuente de verdad** de colores, tipografía y medidas.

Regla del plan: **ningún color literal fuera de este módulo**. Si un widget necesita
un color que no está aquí, se añade el token primero y luego se usa.

Los colores van en tuplas ``(claro, oscuro)``, que es lo que aceptan todos los
parámetros de color de CustomTkinter: pasándolas, el cambio de apariencia lo
resuelve la propia librería y **no hace falta reconfigurar los widgets a mano**.

Las fuentes se crean con ``Theme.font()`` y no como constantes de módulo porque un
``CTkFont`` necesita que ya exista una raíz de Tk; a nivel de módulo el import
reventaría.
"""

from typing import Dict, List, Tuple

import customtkinter as ctk

#: Tipo de un token de color: (claro, oscuro).
ColorToken = Tuple[str, str]


class Theme:
    """Paleta y tipografía del rediseño (``.claude/plan-rediseno/DISENO.md`` §1 y §2)."""

    # ------------------------------------------------------------------
    # Colores base
    # ------------------------------------------------------------------
    #: Fondo del área de contenido.
    BG: ColorToken = ("#F4F5F7", "#14161A")
    #: Fondo de la barra lateral.
    PANEL: ColorToken = ("#E9EBEF", "#0F1115")
    #: Tarjetas, fila activa y controles.
    CARD: ColorToken = ("#FFFFFF", "#1B1E24")
    #: Hover de fila y de tarjeta.
    CARD_HOVER: ColorToken = ("#EFF1F5", "#232730")
    #: Bordes de control y de tarjeta.
    LINE: ColorToken = ("#DCDFE5", "#262A33")
    #: Separador entre filas de lista.
    LINE_SOFT: ColorToken = ("#E7EAEF", "#1D212A")

    #: Títulos y texto principal.
    TXT: ColorToken = ("#171A1F", "#ECEEF2")
    #: Texto secundario (sinopsis, ítems inactivos).
    TXT_2: ColorToken = ("#525A66", "#A6AEBA")
    #: Texto terciario (géneros, contadores, subtítulos).
    TXT_3: ColorToken = ("#7C8593", "#6F7885")

    #: Selección, progreso y acción principal.
    ACCENT: ColorToken = ("#3A55C9", "#6D8AF0")
    #: Fondo de acento (globo del contador, ficha de género activa).
    ACCENT_SOFT: ColorToken = ("#E4E9FA", "#222A44")
    #: Texto **sobre** ACCENT.
    ACCENT_INK: ColorToken = ("#FFFFFF", "#0C1020")

    #: Identidad partida (el aviso de la ficha). Es el color que ya usaba anime_window.py.
    WARN: ColorToken = ("#B45309", "#FBBF24")

    #: Fondo transparente, para no repetir la cadena suelta por ahí.
    TRANSPARENT: str = "transparent"

    # ------------------------------------------------------------------
    # Píldoras y sellos de estado
    # ------------------------------------------------------------------
    #: Favorito: (texto, fondo).
    FAV_TXT: ColorToken = ("#8E3F86", "#D18ACB")
    FAV_BG: ColorToken = ("#F6E9F5", "#2C1A2E")
    #: Viendo.
    SEE_TXT: ColorToken = ("#1F6F85", "#5FC6DE")
    SEE_BG: ColorToken = ("#E2F1F6", "#12303A")
    #: Pendiente.
    PEN_TXT: ColorToken = ("#8A6420", "#D6A852")
    PEN_BG: ColorToken = ("#F7EEDC", "#332714")
    #: Finalizado.
    FIN_TXT: ColorToken = ("#2E7D5B", "#68C888")
    FIN_BG: ColorToken = ("#E3F3EA", "#14321F")

    #: Sello superpuesto a un póster (el «12 / 12» de finalizados, el «Viendo» de
    #: buscar). El diseño lo pide con fondo translúcido oscuro; Tk no sabe pintar
    #: un fondo con alfa, así que se usa el color opaco equivalente. Va **sobre
    #: la carátula**, no sobre el fondo de la aplicación, de modo que es el mismo
    #: en claro y en oscuro: un póster claro puede aparecer con cualquier tema y
    #: solo un sello oscuro se lee siempre sobre los dos.
    BADGE_BG: ColorToken = ("#0F1218", "#0F1218")
    #: Texto **sobre** BADGE_BG.
    BADGE_INK: ColorToken = ("#FFFFFF", "#FFFFFF")

    # ------------------------------------------------------------------
    # Tipografía
    # ------------------------------------------------------------------
    #: Segoe UI y Cascadia Mono vienen con Windows: no se empaqueta ninguna fuente.
    FAMILY: str = "Segoe UI"
    FAMILY_MONO: str = "Cascadia Mono"

    # Roles tipográficos como (tamaño, negrita, monoespaciada). Se usan
    # desempaquetados: Theme.font(*Theme.T_VIEW). CustomTkinter no admite
    # tamaños fraccionarios, así que todos son enteros.
    #: Título de vista ("Viendo").
    T_VIEW: Tuple[int, bool, bool] = (24, True, False)
    #: Título en la ficha del anime.
    T_SHEET: Tuple[int, bool, bool] = (30, True, False)
    #: Título de anime en una fila de lista.
    T_ROW: Tuple[int, bool, bool] = (17, True, False)
    #: Título en la tarjeta de retomar.
    T_CARD: Tuple[int, bool, bool] = (19, True, False)
    #: Sinopsis.
    T_BODY: Tuple[int, bool, bool] = (15, False, False)
    #: Controles, ítems de navegación, texto de tarjeta.
    T_UI: Tuple[int, bool, bool] = (13, False, False)
    #: Subtítulo de vista y proveedor. Va con TXT_3.
    T_SUB: Tuple[int, bool, bool] = (13, False, False)
    #: Etiqueta de sección en MAYÚSCULAS. Va con TXT_3.
    T_LABEL: Tuple[int, bool, bool] = (11, True, False)
    #: Géneros, contadores, sellos.
    T_META: Tuple[int, bool, bool] = (11, False, False)
    #: Números en columna ("12 / 24", paginación).
    T_NUM: Tuple[int, bool, bool] = (12, False, True)

    #: Fuentes ya construidas, indexadas por (tamaño, negrita, mono). Un CTkFont
    #: se puede compartir entre widgets y así no se crea uno por etiqueta.
    _font_cache: Dict[Tuple[int, bool, bool], ctk.CTkFont] = {}

    @staticmethod
    def font(size: int, bold: bool = False, mono: bool = False) -> ctk.CTkFont:
        """Devuelve la fuente de un rol tipográfico.

        Solo se puede llamar **después** de crear la ventana raíz: ``CTkFont``
        necesita que Tk exista.

        :param size: tamaño en puntos.
        :param bold: negrita.
        :param mono: usar la monoespaciada (números en columna).
        """
        key = (size, bold, mono)
        cached = Theme._font_cache.get(key)
        if cached is not None:
            return cached
        new_font = ctk.CTkFont(
            family=Theme.FAMILY_MONO if mono else Theme.FAMILY,
            size=size,
            weight="bold" if bold else "normal"
        )
        Theme._font_cache[key] = new_font
        return new_font

    @staticmethod
    def clear_font_cache() -> None:
        """Vacía la caché de fuentes. Solo hace falta si se destruye la raíz de Tk."""
        Theme._font_cache.clear()

    @staticmethod
    def ellipsize(text: str, font: ctk.CTkFont, max_width: int, max_lines: int = 2) -> str:
        """Recorta un texto para que quepa en ``max_lines`` líneas de ``max_width`` píxeles.

        El diseño pide títulos «a dos líneas», y ``wraplength`` por sí solo no lo
        cumple: envuelve todas las que hagan falta y estira la celda. Reservar
        alto tampoco vale, porque un ``CTkLabel`` crece por encima de su
        ``height`` en vez de recortarse.

        Reproduce el mismo reparto por palabras que hace Tk y, si el texto no
        cabe, corta la última línea y le pone puntos suspensivos.

        Solo se puede llamar con Tk ya creado: mide con ``font.measure()``.
        """
        if not text:
            return text

        lines: List[str] = []
        current = ""
        for word in text.split():
            candidate = f"{current} {word}".strip()
            if not current or font.measure(candidate) <= max_width:
                current = candidate
                continue
            lines.append(current)
            current = word
            if len(lines) == max_lines:
                break
        else:
            if current:
                lines.append(current)
            return "\n".join(lines)

        # Se ha salido por el break: sobra texto. La última línea admitida se
        # recorta letra a letra hasta que quepa junto a los puntos suspensivos.
        overflow = lines.pop()
        while overflow and font.measure(overflow + "…") > max_width:
            overflow = overflow[:-1]
        lines.append(overflow.rstrip() + "…")
        return "\n".join(lines)


class Metrics:
    """Medidas del rediseño (``.claude/plan-rediseno/DISENO.md`` §3), en píxeles a escala 1.

    Viven junto a los colores por el mismo motivo: que un número del diseño no se
    copie a mano en cinco vistas y luego solo se corrija en tres.
    """

    #: Ventana. Sin cambios respecto a lo que ya había.
    WINDOW_W: int = 1440
    WINDOW_H: int = 910

    #: Barra lateral, desplegada y plegada.
    SIDEBAR_W: int = 224
    SIDEBAR_COLLAPSED_W: int = 84

    #: Ítem de navegación desplegado.
    NAV_ITEM_H: int = 38
    NAV_ITEM_PAD_X: int = 18
    NAV_ITEM_GAP: int = 11
    NAV_ICON: int = 16

    #: Ítem de navegación plegado.
    NAV_COLLAPSED_SIZE: int = 48
    NAV_COLLAPSED_RADIUS: int = 11
    NAV_COLLAPSED_ICON: int = 20
    NAV_BADGE: int = 15

    #: Cabecera de vista y márgenes del contenido.
    VIEW_HEADER_H: int = 80
    CONTENT_PAD_X: int = 28

    #: Rejilla de 6 columnas (nuevos, finalizados, buscar).
    GRID6_POSTER: Tuple[int, int] = (176, 264)
    #: Rejilla de 5 columnas (favoritos).
    GRID5_POSTER: Tuple[int, int] = (216, 324)
    GRID_GAP_X: int = 20
    GRID_GAP_Y: int = 24

    #: Filas en cascada.
    ROW_WATCHING_POSTER: Tuple[int, int] = (70, 100)
    ROW_WATCHING_H: int = 132
    ROW_PENDING_POSTER: Tuple[int, int] = (56, 80)
    ROW_PENDING_H: int = 113

    #: Tarjeta "Retomar" y panel lateral de "Viendo".
    RESUME_CARD_POSTER: Tuple[int, int] = (84, 118)
    SIDE_PANEL_W: int = 290

    #: Ficha del anime.
    SHEET_POSTER: Tuple[int, int] = (248, 372)
    STATUS_BUTTON_H: int = 40
    EPISODE_ROW_H: int = 52

    #: Barra de progreso.
    PROGRESS_H: int = 4
    PROGRESS_RADIUS: int = 2

    #: Radios generales.
    RADIUS_CONTROL: int = 7
    RADIUS_POSTER: int = 9
    RADIUS_CARD: int = 12
    RADIUS_SHEET_POSTER: int = 11

    #: Tamaño al que se **guardan** los pósters en disco: el mayor que pide
    #: cualquier vista. Cada vista reduce con su propio size= al construir el
    #: CTkImage, que escala con calidad; ampliar un JPG pequeño, no.
    POSTER_CACHE_SIZE: Tuple[int, int] = SHEET_POSTER

    @staticmethod
    def pill_radius(height: int) -> int:
        """Radio de una píldora: la mitad de su alto."""
        return height // 2
