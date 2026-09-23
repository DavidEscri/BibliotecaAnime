"""
mp4upload.com: la alternativa MP4 al HLS de AnimeAV1.

La fuente viene en claro en la inicialización de video.js del embed
(`player.src({ type: "video/mp4", src: "…" })`); Rocket Loader de Cloudflare
renombra el `type` de los <script>, pero no ofusca su contenido. El medio se
sirve en el puerto 183 y exige el Referer del propio hoster, no el del sitio
que lo embebe.
"""
__author__ = "Jose David Escribano Orts"
__subsystem__ = "APIs.resolvers"
__module__ = "mp4upload.py"
__version__ = "0.1"
__info__ = {"subsystem": __subsystem__, "module_name": __module__, "version": __version__}

import re

import requests

from typing import Optional

from APIs.resolvers.base import BROWSER_USER_AGENT, REQUEST_TIMEOUT, MediaSource, Resolver, url_host

MP4UPLOAD_HOST = "mp4upload.com"
MP4UPLOAD_REFERER = f"https://www.{MP4UPLOAD_HOST}/"

_PLAYER_SRC_PATTERN = re.compile(r"player\.src\(\s*\{.*?src:\s*['\"](?P<url>https?://[^'\"]+)['\"]", re.DOTALL)
_VIDEO_URL_PATTERN = re.compile(r"(?P<url>https?://[\w.-]*mp4upload\.com(?::\d+)?/[^\s'\"<>]+\.mp4)")


class MP4UploadResolver(Resolver):

    def matches(self, url: str) -> bool:
        """:return: True si la URL es de mp4upload.com, con o sin `www.`."""
        return url_host(url) == MP4UPLOAD_HOST

    def resolve(self, url: str) -> Optional[MediaSource]:
        """Descarga el embed y extrae la URL del MP4 de la inicialización del reproductor.

        :param url: URL `https://www.mp4upload.com/embed-<id>.html`.
        :return: MP4 con el Referer del hoster, o None si el embed no la trae o no conecta.
        """
        try:
            response = requests.get(url, headers={"User-Agent": BROWSER_USER_AGENT},
                                    timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
        except requests.RequestException as exc:
            print(f"[mp4upload] No se pudo descargar el embed: {exc}")
            return None

        match = _PLAYER_SRC_PATTERN.search(response.text) or _VIDEO_URL_PATTERN.search(response.text)
        if match is None:
            print("[mp4upload] El embed no trae la URL del vídeo")
            return None

        # Con el Referer del sitio que lo embebe el medio responde 403; con el suyo, 206.
        # El token del path parece de sesión: no se da por válido más allá de esta reproducción.
        return MediaSource(
            url=match.group("url"),
            headers={"User-Agent": BROWSER_USER_AGENT, "Referer": MP4UPLOAD_REFERER},
            kind="mp4",
            expires_at=None,
        )
