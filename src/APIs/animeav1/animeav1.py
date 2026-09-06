"""
animeav1.com está construido con SvelteKit: los datos de la página vienen
incrustados como un objeto JS dentro de un <script> con `kit.start(app, element, {`,
no como HTML navegable por selectores. Se extraen con regex, con fallback al DOM.
"""
__author__ = "Jose David Escribano Orts"
__subsystem__ = "APIs.animeav1"
__module__ = "animeav1.py"
__version__ = "0.4"
__info__ = {"subsystem": __subsystem__, "module_name": __module__, "version": __version__}

import re
import time

import requests

from typing import List, Optional, Union, Tuple
from bs4 import BeautifulSoup
from urllib.parse import urlencode, urlparse, parse_qs

from utils.utils import removeprefix
from APIs.common.animeProviderMgr import AnimeProvider
from APIs.common.models import AnimeGenreFilter, AnimeOrderFilter, AnimeProviderId, ServerInfo, EpisodeInfo, AnimeInfo

BASE_URL = "https://animeav1.com"
CATALOG_URL = f"{BASE_URL}/catalogo"
MEDIA_URL = f"{BASE_URL}/media"

# Fragmento que identifica el <script> de hidratación de SvelteKit con los datos de la página.
_SVELTE_PAYLOAD_MARKER = "kit.start(app, element, {"


def _fetch(url: str, **kwargs) -> requests.Response:
    """Descarga una página de animeav1.com forzando UTF-8 si el servidor no declara charset.

    :param url: URL a descargar.
    :param kwargs: Argumentos adicionales para requests.get.
    :return: Respuesta HTTP con response.text ya en UTF-8.
    """
    response = requests.get(url, **kwargs)
    if "charset" not in response.headers.get("Content-Type", "").lower():
        response.encoding = "utf-8"
    return response


