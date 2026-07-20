__author__ = "Jose David Escribano Orts"
__subsystem__ = "animeflv"
__module__ = "animeflv.py"
__version__ = "0.1"
__info__ = {"subsystem": __subsystem__, "module_name": __module__, "version": __version__}

import time

import requests
import json

from typing import List, Optional, Union
from enum import Enum
from bs4 import BeautifulSoup, ResultSet
from urllib.parse import urlencode
from dataclasses import dataclass

from utils.utils import removeprefix


BASE_URL = "https://animeav1.com"
BROWSE_URL = f"{BASE_URL}/catalogo"
ANIME_VIDEO_URL = f"{BASE_URL}/media/"
ANIME_URL = f"{BASE_URL}/media"

@dataclass
class EpisodeInfo:
    id: int
    anime: str

@dataclass
class AnimeInfo:
    id: str
    title: str
    poster: str
    synopsis: Optional[str] = None
    genres: Optional[List[str]] = None
    episodes: Optional[List[EpisodeInfo]] = None

class AnimeAV1:

    def get_recent_animes(self) -> List[AnimeInfo]:
        """
        Obtiene la lista de los animes recientemente añadidos a animeav1.com (portada).

        :rtype: List[AnimeInfo]
        """
        try:
            response = requests.get(BASE_URL, timeout=10)
            response.raise_for_status()
        except Exception:
            print(f"Error al conectarse a {BASE_URL} para obtener los animes recientes")
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        return self.__parse_anime_cards(soup)

    def get_anime_info(self, anime_id: Union[str, int]) -> AnimeInfo | None:
        """
        Obtiene información sobre un anime específico.

        :param anime_id: Identificador (slug) del anime, como por ejemplo 'one-piece'.
        :rtype: AnimeInfo
        """
        attempt = 0
        max_attempts = 3
        while attempt < max_attempts:
            try:
                response = requests.get(f"{MEDIA_URL}/{anime_id}", timeout=5)
                response.raise_for_status()

                soup = BeautifulSoup(response.text, "html.parser")
                payload = self.__extract_svelte_payload(soup)

                title = None
                synopsis = None
                episodes_count = 0

                if payload is not None:
                    title_match = re.search(r'title:\s*"(.+?)",', payload)
                    synopsis_match = re.search(r'synopsis:\s*"(.*?)",', payload)
                    episodes_match = re.search(r'episodesCount:\s*(\d+),', payload)

                    if title_match:
                        title = title_match.group(1)
                    if synopsis_match:
                        synopsis = synopsis_match.group(1).replace('\\n', '\n').replace('\\"', '"')
                    if episodes_match:
                        episodes_count = int(episodes_match.group(1))

                # Fallbacks por si el payload cambia de formato entre despliegues del sitio
                if title is None:
                    title_el = soup.select_one("main h1")
                    title = title_el.get_text(strip=True) if title_el else str(anime_id)

                if synopsis is None:
                    synopsis_el = soup.select_one("main div.entry p") or soup.select_one("main article p")
                    synopsis = synopsis_el.get_text(strip=True) if synopsis_el else None

                cover_el = soup.select_one("main figure img")
                poster = cover_el.get("src", "") if cover_el is not None else ""

                genres = self.__extract_genres(soup)

                if episodes_count == 0:
                    episodes_count = self.__count_episodes_from_dom(soup, anime_id)

                episodes = [EpisodeInfo(id=i, anime=anime_id) for i in range(1, episodes_count + 1)]

                return AnimeInfo(
                    id=anime_id,
                    title=title,
                    poster=poster,
                    synopsis=synopsis,
                    genres=genres,
                    episodes=episodes,
                )

            except requests.RequestException as exc:
                print(f"Intento {attempt + 1}/{max_attempts} fallido para el anime {anime_id}: {exc}")
                attempt += 1
                time.sleep(1)

        print(f"No se pudo obtener la información del anime {anime_id}")
        return None

    # ------------------------------------------------------------------
    # Helpers privados de parseo
    # ------------------------------------------------------------------

    @staticmethod
    def __extract_svelte_payload(soup: BeautifulSoup) -> Optional[str]:
        """
        Localiza el <script> de hidratación de SvelteKit y devuelve el fragmento
        que contiene los datos de la página ('data: [...]').
        """
        for script in soup.find_all("script"):
            content = script.string or script.get_text() or ""
            if _SVELTE_PAYLOAD_MARKER in content:
                match = re.search(r"data:(.+\]),", content, re.DOTALL)
                if match:
                    return match.group(1)
        return None

    @staticmethod
    def __parse_anime_cards(soup: BeautifulSoup) -> List[AnimeInfo]:
        """
        Parsea las tarjetas de anime (<article>) presentes tanto en el catálogo/
        búsqueda como en la portada. Descarta cualquier tarjeta cuyo enlace apunte
        a un episodio concreto (/media/{slug}/{numero}) en vez de a la ficha del anime.
        """
        animes: List[AnimeInfo] = []
        seen_ids = set()

        for article in soup.select("main article"):
            link = article.select_one("a[href*='/media/']")
            if link is None:
                continue

            href = link.get("href", "")
            anime_id = removeprefix(urlparse(href).path, "/media/").strip("/")
            if not anime_id or "/" in anime_id or anime_id in seen_ids:
                continue

            title_el = article.select_one("h3")
            img_el = article.select_one("figure img")
            if title_el is None or img_el is None:
                continue

            seen_ids.add(anime_id)
            animes.append(
                AnimeInfo(
                    id=anime_id,
                    title=title_el.get_text(strip=True),
                    poster=img_el.get("src", ""),
                )
            )

        return animes

    @staticmethod
    def __extract_genres(soup: BeautifulSoup) -> List[str]:
        """
        Extrae los slugs de género (p.ej. 'accion', 'aventura') a partir de los
        enlaces de género de la ficha del anime, igual que hace animeflv.py.
        """
        genres: List[str] = []
        seen = set()
        for link in soup.select("main a[href*='genre=']"):
            parsed = urlparse(link.get("href", ""))
            values = parse_qs(parsed.query).get("genre")
            if not values:
                continue
            genre_slug = values[0]
            if genre_slug not in seen:
                seen.add(genre_slug)
                genres.append(genre_slug)
        return genres

    @staticmethod
    def __count_episodes_from_dom(soup: BeautifulSoup, anime_id: Union[str, int]) -> int:
        """
        Fallback: si no se pudo leer 'episodesCount' del payload de SvelteKit,
        cuenta los episodios a partir de los enlaces /media/{anime_id}/{n} listados
        en la propia ficha del anime.
        """
        episode_pattern = re.compile(rf"/media/{re.escape(str(anime_id))}/(\d+)$")
        episode_numbers = set()
        for link in soup.select(f"a[href*='/media/{anime_id}/']"):
            match = episode_pattern.search(urlparse(link.get("href", "")).path)
            if match:
                episode_numbers.add(int(match.group(1)))
        return max(episode_numbers) if episode_numbers else 0
class AnimeAV1Singleton:
    __instance = None

    def __new__(cls):
        if AnimeAV1Singleton.__instance is None:
            AnimeAV1Singleton.__instance = AnimeAV1()
        return AnimeAV1Singleton.__instance