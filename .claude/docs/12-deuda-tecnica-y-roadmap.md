# 12 — Deuda técnica y roadmap

| | |
|---|---|
| **Fecha** | 2026-08-16 · **Commit** `54fb3d6` · árbol **sucio**: 16 ficheros de `src/` sin commitear |
| **Cubre** | `src/**`, `.claude/CLAUDE.md`, `README.md`, `requirements.txt`, `MiBibliotecaAnime.spec` |
| **Última revisión** | 2026-08-16 (**columna `provider_id`**): **B4 y B10 cerrados**, R2 cerrado del todo, punto 2 del roadmap cerrado, e inventario de TODOs corregido otra vez (**5**, no 3 — los 2 de `jkanime.py` nunca se inventariaron) |

Procedencia: ✅ verificado en ejecución · 📖 leído en código · ⚠️ sin verificar.

---

## 1. Estado del árbol de trabajo

⚠️ **2026-08-16: el árbol NO está limpio.** La columna `provider_id` está implementada y verificada
(351 comprobaciones, [09 §3c](09-verificacion-y-pruebas.md)) pero **sin commitear**: 16 ficheros
modificados bajo `src/`, +1 312 / −273 líneas. El commit es lo siguiente que hay que hacer.

| Capa | Ficheros |
|---|---|
| Dominio | `APIs/common/models.py`, `APIs/common/animeProviderMgr.py` |
| Proveedores | `animeav1.py`, `jkanime.py`, `animeflv.py` (solo el tipo de `PROVIDER_ID`) |
| Datos | `dataPersistence/animesPersistence.py` |
| GUI | `gui/main_window.py`, `gui/anime_window.py`, las **6** vistas, `utils/buttons/utilsButtons.py` |
| Infra | `utils/utils.py` |

✅ `git status` sobre **`18311e3`** (rama `develop`), 2026-08-07. El árbol estaba limpio entonces. Las
dos tareas que la revisión anterior daba por pendientes de commitear ya están dentro:

| Commit | Fecha | Qué entró |
|---|---|---|
| `ab5e75b` | 2026-08-06 | **El pin de proveedor** — `main_window.py` v0.2, `anime_window.py` v0.3 (el selector de la ficha pasa a etiqueta), `userPersistence.py` v0.2, + los 4 iconos `{fijado,no_fijado}_{light,dark}.png` |
| `c9cc6d0` | 2026-08-06 | Documentación del pin |
| `a0d08f1` | 2026-08-06 | **El proveedor JKAnime** — `APIs/jkanime/jkanime.py` (v0.1) + registro en `main_window.py` |
| `d99a2ee` | 2026-08-07 | `.spec`: `hiddenimports` completado y `gui.anime_windows` → `gui.anime_window` |
| `ae126fd` | 2026-08-07 | `.spec`: retirado `gui.sidebarButtons.sidebarButton`, que no existía → **cierra la trampa 18a** |
| `e6d1a73` | 2026-08-07 | Eliminado el stub muerto `WatchingAnimeButton` → **cierra B9 y la trampa 19** |
| `18311e3` | 2026-08-07 | Documentación de JKAnime |

**Lo único sin trackear hoy**:

| Ruta | Qué es |
|---|---|
| `resources/images/utils/{viendo,pendientes}_{light,dark}.png` | 4 iconos generados pero **aún sin usar**: su carga sigue comentada en `watchingAnimes.py:23-25` y `pendingAnimes.py:23-25` |
| `.vscode/` | configuración local del editor |
| `.claude/settings.local.json` | permisos locales de Claude Code |

> ⚠️ Los 4 PNG de «viendo» y «pendientes» llevan sin trackear desde antes del 2026-07-30 y **no los
> referencia ningún código activo**. O se descomenta su uso, o se borran: hoy son solo ruido en
> `git status`.

✅ **La migración ya se ejecutó sobre la BD real del usuario** (2026-07-30). Copia previa en
`resources/DB/backups/DB_Animes_20260730_011337.db`; una segunda pasada responde «esquema correcto, no
hay nada que migrar», confirmando la idempotencia sobre datos reales.

✅ **Reparación de datos** (2026-07-30): 3 de las 25 filas tenían la sinopsis con mojibake persistido de
antes del arreglo de A5. Se re-descargaron con el scraper corregido; copia previa en
`resources/DB/backups/DB_Animes_20260730_013507.db`.

---

## 2. TODOs reales en el código

✅ Inventario **rehecho con `git grep -n "TODO" -- src/` el 2026-08-16**. Son **5**, no 3:

