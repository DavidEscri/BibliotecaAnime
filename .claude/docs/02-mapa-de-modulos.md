# 02 — Mapa de módulos

| | |
|---|---|
| **Fecha** | 2026-07-30 · **Commit** `83a8448` · árbol **sucio** |
| **Última revisión** | 2026-07-30: fichas de `animeav1.py` (v0.3, `_fetch`), `anime_window.py` (`show_anime_info_error`) y `utils.py` (v0.2) tras `1bfdf0f`, `94b497e` y `83a8448` |
| **Cubre** | los 34 ficheros `.py` de `src/` (18 con contenido + 16 `__init__.py` vacíos) |

Procedencia: ✅ verificado en ejecución · 📖 leído en código · ⚠️ sin verificar.
Todas las líneas citadas corresponden al **árbol de trabajo actual**, no al último commit.

---

## Inventario

| Ruta | Líneas | Capa |
|---|---:|---|
| `src/app.py` | 17 | arranque |
| `src/APIs/common/models.py` | 93 | dominio |
| `src/APIs/common/animeProviderMgr.py` | 283 | dominio |
| `src/APIs/animeav1/animeav1.py` | 366 | infraestructura |
| `src/APIs/animeflv/animeflv.py` | 245 | infraestructura |
| `src/dataPersistence/animesPersistence.py` | 552 | dominio/datos |
| `src/utils/db/sqlite.py` | 446 | infraestructura |
| `src/utils/utils.py` | 198 | infraestructura |
| `src/utils/buttons/utilsButtons.py` | 197 | GUI |
| `src/gui/main_window.py` | 258 | GUI |
| `src/gui/anime_window.py` | 514 | GUI |
| `src/gui/sidebarButtons/recentAnimes/recentAnimes.py` | 106 | GUI |
| `src/gui/sidebarButtons/favouriteAnimes/favouriteAnimes.py` | 138 | GUI |
| `src/gui/sidebarButtons/finishedAnimes/finishedAnimes.py` | 135 | GUI |
| `src/gui/sidebarButtons/watchingAnimes/watchingAnimes.py` | 137 | GUI |
| `src/gui/sidebarButtons/pendingAnimes/pendingAnimes.py` | 137 | GUI |
| `src/gui/sidebarButtons/searchAnimes/searchAnimes.py` | 342 | GUI |
| `src/gui/sidebarButtons/watchingAnimes/__init__.py` | 2 | **código muerto** |

Los otros 16 `__init__.py` están **vacíos** (0 bytes) y solo marcan paquete.

---

## `src/app.py`

**Responsabilidad**: punto de entrada. Nada más.
**API**: `main()` (`:9-14`) → instancia `MainWindow()` y llama a `mainloop()`.
**Entrantes**: nadie (es el script). **Salientes**: `gui.main_window.MainWindow` (`:7`).
**Efectos**: ninguno propio.

> 📖 Debe lanzarse **como script** (`python src/app.py`), lo que pone `src` en `sys.path`. Los
> imports del proyecto son absolutos con raíz en `src`, así que `python -m src.app` **no** funciona.

---

## `src/APIs/common/models.py`

**Responsabilidad**: única fuente de verdad de los tipos de dominio (`:1-6`).

| Símbolo | Línea | Detalle |
|---|---|---|
| `AnimeGenreFilter(Enum)` | `:18-65` | **40 miembros**. Valor = slug (`ACCIÓN = "accion"`) |
| `AnimeOrderFilter(Enum)` | `:68-71` | `POR_DEFECTO="default"`, `ALFABÉTICAMENTE="title"`, `CALIFICACIÓN="rating"` |
| `ServerInfo` | `:74-77` | `server: str`, `url: str` |
| `EpisodeInfo` | `:80-83` | `id: Union[str,int]`, `anime: str` |
| `AnimeInfo` | `:86-93` | `id`, `title`, `poster` + `synopsis=None`, `genres=None`, `episodes=None` |

**Entrantes**: proveedores, `animeProviderMgr`, `animesPersistence`, `utilsButtons`, todas las vistas.
**Salientes**: solo stdlib. **Efectos**: ninguno.

> 📖 Los tres campos opcionales de `AnimeInfo` valen `None` en los **listados** (recientes/búsqueda)
> y solo se rellenan al pedir `get_anime_info()`. ✅ Verificado en ambos proveedores.

