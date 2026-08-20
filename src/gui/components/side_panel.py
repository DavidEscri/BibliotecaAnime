__author__ = "Jose David Escribano Orts"
__subsystem__ = "gui.components"
__module__ = "side_panel.py"
__version__ = "0.1"
__info__ = {"subsystem": __subsystem__, "module_name": __module__, "version": __version__}

"""Panel lateral de «Viendo»: la tarjeta grande de lo último que estabas viendo.

Es la contrapartida de la banda «Retomar» de la portada: allí caben tres tarjetas
pequeñas porque la portada va de novedades; aquí, en la vista que existe para
seguir viendo, el candidato número uno se enseña en grande y con su acción propia.

Se alimenta de la **misma** preferencia que la banda
(``UserSettingKey.LAST_WATCHED_ANIME_IDS``, fase 2) y del **mismo** cálculo de
progreso (``resume_card.resume_progress()``), que sigue siendo el único sitio donde
se decide por qué episodio ibas.

⚠️ El ancho de 290 px del diseño no es un número suelto: son los 248 px a los que
se guarda el póster en disco (``Metrics.SHEET_POSTER``) más 21 px de aire a cada
lado. Así el póster se pinta a tamaño natural, sin ampliar un JPG, y sale la
proporción 2:3 que pide `DISENO.md` §3.
"""

from typing import Any, Callable, Optional

import customtkinter as ctk

from dataPersistence.animesPersistence import AnimeRecord
from gui.components.resume_card import resume_progress
from gui.theme import Metrics, Theme
from utils.utils import find_cached_poster_path, load_rounded_image


