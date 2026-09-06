"""
Estructuras de datos comunes que devuelven todos los proveedores de anime.
Ningún proveedor debe redefinir estas clases: se importan siempre desde aquí.
"""
__author__ = "Jose David Escribano Orts"
__subsystem__ = "APIs.models"
__module__ = "models.py"
__version__ = "0.2"
__info__ = {"subsystem": __subsystem__, "module_name": __module__, "version": __version__}

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Union


class AnimeProviderId(Enum):
    """Identificador de cada proveedor de anime registrable.

    Es un enum y no una cadena suelta para que el proveedor sea un tipo con
    nombre en todo el código; su valor es lo que se persiste en la base de datos.
    """
    ANIMEAV1 = "animeav1"
    JKANIME = "jkanime"
    ANIMEFLV = "animeflv"


class ProviderType(Enum):
    """Tipo de medio que sirve un proveedor."""
    ANIME = "anime"
    MANGA = "manga"

@dataclass(frozen=True)
class ProviderInfo:
    """Ficha de identidad de un proveedor: lo que la interfaz necesita saber de él.

    Se construye a partir de los atributos de clase del proveedor
    (AnimeProvider.provider_info()); es frozen porque describe una constante.
    """
    id: AnimeProviderId
    name: str
    base_url: str


class AnimeGenreFilter(Enum):
    """Catálogo común de géneros.

    Un proveedor cuyo sitio use slugs distintos es responsable de traducirlos
    internamente; quien consume la API nunca ve los slugs propios de cada sitio.
    """
    ACCIÓN = "accion"
    ARTES_MARCIALES = "artes-marciales"
    AVENTURA = "aventura"
    CARRERAS = "carreras"
    CIENCIA_FICCIÓN = "ciencia-ficcion"
    COMEDIA = "comedia"
    DEMENCIA = "demencia"
    DEMONIOS = "demonios"
    DEPORTES = "deportes"
    DRAMA = "drama"
    ECCHI = "ecchi"
    ESCOLARES = "escolares"
    ESPACIAL = "espacial"
    FANTASÍA = "fantasia"
    HAREM = "harem"
    HISTÓRICO = "historico"
    INFANTIL = "infantil"
    JOSEI = "josei"
    JUEGOS = "juegos"
    MAGIA = "magia"
    MECHA = "mecha"
    MILITAR = "militar"
    MISTERIO = "misterio"
    MÚSICA = "musica"
    PARODIA = "parodia"
    POLICÍA = "policia"
    PSICOLÓGICO = "psicologico"
    RECUENTOS_DE_LA_VIDA = "recuentos-de-la-vida"
    ROMANCE = "romance"
    SAMURAI = "samurai"
    SEINEN = "seinen"
    SHOUJO = "shoujo"
    SHOUNEN = "shounen"
    SOBRENATURAL = "sobrenatural"
    SUPERPODERES = "superpoderes"
    SUSPENSO = "suspenso"
    TERROR = "terror"
    VAMPIROS = "vampiros"
    YAOI = "yaoi"
    YURI = "yuri"


class AnimeOrderFilter(Enum):
    POR_DEFECTO = "default"
    ALFABÉTICAMENTE = "title"
    CALIFICACIÓN = "rating"


@dataclass
class ServerInfo:
    server: str
    url: str


@dataclass
class EpisodeInfo:
    id: Union[str, int]
    anime: str


@dataclass
class AnimeInfo:
    id: Union[str, int]
    title: str
    poster: str
    synopsis: Optional[str] = None
    genres: Optional[List[str]] = None
    episodes: Optional[List[EpisodeInfo]] = None
    provider_id: Optional[AnimeProviderId] = None