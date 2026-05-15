__author__ = "Jose David Escribano Orts"
__subsystem__ = "utils"
__module__ = "utils.py"
__version__ = "0.1"
__info__ = {"subsystem": __subsystem__, "module_name": __module__, "version": __version__}

import os
import sys
import threading
import tkinter as tk
import customtkinter as ctk
from concurrent.futures import ThreadPoolExecutor, as_completed
from PIL import Image
from io import BytesIO
import requests

# Número de hilos paralelos para descarga de imágenes.
# 8 es el equilibrio entre velocidad y no saturar el servidor de AnimeFLV.
_MAX_DOWNLOAD_WORKERS = 8

# Timeout en segundos para cada petición de imagen.
_REQUEST_TIMEOUT = 10

def removeprefix(text: str, prefix_text: str) -> str:
    """
    Remove the prefix of a given string if it contains that
    prefix for compatability with Python >3.9

    :param _str: string to remove prefix from.
    :param episode: prefix to remove from the string.
    :rtype: str
    """

    if type(text) is type(prefix_text):
        if text.startswith(prefix_text):
            return text[len(prefix_text):]
        else:
            return text[:]


def refactor_genre_text(genre_text):
    """
    Genera el nombre para mostrar en la interfaz a partir del nombre
    """
    return genre_text.capitalize().replace("-", " ").replace("_", " ")


def update_gif(label: tk.Label, gif_frames: list, root: tk.Tk, frame = 0):
    label.config(image=gif_frames[frame])
    frame = (frame + 1) % len(gif_frames)
    root.after(100, update_gif, frame)

def download_anime_poster_by_status(status, anime):
    anime_status_dir = get_resource_path(f"resources/images/{status.name.lower()}")
    if not os.path.exists(anime_status_dir):
        os.makedirs(anime_status_dir)
    image_name = f"{anime.id}.jpg"
    response = requests.get(anime.poster, timeout=_REQUEST_TIMEOUT)
    img_data = Image.open(BytesIO(response.content)).resize((130, 185))
    img_data.save(os.path.join(anime_status_dir, image_name))

def remove_anime_poster_by_status(status, anime):
    anime_status_dir = get_resource_path(f"resources/images/{status.name.lower()}")
    image_name = f"{anime.id}.jpg"
    anime_poster_path = os.path.join(anime_status_dir, image_name)
    if not os.path.exists(anime_poster_path):
        print(f"No existe el poster para el anime {anime.title} con estado {status.name}")
        return
    os.remove(anime_poster_path)

def download_animes_poster(images_path, animes):
    if not os.path.exists(images_path):
        os.makedirs(images_path)

    current_animes_images = set(os.listdir(images_path))

    # Filtrar solo los animes cuya imagen aún no existe en disco
    animes_to_download = [
        anime for anime in animes
        if f"{anime.id}.jpg" not in current_animes_images
    ]

    def _download_single(anime):
        image_name = f"{anime.id}.jpg"
        try:
            response = requests.get(anime.poster, timeout=_REQUEST_TIMEOUT)
            img_data = Image.open(BytesIO(response.content)).resize((130, 185))
            img_data.save(os.path.join(images_path, image_name))
        except Exception as e:
            print(f"Error al descargar el poster de {anime.id}: {e}")

    # Descargar en paralelo solo las imágenes que faltan
    if animes_to_download:
        with ThreadPoolExecutor(max_workers=_MAX_DOWNLOAD_WORKERS) as executor:
            executor.map(_download_single, animes_to_download)

    # Eliminar imágenes que ya no corresponden a ningún anime de la lista actual
    anime_ids = {f"{anime.id}.jpg" for anime in animes}
    for image in current_animes_images:
        if image not in anime_ids:
            try:
                os.remove(os.path.join(images_path, image))
            except Exception as e:
                print(f"No se pudo borrar la imagen {image}: {e}")
                continue

