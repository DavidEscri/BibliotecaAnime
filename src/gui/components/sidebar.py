__author__ = "Jose David Escribano Orts"
__subsystem__ = "gui.components"
__module__ = "sidebar.py"
__version__ = "0.2"
__info__ = {"subsystem": __subsystem__, "module_name": __module__, "version": __version__}

"""Barra lateral del rediseño: navegación, proveedor y apariencia.

Sustituye a los seis ``SidebarButton`` sueltos que se pintaban solos dentro de
``MainWindow.sidebar_frame`` y a los controles del pie. Los destinos siguen
siendo las mismas seis vistas: esta clase solo decide **cómo** se ven y cuál está
activo, nunca qué hacen.

Tres avisos que vienen de cómo era esto antes, o de tropezar con ellos aquí:

- La barra tiene ancho **fijo**: ``grid_propagate(False)`` más un ``minsize`` en
  la columna 0 del padre. Hacen falta los dos. Antes se declaraba 340 y acababa
  midiendo unos 220, porque los botones se construían con
  ``width=parent_frame.winfo_width()``, que vale 1 mientras Tk no ha mapeado el
  frame; y sin el ``minsize``, la rejilla de ``MainWindow`` le sigue robando
  píxeles cuando el área de contenido pide más ancho del que cabe.
- Todos los colores salen de ``Theme`` en tuplas ``(claro, oscuro)``, así que el
  cambio de apariencia lo resuelve CustomTkinter. **No** hay que recorrer los
  hijos reconfigurando colores a mano, que es lo que hacía
  ``change_appearance_mode_event()``.
- ⚠️ **Un ``CTkFrame`` sin hijos conserva su tamaño por defecto (200 × 200)** como
  tamaño pedido, y eso estira la fila que lo contiene. Es lo que dejó la barra
  con los seis destinos en blanco: la barrita de acento de 2 px inflaba la fila a
  200 y el icono y la etiqueta caían en ``y=86``, fuera de la parte visible. Todo
  ``CTkFrame`` decorativo o todavía vacío necesita ``height=`` explícito.
"""

from typing import Callable, Dict, List, Optional

import customtkinter as ctk

from APIs.common.animeProviderMgr import AnimeProviderManager
from dataPersistence.userPersistence import UserPersistence
from gui.theme import Metrics, Theme
from utils.buttons.utilsButtons import SidebarButton
from utils.utils import get_resource_path, load_dual_image


