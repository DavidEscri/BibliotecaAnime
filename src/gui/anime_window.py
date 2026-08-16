__author__ = "Jose David Escribano Orts"
__subsystem__ = "gui"
__module__ = "anime_window.py"
__version__ = "0.6"
__info__ = {"subsystem": __subsystem__, "module_name": __module__, "version": __version__}

import difflib
import threading
import time
import webbrowser
import customtkinter as ctk

from dataclasses import replace
from tkinter import messagebox
from typing import List, Optional, Union

from APIs.common.models import AnimeInfo, AnimeProviderId, EpisodeInfo, ServerInfo
from APIs.common.animeProviderMgr import AnimeProviderManager, AnimeProviderManagerSingleton
from dataPersistence.animesPersistence import AnimeStatus, AnimeRecord
from utils import utils
from utils.buttons import utilsButtons
from utils.utils import refactor_genre_text, get_resource_path, get_anime_image, download_anime_poster_by_status, \
    move_anime_poster_by_status, remove_anime_poster_by_status

#: Similitud mínima entre títulos para dar por hecho que un anime que se va a
#: guardar es el mismo que otro que ya está en la biblioteca. Va **muy por
#: encima** del umbral con el que se busca (0.75-0.8) a propósito: aquí un falso
#: positivo interrumpe al usuario con un diálogo por dos animes distintos de la
#: misma saga ("One Piece" y "One Piece Film: Red"), mientras que un falso
#: negativo solo deja pasar el duplicado que ya se colaba antes.
DUPLICATE_TITLE_THRESHOLD = 0.9

#: Cómo se llama cada estado de cara al usuario. En los diálogos hay que nombrar
#: la sección concreta ("tu Biblioteca de Favoritos") y no "tu biblioteca" a
#: secas: es la que el usuario acaba de pulsar y la que va a mirar después.
STATUS_SECTION_NAMES = {
    AnimeStatus.FAVOURITE: "Favoritos",
    AnimeStatus.WATCHING:  "Viendo",
    AnimeStatus.FINISHED:  "Finalizados",
    AnimeStatus.PENDING:   "Pendientes",
}


# TODO: Al final de la lista de episodios nuevo frame del estilo. "Si te ha gustado One piece, te puede interesar..." y
#  mostrar 4 animes con los mimos generos.

# TODO: Agregar botón para alternar entre el manga y el anime.


def show_anime_info_error(anime_id: Union[str, int]) -> None:
    """
    Avisa al usuario de que no se ha podido recuperar la ficha de un anime.

    `AnimeProviderManager.get_anime_info` nunca propaga excepciones: si fallan
    todos los proveedores devuelve None. Sin este aviso, el clic simplemente no
    hace nada (Tkinter se traga la excepción del callback) y la aplicación
    parece colgada.

    :param anime_id: Identificador del anime que no se ha podido cargar.
    """
    print(f"No se pudo obtener la información del anime {anime_id}: ningún proveedor respondió")
    messagebox.showerror(
        "No se pudo cargar el anime",
        "No se ha podido obtener la información de este anime.\n\n"
        "Comprueba tu conexión a internet e inténtalo de nuevo más tarde."
    )


def find_saved_duplicate(anime_records: List[AnimeRecord], title: str,
                         exclude_anime_id: Optional[str] = None) -> Optional[AnimeRecord]:
    """Busca en la biblioteca un anime que sea **el mismo** que ``title``.

    Sirve para no guardar dos veces el mismo anime cuando se abre desde un
    proveedor distinto al que lo guardó.

    Compara por título normalizado (sin tildes, ni mayúsculas, ni signos), que es
    lo único común entre proveedores. No detecta títulos completamente distintos
    para el mismo anime ("Solo Leveling" y "Ore dake Level Up na Ken"): eso no
    hay forma de saberlo sin preguntar a la red, y esto corre en el hilo de la
    interfaz.

    :param exclude_anime_id: fila que no cuenta como duplicado (normalmente, la
        del propio anime que se está guardando).
    :return: el ``AnimeRecord`` más parecido si supera
        ``DUPLICATE_TITLE_THRESHOLD``, o ``None``.
    """
    normalized_title = AnimeProviderManager.normalize_title(title)
    if not normalized_title:
        return None

    best_record: Optional[AnimeRecord] = None
    best_ratio: float = 0.0
    for anime_record in anime_records:
        if exclude_anime_id is not None and str(anime_record.anime_id) == str(exclude_anime_id):
            continue
        normalized_candidate = AnimeProviderManager.normalize_title(anime_record.title)
        if normalized_candidate == normalized_title:
            return anime_record
        ratio = difflib.SequenceMatcher(None, normalized_title, normalized_candidate).ratio()
        if ratio > best_ratio:
            best_record, best_ratio = anime_record, ratio

    return best_record if best_ratio >= DUPLICATE_TITLE_THRESHOLD else None


def open_saved_anime(main_window, anime_id: Union[str, int]) -> None:
    """Abre la ficha de un anime **ya guardado** en la biblioteca.

    Punto de entrada único de las cuatro vistas de estado (favoritos, viendo,
    finalizados y pendientes), que repetían estas mismas líneas una por una.

    El fallback sigue activo a propósito: la propiedad de un slug caduca (hay
    animes guardados que AnimeAV1 servía y hoy devuelven 404), así que fijar el
    proveedor de la fila con ``strict=True`` convertiría un anime que hoy se abre
    despacio en uno que no se abre.

    En el hilo secundario va **solo la petición**. El repintado vuelve al hilo de
    Tkinter con ``after(0, ...)``, que es la regla del proyecto y no una
    formalidad: ``display_anime_info()`` empieza destruyendo los widgets de la
    vista anterior.

    :param main_window: hub de la aplicación (`MainWindow`).
    :param anime_id: ``anime_id`` de la fila, es decir, el slug del proveedor que
        la guardó.
    """
    anime_record: AnimeRecord = main_window.animes_persistence.get_anime_by_anime_id(anime_id)
    provider_id, is_deviation = main_window.provider_for_saved_anime(anime_record.provider_id if anime_record is not None else None)

    main_window.configure(cursor="watch")
    # update_idletasks(): así un segundo clic no puede reentrar aquí y lanzar un segundo hilo.
    main_window.update_idletasks()

    def _show(anime_info, served_by):
        """Ya en el hilo de Tkinter: aquí se toca la interfaz, y solo aquí."""
        if not main_window.winfo_exists():
            return
        main_window.configure(cursor="")
        if anime_info is None:
            show_anime_info_error(anime_id)
            return
        # anime_record va aparte del AnimeInfo y no es redundante: cuando el
        # usuario se ha desviado de proveedor, `anime_info` es la ficha del sitio
        # elegido y su `id` es OTRO slug, así que sin la fila la ficha escribiría
        # con el identificador equivocado y duplicaría el anime.
        AnimeWindowViewer(main_window, anime_info, served_by,
                          anime_record=anime_record).display_anime_info()

    def _load_and_show():
        anime_info = served_by = None
        if is_deviation and anime_record is not None:
            # El usuario se ha desviado en el desplegable. El slug guardado es el
            # del proveedor que lo guardó, así que en el elegido no vale: hay que
            # volver a localizar el anime por su título.
            reference = AnimeInfo(
                id=anime_record.anime_id,
                title=anime_record.title,
                poster=anime_record.poster_url
            )
            resolved = main_window.anime_provider_mgr.resolve_anime_in_provider(reference, provider_id)
            if resolved is not None:
                anime_info, served_by = resolved, provider_id
            else:
                # Que el proveedor elegido no lo tenga provoca que se sigue por la vía normal y la ficha mostrará
                # quién lo ha servido de verdad.
                print(f"[{provider_id.value}] no tiene {anime_record.title!r}; "
                      f"se abre con el proveedor habitual")

        if anime_info is None:
            anime_info, served_by = main_window.anime_provider_mgr.get_anime_info_with_provider(anime_id, provider_id=None if is_deviation else provider_id)

        main_window.after(0, _show, anime_info, served_by)

    threading.Thread(target=_load_and_show, daemon=True).start()


