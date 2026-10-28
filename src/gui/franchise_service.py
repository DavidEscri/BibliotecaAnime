__author__ = "Jose David Escribano Orts"
__subsystem__ = "gui"
__module__ = "franchise_service.py"
__version__ = "0.2"
__info__ = {"subsystem": __subsystem__, "module_name": __module__, "version": __version__}

"""Recorrido en segundo plano de la franquicia de un anime.

Los sitios solo anuncian los relacionados de un salto: la 1.ª temporada ve la
2.ª, no la 3.ª. Este servicio recorre la línea principal de precuela en
precuela y de secuela en secuela, y completa el formato de los relacionados
que no lo traen, pidiendo lo mínimo:

- cada página se pide una sola vez por sesión, venga de la franquicia que venga;
- el recorrido sigue slugs de un sitio, así que nunca hay fallback
  (``strict=True``): el siguiente salto en otro sitio podría ser otro anime;
- las peticiones a un mismo proveedor van de una en una y espaciadas;
- si una petición falla, el recorrido se corta ahí y devuelve lo que tenga.

Nadie espera por él: las respuestas llegan por callback en el hilo de Tk.
"""
import dataclasses
import threading
import time

from dataclasses import dataclass
from typing import Callable, Dict, Iterable, List, Optional, Set, Tuple

from APIs.common.animeProviderMgr import AnimeProviderManager
from APIs.common.models import AnimeFormat, AnimeInfo, AnimeProviderId, AnimeRelationType, RelatedAnime

PageKey = Tuple[AnimeProviderId, str]

# Palabras del título normalizado que delatan el formato, por orden de prioridad:
# «… Season 2 Movie» es una película, no una serie.
_TITLE_FORMAT_WORDS: List[Tuple[AnimeFormat, Set[str]]] = [
    (AnimeFormat.MOVIE, {"movie", "movies", "film", "gekijouban", "gekijoban", "pelicula", "peliculas"}),
    (AnimeFormat.OVA, {"ova", "ovas", "oad", "oads"}),
    (AnimeFormat.ONA, {"ona", "onas"}),
    (AnimeFormat.SPECIAL, {"special", "specials", "especial", "especiales", "recap", "tokubetsu"}),
    (AnimeFormat.SERIES, {"season", "temporada"}),
]


def deduce_format_from_title(title: str) -> Optional[AnimeFormat]:
    """Adivina el formato de un anime por las palabras de su título.

    Es una pista, no un dato: «Special A» es una serie.

    :param title: Título tal como lo da el proveedor.
    :return: Formato deducido, o None si el título no delata ninguno.
    """
    words = set(AnimeProviderManager.normalize_title(title).split())
    for anime_format, format_words in _TITLE_FORMAT_WORDS:
        if words & format_words:
            return anime_format
    return None


def closest_related(related: List[RelatedAnime], relation: AnimeRelationType,
                    exclude: Iterable[str] = ()) -> Optional[RelatedAnime]:
    """El relacionado de ese tipo más cercano en fecha: la temporada anterior o la siguiente.

    Para una secuela, la más temprana; para una precuela, la más tardía. Sin
    años, la primera que anuncie el sitio.

    :param related: Relacionados de un anime.
    :param relation: PREQUEL o SEQUEL.
    :param exclude: Ids que no cuentan (los que ya están en la línea).
    :return: El relacionado, o None si no hay ninguno de ese tipo.
    """
    excluded = set(exclude)
    candidates = [item for item in related if item.relation == relation and str(item.id) not in excluded]
    if len(candidates) <= 1:
        return candidates[0] if candidates else None
    dated = [item for item in candidates if item.year is not None]
    if not dated:
        return candidates[0]
    pick = min if relation == AnimeRelationType.SEQUEL else max
    return pick(dated, key=lambda item: item.year)


