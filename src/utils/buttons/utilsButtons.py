import webbrowser
import tkinter as tk

class BaseButton(tk.Button):
    def __init__(self, parent_frame, text, command, width=None, height=None, font=None, **kwargs):
        super().__init__(
            parent_frame,
            text=text,
            command=command,
            font=font,
            width=width,
            height=height,
            **kwargs
        )


class EpisodeButton(BaseButton):
    def __init__(self, parent_frame, anime_title, episode_info, servers_frame, index, toggle_servers_command):
        self.watched_episode = False
        text = f"{anime_title}\n\nEpisodio {episode_info.id}"
        super().__init__(
            parent_frame,
            text=text,
            command=lambda: toggle_servers_command(parent_frame, episode_info, servers_frame, index),
            width=50,
            height=4,
            font=("Helvetica", 14),
            anchor="w",
            justify="left"
        )

    def is_watched(self):
        #TODO: De alguna manera se debe persistir que el episodio ya ha sido visto. Indiferentemente de lo tenga en favoritos,
        # pendiente, terminado, mirando, etc. No hace falta ni que esté catalogado.
        return self.watched_episode

    def mark_as_watched(self):
        """Marcar el episodio como visto"""
        self.watched_episode = True
        self.configure(bg="#D3D3D3")

    def mark_as_unwatched(self):
        self.watched_episode = False
        self.configure(bg="SystemButtonFace")

class ServerButton(BaseButton):
    def __init__(self, parent_frame, server_info, episode_button: EpisodeButton):
        super().__init__(
            parent_frame,
            text=server_info.server,
            command=lambda: self.__play_video(server_info.url, episode_button),
            width=10,
            font=("Helvetica", 12)
        )

    def __play_video(self, url, episode_button: EpisodeButton):
        webbrowser.open(url)
        if episode_button.is_watched():
            episode_button.mark_as_unwatched()
        else:
            episode_button.mark_as_watched()


class SearchButton(BaseButton):
    def __init__(self, parent_frame, search_command, search_entry):
        super().__init__(
            parent_frame,
            text="Buscar",
            command=lambda: search_command(search_entry),
            width=25,
            font=("Helvetica", 9)
        )


class ApplyFiltersButton(BaseButton):
    def __init__(self, parent_frame, apply_filter_command):
        super().__init__(
            parent_frame,
            text="Aplicar Filtros",
            command=apply_filter_command,
            font=("Helvetica", 10)
        )


class SidebarButton(BaseButton):
    def __init__(self, parent_frame, text, command):
        super().__init__(
            parent_frame,
            text=text,
            command=command,
            bg="#34495E",
            fg="white",
            padx=20,
            pady=5
        )
        self.pack(fill=tk.X, padx=20, pady=10)

    def show_frame(self):
        raise NotImplementedError("Subclasses must implement this method")