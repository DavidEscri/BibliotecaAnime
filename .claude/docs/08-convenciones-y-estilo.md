# 08 — Convenciones y estilo

| | |
|---|---|
| **Fecha** | 2026-07-28 · **Commit** `a972850` · árbol **sucio** |
| **Cubre** | los 19 módulos con contenido de `src/` |

Procedencia: ✅ verificado en ejecución · 📖 leído en código · ⚠️ sin verificar.

> No hay linter ni formateador configurados. Estas convenciones se cumplen **por costumbre**, no por
> herramienta. Si las rompes, nadie te avisará.

---

## 1. Cabecera de módulo — **obligatoria**

📖 Presente en los 19 módulos con contenido. Plantilla copiable:

```python
__author__ = "Jose David Escribano Orts"
__subsystem__ = "<subsistema>"
__module__ = "<nombre_fichero.py>"
__version__ = "0.1"
__info__ = {"subsystem": __subsystem__, "module_name": __module__, "version": __version__}
```

Si el módulo necesita explicación de fondo, el **docstring va antes** de la cabecera
(`models.py:1-11`, `animeav1.py:1-13`).

### Valores reales de `__subsystem__` en uso

📖 Inventario completo:

| `__subsystem__` | Módulos |
|---|---|
| `main` | `app.py` |
| `APIs.models` | `models.py` |
| `APIs.common` | `animeProviderMgr.py` |
| `APIs.animeav1` | `animeav1.py` |
| `APIs.animeflv` | `animeflv.py` |
| `DataPersistence` | `animesPersistence.py` |
| `utils` | `utils.py` |
| `utils.db` | `sqlite.py` |
| `utils.buttons` | `utilsButtons.py` |
| `gui` | `main_window.py`, `anime_window.py` |
| `sidebarButtons` | las 6 vistas |

⚠️ **No es sistemático**: `models.py` usa `APIs.models` (no `APIs.common`) aunque vive en
`APIs/common/`, y `animesPersistence` usa `DataPersistence` con mayúscula inicial mientras el resto
va en minúscula. Al añadir un módulo, **copia el `__subsystem__` de su vecino de carpeta**.

⚠️ **Erratas reales en `__module__`** — no las propagues, pero tampoco las «arregles» sin pensar:

| Fichero | Declara | Debería |
|---|---|---|
| `gui/anime_window.py:3` | `"anime_wnidow.py"` | `anime_window.py` |
| `APIs/common/animeProviderMgr.py:3` | `"animeProvider.py"` | `animeProviderMgr.py` |
| `dataPersistence/animesPersistence.py:3` | `"animesPersistence"` | falta `.py` |

---

## 2. Idioma

📖 Regla observada sin excepciones:

| Elemento | Idioma |
|---|---|
| Nombres de clase, función, variable, módulo | **inglés** (`get_recent_animes`, `watched_episodes`) |
| Comentarios y docstrings | **español con tildes** |
| Textos de UI | **español con tildes** (`"Añadir a favoritos"`, `"Buscar episodio..."`) |
| Mensajes de `print` | **español con tildes** |

**Excepción deliberada**: los miembros de `AnimeGenreFilter` y `AnimeOrderFilter` van en **español
con tildes** (`ACCIÓN`, `CIENCIA_FICCIÓN`, `ALFABÉTICAMENTE`) porque son vocabulario de dominio; su
*valor* es el slug ASCII (`"accion"`). 📖 `models.py:18-71`.

⚠️ Restos en inglés: los docstrings de `animeflv.py:71-76,120-126` y el de `utils.py:25-32`.

---

## 3. Métodos privados: name mangling `__`

📖 Prefijo `__` (doble guion bajo) para lo privado; `_` simple para lo «protegido» dentro de la capa
de persistencia (`_set_status`, `_update_flag`, `_query_by_status`, `_episodes_to_ranges`).

**Consecuencia práctica del mangling**: `self.__x` dentro de `class Foo` se almacena como
`_Foo__x`. Por eso, para leer un privado desde fuera (p. ej. depurando) hace falta el nombre
mangleado:

```python
main_window._MainWindow__recent_animes_button   # main_window.py:51
```

⚠️ **Trampa de herencia**: si defines `self.__episodes_frame` en una subclase de `SidebarButton`, el
atributo se llama `_TuClase__episodes_frame`. Cada vista tiene el suyo, aislado — por eso las 4 vistas
de estado pueden declarar el mismo nombre sin pisarse.

---

## 4. Patrón Singleton

📖 4 singletons en el proyecto. **No son singletons clásicos**: la clase envoltorio devuelve en
`__new__` una instancia de **otra** clase.

```python
class AnimesPersistenceSingleton:
    __instance: Optional[AnimesPersistence] = None

    def __new__(cls) -> AnimesPersistence:      # ← devuelve AnimesPersistence, NO el wrapper
        if cls.__instance is None:
            cls.__instance = AnimesPersistence()
        return cls.__instance
```

**Por eso se anotan con el tipo real**, nunca con el del wrapper:

```python
self.animes_persistence:   AnimesPersistence   = AnimesPersistenceSingleton()
self.anime_provider_mgr:   AnimeProviderManager = AnimeProviderManagerSingleton()
```

| Wrapper | Devuelve | Línea |
|---|---|---|
| `AnimeFLVSingleton` | `AnimeFLV` | `animeflv.py:239-245` |
| `AnimeAV1Singleton` | `AnimeAV1` | `animeav1.py:361-367` |
| `AnimesPersistenceSingleton` | `AnimesPersistence` | `animesPersistence.py:497-503` |
| `AnimeProviderManagerSingleton` | `AnimeProviderManager` | `animeProviderMgr.py:277-283` |

⚠️ Dos estilos conviven: `animeflv.py` y `animeav1.py` usan
`if NombreSingleton.__instance is None` (nombre de clase explícito); los otros dos usan
`if cls.__instance is None`. Ambos funcionan; **copia el del vecino**.

⚠️ **No son thread-safe**: dos hilos podrían crear dos instancias. En la práctica todos se
instancian antes de lanzar hilos.

---

## 5. Type hints

📖 Se **mezclan** dos estilos, deliberadamente o no:

```python
from typing import List, Optional, Union, Dict, Set, Tuple, Any, Callable

def get_anime_info(self, anime_id: Union[str, int]) -> AnimeInfo | None:   # ambos en una firma
```

- `typing.List/Optional/Union/Dict/Set/Tuple` — mayoritario.
- Sintaxis 3.10 (`X | None`) — en `animeflv.py:179`, `animeav1.py:177`, `main_window.py:51-56`,
  `searchAnimes.py:41-42`.
- `tuple[int, int]` en minúscula — `utils.py:166,179`.

**El proyecto requiere Python 3.10+.** ✅ Entorno verificado: `biblio_anime_env` usa **Python 3.10.6**.

⚠️ Anotaciones incorrectas que conviven con el código: `sqlite.py:48` declara `-> (bool, list)`, que
en Python es una **tupla literal**, no un tipo. No lo copies; usa `Tuple[bool, list]`.

---

## 6. Logging: `print`, y nada más

📖 No hay `logging` en ningún módulo. Convenciones observadas:

```python
print(f"Error al descargar el poster de {anime.id}: {e}")          # utils.py:90
print(f"[{provider.PROVIDER_ID}] Fallo en '{method_name}': {exc}")  # animeProviderMgr.py:228
print(f"{self.anime_info.title} añadido a favoritos.")              # anime_window.py:223
```

- Errores: `f"Error al <acción>: {excepción}"`.
- Proveedores: prefijo `[{PROVIDER_ID}]`.
- Acciones del usuario: frase afirmativa en pasado.

⚠️ **Consecuencia de empaquetar**: `MiBibliotecaAnime.spec:60` fija `console=False`, así que en el
`.exe` **todos estos `print` se pierden**. Depurar el ejecutable requiere cambiar temporalmente a
`console=True`.

---

## 7. Plantillas copiables

### 7.1 Módulo nuevo