---

## `src/APIs/common/animeProviderMgr.py`

**Responsabilidad**: contrato `AnimeProvider` (ABC) + registro y fallback (`AnimeProviderManager`).

### `AnimeProvider` (`:21-107`)

| Miembro | Línea |
|---|---|
| `PROVIDER_ID` / `PROVIDER_NAME` / `BASE_URL` | `:45` / `:48` / `:52` |
| `__init_subclass__` | `:54-64` — valida los 3 atributos |
| `search_animes_by_genres_and_order(genres, order=None, page=None) -> (List[AnimeInfo], int)` | `:66-70` |
| `search_animes_by_query(query=None, page=None) -> (List[AnimeInfo], int)` | `:72-75` |
| `get_anime_episode_servers(anime_id, episode_id) -> List[ServerInfo]` | `:77-80` |
| `get_recent_animes() -> List[AnimeInfo]` | `:82-85` |
| `get_anime_info(anime_id) -> AnimeInfo` | `:87-90` |
| `is_available(timeout=5.0) -> bool` | `:92-104` — `GET BASE_URL` |

> ✅ **Trampa**: la comprobación es `if ABC not in cls.__bases__` (`:59`). Como solo `AnimeProvider`
> lista `ABC` entre sus bases, **cualquier** subclase — incluida una clase base intermedia
> abstracta — debe definir los 3 atributos o `NotImplementedError` salta **al importar**.

### `AnimeProviderManager` (`:110-274`)

| Método | Línea | Nota |
|---|---|---|
| `register(provider, default=False)` | `:141-149` | el primero registrado queda por defecto aunque no lo pidas |
| `unregister(provider_id)` | `:151-154` | si era el default, pasa al siguiente registrado |
| `set_default` / `get_default_provider_id` | `:156-162` | `set_default` lanza `UnknownProviderError` |
| `get(provider_id=None)` | `:164-171` | lanza `UnknownProviderError` |
| `list_providers()` / `list_available_providers()` | `:173-178` | la segunda hace **una petición HTTP por proveedor** |
| `_ordered_providers(provider_id=None)` | `:180-191` | preferido primero, resto por orden de registro |
| `__is_empty_result(result)` | `:193-202` | `None`, `[]`, o `([], …)` cuentan como vacío |
| `call_with_fallback(...) -> (Any, Optional[str])` | `:204-242` | devuelve `(None, None)` si todos fallan |
| wrappers `get_recent_animes`, `get_anime_info`, `search_animes_by_query`, `search_animes_by_genres_and_order`, `get_anime_episode_servers` | `:250-274` | mismos nombres que el contrato + `provider_id=`, `strict=` |
| `AnimeProviderManagerSingleton` | `:277-283` | |

**Efectos**: red (indirecta, vía proveedores) + `print` de diagnóstico.
Semántica exacta y casos límite verificados: [05 §5](05-proveedores-y-scraping.md).

---

## `src/APIs/animeav1/animeav1.py` — proveedor **por defecto**

**Responsabilidad**: scraping de `animeav1.com` (SvelteKit). **v0.3** desde el 2026-07-30 (`94b497e`).
**Constantes**: `BASE_URL` `:28`, `CATALOG_URL=/catalogo` `:29`, `MEDIA_URL=/media` `:30`,
`_SVELTE_PAYLOAD_MARKER = "kit.start(app, element, {"` `:34`.

**Helper de módulo**: `_fetch(url, **kwargs) -> Response` `:37-56`. **Único punto del módulo que llama
a `requests.get`**; fuerza UTF-8 cuando el sitio no declara charset. Los 5 métodos de red pasan por él
— saltárselo reintroduce el mojibake ([05 §7](05-proveedores-y-scraping.md), trampa 14).

| Método público | Línea | Efecto de red |
|---|---|---|
| `search_animes_by_genres_and_order` | `:65-95` | `GET /catalogo?genre=…&page=N` |
| `search_animes_by_query` | `:97-125` | `GET /catalogo?search=…&page=N` |
| `get_anime_episode_servers` | `:127-159` | `GET /media/{slug}/{n}`, timeout 10 |
| `get_recent_animes` | `:161-175` | `GET /`, timeout 10 |
| `get_anime_info` | `:177-244` | `GET /media/{slug}`, timeout 5, **3 intentos** con `sleep(1)` |

