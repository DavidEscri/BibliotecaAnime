__author__ = "Jose David Escribano Orts"
__subsystem__ = "utils"
__module__ = "utils.py"
__version__ = "0.1"
__info__ = {"subsystem": __subsystem__, "module_name": __module__, "version": __version__}

import os
import sys
import tkinter as tk
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


def update_gif(label: tk.Label, gif_frames: list, root: tk.Tk, frame = 0):
    label.config(image=gif_frames[frame])
    frame = (frame + 1) % len(gif_frames)
    root.after(100, update_gif, frame)


def download_images(images_path, recent_animes):
    if not os.path.exists(images_path):
        os.makedirs(images_path)

    current_animes_images = os.listdir(images_path)
    for anime in recent_animes:
        image_name = f"{anime.id}.jpg"
        if image_name in current_animes_images:
            continue
        response = requests.get(anime.poster)
        img_data = Image.open(BytesIO(response.content)).resize((130, 185))
        img_data.save(os.path.join(images_path, image_name))

    for image in current_animes_images:
        if not any(image == f"{anime.id}.jpg" for anime in recent_animes):
            try:
                os.remove(os.path.join(images_path, image))
            except Exception as e:
                print(f"No se pudo borrar la imagen {image}: {e}")
                continue


def load_image(image_path: str):
    if os.path.exists(image_path):
        return ImageTk.PhotoImage(Image.open(image_path))
    return ImageTk.PhotoImage(Image.new('RGB', (130, 185), (200, 200, 200)))  # Placeholder


def on_mousewheel(event, canvas):
    if event.delta:
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    else:
        canvas.yview_scroll(int(event.num * -1), "units")

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