def download_images_progress(images_path, recent_animes, progress_bar: ctk.CTkProgressBar, progress_label: ctk.CTkLabel):
    if not os.path.exists(images_path):
        os.makedirs(images_path)

    total_images = len(recent_animes)
    if total_images == 0:
        return

    current_animes_images = set(os.listdir(images_path))

    # Separar los animes en: ya en caché (progreso inmediato) y los que hay que descargar
    cached = [a for a in recent_animes if f"{a.id}.jpg" in current_animes_images]
    to_download = [a for a in recent_animes if f"{a.id}.jpg" not in current_animes_images]

    # Contador compartido entre workers, protegido con Lock
    completed_count = [len(cached)]  # los cacheados ya cuentan como completados
    lock = threading.Lock()

    def _update_progress():
        progress_percentage = round(0.9 + (0.1 * completed_count[0] / total_images), 2)
        progress_bar.set(progress_percentage)
        progress_label.configure(text=f"{int(progress_percentage * 100)} %")

    # Reflejar en la barra el progreso inicial de los ya cacheados
    _update_progress()

    def _download_single(anime):
        image_name = f"{anime.id}.jpg"
        try:
            response = requests.get(anime.poster, timeout=_REQUEST_TIMEOUT)
            img_data = Image.open(BytesIO(response.content)).resize((130, 185))
            img_data.save(os.path.join(images_path, image_name))
        except Exception as e:
            print(f"Error al descargar el poster de {anime.id}: {e}")
        finally:
            # Actualizar el progreso de forma thread-safe
            with lock:
                completed_count[0] += 1
                _update_progress()

    # Descargar en paralelo las imágenes que faltan
    if to_download:
        with ThreadPoolExecutor(max_workers=_MAX_DOWNLOAD_WORKERS) as executor:
            futures = {executor.submit(_download_single, anime): anime for anime in to_download}
            # Esperar a que todos los futures terminen (as_completed ya gestiona el orden de finalización)
            for future in as_completed(futures):
                future.result()  # propagar excepciones no capturadas internamente

    # Eliminar imágenes de animes que ya no están en la lista de recientes
    anime_ids = {f"{anime.id}.jpg" for anime in recent_animes}
    for image in current_animes_images:
        if image not in anime_ids:
            try:
                os.remove(os.path.join(images_path, image))
            except Exception as e:
                print(f"No se pudo borrar la imagen {image}: {e}")
                continue


def get_anime_image(anime, image_size: tuple[int, int] = (195, 275)) -> ctk.CTkImage:
    base_dir = get_resource_path("resources/images")
    subfolders = ["favourite", "finished", "pending", "recent_animes", "search"]
    for subfolder in subfolders:
        folder_path = os.path.join(base_dir, subfolder)
        if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
            continue
        image_path = os.path.join(folder_path, f"{anime.id}.jpg")
        if os.path.exists(image_path):
            return load_image(image_path, image_size)
    response = requests.get(anime.poster)
    return ctk.CTkImage(Image.open(BytesIO(response.content)).resize(image_size))

def load_image(image_path: str, image_size: tuple[int, int] = (130, 185)):
    if os.path.exists(image_path):
        return ctk.CTkImage(Image.open(image_path), size=image_size)
    return ctk.CTkImage(Image.new('RGB', image_size, (200, 200, 200)), size=image_size)  # Placeholder


def get_resource_path(relative_path):
    """Devuelve la ruta absoluta de los recursos, ya sea que se esté ejecutando
    como script o como ejecutable empaquetado."""
    def is_running_as_exe():
        """Determina si el programa se está ejecutando como un archivo .exe o desde el IDE."""
        return getattr(sys, 'frozen', False)

    if is_running_as_exe():
        # Si está empaquetado, _MEIPASS contendrá la ruta temporal donde se extraen los archivos
        return os.path.join(sys._MEIPASS, relative_path)
    # Cuando se ejecuta como script, calcular la raíz del proyecto a partir
    # de la ubicación de este módulo (src/utils/utils.py -> project root)
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    return os.path.normpath(os.path.join(base_dir, relative_path))
    # return os.path.join(os.path.abspath(".."), relative_path)