| # | Ubicación | Contenido | Documento afectado |
|---|---|---|---|
| 1 | `gui/anime_window.py:44-45` | Al final de la lista de episodios, frame «Si te ha gustado X, te puede interesar…» con 4 animes del mismo género | [06](06-gui-y-vistas.md), [03](03-flujos-de-ejecucion.md) |
| 2 | `gui/anime_window.py:47` | Botón para alternar entre manga y anime | [06](06-gui-y-vistas.md), [01](01-arquitectura.md) |
| 3 | `gui/main_window.py:32` | Quitar la palabra «Anime» de los nombres de botones y del título | [06](06-gui-y-vistas.md) |
| **4** | `APIs/jkanime/jkanime.py:191` | Si el texto de búsqueda está vacío, buscar en `DIRECTORY_URL` en vez de en `SEARCH_URL` | [05 §3b](05-proveedores-y-scraping.md) |
| **5** | `APIs/jkanime/jkanime.py:264` | Corregir `get_recent_animes` para no quedarse con todo lo que aparece en la portada | [05 §3b](05-proveedores-y-scraping.md) |
| ~~—~~ | ~~`gui/main_window.py:31-34`~~ | ✅ **Cerrado el 2026-07-30**: selector de proveedor en la sidebar **y** en la ficha, con la preferencia persistida en la BD nueva `DB_user.db`. El TODO se ha borrado del código. Ver **[13](13-selector-de-proveedor.md)** | **[13](13-selector-de-proveedor.md)**, [04 §0](04-modelo-de-datos.md), [05 §5b](05-proveedores-y-scraping.md) |

> ⚠️ **Segunda corrección de este inventario, y por el motivo contrario a la primera.** El 2026-08-07
> se bajó de 5 a 3 quitando dos TODOs **inventados**; hoy sube a 5 porque faltaban dos **reales**, los
> de `jkanime.py`, que entraron con el proveedor el 2026-08-06 y nadie volvió a contar. `CLAUDE.md`
> siguió diciendo «3» nueve días.
>
> La lección de 2026-08-07 seguía siendo correcta —no inventariar de memoria— pero incompleta: hay que
> **volver a ejecutar el `git grep` después de cada cambio en `src/`**, no solo cuando se sospecha de
> una cifra.

