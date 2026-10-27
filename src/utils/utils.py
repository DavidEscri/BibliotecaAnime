__author__ = "Jose David Escribano Orts"
__subsystem__ = "utils"
__module__ = "utils.py"
__version__ = "0.5"
__info__ = {"subsystem": __subsystem__, "module_name": __module__, "version": __version__}

import os
import shutil
import sys
import threading
import customtkinter as ctk
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable
from PIL import Image, ImageDraw
from io import BytesIO
import requests

# 8 es el equilibrio entre velocidad de descarga y no saturar el servidor.
_MAX_DOWNLOAD_WORKERS = 8

_REQUEST_TIMEOUT = 10

# Tamaño al que se guardan los pósters en disco: el mayor que pide cualquier
# vista (la ficha de detalle); cada vista reduce con su propio size= al pintar.
# Duplica a propósito gui.theme.Metrics.POSTER_CACHE_SIZE, porque utils/ tiene
# prohibido importar de gui/; si cambia uno, cambia el otro.
POSTER_CACHE_SIZE = (248, 372)

def refactor_genre_text(genre_text):
    """Genera el nombre legible de un género a partir de su slug.

    :param genre_text: Slug del género (p.ej. 'ciencia-ficcion').
    :return: Nombre capitalizado y con separadores como espacio.
    """
    return genre_text.capitalize().replace("-", " ").replace("_", " ")


def download_anime_poster_by_status(status, anime):
    """Descarga el póster de un anime y lo guarda en la carpeta de su estado.

    :param status: Estado del anime; determina la carpeta destino.
    :param anime: Anime cuyo póster se descarga.
    """
    anime_status_dir = get_resource_path(f"resources/images/{status.name.lower()}")
    if not os.path.exists(anime_status_dir):
        os.makedirs(anime_status_dir)
    image_name = f"{anime.id}.jpg"
    response = requests.get(anime.poster, timeout=_REQUEST_TIMEOUT)
    img_data = Image.open(BytesIO(response.content)).resize(POSTER_CACHE_SIZE)
    img_data.save(os.path.join(anime_status_dir, image_name))

def move_anime_poster_by_status(status, old_anime_id, new_anime_id) -> bool:
    """Renombra el póster cacheado de un anime cuando cambia su anime_id.

    Los pósters se guardan como {anime_id}.jpg; sin renombrar, reapuntar una
    fila a otro proveedor dejaría la imagen huérfana y forzaría descargarla.

    :param status: Estado del anime; determina la carpeta donde buscar el póster.
    :param old_anime_id: Id anterior del anime.
    :param new_anime_id: Id nuevo del anime.
    :return: True si había imagen y se movió; False si no había nada que mover.
    """
    anime_status_dir = get_resource_path(f"resources/images/{status.name.lower()}")
    old_poster_path = os.path.join(anime_status_dir, f"{old_anime_id}.jpg")
    if not os.path.exists(old_poster_path):
        return False
    # os.replace y no os.rename: en Windows rename falla si el destino ya existe.
    os.replace(old_poster_path, os.path.join(anime_status_dir, f"{new_anime_id}.jpg"))
    return True

def sync_status_posters(anime, statuses) -> None:
    """Deja el póster de un anime en las carpetas de sus estados activos y solo en ésas.

    Completa primero y borra después, para que siempre quede una copia que encontrar.
    Copia de otra carpeta antes que descargar; aun así puede salir a la red, así
    que no debe llamarse desde el hilo de Tkinter.

    :param anime: Anime con la identidad de la fila guardada; se leen ``.id`` y ``.poster``.
    :param statuses: Estado → si está activo; la carpeta de cada uno es ``status.name.lower()``.
    """
    image_name = f"{anime.id}.jpg"
    for status, is_active in statuses.items():
        status_dir = get_resource_path(f"resources/images/{status.name.lower()}")
        poster_path = os.path.join(status_dir, image_name)
        if not is_active or os.path.exists(poster_path):
            continue
        try:
            cached_path = find_cached_poster_path(anime.id)
            if cached_path is None:
                download_anime_poster_by_status(status, anime)
            else:
                os.makedirs(status_dir, exist_ok=True)
                shutil.copyfile(cached_path, poster_path)
        except Exception as e:
            print(f"No se pudo guardar el póster de {anime.id} en {status.name.lower()}: {e}")

    for status, is_active in statuses.items():
        poster_path = get_resource_path(f"resources/images/{status.name.lower()}/{image_name}")
        if is_active or not os.path.exists(poster_path):
            continue
        try:
            os.remove(poster_path)
        except Exception as e:
            print(f"No se pudo borrar el póster de {anime.id} de {status.name.lower()}: {e}")