**Helpers privados**: `__extract_svelte_payload` `:250-262` · `__parse_anime_cards` `:264-298` ·
`__get_last_page` `:300-312` · `__extract_genres` `:314-331` · `__count_episodes_from_dom` `:333-346` ·
`__apply_client_side_order` `:348-358`. Singleton `:361-367`.

**Salientes**: `utils.utils.removeprefix` (`:24`), `APIs.common.*`.
✅ Verificado: los 5 métodos funcionan. Detalle del payload en [05 §2](05-proveedores-y-scraping.md).

---

## `src/APIs/animeflv/animeflv.py` — fallback

**Responsabilidad**: scraping de `www3.animeflv.net` con selectores CSS clásicos.
**Constantes**: `BASE_URL` `:21`, `BROWSE_URL=/browse` `:22`, `ANIME_VIDEO_URL=/ver/` `:23`,
`ANIME_URL=/anime` `:24`.

| Método público | Línea | Estado ✅ 2026-07-28 |
|---|---|---|
| `search_animes_by_genres_and_order` | `:33-68` | OK (24 res., `last_page=79`) |
| `search_animes_by_query` | `:70-117` | OK (12 res. para «naruto») |
| `get_anime_episode_servers` | `:119-147` | **devuelve `[]`** — el marcador `var videos = {` ya no aparece |
| `get_recent_animes` | `:149-177` | OK (24 res.) |
| `get_anime_info` | `:179-236` | OK (1167 eps. para `one-piece-tv`) |

Singleton `:239-245`. El usuario confirma que el sitio está **caído / en desuso**; no se invierte más
esfuerzo en diagnosticarlo.

> ✅ **Asimetría real de pósters**: `get_recent_animes` `:174` y `get_anime_info` `:197` **prefijan**
> `BASE_URL` al `src`; las dos búsquedas (`:65`, `:114`) **no**. Es correcto: en la portada el `src`
> es relativo y en `/browse` es absoluto.

---

## `src/dataPersistence/animesPersistence.py`

**Responsabilidad**: única puerta a la tabla `ANIMES`.

| Símbolo | Línea |
|---|---|
| `AnimeStatus(Enum)` | `:21-25` — el **valor** es el nombre de la columna |
| `AnimeField(Enum)` | `:28-55` — `(columna, tipo SQLite)`, props `.column` / `.sql_type` |
| `AnimeRecord` | `:62-201` |
| `AnimeRecord.to_db_dict()` | `:86-104` — **invierte `episodes`** (`:88`), comprime `watched` (`:89`) |
| `AnimeRecord.from_db_dict()` | `:110-146` — **no** deshace la inversión |
| `AnimeRecord.from_anime_info()` | `:152-172` |
| `_episodes_to_ranges` / `_ranges_to_episodes` | `:178-192` / `:195-201` |
| `AnimesPersistence` | `:207-541` |
| `FIELDS` / `FIELD_TYPES` / `PRIMARY_KEY` | `:210-212` — derivados del enum |
| `SCHEMA: List[TableSchema]` | `:218-224` — **esquema declarado de la BD**; añadir una tabla = añadir un `TableSchema` |
| `start()` | `:233-245` — crea la BD si falta **y llama siempre a `validate_db_integrity()`** |
| `validate_db_integrity()` | `:247-273` — ✅ alinea la BD con `SCHEMA`; delega en `ServiceDB.validate_schema` |
| `get_anime_by_anime_id` / `get_watched_episodes` | `:276-285` / `:287-292` |
| `get_favourite/watching/pending/finished_animes` | `:294-308` |
| `get_anime_by_genre_and_order` | `:310-346` |
| `update_watched_episodes` | `:351-371` — **devuelve `False` si el anime no existe** |
| `update_anime_episodes` | `:373-381` — invierte con `[::-1]` (`:375`) |
| `update_anime_to_[not_]favourite/watching/finished/pending` | `:386-444` |
| `_query_by_status` / `_insert_anime` / `_update_flag` / `_set_status` | `:449-531` |
| `_create_db_animes()` | `:533-541` — crea **todas** las tablas de `SCHEMA` |
| `AnimesPersistenceSingleton` | `:547-552` |

