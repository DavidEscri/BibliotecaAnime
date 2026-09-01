# 02 — Mapa de módulos

| | |
|---|---|
| **Fecha** | 2026-09-01 · rama `feature/ui-redisign` · último commit **`a0e3f37`** (**abrir la ficha por un episodio**); **sin commitear**, solo esta tanda de documentación |
| **Última revisión** | 2026-09-01 (**abrir la ficha por un episodio**): recuentos rehechos (**11 430 → 11 599**); `anime_window.py` **1 745 → 1 875** con `focus_episode` / `force_ascending` y sus dos métodos nuevos, `anime_row.py` **333 → 349** con la corrección de sus ataduras ([trampa 40](10-invariantes-y-trampas.md)), y las dos vistas de cascada. Antes, 2026-09-01 (**ancho de las fichas de género**): recuentos rehechos (**11 403 → 11 430**); `genre_chips.py` **333 → 360** con la aritmética real del ancho de un `CTkButton` ([trampa 39](10-invariantes-y-trampas.md)). Antes, 2026-09-01 (**refresco de la banda «Retomar»**): recuentos rehechos (**11 309 → 11 403**); `resume_card.py` estrena `update_record()` en sus **dos** clases y `recentAnimes.py`, `__refresh_resume_episodes()`; la tabla de «cómo abre la ficha» reanclada, que iba ~125 líneas desplazada. Antes, 2026-09-01 (**hover de la lista de episodios**): **ficha de `EpisodeRow` nueva** —no la tenía—, y recuentos rehechos con la convención del documento explicada. Antes, 2026-08-31 (**fondo de la pantalla de carga**): ficha de `MainWindow` reanclada —sus líneas iban ~29 desplazadas—, `show_loading_screen()` descrito de verdad y `__config_main_window()` añadido. Antes, 2026-08-21 (**rediseño de interfaz**): **12 módulos nuevos** en `gui/` —`theme.py` y los 11 de `gui/components/`— con su ficha; recuentos rehechos (**6 245 → 11 309** líneas); `utilsButtons.py` pierde 5 clases y `main_window.py` gana `navigate_to()`. Antes, 2026-08-16 (**columna `provider_id`**): recuentos rehechos — el proyecto pasa de 5 460 a **6 245** líneas; fichas de `models.py`, `animeProviderMgr.py`, `animesPersistence.py`, `utils.py`, `utilsButtons.py`, `main_window.py` y `anime_window.py` actualizadas |
| **Cubre** | los **50** ficheros `.py` de `src/` (**31** con contenido + **19** `__init__.py` vacíos) |

Procedencia: ✅ verificado en ejecución · 📖 leído en código · ⚠️ sin verificar.
Todas las líneas citadas corresponden al **árbol de trabajo actual**, no al último commit.

---

## Inventario

| Ruta | Líneas | Capa |
|---|---:|---|
| `src/app.py` | 17 | arranque |
| `src/APIs/common/models.py` | **130** | dominio |
| `src/APIs/common/animeProviderMgr.py` | **468** | dominio |
| `src/APIs/animeav1/animeav1.py` | 366 | infraestructura |
| `src/APIs/jkanime/jkanime.py` | 534 | infraestructura |
| `src/APIs/animeflv/animeflv.py` | 244 | infraestructura |
| `src/dataPersistence/animesPersistence.py` | **705** | dominio/datos |
| `src/dataPersistence/userPersistence.py` | **334** | dominio/datos |
| `src/utils/db/sqlite.py` | 446 | infraestructura |
| `src/utils/utils.py` | **304** | infraestructura |
| `src/utils/buttons/utilsButtons.py` | **205** | GUI |
| `src/gui/theme.py` 🆕 | **274** | GUI · tokens |
| `src/gui/components/sidebar.py` 🆕 | **525** | GUI · componente |
| `src/gui/components/anime_row.py` 🆕 | **349** | GUI · componente |
| `src/gui/components/genre_chips.py` 🆕 | **360** | GUI · componente |
| `src/gui/components/status_pill.py` 🆕 | **258** | GUI · componente |
| `src/gui/components/pager.py` 🆕 | **247** | GUI · componente |
| `src/gui/components/poster_grid.py` 🆕 | **234** | GUI · componente |
| `src/gui/components/empty_state.py` 🆕 | **232** | GUI · componente |
| `src/gui/components/resume_card.py` 🆕 | **229** | GUI · componente |
| `src/gui/components/side_panel.py` 🆕 | **226** | GUI · componente |
| `src/gui/components/rating_stars.py` 🆕 | **209** | GUI · componente |
| `src/gui/components/view_header.py` 🆕 | **99** | GUI · componente |
| `src/gui/main_window.py` | **545** | GUI |
| `src/gui/anime_window.py` | **1 875** | GUI |
| `src/gui/sidebarButtons/recentAnimes/recentAnimes.py` | **240** | GUI · vista |
| `src/gui/sidebarButtons/favouriteAnimes/favouriteAnimes.py` | **350** | GUI · vista |
| `src/gui/sidebarButtons/finishedAnimes/finishedAnimes.py` | **260** | GUI · vista |
| `src/gui/sidebarButtons/watchingAnimes/watchingAnimes.py` | **278** | GUI · vista |
| `src/gui/sidebarButtons/pendingAnimes/pendingAnimes.py` | **362** | GUI · vista |
| `src/gui/sidebarButtons/searchAnimes/searchAnimes.py` | **607** | GUI · vista |

**11 599 líneas** en **31 módulos**. ✅ Recontado el 2026-09-01 —`wc -l` **+ 1 por módulo**, que es la
convención con la que se contó en agosto: casi ningún fichero termina en salto de línea—. Las **169
últimas** son la apertura de la ficha por un episodio, repartidas en cuatro módulos:
`anime_window.py` **+130** (los dos métodos nuevos y sus dos constantes), `anime_row.py` **+16**
(ataduras corregidas, casi todo explicación de por qué), `watchingAnimes.py` **+14** y
`pendingAnimes.py` **+9**. Antes, **27** del ancho de las fichas de género (`genre_chips.py`) y **94**
del refresco de la banda «Retomar» (`recentAnimes.py` **+57**, `resume_card.py` **+37**).

