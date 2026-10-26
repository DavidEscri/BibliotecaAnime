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
4. **¿Es una trampa conocida?** Coteja con `docs/10-invariantes-y-trampas.md` (**58** trampas con su
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

Desde el 2026-10-20 **reproduce los episodios dentro de la propia ventana**, con mpv incrustado
(`python-mpv` + `libmpv-2.dll`), para los servidores cuyo hoster sabe resolver. Los demás —y cualquier
fallo— **siguen abriendo el navegador**, que es lo que hacía antes.

---

## Comandos

```bash
pip install -r requirements.txt      # dependencias
python src/app.py                    # ejecutar (desde la raíz del repo)
# reproductor: vendor/libmpv-2.dll (120 MB, fuera del repo) → paso 4 del README.md, o bien:
python tools/actualizar_libmpv.py --tag 20260923 --apply   # baja, prueba e instala la DLL y regenera sus avisos
pyinstaller MiBibliotecaAnime.spec   # generar dist/MiBibliotecaAnime_v<APP_VERSION>/
```

- `src/` usa **imports absolutos con raíz en `src`** (`from gui.main_window import ...`), por lo que hay que lanzar
  `app.py` como script (esto pone `src` en `sys.path`); `python -m src.app` **no** funciona.
- El directorio de trabajo es irrelevante: `get_resource_path()` calcula la raíz del proyecto desde
  `src/utils/utils.py`, no desde el cwd.
- **No hay suite de tests, linter ni formateador configurados.** `TESTS/` está en `.gitignore` y contiene ejemplos de
  terceros y scripts sueltos de scraping, no tests del proyecto. No inventes comandos de test.
- `.vscode/launch.json` y `tasks.json` lanzan la app con el intérprete de `biblio_anime_env/`.
- **`vendor/libmpv-2.dll` no está en el repositorio** (supera el límite de 100 MB de GitHub; `vendor/`
  está en `.gitignore`). Sin ella la app arranca y funciona, pero **todo servidor se abre en el
  navegador**; y el `.spec` **se niega a compilar**. URL, nombre del `.7z` y sha256: paso 4 del
  `README.md`.
- 🆕 **`tools/actualizar_libmpv.py`** (2026-10-21) es la forma de poner o **actualizar** la DLL: la
  baja de la release de shinchiro, la prueba con python-mpv, reconstruye la versión de cada
  biblioteca que lleva y regenera la sección de libmpv de `THIRD-PARTY-NOTICES.txt` y el paso 4 del
  `README.md` **entre sus marcas** (no edites a mano lo que hay entre ellas). Sin `--apply` va en
  seco. Vive fuera de `src/`, así que no va en el `.exe` ni en `hiddenimports`. 🔴 **Cambiar la DLL sin
  pasarla deja los avisos de licencia mintiendo.**

---

## Arquitectura

### 1. Capa de proveedores (`src/APIs/`) — la abstracción central

El código de la GUI **nunca** habla con un sitio concreto. Todo pasa por tres piezas:

| Fichero | Rol |
|---|---|
| `APIs/common/models.py` | **Única fuente de verdad** de los tipos de dominio: `AnimeInfo`, `EpisodeInfo`, `ServerInfo`, `ProviderInfo` (dataclasses) y `AnimeProviderId`, `AnimeGenreFilter`, `AnimeOrderFilter` (enums). Ningún proveedor redefine estos tipos. |
| `APIs/common/animeProviderMgr.py` | `AnimeProvider` (ABC con el contrato) + `AnimeProviderManager` (registro, selección y *fallback*). |
| `APIs/animeav1/`, `APIs/jkanime/`, `APIs/animeflv/` | Implementaciones concretas. |

**Contrato de `AnimeProvider`** — cinco métodos abstractos: `get_recent_animes`, `get_anime_info`,
`search_animes_by_query`, `search_animes_by_genres_and_order`, `get_anime_episode_servers`. Toda subclase concreta debe
definir `PROVIDER_ID`, `PROVIDER_NAME` y `BASE_URL`; `__init_subclass__` lanza `NotImplementedError` al importar si
falta alguno **o si `PROVIDER_ID` no es un miembro de `AnimeProviderId`**. Las búsquedas devuelven siempre
`Tuple[List[AnimeInfo], int]` (resultados, última página). `provider_info()` ya viene implementado: construye un
`ProviderInfo` desde esos tres atributos, y es lo que puebla el desplegable de la sidebar.

⚠️ **`PROVIDER_ID` es un enum desde el 2026-08-16**, no una cadena: su `value` es lo que se persiste en
`ANIMES.provider_id` y en `USER_SETTINGS`, así que **elegirlo es una decisión permanente**. Añadir un proveedor
empieza por añadir su miembro a `AnimeProviderId` ([`docs/11 §3`](docs/11-playbooks.md)).

Si un sitio usa slugs de género distintos a `AnimeGenreFilter`, **el proveedor los traduce internamente**: quien llama
siempre pasa el enum común.

**`AnimeProviderManager`** expone wrappers con la misma firma que `AnimeProvider` más `provider_id=` y `strict=`.
`call_with_fallback()` prueba el proveedor pedido (o el por defecto) y, si lanza excepción **o devuelve resultado
vacío**, va probando el resto en orden de registro. `strict=True` desactiva el fallback. Nunca propaga excepciones: los
wrappers devuelven `[]`, `None` o `([], 1)`.

Registro actual (en `MainWindow.__init__`): **AnimeAV1 es el proveedor por defecto**. El **orden de
registro es el orden del fallback**, y desde el 2026-08-06 hay tres:

```python
self.anime_provider_mgr.register(AnimeAV1Singleton(), default=True)
self.anime_provider_mgr.register(JKAnimeSingleton())    # 2026-08-06
self.anime_provider_mgr.register(AnimeFLVSingleton())
```

**JKAnime va en medio a propósito**: hasta entonces el fallback tenía una sola parada y estaba en
desuso, así que en la práctica no existía.

Ese predeterminado **lo puede cambiar el usuario**, y desde el 2026-08-06 son **dos gestos distintos**
en la sidebar:

- **el desplegable** cambia el proveedor **solo para esta sesión** — no escribe en BD, y conserva el
  **fallback**;
- **el pin** que hay a su lado fija (o desfija) el seleccionado como predeterminado en `DB_user.db`.
  `MainWindow.__init__` lo aplica con `set_default()` antes de la primera petición. Azul = lo que usas
  es tu predeterminado; gris = desviación temporal.

La ficha de detalle **ya no permite cambiar de proveedor**: muestra quién sirvió realmente esos datos
—lo que hace visible el fallback— y, si el anime está guardado, **de quién es tu fila**.

**Desde el 2026-08-16 cada fila de `ANIMES` recuerda su proveedor** (`provider_id`), y eso cambia cómo se
abre un anime guardado. `MainWindow.provider_for_saved_anime()` aplica este orden:

1. **la selección del desplegable**, si difiere de la referencia (pin, o predeterminado del registro) —
   desviarse es deliberado y manda;
2. **el `provider_id` de la fila**;
3. la referencia.

El caso 1 obliga a **re-localizar el anime por título** en el proveedor elegido, porque el slug guardado es de
otro sitio: ahí es donde vuelve a usarse `resolve_anime_in_provider()`. Y cuando lo que ves no lo sirve el
proveedor de tu fila, la ficha lo marca con **⚠ en ámbar** y ofrece **«Actualizar a X»**, que reapunta la fila
conservando los episodios vistos. Detalle y decisiones: [`docs/13 §8 y §14`](docs/13-selector-de-proveedor.md).

**Añadir un proveedor nuevo**: heredar de `AnimeProvider` en `APIs/<sitio>/`, implementar los 5 métodos devolviendo
tipos de `APIs.common.models`, crear su `...Singleton` y registrarlo en `MainWindow`. El recorrido completo, con el
caso real de JKAnime, en [`docs/11 §3`](docs/11-playbooks.md).

**Cómo se parsea cada sitio** — no hay una sola respuesta, y equivocarse cuesta horas mirando el DOM que no es:

| Proveedor | Técnica |
|---|---|
| AnimeFLV | selectores CSS clásicos |
| **AnimeAV1** | **SvelteKit**: `animeav1.py` extrae con regex el payload de hidratación del `<script>` que contiene `kit.start(app, element, {`, y usa el DOM solo como *fallback* |
| **JKAnime** | **las dos a la vez**, según la superficie: CSS en portada, búsqueda y ficha; **payload JS incrustado** en el directorio; **JSON con CSRF** en los episodios |

Si AnimeAV1 empieza a devolver campos vacíos, el sospechoso es ese payload, no los selectores. En JKAnime la regla
depende de qué falle: ver la tabla de [`docs/05 §3b`](docs/05-proveedores-y-scraping.md).

⚠️ Tres trampas propias de JKAnime, todas con síntoma silencioso: el `<img>` de la portada lleva **dos** imágenes
(`data-animepic` es el póster; `src`, un fotograma), las rejillas vacías del directorio **no** significan que haga
falta renderizar JS, y el *slug* y el **id numérico interno** no son intercambiables. Son las
[trampas 23, 24 y 25](docs/10-invariantes-y-trampas.md).

### 1b. Capa de resolución (`src/APIs/resolvers/`) — de la URL del servidor al vídeo *(2026-09-24)*

`ServerInfo.url` es la URL del **reproductor incrustado** (*embed*) de un **hoster** (zilla, MP4Upload,
playmudos…), no la del vídeo. Pasar de una a otra es **resolver**, y lo hace esta capa:

| Pieza | Qué es |
|---|---|
| `MediaSource(url, headers, kind, expires_at)` (`base.py`) | El medio ya resuelto. `headers` van en **cada** petición del medio, segmentos HLS incluidos; `kind` es `"hls"` o `"mp4"`; `expires_at`, un *epoch* o `None` si la URL **no lo declara** (que no es «no caduca») |
| `Resolver` (`base.py`) | ABC: `matches(url)` **sin red** y `resolve(url)`, que **nunca lanza** y devuelve `None` |
| `registry.has_resolver(url)` / `registry.resolve(url)` | El único punto de entrada. **Sin caché a propósito** |
| `zilla.py`, `jkplayer.py`, `mp4upload.py` | Los tres resolutores: «HLS» de AnimeAV1 (sintáctico, sin red), «Desu»/«Magi»/«Desuka» de JKAnime y MP4Upload |

🔴 **Por qué no es un sexto método de `AnimeProvider`**: un hoster no es de un proveedor —MP4Upload lo
embeben varios sitios—, así que la capa se indexa por **dominio del hoster**. El *fallback* del manager
**no interviene**: si no se resuelve, la salida es **el navegador**, no otro proveedor. Y `ServerInfo`
no cambia: se resuelve **al pulsar**, nunca al listar, porque hay URLs que caducan en ~3 h o van atadas
a la IP del cliente. La capa **solo importa stdlib, `requests` y a sí misma**; la llaman la ficha y el
reproductor, nadie más. Detalle, qué entrega cada hoster y cómo se diagnostica uno que dejó de
resolver: [`docs/05 §9`](docs/05-proveedores-y-scraping.md).

⚠️ **Las cabeceras son de cada hoster, y lo que uno exige otro lo rechaza**: zilla da 403 en los
segmentos sin `Sec-Fetch-Site: same-origin`, MP4Upload exige **su propio** `Referer`, y `jkplayers.com`
da **410** con cualquier `Referer`. Nada de cabeceras «por si acaso»
([trampas 43-45](docs/10-invariantes-y-trampas.md)).

Hoy **siguen abriendo el navegador** (llevan ↗): UPNShare, Voe, Mega, YourUpload, DoodStream, Netu,
VidHide, StreamTape y Okru (deuda **B14**). Añadir uno: [`docs/11 §9`](docs/11-playbooks.md).

### 2. Persistencia (`src/dataPersistence/animesPersistence.py` + `src/utils/db/sqlite.py`)

Dos bases de datos SQLite en `resources/DB/`, cada una con su clase derivada de `ServiceDB` y su propio
`SCHEMA` declarativo:

| BD | Clase | Contenido | Reemplazable |
|---|---|---|---|
| `DB_Animes.db` | `AnimesPersistence` | Tabla `ANIMES`: la **biblioteca real del usuario** (28 filas) | ❌ irrecuperable |
| `DB_user.db` | `UserPersistence` | Tabla `USER_SETTINGS` (clave/valor): preferencias, hoy el proveedor predeterminado | ✅ se regenera |

Detalle de `DB_user.db` y de por qué está separada: [`docs/13`](docs/13-selector-de-proveedor.md).

Tabla única `ANIMES` en `resources/DB/DB_Animes.db`, creada en el primer arranque (`AnimesPersistence.start()`).

- **`AnimeField`** (enum) define columna + tipo SQLite de cada campo; `FIELDS`/`FIELD_TYPES` se derivan de él, así que
  **añadir una columna es añadir un miembro al enum**. `validate_db_integrity()` migra la BD existente
  en el siguiente arranque (ver más abajo). ✅ **Ejecutado de verdad el 2026-08-16** con `provider_id`,
  y por el camino caro —en la posición 2, con reconstrucción de tabla—: 25 filas antes y después, las
  otras 12 columnas idénticas.
- **`provider_id`** (columna 2, `VARCHAR(50)`) guarda el `value` de `AnimeProviderId`, o `NULL`.
  `NULL` y «un proveedor que ya no existe en el código» se tratan igual: se degradan a `None` al leer
  (`_provider_id_from_db`), **nunca lanzan**. Las filas antiguas se rellenan solas al abrir la ficha o
  al marcar un estado, y **solo si estaban a `NULL`**.
  ⚠️ La columna responde «**quién sirve este slug**», no «quién lo trajo»: cuando el mismo slug existe
  en varios sitios, queda anotado el que respondiera la primera vez ([trampa 27](docs/10-invariantes-y-trampas.md)).
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
- **`migrate_anime_identity()`** es la única operación que reescribe la identidad de una fila
  (`anime_id` + `provider_id`). Conserva `watched_episodes`, `last_watched_episode` y los cuatro
  estados; sobrescribe título, póster, sinopsis, géneros y episodios. **Se niega a migrar si el
  `anime_id` destino ya lo ocupa otra fila**: no hay `UNIQUE` en la tabla, así que el `UPDATE` pasaría
  sin error y dejaría dos filas del mismo anime ([trampa 28](docs/10-invariantes-y-trampas.md)).
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

**Rediseñada por completo entre el 2026-08-20 y el 2026-08-21** (plan de 9 fases en
`.claude/plan-rediseno/`). La GUI pasó de 1 800 a **6 800** líneas y ganó
dos piezas que antes no existían:

- **`gui/theme.py`** — `Theme` (**24** tokens de color en tuplas `(claro, oscuro)` + tipografía) y
  `Metrics` (medidas). 🔴 **Ningún color literal fuera de este módulo**; si hace falta uno que no
  está, se añade el token primero. Comprobable: `git grep -nE "#[0-9A-Fa-f]{6}" -- src/` solo debe
  devolver `theme.py`.
  ⚠️ **Ese grep no detecta el defecto contrario**: un marco **sin `fg_color`** no sale transparente
  ni hereda del padre — sale del gris por defecto de CustomTkinter, que no es de `Theme`. No hay
  literal que buscar, porque el problema es la **ausencia** de uno. Le pasaba a la pantalla de carga
  hasta el 2026-08-31 ([trampa 36](docs/10-invariantes-y-trampas.md)).
- **`gui/components/`** — **13** piezas compartidas: `Sidebar`, `ViewHeader`, `PosterGrid`, `Pager`,
  `AnimeRow`, `SidePanel`, `ResumeBand`, `RatingStars`, `StatusPill`, `GenreChips`, `EmptyState`,
  desde el 2026-09-24 **`VideoPlayer`** (`video_player.py`, ver *El reproductor acoplado* más abajo)
  y desde el 2026-10-21 **`OrderMenu`**, el desplegable de orden de tres vistas.
  🔴 **Nada que viva toda la sesión puede apuntar a un widget que se destruye** (2026-10-21). En
  CustomTkinter 5.2.2 hay tres formas silenciosas de hacerlo, y las tres hacían crecer la memoria
  con cada cambio de vista (49 → 239 MB en 75):
  - un `CTkImage` compartido, porque `CTkLabel`/`CTkButton` no se desapuntan de él al
    destruirse. Las cachés de iconos guardan **el dibujo PIL** y devuelven un `CTkImage` nuevo;
  - un `ctk.CTkOptionMenu` que se destruye, porque su menú se queda en el registro de escalado.
    Para eso está `OrderMenu`;
  - un `bind_all()` sin `deletecommand()`.
  Son las [trampas 55-57](docs/10-invariantes-y-trampas.md), y se miden como dice
  [`docs/09 §6j`](docs/09-verificacion-y-pruebas.md).
  ⚠️ **En CustomTkinter `width` y `height` son una petición, no un contrato.** Un `CTkFrame` vacío no
  mide cero, un `CTkLabel` no se recorta a su `height` y un `CTkButton` se pinta al ancho que necesita
  su rejilla interna, no al que se le pidió. Quien coloque con `place()` y lleve él la cuenta —hoy
  `GenreChips`— tiene que sumar esa reserva y **comprobarla leyendo `winfo_reqwidth()`**, no
  `cget("width")` ([trampas 29, 30 y 39](docs/10-invariantes-y-trampas.md),
  [`docs/09 §6d`](docs/09-verificacion-y-pruebas.md)).
  🔴 **Y atar un evento encima de uno de estos widgets tiene dos reglas.** `bind()` sin `add="+"`
  **sustituye** el manejador que ya hubiera, y CustomTkinter monta los suyos **dentro** (`_clicked`,
  su hover): excluir un botón de un recorrido recursivo **no excluye su canvas ni su etiqueta**, que
  es donde cae el ratón. Las dos juntas dejaron la píldora de `AnimeRow` **sin ejecutar nunca su
  `command`** —y «Empezar» sin mover nada a «Viendo»— durante diez días, en silencio
  ([trampa 40](docs/10-invariantes-y-trampas.md), [`docs/09 §6e`](docs/09-verificacion-y-pruebas.md)).

🔴 **Una vista compone, no dibuja.** Si necesita una variante de un componente, **se le añade un
parámetro; no se bifurca el fichero**. Es lo que mantiene `AnimeRow` en un solo módulo para «Viendo»
y «Pendientes», y `PosterGrid` sirviendo a las tres rejillas.

`MainWindow` (CTk) sigue siendo el **hub compartido**: mantiene `content_frame` (un
`CTkScrollableFrame` único que todas las vistas reutilizan), `player_frame` (el panel del reproductor,
**hermano** de `content_frame`), `sidebar_frame`, las listas cacheadas
(`recent_animes`, `favourite_animes`, …), `animes_persistence`, `user_persistence`,
`anime_provider_mgr` y `last_search_instance`. Cada vista recibe `main_window` y muta ese estado
directamente; no hay router ni gestor de vistas.

Añade `navigate_to(etiqueta)` —abrir otra vista por su etiqueta de barra lateral, que es lo que usan
los botones de los estados vacíos— y `retry_recent_animes()`.

Arranque:
0. `__init__` registra los proveedores y arranca `UserPersistence` **de forma síncrona** para aplicar el proveedor
   predeterminado del usuario antes de la primera petición y de construir el desplegable (es SQLite local, no red).
1. `show_loading_screen()` pinta el GIF + barra de progreso y lanza un hilo daemon. **Cubre la
   ventana entera con `Theme.BG`** y centra el bloque con `place(relx=0.5, rely=0.5)`; la raíz de Tk
   lleva ese mismo fondo desde `__config_main_window()`.
2. Ese hilo hace **solo lo lento**: `load_animes()` (BD, 0→40 %) → `get_recent_animes()` del manager →
   `download_images_progress()` (90→100 %), y avisa del progreso con un callback que pinta la barra con
   `after(0, …)`. Lo demás lo hace `__on_startup_loaded()` **en el hilo de Tk**: retirar la pantalla de
   carga, el aviso si no hay estrenos y `RecentAnimeButton.show_frame()`, que además revela la sidebar.
   Antes del 2026-10-21 todo iba en el hilo, y la portada tardaba 860-1 000 ms en vez de ~200 (C1).
3. Tras mostrar la portada, un segundo hilo (`__preload_recent_animes_info`) rellena sinopsis/géneros/episodios de cada
   anime reciente para que el clic sea instantáneo, escribiendo en `self.recent_animes[index]`.

🔴 **La pantalla de carga se `destroy()` —no se esconde— y se retira también cuando no hay estrenos.**
Hasta el 2026-08-21 solo se retiraba en la rama de éxito, así que **un arranque sin red dejaba el GIF
tapando la portada para siempre**; y como el widget seguía vivo, su animación se reprogramaba cada
100 ms toda la sesión ([trampa 33](docs/10-invariantes-y-trampas.md)).

⚠️ Y hasta el **2026-08-31** el arranque enseñaba **tres fondos a la vez**: el gris por defecto del
`CTkFrame` de carga, el de la raíz de Tk en la franja que reserva el `minsize` de la columna de la
barra lateral —que **sobrevive al `grid_forget()`**— y `Theme.BG` en el resto. El GIF tiene el fondo
**transparente**, así que heredaba el del marco ([trampa 36](docs/10-invariantes-y-trampas.md)).

**La barra lateral** la construye y la mantiene `gui/components/sidebar.py`. Se **pliega** (224 → 84 px)
y recuerda su estado en `DB_user.db`. Los seis destinos van en este orden: Nuevos lanzamientos ·
Favoritos · Viendo · Pendientes · Finalizados · Buscar — **ninguno lleva ya la palabra «Anime»**.

🔴 **`SidebarButton` ya no es un widget** (`utils/buttons/utilsButtons.py`): es una clase llana que
solo describe el destino (`sidebar_text`, `sidebar_command`, `sidebar_icon(size)`). La firma del
constructor no cambió, así que las seis vistas heredan igual. Quien pinta es `Sidebar`; si necesitas
el destino como widget, **no existe**.

**Vistas** (`gui/sidebarButtons/<vista>/`): heredan de `utilsButtons.SidebarButton`, se instancian en
`MainWindow.load_sidebar_buttons()` y siguen todas el mismo patrón — `show_frame()` → `clear_frame()`
→ componer en `main_window.content_frame` → `__on_anime_click()` → la ficha.
Para una vista nueva: heredar de `SidebarButton`, implementar `show_frame()`, registrarla en
`load_sidebar_buttons()` **y declararla en `hiddenimports` del `.spec`**
([`docs/11 §1`](docs/11-playbooks.md)).

⚠️ **`clear_frame()` destruye los hijos, no la configuración de rejilla del `content_frame`.** Los
pesos de filas y columnas **sobreviven**, y una columna con peso y sin widgets también recibe el
espacio sobrante: toda vista que reparta peso tiene que deshacerlo al salir
([trampa 32](docs/10-invariantes-y-trampas.md)).

**Las 4 vistas de biblioteca no son iguales que las otras dos**: trabajan con lo guardado, no con el
catálogo.

- Su clic delega en **`open_saved_anime()`** (`anime_window.py`), que elige el proveedor y saca la
  petición del hilo de Tkinter. Las otras dos abren la ficha con el proveedor que ya conocen.
- Su buscador es **local** (`SavedAnimeSearch`): compara títulos guardados, funciona sin conexión y no
  depende del proveedor seleccionado; la búsqueda web se **suma** encima y nunca quita resultados
  ([trampa 26](docs/10-invariantes-y-trampas.md)).
- **Enseñan siempre el proveedor de la fila**, porque puede no ser el seleccionado.
- El acordeón «Abrir filtro de animes» **desapareció de las cuatro**: no está en el diseño y filtrar
  por género lo que ya es tuyo no aporta. Si el filtrado vuelve, el sitio es `GenreChips`.

**Cómo se ve cada vista** — rejilla donde se mira, cascada donde se decide:

| Vista | Disposición | Paginador (a 1440 · maximizado) |
|---|---|---|
| Nuevos lanzamientos | banda «Retomar» (**se refresca al entrar**) + rejilla de **6 · 8** (176 × 264) | 12 · 16 |
| Favoritos | rejilla de **5 · 7** (216 × 324) + calificación en estrellas | 10 · 14 |
| Viendo | cascada de `AnimeRow` + panel lateral de 290 px | — |
| Pendientes | cascada de `AnimeRow`, orden por duración, «Empezar» en hover | — |
| Finalizados | rejilla de **6 · 8** con el sello «vistos / totales» | 12 · 16 |
| Buscar | campo de 620 px + `GenreChips` + rejilla de **6 · 8** | del proveedor |

🔴 **Las columnas salen del ancho, no de una constante** (2026-09-02). `PosterGrid.columns_that_fit()`
divide su ancho entre `póster + hueco`; el parámetro `columns` quedó como **referencia del diseño**,
para cuando todavía no hay nada que medir. Y con las columnas se mueve el tamaño de página: cada vista
declara `ROWS_PER_PAGE = 2` porque la regla del diseño es «dos filas llenas», y esa regla solo se
sostiene si el número de página acompaña al de columnas. A 1440 salen exactamente los 6, 5, 12 y 10 de
antes.
🔴 **Y la vista tiene que colocarla con `sticky="ew"`.** Con `sticky="w"` la rejilla mide **su propio
contenido**, así que la cuenta se mediría a sí misma y no cambiaría nunca: es exactamente lo que pasó
entre el rediseño y el 2026-09-02, con casi 500 px de fondo muerto a la derecha al maximizar
([trampa 41](docs/10-invariantes-y-trampas.md)). El sobrante del reparto entero se distribuye con
`weight=1` + `uniform` y la celda centrada; al encoger hay que **quitar** ese peso
([trampa 32](docs/10-invariantes-y-trampas.md)).
⚠️ «Buscar» es la excepción y no pasa `on_columns_changed`: allí pagina el proveedor, así que su
última fila puede quedar coja y la rejilla se recoloca sola.

🔴 **«Viendo» y «Pendientes» abren la ficha por un episodio, no por el anime** (2026-09-01). Sus tres
acciones dicen un episodio en su texto —«Episodio N →», «Seguir por el N» y «Empezar»— y lo cumplen:
`open_saved_anime(..., focus_episode=N, force_ascending=…)` deja la ficha con esa fila desplegada, sus
servidores a la vista y la ventana desplazada **solo si la fila no cabía**. El número sale del mismo
`resume_progress()` que escribió el texto.
⚠️ **«Empezar» fuerza el orden ascendente y «Viendo» no**, y no es un descuido: el corte de 25
episodios se aplica sobre la lista **tal y como llega**, así que con One Piece por el 1164 forzarlo a
ascendente lo dejaría fuera. Cuando el episodio cae fuera del corte, se enseña **él solo** con sus
botones de navegación, como al buscarlo a mano ([`docs/03 §12`](docs/03-flujos-de-ejecucion.md)).
✅ La petición de servidores que esto dispara al abrir la ficha **ya no va en el hilo de Tkinter**
(2026-09-24): la fila dice «Buscando servidores…» mientras llega. El `after(50 ms)` se queda, con otro
motivo: medir dónde cae la fila con la ficha ya pintada.

🔴 **Las fichas de `GenreChips` se colocan con `place()`, así que el componente lleva a mano la cuenta
del ancho** — y esa cuenta incluye lo que `CTkButton` reserva por dentro. Quedarse corto no encoge la
ficha: la deja pintándose **encima de la siguiente**, que es como se destapó (la ✕ del género
seleccionado tapada por la ficha de al lado, resuelto el 2026-09-01,
[trampa 39](docs/10-invariantes-y-trampas.md)).

🔴 **Los episodios guardados se refrescan solos, y ninguna vista espera por ello** (2026-10-27,
cierra B12). `ANIMES.episodes` es el recuento del día en que abriste la ficha, así que un anime **en
emisión** mentía en la banda «Retomar», en las barras de «Viendo» y en la duración de «Pendientes»
([trampa 38](docs/10-invariantes-y-trampas.md)). Lo arregla **`EpisodeRefresher`**
(`gui/episode_refresher.py`), un servicio sin interfaz que vive en `MainWindow.episode_refresher`:

- **Cuándo**: `__on_startup_loaded()` encola «Viendo» + «Pendientes» **con la portada ya pintada**,
  y la banda, «Viendo» y «Pendientes» piden las suyas **con prioridad** al entrar. Cada fila se
  comprueba **una vez cada 30 min** (`FRESH_FOR_S`), así que cambiar de vista no repite peticiones.
- **Cómo**: **un hilo por proveedor**, una petición detrás de otra dentro de cada sitio. Un
  proveedor con **2 fallos seguidos** se deja de pedir esa media hora: AnimeFLV tarda 9 s por fila
  en fallar, y AnimeAV1 no tiene por qué esperarlo.
- **Qué ve el usuario**: la vista pinta **con lo guardado** y se suscribe (`subscribe()`); lo que
  cambia se repinta **en el sitio** —`ResumeCard`/`AnimeRow`/`SidePanel.update_record()` y
  `ViewHeader.set_subtitle()`—, nunca reconstruyendo. **«Pendientes» no se reordena** mientras la
  miras. Entrar en «Viendo» cuesta lo mismo que antes (✅ 414-511 ms frente a 414-471 en `develop`).
- **De regalo**: `open_saved_anime()` aprovecha la ficha que trajo el refresco (`cached_info()`, una
  **copia**, porque la ficha reordena sus episodios en el sitio) y se ahorra la petición: ✅ One
  Piece abre en 772 ms en vez de ~1 060. Solo si el desplegable **no** está desviado.

⚠️ Va con **`strict=True`** —al proveedor de la fila y a ninguno más—, al revés que
`open_saved_anime()`. Aquí se **escribe en la biblioteca sin que el usuario lo pida**, y con
*fallback* el mismo slug puede existir en otro sitio con otra cuenta de episodios
([trampa 27](docs/10-invariantes-y-trampas.md)). Tampoco escribe nunca si la respuesta viene vacía,
**relee la fila** antes de escribir —si entretanto cambió de proveedor, el dato ya no es suyo— y
**se salta las filas sin `provider_id`**. Detalle en [`docs/03 §11`](docs/03-flujos-de-ejecucion.md).

⚠️ **Los contadores de la barra salen de las listas cacheadas del hub, y esas listas solo se llenan al
arrancar.** Quien cambie un estado tiene que **releerlas** antes de llamar a
`refresh_sidebar_counts()` ([trampa 31](docs/10-invariantes-y-trampas.md)).

⚠️ **Todo lo que abra una ficha va en hilo daemon y repinta con `after(0, …)`.** Hacerlo desde el hilo
secundario revienta con `invalid command name ...!ctkcanvas` al destruir una vista que tenía un
`<Configure>` encolado.

**`AnimeWindowViewer`** (`gui/anime_window.py`, 2 429 líneas) no es una ventana: reemplaza el contenido
de `content_frame`. Muestra el bloque de proveedor + póster de 248 × 372 + sinopsis + géneros, los 4
botones de estado y la lista de episodios (**los 25 primeros**, `[:25]`).

🔴 **La sinopsis se normaliza al pintar, no al raspar** (2026-09-02). `wraplength` se recalcula en
cada `<Configure>` desde el rediseño, pero **no puede deshacer un `\n` que traiga el texto**: Tk lo
respeta siempre, así que la sinopsis conservaba los renglones del proveedor por ancha que fuera la
ventana —13 de las 35 filas de la biblioteca— mientras el título de al lado sí se reajustaba.
`wrap_synopsis()` convierte los saltos sueltos en espacio y **conserva los dobles**, que son párrafos
que escribió alguien ([trampa 42](docs/10-invariantes-y-trampas.md)). `AnimeInfo.synopsis` sigue
siendo el texto íntegro: cómo se reparte en renglones es cosa de la GUI, y así salen bien también las
filas ya guardadas sin migrar nada. De paso se quitó el tope de 74 caracteres de ancho, que a pantalla
completa dejaba media ficha vacía.
Marcar un episodio como visto es **acumulativo**: marca todos los anteriores hasta ése; desmarcar afecta solo a ese
episodio. Conserva en BD los episodios posteriores ya vistos.

Lo que cambió con el rediseño: **los 4 botones se encienden y se apagan** en vez de cambiar de texto,
y comparten un único `command`; **`EpisodeRow` sustituye al botón de ancho completo** que repetía el
título del anime veinticinco veces; las filas van en las posiciones **pares** de la rejilla y los
servidores en la impar de debajo, así que desplegarlos no empuja nada; el corte de 25 **se anuncia en
pantalla**; y el botón de orden dice **el orden que llega del proveedor**, que no es el mismo en
todos. La ficha además **refresca los contadores** de la barra al cambiar un estado.

🔴 **En `EpisodeRow`, el hover va atado a los cinco hijos y el clic solo a tres.** El interruptor y el
separador de 1 px reciben `<Enter>` / `<Leave>` pero no `<Button-1>`: `CTkFrame.bind()` ata al canvas
interno, que es **hermano** de los demás hijos y no su ancestro, así que salir de la fila por un hijo
sin atar **no manda ningún `<Leave>`** y el episodio se queda resaltado para siempre. Recorrer la
lista despacio dejaba encendidos todos los episodios por los que pasabas — y **deprisa no se
reproduce**, porque el salto se salta el separador ([trampa 37](docs/10-invariantes-y-trampas.md),
resuelta el 2026-09-01). Encima, `EpisodeRow.__hovered` es un atributo **de clase**: la fila que se
enciende apaga a la anterior, así que no puede haber dos. Si añades un hijo a la fila, **átalo**.

**El bloque de proveedor** son hasta tres líneas: `Proveedor: X` (de dónde vienen los datos que ves),
`En tu biblioteca: Y` (de quién es tu fila) y el botón «Actualizar a Z». **El ⚠ ámbar compara las dos
primeras**: iguales → gris informativo; distintas → hay identidad partida.

⚠️ Maneja **dos identidades del mismo anime** y confundirlas duplica filas en la biblioteca del usuario:
`anime_info` / `provider_id` son las del proveedor que sirvió la ficha, mientras que
`persistence_anime_id` / `persistence_poster_url` / `persistence_provider_id` salen de la **fila
guardada** y **no cambian mientras la ficha está en pantalla**. Toda operación de BD y de póster usa las
segundas, vía `__persistence_anime_info()`. Es la [trampa 21](docs/10-invariantes-y-trampas.md).

🔴 **Quien abra una ficha de algo que puede estar en la biblioteca tiene que pasar `anime_record=`** al
constructor. Omitirlo reintrodujo el bug durante la fase 4 del 2026-08-16: con el desplegable desviado,
`anime_info.id` es el slug de otro sitio, la ficha se mostraba como no guardada y un solo clic en un
estado creaba una fila duplicada.

**Antes de guardar**, `__confirm_save()` busca en toda la biblioteca un anime con el **mismo título
normalizado** (umbral 0.9) y avisa nombrando la sección concreta, porque un mismo anime tiene slug
distinto en cada sitio y la comprobación por `anime_id` no lo detecta.

🔴 **Dos temporadas no son el mismo anime, aunque como texto lo parezcan** (2026-10-26). «Kusuriya no
Hitorigoto 3rd Season» y «… 2nd Season» se parecen **0,939**: con solo el umbral, la 3.ª heredaba en
«Buscar» el sello y **la fila** de la 2.ª, y marcarla «Pendiente» sacaba a la 2.ª de «Viendo». Toda
decisión de identidad por título —`find_saved_duplicate()`, `match_animes_from_search()` y
`resolve_anime_in_provider()`— pasa por **`AnimeProviderManager.title_similarity()`**, que da 0 si
los números del título no coinciden («2nd», «Season 2» y «II» cuentan igual). `filter_animes_by_title()`
no la usa a propósito: buscar «kusuriya» tiene que devolver las tres
([trampa 58](docs/10-invariantes-y-trampas.md)).

**Imágenes** (`utils/utils.py`): los pósters se guardan como `{anime_id}.jpg` en `resources/images/<categoría>/`,
redimensionados a **`(248, 372)`** desde el rediseño —el mayor tamaño que pide cualquier vista— y cada
vista reduce con su propio `size=` al construir el `CTkImage`. ⚠️ Ese valor está **duplicado a mano**
en `utils/utils.py:24-33` y en `Metrics.POSTER_CACHE_SIZE`, porque `utils/` no puede importar de
`gui/`: si cambia uno, cambia el otro. La ficha de detalle los pinta a `Metrics.SHEET_POSTER` (248 × 372).
`find_cached_poster_path()` busca en las **6** carpetas de `POSTER_FOLDERS` (`favourite`, `watching`,
`finished`, `pending`, `recent_animes` y `search`); si no está en ninguna, la ficha pinta el cuadro gris y
lo baja **en un hilo** con `download_poster()`, que no toca Tk (desde el 2026-10-21; antes se bajaba en el
hilo de la interfaz). Las descargas van en un
`ThreadPoolExecutor` de 8 workers y borran del disco lo que ya no está en la lista actual.

**El reproductor acoplado** (2026-09-24 a 2026-10-20, plan de 7 fases en
`.claude/plan-reproductor/`; aspecto en
`DISENO-VISUAL.html`, el diseño aprobado):

- **Pulsar un servidor ya no es `webbrowser.open()`.** `__play_video()` monta el panel si hace falta,
  enseña «Cargando», resuelve en un hilo daemon y carga el medio en `VideoPlayer`. Si no hay
  resolutor, si no resuelve, si libmpv no carga o si el medio da error (`end-file` con `reason=4`),
  **abre el navegador** y lo dice en el recuadro del vídeo, ofreciendo otro servidor que sí se vea.
  🔴 **Ningún cambio puede dejar la reproducción peor que eso.** ⚠️ Con un hoster que responde
  **lento** tampoco hay error de mpv, así que `VideoPlayer` lleva un **tope propio de 30 s**
  (`LOAD_TIMEOUT_S`, desde `play()` hasta que empieza a verse) que para mpv y cae al navegador
  (zilla tardó ~70 s el 2026-10-20; [trampa 54](docs/10-invariantes-y-trampas.md), B15 cerrada el 2026-10-21).
- **Va encima de la ficha, no en su lugar**: `MainWindow.show_player_frame()` pone `player_frame` en la
  fila 0 y baja `content_frame` a la fila 1, que **se queda** debajo, encogido y desplazado hasta el
  episodio. «← Volver a la ficha», cambiar de vista (`clear_frame()`) y cerrar la ventana
  (`WM_DELETE_WINDOW`) cierran mpv.
- **Columna de 330 px a la izquierda**: estado, título, «Episodio N de M · servidor X», proveedor,
  fichas de servidor (↗ en las que se abren fuera), progreso y «Siguiente episodio».
- **`VideoPlayer`** es solo el reproductor —qué suena y qué hacer si falla lo decide la ficha, por
  callbacks—: mpv incrustado vía `wid`, tarjetas de estado en el mismo recuadro y `PlayerControls`
  (anterior · −10 · play · +10 · siguiente · progreso · tiempo · volumen · pantalla completa). Su
  fondo es el token **`VIDEO_BG`**, negro en los dos temas, el único que pidió el reproductor.
- **Pantalla completa sin `-fullscreen`**, que con dos monitores lleva la ventana al principal: se
  quita el marco y se ocupa el monitor de la ventana. La barra pasa a una **ventana flotante**
  (`PlayerControls(floating=True)` en un `Toplevel` `-topmost`) que se oculta a los 5 s con el cursor
  y se retira si otra aplicación pasa delante ([trampas 51 y 52](docs/10-invariantes-y-trampas.md)).
- **Al terminar**, tarjeta con «Volver a la ficha» y «Ver el episodio N+1», y **el episodio se marca
  como visto** —decisión del usuario del 2026-10-20— **solo si el anime ya tiene fila** (nunca la
  crea), con la identidad de la fila guardada y la semántica acumulativa de siempre. Un fin de fichero
  a más de 15 s del final es un **corte**, no un fin, y no marca nada
  ([trampas 47 y 48](docs/10-invariantes-y-trampas.md)).

🔴 **Encima del vídeo sí se ve un widget de Tk, si es hermano del frame de mpv y opaco**; uno **hijo**
queda tapado. Y **el ratón y el teclado sobre el vídeo llegan a Tk, no a mpv**: los atajos, el cursor y
la barra se resuelven en Tk ([trampas 49 y 50](docs/10-invariantes-y-trampas.md)). Las dos corrigen
lo que daba por hecho la investigación previa. Detalle completo en
[`docs/06 §12`](docs/06-gui-y-vistas.md) y el flujo, con el hilo de cada paso, en
[`docs/03 §13`](docs/03-flujos-de-ejecucion.md).

### 4. Concurrencia

- Toda petición HTTP va en un hilo daemon; nunca en el hilo de Tkinter. ✅ **Sin excepciones desde el
  2026-10-21**: la última —el póster de la ficha cuando no estaba en disco, que se había quedado sin
  contar— salió con la auditoría de rendimiento; la anterior, los servidores de un episodio, con la
  fase 2 del reproductor. 🆕 Y **toda petición lleva timeout**: las búsquedas de AnimeAV1 (`_fetch`) y
  tres de AnimeFLV no lo tenían, y un servidor colgado dejaba «Buscar» cargando para siempre.
- 🔴 **Los eventos de mpv llegan en su propio hilo (`MPVEventHandlerThread`), y desde él no se llama a
  Tk ni con `after()`**: `after()` desde otro hilo espera a que Tk lo atienda, y `terminate()` desde Tk
  espera a ese hilo. Los callbacks solo dejan el dato en atributos o en una cola, y `VideoPlayer` lo
  recoge con un sondeo de 100 ms ([trampa 46](docs/10-invariantes-y-trampas.md),
  [`docs/07 §1b`](docs/07-concurrencia-e-hilos.md)).
- Una respuesta que puede llegar tarde lleva **número de petición** y se descarta si ya no es la última
  (servidores, resolución y cambio de episodio en la ficha).
- 🆕 `EpisodeRefresher` (2026-10-27) lanza **como mucho un hilo daemon por proveedor**, que muere al
  vaciar su cola; su estado compartido va bajo un `Lock`, y escribir en la BD y avisar a las vistas
  vuelve al hilo de Tk con `after(0, …)`.
- Para reprogramar trabajo en el hilo de UI, usar `self.after(delay, callback)`.
- ⚠️ **El `time.sleep(0.1)` tras `clear_frame()` desapareció de las seis vistas.** Solo estaba para que
  `winfo_width()` no valiera 1 al calcular columnas; con rejillas de número fijo no se mide nada. **No
  lo reintroduzcas**, ni añadas ningún `sleep` en el hilo de UI.
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

- **`MiBibliotecaAnime.spec`**: `hiddenimports` tiene **39** nombres desde el 2026-10-27 —38 módulos
  de `src/` y `mpv`, que `video_player.py` importa **dentro** de `load_mpv()` y el análisis estático no
  ve—. ✅ Auditado con AST en las dos direcciones el 2026-10-21: todos resuelven a ficheros reales y **ningún módulo
  de `src/` queda sin declarar** salvo `app.py`, que es el script de entrada. El reproductor añadió los
  cinco `APIs.resolvers.*` y `gui.components.video_player`; la auditoría de rendimiento,
  `gui.components.order_menu`; el refresco de episodios, `gui.episode_refresher`. 🔴 **Todo módulo nuevo bajo `src/` hay que
  declararlo aquí**, o el `.exe` compila y revienta al arrancar.
- **`binaries`** lleva `('vendor/libmpv-2.dll', 'vendor')` —destino **`vendor`**, no `'.'`—, porque
  `load_mpv()` la busca en `get_resource_path("vendor")`, que en el `.exe` es `_internal/vendor`; y
  `python-mpv` solo la encuentra si su carpeta está en `%PATH%`, que es lo que `load_mpv()` arregla
  antes del `import` ([trampa 18f](docs/10-invariantes-y-trampas.md)). Sin la DLL, el `.spec` para
  con `SystemExit`. ✅ **Verificado compilando el 2026-10-20**: el `.exe`, lanzado **fuera del repo y sin
  la DLL en `%PATH%`**, reproduce AnimeAV1 por `HLS` y JKAnime por Desu, y carga la DLL de
  `_internal\vendor`. `dist/` pasa de **38 a 153 MB**.
  🆕 **Y desde el 2026-10-21 se para también si la DLL no es la que describen los avisos**: compara
  su sha256 con el de la sección generada de `THIRD-PARTY-NOTICES.txt` y la del paso 4 del
  `README.md`. Se arregla pasando `tools/actualizar_libmpv.py`, nunca editando el sha a mano. No
  comprueba si hay una DLL más reciente, a propósito: actualizar es una decisión.
  ✅ **0.2.2 compilada y probada por el usuario el 2026-10-21** (`HLS`, Desu y navegador).
- La versión de la app vive en `APP_VERSION` dentro del `.spec`.
- `resources/DB/` y las carpetas de pósters están en `.gitignore`: se generan en tiempo de ejecución.
- Hay **4** `# TODO:` en el código, en dos ficheros: `anime_window.py:152,155` (recomendaciones por
  género; alternar anime/manga) y `jkanime.py:156,217` (buscar en el directorio con texto vacío;
  acotar `get_recent_animes`). ✅ Reinventariados el 2026-10-21 con el grep: la auditoría de
  rendimiento no abrió ni cerró ninguno, pero desplazó una línea los de `anime_window.py`. El del selector de proveedor se cerró el 2026-07-30 y el de
  `main_window.py:32` —quitar «Anime» de los botones y el título— el 2026-08-20, con la fase 1 del
  rediseño.
  ⚠️ **Este apartado se ha equivocado tres veces**: hasta el 2026-08-07 citaba dos TODOs inventados;
  hasta el 2026-08-16 se dejó fuera los dos reales de `jkanime.py`; y el 2026-08-21 el propio grep
  devolvía 5 por un comentario que hablaba de uno ya cerrado. Inventaríalos con
  `git grep -n "TODO" -- src/` **después de cada cambio en `src/`**, no de memoria, y **mira lo que
  devuelve** (detalle en [`docs/12 §2`](docs/12-deuda-tecnica-y-roadmap.md)).
- ✅ **`datas` del `.spec` ya no lleva datos de usuario** (2026-08-17). Hasta entonces empaquetaba `resources/DB` y
  las 6 carpetas de pósters, así que el `.exe` distribuía la biblioteca **y las preferencias** del desarrollador.
  Hoy contiene **solo `resources/images/utils`**: la app crea el resto en el primer arranque. **No las vuelvas a
  añadir.** Dos trampas asociadas, ambas silenciosas: PyInstaller **ignora las carpetas vacías** (por eso parecían
  obligatorias) y los destinos de `datas` caen **dentro de `_internal/`**, no junto al `.exe` — por eso los ficheros
  legales se copian en un bloque posterior a `COLLECT`.
  Ver [`docs/10 § trampa 18d y 18e`](docs/10-invariantes-y-trampas.md) y [`docs/12 §7`](docs/12-deuda-tecnica-y-roadmap.md).
- **Licencia: GPL-3.0-or-later** desde el 2026-08-17. `LICENSE` (texto íntegro), aviso de copyright en el `README.md`,
  y `LEEME.txt` + `THIRD-PARTY-NOTICES.txt` que se copian junto al `.exe` al empaquetar — no son opcionales: cubren
  la §6 de la GPL y los avisos MIT/BSD/Apache/MPL de las dependencias. ⚠️ **`THIRD-PARTY-NOTICES.txt` caduca al tocar
  `requirements.txt`**; regenéralo ([`docs/11 §6`](docs/11-playbooks.md)). Estado completo en
  [`docs/12 §7`](docs/12-deuda-tecnica-y-roadmap.md).
  🆕 **El reproductor (2026-10-20)**: `python-mpv` es **GPL-2.0+ o LGPL-2.1+** y **`libmpv-2.dll` es
  GPL-3.0+ en conjunto** (mpv sin `-Dgpl=false`, FFmpeg con `--enable-gpl --enable-version3`, sin
  `nonfree`): compatibles con el proyecto. Los avisos pasan de 14 a **20** componentes —cuatro ya
  viajaban en el `.exe` sin aviso— y, por la §6, dan la versión exacta y los enlaces al fuente de mpv,
  FFmpeg y la receta de compilación, **más una oferta de facilitar el fuente** si caen.
  ⚠️ **Esa oferta compromete al autor**, y el usuario decidió mantenerla (2026-10-21).
  ✅ **L10 y L11 cerrados el 2026-10-21**: la DLL lleva **89** bibliotecas (más submódulos y 71 crates
  de Rust), y sus avisos van íntegros —el fichero pasa de 2 460 a 16 810 líneas—; la licencia de
  FFmpeg se comprobó en la etiqueta exacta. ⚠️ **La receta no anota qué versión de cada biblioteca
  compila**: las de los avisos son **reconstruidas** (último commit antes de compilar), y así lo dicen;
  el método acierta el hash real de mpv y de FFmpeg en las dos releases probadas (L12).
- ⚠️ **Los iconos `viendo_light/dark.png` y `pendientes_light/dark.png` existen en
  `resources/images/utils/` pero NO se usan, y activarlos no funcionaría**: ✅ comprobado, **los dos
  dibujos de cada par son de tinta negra**, así que como par (claro, oscuro) el del tema oscuro sería
  invisible. El icono único vale porque es bicolor. El código comentado que los invocaba se retiró el
  2026-08-21; si se quieren pares de verdad, hay que **redibujarlos**
  ([`docs/11 §5`](docs/11-playbooks.md)). Los cuatro PNG siguen **sin trackear**.
- **Todo lo gráfico que ha dibujado el proyecto se hace con PIL en tiempo de ejecución**, no como PNG
  en `resources/`: el pin del proveedor (2026-08-06), las estrellas de la calificación, los cuatro
  glifos de estado (`StatusPill.icon()`), los dos iconos de estado vacío (`empty_state.glyph()`) y,
  desde el 2026-09-24, los **15 glifos del reproductor** y su aro de «Cargando» (`player_icon()`).
  Todos se supermuestrean a 8x y se reducen con LANCZOS —sin eso un trazo diagonal sale dentado— y se
  cachean como `CTkImage` con variante clara y oscura. Receta en
  [`docs/11 §5`](docs/11-playbooks.md). ⚠️ El pin se distingue por **color** (azul/gris), no por
  relleno vs. contorno: la silueta contorneada es ilegible a los 20×20 a los que se pinta.
- ⚠️ **Los ~7 iconos de la sidebar y los dos GIF de carga son de origen desconocido** y
  probablemente incompatibles con la GPL del proyecto. Sus metadatos (512×512, `Software:
  www.inkscape.org`, DPI distintos entre sí) apuntan a descargas de **Flaticon**, cuya licencia
  gratuita **no permite sublicenciar**; los GIF no tienen metadatos y uno lleva un recorte `320×319`.
  La salida más probable es **redibujarlos con PIL**, como ya se hizo con el pin. Es la deuda **B11**:
  evidencia y alternativas en [`docs/12 §4`](docs/12-deuda-tecnica-y-roadmap.md).

---

## Roadmap

**El orden lo fijó el usuario el 2026-07-30 y no se reinterpreta. Sus tres primeros puntos ya están
cerrados —el pin y la integración de un proveedor nuevo el 2026-08-06, y la columna `provider_id` el
2026-08-16—, así que la lista avanza.**

1. ✅ ~~**Integrar un proveedor nuevo**~~ — **hecho el 2026-08-06 con JKAnime**. Validó que la
   abstracción aguanta sin tocarla: fue el primero que necesitó traducir géneros y el primero que
   mezcla dos técnicas de parseo. Quedan MonosChinos2 y TioAnime, ya sin urgencia.
2. ✅ ~~**Columna `provider_id` en `ANIMES`**~~ — **hecha el 2026-08-16**
   ([`docs/13 §14`](docs/13-selector-de-proveedor.md)). Trajo con ella tres cosas que resultaron
   inseparables: el proveedor como **tipo** (`AnimeProviderId`), **migrar una fila a otro proveedor** y
   el **aviso de duplicado** — sin las dos últimas, poder elegir proveedor convierte la biblioteca en
   un sitio donde el mismo anime puede acabar dos veces. De paso, el buscador de las cuatro vistas de
   estado pasó a ser **local**. 351/351 comprobaciones.
   ✅ **Commiteado** en `a3d4331` («Actualización v0.2.0 del proyecto»), rama `main`.

3. ✅ ~~**Rediseño completo de la interfaz**~~ — **hecho entre el 2026-08-20 y el 2026-08-21**, en
   **9 fases**, una por sesión (`.claude/plan-rediseno/`). No estaba en la
   lista original: se cruzó por delante y cerró de paso **cinco puntos** que sí estaban.

4. ✅ ~~**Reproducir los episodios dentro de la aplicación**~~ — **hecho entre el 2026-09-23 y el
   2026-10-20**, en **7 fases**, una por sesión (`.claude/plan-reproductor/`,
   cierre en su `ESTADO.md`). Tampoco estaba en la lista. Cerró de paso la **deuda nº 1** del rediseño
   (los servidores en el hilo de Tk). ✅ **El audio lo oyó el usuario el 2026-10-21**, que era lo
   último sin verificar. **Deja sin hacer, a propósito**:
   los hosters aplazados (**B14**), recordar el minuto donde lo dejaste (una columna más, no pedida),
   elegir calidad o subtítulos (los playlists no ofrecen alternativas) y descargar episodios.

Después, sin orden fijado. **El rediseño se llevó por delante buena parte de lo que había aquí**:

- ✅ ~~Renombrar «animes recientes» a **nuevos lanzamientos**~~ — fase 1.
- **Convivencia anime + manga** *(lo único que queda del bloque, y ya con la mitad hecha)*:
  - Desplegable en la esquina inferior izquierda para elegir *animes / mangas / ambos*, accesible desde todas las
    pestañas salvo la ficha de detalle, con opción de fijar la elección por defecto. La preferencia ya tiene dónde
    guardarse: una fila más en `USER_SETTINGS`, sin migración ([`docs/11 §2c`](docs/11-playbooks.md)).
  - Nuevos lanzamientos a dos columnas (animes / mangas) si se eligen ambos; si no, como ahora.
  - ✅ ~~Quitar «Anime» del nombre de las pestañas~~ (fase 1) y ✅ ~~paginarlas~~ (fases 2, 5 y 6;
    desde el 2026-09-02 el tamaño de página es `columnas × 2`, no una constante). **Falta** el filtro
    Animes / Mangas / Ambos.
  - ✅ ~~En «viendo», resultados en cascada de uno por fila indicando el último capítulo visto~~ — fase 3.
  - ✅ ~~En «favoritos», calificación personal guardada y ordenación por ella~~ — fase 5, columna
    `rating` ([`docs/04 §3b`](docs/04-modelo-de-datos.md)).
- Bloque «Si te ha gustado *X*, te puede interesar…» al final de la lista de episodios, con 4 animes del mismo género.
- Integrar más proveedores (MonosChinos2, TioAnime) y proveedores de manga.
- **Deuda que deja el rediseño**, por orden de lo que más molesta:
  1. ✅ ~~**La petición de servidores de la ficha sigue en el hilo de Tkinter**~~ — **cerrada el
     2026-09-24** con la fase 2 del reproductor, que la necesitaba antes de añadir una segunda
     petición en el mismo punto. ⚠️ «Ya ningún sitio de la GUI sale a la red desde el hilo de la
     interfaz» **no era cierto** hasta el 2026-10-21: quedaba el póster de la ficha sin caché.
  2. **B11**: los ~7 iconos de la barra lateral y los 2 GIF de carga siguen siendo de origen
     desconocido ([`docs/12 §4`](docs/12-deuda-tecnica-y-roadmap.md)). El rediseño **no la hizo
     crecer**: sus diez glifos se dibujan con PIL.
  3. ✅ ~~El orden de «Pendientes» **no se persiste**~~ — **cerrada el 2026-10-26**: se guarda en
     `USER_SETTINGS` (`pending_order`) como el de «Favoritos», con un código estable y no el texto del
     desplegable ([`docs/13 §4`](docs/13-selector-de-proveedor.md)).
  4. ✅ ~~**B12**: el refresco de episodios llega **solo a las ≤3 filas de la banda «Retomar»**~~ —
     **cerrada el 2026-10-27** con `EpisodeRefresher`: «Viendo» y «Pendientes» se refrescan en segundo
     plano tras la portada y al entrar, y se repintan en el sitio. ⚠️ **«Finalizados» queda fuera a
     propósito**: lo terminado casi nunca crece, y son 24 peticiones más
     ([trampa 38](docs/10-invariantes-y-trampas.md), [`docs/12 §4`](docs/12-deuda-tecnica-y-roadmap.md)).
  5. **B13**: cambiar de vista bloquea la interfaz **270-620 ms**. ✅ Rediagnosticada el 2026-10-21:
     ~70 % es crear los widgets de CustomTkinter (8-12 mil llamadas a Tcl por vista), y los JPG cuestan
     menos de 60 ms. Una caché de `CTkImage` **no** es el arreglo, y además reintroduciría la
     [trampa 55](docs/10-invariantes-y-trampas.md). La palanca es conservar las vistas construidas en
     vez de rehacerlas. Opcional ([`docs/12 §4`](docs/12-deuda-tecnica-y-roadmap.md)).
  6. **B16-B17** (2026-10-21, opcionales): sin `requests.Session` (~90 ms por petición, casi todo en
     segundo plano) y el `<Configure>` de la raíz, que se dispara con el de cualquier widget.
- **Deuda que deja el reproductor**:
  1. **B14**: los hosters sin resolutor siguen abriendo el navegador. Lo que más valdría es un segundo
     hoster por proveedor que no dependa del mismo origen: zilla estuvo caído tres días en septiembre.
  2. ✅ ~~**L10 / L11**~~ — **cerradas el 2026-10-21** con `tools/actualizar_libmpv.py`
     ([`docs/12 §7`](docs/12-deuda-tecnica-y-roadmap.md)).
  3. **C12**: la DLL no está en el repo; un clon limpio no compila el `.exe` sin el paso 4 del README.
  4. ✅ ~~**B15**: «Cargando» no tiene tope propio~~ — **cerrada el 2026-10-21**: 30 s desde `play()`
     hasta que empieza a verse, y al vencer cae al navegador ([trampa 54](docs/10-invariantes-y-trampas.md)).

---

## Documentación detallada — `.claude/docs/`

Este fichero es el **resumen de entrada**. La documentación profunda, verificada contra el código y
contra los sitios reales, vive en [`.claude/docs/`](docs/README.md).

Guía de colaboración (cómo plantear una tarea en este repo, qué asumo por defecto y qué palancas
cambian mi comportamiento): [`.claude/COMO-PEDIR-TAREAS.md`](COMO-PEDIR-TAREAS.md).

**Antes de tocar cualquier cosa, lee [`docs/10-invariantes-y-trampas.md`](docs/10-invariantes-y-trampas.md)**
— **58** trampas con su síntoma observable.

| Documento | Qué responde |
|---|---|
| [docs/README.md](docs/README.md) | Índice, mapa de lectura «si tocas X, lee Y», cómo mantenerlo vivo |
| [docs/01-arquitectura.md](docs/01-arquitectura.md) | Capas, dependencias permitidas/prohibidas, invariantes de diseño |
| [docs/02-mapa-de-modulos.md](docs/02-mapa-de-modulos.md) | Ficha por módulo: API pública, dependencias, efectos secundarios |
| [docs/03-flujos-de-ejecucion.md](docs/03-flujos-de-ejecucion.md) | Los **13** flujos en diagramas de secuencia, con el hilo de cada paso |
| [docs/04-modelo-de-datos.md](docs/04-modelo-de-datos.md) | `AnimeInfo` vs `AnimeRecord`, esquema real de `ANIMES`, rangos, estados |
| [docs/05-proveedores-y-scraping.md](docs/05-proveedores-y-scraping.md) | Contrato, payload de AnimeAV1, selectores de AnimeFLV, fallback, diagnóstico **y los hosters de vídeo (§9)** |
| [docs/06-gui-y-vistas.md](docs/06-gui-y-vistas.md) | `MainWindow` como hub, ciclo de vida de una vista, layout, temas |
| [docs/07-concurrencia-e-hilos.md](docs/07-concurrencia-e-hilos.md) | Qué corre en qué hilo, reglas y carreras conocidas |
| [docs/08-convenciones-y-estilo.md](docs/08-convenciones-y-estilo.md) | Cabecera obligatoria, singletons, **plantillas copiables** |
| [docs/09-verificacion-y-pruebas.md](docs/09-verificacion-y-pruebas.md) | Cómo probar cada capa sin GUI; scripts listos; checklist manual |
| [docs/10-invariantes-y-trampas.md](docs/10-invariantes-y-trampas.md) | **Empieza por aquí.** **58** trampas con síntoma observable |
| [docs/11-playbooks.md](docs/11-playbooks.md) | Recetas: añadir vista, columna, proveedor, campo, **resolutor**; empaquetar |
| [docs/12-deuda-tecnica-y-roadmap.md](docs/12-deuda-tecnica-y-roadmap.md) | TODOs con `fichero:línea`, discrepancias, riesgos, roadmap técnico **y licencia/cumplimiento de la distribución (§7)** |
| [docs/13-selector-de-proveedor.md](docs/13-selector-de-proveedor.md) | Selector de proveedor, `DB_user.db` **y la columna `provider_id`** (§14). **Léelo antes de tocar `animeProviderMgr.py`, `main_window.py` o `anime_window.py`** |

> Los documentos marcan la procedencia de cada afirmación: ✅ verificado en ejecución ·
> 📖 leído en código · ⚠️ sin verificar.

> **Correcciones a este fichero** detectadas al auditarlo (detalle en
> [docs/12 §3](docs/12-deuda-tecnica-y-roadmap.md)): no todos los `update_*` devuelven `False` si el
> anime no existe; el orden de `episodes` antes de invertirse **depende del proveedor**.
>
> La tercera corrección (`get_anime_image()` no buscaba en `resources/images/watching/`) quedó
> **resuelta el 2026-07-30** en `83a8448`, junto con el póster a 20×20; el texto de arriba ya refleja
> el comportamiento actual.
