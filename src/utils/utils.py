__author__ = "Jose David Escribano Orts"
__subsystem__ = "utils"
__module__ = "utils.py"
__version__ = "0.1"
__info__ = {"subsystem": __subsystem__, "module_name": __module__, "version": __version__}

import os
import sys
import tkinter as tk
import customtkinter as ctk
from PIL import Image, ImageTk
from io import BytesIO
import requests


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
    return genre_text.capitalize().replace("-", " ")


def update_gif(label: tk.Label, gif_frames: list, root: tk.Tk, frame = 0):
    label.config(image=gif_frames[frame])
    frame = (frame + 1) % len(gif_frames)
    root.after(100, update_gif, frame)


def download_images(images_path, recent_animes, progress_bar: ctk.CTkProgressBar, progress_label: ctk.CTkLabel):
    if not os.path.exists(images_path):
        os.makedirs(images_path)

    total_images = len(recent_animes)
    current_animes_images = os.listdir(images_path)
    for index, anime in enumerate(recent_animes):
        image_name = f"{anime.id}.jpg"
        progress_percentage = round(0.9 + (0.1 * (index + 1) / total_images), 2)
        if image_name in current_animes_images:
            progress_bar.set(progress_percentage)  # Actualizar progreso
            progress_label.configure(text=f"{int(progress_percentage*100)} %")  # Actualizar etiqueta
            continue
        response = requests.get(anime.poster)
        img_data = Image.open(BytesIO(response.content)).resize((130, 185))
        img_data.save(os.path.join(images_path, image_name))
        progress_bar.set(progress_percentage)  # Actualizar progreso
        progress_label.configure(text=f"{int(progress_percentage*100)} %")  # Actualizar etiqueta

    for image in current_animes_images:
        if not any(image == f"{anime.id}.jpg" for anime in recent_animes):
            try:
                os.remove(os.path.join(images_path, image))
            except Exception as e:
                print(f"No se pudo borrar la imagen {image}: {e}")
                continue


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
    return os.path.join(os.path.abspath(".."), relative_path)