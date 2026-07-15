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
        elements = soup.select("section.grid div.grid article.relative")

        if elements is None:
            print("Unable to get list of animes")
            return []
        recent_animes: List[AnimeInfo] = []
        for element in elements:
            try:
                recent_animes.append(
                    AnimeInfo(
                        id=removeprefix(element.select_one("a.absolute")["href"][1:], "media/"),
                        title=element.select_one("h3").string,
                        poster=element.select_one("div.relative figure.dark img")["src"]
                    )
                )
            except Exception as e:
                continue
        return recent_animes

    def get_anime_info(self, anime_id: Union[str, int]) -> AnimeInfo:
        attempt = 0
        max_attemts = 3
        while attempt < max_attemts:
            try:
                response = requests.get(f"{ANIME_URL}/{anime_id}", timeout=2)
                response.raise_for_status()  # Lanza excepción si la respuesta no es exitosa (status code 4xx o 5xx)
                response.encoding = "utf-8"

                soup = BeautifulSoup(response.text, "html.parser")

                information = {
                    "title": soup.select_one("h1.text-lead").string,
                    "poster": soup.select_one("img.aspect-poster")["src"],
                    "synopsis": soup.select_one("div.entry").get_text(strip=True),
                }

                genres = [
                    element["href"].split("=")[1]
                    for element in soup.select("header.grid div.flex a")
                    if "=" in element["href"]
                ]

                episodes = []
                try:
                    for script in soup.find_all("script"):
                        if script.string and 'episodes:[' in script.string:
                            script_text = script.string

                            start_marker = 'episodes:['
                            start_idx = script_text.find(start_marker)

                            if start_idx == -1:
                                continue
                            start_idx += len(start_marker)
                            end_idx = script_text.find(']', start_idx)

                            episodes_content = script_text[start_idx:end_idx]
                            parts = episodes_content.split('number')
                            for part in parts[1:]:
                                num_str = ""
                                for char in part:
                                    if char.isdigit():
                                        num_str += char
                                    elif num_str:
                                        break

                                if num_str:
                                    episode_number = int(num_str)
                                    episodes.append(EpisodeInfo(id=episode_number, anime=anime_id))

                            break

                except Exception as exc:
                    print(f"Error al obtener los episodios de {anime_id}: {exc}")
                return AnimeInfo(id=anime_id, episodes=episodes, genres=genres, **information)

            except requests.RequestException as e:
                print(f"Intento {attempt + 1}/{max_attemts} fallido para el anime {anime_id}: {e}")
                attempt += 1
                time.sleep(1)  # Espera un segundo entre intentos para evitar sobrecargar el servidor

        print(f"No se pudo obtener la información del anime {anime_id}")
        return None

class AnimeAV1Singleton:
    __instance = None

    def __new__(cls):
        if AnimeAV1Singleton.__instance is None:
            AnimeAV1Singleton.__instance = AnimeAV1()
        return AnimeAV1Singleton.__instance