Sin esa tanda daba **11 309**, la **misma cifra** que el 2026-08-21 pese a los 18 renglones ganados desde el
rediseño (`main_window.py` +7 con el fondo de la pantalla de carga, `anime_window.py` +11 con el hover de
los episodios), así que la cifra de agosto venía **18 alta**. Aquella se anotó el 2026-08-21 así: **+5 064 líneas** respecto al
2026-08-16, casi todas del rediseño de interfaz. El grueso está en los **12 módulos nuevos** de
`gui/` (2 962 líneas entre `theme.py` y los 11 componentes), en `anime_window.py` (1 155→**1 875**)
y en las seis vistas, que pasan de 1 071 a **2 017** líneas entre todas.

⚠️ **`utilsButtons.py` es el único que ha encogido** (350 → **205**): el paso 9.4 del rediseño retiró
las cinco clases de botón que ya no usaba nadie.

⚠️ **`anime_window.py` es hoy el módulo más grande del proyecto**, con diferencia, y el más citado por
esta documentación. Cualquier inserción en él desplaza decenas de anclas: reubícalas comparando el
**contenido** de la línea, no sumando un desplazamiento ([README](README.md)).

Los **19** `__init__.py` están **vacíos** (0 bytes) y solo marcan paquete; el decimonoveno es el de `gui/components/`. ✅ El último con contenido,
`watchingAnimes/__init__.py`, se vació en `e6d1a73` (2026-08-07).

> Recuentos actualizados el 2026-08-06 tras integrar **JKAnime**, que añade `jkanime.py` y su
> `__init__.py` vacío y toca `main_window.py`. **19 módulos reales** (antes 18).
> El salto anterior, de 17 a 18, lo trajo el selector de proveedor
> ([13](13-selector-de-proveedor.md)) con `userPersistence.py`.

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
| 🆕 `AnimeProviderId(Enum)` | `:18-31` | **3 miembros**. Valor = id corto y **estable**: es lo que se persiste |
| 🆕 `ProviderInfo` | `:34-47` | `frozen`. `id: AnimeProviderId`, `name: str`, `base_url: str` |
| `AnimeGenreFilter(Enum)` | `:50-97` | **40 miembros**. Valor = slug (`ACCIÓN = "accion"`) |
| `AnimeOrderFilter(Enum)` | `:100-103` | `POR_DEFECTO="default"`, `ALFABÉTICAMENTE="title"`, `CALIFICACIÓN="rating"` |
| `ServerInfo` | `:106-109` | `server: str`, `url: str` |
| `EpisodeInfo` | `:112-115` | `id: Union[str,int]`, `anime: str` |
| `AnimeInfo` | `:118-131` | `id`, `title`, `poster` + `synopsis=None`, `genres=None`, `episodes=None`, 🆕 `provider_id=None` |

**Entrantes**: proveedores, `animeProviderMgr`, `animesPersistence`, `utilsButtons`, `main_window`,
`anime_window`, todas las vistas.
**Salientes**: solo stdlib. **Efectos**: ninguno.

> 📖 Los tres campos opcionales originales de `AnimeInfo` valen `None` en los **listados**
> (recientes/búsqueda) y solo se rellenan al pedir `get_anime_info()`. ✅ Verificado en los tres
> proveedores.

> 🆕 **`provider_id` es distinto**: no lo rellena el proveedor sino
> `AnimeProviderManager.call_with_fallback()`, que es el único que sabe cuál acabó respondiendo.
> `None` significa «este `AnimeInfo` **no pasó por el manager**» (lo construyó alguien a mano), no
> «no se sabe». Detalle en [04 §1b](04-modelo-de-datos.md).

> ⚠️ **Añadir un proveedor obliga a tocar este fichero**, que antes no hacía falta: un miembro más en
> `AnimeProviderId`. Sin él, la clase del proveedor **no importa** ([11 §3](11-playbooks.md)).

---

## `src/APIs/common/animeProviderMgr.py`

**Responsabilidad**: contrato `AnimeProvider` (ABC) + registro y fallback (`AnimeProviderManager`).

### `AnimeProvider` (`:24-128`)

| Miembro | Línea |
|---|---|
| `PROVIDER_ID` / `PROVIDER_NAME` / `BASE_URL` | `:48` / `:51` / `:55` — 🆕 `PROVIDER_ID` es un `AnimeProviderId` |
| `__init_subclass__` | `:57-75` — valida los 3 atributos **y** que `PROVIDER_ID` sea del enum |
| 🆕 `provider_info() -> ProviderInfo` *(classmethod)* | `:77-85` — **ya implementado**; no lo sobrescribas |
| `search_animes_by_genres_and_order(genres, order=None, page=None) -> (List[AnimeInfo], int)` | `:87-91` |
| `search_animes_by_query(query=None, page=None) -> (List[AnimeInfo], int)` | `:93-96` |
| `get_anime_episode_servers(anime_id, episode_id) -> List[ServerInfo]` | `:98-101` |
| `get_recent_animes() -> List[AnimeInfo]` | `:103-105` |
| `get_anime_info(anime_id) -> AnimeInfo` | `:107-108` |
| `is_available(timeout=5.0) -> bool` | `:110-126` — `GET BASE_URL` |

> ✅ **Trampa**: la comprobación es `if ABC not in cls.__bases__` (`:62`). Como solo `AnimeProvider`
> lista `ABC` entre sus bases, **cualquier** subclase — incluida una clase base intermedia
> abstracta — debe definir los 3 atributos o `NotImplementedError` salta **al importar**.

### `AnimeProviderManager` (`:131-460`)

