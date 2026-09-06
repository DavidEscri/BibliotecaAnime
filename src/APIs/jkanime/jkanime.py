"""
jkanime.net mezcla dos técnicas de parseo según la superficie: HTML con
selectores CSS estables en portada, búsqueda y ficha; payload de datos
incrustado en un <script> en el directorio y la lista de episodios.

La petición de episodios (POST /ajax/episodes/<id>/) exige token CSRF y
comparte sesión con la petición de la ficha. El slug del anime (AnimeInfo.id)
y el id numérico interno que exige ese endpoint no son intercambiables.
"""
__author__ = "Jose David Escribano Orts"
__subsystem__ = "APIs.jkanime"
__module__ = "jkanime.py"
__version__ = "0.2"
__info__ = {"subsystem": __subsystem__, "module_name": __module__, "version": __version__}

import json
import re

import requests

from typing import Dict, List, Optional, Tuple, Union
from bs4 import BeautifulSoup
from urllib.parse import urlencode, urlparse, quote

from APIs.common.animeProviderMgr import AnimeProvider
from APIs.common.models import AnimeGenreFilter, AnimeOrderFilter, AnimeProviderId, ServerInfo, EpisodeInfo, AnimeInfo

BASE_URL = "https://jkanime.net"
SEARCH_URL = f"{BASE_URL}/buscar"
DIRECTORY_URL = f"{BASE_URL}/directorio"
EPISODES_AJAX_URL = f"{BASE_URL}/ajax/episodes"

# Sin User-Agent de navegador el sitio responde de forma inconsistente.
_USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
               "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
_HEADERS = {"User-Agent": _USER_AGENT}

# La búsqueda del sitio devuelve una rejilla fija de 30 resultados y no pagina.
SEARCH_MAX_RESULTS = 30

# Solo se listan las excepciones; __translate_genre() cae al valor del enum si no hay traducción.
_GENRE_TRANSLATIONS: Dict[AnimeGenreFilter, str] = {
    AnimeGenreFilter.CARRERAS: "autos",
    AnimeGenreFilter.CIENCIA_FICCIÓN: "sci-fi",
    AnimeGenreFilter.DEMENCIA: "dementia",
    AnimeGenreFilter.ESCOLARES: "colegial",
    AnimeGenreFilter.ESPACIAL: "space",
    AnimeGenreFilter.INFANTIL: "nios",
    AnimeGenreFilter.POLICÍA: "policial",
    AnimeGenreFilter.RECUENTOS_DE_LA_VIDA: "cosas-de-la-vida",
    AnimeGenreFilter.SUPERPODERES: "super-poderes",
    AnimeGenreFilter.SUSPENSO: "thriller",
}

# 'popularidad' se deja adrede sin 'orden': orden=asc invertiría el criterio.
_ORDER_TRANSLATIONS: Dict[str, Dict[str, str]] = {
    AnimeOrderFilter.ALFABÉTICAMENTE.value: {"filtro": "nombre", "orden": "asc"},
    AnimeOrderFilter.CALIFICACIÓN.value: {"filtro": "popularidad"},
}

# Rutas de primer nivel que NO son fichas de anime, para no colarlas como tales.
_RESERVED_PATHS = {"directorio", "buscar", "estrenos", "top", "horario", "aleatorio",
                   "perfil", "registro", "login", "logout", "ajax", "jkplayer", "studio"}


def _fetch(url: str, session: requests.Session = None, **kwargs) -> requests.Response:
    """Descarga una página de jkanime.net con el User-Agent de navegador.

    :param url: URL a descargar.
    :param session: Sesión a reutilizar; necesaria para conservar cookies.
    :param kwargs: Argumentos adicionales para requests.get.
    :return: Respuesta HTTP con response.text ya en UTF-8.
    """
    kwargs.setdefault("timeout", 10)
    headers = dict(_HEADERS)
    headers.update(kwargs.pop("headers", {}))
    getter = session.get if session is not None else requests.get
    response = getter(url, headers=headers, **kwargs)
    if "charset" not in response.headers.get("Content-Type", "").lower():
        response.encoding = "utf-8"
    return response


