__author__ = "Jose David Escribano Orts"
__subsystem__ = "main"
__module__ = "main.py"
__version__ = "0.1"
__info__ = {"subsystem": __subsystem__, "module_name": __module__, "version": __version__}

from src.animeflv.animeflv import AnimeFLV

import tkinter as tk
import requests
from PIL import Image, ImageTk, ImageSequence
from io import BytesIO
import os
import webbrowser
import threading


def show_loading_screen():
    # Desactivar el ajuste de tamaño durante la carga
    root.resizable(False, False)

    # Ocultar el sidebar durante la carga
    sidebar.pack_forget()

    # Crear un frame para la pantalla de carga que ocupe toda la ventana
    global loading_frame
    loading_frame = tk.Frame(root, width=1200, height=850, bg="#ECF0F1")  # Tamaño fijo para centrarlo
    loading_frame.pack_propagate(False)

    # Centrar el frame
    x_position = (root.winfo_width())  # Centrar horizontalmente (ancho ventana - ancho frame) / 2
    y_position = (root.winfo_height() + 150)  # Centrar verticalmente (alto ventana - alto frame) / 2
    loading_frame.place(x=x_position, y=y_position)

    # Mostrar el texto de "Cargando biblioteca de anime"
    loading_label = tk.Label(loading_frame, text="Cargando biblioteca de anime", font=("Helvetica", 24), bg="#ECF0F1")
    loading_label.pack(pady=20)

    # Cargar y mostrar el GIF con todos los frames
    gif_image = Image.open("../../resources/images/utils/loading-image.gif")
    gif_frames = [ImageTk.PhotoImage(frame.copy()) for frame in ImageSequence.Iterator(gif_image)]
    loading_image_label = tk.Label(loading_frame, bg="#ECF0F1")
    loading_image_label.pack(pady=20)

    # Función para animar el GIF
    def update_gif(frame=0):
        loading_image_label.config(image=gif_frames[frame])
        frame = (frame + 1) % len(gif_frames)  # Continuar en bucle
        root.after(100, update_gif, frame)  # Controla la velocidad de cambio de frame (100 ms)

    update_gif()  # Iniciar la animación

    # Iniciar la descarga de imágenes en un hilo
    threading.Thread(target=download_images_and_show_animes, daemon=True).start()

def download_images_and_show_animes():
    global recent_animes
    recent_animes = animeflv_api.get_recent_animes()
    download_images()  # Descargar imágenes
    show_animes_recientes()  # Mostrar animes recientes al finalizar la descarga

def show_animes_recientes():
    # Eliminar la pantalla de carga
    loading_frame.place_forget()  # Usar place_forget para ocultar el frame

    # Mostrar el sidebar ahora que ha terminado la descarga
    sidebar.pack(side=tk.LEFT, fill=tk.Y)

    # Mostrar el contenido de animes recientes
    clear_frame()
    display_recent_animes()

def show_favorites():
    global active_tab
    active_tab = "favorites"
    clear_frame()
    favorites_label = tk.Label(main_frame, text="Mis animes favoritos", font=("Helvetica", 16))
    favorites_label.pack(pady=20)

def show_finished_animes():
    global active_tab
    active_tab = "finalizados"
    clear_frame()
    recent_label = tk.Label(main_frame, text="Mis animes finalizados", font=("Helvetica", 16))
    recent_label.pack(pady=20)

def show_watching_animes():
    global active_tab
    active_tab = "viendo"
    clear_frame()
    recent_label = tk.Label(main_frame, text="Los animes que estoy viendo", font=("Helvetica", 16))
    recent_label.pack(pady=20)

def show_pending_animes():
    global active_tab
    active_tab = "pendientes"
    clear_frame()
    recent_label = tk.Label(main_frame, text="Mis animes pendientes", font=("Helvetica", 16))
    recent_label.pack(pady=20)

def show_buscador():
    global active_tab
    active_tab = "buscador"
    clear_frame()
    recent_label = tk.Label(main_frame, text="Buscador de animes", font=("Helvetica", 16))
    recent_label.pack(pady=20)


def download_images():
    if not os.path.exists(images_path):
        os.makedirs(images_path)  # Crear la carpeta si no existe

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


def on_anime_click(anime_id):
    """Función que se ejecuta al hacer clic en un anime."""
    anime_info = animeflv_api.get_anime_info(anime_id)

    # Limpiar el main_frame
    clear_frame()

    # Cargar la portada del anime
    image_path = os.path.join(images_path, f"{anime_info.id}.jpg")
    anime_image = load_image(image_path)

    # Crear un frame para la imagen y la información
    info_frame = tk.Frame(main_frame)
    info_frame.pack(pady=10)

    # Mostrar la portada en la parte superior izquierda
    image_label = tk.Label(info_frame, image=anime_image)
    image_label.image = anime_image  # Evitar que el garbage collector elimine la imagen
    image_label.grid(row=0, column=0, rowspan=3, padx=10)

    # Título centrado a la derecha de la imagen
    title_label = tk.Label(
        info_frame,
        text=anime_info.title,
        font=("Helvetica", 24, "bold"),
        wraplength=main_frame.winfo_width() - 200
    )
    title_label.grid(row=0, column=1, sticky="w", padx=(10, 50))

    # Géneros debajo del título
    genres_label = tk.Label(
        info_frame,
        text="Géneros: " + ", ".join(anime_info.genres),
        font=("Helvetica", 14)
    )
    genres_label.grid(row=1, column=1, sticky="w", padx=10)


    # Sinopsis en el frame principal, ocupando todo el ancho
    description_title_label = tk.Label(
        main_frame,
        text="Descripción",
        font=("Helvetica", 16, "bold")
    )
    description_title_label.pack(anchor="w", pady=(30, 5), padx=10)

    description_label = tk.Label(
        main_frame,
        text=anime_info.synopsis,
        font=("Helvetica", 14),
        wraplength=main_frame.winfo_width() - 25,
        justify="left",
        anchor="w"
    )
    description_label.pack(pady=5, padx=10)


    # Episodios debajo de la sinopsis, alineados a la izquierda
    episodes_label = tk.Label(
        main_frame,
        text="Lista de episodios",
        font=("Helvetica", 16, "bold")
    )
    episodes_label.pack(anchor="w", pady=(30, 5), padx=10)

    for episode in anime_info.episodes:
        episode_button = tk.Button(
            main_frame,
            text=f"{anime_info.title} episodio {episode.id}",
            font=("Helvetica", 14),
            command=lambda episode_info=episode: open_episode(episode_info),
        )
        episode_button.pack(pady=5, padx=20)