| Método | Línea | Nota |
|---|---|---|
| `register(provider, default=False)` | `:173-181` | el primero registrado queda por defecto aunque no lo pidas |
| `unregister(provider_id)` | `:183-186` | si era el default, pasa al siguiente registrado |
| `set_default` / `get_default_provider_id` | `:188-194` | `set_default` lanza `UnknownProviderError` |
| `get(provider_id=None)` | `:196-203` | lanza `UnknownProviderError` |
| `list_providers()` / `list_available_providers()` | `:205-247` | la segunda hace **una petición HTTP por proveedor** |
| `_ordered_providers(provider_id=None)` | `:249-259` | preferido primero, resto por orden de registro |
| 🆕 `__stamp_provider(result, provider_id)` | `:262-283` | sella quién respondió en cada `AnimeInfo` del resultado |
| `__is_empty_result(result)` | `:285-291` | `None`, `[]`, o `([], …)` cuentan como vacío |
| `call_with_fallback(...) -> (Any, Optional[AnimeProviderId])` | `:293-334` | devuelve `(None, None)` si todos fallan |
| wrappers `get_recent_animes`, `get_anime_info`, `search_animes_by_query`, `search_animes_by_genres_and_order`, `get_anime_episode_servers` | `:340-382` | mismos nombres que el contrato + `provider_id=`, `strict=` |
| `AnimeProviderManagerSingleton` | `:463-469` | |

**Añadidos el 2026-07-30** ([13](13-selector-de-proveedor.md)) — v0.1 → v0.2, **revisados el
2026-08-16** (v0.3): todo lo que era `str` ahora es `AnimeProviderId`.

| Método | Línea | Nota |
|---|---|---|
| `get_provider_name(provider_id)` | `:222-231` | nombre legible. 🆕 **tolera `None`** → `"desconocido"`; si el id no está registrado devuelve su `.value` |
| 🆕 `get_provider_info(provider_id) -> ProviderInfo\|None` | `:208-211` | ficha de un proveedor registrado |
| 🆕 `list_provider_infos() -> List[ProviderInfo]` | `:213-220` | **única** fuente del contenido de los desplegables de la GUI, en orden de registro. Sustituye a `get_provider_names()` |
| 🆕 `get_provider_info_by_name(nombre)` | `:233-243` | vuelta atrás: los widgets muestran nombre, el código usa enums. Sustituye a `get_provider_id_by_name()` |
| `get_anime_info_with_provider(...)` | `:348-361` | expone el `provider_id` que `call_with_fallback` ya devolvía y los wrappers tiraban |
| `normalize_title(title)` *(static)* | `:385-396` | minúsculas, sin tildes, resto a espacios |
| `resolve_anime_in_provider(anime_info, provider_id, threshold=None)` | `:398-460` | localiza el mismo anime en otro proveedor por título. **2 peticiones HTTP** → solo desde hilo secundario. Devuelve `None` antes que un falso positivo. ✅ **Vuelve a tener llamantes** desde el 2026-08-16: `open_saved_anime()` y el botón «Actualizar a …» |
| `TITLE_MATCH_THRESHOLD = 0.75` | `:167` | ✅ **calibrado el 2026-08-16** contra los 3 sitios reales; no ha necesitado moverse |

> ⚠️ **Dos métodos desaparecieron** en el cambio a enum: `get_provider_names()` y
> `get_provider_id_by_name()`. Si encuentras una cita a ellos en documentación o en un script del
> scratchpad, es anterior al 2026-08-16.

**Efectos**: red (indirecta, vía proveedores) + `print` de diagnóstico.
Semántica exacta y casos límite verificados: [05 §5](05-proveedores-y-scraping.md).

---

## `src/dataPersistence/userPersistence.py`

**Responsabilidad**: preferencias del usuario en `resources/DB/DB_user.db`. Tabla `USER_SETTINGS` de
clave/valor. Esquema y razonamiento: [04 §0](04-modelo-de-datos.md), [13](13-selector-de-proveedor.md).

| Símbolo | Nota |
|---|---|
| `UserSettingField` | enum columna + tipo SQLite, igual que `AnimeField` |
| `UserSettingKey` | claves válidas. Añadir una preferencia es **un miembro aquí**, sin migración |
| `UserSetting` | dataclass de una fila, con `from_db_dict()` |
| `UserPersistence(ServiceDB)` | `start()`, `validate_db_integrity()`, `get_setting()`, `set_setting()` (upsert), `get_all_settings()`, `get_default_provider_id()`, `set_default_provider_id()` |
| `UserPersistenceSingleton` | `__new__` devuelve la instancia real |

**Dependencias**: `utils.db.sqlite` (`ServiceDB`, `TableSchema`), `utils.utils.get_resource_path`.
**No** importa nada de `APIs/` ni de `gui/`.

**Efectos**: crea `resources/DB/DB_user.db` y, si el esquema cambiara, una copia en
`resources/DB/backups/`. `print` de diagnóstico.

⚠️ **Nunca lanza**: si la BD no es accesible, `available` queda a `False` y todo degrada a los valores
por defecto. Una preferencia perdida no puede impedir arrancar la aplicación.

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

## `src/APIs/jkanime/jkanime.py` — segundo del fallback *(nuevo el 2026-08-06)*

**Responsabilidad**: scraping de `jkanime.net` (Laravel). **v0.1**.
**Constantes**: `BASE_URL` `:37`, `SEARCH_URL=/buscar` `:38`, `DIRECTORY_URL=/directorio` `:39`,
`EPISODES_AJAX_URL=/ajax/episodes` `:40`, `SEARCH_MAX_RESULTS=30` `:50`,
`_GENRE_TRANSLATIONS` `:55` (10 excepciones), `_ORDER_TRANSLATIONS` `:72`.

**Helper de módulo**: `_fetch(url, session=None, **kwargs)` `:82-99`. Añade el User-Agent de
navegador —sin él el sitio responde de forma inconsistente— y acepta una `Session` para las
llamadas que necesitan conservar cookies.

| Método público | Línea | Efecto de red |
|---|---|---|
| `search_animes_by_genres_and_order` | `:107-168` | `GET /directorio?genero=…&filtro=…&orden=…&p=N` |
| `search_animes_by_query` | `:170-206` | `GET /buscar/<query>` |
| `get_anime_episode_servers` | `:208-251` | `GET /<slug>/<n>` |
| `get_recent_animes` | `:253-300` | `GET /` |
| `get_anime_info` | `:302-356` | **2 peticiones**: `GET /<slug>` + `POST /ajax/episodes/<id>/` |

