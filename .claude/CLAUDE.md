# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Protocolo de recepción de tareas

**Aplica a toda petición, sin excepción y sin que el usuario lo pida.** Antes de actuar, reformula
internamente lo pedido usando [`.claude/COMO-PEDIR-TAREAS.md`](COMO-PEDIR-TAREAS.md) y
[`.claude/docs/`](docs/README.md). Resuelve estos siete puntos:

1. **Tipo de tarea** — refactor · funcionalidad · bug · investigación · documentación · release.
   Determina el resto del encuadre.
2. **¿Persiste algo?** Si roza `AnimeField`, `AnimeRecord` o la serialización: las migraciones son
   automáticas desde el 2026-07-30 (`validate_db_integrity()`, `docs/11 §2`), pero la BD del usuario
   tiene datos reales — hay que declarar el esquema bien y probar sobre una **copia**. Sigue siendo lo
   primero que hay que aclarar, y lo que más cambia el tamaño del trabajo.
3. **Ficheros exactos y frontera de alcance.** Las 4 vistas de estado son casi idénticas línea por
   línea: decide si la tarea afecta a una o a las cuatro.
4. **¿Es una trampa conocida?** Coteja con `docs/10-invariantes-y-trampas.md` (20 trampas con su
   síntoma) **antes** de investigar desde cero.
5. **Nivel de verificación** — ejecutar la GUI · script en el scratchpad · solo lectura. No hay
   tests: si no se ejecuta, se entrega marcado como no verificado.
6. **Diagnosticar vs. arreglar.** Ante un bug, por defecto ambas cosas; parar y consultar si el
   arreglo resulta grande o arriesgado.
7. **¿Desincroniza `.claude/docs/`?** Si sí, decirlo al entregar e indicar qué documentos.

### Cuánto de esto se muestra

| Situación | Qué hacer |
|---|---|
| Petición clara y de bajo riesgo | **Normalizar en silencio** y ejecutar. No mostrar el análisis |
| Ambigua, amplia o de riesgo medio | Abrir con un bloque **«Entiendo que»** de ≤6 líneas (qué · dónde · alcance · verificación · supuestos) y **continuar sin esperar respuesta** |
| Escribe en la BD existente, borra datos, toca git, o el alcance cambia por completo según la respuesta | Presentar el encuadre y **esperar confirmación** |

**Nunca convertir esto en un interrogatorio.** Ante una duda: asumir la opción razonable y
**declarar el supuesto**. Una pregunta bloqueante solo si proceder a ciegas sería inseguro o dejaría
el trabajo inservible. El protocolo existe para acertar a la primera, no para pedir permiso.

---

## Descripción

**BibliotecaAnime** es una aplicación de escritorio para Windows (Python 3.10+, `customtkinter`) que gestiona una
biblioteca personal de anime. Obtiene los datos por *web scraping* de varios sitios de anime, los persiste en SQLite y
cachea los pósters en disco. Todo el estado es local; no hay backend propio.

---

## Comandos

```bash
pip install -r requirements.txt      # dependencias
python src/app.py                    # ejecutar (desde la raíz del repo)
pyinstaller MiBibliotecaAnime.spec   # generar dist/MiBibliotecaAnime_v<APP_VERSION>/
```

- `src/` usa **imports absolutos con raíz en `src`** (`from gui.main_window import ...`), por lo que hay que lanzar
  `app.py` como script (esto pone `src` en `sys.path`); `python -m src.app` **no** funciona.
- El directorio de trabajo es irrelevante: `get_resource_path()` calcula la raíz del proyecto desde
  `src/utils/utils.py`, no desde el cwd.
- **No hay suite de tests, linter ni formateador configurados.** `TESTS/` está en `.gitignore` y contiene ejemplos de
  terceros y scripts sueltos de scraping, no tests del proyecto. No inventes comandos de test.
- `.vscode/launch.json` y `tasks.json` lanzan la app con el intérprete de `biblio_anime_env/`.