class SidePanel(ctk.CTkFrame):
    """Tarjeta grande de retomar, de ancho fijo.

    Uso típico::

        panel = SidePanel(body, anime_record, provider_name="AnimeFLV",
                          on_action=self.__on_anime_click)
        panel.grid(row=0, column=1, sticky="n")

    Quien lo coloca decide si hay algo que enseñar: sin ``anime_record`` el panel
    no se construye, igual que la banda de la portada no se pinta vacía.
    """

    #: Aire entre el borde de la tarjeta y su contenido. Ver la nota del módulo:
    #: 248 + 21 * 2 = 290, el ancho del panel.
    CARD_PAD: int = 21
    #: Alto del botón de acción, del diseño.
    ACTION_H: int = 38

    def __init__(self, parent, anime_record: AnimeRecord,
                 provider_name: Optional[str] = None,
                 on_action: Optional[Callable[[Any], None]] = None,
                 on_click: Optional[Callable[[Any], None]] = None,
                 title: str = "LO ÚLTIMO QUE VEÍAS", **kwargs):
        """
        :param anime_record: fila que se enseña. No puede ser ``None``.
        :param provider_name: nombre legible del proveedor de la fila; se muestra
            junto al episodio. ``None`` lo omite.
        :param on_action: qué hace el botón. Recibe el ``anime_id``.
        :param on_click: qué hace pulsar el póster o el título. Por defecto, lo
            mismo que el botón.
        :param title: etiqueta de sección, en mayúsculas.
        """
        super().__init__(parent, width=Metrics.SIDE_PANEL_W, height=1,
                         corner_radius=0, fg_color=Theme.TRANSPARENT, **kwargs)

        self.anime_record = anime_record
        self.__on_action = on_action
        self.__on_click = on_click or on_action

        label = ctk.CTkLabel(
            self,
            text=title,
            font=Theme.font(*Theme.T_LABEL),
            text_color=Theme.TXT_3,
            anchor="w"
        )
        label.grid(row=0, column=0, sticky="w", pady=(0, 10))

        card = ctk.CTkFrame(
            self,
            corner_radius=Metrics.RADIUS_CARD,
            fg_color=Theme.CARD,
            border_width=1,
            border_color=Theme.LINE
        )
        card.grid(row=1, column=0, sticky="ew")
        card.grid_columnconfigure(0, weight=1)

        poster_path = find_cached_poster_path(anime_record.anime_id) or ""
        #: Referencia viva a la imagen: Tk no la mantiene y el panel saldría en blanco.
        self.__image = load_rounded_image(poster_path, Metrics.SHEET_POSTER, Metrics.RADIUS_POSTER)
        poster_label = ctk.CTkLabel(card, text="", image=self.__image)
        poster_label.grid(row=0, column=0, padx=self.CARD_PAD, pady=(self.CARD_PAD, 0))

        text_width = Metrics.SHEET_POSTER[0]
        title_font = Theme.font(*Theme.T_CARD)
        title_label = ctk.CTkLabel(
            card,
            text=Theme.ellipsize(anime_record.title, title_font, text_width, 2),
            font=title_font,
            text_color=Theme.TXT,
            wraplength=text_width,
            justify="left",
            anchor="w"
        )
        title_label.grid(row=1, column=0, sticky="ew", padx=self.CARD_PAD, pady=(15, 0))

        next_episode, total, fraction = resume_progress(anime_record)
        caption_font = Theme.font(*Theme.T_SUB)
        caption_label = ctk.CTkLabel(
            card,
            text=self.__fitted_caption(provider_name, caption_font, text_width),
            width=text_width,
            font=caption_font,
            text_color=Theme.TXT_3,
            anchor="w"
        )
        caption_label.grid(row=2, column=0, sticky="ew", padx=self.CARD_PAD, pady=(9, 0))

        progress_frame = ctk.CTkFrame(card, height=1, fg_color=Theme.TRANSPARENT)
        progress_frame.grid(row=3, column=0, sticky="ew", padx=self.CARD_PAD, pady=(12, 0))
        progress_frame.grid_columnconfigure(0, weight=1)

        progress_bar = ctk.CTkProgressBar(
            progress_frame,
            # El ancho lo pone el `sticky="ew"` de la columna, no este número. Va
            # pequeño a propósito: una CTkProgressBar pide 200 px por defecto y,
            # sumada al contador, hacía que la tarjeta reclamara 330 px de ancho en
            # vez de los 290 del diseño.
            width=100,
            height=Metrics.PROGRESS_H,
            corner_radius=Metrics.PROGRESS_RADIUS,
            fg_color=Theme.LINE,
            progress_color=Theme.ACCENT
        )
        progress_bar.set(1.0 if next_episode is None else fraction)
        progress_bar.grid(row=0, column=0, sticky="ew")

        watched = len(set(anime_record.watched_episodes) & set(anime_record.episodes))
        counter_label = ctk.CTkLabel(
            progress_frame,
            # Monoespaciada: es el único número de la vista que se lee como cifra
            # («12 / 24»), y con Segoe UI los dígitos bailan de ancho.
            text=f"{watched} / {total}" if total else "—",
            font=Theme.font(*Theme.T_NUM),
            text_color=Theme.TXT_3,
            anchor="e"
        )
        counter_label.grid(row=0, column=1, padx=(11, 0))

        action_button = ctk.CTkButton(
            card,
            text=self.__action_text(next_episode),
            height=self.ACTION_H,
            corner_radius=Metrics.RADIUS_POSTER,
            font=Theme.font(13, True, False),
            fg_color=Theme.ACCENT,
            hover_color=Theme.ACCENT,
            text_color=Theme.ACCENT_INK,
            command=self.__handle_action
        )
        action_button.grid(row=4, column=0, sticky="ew",
                           padx=self.CARD_PAD, pady=(16, self.CARD_PAD))

        if self.__on_click is None:
            return
        # Los eventos de Tk no burbujean: el clic va atado pieza a pieza. El botón
        # se queda fuera, que ya tiene su propio comando.
        for widget in (poster_label, title_label, caption_label):
            widget.bind("<Button-1>", self.__handle_click)
            widget.configure(cursor="hand2")

    # ------------------------------------------------------------------
    # Textos
    # ------------------------------------------------------------------
    def __caption(self, provider_name: Optional[str]) -> str:
        """«Lo dejaste en el episodio N · Proveedor»."""
        last_watched = self.anime_record.last_watched_episode or 0
        left = (f"Lo dejaste en el episodio {last_watched}" if last_watched
                else "Todavía no has visto ningún episodio")
        return f"{left} · {provider_name}" if provider_name else left

    def __fitted_caption(self, provider_name: Optional[str], font: ctk.CTkFont, width: int) -> str:
        """El pie de la tarjeta, en la forma más larga que quepa en una línea.

        Es la línea que más crece de la tarjeta y no puede pasar del ancho del
        póster: si lo pasa, es ella la que decide el ancho y la tarjeta deja de
        medir los 290 px del diseño. Con un anime largo —«Lo dejaste en el
        episodio 1163 · AnimeAV1» son 249 px— recortar con puntos suspensivos se
        comía justo el nombre del proveedor, que es la mitad del dato; se prefiere
        decir lo mismo con menos palabras.
        """
        full = self.__caption(provider_name)
        if font.measure(full) <= width:
            return full
        if not provider_name:
            return Theme.ellipsize(full, font, width, 1)
        last_watched = self.anime_record.last_watched_episode or 0
        # Sin nada visto no se abrevia con «Episodio 0»: ese episodio no existe y
        # el usuario lo leería como un dato, no como un «aún no has empezado».
        short = (f"Episodio {last_watched} · {provider_name}" if last_watched
                 else f"Sin empezar · {provider_name}")
        if font.measure(short) <= width:
            return short
        return Theme.ellipsize(short, font, width, 1)

    def __action_text(self, next_episode: Optional[int]) -> str:
        """«Seguir por el N», o abrir la ficha si ya no queda episodio por ver."""
        if next_episode is None:
            return "Abrir la ficha"
        return f"Seguir por el {next_episode}"

    # ------------------------------------------------------------------
    # Interacción
    # ------------------------------------------------------------------
    def __handle_action(self) -> None:
        if self.__on_action is not None:
            self.__on_action(self.anime_record.anime_id)

    def __handle_click(self, _event=None) -> None:
        self.__on_click(self.anime_record.anime_id)