def download_animes_poster(images_path, animes):
    """Descarga a images_path los pósters que falten y borra los que sobren.

    :param images_path: Carpeta donde se cachean los pósters.
    :param animes: Animes cuyos pósters deben quedar en esa carpeta.
    """
    if not os.path.exists(images_path):
        os.makedirs(images_path)

    current_animes_images = set(os.listdir(images_path))

    animes_to_download = [
        anime for anime in animes
        if f"{anime.id}.jpg" not in current_animes_images
    ]

    def _download_single(anime):
        image_name = f"{anime.id}.jpg"
        try:
            response = requests.get(anime.poster, timeout=_REQUEST_TIMEOUT)
            img_data = Image.open(BytesIO(response.content)).resize(POSTER_CACHE_SIZE)
            img_data.save(os.path.join(images_path, image_name))
        except Exception as e:
            print(f"Error al descargar el poster de {anime.id}: {e}")

    if animes_to_download:
        with ThreadPoolExecutor(max_workers=_MAX_DOWNLOAD_WORKERS) as executor:
            executor.map(_download_single, animes_to_download)

    anime_ids = {f"{anime.id}.jpg" for anime in animes}
    for image in current_animes_images:
        if image not in anime_ids:
            try:
                os.remove(os.path.join(images_path, image))
            except Exception as e:
                print(f"No se pudo borrar la imagen {image}: {e}")
                continue

def download_images_progress(images_path, recent_animes, on_progress: Callable[[float], None]):
    """Descarga en paralelo los pósters que falten, avisando del progreso.

    El progreso ocupa el tramo 90-100%, pensado para encadenarse tras la carga
    inicial de la app. on_progress se llama desde los hilos de descarga.

    :param images_path: Carpeta donde se cachean los pósters.
    :param recent_animes: Animes recientes cuyos pósters hay que asegurar.
    :param on_progress: Recibe la fracción completada conforme terminan las descargas.
    """
    if not os.path.exists(images_path):
        os.makedirs(images_path)

    total_images = len(recent_animes)
    if total_images == 0:
        return

    current_animes_images = set(os.listdir(images_path))

    cached = [a for a in recent_animes if f"{a.id}.jpg" in current_animes_images]
    to_download = [a for a in recent_animes if f"{a.id}.jpg" not in current_animes_images]

    # Contador compartido entre workers; protegido con Lock para no perder incrementos.
    completed_count = [len(cached)]
    lock = threading.Lock()

    def _update_progress():
        on_progress(round(0.9 + (0.1 * completed_count[0] / total_images), 2))

    _update_progress()

    def _download_single(anime):
        image_name = f"{anime.id}.jpg"
        try:
            response = requests.get(anime.poster, timeout=_REQUEST_TIMEOUT)
            img_data = Image.open(BytesIO(response.content)).resize(POSTER_CACHE_SIZE)
            img_data.save(os.path.join(images_path, image_name))
        except Exception as e:
            print(f"Error al descargar el poster de {anime.id}: {e}")
        finally:
            with lock:
                completed_count[0] += 1
                _update_progress()

    if to_download:
        with ThreadPoolExecutor(max_workers=_MAX_DOWNLOAD_WORKERS) as executor:
            futures = {executor.submit(_download_single, anime): anime for anime in to_download}
            for future in as_completed(futures):
                future.result()  # propaga cualquier excepción no capturada dentro del worker

    anime_ids = {f"{anime.id}.jpg" for anime in recent_animes}
    for image in current_animes_images:
        if image not in anime_ids:
            try:
                os.remove(os.path.join(images_path, image))
            except Exception as e:
                print(f"No se pudo borrar la imagen {image}: {e}")
                continue


#: Carpetas donde puede estar cacheado el póster de un anime, en el orden en
#: que se buscan. El mismo anime puede estar en varias; la primera que lo
#: tenga vale, porque el JPG es el mismo.
POSTER_FOLDERS = ["favourite", "watching", "finished", "pending", "recent_animes", "search"]


