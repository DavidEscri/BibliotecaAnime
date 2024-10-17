import threading
import tkinter as tk
from typing import List

from PIL import Image, ImageSequence, ImageTk

from APIs.animeflv.animeflv import AnimeFLVSingleton, AnimeFLV, AnimeInfo
from gui.sidebarButtons.favouriteAnimes.favouriteAnimes import FavouritesButton
from gui.sidebarButtons.finishedAnimes.finishedAnimes import FinishedAnimeButton
from gui.sidebarButtons.pendingAnimes.pendingAnimes import PendingAnimeButton
from gui.sidebarButtons.recentAnimes.recentAnimes import RecentAnimeButton
from gui.sidebarButtons.searchAnimes.searchAnimes import SearchButton
from gui.sidebarButtons.watchingAnimes.watchingAnimes import WatchingAnimeButton

from utils.utils import download_images, on_mousewheel


class MainWindow:
    def __init__(self, root):
        self.root = root
        self.root.config(bg='white')
        self.root.resizable(False, False)

        self.__recent_animes_button: RecentAnimeButton = None
        self.__favourites_animes_button: FavouritesButton = None
        self.__finished_animes_button: FinishedAnimeButton = None
        self.__watching_animes_button: WatchingAnimeButton = None
        self.__pending_animes_button: PendingAnimeButton = None
        self.__search_animes_button: SearchButton = None

        # Crear los frames
        self.loading_frame: tk.Frame | None = None
        self.sidebar_frame: tk.Frame = self.create_sidebar()
        self.content_frame: tk.Frame = self.create_content_frame()

        self.animeflv_api: AnimeFLV = AnimeFLVSingleton()
        self.recent_animes: List[AnimeInfo] = []
        self.images_path = "../../resources/images/recent_animes"

        self.load_buttons()

        # Inicia mostrando pantalla de carga
        self.show_loading_screen()

    def clear_frame(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def create_sidebar(self) -> tk.Frame:
        sidebar = tk.Frame(self.root, width=200, bg="#2C3E50")

        # Título en la barra lateral
        title_label = tk.Label(sidebar, text="Biblioteca de Anime", bg="#2C3E50", fg="white", font=("Helvetica", 18))
        title_label.pack(pady=20, padx=10)

        return sidebar

    def load_buttons(self) -> None:
        # Instanciar los botones
        self.__recent_animes_button: RecentAnimeButton = RecentAnimeButton(self)
        self.__favourites_animes_button: FavouritesButton = FavouritesButton(self)
        self.__finished_animes_button: FinishedAnimeButton = FinishedAnimeButton(self)
        self.__watching_animes_button: WatchingAnimeButton = WatchingAnimeButton(self)
        self.__pending_animes_button: PendingAnimeButton = PendingAnimeButton(self)
        self.__search_animes_button: SearchButton = SearchButton(self)

    def create_content_frame(self) -> tk.Frame:
        main_canvas = tk.Canvas(self.root, bg="#ECF0F1")
        main_frame = tk.Frame(main_canvas, bg="#ECF0F1")

        # Crear una barra de desplazamiento
        scrollbar = tk.Scrollbar(self.root, orient="vertical", command=main_canvas.yview)
        main_canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        main_canvas.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        main_canvas.create_window((0, 0), window=main_frame, anchor="nw")

        # Actualizar el tamaño del canvas para permitir el desplazamiento
        main_frame.bind("<Configure>", lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all")))
        main_canvas.bind_all("<MouseWheel>", lambda event: on_mousewheel(event, main_canvas))
        # Establecer grid en el main_frame
        main_frame.grid_rowconfigure(0, weight=1)  # Permitir que la primera fila se expanda
        main_frame.grid_columnconfigure(0, weight=1)  # Permitir que la primera columna se expanda
        return main_frame

    def show_loading_screen(self):
        self.sidebar_frame.pack_forget()
        self.loading_frame = tk.Frame(self.root, width=1200, height=850, bg="#ECF0F1")  # Tamaño fijo para centrarlo
        self.loading_frame.pack_propagate(False)

        # Centrar el frame
        x_position = (self.root.winfo_width())  # Centrar horizontalmente (ancho ventana - ancho frame) / 2
        y_position = (self.root.winfo_height() + 150)  # Centrar verticalmente (alto ventana - alto frame) / 2
        self.loading_frame.place(x=x_position, y=y_position)

        # Mostrar el texto de "Cargando biblioteca de anime"
        loading_label = tk.Label(self.loading_frame, text="Cargando biblioteca de anime", font=("Helvetica", 24),
                                 bg="#ECF0F1")
        loading_label.pack(pady=20)

        # Cargar y mostrar el GIF con todos los frames
        gif_image = Image.open("../resources/images/utils/loading-image.gif")
        gif_frames = [ImageTk.PhotoImage(frame.copy()) for frame in ImageSequence.Iterator(gif_image)]
        loading_image_label = tk.Label(self.loading_frame, bg="#ECF0F1")
        loading_image_label.pack(pady=20)

        def update_gif(frame=0):
            loading_image_label.config(image=gif_frames[frame])
            frame = (frame + 1) % len(gif_frames)  # Continuar en bucle
            self.root.after(100, update_gif, frame)  # Controla la velocidad de cambio de frame (100 ms)

        update_gif()  # Iniciar la animación

        # Iniciar la descarga de imágenes en un hilo
        threading.Thread(target=self.download_images_and_show_animes, daemon=True).start()

    def download_images_and_show_animes(self):
        self.recent_animes = self.animeflv_api.get_recent_animes()
        download_images(self.images_path, self.recent_animes)  # Descargar imágenes
        self.__recent_animes_button.show_frame()  # Mostrar animes recientes al finalizar la descarga