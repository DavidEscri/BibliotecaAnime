__author__ = "Jose David Escribano Orts"
__subsystem__ = "APIs.common"
__module__ = "animeProviderMgr.py"
__version__ = "0.3"
__info__ = {"subsystem": __subsystem__, "module_name": __module__, "version": __version__}

import difflib
import re
import unicodedata
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple, Union
import requests

from APIs.common.models import AnimeGenreFilter, AnimeInfo, AnimeProviderId, ProviderInfo, ServerInfo

AnimeSearchResult = Tuple[List[AnimeInfo], int]


class UnknownProviderError(Exception):
    """Se lanza al pedir un proveedor con un PROVIDER_ID no registrado."""


class AnimeProvider(ABC):
    """Contrato que debe cumplir cualquier proveedor de anime.

    Cada proveedor concreto define PROVIDER_ID, PROVIDER_NAME y BASE_URL como
    atributos de clase, implementa los métodos abstractos devolviendo siempre
    las estructuras comunes de APIs.common.models, y traduce internamente
    cualquier slug de género propio de su sitio a AnimeGenreFilter.
    """

    #: Identificador único del proveedor; debe ser un miembro de AnimeProviderId.
    PROVIDER_ID: AnimeProviderId = NotImplemented

    #: Nombre legible para mostrar en la interfaz.
    PROVIDER_NAME: str = NotImplemented

    #: URL base del sitio.
    BASE_URL: str = NotImplemented

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if ABC not in cls.__bases__:
            for attr in ("PROVIDER_ID", "PROVIDER_NAME", "BASE_URL"):
                if getattr(cls, attr, NotImplemented) is NotImplemented:
                    raise NotImplementedError(
                        f"{cls.__name__} debe definir el atributo de clase '{attr}'"
                    )
            if not isinstance(cls.PROVIDER_ID, AnimeProviderId):
                raise NotImplementedError(
                    f"{cls.__name__}.PROVIDER_ID debe ser un miembro de AnimeProviderId, "
                    f"no {type(cls.PROVIDER_ID).__name__}"
                )

    @classmethod
    def provider_info(cls) -> ProviderInfo:
        """Ficha de identidad del proveedor, construida desde sus atributos de clase.

        :return: ProviderInfo con id, nombre y URL base.
        """
        return ProviderInfo(id=cls.PROVIDER_ID, name=cls.PROVIDER_NAME, base_url=cls.BASE_URL)

    @abstractmethod
    def search_animes_by_genres_and_order(self, genres: List[AnimeGenreFilter], order: str = None,
                                          page: int = None) -> AnimeSearchResult:
        """Busca animes filtrando por uno o varios géneros, con orden y página opcionales.

        :param genres: Géneros por los que filtrar.
        :param order: Criterio de orden a aplicar, si el proveedor lo soporta.
        :param page: Página de resultados a obtener.
        :return: Tupla (lista de animes, última página disponible).
        """
        raise NotImplementedError

    @abstractmethod
    def search_animes_by_query(self, query: str = None, page: int = None) -> AnimeSearchResult:
        """Busca animes por texto libre.

        :param query: Texto de búsqueda.
        :param page: Página de resultados a obtener.
        :return: Tupla (lista de animes, última página disponible).
        """
        raise NotImplementedError

    @abstractmethod
    def get_anime_episode_servers(self, anime_id: Union[str, int], episode_id: int) -> List[ServerInfo]:
        """Obtiene los servidores de vídeo disponibles para un episodio.

        :param anime_id: Identificador del anime en el proveedor.
        :param episode_id: Número del episodio.
        :return: Lista de servidores disponibles.
        """
        raise NotImplementedError

    @abstractmethod
    def get_recent_animes(self) -> List[AnimeInfo]:
        """Obtiene los animes recientemente añadidos o actualizados en el sitio.

        :return: Lista de animes recientes.
        """
        raise NotImplementedError

    @abstractmethod
    def get_anime_info(self, anime_id: Union[str, int]) -> AnimeInfo:
        """Obtiene la ficha completa de un anime.

        :param anime_id: Identificador del anime en el proveedor.
        :return: Ficha completa (sinopsis, géneros, episodios...).
        """
        raise NotImplementedError

    def is_available(self, timeout: float = 5.0) -> bool:
        """Comprueba si el proveedor responde, haciendo una petición a BASE_URL.

        :param timeout: Tiempo máximo de espera, en segundos.
        :return: True si el sitio responde correctamente.
        """
        try:
            response = requests.get(self.BASE_URL, timeout=timeout)
            return response.ok
        except requests.RequestException:
            return False

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} provider_id={self.PROVIDER_ID.value!r}>"


