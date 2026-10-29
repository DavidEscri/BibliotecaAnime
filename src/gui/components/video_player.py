__author__ = "Jose David Escribano Orts"
__subsystem__ = "gui.components"
__module__ = "video_player.py"
__version__ = "0.2"
__info__ = {"subsystem": __subsystem__, "module_name": __module__, "version": __version__}

"""Reproductor de vídeo incrustado: la superficie de mpv, sus tarjetas de estado y la barra de controles.

La superficie es una ventana nativa hija de un frame de Tk, así que ningún widget
de la ventana puede ir encima: los estados que no son «reproduciendo» son
tarjetas en la misma celda, y lo que flota sobre el vídeo (la barra de pantalla
completa y el deslizador de volumen) son ventanas aparte.

Los eventos de mpv llegan en su propio hilo y **no tocan Tk**: dejan el dato en
atributos o en una cola y el hilo de la interfaz los recoge con un sondeo. Una
llamada a Tk desde ese hilo espera a que la interfaz la atienda, y cerrar el
reproductor desde la interfaz espera a ese hilo: juntas se bloquean.
"""

import ctypes
import os
import queue
import tkinter
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Tuple

import customtkinter as ctk
from PIL import Image, ImageDraw, ImageFont, ImageOps

from APIs.resolvers.base import MediaSource
from gui.theme import ColorToken, Metrics, Theme
from utils.utils import get_resource_path

#: Factor de supermuestreo de los glifos.
_SUPERSAMPLE = 8
#: Lado de los iconos de la barra.
ICON_SIZE = 20
#: Cada cuánto recoge la interfaz lo que ha contado mpv, en milisegundos.
POLL_MS = 100
#: Segundos que saltan los botones de retroceso y avance.
SEEK_STEP = 10
#: Tiempo sin mover el ratón tras el que se ocultan la barra flotante y el cursor.
IDLE_HIDE_MS = 5000
#: Margen de gracia antes de cerrar el deslizador de volumen al salir del icono.
VOLUME_GRACE_MS = 300
#: Alto del deslizador vertical de volumen.
VOLUME_SLIDER_H = 160
#: Cada cuánto se comprueba en pantalla completa que la aplicación sigue en primer plano.
FOREGROUND_CHECK_MS = 150
#: Fotogramas y paso de la animación del aro de «Cargando».
RING_FRAMES = 12
RING_STEP_MS = 80
RING_SIZE = 34
#: Segundos que mpv espera a un servidor que no responde antes de dar error.
NETWORK_TIMEOUT_S = 15
#: Segundos que puede tardar un medio en empezar a verse antes de darlo por fallido.
#: El plazo de mpv cuenta por petición: un servidor que contesta todo despacio no lo agota.
LOAD_TIMEOUT_S = 30

#: `end-file.reason` de mpv que importan aquí: fin natural y error.
END_REASON_EOF = 0
END_REASON_ERROR = 4
#: Segundos que pueden faltar para el final y seguir contando como «terminado».
#: Un fin de fichero antes de eso es el servidor cortando el vídeo.
END_TOLERANCE_S = 15

_mpv_module = None
_mpv_load_error: Optional[str] = None


def load_mpv():
    """Importa ``python-mpv`` con la ``libmpv-2.dll`` de ``vendor/`` en la ruta de búsqueda.

    ``python-mpv`` busca la DLL en ``%PATH%``, no junto al script. Nunca lanza.
    :return: El módulo ``mpv``, o None si falta la DLL o el binding.
    """
    global _mpv_module, _mpv_load_error
    if _mpv_module is not None or _mpv_load_error is not None:
        return _mpv_module
    dll_dir = get_resource_path("vendor")
    if os.path.isdir(dll_dir):
        try:
            os.add_dll_directory(dll_dir)
        except (OSError, AttributeError):
            pass
        os.environ["PATH"] = dll_dir + os.pathsep + os.environ.get("PATH", "")
    try:
        import mpv
        _mpv_module = mpv
    except (OSError, ImportError) as exc:
        _mpv_load_error = str(exc)
        print(f"No se pudo cargar libmpv; los servidores se abrirán en el navegador: {exc}")
    return _mpv_module


def format_time(seconds: Optional[float]) -> str:
    """:return: «m:ss», o «h:mm:ss» a partir de una hora; «--:--» si no se sabe."""
    if seconds is None or seconds < 0:
        return "--:--"
    total = int(seconds)
    hours, rest = divmod(total, 3600)
    minutes, secs = divmod(rest, 60)
    return f"{hours}:{minutes:02d}:{secs:02d}" if hours else f"{minutes:02d}:{secs:02d}"


# ---- Glifos ----
def _round_line(draw: ImageDraw.ImageDraw, points, width: float, color: str) -> None:
    """Polilínea con los extremos y las uniones redondeados, que PIL no hace solo."""
    width = max(1, int(width))
    draw.line(points, fill=color, width=width, joint="curve")
    radius = width / 2
    for x, y in points:
        draw.ellipse([x - radius, y - radius, x + radius, y + radius], fill=color)


def _play_glyph(draw, s, color):
    draw.polygon([(s * 0.30, s * 0.18), (s * 0.30, s * 0.82), (s * 0.82, s * 0.50)], fill=color)


def _pause_glyph(draw, s, color):
    draw.rounded_rectangle([s * 0.26, s * 0.20, s * 0.42, s * 0.80], radius=s * 0.04, fill=color)
    draw.rounded_rectangle([s * 0.58, s * 0.20, s * 0.74, s * 0.80], radius=s * 0.04, fill=color)


def _previous_glyph(draw, s, color):
    draw.rounded_rectangle([s * 0.20, s * 0.22, s * 0.30, s * 0.78], radius=s * 0.03, fill=color)
    draw.polygon([(s * 0.80, s * 0.22), (s * 0.80, s * 0.78), (s * 0.34, s * 0.50)], fill=color)


def _next_glyph(draw, s, color):
    draw.rounded_rectangle([s * 0.70, s * 0.22, s * 0.80, s * 0.78], radius=s * 0.03, fill=color)
    draw.polygon([(s * 0.20, s * 0.22), (s * 0.20, s * 0.78), (s * 0.66, s * 0.50)], fill=color)


def _circular_arrow(draw, s, color, box=(0.12, 0.12, 0.88, 0.88)):
    """Flecha circular en sentido antihorario con la punta arriba, apuntando a la izquierda."""
    width = s * 0.09
    left, top, right, bottom = (value * s for value in box)
    draw.arc([left, top, right, bottom], start=300, end=630, fill=color, width=int(width))
    head = s * 0.13
    center_x = (left + right) / 2
    draw.polygon([(center_x - head, top), (center_x + head * 0.35, top - head),
                  (center_x + head * 0.35, top + head)], fill=color)


def _ten_text(draw, s, color):
    """El «10» dentro de los botones de salto."""
    try:
        font = ImageFont.truetype("segoeuib.ttf", int(s * 0.34))
    except OSError:
        font = ImageFont.load_default()
    draw.text((s * 0.5, s * 0.53), "10", fill=color, font=font, anchor="mm")