---

## Arquitectura

### 1. Capa de proveedores (`src/APIs/`) — la abstracción central

El código de la GUI **nunca** habla con un sitio concreto. Todo pasa por tres piezas:

| Fichero | Rol |
|---|---|
| `APIs/common/models.py` | **Única fuente de verdad** de los tipos de dominio: `AnimeInfo`, `EpisodeInfo`, `ServerInfo` (dataclasses) y `AnimeGenreFilter`, `AnimeOrderFilter` (enums). Ningún proveedor redefine estos tipos. |
| `APIs/common/animeProviderMgr.py` | `AnimeProvider` (ABC con el contrato) + `AnimeProviderManager` (registro, selección y *fallback*). |
| `APIs/animeflv/`, `APIs/animeav1/` | Implementaciones concretas. |

**Contrato de `AnimeProvider`** — cinco métodos abstractos: `get_recent_animes`, `get_anime_info`,
`search_animes_by_query`, `search_animes_by_genres_and_order`, `get_anime_episode_servers`. Toda subclase concreta debe
definir `PROVIDER_ID`, `PROVIDER_NAME` y `BASE_URL`; `__init_subclass__` lanza `NotImplementedError` al importar si
falta alguno. Las búsquedas devuelven siempre `Tuple[List[AnimeInfo], int]` (resultados, última página).

Si un sitio usa slugs de género distintos a `AnimeGenreFilter`, **el proveedor los traduce internamente**: quien llama
siempre pasa el enum común.

**`AnimeProviderManager`** expone wrappers con la misma firma que `AnimeProvider` más `provider_id=` y `strict=`.
`call_with_fallback()` prueba el proveedor pedido (o el por defecto) y, si lanza excepción **o devuelve resultado
vacío**, va probando el resto en orden de registro. `strict=True` desactiva el fallback. Nunca propaga excepciones: los
wrappers devuelven `[]`, `None` o `([], 1)`.

Registro actual (en `MainWindow.__init__`): **AnimeAV1 es el proveedor por defecto**, AnimeFLV el fallback.

```python
self.anime_provider_mgr.register(AnimeAV1Singleton(), default=True)
self.anime_provider_mgr.register(AnimeFLVSingleton())
```

Ese predeterminado **lo puede cambiar el usuario** y se persiste en `DB_user.db`: `MainWindow.__init__`
llama a `set_default()` con la preferencia guardada antes de la primera petición. Hay **dos** selectores:
el de la sidebar (global, persistido, **con fallback**) y el de la ficha de detalle (solo esa ficha, no
se persiste, **`strict=True`**). Cambiar de proveedor en una ficha exige **re-resolver** el anime por
título con `resolve_anime_in_provider()`, porque `AnimeInfo.id` es el slug del sitio y no un
identificador universal. Detalle y decisiones: [`docs/13`](docs/13-selector-de-proveedor.md).

**Añadir un proveedor nuevo**: heredar de `AnimeProvider` en `APIs/<sitio>/`, implementar los 5 métodos devolviendo
tipos de `APIs.common.models`, crear su `...Singleton` y registrarlo en `MainWindow`.

Diferencia relevante entre los dos proveedores actuales: AnimeFLV se parsea con selectores CSS clásicos; **AnimeAV1 es
SvelteKit**, así que `animeav1.py` extrae con regex el payload de hidratación del `<script>` que contiene
`kit.start(app, element, {` y usa el DOM solo como *fallback*. Si AnimeAV1 empieza a devolver campos vacíos, el
sospechoso es ese payload, no los selectores.

### 2. Persistencia (`src/dataPersistence/animesPersistence.py` + `src/utils/db/sqlite.py`)

Dos bases de datos SQLite en `resources/DB/`, cada una con su clase derivada de `ServiceDB` y su propio
`SCHEMA` declarativo:

