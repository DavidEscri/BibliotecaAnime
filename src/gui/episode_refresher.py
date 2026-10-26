__author__ = "Jose David Escribano Orts"
__subsystem__ = "gui"
__module__ = "episode_refresher.py"
__version__ = "0.1"
__info__ = {"subsystem": __subsystem__, "module_name": __module__, "version": __version__}

"""Refresco en segundo plano de los episodios guardados en la biblioteca.

``ANIMES.episodes`` es el recuento del día en que se abrió la ficha, así que un
anime en emisión se queda atrás. Este servicio vuelve a preguntar al proveedor
de cada fila sin que ninguna vista espere: las vistas pintan con lo guardado y
se suscriben para repintar en el sitio lo que cambie.

Escribe en la biblioteca sin que el usuario lo pida, y por eso es conservador:

- cada fila se pide a **su** proveedor (``strict=True``): con fallback, el mismo
  slug en otro sitio puede tener otra cuenta de episodios;
- una respuesta sin episodios no escribe nada;
- solo se toca la columna ``episodes``, y solo si cambia el recuento.
"""
import copy
import threading
import time

from collections import deque
from typing import Callable, Deque, Dict, Iterable, List, Optional, Set, Tuple

from APIs.common.animeProviderMgr import AnimeProviderManager
from APIs.common.models import AnimeInfo, AnimeProviderId, EpisodeInfo
from dataPersistence.animesPersistence import AnimeRecord, AnimesPersistence