@dataclass(frozen=True)
class FranchiseEntry:
    """Una temporada de la línea principal, con lo que se sabe de ella.

    year sale de la relación que apuntaba a ella (solo AnimeAV1 lo da); format
    y poster, de su propia página si se llegó a descargar.
    """
    id: str
    title: str
    format: Optional[AnimeFormat] = None
    year: Optional[int] = None
    poster: Optional[str] = None


@dataclass(frozen=True)
class FranchiseLine:
    """Línea principal de una franquicia, de la primera temporada a la última.

    :ivar entries: Temporadas en orden, con el anime pedido incluido.
    :ivar current_index: Posición del anime pedido en entries.
    :ivar truncated: Se paró por el tope de temporadas; hay más.
    :ivar interrupted: Una petición falló y el recorrido se cortó en ese punto.
    """
    entries: List[FranchiseEntry]
    current_index: int
    truncated: bool = False
    interrupted: bool = False


@dataclass(frozen=True)
class FormatHint:
    """Formato de un relacionado y de dónde sale.

    :ivar format: Formato, o None si no se ha podido saber.
    :ivar deduced: Sale del título, no de un proveedor: es una suposición.
    :ivar short_name: Siglas del proveedor que lo dio, si no es el que sirve la ficha.
    """
    format: Optional[AnimeFormat]
    deduced: bool = False
    short_name: Optional[str] = None