> ⚠️ **Corrección de esta sección (2026-08-07).** Las revisiones anteriores listaban dos TODOs más que
> **no existen ni han existido nunca** con ese contenido:
>
> - **«#5 `utilsButtons.py:56` — el color del texto debe cambiar a blanco en apariencia oscura».** Ese
>   fichero no contiene ningún `TODO` desde `d0fb393`, muy anterior a la primera versión de estos
>   documentos. El único que tuvo (`c2009e0`) hablaba de *persistir el episodio visto*, no de colores.
>   El comportamiento sí es real y sigue pendiente —`SidebarButton` fija `text_color="black"` y solo
>   `change_appearance_mode_event` lo corrige—, pero es **deuda observada, no un TODO del autor**:
>   está registrado como tal en [06 §5](06-gui-y-vistas.md).
> - **«#6 `recentAnimes.py:19` — renombrar “recientes” a “nuevos lanzamientos”».** `git log -S TODO`
>   sobre ese fichero no devuelve **ningún** commit: nunca contuvo la cadena. La cadena
>   «lanzamiento» no aparece en todo `src/`. Es un punto del **roadmap** ([§6](#6-el-roadmap-traducido-a-impacto-técnico)),
>   que alguien ancló a un `fichero:línea` inventado.
>
> Lección: un `fichero:línea` da apariencia de verificación. Los TODOs se inventarían con
> `git grep -n "TODO" -- src/`, nunca de memoria.

> El TODO #4 era el más caro: implicaba **la primera BD nueva** del proyecto (`DB_user.db`), además de
> tocar el manager de proveedores, la ficha de detalle y los 6 puntos de clic. **Cerrado el
> 2026-07-30**; decisiones de diseño y lo que quedó fuera, en [13](13-selector-de-proveedor.md).

---

## 3. Discrepancias entre `CLAUDE.md` y el código

Auditado punto por punto. Donde el código contradice a `CLAUDE.md`, **gana el código**.

| # | `CLAUDE.md` afirma | Realidad | Evidencia |
|---|---|---|---|
| D1 | «el resto de updates asumen que ya está en BD y **devuelven `False`** si no» | ✅ Solo 3 de 6 lo hacen. `update_anime_episodes`, `update_anime_to_not_favourite` y `update_anime_to_not_pending` devuelven **`True`** | `sqlite.py:106-120` no mira `rowcount` |
| ~~D2~~ | Registro: «`AnimeFLVSingleton(), default=True` …» en el ejemplo del docstring | ✅ **Corregido el 2026-08-16**: el docstring del manager ya muestra el registro real, con los tres proveedores y el orden del fallback | `animeProviderMgr.py:146-149` vs `main_window.py:47-49` |
| ~~D3~~ | «`get_anime_image()` busca en `favourite`, `finished`, `pending`, `recent_animes` y `search`» | ✅ **Resuelto (2026-07-30, `83a8448`)**: `watching` ya está en la lista | `utils.py:187` |
| ~~D4~~ | «la ficha de detalle los pide a `(195, 275)`» | ✅ **Resuelto (2026-07-30, `83a8448`)**: la rama de red ya pasa `size=` | `utils.py:195-196` |
| D5 | «`AnimeAV1` … usa el DOM solo como *fallback*» | 📖 Matiz: **`poster` y `genres` salen SIEMPRE del DOM**, no del payload — aunque los géneros están en el payload | `animeav1.py:219-222` |
| D6 | «`episodes` se guarda invertido» | ✅ Cierto, pero no dice que **el orden de partida depende del proveedor** (AV1 ascendente, FLV descendente), así que el resultado en BD es opuesto según quién sirvió el dato | `animeav1.py:227` vs `animeflv.py:222-223` |
| D7 | «Muestra … la lista de episodios (**los 25 primeros**, `[:25]`)» | ✅ Correcto. El comentario del propio código dice «24» (`anime_window.py:955`) | `anime_window.py:916` |
| **D8** | «Hay **3** `# TODO:` en el código, todos en dos ficheros» | ❌ **Falso otra vez, por el motivo contrario (2026-08-16)**. Son **5**: faltaban los dos de `jkanime.py`, que entraron el 2026-08-06. El diagnóstico de 2026-08-07 (que `recentAnimes.py` y `utilsButtons.py` no tenían ninguno) seguía siendo correcto | `git grep -n TODO -- src/`, §2 |
| ~~D9~~ | «`.spec` … no incluye `APIs.animeav1.animeav1`, `APIs.common.animeProviderMgr` ni `APIs.common.models`, y declara `gui.anime_windows`» | ✅ **Cerrado del todo (2026-08-07)**: corregido en el `.spec` y reescrito en `CLAUDE.md`; `gui.sidebarButtons.sidebarButton` retirado en `ae126fd`. ✅ Los 18 `hiddenimports` resuelven a módulos reales | `MiBibliotecaAnime.spec:21-40` |
| D10 | No menciona `attrs` | ✅ **Ya no aplica (2026-07-28)**: era una dependencia no declarada; el import se cambió a `dataclasses` de la stdlib y `attrs` deja de ser dependencia | [10, trampa 18b](10-invariantes-y-trampas.md) |
| D11 | No menciona el estado de AnimeFLV | ✅ `get_anime_episode_servers` devuelve `[]`; el usuario confirma que el sitio está caído / en desuso | [05 §2](05-proveedores-y-scraping.md) |

### El `README.md` también miente un poco

📖 Anuncia funcionalidades que **no existen en el código**:

- «asigna **calificaciones**» (`README.md:27`) — no hay campo de calificación en `AnimeField`.
- «categoriza por estados (*Viendo, Completado, **Dropeado**, Pendiente*)» (`:27`) — **no hay estado
  «dropeado»**; los estados reales son favorito/viendo/finalizado/pendiente.
- «**100 % offline**, privada y **sin dependencias web**» (`:5`) — la app **depende** de la red para
  todo lo que no esté ya en BD (recientes, fichas, búsquedas, servidores, pósters).
- El árbol de `:83-122` no incluye `APIs/animeav1/` ni `APIs/common/`.

---

## 4. Deuda técnica, por gravedad

### 🔴 Alta

| # | Problema | Dónde | Impacto |
|---|---|---|---|
| A3 | ~~**`.spec` desactualizado**~~ → queda **solo** el empaquetado de `resources/DB` | `MiBibliotecaAnime.spec:12` | ✅ **`hiddenimports` cerrado el 2026-08-07**; el problema grave (la BD) **sigue vivo** |
| A6 | **Widgets Tk desde hilos daemon** | `main_window.py:481-500`, `searchAnimes.py:220-225`, `utils.py:146-147` | Riesgo de cuelgue; funciona por suerte estructural. 🆕 **Reducido**: los 6 puntos de clic y el buscador de la biblioteca ya no lo hacen, y **C2 se cerró** — era un crash reproducible, no teórico ([07 C2](07-concurrencia-e-hilos.md)) |

> **A3 — corrección de diagnóstico** 📖. La versión anterior afirmaba que el `.exe` «falla en runtime»
> por los `hiddenimports` incompletos. **No es así**: todos los imports del proyecto son estáticos, así
> que PyInstaller los resuelve por análisis de dependencias; `hiddenimports` solo hace falta para
> imports dinámicos, y los nombres fantasma (`gui.anime_windows`, `gui.sidebarButtons.sidebarButton`)
> solo generan un warning al compilar.
>
> El problema real del `.spec` es otro y no estaba registrado: **`datas` empaqueta `resources/DB`**
> (`:12`), de modo que el ejecutable distribuye la biblioteca personal del desarrollador, y como el
> build es *onedir* sobre `sys._MEIPASS`, cada actualización pisa la BD del usuario final con la del
> desarrollador. Es el mismo hecho que C11, pero su gravedad es alta, no baja.
>
> ✅ **La mitad de `hiddenimports` quedó saldada el 2026-08-07.** Se añadieron
> `APIs.animeav1.animeav1`, `APIs.jkanime.jkanime`, `APIs.common.animeProviderMgr`,
> `APIs.common.models` y `dataPersistence.userPersistence`; se corrigió `gui.anime_windows` →
> `gui.anime_window` (`d99a2ee`) y se retiró `gui.sidebarButtons.sidebarButton` (`ae126fd`).
> Comprobado el 2026-08-07: los **18** nombres declarados resuelven a ficheros reales de `src/`, y el
> único módulo ausente es `app.py`, que es el script de entrada y no debe figurar.
> ⚠️ **Nada de esto se verificó compilando**: la lista se corrigió leyendo los `import` reales.
> Lo de `resources/DB` **no se ha tocado** — es una decisión de distribución, no un descuido, y es lo
> que mantiene A3 en 🔴.

### 🟡 Media

| # | Problema | Dónde |
|---|---|---|
| B2 | La ordenación por géneros nunca se aplica (`str` vs enum) | `utilsButtons.py:341` |
| B3 | Guard antidoble-búsqueda inoperante (`.start()` → `None`) | `searchAnimes.py:206,212,335` |
| ~~B4~~ | ~~HTTP en el hilo de UI: servidores y clic desde 5 de las 6 vistas~~ ✅ **Casi cerrado (2026-08-16)**: los **6** puntos de clic van ya en hilo + `after(0,…)`. Queda **solo** la llamada de servidores | `anime_window.py:1116-1121` ([07 C5](07-concurrencia-e-hilos.md)) |
| B6 | Las 4 listas cacheadas de `MainWindow` **no las usa nadie** | `main_window.py:87-93` vs `favouriteAnimes.py:75` |
| B7 | `remove_from_finished` mueve a *pendiente* en BD pero **borra el póster sin recrearlo** en `pending/` | `anime_window.py:859-865` |
| B8 | `time.sleep(0.1)` en el hilo de UI × 7 | [07 §5](07-concurrencia-e-hilos.md) |
| ~~B10~~ | ~~El buscador de las vistas de estado va **contra la red**, no contra la BD~~ ✅ **Cerrado (2026-08-16)**: búsqueda **local** primero, la web solo suma. Era peor de lo diagnosticado —no era solo «no funciona sin conexión», sino que **perdía animes** según el proveedor puesto ([trampa 26](10-invariantes-y-trampas.md)) | `utilsButtons.py:23-166` |

> **B7, alcance medido el 2026-07-30** ✅. Es un caso particular de algo más general: la BD fuerza la
> exclusividad viendo/finalizado/pendiente (`_set_status`), pero la GUI solo gestiona el póster **del
> estado que pulsas**. Consecuencias, contadas sobre la biblioteca real (25 animes):
>
> - **6 pósters huérfanos** en `resources/images/watching/` — animes que salieron de «viendo» y dejaron
>   su fichero atrás. Solo gastan disco; las vistas filtran por BD.
> - La variante **visible** es únicamente `remove_from_finished`: mueve el anime a *pendiente* en BD y
>   borra el póster de `finished/` sin crearlo en `pending/`, así que la vista de pendientes muestra el
>   recuadro gris de `load_image`. ⚠️ Hoy no se da en los datos del usuario: 0 animes marcados sin
>   póster en su carpeta.

### 🟢 Baja

| # | Problema | Dónde |
|---|---|---|
| C1 | Errata en `__module__`: `animesPersistence` sin `.py`. ✅ Las otras dos (`anime_wnidow.py`, `animeProvider.py`) **ya están corregidas** en el código | `animesPersistence.py:3`, [08 §1](08-convenciones-y-estilo.md) |
| C2 | `update_gif` suelto, muerto y roto | `utils.py:48-51` |
| C3 | `removeprefix` devuelve `None` si los tipos difieren | `utils.py:24-38` |
| C4 | `SearchButton` duplicado (widget vs vista) | `utilsButtons.py:37` y `searchAnimes.py:35` |
| C5 | Nomenclatura mixta `show_*` / `__show_*` en las vistas | [06 §3](06-gui-y-vistas.md) |
| C6 | `AccordionFilterButton` crea un frame nuevo en cada expansión | `utilsButtons.py:122-128` |
| C7 | `info_frame` con `fg_color="white"` fijo, no respeta el tema | `anime_window.py:176` |
| C8 | `-> (bool, list)` como anotación de tipo | `sqlite.py:122` |
| C9 | Comentario «24 primeros» donde el código dice 25 | `anime_window.py:447` |
| C10 | `README.md` describe funciones inexistentes | §3 |
| C11 | La BD del desarrollador se empaqueta en el `.exe` | `MiBibliotecaAnime.spec:12` |

### ✅ Resuelto

| # | Problema | Resuelto | Cómo |
|---|---|---|---|
| A1 | **Sin migraciones de BD** — `start()` (`animesPersistence.py:221-227`) solo creaba la tabla si el `.db` no existía. Cualquier columna nueva desalineaba silenciosamente las lecturas en instalaciones con datos previos (trampas 1 y 2). Bloqueaba el TODO #4 y medio roadmap | 2026-07-30 | Esquema declarativo `AnimesPersistence.SCHEMA` (lista de `TableSchema`) + `validate_db_integrity()`, llamado desde `start()`. Motor genérico en `utils/db/sqlite.py` (v1.1): `sqlite_affinity()`, `TableSchema`, `SqlUtils.execute_transaction/get_table_names/get_table_columns`, `ServiceDB.validate_schema/diff_table/apply_table_migration/backup_db`. Escala de `CREATE TABLE` → `ALTER TABLE ADD COLUMN` → reconstrucción transaccional copiando **por nombre de columna**. Copia de seguridad en `resources/DB/backups/` antes de la primera modificación. ✅ Verificado con 57 comprobaciones sobre copias de la BD real (24 filas): retipado, columna al final, columna en medio, desorden, tabla nueva, BD desde cero, idempotencia y rollback |
| A2 | **`attrs` no declarada** — `searchAnimes.py:15` hacía `from attr import dataclass` de un paquete ausente de `requirements.txt`, presente solo como transitiva de `selenium → trio → outcome → attrs`. Entorno limpio → `ModuleNotFoundError: No module named 'attr'` | 2026-07-28 | Sustituido por `from dataclasses import dataclass` (stdlib). Se elimina la dependencia en vez de declararla; `src/` ya no referencia `attrs` ni `selenium`. ✅ Verificado importando el módulo e instanciando `AnimeSearch` |
| A5 | **Mojibake de AnimeAV1** — el sitio responde sin `charset`, requests aplicaba el defecto de la RFC 2616 (ISO-8859-1) y el texto mal decodificado llegaba a `AnimeInfo.synopsis`, a la pantalla **y a la BD**. Afectaba también a `title` (extremo que la trampa 14 daba por no comprobado) | 2026-07-30 `94b497e` | Helper `_fetch()` (`animeav1.py:37-56`) que fija UTF-8 **solo si el servidor no declara charset**; las 5 llamadas de scraping pasan por él. v0.2 → v0.3. ✅ Verificado contra el sitio real (ficha, portada y búsqueda: 0 marcadores). **Datos ya guardados**: 3 de 25 filas reparadas re-descargando la ficha, con copia previa en `resources/DB/backups/` |
| B5 | **`AnimeWindowViewer(mw, None)` petaba** — el constructor iteraba `.episodes` sin guarda y las 6 vistas pasaban directo el retorno de `get_anime_info`, que es `None` si fallan todos los proveedores. Tkinter se tragaba el `AttributeError`: el clic no hacía nada y la app parecía colgada | 2026-07-30 `1bfdf0f` | `show_anime_info_error()` (`anime_window.py:30-46`) con log y `messagebox`; guarda en los 6 puntos de clic; contrato en el constructor (`:77-105`): `None` → `ValueError`, `episodes=None` → `dataclasses.replace` sobre **una copia**. Corregido además `recentAnimes.py`, que comprobaba el `None` pero caía de vuelta al objeto obsoleto con `.episodes` a `None`. ✅ Verificado simulando la caída total de proveedores |
| A4 | **Póster a 20×20 al descargar** — la rama de red de `get_anime_image` construía el `CTkImage` sin `size=`, y ese parámetro (no el tamaño del PIL) es lo que se pinta; su defecto es `(20, 20)`, así que el `.resize()` se hacía y se tiraba | 2026-07-30 `83a8448` | `ctk.CTkImage(Image.open(...), size=image_size)` sin `.resize()`, igual que `load_image()`. Se añadió `timeout=_REQUEST_TIMEOUT`: era la única petición del módulo sin timeout y corre en el hilo de UI. `utils.py` v0.1 → v0.2. ✅ Verificado contra un póster real: `(195, 275)` |
| B9 | **Stub muerto `WatchingAnimeButton`** — `watchingAnimes/__init__.py` definía una clase vacía con el mismo nombre que la real. `main_window.py:25` importa desde el **módulo**, así que nunca llegó a usarse, pero `from gui.sidebarButtons.watchingAnimes import WatchingAnimeButton` habría cogido el stub sin error de importación | 2026-08-07 `e6d1a73` | Fichero vaciado. ✅ Los **18** `__init__.py` de `src/` están hoy todos a 0 bytes. Ver [trampa 19](10-invariantes-y-trampas.md) |
| B1 | **`get_anime_image` no buscaba en `watching/`** — provocaba una descarga redundante y, combinado con A4, el póster diminuto en la ficha de un anime que solo estuviera en «viendo» | 2026-07-30 `83a8448` | `watching` añadido a `subfolders` (`utils.py:168`), ahora las 6 categorías. ✅ Verificado con `one-piece-gyojin-touhen` (solo en `watching/` en la BD real): resuelve desde disco aun pasándole una URL inválida |

> Los identificadores retirados (`A2`, `A4`, `A5`, `B1`, `B5`, `B9`) **no se reutilizan**: otros
> documentos los citan.

---

## 5. Los 3 riesgos que más preocupan

### ~~R1 — La ausencia de migraciones bloquea todo el roadmap~~ ✅ **Resuelto (2026-07-30)**

Cada punto interesante del roadmap (calificación personal, preferencia de proveedor, convivencia
anime/manga) necesita **columnas o tablas nuevas**. Hasta el 2026-07-30, añadirlas corrompía
silenciosamente las instalaciones existentes — y la BD del usuario, con 24 animes reales, era
exactamente ese caso.

`validate_db_integrity()` lo resuelve: el esquema se declara en `AnimesPersistence.SCHEMA` y la BD se
alinea en cada arranque, con copia de seguridad previa. Ver [A1 en §4 → Resuelto](#-resuelto),
[04 §3](04-modelo-de-datos.md) y [11 §2](11-playbooks.md).

**Riesgo residual**: la reconstrucción **descarta** las columnas presentes en BD que no estén
declaradas en `SCHEMA` (quedan en la copia de seguridad, y se avisa por consola). No se purgan las
copias antiguas, así que `resources/DB/backups/` crece una copia por migración.

### ~~R2 — Dependencia de un único proveedor sano~~ ✅ **Cerrado como riesgo alto (2026-08-16)**

✅ **JKAnime integrado y verificado** el 2026-08-06 ([05 §3b](05-proveedores-y-scraping.md)), y
registrado **entre** AnimeAV1 y AnimeFLV, así que el fallback ya tiene una primera parada que
funciona. Los 5 métodos del contrato responden, servidores de vídeo incluidos — que era justo lo
que AnimeFLV no cubría.

El texto original del riesgo, que sigue explicando por qué importaba:

> AnimeAV1 es el por defecto y **el único operativo**: AnimeFLV ya no sirve servidores de vídeo. El
> mecanismo de fallback existe pero hoy no tiene a dónde caer. Además, el parseo de AnimeAV1 depende
> de **regex sobre un payload JS no estructurado**: cualquier despliegue del sitio puede romperlo sin
> aviso, y el fallback al DOM solo cubre `title`, `synopsis` y el conteo de episodios — **no** los
> servidores. Integrar un tercer proveedor es una medida de resiliencia, no un capricho.

⚠️ **Lo que NO resuelve.** JKAnime depende a su vez de un payload JS incrustado para el directorio
y de un endpoint con CSRF para los episodios: hereda la misma fragilidad estructural que se le
achaca a AnimeAV1, solo que en superficies distintas. Que haya dos proveedores sanos reduce la
probabilidad de quedarse a ciegas, **no** la de que cualquiera de los dos se rompa en silencio.

⚠️ Tampoco resuelve el fallo **parcial** descrito abajo, que sigue sin detectarse.

✅ **Mitigación completada (2026-08-16)**: el selector de proveedor
([13](13-selector-de-proveedor.md)) da la palanca para **saltarse** el que esté roto, la etiqueta de
la ficha hace **visible** qué proveedor sirvió realmente cada anime, y el pin permite probar un
proveedor roto sin ensuciar la configuración.

✅ **Lo que faltaba —poder saltarse el proveedor roto para un anime concreto ya guardado— entró con la
columna `provider_id`**: hoy un anime guardado se abre por su proveedor, una desviación del
desplegable lo abre por otro **re-localizándolo por título**, y el botón «Actualizar a X» permite
**mudar la fila** al proveedor que funcione, conservando los episodios vistos. Es la respuesta
completa a este riesgo desde la GUI ([13 §14](13-selector-de-proveedor.md)).

**Agravado el 2026-07-30** por lo aprendido al arreglar A5: el proveedor no solo puede romperse
devolviendo *nada* (lo que el fallback sí cubre), sino devolviendo **datos silenciosamente corruptos**.
El mojibake pasó los controles de `call_with_fallback` —había resultado, no vacío, sin excepción— y se
persistió en la BD del usuario. `__is_empty_result` mide *presencia*, no *corrección*, así que un
cambio de encoding, de idioma o de estructura del payload que devuelva texto plausible no lo detecta
nadie. Con B5 resuelto, el fallo total ya avisa al usuario; el fallo **parcial** sigue sin detectarse.

### R3 — Manipulación de widgets Tk desde hilos daemon 🚧 **Reducido (2026-08-16)**

El arranque construye **toda** la vista de recientes desde un hilo secundario
(`main_window.py:495`), y el buscador hace lo mismo con cada resultado. Tkinter no es thread-safe.
✅ Hoy funciona, pero es el tipo de fallo que aparece como un cuelgue esporádico e irreproducible en
la máquina del usuario, imposible de depurar sin logs (y `console=False` en el `.exe` los borra).

🆕 **Dejó de ser teórico, y luego se acotó.** Durante la fase 8 este riesgo se materializó en un crash
**reproducible**: construir la ficha desde el hilo secundario revienta con
`invalid command name ...!searchbutton.!ctkcanvas` si la vista que se está destruyendo tenía un
`<Configure>` encolado —lo tienen las 4 vistas de estado, por su barra de búsqueda—. Los **6 puntos de
clic**, el buscador de la biblioteca y la migración devuelven ya con `after(0, …)`
([07 C2](07-concurrencia-e-hilos.md)); los `after()` correctos pasan de 1 a **7**.

⚠️ **Lo que sigue vivo** es el arranque, el buscador de la lupa y la llamada de servidores. Es código
anterior y no se ha tocado en esta fase: la regla del proyecto es no propagar el patrón heredado, no
reescribirlo de golpe.

---

## 6. El roadmap traducido a impacto técnico

Roadmap declarado en `.claude/CLAUDE.md` y `README.md:124-130`.

| Punto del roadmap | Módulos a tocar | Requisitos previos | Docs a actualizar |
|---|---|---|---|
| **Renombrar «recientes» → «nuevos lanzamientos»** | `recentAnimes.py:22`, `main_window.py:32` | ninguno — es el más barato | [06](06-gui-y-vistas.md), [02](02-mapa-de-modulos.md) |
| **Quitar «Anime» de los nombres de pestañas** | las 6 vistas + `main_window.py:134` | ninguno | [06](06-gui-y-vistas.md) |
| ~~**Selector de proveedor con preferencia persistida**~~ | ✅ **Hecho el 2026-07-30**: `userPersistence.py` (nuevo), `animeProviderMgr.py` v0.2, `main_window.py`, `anime_window.py` v0.2 y los 6 puntos de clic | — | **[13](13-selector-de-proveedor.md)** |
| ~~**Separar «usar ahora» de «fijar como predeterminado»**~~ | ✅ **Hecho el 2026-08-06** con un **pin** junto al desplegable: `main_window.py` v0.2, `anime_window.py` v0.3 (se retira el selector de la ficha), `userPersistence.py` v0.2, 4 iconos nuevos | — | **[13 §12](13-selector-de-proveedor.md)** |
| ~~**Columna `provider_id` en `ANIMES`**~~ | ✅ **Hecha el 2026-08-16**: `models.py` (`AnimeProviderId`, `ProviderInfo`), `animeProviderMgr.py` v0.3, `animesPersistence.py` v2.3, `main_window.py` v0.4, `anime_window.py` v0.6, `utilsButtons.py` v0.2, `utils.py` v0.3, los 3 proveedores y las 6 vistas | — | **[13 §14](13-selector-de-proveedor.md)**, [04 §8](04-modelo-de-datos.md) |
| **Calificación personal en favoritos + ordenar por ella** | `AnimeField`, `AnimeRecord`, `anime_window.py`, `favouriteAnimes.py` | arreglar B2 (`str` vs enum); la migración ya es automática | [04](04-modelo-de-datos.md), [06](06-gui-y-vistas.md) |
| **Paginar favoritos/viendo/pendientes/finalizados de 10 en 10** | las 4 vistas de estado; reutilizar `searchAnimes.py:273-330` | extraer la paginación a `utilsButtons.py` | [06](06-gui-y-vistas.md), [03](03-flujos-de-ejecucion.md) |
| **«Viendo» en cascada con el último capítulo visto** | `watchingAnimes.py` | ya está en BD (`last_watched_episode`) — barato | [06](06-gui-y-vistas.md) |
| **Bloque «Si te ha gustado X…» (4 animes del mismo género)** | `anime_window.py:44-45`, `get_anime_by_genre_and_order` | arreglar B2 primero | [03](03-flujos-de-ejecucion.md), [06](06-gui-y-vistas.md) |
| **Convivencia anime + manga** | 🔴 **transversal**: `models.py` (¿`MediaInfo`?, y `ProviderInfo` gana el tipo de medio), `AnimeProvider` (¿`MediaProvider`?), `AnimeField`, las 6 vistas, `anime_window.py:47` | decidir si se generalizan los modelos o se duplican | **todos** |
| **Nuevos lanzamientos a dos columnas, 3 por fila, pósters grandes** | `recentAnimes.py:39,55-80`, tamaños de `utils.py:59,105,156` | el redimensionado a `(130,185)` está **hardcodeado en 4 sitios** | [06 §4](06-gui-y-vistas.md), [10](10-invariantes-y-trampas.md) |
| **Filtro radio Animes/Mangas/Ambos en las 4 vistas** | `utilsButtons.AccordionFilterButton` | modelo de manga | [06](06-gui-y-vistas.md) |
| **Desplegable global anime/manga/ambos (esquina inferior izquierda)** | `main_window.py:166-238` | modelo de manga (la preferencia persistida ya es viable) | [06](06-gui-y-vistas.md), [01](01-arquitectura.md) |
| ~~**Integrar JKAnime**~~ | ✅ **Hecho el 2026-08-06**: `APIs/jkanime/jkanime.py` (nuevo, v0.1), `main_window.py`, `MiBibliotecaAnime.spec` | — | **[05 §3b](05-proveedores-y-scraping.md)**, [02](02-mapa-de-modulos.md), trampas 23-25 |
| **Integrar MonosChinos2, TioAnime** | `APIs/<sitio>/` nuevos + registro en `main_window.py` | ninguno — sigue mitigando R2 | [05](05-proveedores-y-scraping.md), [11 §3](11-playbooks.md) |
| **Proveedores de manga** | contrato nuevo o generalización de `AnimeProvider` | decisión de diseño de la convivencia | [01](01-arquitectura.md), [05](05-proveedores-y-scraping.md) |
| **Capítulo de manga por el que continuar tras el anime** | requiere mapeo anime↔manga | modelo de manga + fuente de datos del mapeo | [04](04-modelo-de-datos.md) |

### Orden sugerido

*(Revisado el 2026-07-30. ~~A1~~, ~~A2~~, ~~A4~~, ~~A5~~, ~~B1~~ y ~~B5~~ ya pagadas: ver
[§4 → Resuelto](#-resuelto).)*

**El orden lo fijó el usuario el 2026-07-30. Sus tres primeros puntos ya están cerrados —el selector
y la integración de un proveedor nuevo el 2026-08-06, y la columna `provider_id` el 2026-08-16—, así
que la lista avanza.**

1. ~~🔴 **Integrar un proveedor nuevo**~~ — ✅ **hecho el 2026-08-06 con JKAnime**. Validó que la
   abstracción aguanta: fue el primer proveedor que necesitó traducir géneros y el primero que mezcla
   dos técnicas de parseo, y el contrato no hubo que tocarlo.
2. ~~🔴 **La columna `provider_id` en `ANIMES`**~~ — ✅ **hecha el 2026-08-16**
   ([13 §14](13-selector-de-proveedor.md)). Trajo consigo tres cosas que no estaban en el plan y
   resultaron inseparables: que el proveedor deje de ser una cadena (`AnimeProviderId`), **migrar una
   fila a otro proveedor** y el **aviso de duplicado** — porque elegir proveedor sin ellas convierte
   la biblioteca en un sitio donde el mismo anime puede acabar dos veces. Cerró **B4** (casi), **B10**
   y **R2**, y redujo **R3**.
3. **Arreglar B2** — barato, y desbloquea dos puntos del roadmap (recomendaciones por género, ordenar
   favoritos por calificación). **Es lo siguiente que queda barato.**
4. **Sacar la llamada de servidores del hilo de Tkinter** — lo único que queda de B4, y ahora el
   patrón está establecido en 7 sitios: es copiar y pegar.
5. **Entonces** abordar la convivencia anime/manga, que es la refactorización grande. `ProviderInfo`
   ya tiene dónde llevar el tipo de medio, y `USER_SETTINGS` dónde guardar la preferencia.

> ~~**Selector de proveedor con preferencia persistida** (TODO #4)~~ — ✅ **hecho el 2026-07-30**
> ([13](13-selector-de-proveedor.md)) y **cerrado del todo el 2026-08-06** con el pin. Estrenó la
> infraestructura de esquema declarativo con **una BD nueva** (`DB_user.db`) y dejó el sitio donde
> guardar la futura preferencia anime/manga.

**A3** queda fuera de ese orden porque su urgencia depende de si vas a distribuir el `.exe`: mientras
no empaquetes, no molesta; en cuanto empaquetes, es lo primero (ver la nota de reevaluación en §4).

Con R1 resuelto, cualquier punto del roadmap que necesite columnas o tablas nuevas (preferencia de
proveedor, calificación personal) es ya abordable sin riesgo para los datos existentes.

⚠️ Este orden es una **recomendación**, no una decisión tomada. Las prioridades son del usuario.