class _NavItem:
    """Un destino pintado en la barra: el marco, sus hijos y su estado activo.

    No hereda de ningún widget a propósito. Un ítem son cuatro piezas (barra de
    acento, icono, etiqueta y contador) que tienen que reaccionar juntas al hover
    y al clic, y en Tk los eventos de ``<Enter>`` / ``<Button-1>`` **no burbujean**
    desde los hijos: hay que atarlos uno a uno. Tenerlos agrupados aquí evita
    olvidarse de alguno.
    """

    def __init__(self, parent: ctk.CTkFrame, destination: SidebarButton,
                 on_click: Callable[["_NavItem"], None], show_counter: bool):
        self.destination = destination
        self.show_counter = show_counter
        self.__on_click = on_click
        self.__active = False
        self.__count: Optional[int] = None

        # --- desplegado -------------------------------------------------
        # El alto se fija con `minsize` en la fila y NO con `height=` +
        # `grid_propagate(False)`: medido, esa combinación deja el marco a 38 px
        # por fuera pero su rejilla interna sigue centrando los hijos como si
        # midiera los 200 por defecto de CTkFrame, y el icono y la etiqueta caen
        # en y=86, fuera de la parte visible. Con minsize la fila mide 38 de
        # verdad y el marco se ajusta a ella.
        self.expanded_frame = ctk.CTkFrame(
            parent,
            corner_radius=Metrics.RADIUS_CONTROL,
            fg_color=Theme.TRANSPARENT
        )
        self.expanded_frame.grid_columnconfigure(2, weight=1)
        self.expanded_frame.grid_rowconfigure(0, minsize=Metrics.NAV_ITEM_H)

        # Barra de acento de 2 px. Siempre está; lo que cambia es su color, para
        # que el texto no se desplace al activarse el ítem.
        #
        # ⚠️ El `height` NO es decorativo. Un CTkFrame **sin hijos** conserva su
        # alto por defecto (200) como tamaño pedido, así que sin esto la barra
        # infla la fila entera a 200 px: el marco se queda en 38 por fuera pero su
        # rejilla interna centra el icono y la etiqueta en y=86, fuera de la parte
        # visible. Síntoma: la barra lateral sale con los seis destinos en blanco.
        self.accent_bar = ctk.CTkFrame(
            self.expanded_frame, width=2, height=Metrics.NAV_ITEM_H,
            corner_radius=0, fg_color=Theme.TRANSPARENT
        )
        self.accent_bar.grid(row=0, column=0, sticky="ns")

        self.expanded_icon = destination.sidebar_icon((Metrics.NAV_ICON, Metrics.NAV_ICON))
        self.icon_label = ctk.CTkLabel(self.expanded_frame, text="", image=self.expanded_icon)
        self.icon_label.grid(row=0, column=1, padx=(Metrics.NAV_ITEM_PAD_X - 2, Metrics.NAV_ITEM_GAP))

        self.text_label = ctk.CTkLabel(
            self.expanded_frame,
            text=destination.sidebar_text,
            font=Theme.font(*Theme.T_UI),
            text_color=Theme.TXT_2,
            anchor="w"
        )
        self.text_label.grid(row=0, column=2, sticky="ew")

        self.count_label = ctk.CTkLabel(
            self.expanded_frame,
            text="",
            font=Theme.font(*Theme.T_META),
            text_color=Theme.TXT_3,
            anchor="e"
        )
        self.count_label.grid(row=0, column=3, padx=(4, Metrics.NAV_ITEM_PAD_X - 4))

        # --- plegado ----------------------------------------------------
        # Mismo motivo que arriba para el cuadrado de 48: minsize, no height=.
        self.collapsed_frame = ctk.CTkFrame(
            parent,
            corner_radius=Metrics.NAV_COLLAPSED_RADIUS,
            fg_color=Theme.TRANSPARENT
        )
        self.collapsed_frame.grid_rowconfigure(0, minsize=Metrics.NAV_COLLAPSED_SIZE)
        self.collapsed_frame.grid_columnconfigure(0, minsize=Metrics.NAV_COLLAPSED_SIZE)

        self.collapsed_icon = destination.sidebar_icon(
            (Metrics.NAV_COLLAPSED_ICON, Metrics.NAV_COLLAPSED_ICON)
        )
        self.collapsed_icon_label = ctk.CTkLabel(
            self.collapsed_frame, text="", image=self.collapsed_icon
        )
        self.collapsed_icon_label.grid(row=0, column=0)

        # El globo del contador va con place() y no con grid: se superpone al
        # icono en la esquina, no ocupa sitio en la rejilla.
        self.badge_label = ctk.CTkLabel(
            self.collapsed_frame,
            text="",
            width=Metrics.NAV_BADGE,
            height=Metrics.NAV_BADGE,
            corner_radius=Metrics.pill_radius(Metrics.NAV_BADGE),
            font=Theme.font(*Theme.T_META),
            fg_color=Theme.ACCENT_SOFT,
            text_color=Theme.ACCENT
        )

        for widget in self.__all_widgets():
            widget.bind("<Button-1>", self.__handle_click)
            widget.bind("<Enter>", self.__handle_enter)
            widget.bind("<Leave>", self.__handle_leave)
            widget.configure(cursor="hand2")

        self.__paint()

    # ------------------------------------------------------------------
    # Eventos
    # ------------------------------------------------------------------
    def __all_widgets(self) -> List[ctk.CTkBaseClass]:
        return [
            self.expanded_frame, self.accent_bar, self.icon_label,
            self.text_label, self.count_label,
            self.collapsed_frame, self.collapsed_icon_label, self.badge_label
        ]

    def __handle_click(self, _event=None) -> None:
        self.__on_click(self)

    def __handle_enter(self, _event=None) -> None:
        if self.__active:
            return
        self.expanded_frame.configure(fg_color=Theme.CARD_HOVER)
        self.collapsed_frame.configure(fg_color=Theme.CARD_HOVER)

    def __handle_leave(self, _event=None) -> None:
        if self.__active:
            return
        self.expanded_frame.configure(fg_color=Theme.TRANSPARENT)
        self.collapsed_frame.configure(fg_color=Theme.TRANSPARENT)

    # ------------------------------------------------------------------
    # Estado
    # ------------------------------------------------------------------
    def set_active(self, active: bool) -> None:
        self.__active = active
        self.__paint()

    def set_count(self, count: Optional[int]) -> None:
        """Fija el contador. ``None`` lo deja en blanco (es el caso de Buscar)."""
        self.__count = count
        self.__paint_count()

    def __paint(self) -> None:
        background = Theme.CARD if self.__active else Theme.TRANSPARENT
        self.expanded_frame.configure(fg_color=background)
        self.collapsed_frame.configure(fg_color=background)
        self.accent_bar.configure(fg_color=Theme.ACCENT if self.__active else Theme.TRANSPARENT)
        self.text_label.configure(text_color=Theme.TXT if self.__active else Theme.TXT_2)
        self.__paint_count()

    def __paint_count(self) -> None:
        if not self.show_counter or self.__count is None:
            self.count_label.configure(text="")
            self.badge_label.place_forget()
            return
        self.count_label.configure(text=str(self.__count))
        if self.__count > 0:
            # place() en coordenadas relativas para que el globo quede pegado a
            # la esquina superior derecha del cuadrado del icono.
            self.badge_label.place(relx=1.0, rely=0.0, x=-2, y=2, anchor="ne")
        else:
            self.badge_label.place_forget()
        self.badge_label.configure(text=str(self.__count))

    # ------------------------------------------------------------------
    # Disposición
    # ------------------------------------------------------------------
    def grid_expanded(self, row: int) -> None:
        self.collapsed_frame.grid_forget()
        self.expanded_frame.grid(row=row, column=0, sticky="ew", padx=10, pady=1)

    def grid_collapsed(self, row: int) -> None:
        self.expanded_frame.grid_forget()
        self.collapsed_frame.grid(row=row, column=0, pady=3)