| BD | Clase | Contenido | Reemplazable |
|---|---|---|---|
| `DB_Animes.db` | `AnimesPersistence` | Tabla `ANIMES`: la **biblioteca real del usuario** | ❌ irrecuperable |
| `DB_user.db` | `UserPersistence` | Tabla `USER_SETTINGS` (clave/valor): preferencias, hoy el proveedor predeterminado | ✅ se regenera |

Detalle de `DB_user.db` y de por qué está separada: [`docs/13`](docs/13-selector-de-proveedor.md).

Tabla única `ANIMES` en `resources/DB/DB_Animes.db`, creada en el primer arranque (`AnimesPersistence.start()`).

- **`AnimeField`** (enum) define columna + tipo SQLite de cada campo; `FIELDS`/`FIELD_TYPES` se derivan de él, así que
  **añadir una columna es añadir un miembro al enum**. `validate_db_integrity()` migra la BD existente
  en el siguiente arranque (ver más abajo).
- **`AnimeRecord`** (dataclass) es la representación tipada de una fila. Conversión: `from_db_dict()` /
  `to_db_dict()` / `from_anime_info()`. La GUI trabaja con `AnimeRecord` para lo guardado y con `AnimeInfo` para lo que
  viene de la red — no son intercambiables (`anime_record.anime_id` vs `anime_info.id`, `poster_url` vs `poster`).
- Serialización no obvia:
  - `genres` y `episodes` → JSON. **`episodes` se guarda invertido** (`list(reversed(...))`).
  - `watched_episodes` → JSON de **rangos comprimidos**: `{1,2,3,5}` se persiste como `[[1,3],[5,5]]`
    (`_episodes_to_ranges` / `_ranges_to_episodes`). Nunca escribas ese campo a mano.
- **Estados** (`AnimeStatus`): `FAVOURITE` es independiente; `WATCHING`, `FINISHED` y `PENDING` son mutuamente
  excluyentes — activar uno pone los otros dos a 0 (ver `_set_status`). `update_anime_to_not_finished` mueve el anime
  a *pendiente*.
- `_set_status` **inserta el anime si no existía**; el resto de updates asumen que ya está en BD y devuelven `False`
  si no.
- `sqlite.py` es una capa mínima: `SqlUtils` abre y cierra una conexión por operación (sin pool), captura las
  excepciones y devuelve `bool`. Los errores se imprimen, no se lanzan. `query_sql` recibe la lista de campos y
  devuelve `List[Dict]` mapeando posición → nombre de columna, así que **el orden de `FIELDS` debe coincidir con el
  orden de las columnas de la tabla**.

**Migraciones automáticas** (desde 2026-07-30). El esquema declarado es `AnimesPersistence.SCHEMA`, una lista de
`TableSchema` (`utils/db/sqlite.py`); la tabla `ANIMES` se deriva de `AnimeField`. `start()` llama a
**`validate_db_integrity()`**, que compara la BD física con `SCHEMA` y aplica la corrección mínima:

- tabla ausente → `CREATE TABLE`;
- solo faltan columnas al final → `ALTER TABLE ADD COLUMN` (sin mover datos);
- orden o afinidad de tipo distintos → reconstrucción en una transacción, copiando **por nombre de columna**.

Los tipos se comparan **por afinidad SQLite** (`sqlite_affinity()`), no por texto: `VARCHAR(100)` → `VARCHAR(200)` no
dispara nada. Antes de la primera modificación se copia el `.db` a `resources/DB/backups/`. Es idempotente. Las
columnas presentes en BD que no estén en `SCHEMA` **se descartan** al reconstruir (quedan en la copia).

Para añadir una columna o una tabla → `docs/11 §2` y `§2b`. **La migración es automática; actualizar `AnimeRecord`
(`to_db_dict` / `from_db_dict`) no lo es.**

### 3. GUI (`src/gui/`)

