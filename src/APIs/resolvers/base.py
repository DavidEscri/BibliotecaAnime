"""
Tipos comunes de la capa de resolución: de la URL de embed de un servidor a la
URL del medio que un reproductor puede abrir, con las cabeceras que exige.

La resolución se indexa por dominio del hoster, no por proveedor: un mismo
hoster lo embeben varios sitios. Las cabeceras son propias de cada hoster y no
hay valores por defecto comunes, porque lo que uno exige otro lo rechaza.
"""
__author__ = "Jose David Escribano Orts"
__subsystem__ = "APIs.resolvers"
__module__ = "base.py"
__version__ = "0.1"
__info__ = {"subsystem": __subsystem__, "module_name": __module__, "version": __version__}

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import urlparse

BROWSER_USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

REQUEST_TIMEOUT = 10


@dataclass
class MediaSource:
    """Medio reproducible ya resuelto.

    `headers` son las que hay que mandar en cada petición del medio, playlist y
    segmentos incluidos; `expires_at` es un epoch, o None si la URL no declara
    caducidad. Ninguna se cachea: hay URLs atadas a la IP o a una sesión.
    """
    url: str
    headers: dict[str, str] = field(default_factory=dict)
    kind: str = "mp4"
    expires_at: Optional[float] = None


class Resolver(ABC):
    """Resolutor de un hoster concreto."""

    @abstractmethod
    def matches(self, url: str) -> bool:
        """Dice, sin hacer ninguna petición, si la URL es de este hoster.

        :param url: URL de embed del servidor.
        :return: True si este resolutor sabe tratarla.
        """

    @abstractmethod
    def resolve(self, url: str) -> Optional[MediaSource]:
        """Obtiene el medio reproducible de una URL de embed.

        Nunca lanza: cualquier fallo devuelve None, que es lo que permite caer al navegador.
        :param url: URL de embed del servidor.
        :return: Medio resuelto, o None si no se pudo resolver.
        """


def url_host(url: str) -> str:
    """:return: Host de la URL en minúsculas y sin `www.`, o cadena vacía si no se puede leer."""
    try:
        host = (urlparse(url).hostname or "").lower()
    except ValueError:
        return ""
    return host[4:] if host.startswith("www.") else host