**Efectos**: escribe en `resources/DB/DB_Animes.db`. **Salientes**: `APIs.common.models`,
`utils.db.sqlite.ServiceDB`, `utils.utils.get_resource_path`.
Todo verificado ✅ sobre una copia de la BD → [04](04-modelo-de-datos.md).

---

## `src/utils/db/sqlite.py`

**Responsabilidad**: capa mínima sobre `sqlite3` + **motor de migraciones de esquema**. Sin ORM, sin
pool; transacciones solo en las migraciones.

| Símbolo | Línea | Nota |
|---|---|---|
| `sqlite_affinity(declared_type) -> str` | `:18-40` | las 5 reglas de afinidad de SQLite; `VARCHAR(100)` y `VARCHAR(200)` → ambas `TEXT` |
| `TableSchema` | `:43-82` | esquema declarativo: `name`, `fields` **ordenados**, `primary_key`, `defaults` |
| `TableSchema.create_sql(table_name=None)` | `:73-82` | el parámetro permite crear la tabla temporal de la reconstrucción |
| `SqlUtils.insert_sql(sql, params) -> bool` | `:90-104` | conexión abierta y cerrada por llamada |
| `SqlUtils.update_sql(sql, params) -> bool` | `:106-120` | ✅ **devuelve `True` aunque no afecte a ninguna fila** |
| `SqlUtils.query_sql(sql, params, list_field) -> (bool, list)` | `:122-144` | mapea **por posición** `columna[i] → list_field[i]` |
| `SqlUtils.create_db(sql) -> bool` | `:146-160` | |
| `SqlUtils.execute_transaction(statements) -> bool` | `:162-192` | todo o nada, con `ROLLBACK`; usado por las migraciones |
| `SqlUtils.get_table_names()` | `:194-210` | tablas de usuario (excluye `sqlite_%`) |
| `SqlUtils.get_table_columns(table)` | `:212-225` | `[(columna, tipo_declarado)]` en **orden físico** |
| `SqlUtils.get_conn() -> Connection` | `:227-228` | sin uso en el proyecto 📖 |
| `ServiceDB.__init__(db_path)` | `:232-237` | crea el directorio padre si falta |
| `ServiceDB.create_table(...)` | `:239-253` | `CREATE TABLE IF NOT EXISTS`; API antigua, hoy sin llamantes |
| `ServiceDB.validate_schema(schemas, backup=True)` | `:255-292` | orquesta la migración y **re-verifica** al terminar |
| `ServiceDB.diff_table(schema)` | `:294-330` | `exists` · `missing` · `extra` · `retyped` · `reordered` · `needs_migration` |
| `ServiceDB.apply_table_migration(schema, diff)` | `:332-357` | elige `CREATE` / `ADD COLUMN` / reconstrucción |
| `ServiceDB.__rebuild_table(schema, diff)` | `:359-394` | tabla temporal → `INSERT…SELECT` **por nombre** → `DROP` → `RENAME` |
| `ServiceDB.backup_db()` | `:396-417` | `resources/DB/backups/<nombre>_<timestamp>.db` vía `Connection.backup` |
| `ServiceDB.validate_record(...)` | `:419-424` | |
| `ServiceDB.insert_record_db(...)` | `:426-446` | `"NULL"` literal → `NULL` sin bind (`:439`) |

> ⚠️ **Por qué el orden de `FIELDS` importa**: `query_sql` (`:131-137`) recorre la tupla de la fila por
> índice y le asigna el nombre de `list_field` en la **misma posición**. Como todas las consultas son
> `SELECT *`, si el orden de `AnimeField` deja de coincidir con el de las columnas físicas, los
> valores se asignan a claves equivocadas **sin ningún error**. ✅ Hoy coinciden — y desde el
> 2026-07-30 `validate_schema` lo **restaura** automáticamente si dejan de coincidir.

> 📌 `ServiceDB` es genérica: cualquier subclase futura obtiene las migraciones declarando su lista de
> `TableSchema` y llamando a `validate_schema()`.

---

## `src/utils/utils.py`

**Responsabilidad**: rutas de recursos, caché de pósters, descargas, helpers de texto.
**Constantes**: `_MAX_DOWNLOAD_WORKERS = 8` `:19`, `_REQUEST_TIMEOUT = 10` `:22`.