`MainWindow` (CTk) es el **hub compartido**: mantiene `content_frame` (un `CTkScrollableFrame` único que todas las
vistas reutilizan), `sidebar_frame`, las listas cacheadas (`recent_animes`, `favourite_animes`, …),
`animes_persistence`, `user_persistence`, `anime_provider_mgr` y `last_search_instance`. Cada vista recibe
`main_window` y muta ese estado directamente; no hay router ni gestor de vistas.

Arranque:
0. `__init__` registra los proveedores y arranca `UserPersistence` **de forma síncrona** para aplicar el proveedor
   predeterminado del usuario antes de la primera petición y de construir el desplegable (es SQLite local, no red).
1. `show_loading_screen()` pinta el GIF + barra de progreso y lanza un hilo daemon.
2. Ese hilo: `load_animes()` (BD, 0→40 %) → `get_recent_animes()` del manager → `download_images_progress()`
   (90→100 %) → `RecentAnimeButton.show_frame()`, que además revela la sidebar.
3. Tras mostrar la portada, un segundo hilo (`__preload_recent_animes_info`) rellena sinopsis/géneros/episodios de cada
   anime reciente para que el clic sea instantáneo, escribiendo en `self.recent_animes[index]`.

**Botones de la sidebar** (`gui/sidebarButtons/<vista>/`): heredan de `utilsButtons.SidebarButton`, se instancian en
`MainWindow.load_sidebar_buttons()` y siguen todos el mismo patrón — `show_frame()` → `clear_frame()` →
construir widgets en `main_window.content_frame` → `__on_anime_click()` → `AnimeWindowViewer(...).display_anime_info()`.
Para una vista nueva: heredar de `SidebarButton`, implementar `show_frame()` y registrarla en `load_sidebar_buttons()`.

**`AnimeWindowViewer`** (`gui/anime_window.py`) no es una ventana: reemplaza el contenido de `content_frame`. Muestra
selector de proveedor + póster + sinopsis + géneros, los 4 botones de estado y la lista de episodios
(**los 25 primeros**, `[:25]`).
Marcar un episodio como visto es **acumulativo**: marca todos los anteriores hasta ése; desmarcar afecta solo a ese
episodio. Conserva en BD los episodios posteriores ya vistos.

⚠️ Maneja **dos identidades del mismo anime** y confundirlas duplica filas en la biblioteca del usuario:
`anime_info` es la del proveedor que se está mostrando (cambia con el selector), mientras que
`persistence_anime_id` / `persistence_poster_url` son las de apertura y **no cambian nunca**. Toda
operación de BD y de póster usa las segundas, vía `__persistence_anime_info()`. Es la
[trampa 21](docs/10-invariantes-y-trampas.md).

**Imágenes** (`utils/utils.py`): los pósters se guardan como `{anime_id}.jpg` en `resources/images/<categoría>/`,
redimensionados a `(130, 185)`; la ficha de detalle los pide a `(195, 275)`. `get_anime_image()` busca en las **6**
categorías (`favourite`, `watching`, `finished`, `pending`, `recent_animes` y `search`) antes de bajarlo de la
red, y en esa rama pasa `size=` explícito — sin él `CTkImage` pinta a 20×20. Las descargas van en un
`ThreadPoolExecutor` de 8 workers y borran del disco lo que ya no está en la lista actual.

### 4. Concurrencia

- Toda petición HTTP va en un hilo daemon; nunca en el hilo de Tkinter.
- Para reprogramar trabajo en el hilo de UI, usar `self.after(delay, callback)`.
- Las vistas existentes llaman a `time.sleep(0.1)` justo después de `clear_frame()` en el hilo principal (patrón
  heredado para dejar que Tk procese el destroy). No añadas más `sleep` en el hilo de UI en código nuevo.
- Antes de tocar un widget desde un callback diferido, comprobar `widget.winfo_exists()` — el frame puede haberse
  destruido (ver `__show_loading_frame` en `searchAnimes.py`).

---

## Convenciones

