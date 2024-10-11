import tkinter as tk
import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageTk, ImageSequence
from io import BytesIO
import os
import webbrowser
import threading
import json


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

def show_buscador():
    global active_tab
    active_tab = "buscador"
    clear_frame()
    recent_label = tk.Label(main_frame, text="Buscador de animes", font=("Helvetica", 16))
    recent_label.pack(pady=20)

def fetch_recent_animes():
    response = requests.get(animeflv_url)
    soup = BeautifulSoup(response.text, 'html.parser')

    animes_list = []
    for anime in soup.select('ul.ListAnimes.AX.Rows.A06.C04.D03 li'):
        title = anime.find('h3', class_='Title').get_text(strip=True).replace(".", "").replace(":", "")
        img_src = anime.find('img')['src']
        animes_list.append((title, animeflv_url + img_src))

    return animes_list

def download_images():
    if not os.path.exists(images_path):
        os.makedirs(images_path)  # Crear la carpeta si no existe

    recent_animes_images = os.listdir(images_path)
    if len(recent_animes_images) > 0:
        for recent_anime in recent_animes_images:
            try:
                os.remove(os.path.join(images_path, recent_anime))
            except FileNotFoundError:
                continue

    for title, img_src in animes:
        # Normalizar el título para crear un nombre de archivo válido
        filename = f"{title}.jpg"
        try:
            response = requests.get(img_src)
            img_data = Image.open(BytesIO(response.content)).resize((130, 185))
            img_data.save(os.path.join(images_path, filename))  # Guardar la imagen
        except Exception as e:
            print(f"Error al descargar {title}: {e}")


def fetch_anime_details(title):
    """Obtiene detalles del anime desde la página web."""
    title = parse_title(title)
    url = f"https://www3.animeflv.net/anime/{title}"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    if response.status_code != 200:
        print(f"Error al acceder a la página: {response.status_code}")
        return [], "", []

    # Obtener género
    genres = [a.text for a in soup.select('section.WdgtCn nav.Nvgnrs a')]

    # Obtener descripción
    description = soup.select_one('section.WdgtCn div.Description p').text.strip()

    # Obtener capítulos
    episodes = []

    for script in soup.find_all("script"):
        contents = str(script)

        if "var episodes = [" in contents:
            data = contents.split("var episodes = ")[1].split(";")[0]
            episodes = [episode[0] for episode in json.loads(data)]
    #TODO: EPISODES TIENE QUE TENER UN TITULO Y UN ENLACE
    return genres, description, episodes[::-1]

def parse_title(anime_title: str) -> str:
    anime_title = anime_title.replace("!", "").replace("?", "").replace(",", "").replace("(", "").replace(")", "").replace("@", "").replace("½", "12").replace("-", "")
    return anime_title.replace(" ", "-").lower()

def on_anime_click(title):
    """Función que se ejecuta al hacer clic en un anime."""
    genres, description, episodes = fetch_anime_details(title)

    # Limpiar el main_frame
    clear_frame()

    # Mostrar información del anime
    title_label = tk.Label(main_frame, text=title, font=("Helvetica", 24, "bold"))
    title_label.pack(pady=10)

    genres_label = tk.Label(main_frame, text="Géneros: " + ", ".join(genres), font=("Helvetica", 12))
    genres_label.pack(pady=5)

    description_label = tk.Label(main_frame, text="Descripción: " + description, wraplength=600, justify="left")
    description_label.pack(pady=10)

    episodes_label = tk.Label(main_frame, text="Episodios:", font=("Helvetica", 16, "bold"))
    episodes_label.pack(pady=5)

    for episode_title, episode_link in episodes:
        episode_button = tk.Button(main_frame, text=episode_title, command=lambda link=episode_link: open_episode(link))
        episode_button.pack(pady=5)


def open_episode(link):
    """Función para abrir el enlace del episodio en el navegador."""
    webbrowser.open(link)

def display_recent_animes():
    clear_frame()
    num_columns = max(1, (root.winfo_width() - 250) // 150)  # Calcula el número de columnas

    # Configurar que las columnas tengan el mismo peso y estén centradas
    for col in range(num_columns):
        main_frame.grid_columnconfigure(col, weight=1)

    for index, (title, _) in enumerate(animes):
        row = index // num_columns
        column = index % num_columns

        # Cargar la imagen desde el archivo en lugar de la URL
        img_file = f"{title}.jpg"
        img_path = os.path.join(images_path, img_file)
        if os.path.exists(img_path):
            img = ImageTk.PhotoImage(Image.open(img_path))
        else:
            img = ImageTk.PhotoImage(Image.new('RGB', (130, 185), (200, 200, 200)))  # Placeholder

        img_label = tk.Label(main_frame, image=img)
        img_label.image = img  # Mantener una referencia a la imagen
        img_label.grid(row=row * 2, column=column, padx=10, pady=(20, 0), sticky="nsew")  # Posicionar con relleno
        img_label.bind("<Button-1>", lambda e, title=title: on_anime_click(title))

        # Título del anime
        title_label = tk.Label(main_frame, text=title, font=("Helvetica", 10, "bold"), wraplength=130, justify="center")
        title_label.grid(row=(row * 2) + 1, column=column, padx=10, pady=(0,10), sticky="n")  # Posicionar con relleno

        title_label.bind("<Button-2>", lambda e, title=title: on_anime_click(title))

def clear_frame():
    for widget in main_frame.winfo_children():
        widget.destroy()

animeflv_url = "https://animeflv.net"
images_path = "../../resources/images/recent_animes/"
animes = fetch_recent_animes()

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

favorites_button = tk.Button(sidebar, text="FAVORITOS", command=show_favorites, bg="#34495E", fg="white", padx=10, pady=5)
favorites_button.pack(fill=tk.X, padx=20, pady=10)

recent_button = tk.Button(sidebar, text="BUSCADOR", command=show_buscador, bg="#34495E", fg="white", padx=10, pady=5)
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