| Función | Línea | Efecto |
|---|---|---|
| `removeprefix(text, prefix_text)` | `:24-38` | ⚠️ **devuelve `None`** si los tipos difieren (falta `else`) |
| `refactor_genre_text(genre_text)` | `:41-45` | `capitalize()` + `-`/`_` → espacio |
| `update_gif(label, gif_frames, root, frame=0)` | `:48-51` | ⚠️ **código muerto y roto**: `root.after(100, update_gif, frame)` pasaría `frame` como `label`. Sin llamadas en `src/` |
| `download_anime_poster_by_status(status, anime)` | `:53-60` | red + disco → `resources/images/{status.name.lower()}/{id}.jpg`, `(130,185)` |
| `remove_anime_poster_by_status(status, anime)` | `:62-69` | borra ese fichero; si no existe, imprime y vuelve |
| `download_animes_poster(images_path, animes)` | `:71-105` | descarga las que faltan (8 hilos) y **purga huérfanas** `:97-105` |
| `download_images_progress(images_path, recent_animes, progress_bar, progress_label)` | `:107-163` | igual + progreso 90 %→100 % `:126`; **toca widgets Tk desde workers** |
| `get_anime_image(anime, image_size=(195,275)) -> CTkImage` | `:166-177` | busca en las **6** categorías `:168`; si no está en ninguna, la baja de la red `:176-177` |
| `load_image(image_path, image_size=(130,185))` | `:179-182` | placeholder gris si no existe |
| `get_resource_path(relative_path)` | `:185-199` | `sys._MEIPASS` si está congelado; si no, raíz calculada desde este fichero |

> ✅ **Los dos bugs que tenía `get_anime_image` están resueltos** (2026-07-30, `83a8448`): la lista de
> carpetas incluye ya `watching` (era B1) y la rama de red pasa `size=` (era A4, el póster salía a
> 20×20). Ver trampas [15 y 16](10-invariantes-y-trampas.md), que conservan el invariante vigente:
> **toda carpeta a la que escriba `download_anime_poster_by_status` debe estar en `:168`**, y todo
> `CTkImage` nuevo necesita `size=` explícito.

---

## `src/utils/buttons/utilsButtons.py`

| Clase | Línea | Rol |
|---|---|---|
| `BaseButton(ctk.CTkButton)` | `:14-21` | base de todos |
| `EpisodeButton` | `:24-34` | «{título} - Episodio {n}» |
| `SearchButton` | `:37-44` | ⚠️ **homónimo** del `SearchButton` de la sidebar (`searchAnimes.py:34`) |
| `ApplyFiltersButton` | `:47-54` | |
| `SidebarButton` | `:57-83` | base de las 6 vistas; `update_icon(mode)` `:78-80`; `show_frame()` abstracto `:82-83` |
| `AccordionFilterButton` | `:85-197` | filtro plegable de género + orden |

**Efectos**: lee iconos de disco (`load_image`), consulta la BD en `__apply_filters` (`:182-194`).

> ✅ **Bug**: `__apply_filters` (`:187`) pasa `self.selected_order.get()`, un **`str`**, a
> `get_anime_by_genre_and_order`, que compara contra el **enum** (`animesPersistence.py:294`). La
> comparación siempre es `True` → *return* temprano → **la ordenación por coincidencias de género
> nunca se aplica**. Trampa 6.

---

## `src/gui/main_window.py`

**Responsabilidad**: ventana raíz y **hub de estado compartido**. Composition root de proveedores.

**Estado público mutable** (`:58-64`) — quién lo muta en [06 §2](06-gui-y-vistas.md):
`recent_animes`, `favourite_animes`, `finished_animes`, `watching_animes`, `pending_animes`,
`last_search_instance`, `images_path`, `animes_persistence`, `anime_provider_mgr`,
`sidebar_frame`, `content_frame`.

| Método | Línea |
|---|---|
| `__init__` | `:40-69` — registra proveedores `:48-49`, `load_sidebar_buttons()` `:66`, `show_loading_screen()` `:69` |
| `clear_frame()` | `:89-91` — destruye los hijos de `content_frame` |
| `create_sidebar_frame` / `create_content_frame` | `:93-123` |
| `load_sidebar_buttons()` | `:125-151` — instancia las 6 vistas + selector de apariencia |
| `change_appearance_mode_event(mode)` | `:153-163` |
| `show_loading_screen()` | `:165-204` — GIF + barra; lanza el hilo daemon `:204` |
| `download_images_and_show_animes(...)` | `:206-224` — **hilo daemon** |
| `__preload_recent_animes_info()` | `:226-243` — **hilo daemon** |
| `load_animes(...)` | `:245-258` — BD, progreso 0→40 % |