- **Idioma**: identificadores en inglés; comentarios, `print` de log y textos de UI en **español** (con tildes).
- **Cabecera de módulo obligatoria**: todo `.py` empieza con `__author__`, `__subsystem__`, `__module__`,
  `__version__` e `__info__`.
- **Singletons**: `AnimeFLVSingleton`, `AnimeAV1Singleton`, `AnimesPersistenceSingleton`,
  `AnimeProviderManagerSingleton`. Son clases envoltorio cuyo `__new__` devuelve la instancia real (no la envoltura),
  por lo que se anotan con el tipo real: `mgr: AnimeProviderManager = AnimeProviderManagerSingleton()`.
- **Métodos privados**: prefijo `__` (name mangling).
- **Type hints**: se mezcla `typing` (`List`, `Optional`, `Union`) con sintaxis 3.10 (`AnimeInfo | None`). El proyecto
  requiere **Python 3.10+**.
- No hay logging estructurado: se usa `print`.

---

## Notas de mantenimiento

- **`MiBibliotecaAnime.spec` está desactualizado**: su lista `hiddenimports` no incluye `APIs.animeav1.animeav1`,
  `APIs.common.animeProviderMgr` ni `APIs.common.models`, y declara `gui.anime_windows` (el módulo real es
  `gui.anime_window`). Revísalo antes de empaquetar y al añadir módulos o carpetas de `resources/` (sección `datas`).
- La versión de la app vive en `APP_VERSION` dentro del `.spec`.
- `resources/DB/` y las carpetas de pósters están en `.gitignore`: se generan en tiempo de ejecución.
- Hay `# TODO:` en el código que marcan trabajo en curso: `main_window.py` (renombrado de botones),
  `anime_window.py` (recomendaciones por género, alternar anime/manga), `recentAnimes.py` (renombrar a
  «nuevos lanzamientos»), `utilsButtons.py` (color de texto en modo oscuro). El del selector de proveedor
  se cerró el 2026-07-30.
- **`MiBibliotecaAnime.spec` empaqueta `resources/DB`**, así que el `.exe` distribuye la biblioteca **y ahora
  también las preferencias** del desarrollador. Ver A3/C11 en [`docs/12 §4`](docs/12-deuda-tecnica-y-roadmap.md).
- En `resources/images/utils/` ya existen los iconos `viendo_light/dark.png` y `pendientes_light/dark.png`, pero su uso
  está comentado en `watchingAnimes.py` y `pendingAnimes.py` (siguen con el icono único).

---

## Roadmap

- Renombrar «animes recientes» a **nuevos lanzamientos**.
- **Integrar más proveedores** (JKAnime, MonosChinos2, TioAnime) — es ahora lo primero: AnimeAV1 es el único
  operativo, y sin un segundo proveedor sano no se puede verificar de verdad la resolución *cross-provider*
  del selector ([`docs/12 §6`](docs/12-deuda-tecnica-y-roadmap.md)).
- **Convivencia anime + manga**:
  - Desplegable en la esquina inferior izquierda para elegir *animes / mangas / ambos*, accesible desde todas las
    pestañas salvo la ficha de detalle, con opción de fijar la elección por defecto. La preferencia ya tiene dónde
    guardarse: una fila más en `USER_SETTINGS`, sin migración ([`docs/11 §2c`](docs/11-playbooks.md)).
  - Nuevos lanzamientos a dos columnas (animes / mangas) si se eligen ambos, en cascada y con pósters más grandes,
    3 por fila; si no, listado único como ahora.
  - Quitar «Anime» del nombre de las pestañas favoritos / viendo / pendientes / finalizados y paginarlas de 10 en 10,
    con filtro tipo *radio button* Animes / Mangas / Ambos.
  - En «viendo», resultados en cascada de uno por fila indicando el último capítulo visto.
  - En «favoritos», calificación personal guardada y ordenación por ella.
- Bloque «Si te ha gustado *X*, te puede interesar…» al final de la lista de episodios, con 4 animes del mismo género.
- Integrar más proveedores (JKAnime, MonosChinos2, TioAnime) y proveedores de manga.