def _replay_glyph(draw, s, color):
    _circular_arrow(draw, s, color)
    draw.polygon([(s * 0.42, s * 0.36), (s * 0.42, s * 0.66), (s * 0.66, s * 0.51)], fill=color)


def _volume_body(draw, s, color):
    draw.polygon([(s * 0.10, s * 0.38), (s * 0.28, s * 0.38), (s * 0.50, s * 0.18),
                  (s * 0.50, s * 0.82), (s * 0.28, s * 0.62), (s * 0.10, s * 0.62)], fill=color)


def _volume_glyph(draw, s, color):
    _volume_body(draw, s, color)
    width = int(s * 0.08)
    for radius in (0.16, 0.30):
        draw.arc([s * (0.50 - radius), s * (0.50 - radius), s * (0.50 + radius), s * (0.50 + radius)],
                 start=-50, end=50, fill=color, width=width)


def _muted_glyph(draw, s, color):
    _volume_body(draw, s, color)
    width = s * 0.08
    _round_line(draw, [(s * 0.64, s * 0.36), (s * 0.90, s * 0.64)], width, color)
    _round_line(draw, [(s * 0.64, s * 0.64), (s * 0.90, s * 0.36)], width, color)


def _fullscreen_glyph(draw, s, color):
    width = s * 0.09
    a, b, c = 0.16, 0.40, 0.84
    for points in ([(a, b), (a, a), (b, a)], [(1 - b, a), (c, a), (c, b)],
                   [(c, 1 - b), (c, c), (1 - b, c)], [(b, c), (a, c), (a, 1 - b)]):
        _round_line(draw, [(x * s, y * s) for x, y in points], width, color)


def _exit_fullscreen_glyph(draw, s, color):
    width = s * 0.09
    a, b = 0.40, 0.16
    for points in ([(b, a), (a, a), (a, b)], [(1 - a, b), (1 - a, a), (1 - b, a)],
                   [(1 - b, 1 - a), (1 - a, 1 - a), (1 - a, 1 - b)], [(a, 1 - b), (a, 1 - a), (b, 1 - a)]):
        _round_line(draw, [(x * s, y * s) for x, y in points], width, color)


def _external_glyph(draw, s, color):
    """↗: se abre fuera de la aplicación."""
    width = s * 0.11
    _round_line(draw, [(s * 0.24, s * 0.76), (s * 0.74, s * 0.26)], width, color)
    _round_line(draw, [(s * 0.36, s * 0.26), (s * 0.74, s * 0.26), (s * 0.74, s * 0.64)], width, color)


def _left_glyph(draw, s, color):
    """←: volver."""
    width = s * 0.10
    _round_line(draw, [(s * 0.80, s * 0.50), (s * 0.20, s * 0.50)], width, color)
    _round_line(draw, [(s * 0.46, s * 0.24), (s * 0.20, s * 0.50), (s * 0.46, s * 0.76)], width, color)


def _close_glyph(draw, s, color):
    """✕: cerrar un aviso."""
    width = s * 0.10
    _round_line(draw, [(s * 0.26, s * 0.26), (s * 0.74, s * 0.74)], width, color)
    _round_line(draw, [(s * 0.26, s * 0.74), (s * 0.74, s * 0.26)], width, color)


def _check_glyph(draw, s, color):
    """✓: hecho."""
    _round_line(draw, [(s * 0.20, s * 0.52), (s * 0.42, s * 0.74), (s * 0.80, s * 0.30)], s * 0.11, color)


def _draw_back10(image: Image.Image, color: str) -> Image.Image:
    draw = ImageDraw.Draw(image)
    _circular_arrow(draw, image.width, color)
    _ten_text(draw, image.width, color)
    return image


def _draw_forward10(image: Image.Image, color: str) -> Image.Image:
    _circular_arrow(ImageDraw.Draw(image), image.width, color)
    image = ImageOps.mirror(image)
    _ten_text(ImageDraw.Draw(image), image.width, color)
    return image


#: Cómo se dibuja cada glifo: sobre el lienzo o, si necesita espejarse, sobre la imagen entera.
_GLYPHS: Dict[str, Callable] = {
    "play": _play_glyph,
    "pause": _pause_glyph,
    "previous": _previous_glyph,
    "next": _next_glyph,
    "replay": _replay_glyph,
    "volume": _volume_glyph,
    "muted": _muted_glyph,
    "fullscreen": _fullscreen_glyph,
    "exit_fullscreen": _exit_fullscreen_glyph,
    "external": _external_glyph,
    "left": _left_glyph,
    "close": _close_glyph,
    "check": _check_glyph,
}
_IMAGE_GLYPHS: Dict[str, Callable[[Image.Image, str], Image.Image]] = {
    "back10": _draw_back10,
    "forward10": _draw_forward10,
}
#: Dibujos ya hechos (claro, oscuro). Se cachea el dibujo y no el CTkImage,
#: porque un CTkImage compartido retiene a todo widget que lo haya usado aunque
#: ya esté destruido.
_ICON_CACHE: Dict[Tuple[str, int, ColorToken], Tuple[Image.Image, Image.Image]] = {}


def player_icon(name: str, size: int = ICON_SIZE, color: ColorToken = Theme.TXT_2) -> ctk.CTkImage:
    """Glifo del reproductor dibujado con PIL, con variante clara y oscura.

    :param name: «play», «pause», «previous», «next», «back10», «forward10», «replay»,
        «volume», «muted», «fullscreen», «exit_fullscreen», «external», «left», «close» o «check».
    :param size: Lado del icono.
    :param color: Par (claro, oscuro) con el que se tiñe.
    :return: Un CTkImage nuevo; el dibujo sale cacheado por nombre, tamaño y color.
    """
    key = (name, size, color)
    images = _ICON_CACHE.get(key)
    if images is None:
        drawn = []
        for tone in color:
            big = Image.new("RGBA", (size * _SUPERSAMPLE, size * _SUPERSAMPLE), (0, 0, 0, 0))
            if name in _IMAGE_GLYPHS:
                big = _IMAGE_GLYPHS[name](big, tone)
            else:
                _GLYPHS[name](ImageDraw.Draw(big), big.width, tone)
            drawn.append(big.resize((size, size), Image.LANCZOS))
        images = (drawn[0], drawn[1])
        _ICON_CACHE[key] = images
    return ctk.CTkImage(light_image=images[0], dark_image=images[1], size=(size, size))


#: Fotogramas del aro ya dibujados, como pares (claro, oscuro).
_RING_CACHE: List[Tuple[Image.Image, Image.Image]] = []


