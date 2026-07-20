"""
Este módulo es la ÚNICA fuente de verdad para las estructuras de datos que devuelven todos los proveedores de anime
(AnimeFLV, AnimeAV1 y los que vengan después: MonosChinos2, TioAnime, JKAnime...). Ningún proveedor debe redefinir
estas clases: se importan desde aquí para garantizar que main_window.py, losbotones de la sidebar, etc. reciban siempre
el mismo tipo de objeto sin importar de qué web viene el dato.
"""
__author__ = "Jose David Escribano Orts"
__subsystem__ = "APIs.models"
__module__ = "models.py"
__version__ = "0.1"
__info__ = {"subsystem": __subsystem__, "module_name": __module__, "version": __version__}

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Union


class AnimeGenreFilter(Enum):
    """
    Catálogo común de géneros. Un proveedor concreto puede usar slugs distintos
    en su propia web (p.ej. 'action' en vez de 'accion'); en ese caso, el
    proveedor es responsable de traducir estos valores a los suyos internamente
    (ver AnimeProvider para más detalle), de forma que quien consuma la API
    nunca tenga que conocer los slugs específicos de cada sitio.
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