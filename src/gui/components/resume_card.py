__author__ = "Jose David Escribano Orts"
__subsystem__ = "gui.components"
__module__ = "resume_card.py"
__version__ = "0.2"
__info__ = {"subsystem": __subsystem__, "module_name": __module__, "version": __version__}

"""Banda «Retomar donde lo dejaste» de la portada: hasta tres tarjetas en fila.

Cada tarjeta responde a una sola pregunta —«¿por qué episodio iba?»— y por eso no
repite ni géneros ni sinopsis ni proveedor: eso está a un clic, en la ficha.

Los episodios de un ``AnimeRecord`` vienen en orden descendente, así que el
«siguiente» no es ``episodes[0]``; ``resume_progress()`` los ordena antes de
mirar nada y es el único sitio donde se calcula ese dato.

La banda no se pinta si no hay nada que retomar: ni etiqueta ni hueco.
"""

from typing import Callable, List, Optional, Tuple

import customtkinter as ctk

from dataPersistence.animesPersistence import AnimeRecord
from gui.theme import Metrics, Theme
from utils.utils import find_cached_poster_path, load_rounded_image


def resume_progress(anime_record: AnimeRecord) -> Tuple[Optional[int], int, float]:
    """Calcula por dónde iba el usuario en un anime guardado.

    :return: ``(siguiente_episodio, total, fracción_vista)``. ``siguiente`` es
        ``None`` cuando ya están todos vistos, y ``total`` vale 0 si la fila no
        tiene episodios guardados (pasa con filas viejas o con animes que se
        marcaron antes de abrir su ficha).
    """
    episodes = sorted(set(anime_record.episodes))
    watched = set(anime_record.watched_episodes)

    if not episodes:
        # Sin lista de episodios lo único fiable es el último visto. Se ofrece el
        # siguiente sin prometer un total que no se conoce.
        next_episode = (anime_record.last_watched_episode or 0) + 1
        return next_episode, 0, 0.0

    watched_known = watched & set(episodes)
    next_episode = next((episode for episode in episodes if episode not in watched_known), None)
    return next_episode, len(episodes), len(watched_known) / len(episodes)


def resume_caption(next_episode: Optional[int], total: int) -> str:
    """Texto de apoyo de la tarjeta, a partir de lo que devuelve ``resume_progress()``."""
    if next_episode is None:
        return f"Lo has visto entero · {total} episodio{'' if total == 1 else 's'}"
    if total:
        return f"Siguiente: episodio {next_episode} de {total}"
    return f"Siguiente: episodio {next_episode}"


class ResumeCard(ctk.CTkFrame):
    """Una tarjeta: póster, título a dos líneas, el episodio siguiente y el progreso."""

    #: Alto reservado al título. Dos líneas de `T_CARD`, para que las tres
    #: tarjetas de la fila queden alineadas aunque un título ocupe una sola.
    TITLE_H: int = 52
    #: Ancho de la columna de texto de la tarjeta. Es lo que se mide para recortar
    #: el título; el `wraplength` del propio label queda de red de seguridad.
    TEXT_W: int = 200

    def __init__(self, parent, anime_record: AnimeRecord,
                 on_click: Optional[Callable[[str], None]] = None, **kwargs):
        """Construye la tarjeta.

        :param anime_record: Fila que se enseña.
        :param on_click: Se llama con el anime_id al pulsar la tarjeta.
        """
        super().__init__(
            parent,
            corner_radius=Metrics.RADIUS_CARD,
            fg_color=Theme.CARD,
            border_width=1,
            border_color=Theme.LINE,
            **kwargs
        )
        self.anime_record = anime_record
        self.__on_click = on_click

        self.grid_columnconfigure(1, weight=1)

        poster_path = find_cached_poster_path(anime_record.anime_id) or ""
        #: Referencia viva a la imagen: Tk no la mantiene y el recolector dejaría
        #: la tarjeta en blanco.
        self.__image = load_rounded_image(
            poster_path, Metrics.RESUME_CARD_POSTER, Metrics.RADIUS_CONTROL
        )
        poster_label = ctk.CTkLabel(self, text="", image=self.__image)
        poster_label.grid(row=0, column=0, rowspan=3, padx=(14, 12), pady=14, sticky="n")

        title_font = Theme.font(*Theme.T_CARD)
        title_label = ctk.CTkLabel(
            self,
            text=Theme.ellipsize(anime_record.title, title_font, self.TEXT_W, 2),
            font=title_font,
            text_color=Theme.TXT,
            wraplength=self.TEXT_W,
            height=self.TITLE_H,
            justify="left",
            anchor="nw"
        )
        title_label.grid(row=0, column=1, sticky="ew", padx=(0, 14), pady=(14, 0))

        self.__caption_label = ctk.CTkLabel(
            self,
            text="",
            font=Theme.font(*Theme.T_UI),
            text_color=Theme.TXT_2,
            anchor="w"
        )
        self.__caption_label.grid(row=1, column=1, sticky="ew", padx=(0, 14))

        self.__progress_bar = ctk.CTkProgressBar(
            self,
            height=Metrics.PROGRESS_H,
            corner_radius=Metrics.PROGRESS_RADIUS,
            fg_color=Theme.LINE_SOFT,
            progress_color=Theme.ACCENT
        )
        self.__progress_bar.grid(row=2, column=1, sticky="ew", padx=(0, 14), pady=(10, 16))
        self.__apply_progress()

        if self.__on_click is None:
            return
        # Los eventos de Tk no burbujean: hay que atar el clic a cada pieza.
        for widget in (self, poster_label, title_label, self.__caption_label, self.__progress_bar):
            widget.bind("<Button-1>", self.__handle_click)
            widget.bind("<Enter>", self.__handle_enter)
            widget.bind("<Leave>", self.__handle_leave)
            widget.configure(cursor="hand2")

    def update_record(self, anime_record: AnimeRecord) -> None:
        """Repinta el progreso con una fila recién leída de la BD.

        Solo se tocan el pie y la barra: el anime es el mismo, así que recrear la
        tarjeta únicamente serviría para releer el póster del disco y hacer
        parpadear la banda entera.
        """
        self.anime_record = anime_record
        self.__apply_progress()

    def __apply_progress(self) -> None:
        """Vuelca en el pie y en la barra lo que dice ``resume_progress()``."""
        next_episode, total, fraction = resume_progress(self.anime_record)
        self.__caption_label.configure(text=resume_caption(next_episode, total))
        self.__progress_bar.set(1.0 if next_episode is None else fraction)

    def __handle_click(self, _event=None) -> None:
        """Delega en on_click con el anime_id de la tarjeta."""
        self.__on_click(self.anime_record.anime_id)

    def __handle_enter(self, _event=None) -> None:
        """Aplica el estilo de hover."""
        self.configure(fg_color=Theme.CARD_HOVER, border_color=Theme.ACCENT)

    def __handle_leave(self, _event=None) -> None:
        """Restaura el estilo normal."""
        self.configure(fg_color=Theme.CARD, border_color=Theme.LINE)