class FranchiseService:
    """Línea principal y formatos de los relacionados, con caché de páginas de sesión.

    Cada petición pública arranca su propio hilo daemon; las de un mismo
    proveedor se turnan con un lock por proveedor, que además evita pedir dos
    veces la misma página. El resto del estado compartido va bajo ``__lock``.
    """

    #: Temporadas, como mucho, en una línea principal; el anime pedido cuenta.
    MAX_LINE_LENGTH: int = 25
    #: Separación mínima, en segundos, entre dos peticiones al mismo proveedor.
    REQUEST_SPACING_S: float = 0.5
    #: Segundos durante los que una página que falló no se vuelve a pedir.
    RETRY_FAILED_AFTER_S: float = 2 * 60

    def __init__(self, main_window, anime_provider_mgr: AnimeProviderManager):
        """Crea el servicio, sin lanzar nada todavía.

        :param main_window: Ventana principal; se usa para volver al hilo de Tk.
        :param anime_provider_mgr: Gestor de proveedores.
        """
        self.__main_window = main_window
        self.__anime_provider_mgr = anime_provider_mgr

        self.__lock = threading.Lock()
        self.__pages: Dict[PageKey, AnimeInfo] = {}
        self.__failed_at: Dict[PageKey, float] = {}
        self.__provider_locks: Dict[AnimeProviderId, threading.Lock] = {}
        self.__last_request_at: Dict[AnimeProviderId, float] = {}

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------
    def request_franchise(self, anime_info: AnimeInfo, provider_id: AnimeProviderId,
                          callback: Callable[[FranchiseLine], None]) -> None:
        """Recorre la línea principal del anime en un hilo y vuelve en el acto.

        Hacia atrás por Precuela y hacia delante por Secuela; con varias, la de
        fecha más cercana. Lo ya recorrido no se vuelve a pedir en la sesión.

        :param anime_info: Ficha del anime que se está viendo, con sus relacionados.
        :param provider_id: Proveedor que sirvió esa ficha.
        :param callback: Recibe la línea en el hilo de Tk. Debe comprobar
            ``winfo_exists()`` de sus widgets: la ficha puede haberse ido.
        """
        threading.Thread(target=self.__walk_and_deliver, args=(anime_info, provider_id, callback),
                         daemon=True).start()

    def request_formats(self, anime_info: AnimeInfo, provider_id: AnimeProviderId,
                        callback: Callable[[Dict[str, FormatHint]], None]) -> None:
        """Completa en un hilo el formato de los relacionados del anime y vuelve en el acto.

        Por orden: lo que da el proveedor, las páginas ya descargadas, el título
        y, para lo que siga sin formato, **una** petición al otro proveedor con
        el mismo slug. Si allí no existe, se queda sin formato.

        :param anime_info: Ficha del anime que se está viendo, con sus relacionados.
        :param provider_id: Proveedor que sirvió esa ficha.
        :param callback: Recibe {id del relacionado: FormatHint} en el hilo de Tk,
            con una entrada por relacionado.
        """
        threading.Thread(target=self.__formats_and_deliver, args=(anime_info, provider_id, callback),
                         daemon=True).start()

    # ------------------------------------------------------------------
    # Hilos
    # ------------------------------------------------------------------
    def __deliver(self, callback: Callable, result) -> None:
        """Entrega un resultado en el hilo de Tk, si la ventana sigue abierta."""
        try:
            self.__main_window.after(0, self.__deliver_on_tk, callback, result)
        except RuntimeError:
            # La ventana ya se cerró y Tk no admite más trabajo.
            pass

    def __deliver_on_tk(self, callback: Callable, result) -> None:
        """Llama al callback ya en el hilo de Tk."""
        if self.__main_window.winfo_exists():
            callback(result)

    def __walk_and_deliver(self, anime_info: AnimeInfo, provider_id: AnimeProviderId,
                           callback: Callable[[FranchiseLine], None]) -> None:
        """Hilo de request_franchise()."""
        try:
            line = self.walk_franchise(anime_info, provider_id)
        except Exception as exc:
            print(f"[{provider_id.value}] Fallo al recorrer la franquicia de {anime_info.id!r}: {exc}")
            line = FranchiseLine(entries=[FranchiseEntry(id=str(anime_info.id), title=anime_info.title,
                                                         format=anime_info.format)],
                                 current_index=0, interrupted=True)
        self.__deliver(callback, line)

    def __formats_and_deliver(self, anime_info: AnimeInfo, provider_id: AnimeProviderId,
                              callback: Callable[[Dict[str, FormatHint]], None]) -> None:
        """Hilo de request_formats()."""
        try:
            hints = self.find_formats(anime_info, provider_id)
        except Exception as exc:
            print(f"[{provider_id.value}] Fallo al completar los formatos de {anime_info.id!r}: {exc}")
            hints = {str(related.id): FormatHint(related.format) for related in anime_info.related or []}
        self.__deliver(callback, hints)

    # ------------------------------------------------------------------
    # Trabajo síncrono: se ejecuta en el hilo que llama
    # ------------------------------------------------------------------
    def walk_franchise(self, anime_info: AnimeInfo, provider_id: AnimeProviderId) -> FranchiseLine:
        """Recorre la línea principal en el hilo que llama. Nunca lanza.

        :param anime_info: Ficha del anime de partida, con sus relacionados.
        :param provider_id: Proveedor que sirvió esa ficha.
        :return: Línea principal; solo el anime de partida si no tiene precuela ni secuela.
        """
        self.__remember(provider_id, anime_info)
        current_id = str(anime_info.id)
        current = FranchiseEntry(id=current_id, title=anime_info.title, format=anime_info.format,
                                 poster=anime_info.poster or None)
        visited: Set[str] = {current_id}
        before, truncated_before, interrupted_before = self.__walk_direction(
            anime_info, provider_id, AnimeRelationType.PREQUEL, visited, self.MAX_LINE_LENGTH - 1)
        after, truncated_after, interrupted_after = self.__walk_direction(
            anime_info, provider_id, AnimeRelationType.SEQUEL, visited,
            self.MAX_LINE_LENGTH - 1 - len(before))

        # El año del anime de partida solo lo sabe quien apunta a él.
        year = self.__year_pointed_from(before[0][1] if before else None, current_id) \
            or self.__year_pointed_from(after[0][1] if after else None, current_id)
        if year is not None:
            current = dataclasses.replace(current, year=year)

        entries = [entry for entry, _ in reversed(before)] + [current] + [entry for entry, _ in after]
        return FranchiseLine(entries=entries, current_index=len(before),
                             truncated=truncated_before or truncated_after,
                             interrupted=interrupted_before or interrupted_after)

    def find_formats(self, anime_info: AnimeInfo, provider_id: AnimeProviderId) -> Dict[str, FormatHint]:
        """Calcula el formato de cada relacionado en el hilo que llama. Nunca lanza.

        :param anime_info: Ficha del anime, con sus relacionados.
        :param provider_id: Proveedor que sirvió esa ficha.
        :return: {id del relacionado: FormatHint}, con una entrada por relacionado.
        """
        self.__remember(provider_id, anime_info)
        hints: Dict[str, FormatHint] = {}
        missing: List[RelatedAnime] = []
        for related in anime_info.related or []:
            related_id = str(related.id)
            anime_format = related.format or self.__cached_format(provider_id, related_id)
            if anime_format is not None:
                hints[related_id] = FormatHint(anime_format)
                continue
            deduced = deduce_format_from_title(related.title)
            if deduced is not None:
                hints[related_id] = FormatHint(deduced, deduced=True)
                continue
            hints[related_id] = FormatHint(None)
            missing.append(related)

        if missing:
            hints.update(self.__formats_from_other_provider(anime_info, provider_id, missing))
        return hints

    # ------------------------------------------------------------------
    # Recorrido
    # ------------------------------------------------------------------
    def __walk_direction(self, start: AnimeInfo, provider_id: AnimeProviderId, relation: AnimeRelationType,
                         visited: Set[str], limit: int) -> Tuple[List[Tuple[FranchiseEntry, Optional[AnimeInfo]]],
                                                                 bool, bool]:
        """Sigue una relación de página en página hasta que se acabe.

        :param start: Página de partida.
        :param provider_id: Proveedor de todas las páginas.
        :param relation: PREQUEL para ir hacia atrás, SEQUEL hacia delante.
        :param visited: Ids ya en la línea; se amplía en el sitio y corta los ciclos.
        :param limit: Temporadas que caben todavía en la línea.
        :return: Tupla ([(temporada, su página o None)] desde la más cercana,
            si se paró por el tope, si se paró por un fallo).
        """
        steps: List[Tuple[FranchiseEntry, Optional[AnimeInfo]]] = []
        page: Optional[AnimeInfo] = start
        while page is not None:
            next_related = closest_related(page.related or [], relation, visited)
            if next_related is None:
                return steps, False, False
            if len(steps) >= limit:
                return steps, True, False
            next_id = str(next_related.id)
            visited.add(next_id)
            page = self.__get_page(provider_id, next_id)
            steps.append((self.__entry_from(next_related, page), page))
            if page is None:
                return steps, False, True
        return steps, False, False

    @staticmethod
    def __entry_from(related: RelatedAnime, page: Optional[AnimeInfo]) -> FranchiseEntry:
        """Una temporada a partir de la relación que la anunció y, si llegó, su página."""
        if page is None:
            return FranchiseEntry(id=str(related.id), title=related.title, format=related.format,
                                  year=related.year, poster=related.poster)
        return FranchiseEntry(id=str(related.id), title=page.title or related.title,
                              format=page.format or related.format, year=related.year,
                              poster=related.poster or page.poster or None)

    @staticmethod
    def __year_pointed_from(page: Optional[AnimeInfo], anime_id: str) -> Optional[int]:
        """El año con el que una página vecina anuncia al anime dado, si lo da."""
        for related in (page.related or []) if page is not None else []:
            if str(related.id) == anime_id and related.year is not None:
                return related.year
        return None

    # ------------------------------------------------------------------
    # Formatos del otro proveedor
    # ------------------------------------------------------------------
    def __cached_format(self, provider_id: AnimeProviderId, anime_id: str) -> Optional[AnimeFormat]:
        """El formato de una página ya descargada en la sesión, sin pedir nada."""
        with self.__lock:
            page = self.__pages.get((provider_id, anime_id))
        return page.format if page is not None else None

    def __formats_from_other_provider(self, anime_info: AnimeInfo, provider_id: AnimeProviderId,
                                      missing: List[RelatedAnime]) -> Dict[str, FormatHint]:
        """Busca el formato de los relacionados que faltan en el mismo anime de otro sitio.

        Una sola petición: el mismo slug en el primer proveedor cuyos relacionados
        traigan formato. Si allí es otro anime, no vale nada de lo que diga.

        :return: {id del relacionado: FormatHint} solo de los que se encontraron.
        """
        other_id = next((pid for pid in self.__anime_provider_mgr.list_providers()
                         if pid != provider_id and self.__anime_provider_mgr.get(pid).RELATIONS_CARRY_FORMAT),
                        None)
        if other_id is None:
            return {}
        other_page = self.__get_page(other_id, str(anime_info.id))
        if other_page is None:
            return {}
        threshold = AnimeProviderManager.TITLE_MATCH_THRESHOLD
        if AnimeProviderManager.title_similarity(anime_info.title, other_page.title) < threshold:
            print(f"[{other_id.value}] {anime_info.id!r} es {other_page.title!r}, no {anime_info.title!r}: "
                  f"no se usan sus formatos")
            return {}

        short_name = self.__anime_provider_mgr.get_provider_info(other_id).short_name
        other_related = [item for item in other_page.related or [] if item.format is not None]
        hints: Dict[str, FormatHint] = {}
        for related in missing:
            match = next((item for item in other_related if str(item.id) == str(related.id)), None)
            if match is None:
                scored = [(AnimeProviderManager.title_similarity(related.title, item.title), item)
                          for item in other_related]
                best_ratio, best = max(scored, key=lambda pair: pair[0], default=(0.0, None))
                match = best if best_ratio >= threshold else None
            if match is not None:
                hints[str(related.id)] = FormatHint(match.format, short_name=short_name)
        return hints

    # ------------------------------------------------------------------
    # Páginas
    # ------------------------------------------------------------------
    def __remember(self, provider_id: AnimeProviderId, anime_info: AnimeInfo) -> None:
        """Guarda en la caché la ficha que ya tiene la interfaz, sin sus episodios.

        Es una copia: la ficha reordena sus episodios y sus relacionados en el sitio.
        """
        page = dataclasses.replace(anime_info, episodes=None, related=list(anime_info.related or []))
        with self.__lock:
            self.__pages[(provider_id, str(anime_info.id))] = page

    def __get_page(self, provider_id: AnimeProviderId, anime_id: str) -> Optional[AnimeInfo]:
        """La página de un anime: de la caché o, si no está, una petición espaciada.

        El lock del proveedor turna las peticiones y hace que dos hilos que piden
        la misma página solo la descarguen una vez.

        :return: La página, o None si falla o falló hace menos de RETRY_FAILED_AFTER_S.
        """
        key = (provider_id, anime_id)
        with self.__lock:
            provider_lock = self.__provider_locks.setdefault(provider_id, threading.Lock())
        with provider_lock:
            with self.__lock:
                if key in self.__pages:
                    return self.__pages[key]
                failed_at = self.__failed_at.get(key)
                if failed_at is not None and time.monotonic() - failed_at < self.RETRY_FAILED_AFTER_S:
                    return None
                wait = self.__last_request_at.get(provider_id, 0.0) + self.REQUEST_SPACING_S - time.monotonic()
            if wait > 0:
                time.sleep(wait)

            page = self.__anime_provider_mgr.get_anime_relations(anime_id, provider_id)

            with self.__lock:
                self.__last_request_at[provider_id] = time.monotonic()
                if page is None:
                    self.__failed_at[key] = time.monotonic()
                    return None
                page = dataclasses.replace(page, episodes=None)
                self.__pages[key] = page
                return page