**Helpers privados**: `__translate_genre` `:359` · `__slug_from_url` `:364` ·
`__parse_anime_cards` `:379` · `__extract_directory_payload` `:415` · `__parse_directory_entry`
`:458` · `__extract_genres` `:472` · `__get_episodes` `:487`. Singleton `:525-531`.

**Salientes**: solo `APIs.common.*`. No depende de `utils.utils`.

Tres cosas que lo separan de los otros dos proveedores:

- **Mezcla las dos técnicas de parseo** según la superficie (CSS en portada/búsqueda/ficha,
  payload JS en directorio, JSON en episodios). Ver [05 §3b](05-proveedores-y-scraping.md) antes
  de tocar nada.
- **Es el único que abre una `Session`**, y solo en `get_anime_info`: el `POST` de episodios
  necesita cookies y token CSRF. Se crea una por llamada en vez de compartir una del módulo,
  porque las peticiones salen desde hilos daemon distintos.
- **Es el único que traduce géneros** (10 de 40).

✅ Verificado el 2026-08-06: 50/50 comprobaciones sobre el sitio real, más 12/12 de registro y
fallback ([09 §3d](09-verificacion-y-pruebas.md)).

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
| `AnimeField(Enum)` | `:28-57` — `(columna, tipo SQLite)`, props `.column` / `.sql_type`. 🆕 `PROVIDER_ID` en **posición 2** |
| `AnimeRecord` | `:63-236` — 🆕 campo `provider_id: Optional[AnimeProviderId]` |
| `AnimeRecord.to_db_dict()` | `:88-110` — **invierte `episodes`** (`:90`), comprime `watched` (`:91`), 🆕 `provider_id` → `.value` o `None` (`:94`) |
| `AnimeRecord.from_db_dict()` | `:112-150` — **no** deshace la inversión |
| 🆕 `AnimeRecord._provider_id_from_db()` | `:152-171` — texto → enum; **degrada a `None`** ante un valor desconocido, sin lanzar |
| `AnimeRecord.from_anime_info()` | `:176-207` — 🆕 acepta `provider_id=`; si falta, toma el del `AnimeInfo` |
| `_episodes_to_ranges` / `_ranges_to_episodes` | `:209-224` / `:226-236` |
| `AnimesPersistence` | `:239-697` |
| `FIELDS` / `FIELD_TYPES` / `PRIMARY_KEY` | `:242-244` — derivados del enum |
| `SCHEMA: List[TableSchema]` | `:250-256` — **esquema declarado de la BD**; añadir una tabla = añadir un `TableSchema` |
| `start()` | `:265-277` — crea la BD si falta **y llama siempre a `validate_db_integrity()`** |
| `validate_db_integrity()` | `:279-306` — ✅ alinea la BD con `SCHEMA`; delega en `ServiceDB.validate_schema` |
| `get_anime_by_anime_id` | `:308-317` |
| 🆕 `get_all_animes()` | `:319-331` — **todas** las filas, incluidas las que no están en ninguna categoría. Para detectar duplicados |
| `get_watched_episodes` | `:333-338` |
| `get_favourite/watching/pending/finished_animes` | `:340-354` |
| `get_anime_by_genre_and_order` | `:356-395` |
| `update_watched_episodes` | `:397-417` — **devuelve `False` si el anime no existe** |
| 🆕 `update_anime_provider_id(anime_id, provider_id)` | `:419-440` — anota o corrige el proveedor de una fila. `False` si no existe |
| 🆕 `migrate_anime_identity(current_anime_id, anime_info, provider_id=None)` | `:442-516` — **la única reescritura de identidad**. Conserva episodios vistos y estados; **rechaza el destino ocupado** ([trampa 28](10-invariantes-y-trampas.md)) |
| `update_anime_episodes` | `:518-529` — invierte con `[::-1]` (`:519-520`) |
| `update_anime_to_[not_]favourite/watching/finished/pending` | `:531-592` |
| `_query_by_status` / `_insert_anime` / `_update_flag` / `_set_status` | `:594-684` — 🆕 `_set_status` **autorrellena** `provider_id` si la fila lo tenía a `NULL` (`:643-644`) |
| `_create_db_animes()` | `:686-697` — crea **todas** las tablas de `SCHEMA` |
| `AnimesPersistenceSingleton` | `:700-706` |

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
| 🆕 `move_anime_poster_by_status(status, old_id, new_id) -> bool` | `:62-79` | **renombra** el póster cacheado al cambiar el `anime_id`. `False` si no había nada que mover → quien llama lo descarga. Usa `os.replace`, no `os.rename`: en Windows `rename` falla si el destino existe |
| `remove_anime_poster_by_status(status, anime)` | `:81-88` | borra ese fichero; si no existe, imprime y vuelve |
| `download_animes_poster(images_path, animes)` | `:90-124` | descarga las que faltan (8 hilos) y **purga huérfanas** `:116-124` |
| `download_images_progress(images_path, recent_animes, progress_bar, progress_label)` | `:126-183` | igual + progreso 90 %→100 % `:145`; **toca widgets Tk desde workers** |
| `get_anime_image(anime, image_size=(195,275)) -> CTkImage` | `:185-196` | busca en las **6** categorías `:187`; si no está en ninguna, la baja de la red `:195-196` |
| `load_image(image_path, image_size=(130,185))` | `:198-202` | placeholder gris si no existe |
| `get_resource_path(relative_path)` | `:204-217` | `sys._MEIPASS` si está congelado; si no, raíz calculada desde este fichero |

> ✅ **Los dos bugs que tenía `get_anime_image` están resueltos** (2026-07-30, `83a8448`): la lista de
> carpetas incluye ya `watching` (era B1) y la rama de red pasa `size=` (era A4, el póster salía a
> 20×20). Ver trampas [15 y 16](10-invariantes-y-trampas.md), que conservan el invariante vigente:
> **toda carpeta a la que escriba `download_anime_poster_by_status` debe estar en `:187`**, y todo
> `CTkImage` nuevo necesita `size=` explícito.

---

## `src/utils/buttons/utilsButtons.py`