def _ring_frames() -> List[ctk.CTkImage]:
    """Fotogramas del aro que gira en la tarjeta de «Cargando».

    :return: Una lista nueva de CTkImage, para que la tarjeta se la lleve al destruirse.
    """
    if not _RING_CACHE:
        big = RING_SIZE * _SUPERSAMPLE
        width = 3 * _SUPERSAMPLE
        for index in range(RING_FRAMES):
            pair = []
            for track, arc in zip(Theme.LINE, Theme.ACCENT):
                image = Image.new("RGBA", (big, big), (0, 0, 0, 0))
                draw = ImageDraw.Draw(image)
                box = [width / 2, width / 2, big - width / 2, big - width / 2]
                draw.ellipse(box, outline=track, width=width)
                start = index * 360 / RING_FRAMES - 90
                draw.arc(box, start=start, end=start + 90, fill=arc, width=width)
                pair.append(image.resize((RING_SIZE, RING_SIZE), Image.LANCZOS))
            _RING_CACHE.append((pair[0], pair[1]))
    return [ctk.CTkImage(light_image=light, dark_image=dark, size=(RING_SIZE, RING_SIZE))
            for light, dark in _RING_CACHE]


def _pointer_inside(widget) -> bool:
    """:return: True si el puntero está dentro del rectángulo visible del widget."""
    try:
        if widget is None or not widget.winfo_exists() or not widget.winfo_viewable():
            return False
        x, y = widget.winfo_pointerxy()
        left, top = widget.winfo_rootx(), widget.winfo_rooty()
        return left <= x < left + widget.winfo_width() and top <= y < top + widget.winfo_height()
    except tkinter.TclError:
        return False


def _foreground_is_ours() -> bool:
    """:return: True si la ventana en primer plano es de este proceso."""
    try:
        user32 = ctypes.windll.user32
        pid = ctypes.c_ulong()
        user32.GetWindowThreadProcessId(user32.GetForegroundWindow(), ctypes.byref(pid))
        return pid.value == os.getpid()
    except Exception:
        return True


@dataclass
class PlaybackState:
    """Lo que la barra necesita saber para pintarse."""
    enabled: bool = False
    paused: bool = False
    ended: bool = False
    position: Optional[float] = None
    duration: Optional[float] = None
    volume: float = 100.0
    muted: bool = False
    fullscreen: bool = False
    has_previous: bool = False
    has_next: bool = False


class _VolumePopup:
    """Deslizador vertical de volumen: una ventana sin marco encima del icono."""

    def __init__(self, controls: "PlayerControls"):
        self.__controls = controls
        self.window = tkinter.Toplevel(controls)
        self.window.withdraw()
        self.window.overrideredirect(True)
        self.window.attributes("-topmost", True)
        frame = ctk.CTkFrame(self.window, corner_radius=0, fg_color=Theme.CARD,
                             border_width=1, border_color=Theme.LINE)
        frame.pack(fill="both", expand=True)
        self.label = ctk.CTkLabel(frame, text="100 %", font=Theme.font(*Theme.T_NUM),
                                  text_color=Theme.TXT, width=52)
        self.label.pack(padx=6, pady=(10, 4))
        self.slider = ctk.CTkSlider(
            frame, from_=0, to=100, orientation="vertical", width=16, height=VOLUME_SLIDER_H,
            border_width=6, button_length=0, button_corner_radius=8,
            fg_color=Theme.LINE, progress_color=Theme.ACCENT,
            button_color=Theme.ACCENT, button_hover_color=Theme.ACCENT,
            command=controls.volume_slider_moved
        )
        self.slider.pack(padx=18, pady=(4, 14))
        self.window.bind("<Leave>", lambda _event: controls.schedule_volume_check(), add="+")

    def show(self, anchor: tkinter.Misc, volume: float) -> None:
        """Abre el deslizador centrado sobre ``anchor`` y por encima de la barra.

        :param anchor: El botón de volumen.
        :param volume: Volumen actual, de 0 a 100.
        """
        self.set_volume(volume)
        self.window.update_idletasks()
        width, height = self.window.winfo_reqwidth(), self.window.winfo_reqheight()
        bar_top = self.__controls.winfo_rooty()
        x = anchor.winfo_rootx() + anchor.winfo_width() // 2 - width // 2
        tkinter.Toplevel.wm_geometry(self.window, f"{width}x{height}+{x}+{bar_top - height - 6}")
        self.window.deiconify()
        self.window.lift()

    def hide(self) -> None:
        if self.window.winfo_exists():
            self.window.withdraw()

    def is_open(self) -> bool:
        return self.window.winfo_exists() and self.window.state() != "withdrawn"

    def set_volume(self, volume: float) -> None:
        self.slider.set(volume)
        self.label.configure(text=f"{int(round(volume))} %")

    def destroy(self) -> None:
        if self.window.winfo_exists():
            self.window.destroy()