class Sidebar(ctk.CTkFrame):
    """Barra lateral completa: cabecera, seis destinos, proveedor y apariencia.

    Es el ``sidebar_frame`` de ``MainWindow``: se sigue pudiendo ocultar con
    ``grid_forget()`` durante la pantalla de carga y volver a mostrar con
    ``grid()``, que es lo que hace ``RecentAnimeButton.show_frame()``.
    """

    #: Fila del espaciador que empuja el pie al fondo. Los destinos van por
    #: encima y el pie por debajo; si se añade un destino, esta constante sube.
    __SPACER_ROW = 20

    def __init__(self, main_window, destinations: List[SidebarButton],
                 counter_providers: Dict[str, Callable[[], int]]):
        """
        :param main_window: el hub. Se usa para el proveedor, las preferencias y
            para ``after()``; la barra no toca las listas de animes.
        :param destinations: las seis vistas, **en el orden en que se muestran**.
        :param counter_providers: contador por etiqueta de destino. Lo que no
            aparezca aquí se pinta sin número (es el caso de Buscar).
        """
        super().__init__(main_window, width=Metrics.SIDEBAR_W, corner_radius=0, fg_color=Theme.PANEL)

        self.__main_window = main_window
        self.__anime_provider_mgr: AnimeProviderManager = main_window.anime_provider_mgr
        self.__user_persistence: UserPersistence = main_window.user_persistence
        self.__counter_providers = counter_providers

        self.__collapsed: bool = self.__user_persistence.get_sidebar_collapsed()

        self.grid_propagate(False)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(self.__SPACER_ROW, weight=1)

        self.__build_header()
        self.__items: List[_NavItem] = [
            _NavItem(
                self,
                destination,
                on_click=self.__on_item_click,
                show_counter=destination.sidebar_text in counter_providers
            )
            for destination in destinations
        ]
        self.__build_provider_block()
        self.__build_appearance_block()

        self.__apply_collapsed_layout()
        self.refresh_counts()

    # ------------------------------------------------------------------
    # Construcción
    # ------------------------------------------------------------------
    def __build_header(self) -> None:
        self.__header_frame = ctk.CTkFrame(self, fg_color=Theme.TRANSPARENT, height=64)
        self.__header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(16, 12))
        self.__header_frame.grid_columnconfigure(0, weight=1)

        # Sin la palabra "Anime": cierra la tarea que anotaba main_window.py:32.
        # El inventario de tareas pendientes se hace por grep, así que este
        # comentario evita a propósito la palabra con la que se marcan: hablar de
        # una ya cerrada falsearía la cuenta.
        self.__title_label = ctk.CTkLabel(
            self.__header_frame,
            text="Mi Biblioteca",
            font=Theme.font(*Theme.T_VIEW),
            text_color=Theme.TXT,
            anchor="w"
        )
        self.__title_label.grid(row=0, column=0, sticky="w", padx=(8, 0))

        self.__collapse_button = ctk.CTkButton(
            self.__header_frame,
            text="«",
            width=28,
            height=28,
            corner_radius=Metrics.RADIUS_CONTROL,
            font=Theme.font(*Theme.T_UI),
            fg_color=Theme.TRANSPARENT,
            hover_color=Theme.CARD_HOVER,
            text_color=Theme.TXT_3,
            command=self.toggle_collapsed
        )
        self.__collapse_button.grid(row=0, column=1, sticky="e")

    def __build_provider_block(self) -> None:
        self.__provider_label = ctk.CTkLabel(
            self,
            text="PROVEEDOR",
            font=Theme.font(*Theme.T_LABEL),
            text_color=Theme.TXT_3,
            anchor="w"
        )

        self.__provider_frame = ctk.CTkFrame(self, fg_color=Theme.TRANSPARENT)
        self.__provider_frame.grid_columnconfigure(0, weight=1)

        # El contenido del desplegable sale SIEMPRE del manager: la GUI no
        # mantiene su propia lista de proveedores.
        providers_info = self.__anime_provider_mgr.list_providers_info()
        self.provider_optionmenu = ctk.CTkOptionMenu(
            self.__provider_frame,
            values=[provider_info.name for provider_info in providers_info],
            width=130,
            height=30,
            corner_radius=Metrics.RADIUS_CONTROL,
            font=Theme.font(*Theme.T_UI),
            dropdown_font=Theme.font(*Theme.T_UI),
            fg_color=Theme.CARD,
            button_color=Theme.CARD,
            button_hover_color=Theme.CARD_HOVER,
            text_color=Theme.TXT,
            dropdown_fg_color=Theme.CARD,
            dropdown_hover_color=Theme.CARD_HOVER,
            dropdown_text_color=Theme.TXT,
            command=self.__main_window.change_anime_provider_event
        )
        self.provider_optionmenu.grid(row=0, column=0, sticky="ew")
        current_provider_id = self.__anime_provider_mgr.get_default_provider_id()
        if current_provider_id is not None:
            self.provider_optionmenu.set(self.__anime_provider_mgr.get_provider_name(current_provider_id))

        # Los dos estados del pin se distinguen por color (azul fijado / gris sin
        # fijar) y no por relleno frente a contorno: contorneada, la silueta se
        # vuelve ilegible al bajar a los 20x20 a los que se pinta.
        icons_path = get_resource_path("resources/images/utils")
        self.__pin_icon_pinned = load_dual_image(
            f"{icons_path}/fijado_light.png", f"{icons_path}/fijado_dark.png", (20, 20)
        )
        self.__pin_icon_unpinned = load_dual_image(
            f"{icons_path}/no_fijado_light.png", f"{icons_path}/no_fijado_dark.png", (20, 20)
        )
        self.pin_provider_button = ctk.CTkButton(
            self.__provider_frame,
            text="",
            image=self.__pin_icon_unpinned,
            width=30,
            height=30,
            corner_radius=Metrics.RADIUS_CONTROL,
            fg_color=Theme.TRANSPARENT,
            hover_color=Theme.CARD_HOVER,
            command=self.__main_window.toggle_pinned_provider_event
        )
        self.pin_provider_button.grid(row=0, column=1, padx=(6, 0))

    def __build_appearance_block(self) -> None:
        self.__appearance_label = ctk.CTkLabel(
            self,
            text="APARIENCIA",
            font=Theme.font(*Theme.T_LABEL),
            text_color=Theme.TXT_3,
            anchor="w"
        )
        self.appearance_optionmenu = ctk.CTkOptionMenu(
            self,
            values=["Light", "Dark", "System"],
            height=30,
            corner_radius=Metrics.RADIUS_CONTROL,
            font=Theme.font(*Theme.T_UI),
            dropdown_font=Theme.font(*Theme.T_UI),
            fg_color=Theme.CARD,
            button_color=Theme.CARD,
            button_hover_color=Theme.CARD_HOVER,
            text_color=Theme.TXT,
            dropdown_fg_color=Theme.CARD,
            dropdown_hover_color=Theme.CARD_HOVER,
            dropdown_text_color=Theme.TXT,
            command=self.__main_window.change_appearance_mode_event
        )
        self.appearance_optionmenu.set("System")

    # ------------------------------------------------------------------
    # Plegado
    # ------------------------------------------------------------------
    def is_collapsed(self) -> bool:
        return self.__collapsed

    def toggle_collapsed(self) -> None:
        """Pliega o despliega la barra y **guarda** el estado en DB_user.db."""
        self.__collapsed = not self.__collapsed
        self.__apply_collapsed_layout()
        if not self.__user_persistence.set_sidebar_collapsed(self.__collapsed):
            # Perder la preferencia no puede impedir usar la aplicación: la barra
            # se queda como la ha dejado el usuario y solo se pierde el recuerdo.
            print(f"No se pudo guardar el estado de la barra lateral ({self.__collapsed})")

    def __apply_collapsed_layout(self) -> None:
        """Rehace la disposición según el estado plegado. Es idempotente."""
        width = Metrics.SIDEBAR_COLLAPSED_W if self.__collapsed else Metrics.SIDEBAR_W
        self.configure(width=width)
        # `grid_propagate(False)` evita que la barra encoja por su contenido, pero
        # NO evita que la rejilla del padre le robe píxeles cuando el área de
        # contenido pide más ancho del que cabe en la ventana: medido, se queda en
        # 219 en vez de 224. El minsize de la columna es lo que lo impide, y hay
        # que rehacerlo en cada plegado porque el ancho cambia.
        self.__main_window.grid_columnconfigure(0, weight=0, minsize=width)
        self.__collapse_button.configure(text="»" if self.__collapsed else "«")

        if self.__collapsed:
            self.__title_label.grid_remove()
            self.__header_frame.grid_columnconfigure(0, weight=0)
            self.__collapse_button.grid_configure(sticky="")
        else:
            self.__title_label.grid()
            self.__header_frame.grid_columnconfigure(0, weight=1)
            self.__collapse_button.grid_configure(sticky="e")

        for index, item in enumerate(self.__items):
            if self.__collapsed:
                item.grid_collapsed(index + 1)
            else:
                item.grid_expanded(index + 1)

        # Pie: las etiquetas de sección solo tienen sentido desplegada, y el
        # desplegable de apariencia no cabe a 84 px.
        footer_row = self.__SPACER_ROW + 1
        if self.__collapsed:
            self.__provider_label.grid_remove()
            self.__appearance_label.grid_remove()
            self.appearance_optionmenu.grid_remove()
            self.provider_optionmenu.grid_remove()
            self.__provider_frame.grid(row=footer_row + 1, column=0, pady=(0, 16))
            self.pin_provider_button.grid_configure(padx=0)
        else:
            self.__provider_label.grid(row=footer_row, column=0, sticky="ew", padx=18, pady=(0, 6))
            self.__provider_frame.grid(row=footer_row + 1, column=0, sticky="ew", padx=18)
            self.provider_optionmenu.grid()
            self.pin_provider_button.grid_configure(padx=(6, 0))
            self.__appearance_label.grid(row=footer_row + 2, column=0, sticky="ew", padx=18, pady=(16, 6))
            self.appearance_optionmenu.grid(row=footer_row + 3, column=0, sticky="ew", padx=18, pady=(0, 20))

    # ------------------------------------------------------------------
    # Navegación
    # ------------------------------------------------------------------
    def __on_item_click(self, item: _NavItem) -> None:
        self.set_active(item.destination)
        item.destination.sidebar_command()

    def set_active(self, destination: SidebarButton) -> None:
        """Marca un destino como activo. Acepta la vista, no el ítem pintado.

        Es público porque hay navegación que no pasa por un clic: el arranque y
        la recarga de proveedor llaman a ``show_frame()`` directamente.
        """
        for item in self.__items:
            is_active = item.destination is destination
            item.set_active(is_active)

    def navigate_to(self, sidebar_text: str) -> bool:
        """Cambia de vista **como si se hubiera pulsado su ítem**: activo y pintado.

        Existe desde los estados vacíos de la fase 9: «Ir a Pendientes» tiene que
        dejar la barra señalando Pendientes, no la pestaña de la que se venía.
        Se busca por la etiqueta y no por la clase porque las etiquetas ya son la
        clave de ``counter_providers`` y viven en cada vista, no aquí.

        :param sidebar_text: etiqueta del destino («Viendo», «Buscar»…).
        :return: ``False`` si esa etiqueta no es ningún destino. No lanza: un
            estado vacío no puede tumbar la aplicación por una cadena mal escrita.
        """
        for item in self.__items:
            if item.destination.sidebar_text == sidebar_text:
                self.set_active(item.destination)
                item.destination.sidebar_command()
                return True
        print(f"Destino de barra lateral desconocido: {sidebar_text!r}")
        return False

    # ------------------------------------------------------------------
    # Contadores
    # ------------------------------------------------------------------
    def refresh_counts(self) -> None:
        """Relee los contadores de la barra desde las listas cacheadas del hub.

        Lo llaman las fases siguientes cada vez que se guarda o se quita un anime.
        Es barato: son ``len()`` sobre listas que ya están en memoria.
        """
        if not self.winfo_exists():
            return
        for item in self.__items:
            provider = self.__counter_providers.get(item.destination.sidebar_text)
            item.set_count(provider() if provider is not None else None)

    # ------------------------------------------------------------------
    # Proveedor
    # ------------------------------------------------------------------
    def refresh_pin_button(self, is_pinned: bool) -> None:
        """Sincroniza el icono del pin con la selección actual.

        Marcado (azul) significa "lo que estás usando es tu predeterminado"; en
        gris, que te has desviado solo para esta sesión.
        """
        if not self.pin_provider_button.winfo_exists():
            return
        self.pin_provider_button.configure(
            image=self.__pin_icon_pinned if is_pinned else self.__pin_icon_unpinned
        )

    def set_provider_name(self, provider_name: str) -> None:
        """Pone el desplegable en un proveedor concreto, sin disparar su comando."""
        if self.provider_optionmenu.winfo_exists():
            self.provider_optionmenu.set(provider_name)
