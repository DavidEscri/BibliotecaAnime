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

    #: Identificador del proveedor (se usa como clave en el registro de
    #: AnimeProviderManager). Es un miembro de AnimeProviderId, no una cadena.
    PROVIDER_ID: AnimeProviderId = NotImplemented

    #: Nombre legible para mostrar en la interfaz. Ej: "AnimeFLV".
    PROVIDER_NAME: str = NotImplemented

    #: URL base del sitio, usada tanto para hacer scraping como para el
    #: chequeo de disponibilidad por defecto (is_available).
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
        """
        Ficha de identidad del proveedor, construida desde sus atributos de clase.

        Es lo que consume la interfaz para poblar el desplegable de proveedor, de forma que no haya en la GUI ninguna
        lista de nombres que mantener a mano.
        """
        return ProviderInfo(id=cls.PROVIDER_ID, name=cls.PROVIDER_NAME, base_url=cls.BASE_URL)

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
        return f"<{self.__class__.__name__} provider_id={self.PROVIDER_ID.value!r}>"


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

    Uso típico (tal y como está hoy en main_window.py, al arrancar la aplicación):

        manager = AnimeProviderManagerSingleton()
        manager.register(AnimeAV1Singleton(), default=True)   # el orden de registro es el del fallback
        manager.register(JKAnimeSingleton())
        manager.register(AnimeFLVSingleton())
        # más adelante: manager.register(MonosChinos2Singleton())

    Y luego, en vez de llamar directamente a AnimeAV1Singleton().get_recent_animes(),
    cualquier parte de la app puede llamar a:

        manager.get_recent_animes()                                          # predeterminado, con fallback
        manager.get_recent_animes(provider_id=AnimeProviderId.ANIMEFLV)      # fuerza un proveedor concreto

    El predeterminado no es solo un detalle de arranque: es una **preferencia del
    usuario** persistida en DB_user.db y aplicada con set_default() antes de la
    primera petición (ver dataPersistence/userPersistence.py y
    .claude/docs/13-selector-de-proveedor.md).
    """

    #: Umbral de similitud de títulos por debajo del cual resolve_anime_in_provider
    #: considera que el anime NO existe en el proveedor destino. Preferir un falso
    #: negativo ("no lo encuentro") a abrir un anime equivocado.
    TITLE_MATCH_THRESHOLD: float = 0.75

    def __init__(self):
        self._providers: Dict[AnimeProviderId, AnimeProvider] = {}
        self._default_provider_id: Optional[AnimeProviderId] = None

    def register(self, provider: AnimeProvider, default: bool = False) -> None:
        """
        Registra un proveedor. El primero que se registra se convierte en
        predeterminado automáticamente; para forzar otro predeterminado más
        adelante, usa default=True o set_default().
        """
        self._providers[provider.PROVIDER_ID] = provider
        if default or self._default_provider_id is None:
            self._default_provider_id = provider.PROVIDER_ID

    def unregister(self, provider_id: AnimeProviderId) -> None:
        self._providers.pop(provider_id, None)
        if self._default_provider_id == provider_id:
            self._default_provider_id = next(iter(self._providers), None)

    def set_default(self, provider_id: AnimeProviderId | None) -> None:
        if provider_id is None or provider_id not in self._providers:
            raise UnknownProviderError(f"Proveedor desconocido: {provider_id}")
        self._default_provider_id = provider_id

    def get_default_provider_id(self) -> Optional[AnimeProviderId]:
        return self._default_provider_id

    def get(self, provider_id: AnimeProviderId = None) -> AnimeProvider:
        """Devuelve un proveedor concreto, o el predeterminado si no se indica ninguno."""
        target_id = provider_id or self._default_provider_id
        if target_id is None:
            raise UnknownProviderError("No hay ningún proveedor registrado")
        if target_id not in self._providers:
            raise UnknownProviderError(f"Proveedor desconocido: {target_id}")
        return self._providers[target_id]

    def list_providers(self) -> List[AnimeProviderId]:
        return list(self._providers.keys())

    def get_provider_info(self, provider_id: AnimeProviderId) -> Optional[ProviderInfo]:
        """Ficha de identidad de un proveedor registrado, o ``None`` si no lo está."""
        provider = self._providers.get(provider_id)
        return provider.provider_info() if provider is not None else None

    def list_providers_info(self) -> List[ProviderInfo]:
        """Devuelve la ficha de todos los proveedores registrados, **en orden de registro**.

        Es la **única** fuente del contenido de los desplegables de proveedor de
        la interfaz: la GUI no debe construir esa lista a mano. Cuando existan
        proveedores de manga, el filtrado por tipo de medio se hará aquí.
        """
        return [provider.provider_info() for provider in self._providers.values()]

    def get_provider_name(self, provider_id: Optional[AnimeProviderId]) -> str:
        """Nombre legible de un proveedor. Si no está registrado, devuelve su id.

        Tolera ``None`` porque quien lo llama suele venir de un ``provider_id``
        opcional (una ficha servida por nadie, una fila de BD sin proveedor).
        """
        if provider_id is None:
            return "desconocido"
        provider = self._providers.get(provider_id)
        return provider.PROVIDER_NAME if provider is not None else provider_id.value

    def get_provider_info_by_name(self, provider_name: str) -> Optional[ProviderInfo]:
        """Traduce un ``PROVIDER_NAME`` de vuelta a la ficha de su proveedor.

        Los widgets muestran el nombre legible pero el resto del código trabaja
        con ``AnimeProviderId``; esto cierra ese círculo sin que la GUI mantenga
        su propio mapa.
        """
        for provider in self._providers.values():
            if provider.PROVIDER_NAME == provider_name:
                return provider.provider_info()
        return None

    def list_available_providers(self) -> List[AnimeProviderId]:
        """Subconjunto de proveedores registrados que responden ahora mismo (is_available)."""
        return [pid for pid, provider in self._providers.items() if provider.is_available()]

    def _ordered_providers(self, provider_id: AnimeProviderId = None) -> List[AnimeProvider]:
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
    def __stamp_provider(result: Any, provider_id: AnimeProviderId) -> None:
        """Marca en cada ``AnimeInfo`` del resultado quién lo ha servido.

        Lo hace el manager y no cada proveedor por dos motivos: es el único que
        sabe cuál de ellos acabó respondiendo cuando entra el fallback, y así los
        proveedores no tienen que acordarse de rellenar el campo.

        Cubre las tres formas en que viaja un AnimeInfo por esta capa: suelto
        (``get_anime_info``), en lista (``get_recent_animes``) y en la tupla
        ``(lista, última_página)`` de las búsquedas. Cualquier otro resultado
        (``ServerInfo``, por ejemplo) se ignora en silencio.
        """
        if isinstance(result, tuple) and len(result) > 0:
            result = result[0]
        candidates = result if isinstance(result, list) else [result]
        for candidate in candidates:
            if isinstance(candidate, AnimeInfo):
                candidate.provider_id = provider_id

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

    def call_with_fallback(self, method_name: str, *args, provider_id: AnimeProviderId = None,
                           strict: bool = False, **kwargs) -> Tuple[Any, Optional[AnimeProviderId]]:
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
    # Wrappers de conveniencia: mismo nombre/firma que AnimeProvider, más el
    # parámetro opcional provider_id para forzar un proveedor puntual, y
    # fallback automático transparente al resto de proveedores registrados.
    # ------------------------------------------------------------------

    def get_recent_animes(self, provider_id: AnimeProviderId = None, strict: bool = False) -> List[AnimeInfo]:
        result, _ = self.call_with_fallback("get_recent_animes", provider_id=provider_id, strict=strict)
        return result if result is not None else []

    def get_anime_info(self, anime_id, provider_id: AnimeProviderId = None,
                       strict: bool = False) -> Optional[AnimeInfo]:
        result, _ = self.call_with_fallback("get_anime_info", anime_id, provider_id=provider_id, strict=strict)
        return result

    def get_anime_info_with_provider(self, anime_id, provider_id: AnimeProviderId = None,
                                     strict: bool = False) -> Tuple[Optional[AnimeInfo], Optional[AnimeProviderId]]:
        """Como ``get_anime_info``, pero devuelve también **quién** sirvió la ficha.

        El fallback es silencioso por diseño: quien llama pide el predeterminado y
        puede recibir datos de otro proveedor sin enterarse. La ficha de detalle
        necesita saberlo para dos cosas: mostrarlo en su selector de proveedor y
        pedir los servidores de vídeo al proveedor correcto (si no, pediría los
        servidores de un sitio con el slug de otro).

        :return: ``(AnimeInfo, provider_id)``, o ``(None, None)`` si nadie respondió.
        """
        return self.call_with_fallback("get_anime_info", anime_id, provider_id=provider_id, strict=strict)

    def search_animes_by_query(self, query: str = None, page: int = None,
                               provider_id: AnimeProviderId = None, strict: bool = False):
        result, _ = self.call_with_fallback("search_animes_by_query", query, page,
                                            provider_id=provider_id, strict=strict)
        return result if result is not None else ([], 1)

    def search_animes_by_genres_and_order(self, genres, order: str = None, page: int = None,
                                          provider_id: AnimeProviderId = None, strict: bool = False):
        result, _ = self.call_with_fallback("search_animes_by_genres_and_order", genres, order, page,
                                            provider_id=provider_id, strict=strict)
        return result if result is not None else ([], 1)

    def get_anime_episode_servers(self, anime_id, episode_id, provider_id: AnimeProviderId = None,
                                  strict: bool = False) -> List[ServerInfo]:
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
        espacio: "Ataque a los Titanes: Final" y "ataque-a-los-titanes final"
        acaban siendo la misma cadena.
        """
        if not title:
            return ""
        decomposed = unicodedata.normalize("NFKD", title)
        without_accents = "".join(char for char in decomposed if not unicodedata.combining(char))
        return re.sub(r"[^a-z0-9]+", " ", without_accents.lower()).strip()

    def resolve_anime_in_provider(self, anime_info: AnimeInfo, provider_id: AnimeProviderId,
                                  threshold: float = None) -> Optional[AnimeInfo]:
        """Busca el equivalente de un anime en otro proveedor y devuelve su ficha.

        ``AnimeInfo.id`` es el *slug* del sitio, no un identificador universal: el
        mismo anime es "one-piece" en AnimeAV1 y "one-piece-tv" en
        AnimeFLV. Por eso no se puede reutilizar el id al cambiar de proveedor;
        hay que volver a localizar el anime por su título.

        Cuesta **dos peticiones HTTP** (buscar + ficha), así que debe llamarse
        siempre desde un hilo secundario, nunca desde el hilo de Tkinter.

        Se prefiere un falso negativo a un falso positivo: si la mejor coincidencia
        no llega al umbral, devuelve ``None`` en vez de abrir otro anime parecido.

        :param anime_info: ficha del anime tal y como se está viendo ahora.
        :param provider_id: proveedor en el que se quiere localizar.
        :param threshold: similitud mínima; por defecto ``TITLE_MATCH_THRESHOLD``.
        :return: ``AnimeInfo`` del proveedor destino, o ``None``. Nunca lanza.
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