"""
Registro de resolutores: el único punto de entrada de la capa de resolución.

Sin caché a propósito: varias URLs de medio caducan en horas y otras quedan
atadas a la IP del cliente, así que se resuelve cada vez que se va a reproducir.
"""
__author__ = "Jose David Escribano Orts"
__subsystem__ = "APIs.resolvers"
__module__ = "registry.py"
__version__ = "0.1"
__info__ = {"subsystem": __subsystem__, "module_name": __module__, "version": __version__}

from typing import List, Optional

from APIs.resolvers.base import MediaSource, Resolver
from APIs.resolvers.jkplayer import JKPlayerResolver
from APIs.resolvers.mp4upload import MP4UploadResolver
from APIs.resolvers.zilla import ZillaResolver

_RESOLVERS: List[Resolver] = [
    ZillaResolver(),
    JKPlayerResolver(),
    MP4UploadResolver(),
]


def _resolver_for(url: str) -> Optional[Resolver]:
    """:return: El primer resolutor que acepta la URL, o None si ninguno."""
    if not url:
        return None
    for resolver in _RESOLVERS:
        try:
            if resolver.matches(url):
                return resolver
        except Exception as exc:
            print(f"[resolvers] {type(resolver).__name__}.matches() falló con {url}: {exc}")
    return None


def has_resolver(url: str) -> bool:
    """Dice, sin hacer ninguna petición, si algún resolutor sabe tratar la URL.

    Es una promesa a priori: un servidor con resolutor puede acabar igualmente en el navegador.
    :param url: URL de embed del servidor.
    :return: True si hay un resolutor para su hoster.
    """
    return _resolver_for(url) is not None


def resolve(url: str) -> Optional[MediaSource]:
    """Resuelve la URL de embed con el resolutor de su hoster.

    :param url: URL de embed del servidor.
    :return: Medio reproducible, o None si no hay resolutor o el suyo no pudo resolverla.
    """
    resolver = _resolver_for(url)
    if resolver is None:
        return None
    try:
        return resolver.resolve(url)
    except Exception as exc:
        print(f"[resolvers] {type(resolver).__name__} lanzó al resolver {url}: {exc}")
        return None
