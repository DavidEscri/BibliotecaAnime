import os
import tkinter as tk
from PIL import Image, ImageTk
from io import BytesIO
import requests


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