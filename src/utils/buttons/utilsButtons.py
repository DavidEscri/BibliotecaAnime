__author__ = "Jose David Escribano Orts"
__subsystem__ = "utils.buttons"
__module__ = "utilsButtons.py"
__version__ = "0.3"
__info__ = {"subsystem": __subsystem__, "module_name": __module__, "version": __version__}

"""Lo que las vistas comparten y no es un componente de gui/components/.

Quedan tres piezas, ninguna un botón pese al nombre del módulo:
filter_animes_by_title() y match_animes_from_search(), el cruce por título con
el que las vistas de estado buscan en local; SavedAnimeSearch, que lo orquesta
y suma encima lo que encuentre el proveedor; y SidebarButton, que solo
describe un destino de la barra lateral (etiqueta, iconos y comando).
"""

import difflib
import threading
from typing import List, Callable, Optional

from APIs.common.animeProviderMgr import AnimeProviderManager
from APIs.common.models import AnimeInfo
from dataPersistence.animesPersistence import AnimeRecord
from utils.utils import load_dual_image
import customtkinter as ctk

#: Parecido mínimo para dar por buena una coincidencia que no es subcadena
#: (tolera erratas tipo "dandandan" → "Dandadan"); alto a propósito para no
#: devolver animes que no vienen a cuento.
TITLE_SEARCH_THRESHOLD = 0.8


def filter_animes_by_title(anime_records: List[AnimeRecord], query: str) -> List[AnimeRecord]:
    """Filtra animes ya guardados por su título, sin red y sin mirar el proveedor.

    Compara sobre el título normalizado; coincide si la consulta aparece
    dentro del título (así "One Piece" también encuentra "One Piece Film:
    Red") o si el parecido supera el umbral, para tolerar erratas.

    :param anime_records: Filas ya filtradas por estado (favoritos, viendo...).
    :param query: Texto tal cual lo escribió el usuario; vacío devuelve todo.
    :return: Filas que coinciden, en el mismo orden en que llegaron.
    """
    normalized_query = AnimeProviderManager.normalize_title(query)
    if not normalized_query:
        return list(anime_records)

    matches: List[AnimeRecord] = []
    for anime_record in anime_records:
        normalized_title = AnimeProviderManager.normalize_title(anime_record.title)
        if normalized_query in normalized_title:
            matches.append(anime_record)
            continue
        if difflib.SequenceMatcher(None, normalized_query, normalized_title).ratio() >= TITLE_SEARCH_THRESHOLD:
            matches.append(anime_record)
    return matches


def match_animes_from_search(anime_records: List[AnimeRecord],
                             search_results: List[AnimeInfo]) -> List[AnimeRecord]:
    """Traduce resultados de una búsqueda web a los animes guardados que corresponden.

    Empareja primero por slug y, si no, por título normalizado (mismo criterio
    y umbral que resolve_anime_in_provider), porque el slug solo coincide si
    la fila la guardó el mismo proveedor que acaba de responder.

    :param anime_records: Filas guardadas de la pestaña, ya filtradas por estado.
    :param search_results: Resultados devueltos por el proveedor.
    :return: Filas guardadas que corresponden, sin repetidos, en el orden del proveedor.
    """
    if not search_results:
        return []

    records_by_slug = {str(record.anime_id): record for record in anime_records}
    matches: List[AnimeRecord] = []
    already_matched = set()
    for result in search_results:
        record: Optional[AnimeRecord] = records_by_slug.get(str(result.id))
        if record is None:
            normalized_result = AnimeProviderManager.normalize_title(result.title)
            for candidate in anime_records:
                normalized_candidate = AnimeProviderManager.normalize_title(candidate.title)
                if (normalized_candidate == normalized_result
                        or difflib.SequenceMatcher(None, normalized_result, normalized_candidate).ratio() >= AnimeProviderManager.TITLE_MATCH_THRESHOLD):
                    record = candidate
                    break
        if record is not None and record.anime_id not in already_matched:
            already_matched.add(record.anime_id)
            matches.append(record)
    return matches