class PlayerControls(ctk.CTkFrame):
    """La barra de controles, en su orden: anterior · −10 · play · +10 · siguiente · progreso · tiempo · volumen · pantalla completa.

    La misma clase sirve a la barra fija de debajo del vídeo y a la flotante de
    pantalla completa (``floating=True``): un widget no cambia de padre, así que
    son dos instancias que pintan el mismo estado del reproductor.
    """

    def __init__(self, parent, player: "VideoPlayer", floating: bool = False):
        """
        :param player: Reproductor al que manda las órdenes y del que pinta el estado.
        :param floating: Versión de pantalla completa: 64 px y la tecla «Esc» junto al botón.
        """
        height = Metrics.PLAYER_FLOAT_BAR_H if floating else Metrics.PLAYER_BAR_H
        super().__init__(parent, height=height, corner_radius=0, fg_color=Theme.CARD,
                         border_width=1, border_color=Theme.LINE)
        self.__player = player
        self.__floating = floating
        self.__dragging = False
        self.__state: Optional[PlaybackState] = None
        self.__volume_popup: Optional[_VolumePopup] = None
        self.__volume_check_job: Optional[str] = None
        self.grid_propagate(False)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(5, weight=1)
        side_pad = 18 if floating else 10

        self.previous_button = self.__button("previous", player.go_previous)
        self.back_button = self.__button("back10", lambda: player.seek_relative(-SEEK_STEP))
        self.play_button = ctk.CTkButton(
            self, text="", font=Theme.font(*Theme.T_UI), width=Metrics.PLAYER_BUTTON, height=Metrics.PLAYER_BUTTON, corner_radius=8,
            fg_color=Theme.ACCENT, hover_color=Theme.ACCENT,
            image=player_icon("pause", color=Theme.ACCENT_INK), command=player.toggle_pause
        )
        self.forward_button = self.__button("forward10", lambda: player.seek_relative(SEEK_STEP))
        self.next_button = self.__button("next", player.go_next)
        for column, widget in enumerate((self.previous_button, self.back_button, self.play_button,
                                         self.forward_button, self.next_button)):
            padx = (side_pad, 1) if column == 0 else ((4, 4) if widget is self.play_button else (1, 1))
            widget.grid(row=0, column=column, padx=padx)

        self.seek_slider = ctk.CTkSlider(
            self, from_=0, to=1, height=14, border_width=5, button_length=0, button_corner_radius=7,
            fg_color=Theme.LINE, progress_color=Theme.ACCENT,
            button_color=Theme.ACCENT, button_hover_color=Theme.ACCENT,
            command=self.__seek_slider_moved
        )
        self.seek_slider.set(0)
        self.seek_slider.grid(row=0, column=5, sticky="ew", padx=(18 if floating else 12, 12))
        self.seek_slider.bind("<ButtonPress-1>", self.__seek_pressed, add="+")
        self.seek_slider.bind("<ButtonRelease-1>", self.__seek_released, add="+")

        time_frame = ctk.CTkFrame(self, fg_color=Theme.TRANSPARENT, height=1)
        time_frame.grid(row=0, column=6, padx=(0, 8))
        self.position_label = ctk.CTkLabel(time_frame, text="--:--", font=Theme.font(*Theme.T_NUM),
                                           text_color=Theme.TXT)
        self.position_label.grid(row=0, column=0)
        self.duration_label = ctk.CTkLabel(time_frame, text=" / --:--", font=Theme.font(*Theme.T_NUM),
                                           text_color=Theme.TXT_3)
        self.duration_label.grid(row=0, column=1)

        self.volume_button = self.__button("volume", player.toggle_mute)
        self.volume_button.grid(row=0, column=7, padx=1)
        self.volume_button.bind("<Enter>", self.__open_volume, add="+")
        self.volume_button.bind("<Leave>", lambda _event: self.schedule_volume_check(), add="+")
        self.fullscreen_button = self.__button("fullscreen", player.request_fullscreen_toggle)
        self.fullscreen_button.grid(row=0, column=8, padx=(1, side_pad if not floating else 4))
        if floating:
            esc_frame = ctk.CTkFrame(self, fg_color=Theme.TRANSPARENT, corner_radius=5,
                                     border_width=1, border_color=Theme.LINE, height=1)
            esc_frame.grid(row=0, column=9, padx=(0, side_pad))
            ctk.CTkLabel(esc_frame, text="Esc", height=18, font=Theme.font(11, False, True),
                         text_color=Theme.TXT_3).pack(padx=6, pady=1)

    def __button(self, icon: str, command: Optional[Callable[[], None]]) -> ctk.CTkButton:
        """Un control de 38 × 38 con su glifo, sin texto."""
        return ctk.CTkButton(
            self, text="", font=Theme.font(*Theme.T_UI), width=Metrics.PLAYER_BUTTON, height=Metrics.PLAYER_BUTTON, corner_radius=8,
            fg_color=Theme.TRANSPARENT, hover_color=Theme.CARD_HOVER,
            image=player_icon(icon), command=command
        )

    # ---- Estado ----
    def refresh(self, state: PlaybackState) -> None:
        """Pinta el estado del reproductor, tocando solo lo que ha cambiado."""
        previous = self.__state
        self.__state = state
        if (previous is None or previous.enabled != state.enabled or previous.paused != state.paused
                or previous.ended != state.ended):
            self.__refresh_buttons(state)
        if (previous is None or previous.has_previous != state.has_previous
                or previous.has_next != state.has_next):
            self.__refresh_navigation(state)
        if previous is None or previous.fullscreen != state.fullscreen:
            icon = "exit_fullscreen" if state.fullscreen else "fullscreen"
            self.fullscreen_button.configure(image=player_icon(icon))
        if previous is None or previous.muted != state.muted:
            self.volume_button.configure(image=player_icon("muted" if state.muted else "volume"))
        if self.__volume_popup is not None and (previous is None or previous.volume != state.volume):
            self.__volume_popup.set_volume(state.volume)
        if not self.__dragging:
            self.__refresh_time(state.position, state.duration)

    def __refresh_buttons(self, state: PlaybackState) -> None:
        if not state.enabled:
            self.play_button.configure(state="disabled", fg_color=Theme.LINE,
                                       image=player_icon("play", color=Theme.TXT_3))
        else:
            icon = "replay" if state.ended else ("play" if state.paused else "pause")
            self.play_button.configure(state="normal", fg_color=Theme.ACCENT,
                                       image=player_icon(icon, color=Theme.ACCENT_INK))
        for button, icon, allowed in ((self.back_button, "back10", state.enabled),
                                      (self.forward_button, "forward10", state.enabled and not state.ended)):
            button.configure(state="normal" if allowed else "disabled",
                             image=player_icon(icon, color=Theme.TXT_2 if allowed else Theme.LINE))
        self.seek_slider.configure(state="normal" if state.enabled else "disabled")

    def __refresh_navigation(self, state: PlaybackState) -> None:
        """Anterior y siguiente no dependen de que el medio suene: también navegan cargando o al terminar."""
        for button, icon, allowed in ((self.previous_button, "previous", state.has_previous),
                                      (self.next_button, "next", state.has_next)):
            button.configure(state="normal" if allowed else "disabled",
                             image=player_icon(icon, color=Theme.TXT_2 if allowed else Theme.LINE))

    def __refresh_time(self, position: Optional[float], duration: Optional[float]) -> None:
        self.position_label.configure(text=format_time(position))
        self.duration_label.configure(text=f" / {format_time(duration)}")
        self.seek_slider.set(min(1.0, max(0.0, position / duration)) if position and duration else 0)

    # ---- Progreso ----
    def __seek_pressed(self, _event=None) -> None:
        if self.__state is not None and self.__state.enabled:
            self.__dragging = True

    def __seek_slider_moved(self, value: float) -> None:
        """Mientras se arrastra, el tiempo enseña adónde se va a saltar."""
        if self.__state is not None and self.__state.duration:
            self.position_label.configure(text=format_time(value * self.__state.duration))

    def __seek_released(self, _event=None) -> None:
        if not self.__dragging:
            return
        self.__dragging = False
        self.__player.seek_fraction(self.seek_slider.get())

    # ---- Volumen ----
    def __open_volume(self, _event=None) -> None:
        if self.__volume_check_job is not None:
            self.after_cancel(self.__volume_check_job)
            self.__volume_check_job = None
        if self.__volume_popup is None:
            self.__volume_popup = _VolumePopup(self)
        if not self.__volume_popup.is_open():
            self.__volume_popup.show(self.volume_button, self.__player.volume)

    def schedule_volume_check(self) -> None:
        """Cierra el deslizador tras el margen de gracia, si el puntero no ha vuelto a él ni al icono."""
        if self.__volume_check_job is not None:
            self.after_cancel(self.__volume_check_job)
        self.__volume_check_job = self.after(VOLUME_GRACE_MS, self.__check_volume)

    def __check_volume(self) -> None:
        self.__volume_check_job = None
        popup = self.__volume_popup
        if popup is None or not popup.is_open():
            return
        if _pointer_inside(self.volume_button) or _pointer_inside(popup.window):
            self.__volume_check_job = self.after(VOLUME_GRACE_MS, self.__check_volume)
            return
        popup.hide()

    def volume_slider_moved(self, value: float) -> None:
        if self.__volume_popup is not None:
            self.__volume_popup.label.configure(text=f"{int(round(value))} %")
        self.__player.set_volume(value)

    def is_volume_open(self) -> bool:
        return self.__volume_popup is not None and self.__volume_popup.is_open()

    def hide_volume(self) -> None:
        if self.__volume_popup is not None:
            self.__volume_popup.hide()

    def destroy(self):
        if self.__volume_popup is not None:
            self.__volume_popup.destroy()
            self.__volume_popup = None
        super().destroy()