class ResumeBand(ctk.CTkFrame):
    """Etiqueta de sección más las tarjetas, en una fila de columnas iguales.

    Quien la coloca debe comprobar ``has_content()`` antes de meterla en la
    rejilla: sin tarjetas no se pinta ni etiqueta ni hueco.
    """

    def __init__(self, parent, anime_records: List[AnimeRecord],
                 on_click: Optional[Callable[[str], None]] = None,
                 title: str = "RETOMAR DONDE LO DEJASTE", **kwargs):
        """Construye la banda.

        :param anime_records: Filas a mostrar, hasta tres.
        :param on_click: Se llama con el anime_id al pulsar una tarjeta.
        :param title: Etiqueta de sección, en mayúsculas.
        """
        super().__init__(parent, height=1, corner_radius=0, fg_color=Theme.TRANSPARENT, **kwargs)

        self.__records = list(anime_records)
        #: Las tarjetas en el mismo orden que ``__records``, para poder refrescar
        #: una sola sin recorrer los hijos de Tk ni recrear la banda.
        self.__cards: List[ResumeCard] = []
        if not self.__records:
            # Sin tarjetas la banda se queda vacía a propósito: quien la coloca
            # consulta has_content() y ni siquiera la mete en la rejilla.
            return

        label = ctk.CTkLabel(
            self,
            text=title,
            font=Theme.font(*Theme.T_LABEL),
            text_color=Theme.TXT_3,
            anchor="w"
        )
        label.grid(row=0, column=0, columnspan=len(self.__records), sticky="w", pady=(0, 10))

        for index, anime_record in enumerate(self.__records):
            self.grid_columnconfigure(index, weight=1, uniform="resume")
            card = ResumeCard(self, anime_record, on_click=on_click)
            self.__cards.append(card)
            card.grid(
                row=1, column=index, sticky="ew",
                padx=(0 if index == 0 else Metrics.GRID_GAP_X // 2,
                      0 if index == len(self.__records) - 1 else Metrics.GRID_GAP_X // 2)
            )

    def has_content(self) -> bool:
        """``True`` si hay al menos una tarjeta que pintar."""
        return bool(self.__records)

    def update_record(self, anime_record: AnimeRecord) -> bool:
        """Refresca la tarjeta de ese anime con una fila nueva, si está en la banda.

        Se busca por ``anime_id`` y no por posición: entre que se pidieron los
        datos y llegan, la banda pudo repintarse con otro reparto.

        :return: ``True`` si había una tarjeta que refrescar.
        """
        for card in self.__cards:
            if card.anime_record.anime_id == anime_record.anime_id:
                card.update_record(anime_record)
                return True
        return False