```python
"""
(Opcional) Explicación de fondo: por qué existe este módulo y qué decisión no obvia encapsula.
"""
__author__ = "Jose David Escribano Orts"
__subsystem__ = "<copia el de tu carpeta vecina>"
__module__ = "<nombre_fichero.py>"
__version__ = "0.1"
__info__ = {"subsystem": __subsystem__, "module_name": __module__, "version": __version__}

import os
from typing import List, Optional

from APIs.common.models import AnimeInfo          # imports absolutos con raíz en src/
```

### 7.2 Vista de sidebar nueva

Crea `src/gui/sidebarButtons/<vista>/__init__.py` **vacío** y `<vista>.py`:

```python
__author__ = "Jose David Escribano Orts"
__subsystem__ = "sidebarButtons"
__module__ = "miVista.py"
__version__ = "0.1"
__info__ = {"subsystem": __subsystem__, "module_name": __module__, "version": __version__}

import os
import time
from typing import List, Union, Optional

import customtkinter as ctk

from APIs.common.models import AnimeInfo
from APIs.common.animeProviderMgr import AnimeProviderManager, AnimeProviderManagerSingleton
from dataPersistence.animesPersistence import (AnimesPersistence, AnimesPersistenceSingleton,
                                               AnimeStatus, AnimeRecord)
from gui.anime_window import AnimeWindowViewer
from utils.buttons import utilsButtons
from utils.utils import load_image, get_resource_path


class MiVistaButton(utilsButtons.SidebarButton):
    def __init__(self, main_window, icon_path, row, column):
        icon_path_light = icon_path_dark = os.path.join(icon_path, "mi_icono.png")
        super().__init__(main_window.sidebar_frame, "MI VISTA", row, column,
                         self.show_mi_vista, icon_path_light, icon_path_dark)
        self.main_window = main_window
        self.anime_provider_mgr: AnimeProviderManager = AnimeProviderManagerSingleton()
        self.animes_persistence: AnimesPersistence = AnimesPersistenceSingleton()
        self.__episodes_frame: ctk.CTkFrame = None

    def show_frame(self):
        """Punto de entrada programático (lo llama MainWindow)."""
        self.main_window.clear_frame()
        self.show_mi_vista()

    def show_mi_vista(self):
        self.main_window.clear_frame()
        time.sleep(0.1)   # patrón heredado — ver 07-concurrencia-e-hilos.md §5 antes de copiarlo
        self.__display_animes(self.animes_persistence.get_favourite_animes())

    def __display_animes(self, animes: List[AnimeRecord]):
        if self.__episodes_frame is not None and self.__episodes_frame.winfo_exists():
            for widget in self.__episodes_frame.winfo_children():
                widget.destroy()
            self.__episodes_frame.destroy()
        self.__episodes_frame = ctk.CTkFrame(self.main_window.content_frame)
        self.__episodes_frame.grid(row=5, column=0, padx=10, pady=10, sticky=ctk.EW)

        num_columns = max(1, self.main_window.content_frame.winfo_width() // 150)
        for index, anime_record in enumerate(animes):
            row, column = index // num_columns, index % num_columns
            image = load_image(get_resource_path(
                f"resources/images/<categoria>/{anime_record.anime_id}.jpg"))
            img_label = ctk.CTkLabel(self.__episodes_frame, text="", image=image)
            img_label.grid(row=row * 2, column=column, padx=10, pady=(20, 0), sticky=ctk.NSEW)
            img_label.bind("<Button-1>",
                           lambda e, anime_id=anime_record.anime_id: self.__on_anime_click(anime_id))

            title_label = ctk.CTkLabel(self.__episodes_frame, text=anime_record.title,
                                       font=ctk.CTkFont(size=14), wraplength=120, justify="center")
            title_label.grid(row=(row * 2) + 1, column=column, padx=10, pady=(5, 10), sticky=ctk.N)

    def __on_anime_click(self, anime_id: Union[str, int]):
        anime_clicked: AnimeInfo | None = self.anime_provider_mgr.get_anime_info(anime_id)
        if anime_clicked is None:          # ← el original NO comprueba esto; hazlo tú
            print(f"No se pudo obtener la información del anime {anime_id}")
            return
        AnimeWindowViewer(self.main_window, anime_clicked).display_anime_info()
```

