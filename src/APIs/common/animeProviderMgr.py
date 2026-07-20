__author__ = "Jose David Escribano Orts"
__subsystem__ = "APIs.common"
__module__ = "animeProvider.py"
__version__ = "0.1"
__info__ = {"subsystem": __subsystem__, "module_name": __module__, "version": __version__}

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple, Union
import requests

from APIs.common.models import AnimeGenreFilter, AnimeInfo, ServerInfo

# Alias de tipo para no repetir la tupla (lista de animes, última página) en cada firma de método.
AnimeSearchResult = Tuple[List[AnimeInfo], int]


class UnknownProviderError(Exception):
    """Se lanza al pedir un proveedor con un PROVIDER_ID no registrado."""


class AnimeProvider(ABC):
    """
    Contrato que debe cumplir cualquier proveedor de anime (AnimeFLV, AnimeAV1,
    y en el futuro MonosChinos2, TioAnime, JKAnime, etc.).

    Cada proveedor concreto:
      1. Define PROVIDER_ID, PROVIDER_NAME y BASE_URL como atributos de clase.
      2. Implementa los 5 métodos abstractos siempre devolviendo las estructuras
         de datos comunes definidas en APIs.common.models (AnimeInfo, EpisodeInfo,
         ServerInfo), nunca tipos propios del sitio.
      3. Si el sitio usa slugs de género distintos a los de AnimeGenreFilter,
         el proveedor debe encargarse internamente de traducirlos (por ejemplo,
         con un diccionario privado {AnimeGenreFilter.ACCIÓN: "action"}), de forma
         que quien llama a search_animes_by_genres_and_order siga usando siempre
         el enum común sin preocuparse de las particularidades de cada web.

    De esta forma, AnimeProviderManager (ver provider_manager.py) puede tratar a
    todos los proveedores de forma intercambiable: elegir uno por defecto, elegir
    uno puntual para una operación concreta, o hacer fallback automático a otro
    proveedor si el primero falla o no devuelve resultados.
    """

    #: Identificador corto y estable del proveedor (se usa como clave en el
    #: registro de AnimeProviderManager). Ej: "animeflv", "animeav1".
    PROVIDER_ID: str = NotImplemented

    #: Nombre legible para mostrar en la interfaz. Ej: "AnimeFLV".
    PROVIDER_NAME: str = NotImplemented

    #: URL base del sitio, usada tanto para hacer scraping como para el
    #: chequeo de disponibilidad por defecto (is_available).
    BASE_URL: str = NotImplemented

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        # Evita registrar por error un proveedor a medio implementar: si una
        # subclase concreta (no abstracta) olvida rellenar estos atributos,
        # falla pronto y con un mensaje claro en vez de romper en tiempo de uso.
        if ABC not in cls.__bases__:
            for attr in ("PROVIDER_ID", "PROVIDER_NAME", "BASE_URL"):
                if getattr(cls, attr, NotImplemented) is NotImplemented:
                    raise NotImplementedError(
                        f"{cls.__name__} debe definir el atributo de clase '{attr}'"
                    )

    @abstractmethod
    def search_animes_by_genres_and_order(self, genres: List[AnimeGenreFilter], order: str = None,
                                          page: int = None) -> AnimeSearchResult:
        """Busca animes filtrando por género(s) y devuelve (lista de animes, última página)."""
        raise NotImplementedError

    @abstractmethod
    def search_animes_by_query(self, query: str = None, page: int = None) -> AnimeSearchResult:
        """Busca animes por texto libre y devuelve (lista de animes, última página)."""
        raise NotImplementedError

    @abstractmethod
    def get_anime_episode_servers(self, anime_id: Union[str, int], episode_id: int) -> List[ServerInfo]:
        """Devuelve los servidores de vídeo disponibles para un episodio concreto."""
        raise NotImplementedError

    @abstractmethod
    def get_recent_animes(self) -> List[AnimeInfo]:
        """Devuelve los animes recientemente añadidos/actualizados en el sitio."""
        raise NotImplementedError

    @abstractmethod
    def get_anime_info(self, anime_id: Union[str, int]) -> AnimeInfo:
        """Devuelve la ficha completa de un anime (sinopsis, géneros, episodios...)."""
        raise NotImplementedError

    def is_available(self, timeout: float = 5.0) -> bool:
        """
        Chequeo de disponibilidad por defecto: comprueba que BASE_URL responde.
        Los proveedores pueden sobrescribirlo con algo más barato/preciso
        (p.ej. un endpoint de salud, o una petición HEAD) si lo necesitan.
        Se usa desde AnimeProviderManager para descartar proveedores caídos
        antes de intentar operaciones más costosas.
        """
        try:
            response = requests.get(self.BASE_URL, timeout=timeout)
            return response.ok
        except requests.RequestException:
            return False

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} provider_id={self.PROVIDER_ID!r}>"