⚠️ **Ya no contiene ni un botón, pese al nombre.** El paso 9.4 del rediseño (2026-08-21) retiró las
**cinco** clases de botón que quedaban huérfanas —`BaseButton`, `EpisodeButton`, `SearchButton`,
`ApplyFiltersButton` y `AccordionFilterButton`—, sustituidas por los componentes de
`gui/components/` y por `EpisodeRow`. El módulo pasó de **361 a 205 líneas**. Renombrarlo se dejó
fuera del plan: el rediseño es solo interfaz y esto vive en `utils/`.

| Símbolo | Línea | Rol |
|---|---|---|
| `filter_animes_by_title(records, query)` | `:43-71` | búsqueda **local** en la biblioteca, sin red y sin mirar el proveedor ([trampa 26](10-invariantes-y-trampas.md)) |
| `match_animes_from_search(records, results)` | `:74-109` | traduce resultados web → filas guardadas, por slug **y** por título |
| `SavedAnimeSearch` | `:112-176` | el buscador de las 4 vistas de estado: local al instante + web con `after(0,…)`. Contador de generación y guarda de visibilidad |
| `SidebarButton` | `:179-224` | **no es un widget**: describe un destino (`sidebar_text`, `sidebar_command`, `sidebar_icon(size)`) y declara `show_frame()` abstracto. Quien pinta es `gui.components.sidebar.Sidebar` |

**Efectos**: lee iconos de disco (`load_dual_image`) y **la red** en `SavedAnimeSearch` (hilo daemon).
Ya **no consulta la BD**: la consulta por género y orden se fue con `AccordionFilterButton`.

⚠️ **Homónimos**: el `SearchButton` que existe hoy es el de `searchAnimes.py` —la vista «Buscar»—, no
el botón que había aquí.

> ✅ **Bug**: `__apply_filters` (`:341`) pasa `self.selected_order.get()`, un **`str`**, a
> `get_anime_by_genre_and_order`, que compara contra el **enum** (`animesPersistence.py:384`). La
> comparación siempre es `True` → *return* temprano → **la ordenación por coincidencias de género
> nunca se aplica**. Trampa 6.

---

## `src/gui/theme.py` 🆕

**Rol**: la **única fuente de verdad** de color, tipografía y medida de toda la interfaz.

**API pública**:

| Símbolo | Qué es |
|---|---|
| `Theme` | 20 tokens de color como tuplas `(claro, oscuro)`, los 10 roles tipográficos y las dos familias |
| `Theme.font(size, bold, mono)` | Construye —y cachea— un `CTkFont`. **Solo después de crear la raíz de Tk** |
| `Theme.ellipsize(texto, fuente, ancho, líneas)` | Recorta a N líneas midiendo con `font.measure()`. Ver [trampa 30](10-invariantes-y-trampas.md) |
| `Theme.clear_font_cache()` | Solo hace falta si se destruye la raíz de Tk |
| `Metrics` | Las medidas de `DISENO.md` §3 |
| `Metrics.pill_radius(alto)` | Radio de una píldora: la mitad de su alto |
| `ColorToken` | Alias de `Tuple[str, str]` |

**Dependencias**: solo `customtkinter` y `typing`. **No importa nada del proyecto**, y por eso puede
importarlo cualquier módulo de `gui/`.

**Efectos secundarios**: ninguno, salvo la caché de fuentes.

⚠️ `Metrics.POSTER_CACHE_SIZE` está **duplicado a mano** en `utils/utils.py:24-33`, con un comentario
que nombra a su pareja: `utils/` tiene prohibido importar de `gui/` ([01 §2](01-arquitectura.md)).
Si cambia uno, cambia el otro.

---

## `src/gui/components/` 🆕 — las 11 piezas compartidas

Todas viven en `gui/components/`, todas importan de `gui.theme` y **ninguna conoce a `MainWindow`**:
reciben datos y callbacks. Una vista **compone**; si necesita una variante, se añade un **parámetro**,
nunca una copia del fichero.

| Módulo | API pública | Nace en | Notas |
|---|---|---|---|
| `sidebar.py` | `Sidebar` (+ `_NavItem`, privado) | fase 1 | La barra entera: 6 destinos, plegado persistido, proveedor con pin y apariencia. `navigate_to(etiqueta)` 🆕 |
| `view_header.py` | `ViewHeader` | fase 1 | Título + subtítulo + `controls_frame`. Alto fijo 80 |
| `poster_grid.py` | `PosterGrid`, `PosterItem` | fase 2 | Rejilla de N columnas. Sello con `place()`, pie y `extra_builder` |
| `pager.py` | `Pager` | fase 2 | `set_total()` (corta la lista) o `set_pages()` (pagina el proveedor) |
| `resume_card.py` | `ResumeBand`, `ResumeCard`, `resume_progress()`, `resume_caption()` | fase 2 | `resume_progress()` es el **único** sitio donde se calcula por dónde ibas. 🆕 `update_record()` repinta el pie y la barra de **una** tarjeta sin recrear la banda |
| `anime_row.py` | `AnimeRow`, `RowAction` | fase 3 | Fila en cascada con acción en hover. La comparten «Viendo» y «Pendientes». 🔴 `__bind_interactions()` (`:278-312`) ata el **hover** a todos los descendientes de `__body` y el **clic** a todos menos el **subárbol** de la píldora, con `add="+"` para no pisar lo que CustomTkinter monta dentro ([trampa 40](10-invariantes-y-trampas.md)) |
| `side_panel.py` | `SidePanel` | fase 3 | Los 290 px de la derecha en «Viendo» |
| `rating_stars.py` | `RatingStars` | fase 5 | Cinco estrellas con medios puntos, dibujadas con PIL |
| `status_pill.py` | `StatusPill` | fase 5 | Texto, colores y glifo de los 4 estados. `other_status()`, `icon()` |
| `genre_chips.py` | `GenreChips` | fase 7 | Fichas de género. Colocadas con `place()`, no con `grid()`, así que el componente **lleva a mano la cuenta del ancho** — y esa cuenta incluye lo que `CTkButton` reserva por dentro ([trampa 39](10-invariantes-y-trampas.md)) |
| `empty_state.py` 🆕 | `EmptyState`, `glyph()`, `ICON_SIZE` | fase 9 | Icono, frase, pista y acción. Dibuja «nube tachada» y «lupa» con PIL |