class AnimeProviderManager:
    """Registro central de proveedores de anime.

    Permite registrar proveedores, marcar uno como predeterminado, obtener uno
    concreto por su PROVIDER_ID para una operación puntual, y ejecutar llamadas
    con fallback automático al resto de proveedores registrados cuando el
    solicitado (o el predeterminado) falla o no devuelve resultados.
    """

    #: Umbral de similitud de título por debajo del cual resolve_anime_in_provider
    #: considera que el anime no existe en el proveedor destino.
    TITLE_MATCH_THRESHOLD: float = 0.75

    def __init__(self):
        self._providers: Dict[AnimeProviderId, AnimeProvider] = {}
        self._default_provider_id: Optional[AnimeProviderId] = None

    def register(self, provider: AnimeProvider, default: bool = False) -> None:
        """Registra un proveedor. El primero registrado queda como predeterminado.

        :param provider: Proveedor a registrar.
        :param default: Si es True, lo fija como predeterminado aunque ya hubiera otro.
        """
        self._providers[provider.PROVIDER_ID] = provider
        if default or self._default_provider_id is None:
            self._default_provider_id = provider.PROVIDER_ID

    def unregister(self, provider_id: AnimeProviderId) -> None:
        """Elimina un proveedor del registro y reasigna el predeterminado si era él.

        :param provider_id: Proveedor a eliminar.
        """
        self._providers.pop(provider_id, None)
        if self._default_provider_id == provider_id:
            self._default_provider_id = next(iter(self._providers), None)

    def set_default(self, provider_id: AnimeProviderId | None) -> None:
        """Fija el proveedor predeterminado.

        :param provider_id: Proveedor a marcar como predeterminado; debe estar registrado.
        """
        if provider_id is None or provider_id not in self._providers:
            raise UnknownProviderError(f"Proveedor desconocido: {provider_id}")
        self._default_provider_id = provider_id

    def get_default_provider_id(self) -> Optional[AnimeProviderId]:
        """:return: Id del proveedor predeterminado, o None si no hay ninguno registrado."""
        return self._default_provider_id

    def get(self, provider_id: AnimeProviderId = None) -> AnimeProvider:
        """Devuelve un proveedor concreto, o el predeterminado si no se indica ninguno.

        :param provider_id: Proveedor solicitado; opcional.
        :return: Instancia del proveedor.
        """
        target_id = provider_id or self._default_provider_id
        if target_id is None:
            raise UnknownProviderError("No hay ningún proveedor registrado")
        if target_id not in self._providers:
            raise UnknownProviderError(f"Proveedor desconocido: {target_id}")
        return self._providers[target_id]

    def list_providers(self) -> List[AnimeProviderId]:
        """:return: Ids de todos los proveedores registrados."""
        return list(self._providers.keys())

    def get_provider_info(self, provider_id: AnimeProviderId) -> Optional[ProviderInfo]:
        """Ficha de identidad de un proveedor registrado.

        :param provider_id: Proveedor consultado.
        :return: ProviderInfo, o None si no está registrado.
        """
        provider = self._providers.get(provider_id)
        return provider.provider_info() if provider is not None else None

    def list_providers_info(self) -> List[ProviderInfo]:
        """:return: Ficha de todos los proveedores registrados, en orden de registro."""
        return [provider.provider_info() for provider in self._providers.values()]

    def get_provider_name(self, provider_id: Optional[AnimeProviderId]) -> str:
        """Nombre legible de un proveedor.

        :param provider_id: Proveedor consultado; admite None.
        :return: Nombre legible, su propio id si no está registrado, o "desconocido" si es None.
        """
        if provider_id is None:
            return "desconocido"
        provider = self._providers.get(provider_id)
        return provider.PROVIDER_NAME if provider is not None else provider_id.value

    def get_provider_info_by_name(self, provider_name: str) -> Optional[ProviderInfo]:
        """Traduce un PROVIDER_NAME de vuelta a la ficha de su proveedor.

        :param provider_name: Nombre legible del proveedor.
        :return: ProviderInfo del proveedor, o None si no coincide ninguno.
        """
        for provider in self._providers.values():
            if provider.PROVIDER_NAME == provider_name:
                return provider.provider_info()
        return None

    def list_available_providers(self) -> List[AnimeProviderId]:
        """:return: Ids de los proveedores registrados que responden ahora mismo."""
        return [pid for pid, provider in self._providers.items() if provider.is_available()]

    def _ordered_providers(self, provider_id: AnimeProviderId = None) -> List[AnimeProvider]:
        """Orden en el que se intentan los proveedores para el fallback.

        :param provider_id: Proveedor a intentar primero; por defecto el predeterminado.
        :return: Proveedores ordenados: el preferido primero, el resto por orden de registro.
        """
        preferred_id = provider_id or self._default_provider_id
        ordered = []
        if preferred_id in self._providers:
            ordered.append(self._providers[preferred_id])
        ordered.extend(provider for pid, provider in self._providers.items() if pid != preferred_id)
        return ordered

    @staticmethod
    def __stamp_provider(result: Any, provider_id: AnimeProviderId) -> None:
        """Marca en cada AnimeInfo del resultado quién lo ha servido.

        Cubre las tres formas en que viaja un AnimeInfo por esta capa: suelto,
        en lista, o en la tupla (lista, última_página) de las búsquedas.

        :param result: Resultado devuelto por el proveedor.
        :param provider_id: Proveedor que lo sirvió.
        """
        if isinstance(result, tuple) and len(result) > 0:
            result = result[0]
        candidates = result if isinstance(result, list) else [result]
        for candidate in candidates:
            if isinstance(candidate, AnimeInfo):
                candidate.provider_id = provider_id

    @staticmethod
    def __is_empty_result(result: Any) -> bool:
        """:return: True si `result` es None, lista vacía, o (lista_vacía, ...)."""
        if result is None:
            return True
        if isinstance(result, list):
            return len(result) == 0
        if isinstance(result, tuple) and len(result) > 0 and isinstance(result[0], list):
            return len(result[0]) == 0
        return False

    def call_with_fallback(self, method_name: str, *args, provider_id: AnimeProviderId = None,
                           strict: bool = False, **kwargs) -> Tuple[Any, Optional[AnimeProviderId]]:
        """Llama a un método sobre un proveedor, reintentando con el resto si falla.

        Prueba el proveedor solicitado (o el predeterminado); si lanza una
        excepción o devuelve un resultado vacío, continúa con el resto de
        proveedores registrados en orden hasta obtener un resultado útil.

        :param method_name: Nombre del método de AnimeProvider a invocar.
        :param provider_id: Proveedor por el que empezar; por defecto el predeterminado.
        :param strict: Si es True, no hace fallback a otros proveedores.
        :return: Tupla (resultado, provider_id que respondió), o (None, None) si todos fallan.
        """
        providers_to_try = self._ordered_providers(provider_id)
        if strict:
            providers_to_try = providers_to_try[:1]

        last_exception: Optional[Exception] = None
        for provider in providers_to_try:
            try:
                method = getattr(provider, method_name)
                result = method(*args, **kwargs)
            except Exception as exc:
                last_exception = exc
                print(f"[{provider.PROVIDER_ID.value}] Fallo en '{method_name}': {exc}")
                continue

            if self.__is_empty_result(result):
                print(f"[{provider.PROVIDER_ID.value}] '{method_name}' no devolvió resultados, "
                      f"probando siguiente proveedor...")
                continue

            self.__stamp_provider(result, provider.PROVIDER_ID)
            return result, provider.PROVIDER_ID

        if last_exception is not None:
            print(f"Todos los proveedores fallaron en '{method_name}': {last_exception}")
        else:
            print(f"Ningún proveedor devolvió resultados para '{method_name}'")
        return None, None

    # ------------------------------------------------------------------
    # Wrappers de conveniencia, con fallback automático incorporado
    # ------------------------------------------------------------------

    def get_recent_animes(self, provider_id: AnimeProviderId = None, strict: bool = False) -> List[AnimeInfo]:
        """:return: Animes recientes del proveedor solicitado (o con fallback); [] si ninguno responde."""
        result, _ = self.call_with_fallback("get_recent_animes", provider_id=provider_id, strict=strict)
        return result if result is not None else []

    def get_anime_info(self, anime_id, provider_id: AnimeProviderId = None,
                       strict: bool = False) -> Optional[AnimeInfo]:
        """:return: Ficha del anime, o None si ningún proveedor responde."""
        result, _ = self.call_with_fallback("get_anime_info", anime_id, provider_id=provider_id, strict=strict)
        return result

    def get_anime_info_with_provider(self, anime_id, provider_id: AnimeProviderId = None,
                                     strict: bool = False) -> Tuple[Optional[AnimeInfo], Optional[AnimeProviderId]]:
        """Como get_anime_info, pero indicando también qué proveedor sirvió la ficha.

        :return: Tupla (AnimeInfo, provider_id), o (None, None) si nadie respondió.
        """
        return self.call_with_fallback("get_anime_info", anime_id, provider_id=provider_id, strict=strict)

    def search_animes_by_query(self, query: str = None, page: int = None,
                               provider_id: AnimeProviderId = None, strict: bool = False):
        """:return: Tupla (lista de animes, última página); ([], 1) si ningún proveedor responde."""
        result, _ = self.call_with_fallback("search_animes_by_query", query, page,
                                            provider_id=provider_id, strict=strict)
        return result if result is not None else ([], 1)

    def search_animes_by_genres_and_order(self, genres, order: str = None, page: int = None,
                                          provider_id: AnimeProviderId = None, strict: bool = False):
        """:return: Tupla (lista de animes, última página); ([], 1) si ningún proveedor responde."""
        result, _ = self.call_with_fallback("search_animes_by_genres_and_order", genres, order, page,
                                            provider_id=provider_id, strict=strict)
        return result if result is not None else ([], 1)

    def get_anime_episode_servers(self, anime_id, episode_id, provider_id: AnimeProviderId = None,
                                  strict: bool = False) -> List[ServerInfo]:
        """:return: Servidores de vídeo del episodio; [] si ningún proveedor responde."""
        result, _ = self.call_with_fallback("get_anime_episode_servers", anime_id, episode_id,
                                            provider_id=provider_id, strict=strict)
        return result if result is not None else []

    # ------------------------------------------------------------------
    # Identidad de un anime entre proveedores
    # ------------------------------------------------------------------
    @staticmethod
    def normalize_title(title: str) -> str:
        """Normaliza un título para poder compararlo entre sitios distintos.

        Pasa a minúsculas, quita tildes y reduce cualquier otro carácter a un
        espacio, de forma que variantes de formato del mismo título coincidan.

        :param title: Título a normalizar.
        :return: Título normalizado.
        """
        if not title:
            return ""
        decomposed = unicodedata.normalize("NFKD", title)
        without_accents = "".join(char for char in decomposed if not unicodedata.combining(char))
        return re.sub(r"[^a-z0-9]+", " ", without_accents.lower()).strip()

    def resolve_anime_in_provider(self, anime_info: AnimeInfo, provider_id: AnimeProviderId,
                                  threshold: float = None) -> Optional[AnimeInfo]:
        """Localiza el equivalente de un anime en otro proveedor por similitud de título.

        El id de un anime es el slug del sitio que lo sirvió, así que no es
        válido en otro proveedor: se busca por título y se toma la mejor
        coincidencia por encima del umbral.

        :param anime_info: Ficha del anime tal y como se está viendo ahora.
        :param provider_id: Proveedor en el que se quiere localizar el anime.
        :param threshold: Similitud mínima aceptada; por defecto TITLE_MATCH_THRESHOLD.
        :return: Ficha del anime en el proveedor destino, o None si no se encuentra.
        """
        if provider_id not in self._providers:
            print(f"No se puede resolver el anime: proveedor no registrado {provider_id}")
            return None

        threshold = self.TITLE_MATCH_THRESHOLD if threshold is None else threshold
        target_title = self.normalize_title(anime_info.title)
        if not target_title:
            print("No se puede resolver el anime: no tiene título con el que buscar")
            return None

        # strict=True: buscar en OTRO proveedor y que el fallback nos devuelva
        # resultados del actual no resolvería nada, solo confundiría.
        candidates, _ = self.search_animes_by_query(anime_info.title, provider_id=provider_id,
                                                    strict=True)
        if not candidates:
            print(f"[{provider_id.value}] Sin resultados al buscar {anime_info.title!r}")
            return None

        best_candidate: Optional[AnimeInfo] = None
        best_ratio: float = 0.0
        for candidate in candidates:
            candidate_title = self.normalize_title(candidate.title)
            if candidate_title == target_title:
                best_candidate, best_ratio = candidate, 1.0
                break
            ratio = difflib.SequenceMatcher(None, target_title, candidate_title).ratio()
            if ratio > best_ratio:
                best_candidate, best_ratio = candidate, ratio

        if best_candidate is None or best_ratio < threshold:
            print(f"[{provider_id.value}] {anime_info.title!r} no encontrado "
                  f"(mejor coincidencia {best_ratio:.2f} < {threshold})")
            return None

        resolved = self.get_anime_info(best_candidate.id, provider_id=provider_id, strict=True)
        if resolved is None:
            print(f"[{provider_id.value}] {best_candidate.id!r} apareció en la búsqueda "
                  f"pero su ficha no se pudo obtener")
            return None

        print(f"[{provider_id.value}] {anime_info.title!r} resuelto como {resolved.title!r} "
              f"(id={resolved.id!r}, similitud {best_ratio:.2f})")
        return resolved


class AnimeProviderManagerSingleton:
    __instance = None

    def __new__(cls):
        if AnimeProviderManagerSingleton.__instance is None:
            AnimeProviderManagerSingleton.__instance = AnimeProviderManager()
        return AnimeProviderManagerSingleton.__instance