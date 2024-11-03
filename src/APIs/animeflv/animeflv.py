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


BASE_URL = "https://www3.animeflv.net"
BROWSE_URL = f"{BASE_URL}/browse"
ANIME_VIDEO_URL = f"{BASE_URL}/ver/"
ANIME_URL = f"{BASE_URL}/anime"

class AnimeGenreFilter(Enum):
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


class AnimeFLV:

    def search_animes_by_genres_and_order(self, genres: List[AnimeGenreFilter], order: str = None,
                                          page: int = None) -> List[AnimeInfo]:
        genre_values = [genre.value for genre in genres]

        # Generar la query string
        query_string = urlencode([("genre[]", genre) for genre in genre_values])
        order_param = f"&order={order}" if order is not None else ""
        page_param = f"&page={page}" if page is not None else ""
        url = f"{BROWSE_URL}?{query_string}{order_param}{page_param}"
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")

        elements = soup.select("div.Container ul.ListAnimes li article")

        if elements is None:
            print("Unable to get list of animes")
            return []

        return self.__process_anime_list_info(elements)

    def search_animes_by_query(self, query: str = None, page: int = None) -> List[AnimeInfo]:
        """
        Search in animeflv.net by query.
        :param query: Query information like: 'Nanatsu no Taizai'.
        :param page: Page of the information return.
        :rtype: list[AnimeInfo]
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

        elements = soup.select("div.Container ul.ListAnimes li article")

        if elements is None:
            print("Unable to get list of animes")
            return []

        return self.__process_anime_list_info(elements)

    def get_anime_episode_servers(self, anime_id: str, episode_id: int) -> List[ServerInfo]:
        """
        Obtiene una lista de servidores de los videos del episodio solicitado para un anime dado.

        :param anime_id: Identificador del anime, como por ejemplo 'one-piece-tv'.
        :param episode_id: Identificador del episodio del anime, como por ejemplo 1.
        :rtype: List[ServerInfo]
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
        """
        Obtiene lista de los últimos animes añadidos

        :rtype: List[AnimeInfo]
        """
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

    def get_anime_info(self, anime_id: Union[str, int]) -> AnimeInfo:
        """
        Obtiene información sobre un anime específico.

        :param anime_id: Identificador del anime, como por ejemplo 'one-piece-tv'.
        :rtype: AnimeInfo
        """
        attempt = 0
        max_attemts = 3
        while attempt < max_attemts:
            try:
                response = requests.get(f"{ANIME_URL}/{anime_id}", timeout=2)
                response.raise_for_status()  # Lanza excepción si la respuesta no es exitosa (status code 4xx o 5xx)

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
                            anime_info = contents.split("var anime_info = ")[1].split(";")[0]
                            info_ids.append(json.loads(anime_info))

                            episode_info = contents.split("var episodes = ")[1].split(";")[0]
                            episodes_data.extend(json.loads(episode_info))
                            break

                    for episode, _ in episodes_data:
                        episodes.append(EpisodeInfo(id=episode, anime=anime_id))

                except Exception as exc:
                    print(f"Error al los episodios de {anime_id}: {exc}")

                return AnimeInfo(id=anime_id, episodes=episodes, genres=genres, **information)

            except requests.RequestException as e:
                print(f"Intento {attempt + 1}/{max_attemts} fallido para el anime {anime_id}: {e}")
                attempt += 1
                time.sleep(1)  # Espera un segundo entre intentos para evitar sobrecargar el servidor

        print(f"No se pudo obtener la información del anime {anime_id}")
        return None

    def __process_anime_list_info(self, elements: ResultSet) -> List[AnimeInfo]:
        ret: List[AnimeInfo] = []

        for element in elements:
            try:
                anime_id = removeprefix(element.select_one("div.Description a.Button")["href"][1:], "anime/")
                anime_info = self.get_anime_info(anime_id)
                if anime_info is None:
                    continue
                ret.append(anime_info)
            except requests.RequestException as exc:
                print(f"Error al obtener información del anime {anime_id}: {exc}")
                continue

        return ret


class AnimeFLVSingleton:
    __instance = None

    def __new__(cls):
        if AnimeFLVSingleton.__instance is None:
            AnimeFLVSingleton.__instance = AnimeFLV()
        return AnimeFLVSingleton.__instance