---

## Documentación detallada — `.claude/docs/`

Este fichero es el **resumen de entrada**. La documentación profunda, verificada contra el código y
contra los sitios reales, vive en [`.claude/docs/`](docs/README.md).

Guía de colaboración (cómo plantear una tarea en este repo, qué asumo por defecto y qué palancas
cambian mi comportamiento): [`.claude/COMO-PEDIR-TAREAS.md`](COMO-PEDIR-TAREAS.md).

**Antes de tocar cualquier cosa, lee [`docs/10-invariantes-y-trampas.md`](docs/10-invariantes-y-trampas.md)**
— 20 trampas con su síntoma observable.

| Documento | Qué responde |
|---|---|
| [docs/README.md](docs/README.md) | Índice, mapa de lectura «si tocas X, lee Y», cómo mantenerlo vivo |
| [docs/01-arquitectura.md](docs/01-arquitectura.md) | Capas, dependencias permitidas/prohibidas, invariantes de diseño |
| [docs/02-mapa-de-modulos.md](docs/02-mapa-de-modulos.md) | Ficha por módulo: API pública, dependencias, efectos secundarios |
| [docs/03-flujos-de-ejecucion.md](docs/03-flujos-de-ejecucion.md) | Los 10 flujos en diagramas de secuencia, con el hilo de cada paso |
| [docs/04-modelo-de-datos.md](docs/04-modelo-de-datos.md) | `AnimeInfo` vs `AnimeRecord`, esquema real de `ANIMES`, rangos, estados |
| [docs/05-proveedores-y-scraping.md](docs/05-proveedores-y-scraping.md) | Contrato, payload de AnimeAV1, selectores de AnimeFLV, fallback, diagnóstico |
| [docs/06-gui-y-vistas.md](docs/06-gui-y-vistas.md) | `MainWindow` como hub, ciclo de vida de una vista, layout, temas |
| [docs/07-concurrencia-e-hilos.md](docs/07-concurrencia-e-hilos.md) | Qué corre en qué hilo, reglas y carreras conocidas |
| [docs/08-convenciones-y-estilo.md](docs/08-convenciones-y-estilo.md) | Cabecera obligatoria, singletons, **plantillas copiables** |
| [docs/09-verificacion-y-pruebas.md](docs/09-verificacion-y-pruebas.md) | Cómo probar cada capa sin GUI; scripts listos; checklist manual |
| [docs/10-invariantes-y-trampas.md](docs/10-invariantes-y-trampas.md) | **Empieza por aquí.** 20 trampas con síntoma observable |
| [docs/11-playbooks.md](docs/11-playbooks.md) | Recetas: añadir vista, columna, proveedor, campo; empaquetar |
| [docs/12-deuda-tecnica-y-roadmap.md](docs/12-deuda-tecnica-y-roadmap.md) | TODOs con `fichero:línea`, discrepancias, riesgos, roadmap técnico |
| [docs/13-selector-de-proveedor.md](docs/13-selector-de-proveedor.md) | Selector de proveedor (sidebar + ficha) y `DB_user.db`. **Léelo antes de tocar `animeProviderMgr.py`, `main_window.py` o `anime_window.py`** |

> Los documentos marcan la procedencia de cada afirmación: ✅ verificado en ejecución ·
> 📖 leído en código · ⚠️ sin verificar.

> **Correcciones a este fichero** detectadas al auditarlo (detalle en
> [docs/12 §3](docs/12-deuda-tecnica-y-roadmap.md)): no todos los `update_*` devuelven `False` si el
> anime no existe; el orden de `episodes` antes de invertirse **depende del proveedor**.
>
> La tercera corrección (`get_anime_image()` no buscaba en `resources/images/watching/`) quedó
> **resuelta el 2026-07-30** en `83a8448`, junto con el póster a 20×20; el texto de arriba ya refleja
> el comportamiento actual.