class JKAnime(AnimeProvider):

    PROVIDER_ID = AnimeProviderId.JKANIME
    PROVIDER_NAME = "JKAnime"
    BASE_URL = BASE_URL

    def search_animes_by_genres_and_order(self, genres: List[AnimeGenreFilter], order: str = None,
                                          page: int = None) -> Tuple[List[AnimeInfo], int]:
        """Busca animes en el directorio de jkanime.net filtrando por género y orden.

        Solo se aplica el primer género si se pasan varios, y
        AnimeOrderFilter.CALIFICACIÓN se sirve como popularidad, lo más
        cercano que ofrece el sitio a una puntuación.

        :param genres: Lista de géneros por los que filtrar.
        :param order: Valor de AnimeOrderFilter.
        :param page: Página del listado a consultar.
        :return: Tupla (lista de animes, última página).
        """
        params = dict()

        if genres:
            if len(genres) > 1:
                print(f"Aviso: JKAnime solo permite filtrar por un género a la vez; "
                      f"se usará {genres[0].value!r} y se ignoran los demás.")
            params["genero"] = self.__translate_genre(genres[0])

        order_params = _ORDER_TRANSLATIONS.get(order)
        if order_params is not None:
            params.update(order_params)
        elif order not in (None, AnimeOrderFilter.POR_DEFECTO.value):
            print(f"Aviso: JKAnime no admite el orden {order!r}; se usa el orden por defecto del sitio.")

        if page is not None:
            params["p"] = page

        url = f"{DIRECTORY_URL}?{urlencode(params)}" if params else DIRECTORY_URL

        try:
            response = _fetch(url)
            response.raise_for_status()
        except requests.RequestException as exc:
            print(f"Error al consultar el directorio de JKAnime: {exc}")
            return [], 1

        paginator = self.__extract_directory_payload(response.text)
        if paginator is None:
            print("No se pudo extraer el payload del directorio de JKAnime")
            return [], 1

        animes = [anime for anime in
                  (self.__parse_directory_entry(entry) for entry in paginator.get("data") or [])
                  if anime is not None]
        last_page = int(paginator.get("last_page") or 1)

        return animes, last_page

    def search_animes_by_query(self, query: str = None, page: int = None) -> Tuple[List[AnimeInfo], int]:
        """Busca en jkanime.net por texto libre.

        La búsqueda del sitio no pagina: devuelve como mucho 30 resultados y
        siempre 1 como última página. Para recorrer el catálogo completo hay
        que usar search_animes_by_genres_and_order.

        :param query: Texto de búsqueda.
        :param page: Se acepta por compatibilidad con el contrato, pero se ignora.
        :return: Tupla (lista de animes, 1).
        """
        if page is not None and not isinstance(page, int):
            raise TypeError

        if not query:
            # TODO: Si el texto está vacío, en vez de buscar en SEARCH_URL, habría que buscar en DIRECTORY_URL para así poder obtener animes.
            return [], 1

        if page is not None and page > 1:
            print("Aviso: la búsqueda de JKAnime no pagina; solo existe la primera página.")
            return [], 1

        try:
            response = _fetch(f"{SEARCH_URL}/{quote(query)}")
            response.raise_for_status()
        except requests.RequestException as exc:
            print(f"Error al buscar {query!r} en JKAnime: {exc}")
            return [], 1

        soup = BeautifulSoup(response.text, "html.parser")
        return self.__parse_anime_cards(soup)[:SEARCH_MAX_RESULTS], 1

    def get_anime_episode_servers(self, anime_id: Union[str, int], episode_id: int) -> List[ServerInfo]:
        """Obtiene la lista de servidores de vídeo de un episodio.

        :param anime_id: Identificador (slug) del anime.
        :param episode_id: Número del episodio.
        :return: Lista de servidores disponibles.
        """
        try:
            response = _fetch(f"{BASE_URL}/{anime_id}/{episode_id}")
            response.raise_for_status()
        except requests.RequestException as exc:
            print(f"Error al obtener los servidores del episodio {episode_id} de {anime_id}: {exc}")
            return []

        html = response.text
        soup = BeautifulSoup(html, "html.parser")

        # Nombre visible de cada pestaña, indexado por el N de 'btn-show-N'.
        server_names: Dict[int, str] = {}
        for tab in soup.select("a[id^='btn-show-']"):
            match = re.search(r"btn-show-(\d+)$", tab.get("id", ""))
            if match:
                server_names[int(match.group(1))] = tab.get_text(strip=True)

        # Los reproductores viven en un bloque JS (video[N] = '<iframe .../>') separado
        # de sus nombres (pestañas btn-show-N); se emparejan por ese índice N.
        servers: List[ServerInfo] = []
        for index_text, iframe_html in re.findall(r"video\[(\d+)\]\s*=\s*'(.*?)';", html, re.DOTALL):
            src_match = re.search(r'src="([^"]+)"', iframe_html)
            if src_match is None:
                continue
            index = int(index_text)
            servers.append(
                ServerInfo(
                    server=server_names.get(index, f"Opción {index + 1}"),
                    url=src_match.group(1),
                )
            )

        return servers

    def get_recent_animes(self) -> List[AnimeInfo]:
        """:return: Animes con episodio recién publicado en la portada de jkanime.net."""
        # TODO: Corregir para que, en vez de obtener todos los animes que aparecen en `https://jkanime.net/` únicamente
        # se obtengan los que se encuentran en la sección de `PROGRAMACIÓN` y, dentro de esta únicamente la secciónd e `Animes`
        try:
            response = _fetch(BASE_URL)
            response.raise_for_status()
        except requests.RequestException as exc:
            print(f"Error al conectarse a {BASE_URL} para obtener los animes recientes: {exc}")
            return []

        soup = BeautifulSoup(response.text, "html.parser")

        animes: List[AnimeInfo] = []
        seen_ids = set()

        for card in soup.select("div.card"):
            link = card.select_one("a[href]") or card.find_parent("a", href=True)
            if link is None:
                continue

            anime_id = self.__slug_from_url(link.get("href", ""))
            if anime_id is None or anime_id in seen_ids:
                continue

            title_el = card.select_one("h5.card-title")
            img_el = card.select_one("img")
            if title_el is None or img_el is None:
                continue

            # El <img> lleva dos imágenes: "src" es la captura del episodio y
            # "data-animepic" el póster del anime; se usa la segunda.
            poster = img_el.get("data-animepic") or img_el.get("src", "")

            seen_ids.add(anime_id)
            animes.append(
                AnimeInfo(
                    id=anime_id,
                    title=title_el.get_text(strip=True),
                    poster=poster,
                )
            )

        return animes

    def get_anime_info(self, anime_id: Union[str, int]) -> Optional[AnimeInfo]:
        """Obtiene la ficha completa de un anime.

        Cuesta dos peticiones: la ficha y el POST al endpoint de episodios. Si
        esa segunda llamada falla, se devuelve igualmente la ficha con la lista
        de episodios vacía.

        :param anime_id: Identificador (slug) del anime.
        :return: Ficha del anime, o None si falla la primera petición.
        """
        session = requests.Session()
        try:
            response = _fetch(f"{BASE_URL}/{anime_id}", session=session)
            response.raise_for_status()
        except requests.RequestException as exc:
            print(f"No se pudo obtener la información del anime {anime_id}: {exc}")
            return None

        html = response.text
        soup = BeautifulSoup(html, "html.parser")

        info_block = soup.select_one("div.anime_info")

        title_el = info_block.select_one("h3") if info_block else None
        title = title_el.get_text(strip=True) if title_el else None
        if not title:
            # Fallback: el <title> del documento antepone el nombre del anime.
            og_title = soup.select_one("meta[property='og:title']")
            title = og_title.get("content", "").split(" - ")[0].strip() if og_title else str(anime_id)

        synopsis_el = info_block.select_one("p.scroll") if info_block else None
        synopsis = synopsis_el.get_text(" ", strip=True) if synopsis_el else None

        og_image = soup.select_one("meta[property='og:image']")
        poster = og_image.get("content", "") if og_image else ""

        genres = self.__extract_genres(soup)

        episodes = self.__get_episodes(html, anime_id, session)

        return AnimeInfo(
            id=anime_id,
            title=title,
            poster=poster,
            synopsis=synopsis,
            genres=genres,
            episodes=episodes,
        )

    # ------------------------------------------------------------------
    # Helpers privados de parseo
    # ------------------------------------------------------------------

    @staticmethod
    def __translate_genre(genre: AnimeGenreFilter) -> str:
        """Traduce un género del catálogo común al slug propio de JKAnime."""
        return _GENRE_TRANSLATIONS.get(genre, genre.value)

    @staticmethod
    def __slug_from_url(url: str) -> Optional[str]:
        """Extrae el slug del anime de una URL de ficha o de episodio del sitio.

        :param url: URL del sitio.
        :return: Slug del anime, o None si la URL no apunta a un anime.
        """
        path = urlparse(url).path.strip("/")
        if not path:
            return None
        slug = path.split("/")[0]
        if not slug or slug in _RESERVED_PATHS:
            return None
        return slug

    @classmethod
    def __parse_anime_cards(cls, soup: BeautifulSoup) -> List[AnimeInfo]:
        """Parsea las tarjetas div.anime__item de la búsqueda.

        El póster no está en un <img> sino en el atributo data-setbg del div de la imagen.
        """
        animes: List[AnimeInfo] = []
        seen_ids = set()

        for card in soup.select("div.anime__item"):
            link = card.select_one("a[href]")
            if link is None:
                continue

            anime_id = cls.__slug_from_url(link.get("href", ""))
            if anime_id is None or anime_id in seen_ids:
                continue

            title_el = card.select_one(".anime__item__text h5")
            pic_el = card.select_one(".anime__item__pic")
            if title_el is None:
                continue

            poster = pic_el.get("data-setbg", "") if pic_el is not None else ""

            seen_ids.add(anime_id)
            animes.append(
                AnimeInfo(
                    id=anime_id,
                    title=title_el.get_text(strip=True),
                    poster=poster,
                )
            )

        return animes

    @staticmethod
    def __extract_directory_payload(html: str) -> Optional[dict]:
        """Recorta el objeto JS 'animes = {...}' incrustado en el directorio y lo parsea.

        El recorte cuenta llaves y respeta cadenas y escapes, porque las
        sinopsis llevan comillas dentro y una regex perezosa cortaría mal.

        :param html: HTML de la página del directorio.
        :return: Payload ya parseado, o None si no se encuentra o no es JSON válido.
        """
        match = re.search(r"\banimes\s*=\s*\{", html)
        if match is None:
            return None

        start = match.end() - 1
        depth = 0
        in_string = False
        escaped = False
        quote_char = ""

        for index in range(start, len(html)):
            char = html[index]
            if in_string:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == quote_char:
                    in_string = False
            elif char in "\"'":
                in_string, quote_char = True, char
            elif char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(html[start:index + 1])
                    except json.JSONDecodeError as exc:
                        print(f"El payload del directorio de JKAnime no es JSON válido: {exc}")
                        return None
        return None

    @classmethod
    def __parse_directory_entry(cls, entry: dict) -> Optional[AnimeInfo]:
        """:return: AnimeInfo a partir de un elemento del payload del directorio, o None."""
        anime_id = cls.__slug_from_url(entry.get("url") or "") or entry.get("slug")
        if not anime_id:
            return None

        return AnimeInfo(
            id=anime_id,
            title=entry.get("title") or entry.get("short_title") or str(anime_id),
            poster=entry.get("image") or "",
            synopsis=entry.get("synopsis"),
        )

    @staticmethod
    def __extract_genres(soup: BeautifulSoup) -> List[str]:
        """Extrae los slugs de género de los enlaces /genero/<slug>/ de la ficha."""
        genres: List[str] = []
        seen = set()
        for link in soup.select("a[href*='/genero/']"):
            slug = urlparse(link.get("href", "")).path.strip("/").split("/")[-1]
            if slug and slug not in seen:
                seen.add(slug)
                genres.append(slug)
        return genres

    @classmethod
    def __get_episodes(cls, html: str, anime_id: Union[str, int],
                       session: requests.Session) -> List[EpisodeInfo]:
        """Obtiene la lista de episodios vía POST /ajax/episodes/<id_numerico>/.

        Solo interesa el 'total' del paginador que devuelve el endpoint, ya que
        los episodios están numerados de 1 a N.

        :param html: HTML de la ficha, de donde se extraen el id numérico y el token CSRF.
        :param anime_id: Slug del anime, usado solo para los mensajes de log.
        :param session: Sesión que comparte cookies con la petición de la ficha.
        :return: Lista de episodios, o [] si no se puede completar la petición.
        """
        id_match = re.search(r"/ajax/episodes/(\d+)", html)
        if id_match is None:
            print(f"No se encontró el id numérico interno de {anime_id}; sin lista de episodios")
            return []

        token_match = re.search(r'name="csrf-token"\s+content="([^"]+)"', html)
        if token_match is None:
            print(f"No se encontró el token CSRF en la ficha de {anime_id}; sin lista de episodios")
            return []

        try:
            response = session.post(
                f"{EPISODES_AJAX_URL}/{id_match.group(1)}/",
                headers={**_HEADERS,
                         "X-CSRF-TOKEN": token_match.group(1),
                         "X-Requested-With": "XMLHttpRequest",
                         "Referer": f"{BASE_URL}/{anime_id}"},
                timeout=10,
            )
            response.raise_for_status()
            paginator = response.json()
        except (requests.RequestException, ValueError) as exc:
            print(f"No se pudieron obtener los episodios de {anime_id}: {exc}")
            return []

        total = int(paginator.get("total") or 0)
        return [EpisodeInfo(id=number, anime=anime_id) for number in range(1, total + 1)]


class JKAnimeSingleton:
    __instance = None

    def __new__(cls):
        if JKAnimeSingleton.__instance is None:
            JKAnimeSingleton.__instance = JKAnime()
        return JKAnimeSingleton.__instance