def open_episode(episode_info):
    """Función para abrir el enlace del episodio en el navegador."""
    servers_info = animeflv_api.get_anime_episode_video_servers(episode_info.anime, episode_info.id)
    webbrowser.open(servers_info[0].url)

def display_recent_animes():
    clear_frame()
    num_columns = max(1, (root.winfo_width() - 250) // 150)  # Calcula el número de columnas

    # Configurar que las columnas tengan el mismo peso y estén centradas
    for col in range(num_columns):
        main_frame.grid_columnconfigure(col, weight=1)

    for index, anime in enumerate(recent_animes):
        row = index // num_columns
        column = index % num_columns

        # Cargar la imagen desde el archivo en lugar de la URL
        img_file = f"{anime.id}.jpg"
        image = load_image(os.path.join(images_path, img_file))

        img_label = tk.Label(main_frame, image=image)
        img_label.image = image  # Mantener una referencia a la imagen
        img_label.grid(row=row * 2, column=column, padx=10, pady=(20, 0), sticky="nsew")  # Posicionar con relleno
        img_label.bind("<Button-1>", lambda e, anime_id=anime.id: on_anime_click(anime_id))

        # Título del anime
        title_label = tk.Label(main_frame, text=anime.title, font=("Helvetica", 10, "bold"), wraplength=130, justify="center")
        title_label.grid(row=(row * 2) + 1, column=column, padx=10, pady=(0, 10), sticky="n")  # Posicionar con relleno

        title_label.bind("<Button-2>", lambda e, anime_id=anime.id: on_anime_click(anime_id))

def load_image(image_path: str):
    if os.path.exists(image_path):
        return ImageTk.PhotoImage(Image.open(image_path))
    return ImageTk.PhotoImage(Image.new('RGB', (130, 185), (200, 200, 200)))  # Placeholder

def clear_frame():
    for widget in main_frame.winfo_children():
        widget.destroy()

animeflv_api = AnimeFLV()

images_path = "../../resources/images/recent_animes/"
recent_animes = []

# Crear la ventana principal
root = tk.Tk()
root.title("Mi Biblioteca de Anime")
root.geometry("1185x850")
# root.minsize(570, 500)  # Establecer el tamaño mínimo de la aplicación

# Crear el marco izquierdo (barra lateral)
sidebar = tk.Frame(root, width=200, bg="#2C3E50")

# Título en la barra lateral
title_label = tk.Label(sidebar, text="Biblioteca de Anime", bg="#2C3E50", fg="white", font=("Helvetica", 18))
title_label.pack(pady=20, padx=10)

# Botones en la barra lateral
home_button = tk.Button(sidebar, text="ANIMES RECIENTES", command=show_animes_recientes, bg="#34495E", fg="white", padx=20, pady=5)
home_button.pack(fill=tk.X, padx=20, pady=10)

favorites_button = tk.Button(sidebar, text="ANIMES FAVORITOS", command=show_favorites, bg="#34495E", fg="white", padx=10, pady=5)
favorites_button.pack(fill=tk.X, padx=20, pady=10)

finished_button = tk.Button(sidebar, text="ANIMES FINALIZADOS", command=show_finished_animes, bg="#34495E", fg="white", padx=10, pady=5)
finished_button.pack(fill=tk.X, padx=20, pady=10)

watching_button = tk.Button(sidebar, text="ANIMES VIENDO", command=show_watching_animes, bg="#34495E", fg="white", padx=10, pady=5)
watching_button.pack(fill=tk.X, padx=20, pady=10)

pending_button = tk.Button(sidebar, text="ANIMES PENDIENTES", command=show_pending_animes, bg="#34495E", fg="white", padx=10, pady=5)
pending_button.pack(fill=tk.X, padx=20, pady=10)

recent_button = tk.Button(sidebar, text="BUSCADOR DE ANIMES", command=show_buscador, bg="#34495E", fg="white", padx=10, pady=5)
recent_button.pack(fill=tk.X, padx=20, pady=10)

# Crear el marco derecho (área principal)
main_canvas = tk.Canvas(root, bg="#ECF0F1")
main_frame = tk.Frame(main_canvas, bg="#ECF0F1")

# Crear una barra de desplazamiento
scrollbar = tk.Scrollbar(root, orient="vertical", command=main_canvas.yview)
main_canvas.configure(yscrollcommand=scrollbar.set)

scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
main_canvas.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
main_canvas.create_window((0, 0), window=main_frame, anchor="nw")

# Actualizar el tamaño del canvas para permitir el desplazamiento
main_frame.bind("<Configure>", lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all")))

# Mostrar la pantalla de carga al inicio
show_loading_screen()
# root.resizable(True, True)

# Iniciar el bucle principal
root.mainloop()