class SavedAnimeSearch:
    """Buscador de una pestaña de la biblioteca: local al instante, web al llegar.

    La búsqueda local compara títulos ya guardados: es instantánea, funciona
    sin conexión y no depende del proveedor seleccionado. La web pregunta al
    proveedor seleccionado (sin fallback) y encuentra lo que un título
    guardado no puede saber, como que "Solo Leveling" es "Ore dake Level Up
    na Ken". Lo local se pinta antes de salir a la red; lo de la web se suma
    después sin quitar nunca resultados.
    """

    def __init__(self, main_window, anime_provider_mgr: AnimeProviderManager,
                 get_saved_animes: Callable[[], List[AnimeRecord]],
                 display_animes: Callable[[List[AnimeRecord]], None],
                 is_still_visible: Callable[[], bool]):
        """
        :param main_window: Hub, solo para devolver el resultado con after().
        :param get_saved_animes: Devuelve las filas de esta pestaña, ya por estado.
        :param display_animes: Repinta la rejilla con la lista que se le pase.
        :param is_still_visible: Si la pestaña sigue en pantalla; evita que una
            búsqueda lenta repinte encima de la vista a la que ya se cambió.
        """
        self.__main_window = main_window
        self.__anime_provider_mgr = anime_provider_mgr
        self.__get_saved_animes = get_saved_animes
        self.__display_animes = display_animes
        self.__is_still_visible = is_still_visible
        self.__generation = 0

    def search(self, search_text: str) -> None:
        """Muestra al instante las coincidencias locales y suma en segundo plano las de la web.

        :param search_text: Texto de búsqueda escrito por el usuario.
        """
        saved_animes = self.__get_saved_animes()
        local_matches = filter_animes_by_title(saved_animes, search_text)
        self.__display_animes(local_matches)

        self.__generation += 1
        generation = self.__generation
        if not AnimeProviderManager.normalize_title(search_text):
            return                      # sin texto ya se muestra todo: nada que buscar

        def _merge(extra_animes: List[AnimeRecord]):
            """Ya en el hilo de Tkinter."""
            if generation != self.__generation or not self.__is_still_visible():
                return
            known = {record.anime_id for record in local_matches}
            merged = local_matches + [record for record in extra_animes if record.anime_id not in known]
            if len(merged) == len(local_matches):
                return                  # la web no ha aportado nada nuevo
            print(f"La búsqueda en el proveedor añade {len(merged) - len(local_matches)} "
                  f"anime(s) que el título guardado no encontraba")
            self.__display_animes(merged)

        def _search_online():
            search_results, _ = self.__anime_provider_mgr.search_animes_by_query(search_text, strict=True)
            self.__main_window.after(0, _merge, match_animes_from_search(saved_animes, search_results))

        threading.Thread(target=_search_online, daemon=True).start()


class SidebarButton:
    """Descriptor de un destino de la barra lateral. No es un widget.

    Solo guarda qué hay que pintar (etiqueta, iconos, comando); quien lo
    pinta es gui.components.sidebar.Sidebar. La firma del constructor
    conserva parent_frame, row y column por compatibilidad, aunque ya no se
    usan, para que las vistas sigan heredando de ella sin cambios.
    """

    def __init__(self, parent_frame, text, row, column, command, icon_path_light, icon_path_dark):
        #: Etiqueta que la barra lateral muestra para este destino.
        self.sidebar_text: str = text
        #: Qué se ejecuta al pulsarlo.
        self.sidebar_command: Callable = command
        self.icon_path_light: str = icon_path_light
        self.icon_path_dark: str = icon_path_dark
        # Conservados solo por compatibilidad con la firma anterior.
        self.parent_frame = parent_frame
        self.row = row
        self.column = column

    def sidebar_icon(self, image_size: tuple) -> ctk.CTkImage:
        """Construye el icono del destino al tamaño pedido.

        No se cachea a propósito: la barra pide dos tamaños distintos
        (desplegada y plegada) y un mismo CTkImage solo admite un tamaño.

        :param image_size: Tamaño (ancho, alto) del icono a construir.
        :return: Icono con variante clara y oscura.
        """
        return load_dual_image(self.icon_path_light, self.icon_path_dark, image_size)

    def show_frame(self):
        """Pinta esta vista en el frame de contenido; cada subclase debe implementarlo."""
        raise NotImplementedError("Subclasses must implement this method")