class AnimeWindowViewer:
    """Ficha de detalle de un anime. No es una ventana: reemplaza el contenido de
    ``main_window.content_frame``.

    **Maneja dos identidades distintas del mismo anime**, y confundirlas duplica
    datos en la biblioteca del usuario:

    - *Identidad de visualización* (``self.anime_info``, ``self.provider_id``): la
      del proveedor que sirvió la ficha, que es el que muestra la etiqueta
      «Proveedor:». De aquí salen título, sinopsis, géneros, episodios y servidores.
    - *Identidad de persistencia* (``self.persistence_anime_id``,
      ``self.persistence_poster_url`` y ``self.persistence_provider_id``): la de la
      **fila guardada** (el ``anime_record`` del constructor) y, si no está
      guardado, la del ``AnimeInfo`` con el que se abrió la ficha. **Nunca cambia
      mientras la ficha está en pantalla.** Es la que se usa en toda operación de
      BD y en todo fichero de póster.

    El motivo es que ``AnimeInfo.id`` es el *slug* del sitio, no un identificador
    universal: el mismo anime es "one-piece" en AnimeAV1 y
    "one-piece-tv" en AnimeFLV. Si se persistiera con el id del proveedor que sirvió
    la ficha en vez de con el de apertura, «añadir a favoritos» insertaría una
    **fila nueva** en ANIMES y el mismo anime aparecería dos veces.

    Las dos identidades **siguen sin poder fundirse** aunque la ficha ya no
    permita cambiar de proveedor: el fallback puede servirla desde un proveedor
    distinto al que guardó la fila, y desviarse en el desplegable de la sidebar
    la abre directamente con el slug de otro sitio.

    Cuando se separan, la ficha lo dice y ofrece juntarlas de la única forma que
    no pierde datos: reapuntar la fila a otro proveedor
    (``__repair_to_target_provider``), que también sirve para llevártela al
    proveedor que estés usando aunque no haya nada partido.

    Ver .claude/docs/13-selector-de-proveedor.md (decisión D5).
    """

    def __init__(self, main_window, anime_info: AnimeInfo, provider_id: AnimeProviderId | None = None,
                 anime_record: AnimeRecord | None = None):
        """
        :param anime_info: ficha del anime. No puede ser ``None``.
        :param provider_id: proveedor que sirvió esa ficha. Si se omite se usa el
            que traiga el propio ``AnimeInfo`` (lo estampa el manager al responder)
            y, en último caso, el predeterminado.
        :param anime_record: fila con la que está guardado este anime en la
            biblioteca, si lo está. **Obligatorio cuando la ficha puede venir de
            un proveedor distinto al que la guardó**: es de donde sale la
            identidad de persistencia. Sin él se asume que ``anime_info`` es
            también lo guardado, que es cierto al abrir desde recientes o desde
            una búsqueda, pero no al abrir un anime de la biblioteca con el
            desplegable desviado.
        """
        if anime_info is None:
            raise ValueError("AnimeWindowViewer requiere un AnimeInfo; se recibió None")
        self.main_window = main_window
        self.anime_provider_mgr: AnimeProviderManager = AnimeProviderManagerSingleton()
        self.anime_info: AnimeInfo = self.__with_episodes(anime_info)

        self.provider_id: AnimeProviderId | None = (provider_id or anime_info.provider_id or self.anime_provider_mgr.get_default_provider_id())

        # Identidad de persistencia: se congela aquí y no se vuelve a tocar.
        #
        # Solo se separa de la de visualización cuando el slug que se está viendo
        # NO es el guardado, es decir, cuando la ficha se ha localizado por título
        # en otro proveedor. Si los dos slugs coinciden manda el de visualización
        # aunque haya entrado el fallback: ahí el proveedor que respondió sí sirve
        # ese slug, y es la respuesta correcta para el autorrelleno de la columna.
        is_split_identity = (anime_record is not None and str(anime_record.anime_id) != str(anime_info.id))
        self.persistence_anime_id: str = (str(anime_record.anime_id) if is_split_identity else str(anime_info.id))
        self.persistence_poster_url: str = anime_info.poster
        self.persistence_provider_id: AnimeProviderId | None = (
            anime_record.provider_id if is_split_identity else self.provider_id)

        # Proveedor que consta en la fila de la biblioteca. Lo rellena
        # __load_anime_status() y sirve para avisar cuando no coincide con quien
        # está sirviendo la ficha; None mientras no se sepa o si no está guardado.
        self.__saved_provider_id: AnimeProviderId | None = None
        # Si este anime tiene fila en la tabla ANIMES de DB_Animes.db. No se deduce de __saved_provider_id,
        # que también es None en las filas anteriores a la columna.
        self.__is_saved: bool = False

        self.episode_switches: list = []
        self.watched_status = {episode.id: False for episode in self.anime_info.episodes}
        self.sort_descending: bool = True
        self.__anime_status_frame = None
        self.__list_episodes_frame = None
        self.__anime_is_favourite: bool = False
        self.__anime_is_finished: bool = False
        self.__anime_is_watching: bool = False
        self.__anime_is_pending: bool = False

    @staticmethod
    def __with_episodes(anime_info: AnimeInfo) -> AnimeInfo:
        """Normaliza ``episodes=None`` a lista vacía, **sobre una copia**.

        No se muta el original porque puede ser el objeto cacheado en
        ``main_window.recent_animes``, donde ese ``None`` es justo lo que marca que
        aún le falta la precarga.
        """
        if anime_info.episodes is None:
            return replace(anime_info, episodes=[])
        return anime_info

    def __persistence_anime_info(self) -> AnimeInfo:
        """Copia de la ficha actual con la **identidad de persistencia**.

        Es lo que hay que pasar a `animes_persistence` y a los helpers de póster,
        que leen ``.id`` y ``.poster`` del ``AnimeInfo`` que reciben. Sin esto, un
        cambio de proveedor duplicaría la fila en ANIMES.
        """
        return replace(
            self.anime_info,
            id=self.persistence_anime_id,
            poster=self.persistence_poster_url,
            provider_id=self.persistence_provider_id
        )

    def display_anime_info(self):
        self.main_window.clear_frame()
        self.__load_anime_status()
        self.__display_anime_info()

    def __load_anime_status(self):
        anime_record: AnimeRecord = self.main_window.animes_persistence.get_anime_by_anime_id(
            self.persistence_anime_id)
        if anime_record is None:
            return
        self.__is_saved = True
        self.__saved_provider_id = anime_record.provider_id
        if anime_record.provider_id is None and self.persistence_provider_id is not None:
            if self.main_window.animes_persistence.update_anime_provider_id(self.persistence_anime_id, self.persistence_provider_id):
                print(f"Anotado el proveedor {self.persistence_provider_id.value} "
                      f"para {self.persistence_anime_id}")
                self.__saved_provider_id = self.persistence_provider_id
        if len(anime_record.episodes) != len(self.anime_info.episodes):
            self.main_window.animes_persistence.update_anime_episodes(self.persistence_anime_id, self.anime_info.episodes)
        self.__anime_is_favourite = anime_record.is_favourite
        self.__anime_is_finished = anime_record.is_finished
        self.__anime_is_watching = anime_record.is_watching
        self.__anime_is_pending = anime_record.is_pending

        # Restaurar episodios vistos desde la BD
        watched_ids = self.main_window.animes_persistence.get_watched_episodes(self.persistence_anime_id)
        for episode in self.anime_info.episodes:
            self.watched_status[episode.id] = episode.id in watched_ids

    def __display_anime_info(self):
        self.main_window.clear_frame()
        time.sleep(0.1)
        # Configuración inicial del layout en content_frame
        # Fila 0: selector de proveedor. Ocupa su propia fila y abarca las columnas
        # 1-3 a propósito: si se metiera en las columnas 2-3 de la fila del título,
        # les reservaría ancho y la sinopsis —cuyo `wraplength` va calculado a mano
        # sobre el ancho del content_frame— se vería recortada por la derecha.
        self.main_window.content_frame.grid_rowconfigure(0, weight=0)
        self.main_window.content_frame.grid_rowconfigure(1, weight=1)
        self.main_window.content_frame.grid_rowconfigure(2, weight=1)
        self.main_window.content_frame.grid_rowconfigure(3, weight=1)
        self.main_window.content_frame.grid_columnconfigure(0, weight=1)
        self.main_window.content_frame.grid_columnconfigure(1, weight=4)  # Espacio más amplio para el título, sinopsis, y géneros
        self.main_window.content_frame.grid_columnconfigure(2, weight=1)  # Añadir espacio para los botones
        self.main_window.content_frame.grid_columnconfigure(3, weight=1)  # Añadir espacio para los botones

        # Cargar la imagen del póster.
        anime_image = get_anime_image(self.__persistence_anime_info())

        # Crear el frame para contener el póster y la información
        info_frame = ctk.CTkFrame(self.main_window.content_frame, fg_color="white")
        info_frame.grid(row=0, column=0, rowspan=4, sticky=ctk.NW, padx=10, pady=10)

        # Etiqueta para mostrar la imagen (póster)
        poster_label = ctk.CTkLabel(
            info_frame,
            text="",
            image=anime_image
        )
        #poster_label.image = anime_image  # Mantener referencia de la imagen
        poster_label.grid(row=0, column=0, rowspan=3, sticky=ctk.NW, padx=10, pady=10)

        # Etiqueta para el título del anime
        title_label = ctk.CTkLabel(
            self.main_window.content_frame,
            text=self.anime_info.title,
            font=ctk.CTkFont(size=28, weight="bold"),
            justify="left",
            anchor="w",
        )
        title_label.grid(row=1, column=1, sticky=ctk.NW, padx=5, pady=(5, 0))

        # Etiqueta para la sinopsis del anime
        synopsis_label = ctk.CTkLabel(
            self.main_window.content_frame,
            text=f"{self.anime_info.synopsis if self.anime_info.synopsis else ''}",
            font=ctk.CTkFont(size=18),
            width=self.main_window.content_frame.winfo_width() - 275,
            wraplength=self.main_window.content_frame.winfo_width() - 275,  # Mayor ancho para ocupar el espacio disponible
            justify="left",
            anchor="w"
        )
        synopsis_label.grid(row=2, column=1, sticky=ctk.NW, padx=(5, 10), pady=(10, 0))

        # Etiqueta para los géneros del anime
        genres_text = ', '.join(refactor_genre_text(genre) for genre in self.anime_info.genres)
        genres_label = ctk.CTkLabel(
            self.main_window.content_frame,
            text=f"Géneros: {genres_text}",
            font=ctk.CTkFont(size=14),
            width=self.main_window.content_frame.winfo_width() - 275,
            wraplength=self.main_window.content_frame.winfo_width() - 275,  # Mayor ancho para ocupar el espacio disponible
            justify="left",
            anchor="w"
        )
        genres_label.grid(row=3, column=1, sticky=ctk.EW, padx=(5, 10), pady=(20, 0))

        self.__show_provider_label()
        self.__show_anime_status()

    # ------------------------------------------------------------------
    # Proveedor de la ficha
    # ------------------------------------------------------------------
    def __show_provider_label(self):
        """Indica **quién sirvió realmente** esta ficha, no el predeterminado.

        Es lo único que hace visible el fallback silencioso de
        ``call_with_fallback``: puedes tener AnimeAV1 seleccionado y estar viendo
        datos de otro porque el primero falló.

        El proveedor se elige en la sidebar.
        """
        provider_frame = ctk.CTkFrame(self.main_window.content_frame, fg_color="transparent")
        provider_frame.grid(row=0, column=1, columnspan=3, sticky=ctk.E, padx=(5, 10), pady=(5, 0))

        provider_title = ctk.CTkLabel(
            provider_frame,
            text="Proveedor:",
            font=ctk.CTkFont(size=14),
            anchor="e"
        )
        provider_title.grid(row=0, column=0, sticky=ctk.E, padx=(0, 5))

        provider_name = self.anime_provider_mgr.get_provider_name(self.provider_id)
        provider_value = ctk.CTkLabel(
            provider_frame,
            text=provider_name,
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="e"
        )
        provider_value.grid(row=0, column=1, sticky=ctk.E)

        # Aviso de identidad partida: estos datos vienen de un sitio y la fila de la
        # biblioteca es de otro.
        if self.__is_saved:
            # De quién es la FILA, que es un dato distinto del de arriba y se
            # muestra siempre que el anime esté guardado.
            is_split = self.__has_split_identity()
            saved_name = (self.anime_provider_mgr.get_provider_name(self.__saved_provider_id)
                          if self.__saved_provider_id is not None
                          else "sin proveedor anotado")
            # La advertencia se reserva para la discrepancia de verdad: lo que estás
            # viendo no lo sirve el proveedor de tu fila, así que los botones de
            # estado y el póster escriben en algo distinto de lo que tienes
            # delante.
            library_label = ctk.CTkLabel(
                provider_frame,
                text=f"{'⚠ ' if is_split else ''}En tu biblioteca: {saved_name}",
                font=ctk.CTkFont(size=12),
                text_color=("#B45309", "#FBBF24") if is_split else ("gray45", "gray60"),
                anchor="e"
            )
            library_label.grid(row=1, column=0, columnspan=2, sticky=ctk.E, pady=(2, 0))

        target_provider_id = self.__repair_target_provider_id()
        if target_provider_id is None:
            return
        # Pasar la fila a otro proveedor. Se ofrece aquí, pegado a la etiqueta que
        # dice de dónde salen los datos, porque es la misma pregunta vista desde
        # los dos lados: "esto viene de X" / "guárdalo desde Y".
        migrate_button = ctk.CTkButton(
            provider_frame,
            text=f"Actualizar a {self.anime_provider_mgr.get_provider_name(target_provider_id)}",
            font=ctk.CTkFont(size=12),
            height=26,
            width=170,
            command=self.__repair_to_target_provider
        )
        migrate_button.grid(row=2, column=0, columnspan=2, sticky=ctk.E, pady=(4, 0))

    def __has_split_identity(self) -> bool:
        """Si la fila guardada y la ficha que se está viendo no son la misma cosa.

        Dos formas de que ocurra, y las dos se arreglan igual: el slug guardado es
        de otro sitio (el usuario se desvió y la ficha se localizó por título), o
        es el mismo slug pero lo está sirviendo un proveedor distinto del que
        consta en la fila (fallback).
        """
        if not self.__is_saved:
            return False
        if self.persistence_anime_id != str(self.anime_info.id):
            return True
        return (self.__saved_provider_id is not None and self.provider_id is not None
                and self.__saved_provider_id != self.provider_id)

    def __repair_target_provider_id(self) -> AnimeProviderId | None:
        """A qué proveedor se ofrece pasar esta fila, o ``None`` si no hay nada que hacer.

        Dos orígenes, en este orden:

        1. **Quien está sirviendo la ficha**, cuando no es el de la fila. Es lo que
           tienes delante, así que migrar no cuesta ni una petición.
        2. **El proveedor seleccionado en la sidebar**, cuando la ficha la sirve el
           de la fila pero tú estás usando otro. Este es el caso corriente —«tengo
           One Piece guardado desde AnimeFLV y quiero pasarlo a AnimeAV1»— y hay
           que localizar el anime allí antes de migrar, porque el slug es distinto
           en cada sitio.

        Atarlo solo al caso 1, como estaba, dejaba la acción fuera de alcance
        justo cuando más falta hace: al abrir un anime guardado sin desviar el
        desplegable lo sirve **el proveedor de su propia fila**, así que nunca
        había nada "partido" que reparar y el botón no llegaba a aparecer.
        """
        if not self.__is_saved:
            return None
        if self.__has_split_identity():
            return self.provider_id
        selected_provider_id = self.anime_provider_mgr.get_default_provider_id()
        if (selected_provider_id is not None and self.__saved_provider_id is not None and selected_provider_id != self.__saved_provider_id):
            return selected_provider_id
        return None

    def __repair_to_target_provider(self):
        """Punto de entrada del botón «Actualizar a …».

        Si el proveedor destino es el que ya está sirviendo la ficha, se migra con
        lo que hay en pantalla. Si es otro —el seleccionado en la sidebar—, primero
        hay que **localizar el anime allí**, porque su ``anime_id`` es un slug
        propio de cada sitio y el guardado no vale. Eso cuesta dos peticiones, así
        que va en un hilo aparte con el cursor de espera.
        """
        target_provider_id = self.__repair_target_provider_id()
        if target_provider_id is None:
            return

        if target_provider_id == self.provider_id:
            # Ya la tenemos delante: ni una petición.
            self.__confirm_and_migrate(self.anime_info, target_provider_id)
            return

        self.main_window.configure(cursor="watch")
        self.main_window.update_idletasks()

        def _resolved(resolved_anime_info: AnimeInfo | None):
            """Vuelta al hilo de Tkinter: aquí se abren los diálogos, no en el hilo."""
            if not self.main_window.winfo_exists():
                return
            self.main_window.configure(cursor="")
            provider_name = self.anime_provider_mgr.get_provider_name(target_provider_id)
            if resolved_anime_info is None:
                messagebox.showinfo(
                    f"{provider_name} no tiene este anime",
                    f"No se ha encontrado «{self.anime_info.title}» en {provider_name}, "
                    f"así que no se puede pasar tu biblioteca a ese proveedor.\n\n"
                    f"El anime sigue guardado como estaba."
                )
                return
            self.__confirm_and_migrate(resolved_anime_info, target_provider_id)

        def _resolve():
            reference = AnimeInfo(
                id=self.persistence_anime_id,
                title=self.anime_info.title,
                poster=self.persistence_poster_url
            )
            resolved_anime_info = self.anime_provider_mgr.resolve_anime_in_provider(reference, target_provider_id)
            self.main_window.after(0, _resolved, resolved_anime_info)

        threading.Thread(target=_resolve, daemon=True).start()

    def __confirm_and_migrate(self, anime_info: AnimeInfo, target_provider_id: AnimeProviderId):
        """Reescribe la fila guardada para que sea la de ``target_provider_id``.

        Es la única acción de la aplicación que reescribe la identidad de una fila
        de la biblioteca, así que se pide confirmación enumerando lo que cambia y
        lo que se conserva. Lo que se conserva es lo importante: los episodios
        vistos, que no se pueden recuperar de ningún sitio.

        :param anime_info: ficha **del proveedor destino**, de donde salen el
            identificador, el título y el póster nuevos.
        """
        animes_persistence = self.main_window.animes_persistence
        anime_record: AnimeRecord = animes_persistence.get_anime_by_anime_id(self.persistence_anime_id)
        if anime_record is None:
            # La fila puede haber desaparecido desde que se pintó la ficha.
            messagebox.showinfo(
                "Este anime ya no está guardado",
                "Este anime ya no consta en tu biblioteca, así que no hay nada que actualizar."
            )
            return

        new_anime_id = str(anime_info.id)
        provider_name = self.anime_provider_mgr.get_provider_name(target_provider_id)
        if (new_anime_id != self.persistence_anime_id
                and animes_persistence.get_anime_by_anime_id(new_anime_id) is not None):
            # Migrar dejaría dos filas del mismo anime, cada una con sus episodios
            # vistos. Se para aquí y no en la capa de persistencia para poder
            # explicarlo; migrate_anime_identity() lo comprueba igualmente.
            messagebox.showwarning(
                "No se puede actualizar",
                f"En tu biblioteca ya hay otra entrada de este anime en {provider_name}.\n\n"
                f"Elimina una de las dos antes de actualizar, o se quedarían duplicadas."
            )
            return

        changes = [f"  · proveedor: "
                   f"{self.anime_provider_mgr.get_provider_name(self.__saved_provider_id)} → {provider_name}"]
        if new_anime_id != self.persistence_anime_id:
            changes.append(f"  · identificador: {self.persistence_anime_id} → {new_anime_id}")
        if anime_info.title and anime_info.title != anime_record.title:
            changes.append(f"  · título: «{anime_record.title}» → «{anime_info.title}»")

        if not messagebox.askyesno(
            "Actualizar el anime guardado",
            f"«{anime_record.title}» pasará a guardarse desde {provider_name}:\n\n"
            + "\n".join(changes) +
            f"\n\nSe conservan los {len(anime_record.watched_episodes)} episodios vistos y "
            f"las categorías en las que está.\n\n¿Actualizarlo?"
        ):
            return

        old_anime_id = self.persistence_anime_id
        self.main_window.configure(cursor="watch")
        self.main_window.update_idletasks()

        def _done(migrated: bool):
            """Vuelta al hilo de Tkinter: aquí, y solo aquí, se toca la interfaz."""
            if not self.main_window.winfo_exists():
                return
            self.main_window.configure(cursor="")
            if not migrated:
                messagebox.showerror(
                    "No se pudo actualizar",
                    "No se ha podido actualizar el anime en tu biblioteca.\n\n"
                    "No se ha cambiado nada; revisa la consola para ver el detalle."
                )
                return
            # Ficha nueva en vez de retocar esta: así la identidad de persistencia
            # se vuelve a congelar a partir del anime ya migrado, en lugar de
            # mutar unos atributos que el resto de la clase da por inmutables. De
            # paso, la ficha pasa a mostrar los datos del proveedor nuevo.
            AnimeWindowViewer(self.main_window, anime_info, target_provider_id).display_anime_info()

        def _migrate():
            migrated = animes_persistence.migrate_anime_identity(
                old_anime_id, anime_info, target_provider_id)
            if migrated:
                self.__move_posters(anime_record, old_anime_id, new_anime_id, anime_info)
            self.main_window.after(0, _done, migrated)

        # En hilo aparte porque, si el póster no estaba cacheado, hay que bajarlo.
        threading.Thread(target=_migrate, daemon=True).start()

    def __move_posters(self, anime_record: AnimeRecord, old_anime_id: str, new_anime_id: str,
                       anime_info: AnimeInfo):
        """Lleva los pósters cacheados al nombre de fichero del ``anime_id`` nuevo.

        Solo en las categorías en las que está el anime, que son las únicas
        carpetas donde se guarda su imagen. Un fallo aquí no revierte la
        migración: el peor caso es un recuadro gris hasta la próxima descarga.
        """
        if old_anime_id == new_anime_id:
            return
        active_statuses = [
            (AnimeStatus.FAVOURITE, anime_record.is_favourite),
            (AnimeStatus.WATCHING,  anime_record.is_watching),
            (AnimeStatus.FINISHED,  anime_record.is_finished),
            (AnimeStatus.PENDING,   anime_record.is_pending),
        ]
        for status, is_active in active_statuses:
            if not is_active:
                continue
            try:
                if not move_anime_poster_by_status(status, old_anime_id, new_anime_id):
                    download_anime_poster_by_status(status, anime_info)
            except Exception as e:
                print(f"No se pudo actualizar el póster de {new_anime_id} "
                      f"en {status.name.lower()}: {e}")

    def __show_anime_status(self):
        self.__anime_status_frame = ctk.CTkFrame(self.main_window.content_frame)
        self.__anime_status_frame.grid(row=4, column=0, columnspan=4, sticky=ctk.NSEW, padx=10, pady=10)
        self.__anime_status_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.__display_anime_status()

    def __display_anime_status(self):
        for widget in self.__anime_status_frame.winfo_children():
            widget.destroy()
        favourite_button_img = utils.load_image(get_resource_path("resources/images/utils/favoritos.png"), image_size=(24, 24))
        non_favourite_button_img = utils.load_image(get_resource_path("resources/images/utils/no_favoritos.png"), image_size=(24, 24))
        favorite_botton = ctk.CTkButton(
            self.__anime_status_frame,
            text=f"Añadir a favoritos" if not self.__anime_is_favourite else f"Eliminar de favoritos",
            font=ctk.CTkFont(size=14),
            anchor="center",
            border_spacing=10,
            image=non_favourite_button_img if not self.__anime_is_favourite else favourite_button_img,
            command=self.add_to_favorites if not self.__anime_is_favourite else self.remove_from_favorites,
        )
        favorite_botton.grid(row=0, column=0, sticky=ctk.EW, padx=(5, 10), pady=(0, 5))

        finished_button_img = utils.load_image(get_resource_path("resources/images/utils/finalizados.png"), image_size=(24, 24))
        finished_button = ctk.CTkButton(
            self.__anime_status_frame,
            text=f"Añadir a finalizados" if not self.__anime_is_finished else f"Eliminar de finalizados",
            font=ctk.CTkFont(size=14),
            anchor="center",
            border_spacing=10,
            image=finished_button_img,
            command=self.add_to_finished if not self.__anime_is_finished else self.remove_from_finished,
        )
        finished_button.grid(row=0, column=1, sticky=ctk.EW, padx=(5, 10), pady=(0, 5))

        watching_button_img = utils.load_image(get_resource_path("resources/images/utils/viendo.png"), image_size=(24, 24))
        watching_button = ctk.CTkButton(
            self.__anime_status_frame,
            text=f"Añadir a viendo" if not self.__anime_is_watching else f"Eliminar de viendo",
            font=ctk.CTkFont(size=14),
            anchor="center",
            border_spacing=10,
            image=watching_button_img,
            command=self.add_to_watching if not self.__anime_is_watching else self.remove_from_watching,
        )
        watching_button.grid(row=0, column=2, sticky=ctk.EW, padx=(5, 10), pady=(0, 5))

        watching_button_img = utils.load_image(get_resource_path("resources/images/utils/pendientes.png"), image_size=(24, 24))
        pending_button = ctk.CTkButton(
            self.__anime_status_frame,
            text=f"Añadir a pendiente" if not self.__anime_is_pending else f"Eliminar de pendiente",
            font=ctk.CTkFont(size=14),
            anchor="center",
            border_spacing=10,
            image=watching_button_img,
            command=self.add_to_pending if not self.__anime_is_pending else self.remove_from_pending,
        )
        pending_button.grid(row=0, column=3, sticky=ctk.EW, padx=(5, 10), pady=(0, 5))

        self.__show_anime_episodes()

    # ------------------------------------------------------------------
    # Botones de estado
    #
    # Todos usan __persistence_anime_info() y persistence_anime_id, nunca
    # self.anime_info directamente: si no, cambiar de proveedor y pulsar uno de
    # estos botones crearía una fila nueva en ANIMES para el mismo anime.
    # ------------------------------------------------------------------
    def __confirm_save(self, status: AnimeStatus) -> bool:
        """Avisa antes de crear una fila nueva de un anime que ya está guardado.

        La comprobación por ``anime_id`` no basta: el mismo anime tiene un slug
        distinto en cada sitio, así que abrirlo desde otro proveedor y pulsar un
        estado inserta una **segunda fila** del mismo anime, con sus propios
        episodios vistos y su propia entrada en las listas. Hasta ahora eso pasaba
        en silencio.

        Se consulta la BD en vez de mirar ``__is_saved``, que se calculó al pintar
        la ficha: si el usuario ya ha pulsado otro estado en esta misma pantalla,
        la fila existe desde entonces y no hay nada que avisar.

        :param status: sección a la que se está añadiendo, para nombrarla en el
            aviso en vez de hablar de «tu biblioteca» en abstracto.
        :return: ``True`` si se puede guardar (no hay duplicado, o el usuario lo
            ha aceptado a sabiendas).
        """
        animes_persistence = self.main_window.animes_persistence
        if animes_persistence.get_anime_by_anime_id(self.persistence_anime_id) is not None:
            return True

        duplicate = find_saved_duplicate(animes_persistence.get_all_animes(), self.anime_info.title,
                                         exclude_anime_id=self.persistence_anime_id)
        if duplicate is None:
            return True

        duplicate_provider = self.anime_provider_mgr.get_provider_name(duplicate.provider_id)
        provider_name = self.anime_provider_mgr.get_provider_name(self.provider_id)
        section_name = STATUS_SECTION_NAMES.get(status, "tu biblioteca")
        # Dónde está el duplicado se saca de sus propios flags y no de la sección
        # que se acaba de pulsar: puede estar en otra, o en ninguna si se quitó de
        # todas. Decir "ya está en Favoritos" cuando está en Pendientes sería
        # mentir justo en el dato por el que el usuario decide.
        duplicate_sections = [name for duplicate_status, name in STATUS_SECTION_NAMES.items()
                              if getattr(duplicate, duplicate_status.value)]
        location = f", en {' y '.join(duplicate_sections)}," if duplicate_sections else ""
        print(f"{self.anime_info.title!r} se parece a {duplicate.title!r} "
              f"({duplicate.anime_id}), ya guardado desde {duplicate_provider}")
        return messagebox.askyesno(
            "Puede que ya lo tengas guardado",
            f"Vas a añadir «{self.anime_info.title}» a tu Biblioteca de {section_name}.\n\n"
            f"«{duplicate.title}» ya está en tu biblioteca{location} guardado desde "
            f"{duplicate_provider}.\n\n"
            f"Si lo añades ahora tendrás el mismo anime dos veces, cada copia con sus "
            f"propios episodios vistos.\n\n"
            f"Para tenerlo en {provider_name} sin duplicarlo, ábrelo desde tu biblioteca "
            f"y usa «Actualizar a {provider_name}».\n\n"
            f"¿Añadirlo de todas formas?"
        )

    def add_to_favorites(self):
        if not self.__confirm_save(AnimeStatus.FAVOURITE):
            return
        anime_info = self.__persistence_anime_info()
        self.main_window.animes_persistence.update_anime_to_favourite(anime_info)
        download_anime_poster_by_status(AnimeStatus.FAVOURITE, anime_info)
        print(f"{self.anime_info.title} añadido a favoritos.")
        self.__anime_is_favourite = True
        self.__display_anime_status()

    def remove_from_favorites(self):
        self.main_window.animes_persistence.update_anime_to_not_favourite(self.persistence_anime_id)
        remove_anime_poster_by_status(AnimeStatus.FAVOURITE, self.__persistence_anime_info())
        print(f"{self.anime_info.title} eliminado de favoritos.")
        self.__anime_is_favourite = False
        self.__display_anime_status()

    def add_to_finished(self):
        if not self.__confirm_save(AnimeStatus.FINISHED):
            return
        anime_info = self.__persistence_anime_info()
        self.main_window.animes_persistence.update_anime_to_finished(anime_info)
        download_anime_poster_by_status(AnimeStatus.FINISHED, anime_info)
        print(f"{self.anime_info.title} añadido a finalizados.")
        self.__anime_is_finished = True
        self.__anime_is_watching = False
        self.__anime_is_pending = False
        self.__display_anime_status()

    def remove_from_finished(self):
        self.main_window.animes_persistence.update_anime_to_not_finished(self.persistence_anime_id)
        remove_anime_poster_by_status(AnimeStatus.FINISHED, self.__persistence_anime_info())
        print(f"{self.anime_info.title} eliminado de finalizados.")
        self.__anime_is_finished = False
        self.__anime_is_pending = True
        self.__display_anime_status()

    def add_to_watching(self):
        if not self.__confirm_save(AnimeStatus.WATCHING):
            return
        anime_info = self.__persistence_anime_info()
        self.main_window.animes_persistence.update_anime_to_watching(anime_info)
        download_anime_poster_by_status(AnimeStatus.WATCHING, anime_info)
        print(f"{self.anime_info.title} añadido a viendo.")
        self.__anime_is_finished = False
        self.__anime_is_watching = True
        self.__anime_is_pending = False
        self.__display_anime_status()

    def remove_from_watching(self):
        self.main_window.animes_persistence.update_anime_to_not_watching(self.persistence_anime_id)
        remove_anime_poster_by_status(AnimeStatus.WATCHING, self.__persistence_anime_info())
        print(f"{self.anime_info.title} eliminado de viendo.")
        self.__anime_is_watching = False
        self.__display_anime_status()

    def add_to_pending(self):
        if not self.__confirm_save(AnimeStatus.PENDING):
            return
        anime_info = self.__persistence_anime_info()
        self.main_window.animes_persistence.update_anime_to_pending(anime_info)
        download_anime_poster_by_status(AnimeStatus.PENDING, anime_info)
        print(f"{self.anime_info.title} añadido a pendientes.")
        self.__anime_is_finished = False
        self.__anime_is_watching = False
        self.__anime_is_pending = True
        self.__display_anime_status()

    def remove_from_pending(self):
        self.main_window.animes_persistence.update_anime_to_not_pending(self.persistence_anime_id)
        remove_anime_poster_by_status(AnimeStatus.PENDING, self.__persistence_anime_info())
        print(f"{self.anime_info.title} eliminado de pendientes.")
        self.__anime_is_pending = False
        self.__display_anime_status()

    def __show_anime_episodes(self):
        self.__list_episodes_frame = ctk.CTkFrame(self.main_window.content_frame)
        self.__list_episodes_frame.grid(row=5, column=0, columnspan=4, sticky=ctk.NSEW, pady=(10, 5), padx=10)
        self.__list_episodes_frame.grid_columnconfigure(0, weight=1)
        self.__list_episodes_frame.grid_columnconfigure(1, weight=1)
        self.__list_episodes_frame.grid_columnconfigure(2, weight=3)
        self.__list_episodes_frame.grid_columnconfigure(3, weight=1)

        self.__display_episodes()

    def __display_episodes(self, episodes_to_show: List[EpisodeInfo] | None = None):
        episodes_to_show = self.anime_info.episodes[:25] if episodes_to_show is None else episodes_to_show
        for widget in self.__list_episodes_frame.winfo_children():
            widget.destroy()

        self.episode_switches.clear()

        bd_watched = self.main_window.animes_persistence.get_watched_episodes(self.persistence_anime_id)
        for episode_info in episodes_to_show:
            self.watched_status[episode_info.id] = episode_info.id in bd_watched

        # Episodios debajo de la sinopsis, alineados a la izquierda
        episodes_label = ctk.CTkLabel(
            self.__list_episodes_frame,
            text="Lista de episodios",
            font=ctk.CTkFont(size=18, weight="bold"),
        )
        episodes_label.grid(row=0, column=0, columnspan=2, sticky=ctk.W, pady=(10, 5))

        # Botón de ordenación
        sort_button = ctk.CTkButton(
            self.__list_episodes_frame,
            text="Mayor a menor  ↓",
            font=ctk.CTkFont(size=14),
            command=lambda: self.__toggle_sort_order(sort_button)
        )
        sort_button.grid(row=0, column=3, sticky=ctk.E, padx=(5, 10), pady=(10, 5))

        # Campo de búsqueda de episodios
        self.search_entry = ctk.CTkEntry(
            self.__list_episodes_frame,
            placeholder_text="Buscar episodio...",
            font=ctk.CTkFont(size=14),
            width=150
        )
        self.search_entry.grid(row=0, column=4, sticky=ctk.E, padx=(5, 10), pady=(10, 5))
        self.search_entry.bind("<Return>", self.__search_episodes)

        servers_frames = {}

        # Solo se muestran los 24 primeros episodios
        for index, episode_info in enumerate(episodes_to_show):
            episode_button = utilsButtons.EpisodeButton(
                parent_frame=self.__list_episodes_frame,
                anime_title=self.anime_info.title,
                episode_info=episode_info,
                servers_frame=servers_frames,
                index=index,
                toggle_servers_command=self.__toggle_servers_frame
            )
            episode_button.grid(row=index + 1, column=0, sticky=ctk.W, pady=(10, 5))

            watched_episode_switch = ctk.CTkSwitch(
                self.__list_episodes_frame,
                text="Visto",
                width=80,
                command=lambda ep_id=episode_info.id: self.__toggle_episode_switch(ep_id)
            )
            watched_episode_switch.grid(row=index + 1, column=1, sticky=ctk.W, padx=(5, 10), pady=(10, 5))
            # Restaurar el estado del switch
            if self.watched_status.get(episode_info.id, False):
                watched_episode_switch.select()
            else:
                watched_episode_switch.deselect()

            # Agregar el switch a la lista de switches
            self.episode_switches.append(watched_episode_switch)

    def __display_previous_and_next_episodes(self, episode_info: EpisodeInfo):
        previous_episode_button = ctk.CTkButton(
            self.__list_episodes_frame,
            text="← Episodio anterior",
            font=ctk.CTkFont(size=14),
            anchor=ctk.W,
            border_spacing=10,
            command=lambda: self.__previous_episode(episode_info)
        )
        previous_episode_button.grid(row=2, column=1, sticky=ctk.W, pady=(30, 5))

        next_episode_button = ctk.CTkButton(
            self.__list_episodes_frame,
            text="Episodio siguiente →",
            font=ctk.CTkFont(size=14),
            anchor=ctk.E,
            border_spacing=10,
            command=lambda: self.__next_episode(episode_info)
        )
        next_episode_button.grid(row=2, column=2, sticky=ctk.E, padx=(5, 10), pady=(30, 5))

    def __toggle_sort_order(self, sort_button):
        # Cambiar el estado de orden y actualizar la lista de episodios
        self.sort_descending = not self.sort_descending
        self.anime_info.episodes.sort(
            key=lambda episode: episode.id,
            reverse=self.sort_descending
        )
        # Cambiar el texto del botón según el estado
        text = "Mayor a menor  ↓" if self.sort_descending else "Menor a mayor  ↑"
        sort_button.configure(text=text)
        self.__display_episodes()

    def __search_episodes(self, event=None):
        # Obtener el valor de búsqueda y filtrar episodios por ID
        query = self.search_entry.get().strip()
        if query.isdigit():
            query_id = int(query)
            # Filtrar la lista según el ID del episodio
            filtered_episode = [next((ep for ep in self.anime_info.episodes if ep.id == query_id), None)]
            if filtered_episode[0] is None:
                self.__display_episodes([])
            else:
                self.__display_episodes(filtered_episode)
                self.__display_previous_and_next_episodes(filtered_episode[0])
        else:
            # Mostrar todos los episodios si no se ingresa un número válido
            self.__display_episodes(self.anime_info.episodes[:25])

    def __previous_episode(self, episode_info: EpisodeInfo):
        current_index = next(i for i, ep in enumerate(self.anime_info.episodes) if ep.id == episode_info.id)
        previous_index = current_index + 1 if self.sort_descending else current_index - 1

        # Verificar que el siguiente episodio está en el rango
        if 0 <= previous_index < len(self.anime_info.episodes):
            previous_episode = self.anime_info.episodes[previous_index]
            self.__display_episodes([previous_episode])
            self.__display_previous_and_next_episodes(previous_episode)

    def __next_episode(self, episode_info: EpisodeInfo):
        current_index = next(i for i, ep in enumerate(self.anime_info.episodes) if ep.id == episode_info.id)
        next_index = current_index - 1 if self.sort_descending else current_index + 1

        # Verificar que el siguiente episodio está en el rango
        if 0 <= next_index < len(self.anime_info.episodes):
            next_episode = self.anime_info.episodes[next_index]
            self.__display_episodes([next_episode])
            self.__display_previous_and_next_episodes(next_episode)

    def __toggle_episode_switch(self, episode_id: int):
        # Encontrar el índice del episodio en la lista COMPLETA del anime
        try:
            index = next(i for i, ep in enumerate(self.anime_info.episodes) if ep.id == episode_id)
        except StopIteration:
            print(f"Error: Episodio con ID {episode_id} no encontrado.")
            return

        current_state = self.watched_status[episode_id]
        marking_as_watched = not current_state

        # --- 1. Actualizar switches VISIBLES en pantalla ---
        # Solo se tocan los widgets renderizados actualmente (los 24 del frame).
        if self.sort_descending:
            if marking_as_watched:
                for i in range(index, len(self.episode_switches)):
                    ep_id = self.anime_info.episodes[i].id
                    self.watched_status[ep_id] = True
                    self.episode_switches[i].select()
            else:
                # Unitario: solo este episodio
                self.watched_status[episode_id] = False
                self.episode_switches[index].deselect()
        else:
            if marking_as_watched:
                for i in range(0, index + 1):
                    ep_id = self.anime_info.episodes[i].id
                    self.watched_status[ep_id] = True
                    self.episode_switches[i].select()
            else:
                # Unitario: solo este episodio
                self.watched_status[episode_id] = False
                self.episode_switches[index].deselect()

        # --- 2. Calcular el conjunto COMPLETO a persistir ---
        bd_watched = self.main_window.animes_persistence.get_watched_episodes(self.persistence_anime_id)

        if marking_as_watched:
            # Al marcar como visto: todos los episodios desde el inicio hasta
            # episode_id (en orden real ascendente) se consideran vistos,
            # salvo los que el usuario haya desmarcado explícitamente en BD.
            # Los episodios posteriores no se tocan.
            all_episodes_sorted = sorted(self.anime_info.episodes, key=lambda ep: ep.id)
            ep_index_asc = next(i for i, ep in enumerate(all_episodes_sorted) if ep.id == episode_id)
            # IDs de todos los episodios hasta el marcado (inclusive) en orden real
            episodes_up_to = {ep.id for ep in all_episodes_sorted[:ep_index_asc + 1]}
            # IDs de episodios posteriores ya vistos en BD (no los tocamos)
            episodes_after = {ep_id for ep_id in bd_watched if ep_id > episode_id}
            merged = episodes_up_to | episodes_after
        else:
            # Al desmarcar: eliminar solo este episodio, el resto se preserva intacto
            merged = bd_watched - {episode_id}

        self.main_window.animes_persistence.update_watched_episodes(self.persistence_anime_id, merged)

    def __toggle_servers_frame(self, episode_info: EpisodeInfo, servers_frames, current_row: int):
        if episode_info.id in servers_frames:
            servers_frames[episode_info.id].destroy()
            del servers_frames[episode_info.id]
        else:
            # strict=True y provider_id explícito: `episode_info.anime` es el slug del
            # proveedor que sirvió esta ficha, así que pedir los servidores a otro
            # sitio con ese slug no devolvería nada útil. Sin esto, el selector de
            # proveedor mentiría: diría "AnimeFLV" y abriría servidores de AnimeAV1.
            servers_info: List[ServerInfo] = self.anime_provider_mgr.get_anime_episode_servers(
                episode_info.anime,
                episode_info.id,
                provider_id=self.provider_id,
                strict=True
            )
            if not servers_info:
                provider_name = self.anime_provider_mgr.get_provider_name(self.provider_id)
                print(f"[{provider_name}] Sin servidores para el episodio "
                      f"{episode_info.id} de {episode_info.anime}")
                messagebox.showinfo(
                    "Sin servidores disponibles",
                    f"{provider_name} no ofrece servidores para el episodio "
                    f"{episode_info.id}.\n\nPrueba a cambiar de proveedor en el "
                    f"desplegable de la barra lateral y vuelve a abrir el anime."
                )
                return
            # Crear un nuevo frame solo para los servidores
            new_server_frame = ctk.CTkFrame(
                self.__list_episodes_frame,
                fg_color="transparent"
            )
            new_server_frame.grid(row=current_row + 1, column=2, columnspan=3, sticky=ctk.NSEW, padx=(5, 10), pady=(10, 5))
            # Guardar el frame de servidores en el diccionario para poder ocultarlo después
            servers_frames[episode_info.id] = new_server_frame

            server_url_map = {server.server: server.url for server in servers_info}
            server_button = ctk.CTkSegmentedButton(
                new_server_frame,
                values=list(server_url_map.keys()),
            )
            server_button.grid(row=0, column=0, sticky=ctk.EW, pady=(15, 5))
            server_button.set(None)
            server_button.configure(command=lambda selected: self.__play_video(server_url_map[selected]))

            new_server_frame.grid_columnconfigure(0, weight=1)

    def __play_video(self, url):
        webbrowser.open(url)