class VideoPlayer(ctk.CTkFrame):
    """Superficie de vídeo con mpv incrustado, sus tarjetas de estado y la barra de controles.

    Es solo el reproductor: qué episodio suena, de qué servidor y qué hacer cuando
    falla lo decide quien lo compone, a través de los callbacks. Cualquier fallo
    de mpv —DLL ausente, error al crear el núcleo o medio que no se abre— acaba en
    ``on_error``, que es donde el dueño cae al navegador.
    """

    #: Volumen y silencio del último reproductor, para que el siguiente episodio suene igual.
    _last_volume: float = 100.0
    _last_muted: bool = False

    def __init__(self, parent, on_error: Callable[[str], None],
                 on_started: Optional[Callable[[], None]] = None,
                 on_end: Optional[Callable[[], None]] = None,
                 on_fullscreen_request: Optional[Callable[[bool], None]] = None,
                 on_previous: Optional[Callable[[], None]] = None,
                 on_next: Optional[Callable[[], None]] = None):
        """
        :param on_error: Se llama con el motivo cuando el medio no se puede reproducir.
        :param on_started: Se llama cuando empieza a verse el medio cargado.
        :param on_end: Se llama cuando el episodio llega al final.
        :param on_fullscreen_request: Se llama con True/False al pedir entrar o salir de
            pantalla completa; el dueño cambia la disposición y llama a ``set_fullscreen()``.
        :param on_previous: Se llama al pulsar «episodio anterior», si está habilitado.
        :param on_next: Se llama al pulsar «episodio siguiente», si está habilitado.
        """
        super().__init__(parent, corner_radius=0, fg_color=Theme.TRANSPARENT)
        self.__on_error = on_error
        self.__on_started = on_started
        self.__on_end = on_end
        self.__on_fullscreen_request = on_fullscreen_request
        self.__on_previous = on_previous
        self.__on_next = on_next
        self.__has_previous = False
        self.__has_next = False

        self.__mpv = None
        self.__default_user_agent: Optional[str] = None
        self.__source: Optional[MediaSource] = None
        self.__closed = False
        self.__poll_job: Optional[str] = None
        self.__load_timeout_job: Optional[str] = None
        #: Lo que cuenta el hilo de mpv. Asignaciones sueltas: el GIL las hace atómicas.
        self.__mpv_position: Optional[float] = None
        self.__mpv_duration: Optional[float] = None
        self.__mpv_paused: bool = False
        self.__events: "queue.Queue[Tuple[str, object]]" = queue.Queue()
        #: Hasta que llegue su start-file, los end-file son del medio anterior.
        self.__awaiting_start = False
        self.__file_active = False
        self.__started = False
        self.__ended = False
        self.__seek_target: Optional[float] = None
        self.__seek_hold = 0
        self.volume: float = VideoPlayer._last_volume
        self.__muted = VideoPlayer._last_muted
        self.__fullscreen = False

        self.__floating_window: Optional[tkinter.Toplevel] = None
        self.__floating_controls: Optional[PlayerControls] = None
        self.__idle_job: Optional[str] = None
        self.__foreground_job: Optional[str] = None
        self.__escape_funcid: Optional[str] = None
        self.__ring_job: Optional[str] = None

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)

        self.__stage = ctk.CTkFrame(self, height=Metrics.PLAYER_VIDEO_H, corner_radius=0, fg_color=Theme.VIDEO_BG)
        self.__stage.grid(row=0, column=0, sticky="nsew")
        self.__stage.grid_propagate(False)
        self.__stage.grid_rowconfigure(0, weight=1)
        self.__stage.grid_columnconfigure(0, weight=1)

        self.__surface = ctk.CTkFrame(self.__stage, corner_radius=0, fg_color=Theme.VIDEO_BG)
        self.__surface.grid(row=0, column=0, sticky="nsew")
        self.__card_frame = ctk.CTkFrame(self.__stage, corner_radius=0, fg_color=Theme.VIDEO_BG)
        self.__card_frame.grid(row=0, column=0, sticky="nsew")
        self.__card_frame.grid_remove()

        self.__controls = PlayerControls(self, self, floating=False)
        self.__controls.grid(row=1, column=0, sticky="ew")

        for widget in (self.__stage, self.__surface, self.__card_frame):
            tkinter.Frame.bind(widget, "<Motion>", self.__on_motion, "+")
            widget.bind("<Motion>", self.__on_motion, add="+")
        self.bind("<Configure>", self.__on_configure, add="+")
        self.__refresh_controls()

    # ---- Medio ----
    def play(self, source: MediaSource) -> None:
        """Carga un medio ya resuelto. La tarjeta que haya sigue a la vista hasta que empiece a verse.

        :param source: URL del medio con las cabeceras que exige su hoster.
        """
        if self.__closed:
            return
        self.__cancel_load_timeout()
        if not self.__ensure_mpv():
            self.__on_error("No se ha podido iniciar el reproductor")
            return
        self.__source = source
        self.__started = False
        self.__ended = False
        self.__mpv_position = None
        self.__mpv_duration = None
        self.__awaiting_start = True
        self.__surface.grid()
        self.__card_frame.lift()
        headers = dict(source.headers or {})
        user_agent = next((value for key, value in headers.items() if key.lower() == "user-agent"), None)
        try:
            self.__mpv.user_agent = user_agent or self.__default_user_agent or ""
            self.__mpv.http_header_fields = [f"{key}: {value}" for key, value in headers.items()
                                             if key.lower() != "user-agent"]
            self.__mpv.pause = False
            self.__mpv.play(source.url)
        except Exception as exc:
            print(f"mpv no aceptó el medio {source.url}: {exc}")
            self.__on_error("El reproductor no ha aceptado el medio")
            return
        self.__load_timeout_job = self.after(LOAD_TIMEOUT_S * 1000, self.__on_load_timeout)
        self.__refresh_controls()

    def __cancel_load_timeout(self) -> None:
        if self.__load_timeout_job is not None:
            try:
                self.after_cancel(self.__load_timeout_job)
            except tkinter.TclError:
                pass
            self.__load_timeout_job = None

    def __on_load_timeout(self) -> None:
        """El medio no ha empezado a verse en ``LOAD_TIMEOUT_S``: se para y se trata como un error.

        Parar antes de avisar evita que un medio que arranca tarde suene detrás del aviso.
        """
        self.__load_timeout_job = None
        if self.__closed or self.__started or self.__source is None:
            return
        print(f"El medio no ha empezado a verse en {LOAD_TIMEOUT_S} s: {self.__source.url}")
        self.stop_media()
        self.__on_error("El servidor tarda demasiado en entregar el vídeo")

    def stop_media(self) -> None:
        """Para el medio que suene, sin cerrar el reproductor."""
        self.__cancel_load_timeout()
        self.__source = None
        self.__started = False
        self.__ended = False
        self.__mpv_position = None
        self.__mpv_duration = None
        if self.__mpv is not None:
            try:
                self.__mpv.stop()
            except Exception as exc:
                print(f"Error al parar mpv: {exc}")
        self.__refresh_controls()

    def close(self) -> None:
        """Para y destruye el núcleo de mpv. Tras esto el reproductor no se reutiliza."""
        if self.__closed:
            return
        self.__closed = True
        if self.__fullscreen:
            self.set_fullscreen(False)
        self.__cancel_load_timeout()
        for job in (self.__poll_job, self.__ring_job, self.__idle_job, self.__foreground_job):
            if job is not None:
                try:
                    self.after_cancel(job)
                except tkinter.TclError:
                    pass
        self.__poll_job = self.__ring_job = self.__idle_job = self.__foreground_job = None
        self.__controls.hide_volume()
        player, self.__mpv = self.__mpv, None
        if player is not None:
            try:
                player.terminate()
            except Exception as exc:
                print(f"Error al cerrar mpv: {exc}")

    def __ensure_mpv(self) -> bool:
        """Crea el núcleo la primera vez, ya con la superficie colocada. :return: si hay reproductor."""
        if self.__mpv is not None:
            return True
        mpv_module = load_mpv()
        if mpv_module is None:
            return False
        self.__surface.grid()
        self.update_idletasks()
        try:
            player = mpv_module.MPV(
                wid=str(self.__surface.winfo_id()),
                idle=True,
                force_window="yes",
                osc=False,
                input_default_bindings=False,
                input_vo_keyboard=False,
                cursor_autohide="no",
                hwdec="auto-safe",
                # Al final se queda en pausa sobre el último fotograma en vez de
                # descargar el medio: es lo que se ve al cerrar el aviso de fin.
                keep_open="yes",
                ytdl=False,
                network_timeout=NETWORK_TIMEOUT_S,
                volume=self.volume,
                mute=self.__muted,
            )
        except Exception as exc:
            print(f"No se pudo crear el reproductor mpv: {exc}")
            return False

        def on_time(_name, value):
            self.__mpv_position = value

        def on_duration(_name, value):
            self.__mpv_duration = value

        def on_pause(_name, value):
            self.__mpv_paused = bool(value)

        def on_eof(_name, value):
            # Con keep-open el final no manda end-file: lo cuenta esta propiedad.
            if value is True:
                self.__events.put(("eof", None))

        player.observe_property("time-pos", on_time)
        player.observe_property("duration", on_duration)
        player.observe_property("pause", on_pause)
        player.observe_property("eof-reached", on_eof)

        @player.event_callback("start-file")
        def on_start_file(_event):
            self.__events.put(("start-file", None))

        @player.event_callback("playback-restart")
        def on_restart(_event):
            self.__events.put(("playback-restart", None))

        @player.event_callback("end-file")
        def on_end_file(event):
            data = getattr(event, "data", None)
            self.__events.put(("end-file", (int(getattr(data, "reason", -1)), getattr(data, "error", None))))

        self.__default_user_agent = player.user_agent
        self.__mpv = player
        self.__poll_job = self.after(POLL_MS, self.__poll)
        return True

    def __poll(self) -> None:
        """Recoge en el hilo de la interfaz lo que ha contado mpv y lo pinta."""
        self.__poll_job = None
        if self.__closed or not self.winfo_exists():
            return
        while True:
            try:
                kind, payload = self.__events.get_nowait()
            except queue.Empty:
                break
            self.__handle_event(kind, payload)
            if self.__closed:
                return
        self.__refresh_controls()
        self.__poll_job = self.after(POLL_MS, self.__poll)

    def __handle_event(self, kind: str, payload) -> None:
        if kind == "start-file":
            self.__awaiting_start = False
            self.__file_active = True
        elif kind == "playback-restart":
            if self.__file_active and not self.__started and self.__source is not None:
                self.__started = True
                self.__cancel_load_timeout()
                self.hide_card()
                if self.__on_started is not None:
                    self.__on_started()
        elif kind == "eof":
            if self.__awaiting_start or not self.__file_active or not self.__started or self.__ended:
                return
            self.__reach_end()
        elif kind == "end-file":
            reason, error = payload
            if self.__awaiting_start or not self.__file_active:
                return
            self.__file_active = False
            if reason == END_REASON_EOF:
                if self.__started and not self.__ended:
                    self.__reach_end()
            elif reason == END_REASON_ERROR:
                print(f"mpv no pudo reproducir el medio (error {error})")
                self.__source = None
                self.__refresh_controls()
                self.__on_error("El servidor no ha entregado el vídeo")

    def __reach_end(self) -> None:
        """El medio ha llegado al final: fin de episodio, o un corte si faltaba demasiado."""
        position, duration = self.__mpv_position, self.__mpv_duration
        if position is not None and duration and duration - position > END_TOLERANCE_S:
            print(f"El medio terminó en {format_time(position)} de {format_time(duration)}: "
                  f"se trata como un corte del servidor")
            self.__source = None
            self.__refresh_controls()
            self.__on_error("El servidor ha cortado el vídeo antes del final")
            return
        self.__ended = True
        self.__refresh_controls()
        if self.__on_end is not None:
            self.__on_end()

    # ---- Órdenes de la barra ----
    def toggle_pause(self) -> None:
        if self.__mpv is None:
            return
        if self.__ended and self.__source is not None:
            self.play(self.__source)
            return
        try:
            self.__mpv.pause = not self.__mpv_paused
            self.__mpv_paused = not self.__mpv_paused
        except Exception as exc:
            print(f"Error al pausar: {exc}")
        self.__refresh_controls()

    def seek_relative(self, seconds: float) -> None:
        """Salta ``seconds`` desde la posición actual, al fotograma exacto y no al clave."""
        if self.__mpv is None or not self.__started or self.__ended:
            return
        try:
            self.__mpv.command("seek", str(seconds), "relative+exact")
        except Exception as exc:
            print(f"Error al saltar {seconds} s: {exc}")

    def seek_fraction(self, fraction: float) -> None:
        """Salta a una fracción de la duración, al soltar la barra de progreso."""
        duration = self.__mpv_duration
        if self.__mpv is None or not self.__started or self.__ended or not duration:
            return
        target = max(0.0, min(1.0, fraction)) * duration
        # Hasta que mpv llegue, time-pos sigue contando la posición vieja y la
        # barra volvería atrás un instante: se enseña el destino mientras tanto.
        self.__seek_target = target
        self.__seek_hold = 20
        try:
            self.__mpv.command("seek", str(target), "absolute")
        except Exception as exc:
            print(f"Error al saltar a {target:.1f} s: {exc}")

    def set_volume(self, volume: float) -> None:
        self.volume = max(0.0, min(100.0, float(volume)))
        VideoPlayer._last_volume = self.volume
        if self.__mpv is not None:
            try:
                self.__mpv.volume = self.volume
            except Exception as exc:
                print(f"Error al cambiar el volumen: {exc}")
        self.__refresh_controls()

    def toggle_mute(self) -> None:
        self.__muted = not self.__muted
        VideoPlayer._last_muted = self.__muted
        if self.__mpv is not None:
            try:
                self.__mpv.mute = self.__muted
            except Exception as exc:
                print(f"Error al silenciar: {exc}")
        self.__refresh_controls()

    def request_fullscreen_toggle(self) -> None:
        if self.__on_fullscreen_request is not None:
            self.__on_fullscreen_request(not self.__fullscreen)

    def set_navigation(self, has_previous: bool, has_next: bool) -> None:
        """Habilita o apaga «episodio anterior» y «episodio siguiente» en las dos barras.

        :param has_previous: Si hay un episodio antes del que suena.
        :param has_next: Si hay uno después.
        """
        self.__has_previous = has_previous
        self.__has_next = has_next
        self.__refresh_controls()

    def go_previous(self) -> None:
        if self.__has_previous and self.__on_previous is not None:
            self.__on_previous()

    def go_next(self) -> None:
        if self.__has_next and self.__on_next is not None:
            self.__on_next()

    def __refresh_controls(self) -> None:
        position = self.__mpv_position
        if self.__seek_target is not None:
            if position is not None and abs(position - self.__seek_target) < 2 or self.__seek_hold <= 0:
                self.__seek_target = None
            else:
                self.__seek_hold -= 1
                position = self.__seek_target
        if self.__ended:
            position = self.__mpv_duration
        state = PlaybackState(
            enabled=self.__started and self.__source is not None,
            paused=self.__mpv_paused,
            ended=self.__ended,
            position=position if self.__started else None,
            duration=self.__mpv_duration if self.__started else None,
            volume=self.volume,
            muted=self.__muted,
            fullscreen=self.__fullscreen,
            has_previous=self.__has_previous,
            has_next=self.__has_next,
        )
        for controls in (self.__controls, self.__floating_controls):
            if controls is not None and controls.winfo_exists():
                controls.refresh(state)

    # ---- Tarjetas de estado ----
    def show_loading(self, title: str, subtitle: str) -> None:
        """Tarjeta de «Cargando» con el aro girando."""
        content = self.__new_card(boxed=False)
        frames = _ring_frames()
        ring = ctk.CTkLabel(content, text="", font=Theme.font(*Theme.T_UI), image=frames[0])
        ring.pack(pady=(0, 14))
        ctk.CTkLabel(content, text=title, font=Theme.font(15, True), text_color=Theme.BADGE_INK).pack()
        ctk.CTkLabel(content, text=subtitle, font=Theme.font(*Theme.T_SUB), text_color=Theme.TXT_3).pack(pady=(4, 0))
        self.__animate_ring(ring, frames, 0)

    def show_message(self, title: str, body: str,
                     buttons: List[Tuple[str, Callable[[], None], bool]],
                     icon: Optional[str] = None, subtitle: Optional[str] = None,
                     check_note: Optional[str] = None, closable: bool = False) -> None:
        """Tarjeta con título, texto y botones, en lugar de la superficie.

        :param buttons: (texto, acción, es_primario), de izquierda a derecha.
        :param icon: Glifo del recuadro de arriba, o None para no ponerlo.
        :param subtitle: Línea gris bajo el título.
        :param check_note: Franja con ✓ bajo el texto («Marcado como visto · 3 de 12»), o None.
        :param closable: Pone una ✕ arriba a la derecha que retira solo la tarjeta y
            deja a la vista la superficie con lo que tenga.
        """
        self.__surface.grid_remove()
        content = self.__new_card(boxed=True)
        wrap = Metrics.PLAYER_CARD_W - 56
        if closable:
            ctk.CTkButton(
                content.master, text="", font=Theme.font(*Theme.T_UI), width=30, height=30, corner_radius=7,
                fg_color=Theme.TRANSPARENT, hover_color=Theme.CARD_HOVER,
                image=player_icon("close", 16, Theme.TXT_3), command=self.hide_card
            ).place(relx=1.0, x=-14, y=14, anchor="ne")
            # El título no puede meterse debajo de la ✕.
            wrap -= 34
        if icon is not None:
            ctk.CTkLabel(content, text="", font=Theme.font(*Theme.T_UI), width=38, height=38, corner_radius=10, fg_color=Theme.ACCENT_SOFT,
                         image=player_icon(icon, color=Theme.ACCENT)).pack(anchor="w", pady=(0, 14))
        ctk.CTkLabel(content, text=title, font=Theme.font(20, True), text_color=Theme.TXT,
                     anchor="w", justify="left", wraplength=wrap).pack(anchor="w", fill="x")
        wrap = Metrics.PLAYER_CARD_W - 56
        if subtitle:
            ctk.CTkLabel(content, text=subtitle, font=Theme.font(*Theme.T_SUB), text_color=Theme.TXT_3,
                         anchor="w", justify="left", wraplength=wrap).pack(anchor="w", fill="x", pady=(5, 0))
        if body:
            ctk.CTkLabel(content, text=body, font=Theme.font(*Theme.T_UI), text_color=Theme.TXT_2,
                         anchor="w", justify="left", wraplength=wrap).pack(anchor="w", fill="x", pady=(8, 0))
        if check_note:
            strip = ctk.CTkFrame(content, height=1, corner_radius=9, fg_color=Theme.BG)
            strip.pack(fill="x", pady=(18, 0))
            ctk.CTkLabel(strip, text=f"  {check_note}", image=player_icon("check", 16, Theme.FIN_TXT),
                         compound="left", font=Theme.font(12), text_color=Theme.TXT_2,
                         fg_color=Theme.BG, anchor="w").pack(anchor="w", padx=13, pady=8)
        if buttons:
            row = ctk.CTkFrame(content, fg_color=Theme.TRANSPARENT, height=1)
            row.pack(fill="x", pady=(20, 0))
            for column, (text, command, primary) in enumerate(buttons):
                row.grid_columnconfigure(column, weight=1, uniform="card_buttons")
                ctk.CTkButton(
                    row, text=text, height=38, corner_radius=9, font=Theme.font(Theme.T_UI[0], True),
                    fg_color=Theme.ACCENT if primary else Theme.CARD,
                    hover_color=Theme.ACCENT if primary else Theme.CARD_HOVER,
                    text_color=Theme.ACCENT_INK if primary else Theme.TXT_2,
                    border_width=0 if primary else 1, border_color=Theme.LINE,
                    image=player_icon("play", 16, Theme.ACCENT_INK) if primary else None,
                    command=command
                ).grid(row=0, column=column, sticky="ew", padx=(0 if column == 0 else 10, 0))

    def hide_card(self) -> None:
        """Quita la tarjeta y deja a la vista la superficie."""
        self.__stop_ring()
        for child in self.__card_frame.winfo_children():
            child.destroy()
        self.__card_frame.grid_remove()
        self.__surface.grid()

    def is_card_visible(self) -> bool:
        return bool(self.__card_frame.winfo_manager())

    def __new_card(self, boxed: bool) -> ctk.CTkFrame:
        """Vacía el frame de tarjetas y lo pone por encima de la superficie."""
        self.__stop_ring()
        for child in self.__card_frame.winfo_children():
            child.destroy()
        self.__card_frame.grid()
        self.__card_frame.lift()
        # A pantalla completa la barra no se oculta mientras haya tarjeta, y si ya
        # se había ido hay que sacarla: es la salida del aviso.
        if self.__fullscreen:
            self.__show_floating_bar()
        if boxed:
            box = ctk.CTkFrame(self.__card_frame, width=Metrics.PLAYER_CARD_W, corner_radius=14,
                               fg_color=Theme.CARD, border_width=1, border_color=Theme.LINE)
            box.place(relx=0.5, rely=0.5, anchor="center")
            content = ctk.CTkFrame(box, fg_color=Theme.TRANSPARENT, width=Metrics.PLAYER_CARD_W - 56, height=1)
            content.pack(padx=28, pady=(26, 24))
            return content
        content = ctk.CTkFrame(self.__card_frame, fg_color=Theme.TRANSPARENT, height=1)
        content.place(relx=0.5, rely=0.5, anchor="center")
        return content

    def __animate_ring(self, ring: ctk.CTkLabel, frames: List[ctk.CTkImage], index: int) -> None:
        self.__ring_job = None
        if self.__closed or not ring.winfo_exists():
            return
        ring.configure(image=frames[index % len(frames)])
        self.__ring_job = self.after(RING_STEP_MS, self.__animate_ring, ring, frames, index + 1)

    def __stop_ring(self) -> None:
        if self.__ring_job is not None:
            self.after_cancel(self.__ring_job)
            self.__ring_job = None

    # ---- Tamaño ----
    def __on_configure(self, event) -> None:
        if not self.__fullscreen and event.widget is not None:
            self.relayout()

    def relayout(self) -> None:
        """Ajusta el alto del vídeo al ancho disponible: 16:9, sin pasar de media ventana."""
        if self.__fullscreen or not self.winfo_exists():
            return
        width = self.winfo_width()
        if width <= 1:
            return
        window_height = self.winfo_toplevel().winfo_height()
        height = min(round(width * 9 / 16), round(window_height * 0.5))
        height = max(180, height)
        logical = round(self._reverse_widget_scaling(height))
        if abs(int(self.__stage.cget("height")) - logical) > 1:
            self.__stage.configure(height=logical)

    # ---- Pantalla completa ----
    def set_fullscreen(self, fullscreen: bool) -> None:
        """Cambia la barra fija por la flotante, o al revés. La disposición la cambia el dueño antes.

        :param fullscreen: True para dejar solo el vídeo con la barra flotante.
        """
        if fullscreen == self.__fullscreen:
            return
        self.__fullscreen = fullscreen
        root = self.winfo_toplevel()
        if fullscreen:
            self.__controls.hide_volume()
            self.__controls.grid_remove()
            self.grid_rowconfigure(0, weight=1)
            # update() y no update_idletasks(): la barra se coloca con la
            # geometría del vídeo ya a pantalla completa.
            root.update()
            self.__create_floating_bar()
            self.__escape_funcid = root.bind_all("<Escape>", self.__on_escape)
            root.focus_force()
            self.__show_floating_bar()
            self.__foreground_job = self.after(FOREGROUND_CHECK_MS, self.__check_foreground)
        else:
            if self.__escape_funcid is not None:
                # unbind_all() no borra el comando Tcl, y ese comando retiene el reproductor.
                root.unbind_all("<Escape>")
                root.deletecommand(self.__escape_funcid)
                self.__escape_funcid = None
            for job in (self.__idle_job, self.__foreground_job):
                if job is not None:
                    self.after_cancel(job)
            self.__idle_job = self.__foreground_job = None
            if self.__floating_controls is not None:
                self.__floating_controls.destroy()
                self.__floating_controls = None
            if self.__floating_window is not None:
                self.__floating_window.destroy()
                self.__floating_window = None
            self.__set_cursor_hidden(False)
            self.grid_rowconfigure(0, weight=0)
            self.__controls.grid()
            self.relayout()
        self.__refresh_controls()

    def is_fullscreen(self) -> bool:
        return self.__fullscreen

    def __create_floating_bar(self) -> None:
        """La barra flotante: una ventana sin marco, siempre encima y pegada al borde inferior."""
        window = tkinter.Toplevel(self)
        window.withdraw()
        window.overrideredirect(True)
        window.attributes("-topmost", True)
        controls = PlayerControls(window, self, floating=True)
        controls.pack(fill="both", expand=True)
        left, top = self.__stage.winfo_rootx(), self.__stage.winfo_rooty()
        width, height = self.__stage.winfo_width(), self.__stage.winfo_height()
        bar_height = round(self._apply_widget_scaling(Metrics.PLAYER_FLOAT_BAR_H))
        tkinter.Toplevel.wm_geometry(window, f"{width}x{bar_height}+{left}+{top + height - bar_height}")
        window.bind("<Motion>", self.__on_motion, add="+")
        self.__floating_window = window
        self.__floating_controls = controls

    def __show_floating_bar(self) -> None:
        window = self.__floating_window
        if window is None or not window.winfo_exists():
            return
        if window.state() == "withdrawn":
            window.deiconify()
            window.lift()
            # Sin mapearla del todo, el primer clic sobre ella se pierde.
            window.update()
        self.__set_cursor_hidden(False)
        self.__restart_idle_timer()

    def __restart_idle_timer(self) -> None:
        if self.__idle_job is not None:
            self.after_cancel(self.__idle_job)
        self.__idle_job = self.after(IDLE_HIDE_MS, self.__hide_floating_bar_if_idle)

    def __hide_floating_bar_if_idle(self) -> None:
        """Oculta la barra y el cursor, salvo si el ratón está encima o hay algo que esperar."""
        self.__idle_job = None
        window = self.__floating_window
        if not self.__fullscreen or window is None or not window.winfo_exists():
            return
        controls = self.__floating_controls
        if (self.is_card_visible() or _pointer_inside(window)
                or (controls is not None and controls.is_volume_open())):
            self.__restart_idle_timer()
            return
        window.withdraw()
        self.__set_cursor_hidden(True)

    def __on_motion(self, _event=None) -> None:
        if self.__fullscreen and _foreground_is_ours():
            self.__show_floating_bar()

    def __check_foreground(self) -> None:
        """Si otra aplicación pasa a primer plano, la barra siempre-encima no puede quedarse flotando sobre ella."""
        self.__foreground_job = None
        if not self.__fullscreen:
            return
        if not _foreground_is_ours():
            if self.__floating_window is not None and self.__floating_window.winfo_exists():
                self.__floating_window.withdraw()
            if self.__floating_controls is not None:
                self.__floating_controls.hide_volume()
        self.__foreground_job = self.after(FOREGROUND_CHECK_MS, self.__check_foreground)

    def __set_cursor_hidden(self, hidden: bool) -> None:
        """mpv no ve el ratón, así que el cursor lo oculta Tk sobre la superficie."""
        cursor = "none" if hidden else ""
        for widget in (self.__stage, self.__surface, self.__card_frame):
            try:
                tkinter.Frame.configure(widget, cursor=cursor)
            except tkinter.TclError:
                pass

    def __on_escape(self, _event=None) -> None:
        if self.__fullscreen and self.__on_fullscreen_request is not None:
            self.__on_fullscreen_request(False)

    def destroy(self):
        self.close()
        super().destroy()