**Quién usa qué**:

| Componente | Lo usan |
|---|---|
| `ViewHeader` | las 5 vistas con título (todas menos «Buscar») |
| `PosterGrid` | Nuevos, Favoritos, Finalizados, Buscar |
| `Pager` | Nuevos, Favoritos, Finalizados, Buscar |
| `AnimeRow` | Viendo, Pendientes |
| `StatusPill` | Favoritos, Finalizados, Buscar, la ficha y `EmptyState` |
| `EmptyState` | las 6 vistas |
| `Sidebar` | `MainWindow` |
| `SidePanel`, `ResumeBand`, `RatingStars`, `GenreChips` | una vista cada uno |

⚠️ **`resume_card.py` es dos cosas, y la tabla de arriba solo cuenta una.** Sus *widgets*
(`ResumeBand` / `ResumeCard`) los usa **una** vista, la portada; pero sus dos **funciones puras**
—`resume_progress()` y `resume_caption()`— tienen **cinco** llamantes: `resume_card.py:155`,
`anime_row.py:190` (la barra de «Viendo» y «Pendientes»), `side_panel.py:112`,
`watchingAnimes.py:162` (el subtítulo «M episodios pendientes») y `watchingAnimes.py:238` (la píldora
«Episodio N →»). Por eso `anime_row.py` y `side_panel.py`, que no pintan ninguna tarjeta, importan de
un módulo que se llama «tarjeta»: `resume` es *retomar*, no *resumen*. Si algún día molesta, la
separación limpia es llevarse las dos funciones a un módulo propio y dejar aquí los widgets.

**Efectos secundarios**: `poster_grid.py`, `anime_row.py`, `side_panel.py` y `resume_card.py` **leen
del disco** los JPG cacheados (`find_cached_poster_path()` + `load_rounded_image()`); ninguno sale a
la red. `rating_stars.py`, `status_pill.py` y `empty_state.py` **dibujan con PIL** en tiempo de
ejecución y cachean el `CTkImage` resultante.

⚠️ **Todo componente nuevo hay que declararlo en `hiddenimports` del `.spec`**, o el `.exe` no
arranca ([11 §6](11-playbooks.md)).

---

## `src/gui/main_window.py`

**Responsabilidad**: ventana raíz y **hub de estado compartido**. Composition root de proveedores.

**Estado público mutable** — quién lo muta en [06 §2](06-gui-y-vistas.md):
`recent_animes`, `favourite_animes`, `finished_animes`, `watching_animes`, `pending_animes`,
`last_search_instance`, `images_path`, `animes_persistence`, `anime_provider_mgr`,
**`user_persistence`**, `sidebar_frame`, `content_frame`.

| Método | Nota |
|---|---|
| `__init__` | registra proveedores, **captura el predeterminado del registro** (`:63`) **antes** de aplicar la preferencia guardada, arranca `UserPersistence` de forma síncrona, `load_sidebar_buttons()`, `show_loading_screen()` |
| `clear_frame()` | destruye los hijos de `content_frame` |
| `create_sidebar_frame` / `create_content_frame` | |
| `__config_main_window()` | `:96-108` — título, geometría, icono, **`fg_color=Theme.BG` de la raíz de Tk** (`:104`) y pesos de la rejilla |
| `load_sidebar_buttons()` | instancia las 6 vistas + **desplegable de proveedor y su pin** (en un frame propio) + selector de apariencia |
| `__apply_saved_provider_preference()` | lee `DB_user.db`, **convierte el texto a `AnimeProviderId`** (`:236`), aplica el proveedor fijado y recuerda cuál es; una preferencia inválida —texto huérfano o proveedor no registrado— solo avisa por consola y deja el pin sin marcar |
| `change_anime_provider_event(nombre)` | `set_default` + recargar recientes. **No persiste**: eso es el pin ([13 §12](13-selector-de-proveedor.md)) |
| `toggle_pinned_provider_event()` | fija el proveedor en uso como predeterminado, o lo desfija (`set_default_provider_id(None)`). Persiste el **`.value`** (`:279`). No cambia qué proveedor se usa |
| `__refresh_pin_provider_button()` | icono azul si lo que usas es tu predeterminado, gris si te has desviado |
| 🆕 `reference_provider_id()` | `:306-314` — el pin, o el predeterminado del **registro** si no hay pin. Es contra esto, y no contra el predeterminado vivo del manager, contra lo que se mide una desviación |
| 🆕 `provider_for_saved_anime(record_provider_id) -> (id, hay_desviación)` | `:316-341` — **implementa el orden de prioridad** de [13 §8](13-selector-de-proveedor.md). Devuelve además si hay desviación, porque eso obliga a re-resolver el anime por título (2 peticiones más) |
| `__reload_recent_animes()` | guarda antidoble + incrementa la **generación** y lanza el hilo |
| `__reload_recent_animes_worker(gen)` | **hilo daemon**: red + pósters; devuelve al hilo de UI con `after(0, …)` |
| `__on_recent_animes_reloaded(animes, gen)` | **hilo de UI**: descarta resultados de una generación caducada |
| `change_appearance_mode_event(mode)` | |
| `show_loading_screen()` | `:412-463` — **cubre la ventana entera con `Theme.BG`** y centra dentro el título, el GIF y la barra; lanza el hilo daemon. 🆕 Antes era un marco del tamaño de su contenido y **sin `fg_color`**: salía del gris por defecto de CustomTkinter ([trampa 36](10-invariantes-y-trampas.md)) |
| `download_images_and_show_animes(...)` | **hilo daemon** |
| `__preload_recent_animes_info(gen)` | **hilo daemon**; aborta si la generación cambió (si no, escribiría el anime equivocado en el índice equivocado tras un cambio de proveedor) |
| `load_animes(...)` | BD, progreso 0→40 % |

**Efectos**: red, disco, BD (`DB_Animes.db` y `DB_user.db`), widgets Tk.