class AnimeProviderManager:
    """
    Registro central de proveedores de anime (AnimeFLV, AnimeAV1, MonosChinos2,
    TioAnime, JKAnime...). Permite:

      - Registrar proveedores y marcar uno como predeterminado.
      - Obtener un proveedor concreto por su PROVIDER_ID para casos puntuales
        (p.ej. "quiero buscar SIEMPRE en JKAnime para esta operación").
      - Ejecutar una operación con fallback automático: si el proveedor
        solicitado (o el predeterminado) falla o no devuelve resultados, se
        prueba con el resto de proveedores registrados en orden hasta obtener
        una respuesta válida.

    Uso típico (por ejemplo en main_window.py, al arrancar la aplicación):

        manager = AnimeProviderManagerSingleton()
        manager.register(AnimeFLVSingleton(), default=True)
        manager.register(AnimeAV1Singleton())
        # más adelante: manager.register(MonosChinos2Singleton())

    Y luego, en vez de llamar directamente a AnimeFLVSingleton().get_recent_animes(),
    cualquier parte de la app puede llamar a:

        manager.get_recent_animes()                       # usa el predeterminado, con fallback
        manager.get_recent_animes(provider_id="animeav1")  # fuerza un proveedor concreto
    """

    def __init__(self):
        self._providers: Dict[str, AnimeProvider] = {}
        self._default_provider_id: Optional[str] = None

    def register(self, provider: AnimeProvider, default: bool = False) -> None:
        """
        Registra un proveedor. El primero que se registra se convierte en
        predeterminado automáticamente; para forzar otro predeterminado más
        adelante, usa default=True o set_default().
        """
        self._providers[provider.PROVIDER_ID] = provider
        if default or self._default_provider_id is None:
            self._default_provider_id = provider.PROVIDER_ID

    def unregister(self, provider_id: str) -> None:
        self._providers.pop(provider_id, None)
        if self._default_provider_id == provider_id:
            self._default_provider_id = next(iter(self._providers), None)

    def set_default(self, provider_id: str) -> None:
        if provider_id not in self._providers:
            raise UnknownProviderError(f"Proveedor desconocido: {provider_id}")
        self._default_provider_id = provider_id

    def get_default_provider_id(self) -> Optional[str]:
        return self._default_provider_id

    def get(self, provider_id: str = None) -> AnimeProvider:
        """Devuelve un proveedor concreto, o el predeterminado si no se indica ninguno."""
        target_id = provider_id or self._default_provider_id
        if target_id is None:
            raise UnknownProviderError("No hay ningún proveedor registrado")
        if target_id not in self._providers:
            raise UnknownProviderError(f"Proveedor desconocido: {target_id}")
        return self._providers[target_id]

    def list_providers(self) -> List[str]:
        return list(self._providers.keys())

    def list_available_providers(self) -> List[str]:
        """Subconjunto de proveedores registrados que responden ahora mismo (is_available)."""
        return [pid for pid, provider in self._providers.items() if provider.is_available()]

    def _ordered_providers(self, provider_id: str = None) -> List[AnimeProvider]:
        """
        Orden en el que se intentan los proveedores para el fallback: primero
        el solicitado explícitamente (o si no, el predeterminado), y después
        el resto por orden de registro.
        """
        preferred_id = provider_id or self._default_provider_id
        ordered = []
        if preferred_id in self._providers:
            ordered.append(self._providers[preferred_id])
        ordered.extend(provider for pid, provider in self._providers.items() if pid != preferred_id)
        return ordered

    @staticmethod
    def __is_empty_result(result: Any) -> bool:
        """Considera 'sin resultado útil' tanto None como listas vacías o (lista_vacía, ...)."""
        if result is None:
            return True
        if isinstance(result, list):
            return len(result) == 0
        if isinstance(result, tuple) and len(result) > 0 and isinstance(result[0], list):
            return len(result[0]) == 0
        return False

    def call_with_fallback(self, method_name: str, *args, provider_id: str = None,
                           strict: bool = False, **kwargs) -> Tuple[Any, Optional[str]]:
        """
        Llama a `method_name` sobre el proveedor solicitado (o el predeterminado).
        Si lanza una excepción, o devuelve un resultado vacío, prueba con el resto
        de proveedores registrados en orden hasta conseguir un resultado útil.

        :param strict: si es True, NO hace fallback a otros proveedores: solo se
            intenta el proveedor solicitado (útil para el caso puntual "quiero
            esto de JKAnime y de ningún otro sitio").
        :return: tupla (resultado, provider_id_usado). Si todos los proveedores
            fallan, devuelve (None, None).
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
                print(f"[{provider.PROVIDER_ID}] Fallo en '{method_name}': {exc}")
                continue

            if self.__is_empty_result(result):
                print(f"[{provider.PROVIDER_ID}] '{method_name}' no devolvió resultados, "
                      f"probando siguiente proveedor...")
                continue

            return result, provider.PROVIDER_ID

        if last_exception is not None:
            print(f"Todos los proveedores fallaron en '{method_name}': {last_exception}")
        else:
            print(f"Ningún proveedor devolvió resultados para '{method_name}'")
        return None, None

    # ------------------------------------------------------------------
    # Wrappers de conveniencia: mismo nombre/firma que AnimeProvider, más el
    # parámetro opcional provider_id para forzar un proveedor puntual, y
    # fallback automático transparente al resto de proveedores registrados.
    # ------------------------------------------------------------------

    def get_recent_animes(self, provider_id: str = None, strict: bool = False) -> List[AnimeInfo]:
        result, _ = self.call_with_fallback("get_recent_animes", provider_id=provider_id, strict=strict)
        return result if result is not None else []

    def get_anime_info(self, anime_id, provider_id: str = None, strict: bool = False) -> Optional[AnimeInfo]:
        result, _ = self.call_with_fallback("get_anime_info", anime_id, provider_id=provider_id, strict=strict)
        return result

    def search_animes_by_query(self, query: str = None, page: int = None, provider_id: str = None,
                               strict: bool = False):
        result, _ = self.call_with_fallback("search_animes_by_query", query, page,
                                            provider_id=provider_id, strict=strict)
        return result if result is not None else ([], 1)

    def search_animes_by_genres_and_order(self, genres, order: str = None, page: int = None,
                                          provider_id: str = None, strict: bool = False):
        result, _ = self.call_with_fallback("search_animes_by_genres_and_order", genres, order, page,
                                            provider_id=provider_id, strict=strict)
        return result if result is not None else ([], 1)

    def get_anime_episode_servers(self, anime_id, episode_id, provider_id: str = None,
                                  strict: bool = False) -> List[ServerInfo]:
        result, _ = self.call_with_fallback("get_anime_episode_servers", anime_id, episode_id,
                                            provider_id=provider_id, strict=strict)
        return result if result is not None else []


class AnimeProviderManagerSingleton:
    __instance = None

    def __new__(cls):
        if AnimeProviderManagerSingleton.__instance is None:
            AnimeProviderManagerSingleton.__instance = AnimeProviderManager()
        return AnimeProviderManagerSingleton.__instance