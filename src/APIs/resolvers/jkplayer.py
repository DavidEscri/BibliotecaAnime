"""
Reproductores propios de JKAnime, servidos bajo jkanime.net/jkplayer/.

Hay dos familias en el mismo dominio y se comportan distinto: `um` y `umv`
(«Desu» y «Magi», que son el mismo stream) devuelven un HLS cuya URL caduca y
aparece dos veces en la página, en claro y dentro de un `atob()`; `jk` apunta a
un MP4 de jkplayers.com atado a la IP del cliente.
"""
__author__ = "Jose David Escribano Orts"
__subsystem__ = "APIs.resolvers"
__module__ = "jkplayer.py"
__version__ = "0.1"
__info__ = {"subsystem": __subsystem__, "module_name": __module__, "version": __version__}

import base64
import binascii
import re

import requests

from typing import Optional
from urllib.parse import parse_qs, urlparse

from APIs.resolvers.base import BROWSER_USER_AGENT, REQUEST_TIMEOUT, MediaSource, Resolver, url_host

JKANIME_HOST = "jkanime.net"
JKANIME_BASE_URL = f"https://{JKANIME_HOST}"

_HLS_PLAYERS = {"um", "umv"}
_MP4_PLAYERS = {"jk"}

_M3U8_PATTERN = re.compile(r"https?://[^\s'\"<>]+?\.m3u8[^\s'\"<>]*")
_ATOB_PATTERN = re.compile(r"atob\(\s*['\"]([A-Za-z0-9+/=]+)['\"]\s*\)")
_MP4_URL_PATTERN = re.compile(r"url:\s*['\"](https?://[^'\"]+)['\"]")


class JKPlayerResolver(Resolver):

    def matches(self, url: str) -> bool:
        """:return: True si la URL es de un reproductor `um`, `umv` o `jk` de jkanime.net."""
        return url_host(url) == JKANIME_HOST and self.__player_name(url) in _HLS_PLAYERS | _MP4_PLAYERS

    def resolve(self, url: str) -> Optional[MediaSource]:
        """Descarga la página del reproductor y extrae de ella la URL del medio.

        :param url: URL `https://jkanime.net/jkplayer/<um|umv|jk>?...`.
        :return: HLS para `um`/`umv`, MP4 para `jk`, o None si la página no la trae.
        """
        player = self.__player_name(url)
        try:
            response = requests.get(url, headers={"User-Agent": BROWSER_USER_AGENT,
                                                  "Referer": f"{JKANIME_BASE_URL}/"},
                                    timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
        except requests.RequestException as exc:
            print(f"[jkplayer] No se pudo descargar el reproductor {player}: {exc}")
            return None

        html = response.text
        if player in _HLS_PLAYERS:
            media_url = self.__find_hls_url(html)
            if media_url is None:
                print(f"[jkplayer] El reproductor {player} no trae ninguna URL .m3u8")
                return None
            return MediaSource(url=media_url, headers={}, kind="hls",
                               expires_at=self.__expiry(media_url))

        match = _MP4_URL_PATTERN.search(html)
        if match is None:
            print("[jkplayer] El reproductor jk no trae la URL del vídeo")
            return None
        media_url = match.group(1)
        # jkplayers.com responde 410 Gone si la petición lleva Referer: las cabeceras
        # tienen que ir vacías, sin ningún Referer «por si acaso».
        return MediaSource(url=media_url, headers={}, kind="mp4",
                           expires_at=self.__expiry(media_url))

    @staticmethod
    def __player_name(url: str) -> str:
        """:return: Nombre del reproductor (`um`, `umv`, `jk`…) o cadena vacía si no es una ruta /jkplayer/."""
        try:
            parts = [part for part in urlparse(url).path.split("/") if part]
        except ValueError:
            return ""
        return parts[1].lower() if len(parts) == 2 and parts[0] == "jkplayer" else ""

    @staticmethod
    def __find_hls_url(html: str) -> Optional[str]:
        """Busca el .m3u8 en claro y, si no aparece, dentro de los `atob()` de la página.

        :param html: Página del reproductor.
        :return: URL del playlist, o None si no está por ninguno de los dos caminos.
        """
        match = _M3U8_PATTERN.search(html)
        if match:
            return match.group(0)

        for encoded in _ATOB_PATTERN.findall(html):
            try:
                decoded = base64.b64decode(encoded).decode("utf-8")
            except (binascii.Error, UnicodeDecodeError):
                continue
            match = _M3U8_PATTERN.fullmatch(decoded.strip())
            if match:
                return match.group(0)
        return None

    @staticmethod
    def __expiry(media_url: str) -> Optional[float]:
        """:return: Caducidad del parámetro `e=` de la URL como epoch, o None si no lo lleva."""
        try:
            value = parse_qs(urlparse(media_url).query).get("e", [None])[0]
            return float(value) if value else None
        except ValueError:
            return None
