"""
Estructuras de datos comunes que devuelven todos los proveedores de anime.
Ningún proveedor debe redefinir estas clases: se importan siempre desde aquí.
"""
__author__ = "Jose David Escribano Orts"
__subsystem__ = "APIs.models"
__module__ = "models.py"
__version__ = "0.3"
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
    short_name: str


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


class AnimeFormat(Enum):
    """Formato de emisión de un anime.

    Los textos que ve el usuario («Serie», «Película»…) son cosa de la interfaz.
    """
    SERIES = "series"
    MOVIE = "movie"
    OVA = "ova"
    SPECIAL = "special"
    ONA = "ona"


class AnimeRelationType(Enum):
    """Relación de un anime con otro de su franquicia.

    Solo cuatro a propósito: cualquier otro tipo que dé un sitio (adicional,
    derivado, resumen…) lo traduce el proveedor a OTHER.
    """
    PREQUEL = "prequel"
    SEQUEL = "sequel"
    ALTERNATIVE = "alternative"
    OTHER = "other"


@dataclass
class RelatedAnime:
    """Anime relacionado con otro, tal como lo anuncia la ficha de este último.

    format, year y poster valen None cuando el proveedor no los da en la relación.
    """
    id: Union[str, int]
    title: str
    relation: AnimeRelationType
    format: Optional[AnimeFormat] = None
    year: Optional[int] = None
    poster: Optional[str] = None


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
    """Anime tal como lo sirve un proveedor.

    related vale [] si el anime no tiene relacionados y None si el proveedor no
    sabe darlos: la interfaz distingue «no tiene» de «no lo sé».
    """
    id: Union[str, int]
    title: str
    poster: str
    synopsis: Optional[str] = None
    genres: Optional[List[str]] = None
    episodes: Optional[List[EpisodeInfo]] = None
    provider_id: Optional[AnimeProviderId] = None
    format: Optional[AnimeFormat] = None
    related: Optional[List[RelatedAnime]] = None