> ⚠️ Las filas 9-12 del `sidebar_frame` están ocupadas por los dos selectores (9 etiqueta de
> proveedor, 10 desplegable **+ pin**, 11 etiqueta de apariencia, 12 tema). La fila **8** tiene
> `weight=1` y es el espaciador que los empuja al fondo: no metas nada en ella. El pin va **dentro
> del frame de la fila 10**, no en una fila propia, para no desplazar las de abajo.

---

## `src/gui/anime_window.py`

**Responsabilidad**: `AnimeWindowViewer` — la ficha de detalle. **No es una ventana**: reemplaza el
contenido de `content_frame`.

**Constantes de módulo**: 🆕 `DUPLICATE_TITLE_THRESHOLD = 0.9` (`:31`), `STATUS_SECTION_NAMES`
(`:36-41`, cómo se llama cada estado de cara al usuario) y 🆕 `FOCUS_DELAY_MS = 50` /
`FOCUS_SCROLL_MARGIN = 24` (`:143` y `:146`, la apertura por un episodio).

**Funciones de módulo** (públicas, las importan las 6 vistas):

| Función | Línea | Nota |
|---|---|---|
| `show_anime_info_error(anime_id)` | `:50-66` | `print` + `messagebox.showerror`. Se llama cuando `get_anime_info` devuelve `None`; sin ella, el clic no hacía nada (trampa 10) |
| 🆕 `find_saved_duplicate(records, title, exclude_anime_id=None)` | `:69-105` | el mismo anime guardado con otro slug, por título normalizado. **No** detecta títulos completamente distintos («Solo Leveling» / «Ore dake Level Up na Ken»): eso necesitaría red y esto corre en el hilo de la UI |
| 🆕 `open_saved_anime(main_window, anime_id, focus_episode=None, force_ascending=False)` | `:211-289` | **punto de entrada único de las 4 vistas de estado**. Elige el proveedor con `provider_for_saved_anime()`, re-resuelve por título si hay desviación, y saca la petición del hilo de Tkinter. 🆕 Los dos últimos parámetros (2026-09-01) dejan la ficha abierta **por un episodio** ([03 §12](03-flujos-de-ejecucion.md)); solo los usan «Viendo» y «Pendientes» |

### `EpisodeRow` — la fila de la lista de episodios

📖 `anime_window.py:266-424`. Un `CTkFrame` con cinco hijos: las etiquetas del número y del estado, el
interruptor «Visto», el separador de 1 px (con `place`, para no gastar una fila de rejilla) y —por
CustomTkinter— su propio `_canvas` interno.

| Miembro | Línea | Nota |
|---|---|---|
| 🆕 `__hovered` *(atributo de **clase**)* | `:280` | la fila resaltada ahora mismo. La que se enciende apaga a la anterior: **nunca hay dos** |
| `set_watched(watched)` | `:344-358` | mueve el interruptor **sin** disparar su `command` (`select()`/`deselect()` no lo llaman) |
| `set_expanded(expanded)` | `:363-370` | resalta la fila mientras sus servidores están desplegados. 🆕 Al **plegar**, vuelve al color de hover si el puntero sigue encima, no a transparente |
| 🆕 `__bind_interactions()` | `:401-409` | **dos bucles**: el hover a los **cinco** hijos, el clic solo a la fila y a las dos etiquetas |
| `__handle_enter` / `__handle_leave` / 🆕 `__release_hover` | `:395-416` | encender, apagar comprobando el puntero, y apagar sin preguntar |
| `__pointer_inside()` | `:418-424` | `winfo_pointerxy()` contra el rectángulo real de la fila |

🔴 **El interruptor y el separador reciben `<Enter>` / `<Leave>` pero no `<Button-1>`.** Sin el hover
quedaban como salidas mudas de las que no llega ningún `<Leave>` ([trampa 37](10-invariantes-y-trampas.md));
con el clic, marcar un episodio abriría sus servidores. Si añades un hijo, va al **primer** bucle.

**v0.1 → v0.2 el 2026-07-30**: la clase maneja **dos identidades del mismo anime**
(**[trampa 21](10-invariantes-y-trampas.md)**, [13 D5](13-selector-de-proveedor.md)).
**v0.2 → v0.3 el 2026-08-06**: se retira el desplegable de proveedor de la ficha; queda una etiqueta.
**v0.5 → v0.6 el 2026-08-16**: la identidad de persistencia sale de la **fila guardada**, no del
`AnimeInfo` de apertura; y la ficha gana la migración de proveedor y el aviso de duplicado.

| Atributo | Qué es |
|---|---|
| `anime_info` | identidad de **visualización**: la del proveedor que sirvió la ficha |
| `provider_id` | quién sirvió lo que se está viendo; es lo que muestra la etiqueta y lo que se pasa con `strict=True` a `get_anime_episode_servers` |
| `persistence_anime_id`, `persistence_poster_url`, 🆕 `persistence_provider_id` | identidad de **persistencia**: la de la fila guardada. **No cambia mientras la ficha está en pantalla** |
| 🆕 `__is_saved`, `__saved_provider_id` | si hay fila en `ANIMES` y de quién es. Son datos **distintos**: una fila anterior a la columna está guardada y no declara proveedor |