def find_cached_poster_path(anime_id) -> str | None:
    """Busca el póster cacheado de un anime sin salir a la red.

    :param anime_id: Id del anime cuyo póster se busca.
    :return: Ruta del fichero, o None si no hay ninguno cacheado.
    """
    base_dir = get_resource_path("resources/images")
    for subfolder in POSTER_FOLDERS:
        folder_path = os.path.join(base_dir, subfolder)
        if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
            continue
        image_path = os.path.join(folder_path, f"{anime_id}.jpg")
        if os.path.exists(image_path):
            return image_path
    return None


def download_poster(poster_url: str) -> Image.Image | None:
    """Descarga un póster sin tocar Tk, para poder hacerlo fuera del hilo de la interfaz.

    :param poster_url: URL del póster.
    :return: La imagen descargada, o None si no se pudo bajar.
    """
    try:
        response = requests.get(poster_url, timeout=_REQUEST_TIMEOUT)
        response.raise_for_status()
        return Image.open(BytesIO(response.content))
    except Exception as e:
        print(f"No se pudo descargar el póster {poster_url}: {e}")
        return None


def load_rounded_image(image_path: str | None, image_size: tuple[int, int],
                       radius: int = 0) -> ctk.CTkImage:
    """Carga un póster reducido al tamaño pedido con las esquinas redondeadas.

    Reduce con LANCZOS en vez del remuestreo por defecto, para no
    desperdiciar la calidad de la caché. Redondea con una máscara alfa,
    porque CustomTkinter no recorta su propia image al corner_radius.

    :param image_path: Ruta del póster, o None si no hay ninguno.
    :param image_size: Tamaño al que se reduce.
    :param radius: Radio de las esquinas redondeadas; 0 para no redondear.
    :return: Imagen lista para un widget CustomTkinter, o un cuadro gris si el fichero no existe.
    """
    if image_path is not None and os.path.exists(image_path):
        return round_image(Image.open(image_path), image_size, radius)
    return round_image(Image.new("RGBA", image_size, (200, 200, 200, 255)), image_size, radius)


def round_image(image: Image.Image, image_size: tuple[int, int], radius: int = 0) -> ctk.CTkImage:
    """Reduce una imagen ya cargada al tamaño pedido y le redondea las esquinas.

    :param image: Imagen de origen, del disco o recién descargada.
    :param image_size: Tamaño al que se reduce.
    :param radius: Radio de las esquinas redondeadas; 0 para no redondear.
    :return: Imagen lista para un widget CustomTkinter.
    """
    image = image.convert("RGBA").resize(image_size, Image.LANCZOS)
    if radius > 0:
        # La máscara va en escala de grises y se pega como canal alfa: lo que
        # queda fuera del rectángulo redondeado se vuelve transparente y deja ver
        # el fondo del contenedor.
        mask = Image.new("L", image_size, 0)
        ImageDraw.Draw(mask).rounded_rectangle(
            (0, 0, image_size[0] - 1, image_size[1] - 1), radius=radius, fill=255
        )
        image.putalpha(mask)

    return ctk.CTkImage(light_image=image, dark_image=image, size=image_size)


def load_dual_image(light_path: str, dark_path: str,
                    image_size: tuple[int, int] = (24, 24)) -> ctk.CTkImage:
    """Carga un icono con sus variantes clara y oscura en un solo CTkImage.

    Al pasar light_image y dark_image juntas, el cambio de apariencia lo
    resuelve CustomTkinter sin reconfigurar el icono a mano. Si un fichero no
    existe, se sustituye por un cuadro gris.

    :param light_path: Ruta del icono para tema claro.
    :param dark_path: Ruta del icono para tema oscuro.
    :param image_size: Tamaño al que se pinta el icono.
    :return: CTkImage con ambas variantes.
    """
    def _open(path: str) -> Image.Image:
        if os.path.exists(path):
            return Image.open(path)
        return Image.new('RGB', image_size, (200, 200, 200))

    return ctk.CTkImage(light_image=_open(light_path), dark_image=_open(dark_path), size=image_size)


def get_resource_path(relative_path):
    """Devuelve la ruta absoluta de un recurso, tanto en script como empaquetado.

    :param relative_path: Ruta relativa a la raíz del proyecto.
    :return: Ruta absoluta normalizada.
    """
    def is_running_as_exe():
        """:return: True si se ejecuta como .exe empaquetado."""
        return getattr(sys, 'frozen', False)

    if is_running_as_exe():
        # _MEIPASS es la carpeta temporal donde PyInstaller extrae los recursos.
        return os.path.join(sys._MEIPASS, relative_path)
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    return os.path.normpath(os.path.join(base_dir, relative_path))