Registro en `gui/main_window.py:130-135`:

```python
self.__mi_vista_button: MiVistaButton = MiVistaButton(self, icon_path, sidebar_button_row + 7,
                                                      sidebar_button_column)
```

⚠️ La fila 8 la ocupa `appearance_mode_label` (`main_window.py:142`) y la 9 el `CTkOptionMenu`
(`:149`). Si añades una séptima vista, **desplaza esos dos**.

### 7.3 Proveedor nuevo

```python
"""
(Si el sitio tiene alguna particularidad de parseo —framework JS, payload embebido, API oculta—,
explícala aquí. Es lo primero que leerá quien tenga que arreglarlo cuando se rompa.)
"""
__author__ = "Jose David Escribano Orts"
__subsystem__ = "APIs.misitio"
__module__ = "misitio.py"
__version__ = "0.1"
__info__ = {"subsystem": __subsystem__, "module_name": __module__, "version": __version__}

import re
import time
from typing import List, Optional, Union, Tuple

import requests
from bs4 import BeautifulSoup
from urllib.parse import urlencode, urlparse, parse_qs

from utils.utils import removeprefix
from APIs.common.animeProviderMgr import AnimeProvider
from APIs.common.models import AnimeGenreFilter, AnimeOrderFilter, ServerInfo, EpisodeInfo, AnimeInfo

BASE_URL = "https://misitio.com"

# Solo si los slugs del sitio NO coinciden con los de AnimeGenreFilter:
_GENRE_MAP = {AnimeGenreFilter.ACCIÓN: "action", AnimeGenreFilter.AVENTURA: "adventure"}


class MiSitio(AnimeProvider):
    PROVIDER_ID = "misitio"
    PROVIDER_NAME = "MiSitio"
    BASE_URL = BASE_URL

    def search_animes_by_genres_and_order(self, genres: List[AnimeGenreFilter], order: str = None,
                                          page: int = None) -> Tuple[List[AnimeInfo], int]:
        raise NotImplementedError

    def search_animes_by_query(self, query: str = None,
                               page: int = None) -> Tuple[List[AnimeInfo], int]:
        raise NotImplementedError

    def get_anime_episode_servers(self, anime_id: str, episode_id: int) -> List[ServerInfo]:
        raise NotImplementedError

    def get_recent_animes(self) -> List[AnimeInfo]:
        raise NotImplementedError

    def get_anime_info(self, anime_id: Union[str, int]) -> AnimeInfo | None:
        raise NotImplementedError


class MiSitioSingleton:
    __instance = None

    def __new__(cls):
        if MiSitioSingleton.__instance is None:
            MiSitioSingleton.__instance = MiSitio()
        return MiSitioSingleton.__instance
```

> ✅ **Los 3 atributos de clase son obligatorios ya en el esqueleto**: sin ellos, el módulo
> **no importa** (`NotImplementedError` desde `__init_subclass__`).

> ⚠️ **Fija la codificación** si el sitio no envía `charset` — es el bug real de AnimeAV1
> ([05 §7](05-proveedores-y-scraping.md)):
> ```python
> response = requests.get(url, timeout=10)
> response.encoding = response.apparent_encoding or "utf-8"
> soup = BeautifulSoup(response.text, "html.parser")
> ```

---

## 8. Estructura de carpetas

📖 Convención observada: **una carpeta por vista y por proveedor**, con un `__init__.py` **vacío** y
un módulo del mismo nombre que la carpeta.

```
src/APIs/<sitio>/__init__.py        ← vacío
src/APIs/<sitio>/<sitio>.py
src/gui/sidebarButtons/<vista>/__init__.py   ← vacío
src/gui/sidebarButtons/<vista>/<vista>.py
```

⚠️ **Deja los `__init__.py` vacíos.** `watchingAnimes/__init__.py` contiene un stub
`class WatchingAnimeButton: pass` que es código muerto y una trampa
([10, trampa 19](10-invariantes-y-trampas.md)).
