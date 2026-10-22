"""
player.zilla-networks.com: el servidor «HLS» de AnimeAV1.

La receta es sintáctica, sin pedir la página del embed: `play/<hash>` pasa a
`m3u8/<hash>`. El playlist es abierto, pero los segmentos dan 403 salvo que la
petición lleve `Sec-Fetch-Site: same-origin`, exactamente con ese valor.
"""
__author__ = "Jose David Escribano Orts"
__subsystem__ = "APIs.resolvers"
__module__ = "zilla.py"
__version__ = "0.1"
__info__ = {"subsystem": __subsystem__, "module_name": __module__, "version": __version__}

import re

from typing import Optional
from urllib.parse import urlparse

from APIs.resolvers.base import MediaSource, Resolver, url_host

ZILLA_HOST = "player.zilla-networks.com"
M3U8_URL = f"https://{ZILLA_HOST}/m3u8"

_HASH_PATTERN = re.compile(r"[0-9a-fA-F]{32}")


class ZillaResolver(Resolver):

    def matches(self, url: str) -> bool:
        """:return: True si la URL es de player.zilla-networks.com."""
        return url_host(url) == ZILLA_HOST

    def resolve(self, url: str) -> Optional[MediaSource]:
        """Convierte la URL `play/<hash>` del embed en la del playlist HLS.

        :param url: URL de embed de zilla.
        :return: Playlist HLS con la cabecera que exigen sus segmentos, o None si la URL no trae el hash.
        """
        try:
            parts = [part for part in urlparse(url).path.split("/") if part]
        except ValueError:
            return None

        # El propio reproductor del sitio rechaza cualquier hash que no mida 32.
        if len(parts) < 2 or parts[-2] != "play" or not _HASH_PATTERN.fullmatch(parts[-1]):
            print(f"[zilla] URL de embed sin hash reconocible: {url}")
            return None

        return MediaSource(
            url=f"{M3U8_URL}/{parts[-1]}",
            headers={"Sec-Fetch-Site": "same-origin"},
            kind="hls",
            expires_at=None,
        )