class EpisodeRefresher:
    """Cola de refresco por proveedor, con memoria de lo ya comprobado en la sesión.

    Hay como mucho un hilo por proveedor: dentro de un sitio las peticiones van
    de una en una y un sitio lento no retrasa a los demás. El estado compartido
    va bajo ``__lock``; escribir en la BD y avisar a las vistas, en el hilo de Tk.
    """

    #: Segundos durante los que una fila ya comprobada no se vuelve a pedir.
    FRESH_FOR_S: float = 30 * 60
    #: Fallos seguidos con los que un proveedor se da por caído hasta ``FRESH_FOR_S``.
    PROVIDER_FAILURES_LIMIT: int = 2

    def __init__(self, main_window, anime_provider_mgr: AnimeProviderManager,
                 animes_persistence: AnimesPersistence):
        """Crea el servicio, sin lanzar nada todavía.

        :param main_window: Ventana principal; se usa para volver al hilo de Tk.
        :param anime_provider_mgr: Gestor de proveedores.
        :param animes_persistence: Persistencia de la biblioteca.
        """
        self.__main_window = main_window
        self.__anime_provider_mgr = anime_provider_mgr
        self.__animes_persistence = animes_persistence

        self.__lock = threading.Lock()
        self.__queues: Dict[AnimeProviderId, Deque[str]] = {}
        self.__workers: Set[AnimeProviderId] = set()
        self.__in_flight: Set[str] = set()
        self.__checked_at: Dict[str, float] = {}
        self.__failures: Dict[AnimeProviderId, int] = {}
        self.__down_until: Dict[AnimeProviderId, float] = {}
        #: Última ficha completa servida para cada fila: (proveedor, ficha, cuándo).
        self.__infos: Dict[str, Tuple[AnimeProviderId, AnimeInfo, float]] = {}
        self.__listeners: List[Callable[[AnimeRecord], None]] = []

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------
    def subscribe(self, listener: Callable[[AnimeRecord], None]) -> None:
        """Registra a quien hay que avisar, en el hilo de Tk, con cada fila que cambie.

        :param listener: Recibe la fila ya releída de la BD. Debe comprobar
            ``winfo_exists()`` de sus widgets: la vista puede no estar en pantalla.
        """
        self.__listeners.append(listener)

    def refresh(self, anime_records: Iterable[AnimeRecord], urgent: bool = False) -> None:
        """Encola las filas que no se hayan comprobado hace poco y vuelve en el acto.

        Se saltan las filas sin proveedor, las que ya están en curso y las de un
        proveedor dado por caído.

        :param anime_records: Filas a comprobar.
        :param urgent: Las pone delante de la cola, en el orden dado: es lo que
            la vista tiene en pantalla.
        """
        records = list(anime_records)
        if urgent:
            records.reverse()
        now = time.monotonic()
        providers_to_start: List[AnimeProviderId] = []
        with self.__lock:
            for anime_record in records:
                provider_id = anime_record.provider_id
                if provider_id is None or self.__down_until.get(provider_id, 0.0) > now:
                    continue
                anime_id = str(anime_record.anime_id)
                if anime_id in self.__in_flight or self.__is_fresh(anime_id, now):
                    continue
                queue = self.__queues.setdefault(provider_id, deque())
                if anime_id in queue:
                    if not urgent:
                        continue
                    queue.remove(anime_id)
                if urgent:
                    queue.appendleft(anime_id)
                else:
                    queue.append(anime_id)
                if provider_id not in self.__workers:
                    self.__workers.add(provider_id)
                    providers_to_start.append(provider_id)

        for provider_id in providers_to_start:
            threading.Thread(target=self.__work, args=(provider_id,), daemon=True).start()

    def cached_info(self, anime_id: str, provider_id: Optional[AnimeProviderId]) -> Optional[AnimeInfo]:
        """La ficha que trajo el último refresco, si es de ese proveedor y sigue fresca.

        :param anime_id: Identificador de la fila.
        :param provider_id: Proveedor al que se iba a pedir la ficha.
        :return: Una copia, porque la ficha reordena sus episodios en el sitio; o
            ``None`` si no hay nada aprovechable.
        """
        with self.__lock:
            entry = self.__infos.get(str(anime_id))
        if entry is None or provider_id is None:
            return None
        cached_provider_id, anime_info, fetched_at = entry
        if cached_provider_id != provider_id or time.monotonic() - fetched_at > self.FRESH_FOR_S:
            return None
        return copy.deepcopy(anime_info)

    # ------------------------------------------------------------------
    # Hilo de cada proveedor
    # ------------------------------------------------------------------
    def __is_fresh(self, anime_id: str, now: float) -> bool:
        """:return: ``True`` si la fila se comprobó hace menos de ``FRESH_FOR_S``. Requiere el lock."""
        checked_at = self.__checked_at.get(anime_id)
        return checked_at is not None and now - checked_at < self.FRESH_FOR_S

    def __work(self, provider_id: AnimeProviderId) -> None:
        """Vacía la cola de un proveedor, una petición detrás de otra, y termina.

        :param provider_id: Proveedor del que se encarga este hilo.
        """
        while True:
            with self.__lock:
                queue = self.__queues.get(provider_id)
                if not queue or self.__down_until.get(provider_id, 0.0) > time.monotonic():
                    if queue:
                        queue.clear()
                    self.__workers.discard(provider_id)
                    return
                anime_id = queue.popleft()
                self.__in_flight.add(anime_id)

            anime_info, _ = self.__anime_provider_mgr.get_anime_info_with_provider(
                anime_id, provider_id=provider_id, strict=True)
            succeeded = anime_info is not None and bool(anime_info.episodes)

            with self.__lock:
                now = time.monotonic()
                self.__in_flight.discard(anime_id)
                self.__checked_at[anime_id] = now
                if succeeded:
                    self.__failures[provider_id] = 0
                    self.__infos[anime_id] = (provider_id, anime_info, now)
                else:
                    self.__failures[provider_id] = self.__failures.get(provider_id, 0) + 1
                    if self.__failures[provider_id] >= self.PROVIDER_FAILURES_LIMIT:
                        self.__down_until[provider_id] = now + self.FRESH_FOR_S
                        print(f"[{provider_id.value}] no responde: se deja de refrescar "
                              f"su biblioteca durante {int(self.FRESH_FOR_S // 60)} min")

            if not succeeded:
                continue
            try:
                self.__main_window.after(0, self.__apply, anime_id, provider_id, anime_info.episodes)
            except RuntimeError:
                # La ventana ya se cerró y Tk no admite más trabajo.
                return

    # ------------------------------------------------------------------
    # Hilo de Tk
    # ------------------------------------------------------------------
    def __apply(self, anime_id: str, provider_id: AnimeProviderId, episodes: List[EpisodeInfo]) -> None:
        """Persiste el recuento nuevo, si cambió, y avisa a las vistas.

        Se relee la fila antes de escribir: mientras llegaba la respuesta pudo
        borrarse o reapuntarse a otro proveedor, y entonces el dato ya no es suyo.
        """
        if not self.__main_window.winfo_exists():
            return
        anime_record = self.__animes_persistence.get_anime_by_anime_id(anime_id)
        if anime_record is None or anime_record.provider_id != provider_id:
            return
        if len(anime_record.episodes) == len(episodes):
            return
        if not self.__animes_persistence.update_anime_episodes(anime_id, episodes):
            return
        print(f"«{anime_record.title}» pasa de {len(anime_record.episodes)} a {len(episodes)} episodios")

        updated_record = self.__animes_persistence.get_anime_by_anime_id(anime_id)
        if updated_record is None:
            return
        for listener in list(self.__listeners):
            listener(updated_record)