| Método | Línea | Nota |
|---|---|---|
| `__init__(main_window, anime_info, provider_id=None, anime_record=None)` | `:232-295` | **contrato**: `anime_info=None` → `ValueError`. 🆕 `anime_record` es de donde sale la identidad de persistencia cuando los slugs difieren |
| `__with_episodes(anime_info)` *(static)* | `:297-307` | normaliza `episodes=None` sobre una **copia** |
| `__persistence_anime_info()` | `:309-321` | copia de la ficha con `id`/`poster`/`provider_id` de persistencia. **Lo que hay que pasar a la BD y a los helpers de póster** |
| `display_anime_info()` | `:323-326` | punto de entrada |
| `__load_anime_status()` | `:328-356` | estados + episodios vistos. 🆕 **autorrellena `provider_id`** si la fila lo tenía a `NULL` (`:341-345`) |
| `__display_anime_info()` | `:358-429` | póster + título + sinopsis + géneros. Filas **1-3** (la 0 es la del proveedor) |
| `__show_provider_label()` | `:434-511` | bloque **no interactivo** de hasta 3 líneas, `row=0, column=1, columnspan=3` ([trampa 22](10-invariantes-y-trampas.md)). Detalle en [06 §4](06-gui-y-vistas.md) |
| 🆕 `__has_split_identity()` | `:513-526` | si la fila guardada y lo que se ve no son la misma cosa |
| 🆕 `__repair_target_provider_id()` | `:528-554` | a qué proveedor se ofrece migrar, o `None` |
| 🆕 `__repair_to_target_provider()` | `:556-600` | el `command` del botón. Si el destino ya sirve la ficha, 0 peticiones; si no, hilo + cursor `watch` |
| 🆕 `__confirm_and_migrate(anime_info, target)` | `:602-683` | diálogo enumerando cambios y episodios conservados → `migrate_anime_identity` + pósters, en hilo. Al terminar **reconstruye la ficha entera** en vez de mutar atributos que el resto de la clase da por inmutables |
| 🆕 `__move_posters(...)` | `:685-709` | renombra el póster en cada categoría activa, o lo baja. Un fallo aquí **no revierte** la migración: el peor caso es un recuadro gris |
| `__show_anime_status()` / `__display_anime_status()` | `:711-770` | los 4 botones de estado, fila **4** |
| 🆕 `__confirm_save(status)` | `:779-828` | guarda de duplicado antes de los 4 `add_to_*` |
| `add_to_*` / `remove_from_*` | `:830-903` | BD + póster + refresco. **Siempre con la identidad de persistencia** |
| `__display_episodes(episodes_to_show=None)` | `:915-981` | **`[:25]`**; frame en la fila **5** |
| `__toggle_sort_order` | `:1004-1014` | ordena `anime_info.episodes` **in place** |
| `__search_episodes` | `:1016-1030` | filtra por número exacto |
| `__previous_episode` / `__next_episode` | `:1032-1050` | |
| `__toggle_episode_switch(episode_id)` | `:1052-1105` | marcado **acumulativo**; desmarcado unitario |
| `__toggle_servers_frame(...)` | `:1802-1871` | `provider_id=self.provider_id, strict=True`. ⚠️ **HTTP en el hilo de Tkinter** ([07 C5](07-concurrencia-e-hilos.md)) |
| 🆕 `__focus_on_episode()` | `:1610-1656` | deja la ficha abierta **por el episodio** con el que se entró. Se dispara con `after(FOCUS_DELAY_MS)` tras pintar; **consume** `__focus_episode`. Si el episodio cae fuera de los 25, lo enseña solo con sus botones de navegación y escribe el número en «Ir al episodio…» |
| 🆕 `__scroll_to_episode(episode_id)` | `:1658-1695` | desplaza el `content_frame` **solo si la fila y sus servidores no caben** en lo que se ve. 🔴 Usa `content_frame._parent_canvas`: `CTkScrollableFrame` no expone el desplazamiento en customtkinter 5.2.2 |
| `__toggle_servers_frame` | ⚠️ **HTTP en el hilo de UI**. Pide los servidores con `provider_id=self.provider_id, strict=True`; si no hay, lo dice y sugiere cambiar de proveedor |
| `__play_video(url)` | `webbrowser.open` |

> Las citas `fichero:línea` de este módulo se han retirado: la tarea del selector desplazó ~150 líneas
> y mantenerlas a mano es la vía rápida a documentación falsa (ver la nota de mantenimiento en
> [README](README.md)).

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

🆕 **Ya no hay una «única» que cargue la ficha en hilo secundario**: desde el 2026-08-16 lo hacen las
seis. `recentAnimes.py` sigue siendo la única con `show_frame()` que revela la sidebar (`:31`).

| Vista | Cómo abre la ficha | Buscador |
|---|---|---|
| `recentAnimes.py` | hilo propio (`:205-232`) → `after(0,…)`; pide al proveedor que trajo la portada | — |
| las **4 de estado** | 🆕 `open_saved_anime()` (`anime_window.py:108-193`) | 🆕 `SavedAnimeSearch`: local + web |
| `searchAnimes.py` | 🆕 hilo propio (`:363-382`) → `after(0,…)`; **arrastra el `provider_id`** del resultado, porque su `id` es el slug de ESE sitio | propio, contra el proveedor |

`searchAnimes.py` añade `AnimeSearch` (`:24-31`, `dataclasses.dataclass` de la stdlib), paginación
(`:273-330`) y un frame de carga con GIF (`:171-216`).

🆕 **`recentAnimes.py` es también la única que refresca datos guardados** (`:131-180`,
`__refresh_resume_episodes()`): al entrar en la vista relee los episodios de las ≤3 filas de la banda
«Retomar» y reescribe la columna `episodes` si el proveedor sirve más que la biblioteca. Es el único
sitio del proyecto que escribe en `ANIMES` **sin que el usuario haya pedido nada**, así que va con
`strict=True` — sin *fallback* ([03 §11](03-flujos-de-ejecucion.md), [trampa 38](10-invariantes-y-trampas.md)).

> ⚠️ **Las 4 vistas de estado ya no son intercambiables con las otras dos** en lo que toca al clic y
> al buscador. Al copiar código de una a otra, mira primero cuál de los dos grupos es: las de estado
> trabajan con `AnimeRecord` (la biblioteca), las otras con `AnimeInfo` (el catálogo).

---

## ~~`src/gui/sidebarButtons/watchingAnimes/__init__.py` — código muerto~~ ✅ **Eliminado (2026-08-07, `e6d1a73`)**

Contenía un stub de 2 líneas, `class WatchingAnimeButton: pass`, que ensombrecía a la clase real.
`main_window.py:25` importa desde `gui.sidebarButtons.watchingAnimes.watchingAnimes`, así que nunca
llegó a usarse; pero un `from gui.sidebarButtons.watchingAnimes import WatchingAnimeButton` habría
importado el stub y roto en tiempo de ejecución sin ningún error de importación.

✅ Hoy el fichero está vacío, como los otros 17. [Trampa 19](10-invariantes-y-trampas.md).
