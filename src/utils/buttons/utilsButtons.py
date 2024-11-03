import webbrowser
import customtkinter as ctk

class BaseButton(ctk.CTkButton):
    def __init__(self, parent_frame, text, command, **kwargs):
        super().__init__(
            parent_frame,
            text=text,
            command=command,
            **kwargs
        )


class EpisodeButton(BaseButton):
    def __init__(self, parent_frame, anime_title, episode_info, servers_frame, index, toggle_servers_command):
        self.watched_episode = False
        super().__init__(
            parent_frame,
            text=f"{anime_title} - Episodio {episode_info.id}",
            command=lambda: toggle_servers_command(episode_info, servers_frame, index),
            height=40,
            font=ctk.CTkFont(size=14),
            anchor=ctk.W,
            border_spacing=20
        )

    def is_watched(self):
        #TODO: De alguna manera se debe persistir que el episodio ya ha sido visto. Indiferentemente de lo tenga en favoritos,
        # pendiente, terminado, mirando, etc. No hace falta ni que esté catalogado.
        return self.watched_episode

    def mark_as_watched(self):
        """Marcar el episodio como visto"""
        self.watched_episode = True

    def mark_as_unwatched(self):
        self.watched_episode = False

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
    def __init__(self, parent_frame, text, row, column, command):
        super().__init__(
            parent_frame,
            text=text,
            command=command,
        )
        self.grid(row=row, column=column, padx=20, pady=10)

    def show_frame(self):
        raise NotImplementedError("Subclasses must implement this method")