**Efectos**: red, disco, BD, widgets Tk.

---

## `src/gui/anime_window.py`

**Responsabilidad**: `AnimeWindowViewer` — la ficha de detalle. **No es una ventana**: reemplaza el
contenido de `content_frame`.

**Función de módulo** (pública, la importan las 6 vistas):

| Función | Línea | Nota |
|---|---|---|
| `show_anime_info_error(anime_id)` | `:30-46` | `print` + `messagebox.showerror`. Se llama cuando `get_anime_info` devuelve `None`; sin ella, el clic no hacía nada (trampa 10) |

| Método | Línea | Nota |
|---|---|---|
| `__init__(main_window, anime_info)` | `:50-71` | **contrato**: `None` → `ValueError` `:51-54`; `episodes=None` → `replace(…, episodes=[])` sobre una copia `:58-59` |
| `display_anime_info()` | `:73-76` | punto de entrada |
| `__load_anime_status()` | `:78-92` | si cambió el nº de episodios, los actualiza en BD `:82-83` |
| `__display_anime_info()` | `:94-157` | póster + título + sinopsis + géneros |
| `__show_anime_status()` / `__display_anime_status()` | `:159-218` | los 4 botones de estado |
| `add_to_*` / `remove_from_*` | `:220-281` | BD + póster en disco + refresco |
| `__display_episodes(episodes_to_show=None)` | `:293-359` | **`[:25]`** en `:294` |
| `__toggle_sort_order` | `:382-392` | ordena `anime_info.episodes` **in place** |
| `__search_episodes` | `:394-408` | filtra por número exacto |
| `__previous_episode` / `__next_episode` | `:410-428` | |
| `__toggle_episode_switch(episode_id)` | `:430-483` | marcado **acumulativo**; desmarcado unitario |
| `__toggle_servers_frame` | `:485-510` | ⚠️ **HTTP en el hilo de UI** (`:490`) |
| `__play_video(url)` | `:512-513` | `webbrowser.open` |

---

## Las 5 vistas «de estado» + buscador

`recentAnimes.py`, `favouriteAnimes.py`, `finishedAnimes.py`, `watchingAnimes.py`,
`pendingAnimes.py` y `searchAnimes.py`. Patrón común y diferencias en
[06 §3](06-gui-y-vistas.md).

| Fichero | Clase | Carpeta de pósters | `AnimeStatus` |
|---|---|---|---|
| `recentAnimes.py` | `RecentAnimeButton` | `recent_animes` | — |
| `favouriteAnimes.py` | `FavouritesButton` | `favourite` | `FAVOURITE` |
| `finishedAnimes.py` | `FinishedAnimeButton` | `finished` | `FINISHED` |
| `watchingAnimes.py` | `WatchingAnimeButton` | `watching` | `WATCHING` |
| `pendingAnimes.py` | `PendingAnimeButton` | `pending` | `PENDING` |
| `searchAnimes.py` | `SearchButton` + `AnimeSearch` | `search` | — |

`recentAnimes.py` es la **única** que carga la ficha en un hilo secundario (`:90-102`) y la única con
`show_frame()` que revela la sidebar (`:31`).

`searchAnimes.py` añade `AnimeSearch` (`:24-31`, `dataclasses.dataclass` de la stdlib), paginación
(`:267-324`) y un frame de carga con GIF (`:170-215`).

---

## `src/gui/sidebarButtons/watchingAnimes/__init__.py` — **código muerto**

```python
class WatchingAnimeButton:
    pass
```

📖 Stub de 2 líneas. `main_window.py:25` importa desde
`gui.sidebarButtons.watchingAnimes.watchingAnimes`, así que **nunca se usa**. Pero un
`from gui.sidebarButtons.watchingAnimes import WatchingAnimeButton` importaría el stub y rompería en
tiempo de ejecución sin ningún error de importación. [Trampa 19](10-invariantes-y-trampas.md).
