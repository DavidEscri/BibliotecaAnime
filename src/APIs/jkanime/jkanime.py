"""
jkanime.net es una aplicación Laravel, y no se parsea de una sola manera: mezcla las dos técnicas que ya usan los otros
proveedores del proyecto, según la superficie que se mire.

  - Portada, búsqueda y ficha son HTML renderizado en el servidor, con selectores CSS estables (como AnimeFLV).
  - El directorio y la lista de episodios llegan como **payload de datos**, no como HTML (como AnimeAV1). En el
    directorio, el servidor incrusta un objeto JS `animes = {...}` dentro de un <script> de la propia página y jQuery
    se limita a pintarlo; por eso las rejillas `div.page_directorio` están vacías en el HTML crudo. NO existe un
    endpoint AJAX que devuelva el listado: el dato ya viene en la página, y basta con recortarlo.

La única petición que necesita token CSRF es la de episodios (`POST /ajax/episodes/<id>/`): sin la cabecera
`X-CSRF-TOKEN` que se lee del <meta> de la ficha, Laravel responde 419. Por eso `get_anime_info` usa una `Session`
propia: necesita encadenar la ficha y esa llamada compartiendo cookies.

Ojo con las dos identidades de un anime en este sitio: el *slug* ('hunter-x-hunter-2011') es el que se usa en las URL
y el que se expone como `AnimeInfo.id`, pero el endpoint de episodios exige el **id numérico interno** (429), que solo
aparece dentro del HTML de la ficha. No son intercambiables.
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

# La búsqueda del sitio devuelve una rejilla fija de 6x5 y no pagina: no es una
# limitación que se pueda sortear con parámetros, es su diseño. Para recorrer el
# catálogo completo está el directorio.
SEARCH_MAX_RESULTS = 30

# JKAnime usa sus propios slugs de género para 12 de los 40 del catálogo común.
# El resto coincide literalmente, así que solo se listan las excepciones y
# __translate_genre() cae al valor del enum cuando no hay traducción.
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

# El desplegable 'filtro' del directorio solo ofrece dos criterios, y el sentido
# lo marca un parámetro 'orden' aparte: sin él, 'nombre' devuelve de la Z a la A.
# 'popularidad' se deja adrede SIN 'orden', porque orden=asc invierte el criterio
# y pondría delante los animes menos populares.
_ORDER_TRANSLATIONS: Dict[str, Dict[str, str]] = {
    AnimeOrderFilter.ALFABÉTICAMENTE.value: {"filtro": "nombre", "orden": "asc"},
    AnimeOrderFilter.CALIFICACIÓN.value: {"filtro": "popularidad"},
}

# Rutas de primer nivel que NO son fichas de anime, para no colarlas como tales.
_RESERVED_PATHS = {"directorio", "buscar", "estrenos", "top", "horario", "aleatorio",
                   "perfil", "registro", "login", "logout", "ajax", "jkplayer", "studio"}


def _fetch(url: str, session: requests.Session = None, **kwargs) -> requests.Response:
    """
    Descarga una página de jkanime.net con el User-Agent de navegador.

    :param url: URL a descargar.
    :param session: Sesión a reutilizar (necesaria cuando hay que conservar cookies).
    :param kwargs: Argumentos que se pasan tal cual a `requests.get`.
    :rtype: requests.Response
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
        """
        Busca animes en el directorio de jkanime.net filtrando por género y orden.

        El directorio es la superficie paginada del sitio (~4.900 animes en 163
        páginas de 30). Los resultados no se leen del DOM sino del objeto JS
        `animes` que el servidor incrusta en la página; ese objeto es un paginador
        de Laravel, así que la última página viene dada y no hay que deducirla.

        Los resultados del directorio ya traen sinopsis e imagen, de modo que no
        hace falta una segunda petición por anime para completarlos.

        ⚠️ El desplegable de género del sitio es de selección única: si se pasan
        varios géneros solo se aplica el primero, y se avisa por consola.

        ⚠️ JKAnime no expone una puntuación, así que AnimeOrderFilter.CALIFICACIÓN
        se sirve con su criterio de **popularidad**, que no es lo mismo pero es lo
        más cercano que ofrece el sitio.

        :param genres: Lista de géneros por los que filtrar.
        :param order: Valor de AnimeOrderFilter.
        :param page: Página del listado a consultar.
        :rtype: (List[AnimeInfo], int)
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
        """
        Busca en jkanime.net por texto libre.

        La búsqueda del sitio **no pagina**: devuelve como mucho 30 resultados
        (rejilla de 6x5) y el parámetro de página se ignora, así que siempre se
        devuelve 1 como última página. Para recorrer el catálogo hay que usar
        search_animes_by_genres_and_order, que sí pagina.

        El separador de las palabras es indiferente para el sitio ('one piece',
        'one+piece' y 'one-piece' devuelven lo mismo), así que basta con
        codificar la consulta tal cual.

        :param query: Texto de búsqueda, como por ejemplo 'Nanatsu no Taizai'.
        :param page: Se acepta por compatibilidad con el contrato, pero se ignora.
        :rtype: (List[AnimeInfo], int)
        """
        if page is not None and not isinstance(page, int):
            raise TypeError

        if not query:
            # TODO: Si el texto está vacío, en vez de buscar en SEARCH_URL, habría que buscar en DIRECTORY_URL para así poder obtener animes.
            return [], 1

        if page is not None and page > 1:
            # Pedir la página 2 y devolver la 1 sería mentir al llamante.
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
        """
        Obtiene la lista de servidores de vídeo de un episodio de un anime.

        Los reproductores no están en el DOM: el HTML trae un bloque JS con
        asignaciones `video[N] = '<iframe ... src="..."></iframe>'`, y los nombres
        de los servidores viven aparte, en las pestañas `<a id="btn-show-N">`.
        Se emparejan por ese índice N.

        :param anime_id: Identificador (slug) del anime, como por ejemplo 'one-piece'.
        :param episode_id: Número del episodio.
        :rtype: List[ServerInfo]
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
        """
        Obtiene los animes con episodio recién publicado en la portada de jkanime.net.

        Las tarjetas de la portada son de **episodio**, no de anime, y su <img>
        lleva dos imágenes: `src` es la captura del episodio y `data-animepic` el
        póster del anime. Se usa la segunda, que es la que espera la biblioteca.

        :rtype: List[AnimeInfo]
        """
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
        """
        Obtiene la ficha completa de un anime.

        Cuesta **dos peticiones**: la ficha (título, sinopsis, géneros, póster) y
        el POST al endpoint de episodios, que necesita el id numérico interno y el
        token CSRF, ambos presentes en el HTML de la ficha. Si esa segunda llamada
        falla, se devuelve la ficha igualmente con la lista de episodios vacía en
        vez de perder también lo que sí se pudo leer.

        :param anime_id: Identificador (slug) del anime, como por ejemplo 'one-piece'.
        :rtype: AnimeInfo
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
        """
        Extrae el slug del anime de cualquier URL del sitio, tanto de ficha
        (/one-piece/) como de episodio (/one-piece/1080/). Devuelve None si la
        URL no apunta a un anime.
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
        """
        Parsea las tarjetas `div.anime__item` de la búsqueda. El póster no está en
        un <img> sino en el atributo `data-setbg` del div de la imagen.
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
        """
        Recorta el objeto JS `animes = {...}` que el servidor incrusta en el
        directorio y lo devuelve parseado.

        El recorte se hace contando llaves y respetando cadenas y escapes: las
        sinopsis llevan comillas dentro, así que una expresión regular perezosa
        cortaría por el sitio equivocado.
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
        """Convierte un elemento del payload del directorio en un AnimeInfo."""
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
        """
        Extrae los slugs de género de los enlaces /genero/<slug>/ de la ficha,
        igual que hacen animeflv.py y animeav1.py.
        """
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
        """
        Obtiene la lista de episodios vía `POST /ajax/episodes/<id_numerico>/`.

        Ese endpoint devuelve un paginador de Laravel; solo interesa su `total`,
        porque los episodios de JKAnime están numerados de 1 a N y no hace falta
        recorrer todas las páginas para reconstruirlos.
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