class AnimeAV1(AnimeProvider):

    PROVIDER_ID = AnimeProviderId.ANIMEAV1
    PROVIDER_NAME = "AnimeAV1"
    BASE_URL = BASE_URL

    def search_animes_by_genres_and_order(self, genres: List[AnimeGenreFilter], order: str = None,
                                          page: int = None) -> Tuple[List[AnimeInfo], int]:
        """Busca animes en animeav1.com filtrando por género y orden.

        :param genres: Lista de géneros por los que filtrar.
        :param order: Valor de AnimeOrderFilter.
        :param page: Página del listado a consultar.
        :return: Tupla (lista de animes, última página).
        """
        genre_values = [genre.value for genre in genres]

        query_pairs = [("genre", genre) for genre in genre_values]
        if page is not None:
            query_pairs.append(("page", page))
        query_string = urlencode(query_pairs)

        url = f"{CATALOG_URL}?{query_string}" if query_string else CATALOG_URL
        response = _fetch(url)
        soup = BeautifulSoup(response.text, "html.parser")

        query_animes = self.__parse_anime_cards(soup)
        last_page = self.__get_last_page(soup)
        query_animes = self.__apply_client_side_order(query_animes, order)

        return query_animes, last_page

    def search_animes_by_query(self, query: str = None, page: int = None) -> Tuple[List[AnimeInfo], int]:
        """Busca en animeav1.com por texto libre.

        :param query: Texto de búsqueda.
        :param page: Página de la búsqueda a devolver.
        :return: Tupla (lista de animes, última página).
        """
        if page is not None and not isinstance(page, int):
            raise TypeError

        params = dict()
        if query is not None:
            params["search"] = query
        if page is not None:
            params["page"] = page
        params = urlencode(params)

        url = CATALOG_URL
        if params != "":
            url += f"?{params}"

        response = _fetch(url)
        soup = BeautifulSoup(response.text, "html.parser")

        query_animes = self.__parse_anime_cards(soup)
        last_page = self.__get_last_page(soup)

        return query_animes, last_page

    def get_anime_episode_servers(self, anime_id: str, episode_id: int) -> List[ServerInfo]:
        """Obtiene la lista de servidores de vídeo (subtitulado) de un episodio.

        :param anime_id: Identificador (slug) del anime.
        :param episode_id: Número del episodio.
        :return: Lista de servidores disponibles.
        """
        try:
            response = _fetch(f"{MEDIA_URL}/{anime_id}/{episode_id}", timeout=10)
            response.raise_for_status()
        except requests.RequestException as exc:
            print(f"Error al obtener los servidores del episodio {episode_id} de {anime_id}: {exc}")
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        payload = self.__extract_svelte_payload(soup)
        if payload is None:
            return []

        # Los servidores de embed en subtitulado vienen como: embeds: { ..., SUB: [ {...}, {...} ] }
        embeds_match = re.search(r"embeds:\s*.*?SUB:\s*(\[.*?\])", payload, re.DOTALL)
        if embeds_match is None:
            return []

        servers: List[ServerInfo] = []
        for entry in embeds_match.group(1).split("},"):
            server_match = re.search(r'server:\s*"(.*?)"', entry)
            url_match = re.search(r'url:\s*"(.*?)"', entry)
            if server_match and url_match:
                servers.append(ServerInfo(server=server_match.group(1), url=url_match.group(1)))

        return servers

    def get_recent_animes(self) -> List[AnimeInfo]:
        """:return: Animes recientemente añadidos a animeav1.com, según la portada."""
        try:
            response = _fetch(BASE_URL, timeout=10)
            response.raise_for_status()
        except Exception:
            print(f"Error al conectarse a {BASE_URL} para obtener los animes recientes")
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        return self.__parse_anime_cards(soup)

    def get_anime_info(self, anime_id: Union[str, int]) -> AnimeInfo | None:
        """Obtiene la ficha completa de un anime, con reintentos ante fallos de red.

        :param anime_id: Identificador (slug) del anime.
        :return: Ficha del anime, o None si fallan todos los intentos.
        """
        attempt = 0
        max_attempts = 3
        while attempt < max_attempts:
            try:
                response = _fetch(f"{MEDIA_URL}/{anime_id}", timeout=5)
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
        """Localiza el <script> de hidratación de SvelteKit y extrae su payload de datos."""
        for script in soup.find_all("script"):
            content = script.string or script.get_text() or ""
            if _SVELTE_PAYLOAD_MARKER in content:
                match = re.search(r"data:(.+\]),", content, re.DOTALL)
                if match:
                    return match.group(1)
        return None

    @staticmethod
    def __parse_anime_cards(soup: BeautifulSoup) -> List[AnimeInfo]:
        """Parsea las tarjetas de anime del catálogo, búsqueda o portada.

        Descarta cualquier tarjeta cuyo enlace apunte a un episodio concreto
        en vez de a la ficha del anime.
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
    def __get_last_page(soup: BeautifulSoup) -> int:
        """Calcula la última página a partir de los enlaces de paginación (?page=N)."""
        last_page = 1
        for link in soup.select("a[href*='page=']"):
            match = re.search(r"[?&]page=(\d+)", link.get("href", ""))
            if match:
                last_page = max(last_page, int(match.group(1)))
        return last_page

    @staticmethod
    def __extract_genres(soup: BeautifulSoup) -> List[str]:
        """Extrae los slugs de género de los enlaces de género de la ficha del anime."""
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
        """Cuenta episodios a partir de los enlaces /media/{anime_id}/{n} de la ficha.

        Fallback usado cuando el payload de SvelteKit no trae 'episodesCount'.
        """
        episode_pattern = re.compile(rf"/media/{re.escape(str(anime_id))}/(\d+)$")
        episode_numbers = set()
        for link in soup.select(f"a[href*='/media/{anime_id}/']"):
            match = episode_pattern.search(urlparse(link.get("href", "")).path)
            if match:
                episode_numbers.add(int(match.group(1)))
        return max(episode_numbers) if episode_numbers else 0

    @staticmethod
    def __apply_client_side_order(animes: List[AnimeInfo], order: str) -> List[AnimeInfo]:
        """Ordena en el cliente la lista de animes, ya que el sitio no lo hace por sí mismo.

        :param animes: Animes a ordenar.
        :param order: Valor de AnimeOrderFilter.
        :return: Lista ordenada (o sin cambios si el orden no está soportado).
        """
        if order == AnimeOrderFilter.ALFABÉTICAMENTE.value:
            return sorted(animes, key=lambda anime: anime.title.lower())
        if order == AnimeOrderFilter.CALIFICACIÓN.value:
            # AnimeAV1 no incluye la puntuación en las tarjetas del listado, por lo
            # que no se puede ordenar por calificación sin pedir cada ficha individual.
            print("Aviso: AnimeAV1 no permite ordenar por calificación en el listado; "
                  "se devuelve el orden por defecto del sitio.")
            return animes
        return animes


class AnimeAV1Singleton:
    __instance = None

    def __new__(cls):
        if AnimeAV1Singleton.__instance is None:
            AnimeAV1Singleton.__instance = AnimeAV1()
        return AnimeAV1Singleton.__instance