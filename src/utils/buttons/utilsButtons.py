import os
from PIL import Image
from utils.utils import load_image
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
        super().__init__(
            parent_frame,
            text=f"{anime_title} - Episodio {episode_info.id}",
            command=lambda: toggle_servers_command(episode_info, servers_frame, index),
            height=40,
            font=ctk.CTkFont(size=14),
            anchor=ctk.W,
            border_spacing=20
        )


class SearchButton(BaseButton):
    def __init__(self, parent_frame, search_command, search_entry):
        super().__init__(
            parent_frame,
            text="Buscar",
            command=lambda: search_command(search_entry),
            font=ctk.CTkFont(size=14)
        )


class ApplyFiltersButton(BaseButton):
    def __init__(self, parent_frame, apply_filter_command):
        super().__init__(
            parent_frame,
            text="Aplicar Filtros",
            command=apply_filter_command,
            font=ctk.CTkFont(size=14)
        )


class SidebarButton(BaseButton):
    def __init__(self, parent_frame, text, row, column, command, icon_path_light, icon_path_dark):
        self.icon_light = load_image(icon_path_light, image_size=(24, 24))
        self.icon_dark = load_image(icon_path_dark, image_size=(24, 24))
        current_icon = self.icon_dark if ctk.get_appearance_mode() == "Dark" else self.icon_light
        super().__init__(
            parent_frame,
            text=" " + text,
            font=ctk.CTkFont(size=14),
            width=parent_frame.winfo_width(),
            height=parent_frame.winfo_height() - 150,
            fg_color=parent_frame.cget("fg_color"),
            text_color="black",
            image=current_icon,
            compound="left",
            corner_radius=0,
            hover_color="white",
            command=command,
        )
        self.grid(row=row, column=column, sticky="nsew")

    def update_icon(self, mode):
        new_icon = self.icon_dark if mode == "Dark" else self.icon_light
        self.configure(image=new_icon)

    def show_frame(self):
        raise NotImplementedError("Subclasses must implement this method")