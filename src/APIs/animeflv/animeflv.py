__author__ = "Jose David Escribano Orts"
__subsystem__ = "APIs.animeflv"
__module__ = "animeflv.py"
__version__ = "0.3"
__info__ = {"subsystem": __subsystem__, "module_name": __module__, "version": __version__}

import time

import requests
import json

from typing import List, Union, Tuple
from bs4 import BeautifulSoup
from urllib.parse import urlencode

from utils.utils import removeprefix
from APIs.common.animeProviderMgr import AnimeProvider
from APIs.common.models import AnimeGenreFilter, AnimeProviderId, ServerInfo, EpisodeInfo, AnimeInfo


BASE_URL = "https://www3.animeflv.net"
BROWSE_URL = f"{BASE_URL}/browse"
ANIME_VIDEO_URL = f"{BASE_URL}/ver/"
ANIME_URL = f"{BASE_URL}/anime"


class AnimeFLV(AnimeProvider):

    PROVIDER_ID = AnimeProviderId.ANIMEFLV
    PROVIDER_NAME = "AnimeFLV"
    BASE_URL = BASE_URL

    def search_animes_by_genres_and_order(self, genres: List[AnimeGenreFilter], order: str = None,
                                          page: int = None) -> Tuple[List[AnimeInfo], int]:
        """Busca animes en animeflv.net filtrando por género y orden.

        :param genres: Lista de géneros por los que filtrar.
        :param order: Valor de AnimeOrderFilter.
        :param page: Página del listado a consultar.
        :return: Tupla (lista de animes, última página).
        """
        genre_values = [genre.value for genre in genres]

        query_string = urlencode([("genre[]", genre) for genre in genre_values])
        order_param = f"&order={order}" if order is not None else ""
        page_param = f"&page={page}" if page is not None else ""
        url = f"{BROWSE_URL}?{query_string}{order_param}{page_param}"
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")

        pages = soup.select("div.Container div.NvCnAnm ul.pagination li")
        elements = soup.select("div.Container ul.ListAnimes li article")

        if elements is None:
            print("Unable to get list of animes")
            return [], 0

        last_page = 1
        if pages is not None:
            for page in pages:
                link = page.find("a")
                if link and link.text.isdigit():
                    last_page = int(link.text)

        query_animes: List[AnimeInfo] = []
        for element in elements:
            query_animes.append(
                AnimeInfo(
                    id=removeprefix(element.select_one("div.Description a.Button")["href"][1:], "anime/"),
                    title=element.select_one("div.Title").string,
                    poster=f"{element.select_one('div.Image figure img').get('src', '')}",
                )
            )
        return query_animes, last_page

    def search_animes_by_query(self, query: str = None, page: int = None) -> Tuple[List[AnimeInfo], int]:
        """Busca en animeflv.net por texto libre.

        :param query: Texto de búsqueda.
        :param page: Página de la búsqueda a devolver.
        :return: Tupla (lista de animes, última página).
        """
        if page is not None and not isinstance(page, int):
            raise TypeError

        params = dict()
        if query is not None:
            params["q"] = query
        if page is not None:
            params["page"] = page
        params = urlencode(params)

        url = f"{BROWSE_URL}"
        if params != "":
            url += f"?{params}"

        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")

        pages = soup.select("div.Container div.NvCnAnm ul.pagination li")
        elements = soup.select("div.Container ul.ListAnimes li article")

        if elements is None:
            print("Unable to get list of animes")
            return [], 0

        last_page = 1
        if pages is not None:
            for page in pages:
                link = page.find("a")
                if link and link.text.isdigit():
                    last_page = int(link.text)
        query_animes: List[AnimeInfo] = []
        for element in elements:
            query_animes.append(
                AnimeInfo(
                    id=removeprefix(element.select_one("div.Description a.Button")["href"][1:], "anime/"),
                    title=element.select_one("div.Title").string,
                    poster=f"{element.select_one('div.Image figure img').get('src', '')}",
                )
            )
        return query_animes, last_page

    def get_anime_episode_servers(self, anime_id: str, episode_id: int) -> List[ServerInfo]:
        """Obtiene la lista de servidores de vídeo de un episodio de un anime.

        :param anime_id: Identificador del anime.
        :param episode_id: Número del episodio.
        :return: Lista de servidores disponibles.
        """
        response = requests.get(f"{ANIME_VIDEO_URL}{anime_id}-{episode_id}")
        soup = BeautifulSoup(response.text, "html.parser")
        scripts = soup.find_all("script")

        servers = []

        for script in scripts:
            content = str(script)
            if "var videos = {" in content:
                videos = content.split("var videos = ")[1].split(";")[0]
                servers_subtitle = json.loads(videos)["SUB"]
                servers = [
                    ServerInfo(
                        server=server_data.get('title'),
                        url=server_data.get('code') or server_data.get('url')
                    )
                    for server_data in servers_subtitle
                ]

        return servers

    def get_recent_animes(self) -> List[AnimeInfo]:
        """:return: Animes recientemente añadidos a animeflv.net."""
        try:
            response = requests.get(BASE_URL, timeout=10)
            response.raise_for_status()
        except Exception as e:
            print(f"Error al conectarse a {BASE_URL} para obtener los animes recientes")
            return []
        soup = BeautifulSoup(response.text, "html.parser")

        elements = soup.select("ul.ListAnimes li article")

        if elements is None:
            print("Unable to get list of animes")
            return []
        recent_animes: List[AnimeInfo] = []
        for element in elements:
            recent_animes.append(
                AnimeInfo(
                    id=removeprefix(element.select_one("div.Description a.Button")["href"][1:], "anime/"),
                    title=element.select_one("div.Title").string,
                    poster=f"{BASE_URL}{element.select_one('div.Image figure img').get('src', '')}",
                )
            )
        return recent_animes

    def get_anime_info(self, anime_id: Union[str, int]) -> AnimeInfo | None:
        """Obtiene la ficha completa de un anime, con reintentos ante fallos de red.

        :param anime_id: Identificador del anime.
        :return: Ficha del anime, o None si fallan todos los intentos.
        """
        attempt = 0
        max_attemts = 3
        while attempt < max_attemts:
            try:
                response = requests.get(f"{ANIME_URL}/{anime_id}", timeout=2)
                response.raise_for_status()

                soup = BeautifulSoup(response.text, "html.parser")

                information = {
                    "title": soup.select_one("div.Container h1.Title").string,
                    "poster": f"{BASE_URL}{soup.select_one('div.Image figure img').get('src', '')}",
                    "synopsis": soup.select_one("div.Description p").string,
                }

                genres = [
                    element["href"].split("=")[1]
                    for element in soup.select("main.Main section.WdgtCn nav.Nvgnrs a")
                    if "=" in element["href"]
                ]

                info_ids = []
                episodes_data = []
                episodes = []

                try:
                    for script in soup.find_all("script"):
                        contents = str(script)
                        if "var anime_info = [" in contents or "var episodes = [" in contents:
                            anime_info = contents.split("var anime_info = ")[1].split("\r")[0].strip(";")
                            info_ids.append(json.loads(anime_info))

                            episode_info = contents.split("var episodes = ")[1].split(";")[0]
                            episodes_data.extend(json.loads(episode_info))
                            break

                    for episode, _ in episodes_data:
                        episodes.append(EpisodeInfo(id=episode, anime=str(anime_id)))

                except Exception as exc:
                    print(f"Error al obtener los episodios de {anime_id}: {exc}")

                return AnimeInfo(id=anime_id, episodes=episodes, genres=genres, **information)

            except requests.RequestException as e:
                print(f"Intento {attempt + 1}/{max_attemts} fallido para el anime {anime_id}: {e}")
                attempt += 1
                time.sleep(1)

        print(f"No se pudo obtener la información del anime {anime_id}")
        return None


class AnimeFLVSingleton:
    __instance = None

    def __new__(cls):
        if AnimeFLVSingleton.__instance is None:
            AnimeFLVSingleton.__instance = AnimeFLV()
        return AnimeFLVSingleton.__instance