# 12 — Deuda técnica y roadmap

| | |
|---|---|
| **Fecha** | 2026-10-28 · rama `release/0.5.0` · último commit de código **`7bbbb3c`**. Revisados §1, §2, §4 (B13, B18, C13) y §6; ⚠️ las anclas `:línea` de §4 anteriores al 2026-10-20 **no se han reverificado** |
| **Cubre** | `src/**`, `.claude/CLAUDE.md`, `README.md`, `requirements.txt`, `MiBibliotecaAnime.spec`, `LICENSE`, `LEEME.txt`, `THIRD-PARTY-NOTICES.txt` |
| **Última revisión** | 2026-10-29 (**estabilizar la 0.5.0**, en `release/0.5.0`): **B18 y C13 cerradas** —ningún widget sin `font=` (24 → 0 fuentes huérfanas) y «Buscar» usa `library_status()`—. Antes, 2026-10-28 (**versión 0.5.0**): **B13 cerrada con medida** (las vistas se conservan: 37-136 ms al volver, eran 226-466; el objetivo de 50 ms solo lo cumple «Buscar»); **B18 nuevo** —17 widgets sin `font=` que pueden congelar la aplicación ([trampa 77](10-invariantes-y-trampas.md))—; **C13 nuevo** (dos funciones con la misma regla de sello); §2 reinventariado (**3** TODOs: cerrado «Si te ha gustado X…»); §6 con temporadas y «Te puede interesar» hechos y **P5 aparcado con su regla**; §1 con los commits de la 0.5.0. Antes, 2026-10-27 (**conexiones y `<Configure>`**): **B16 y B17 cerradas** —una `requests.Session` por hilo para AnimeAV1 y los pósters, y el `<Configure>` de la raíz filtrado en Tcl, incluido el de CustomTkinter—; ver §4 → Resuelto. Antes, 2026-10-27 (**refresco de episodios**): **B12 cerrada** con `EpisodeRefresher`; «Finalizados» queda fuera a propósito. Antes, 2026-10-21 (**auditoría de rendimiento**): **B13 rediagnosticada** —el coste de cambiar de vista es crear widgets de CustomTkinter, no leer JPG— y **B16-B17** nuevas, las dos opcionales; las fugas que destapó la auditoría están resueltas y son las trampas 55-57 de [10](10-invariantes-y-trampas.md). Antes, 2026-10-21: **B2 y B15 cerrados** (§4 y orden sugerido); **L10 y L11 cerrados**, L4c corregido y **L12-L13** nuevos (§7), con la herramienta `tools/actualizar_libmpv.py`; el usuario **ha oído** los episodios, así que el reproductor queda verificado entero. Antes, 2026-10-20 (**reproductor in-app**): **B4 cerrado del todo** —era la **deuda nº 1** del roadmap: la petición de servidores salió del hilo de Tk el 2026-09-24—; **B14 nuevo**, los hosters que siguen abriendo el navegador; **B15 nuevo**, «Cargando» sin tope con un hoster lento; **C12 nuevo**, la DLL de libmpv fuera del repo; §2 reinventariado (**4** TODOs, en líneas nuevas); §6 con el reproductor hecho y la siguiente tarea; **§7** con lo que hizo la fase 5 sobre la GPL —**seis componentes más** en `THIRD-PARTY-NOTICES.txt`, la §6 de la GPL para la DLL **con una oferta de fuente**— y **L10** nuevo. Antes, 2026-09-02 (**rejillas adaptables**): **B13 nuevo** —cada repintado de la rejilla vuelve a leer y reescalar los JPG desde disco, ~350 ms para 16 celdas en el hilo de la interfaz—, hoy mitigado con una espera de coalescencia y no con una caché. Antes, 2026-09-01 (**refresco de la banda «Retomar»**): **B12 nuevo** —solo se refrescan las ≤3 filas de la portada; el resto de la biblioteca sigue enseñando el recuento del día que abriste su ficha—, y **B3 y B8 cerrados**: los tres hilos del buscador y los siete `time.sleep(0.1)` que describían **ya no existen en `src/`** desde el rediseño. Antes, 2026-08-18: §1 rehecho —la tanda de licencia ya está publicada— y **C10 cerrado del todo**: el árbol de directorios del `README.md` tenía dos erratas de copiar-pegar y omitía los ficheros legales. Antes, 2026-08-17 (**licencia y distribución**): **A3 y C11 cerrados** —`datas` ya no lleva datos de usuario y el `.spec` está por fin **verificado compilando**—, C10 cerrado a medias, **B11 abierto** (origen de los recursos gráficos) y §7 nueva |

Procedencia: ✅ verificado en ejecución · 📖 leído en código · ⚠️ sin verificar.

---

## 1. Estado del árbol de trabajo

🆕 **2026-10-28 — rama `release/0.5.0`**, desde `develop` en `7bbbb3c`. La 0.5.0 entró en `develop`
con un commit por fase, cada uno en su `feature/*` fusionada con `--no-ff` y borrada:

| Commit | Merge en `develop` | Qué entró |
|---|---|---|
| `3c77fc9` | `dbecb2a` | Fase 1 — relaciones y formato en `models.py`, AnimeAV1 y JKAnime; `PROVIDER_SHORT_NAME` |
| `fbf357a` | `79a2420` | Fase 2 — `FranchiseService` y `get_anime_relations` |
| `c33448a` | `83bff36` | Fase 3 — ficha con pestañas, temporadas, relacionados, «Volver», tarjeta de fin |
| `3e269e3` | `7eaf968` | Fase 4 — «Te puede interesar» y `genre_filters` |
| `ca9200f` | `7bbbb3c` | Fase 5 — vistas conservadas (B13) |

Sin trackear siguen `.vscode/` y los 4 PNG sin usar. ⚠️ La rama `release/0.4.2` sigue existiendo,
aunque ya está fusionada en `main`.

🆕 **2026-10-20 — rama `feature/reproductor-embebido`**, sin fusionar con `develop` ni con `main`.
La creó el usuario con el plan del reproductor dentro y un merge de `develop` (`5b9dd06`), y lleva un
commit por fase:

| Commit | Qué entró |
|---|---|
| `cbd2721` | (antes del plan, vía `develop`) **comentarios de 30 módulos reescritos**, −400 líneas netas: desplazó las anclas `:línea` de casi toda esta documentación |
| `4152880` | Fase 0 — *spike* de libmpv: `.gitignore` (+`vendor/`) y el estado del plan. `src/` sin tocar |
| `5f81873` | Fase 1 — capa `APIs/resolvers/`, y los «B1» y «B2» **del plan** (servidores repetidos y Okru relativo), que no son los B1 y B2 de §4 |
| `4167f3b` | Fase 2 — servidores fuera del hilo de Tk (cierra **B4** y la deuda nº 1) |
| `1d8b3a8` | Fase 3 — `VideoPlayer`, `player_frame` y la pantalla completa |
| `5a90828` | Fase 4 — anterior/siguiente, tarjeta de fin y marcado como visto |
| `f3fc229` | Fase 5 — `.spec`, `requirements.txt`, `README.md`, `LEEME.txt` y `THIRD-PARTY-NOTICES.txt` |

Sin trackear siguen los mismos: los 4 PNG sin usar, `.vscode/`, `.claude/settings.local.json` y
`.claude/plans/`. ⚠️ **`vendor/libmpv-2.dll` no aparece porque `vendor/` está en `.gitignore`** (C12).

📜 **Estado a 2026-08-18** (lo que decía esta sección hasta el reproductor):

✅ **Árbol limpio y publicado.** `git status` sobre **`e337d20`** (rama `main`, tag **`v0.2.1`**),
2026-08-18: sin ficheros modificados ni en el índice, y **`main == origin/main`** — 0 adelante,
0 detrás. **Todo el trabajo vive en `main`**; `develop` va 3 commits por detrás y no queda ninguna
rama local sin fusionar.

Las dos tandas que las revisiones anteriores daban por pendientes ya están dentro:

| Commit | Fecha | Qué entró |
|---|---|---|
| `a3d4331` | 2026-08-16 | **La columna `provider_id`** — los 16 ficheros de `src/` de la fase 8, más el `README.md` y `APP_VERSION` a 0.2.0 |
| `bec0fbc` | 2026-08-17 | **`LICENSE`** — texto GPL-3.0 íntegro, 674 líneas |
| `e337d20` | 2026-08-18 | **La tanda de licencia y empaquetado**, 11 ficheros y +2 631/−88 — `README.md` (sección «Licencia» y reclamos falsos corregidos), `MiBibliotecaAnime.spec` (`datas` sin datos de usuario + copia de los legales tras `COLLECT`), `LEEME.txt`, `THIRD-PARTY-NOTICES.txt` y los 7 documentos de `.claude/` |

⚠️ **Los tags `v0.1.0` y `v0.2.0` apuntan a commits distintos en local y en GitHub**: el local va una
commit por delante en los dos casos (`v0.2.0` → `bec0fbc` en local, `a3d4331` en el remoto). `git
fetch` **no reescribe tags que ya existen**, así que la divergencia no da ningún aviso. `v0.2.1`
coincide en ambos lados. Pendiente de decidir cuál manda — **lo lleva el usuario**.

📜 **Historial.** `git status` sobre **`18311e3`** (rama `develop`), 2026-08-07: el árbol estaba
limpio entonces, y las dos tareas que la revisión de aquel día daba por pendientes ya estaban dentro:

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
| `.vscode/` | configuración local del editor (`launch.json`, `tasks.json`, `settings.json`) |
| `.claude/settings.local.json` | permisos locales de Claude Code |
| `.claude/plans/` | planes del modo plan de Claude Code |

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

✅ Inventario **rehecho con `git grep -n "TODO" -- src/` el 2026-10-28** sobre `7bbbb3c`, mirando la
salida. Son **3**: la 0.5.0 **cerró** el de «Si te ha gustado X…» con la pestaña «Te puede
interesar» ([03 §17](03-flujos-de-ejecucion.md)), y los otros tres se desplazaron.

| # | Ubicación | Contenido | Documento afectado |
|---|---|---|---|
| ~~1~~ | ~~`gui/anime_window.py:152`~~ | ✅ **Cerrado el 2026-10-28** (0.5.0, fase 4): «Si te ha gustado X, te puede interesar…» es la pestaña **«Te puede interesar»** de la ficha, con 4 animes de los mismos géneros | [06 §8](06-gui-y-vistas.md), [03 §17](03-flujos-de-ejecucion.md) |
| 2 | `gui/anime_window.py:222` | Botón para alternar entre manga y anime | [06](06-gui-y-vistas.md), [01](01-arquitectura.md) |
| 3 | `APIs/jkanime/jkanime.py:181` | Si el texto de búsqueda está vacío, buscar en `DIRECTORY_URL` en vez de en `SEARCH_URL` | [05 §3b](05-proveedores-y-scraping.md) |
| 4 | `APIs/jkanime/jkanime.py:242` | Corregir `get_recent_animes` para no quedarse con todo lo que aparece en la portada | [05 §3b](05-proveedores-y-scraping.md) |
| ~~—~~ | ~~`gui/main_window.py:32`~~ | ✅ **Cerrado el 2026-08-20** (rediseño, fase 1): las pestañas pierden la palabra «Anime» y «Animes recientes» pasa a «Nuevos lanzamientos». Las etiquetas viven ahora en cada vista; el título de la barra dice «Mi Biblioteca» | [06 §3](06-gui-y-vistas.md) |
| ~~—~~ | ~~`gui/main_window.py:31-34`~~ | ✅ **Cerrado el 2026-07-30**: selector de proveedor en la sidebar **y** en la ficha, con la preferencia persistida en la BD nueva `DB_user.db`. Ver **[13](13-selector-de-proveedor.md)** | **[13](13-selector-de-proveedor.md)**, [04 §0](04-modelo-de-datos.md), [05 §5b](05-proveedores-y-scraping.md) |

⚠️ **Cuidado con los falsos positivos del grep.** El 2026-08-21 la cuenta salía a 5 porque un
comentario de `gui/components/sidebar.py` decía «cierra el TODO de main_window.py» hablando de uno ya
cerrado. Está reescrito para no contener la palabra. Un comentario **sobre** una tarea cerrada no es
una tarea pendiente, pero el grep no distingue.

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
| D7 | «Muestra … la lista de episodios (**los 25 primeros**, `[:25]`)» | ✅ Correcto. El comentario del propio código dice «24» (`anime_window.py:1004`) | `anime_window.py:965` |
| **D8** | «Hay **3** `# TODO:` en el código, todos en dos ficheros» | ❌ **Falso otra vez, por el motivo contrario (2026-08-16)**. Son **5**: faltaban los dos de `jkanime.py`, que entraron el 2026-08-06. El diagnóstico de 2026-08-07 (que `recentAnimes.py` y `utilsButtons.py` no tenían ninguno) seguía siendo correcto | `git grep -n TODO -- src/`, §2 |
| ~~D9~~ | «`.spec` … no incluye `APIs.animeav1.animeav1`, `APIs.common.animeProviderMgr` ni `APIs.common.models`, y declara `gui.anime_windows`» | ✅ **Cerrado del todo (2026-08-07)**: corregido en el `.spec` y reescrito en `CLAUDE.md`; `gui.sidebarButtons.sidebarButton` retirado en `ae126fd`. ✅ Los 18 `hiddenimports` resuelven a módulos reales | `MiBibliotecaAnime.spec:21-40` |
| D10 | No menciona `attrs` | ✅ **Ya no aplica (2026-07-28)**: era una dependencia no declarada; el import se cambió a `dataclasses` de la stdlib y `attrs` deja de ser dependencia | [10, trampa 18b](10-invariantes-y-trampas.md) |
| D11 | No menciona el estado de AnimeFLV | ✅ `get_anime_episode_servers` devuelve `[]`; el usuario confirma que el sitio está caído / en desuso | [05 §2](05-proveedores-y-scraping.md) |

---

## 4. Deuda técnica, por gravedad

### 🔴 Alta

| # | Problema | Dónde | Impacto |
|---|---|---|---|
| ~~A3~~ | ~~**`.spec` desactualizado**~~ → ~~queda **solo** el empaquetado de `resources/DB`~~ | `MiBibliotecaAnime.spec` | ✅ **Cerrado del todo el 2026-08-17** (ver abajo) |
| A6 | **Widgets Tk desde hilos daemon** | `main_window.py:481-500`, `searchAnimes.py:227-232`, `utils.py:146-147` | Riesgo de cuelgue; funciona por suerte estructural. 🆕 **Reducido**: los 6 puntos de clic y el buscador de la biblioteca ya no lo hacen, y **C2 se cerró** — era un crash reproducible, no teórico ([07 C2](07-concurrencia-e-hilos.md)) |

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
> ✅ **Cerrado del todo el 2026-08-17.** Dos cosas a la vez:
>
> 1. **`datas` ya no lleva datos de usuario.** Se retiraron las 7 entradas de `resources/DB` y de las
>    6 carpetas de pósters; queda **solo** `resources/images/utils`. Medido sobre el build de v0.2.0
>    antes de quitarlas: viajaban `DB_Animes.db` (77 KB), `DB_user.db`, la carpeta `backups/` **y 85
>    pósters**. Resultó que **no hacían falta**: la app crea esos directorios en tiempo de ejecución
>    (`sqlite.py:233-235`, `utils.py:55-56/91-92/127-128`) y `get_anime_image` salta los ausentes
>    (`utils.py:190-191`). Lo que las hacía parecer obligatorias es que **PyInstaller ignora en
>    silencio las carpetas vacías** ([10 § trampa 18d](10-invariantes-y-trampas.md)).
> 2. **Verificado compilando**, que era la otra mitad pendiente: `pyinstaller MiBibliotecaAnime.spec`
>    termina sin errores, el `.exe` arranca y **crea `resources/DB/DB_Animes.db` a los 3 segundos**.
>    `find dist/… -name "*.db" -o -name "*.jpg"` → **0 ficheros**.
>
> Se añadió además un bloque tras `COLLECT` que copia `LICENSE`, `LEEME.txt` y
> `THIRD-PARTY-NOTICES.txt` **junto al `.exe`** — no en `datas`, porque sus destinos caen dentro de
> `_internal/` ([10 § trampa 18e](10-invariantes-y-trampas.md)). Motivo en §7.

### 🟡 Media

| # | Problema | Dónde |
|---|---|---|
| ~~B2~~ | ~~La ordenación por géneros nunca se aplica (`str` vs enum)~~ ✅ **Cerrado el 2026-10-21**: ver [§4 → Resuelto](#-resuelto) | ~~`utilsButtons.py:341`~~ → `animesPersistence.py` (`get_anime_by_genre_and_order`) |
| ~~B3~~ | ~~Guard antidoble-búsqueda inoperante (`.start()` → `None`)~~ ✅ **Desaparecido con el rediseño (2026-08-21)**: el buscador se quedó con **dos** hilos y un **contador de generación** en vez del guard; verificado el 2026-09-01 | ~~`searchAnimes.py:213,212,335`~~ → `searchAnimes.py:107, 329-330, 361` |
| ~~B4~~ | ~~HTTP en el hilo de UI: servidores y clic desde 5 de las 6 vistas~~ ✅ **Cerrado del todo (2026-09-24, fase 2 del reproductor)**. Los 6 puntos de clic salieron el 2026-08-16; la llamada de servidores —la **deuda nº 1** del roadmap— el 2026-09-24, con número de despliegue para descartar respuestas viejas. ✅ Hueco máximo del bucle durante la petición: **0,03 s** | `anime_window.py:1739-1879` ([07 C5](07-concurrencia-e-hilos.md), [03 §8](03-flujos-de-ejecucion.md)) |
| ~~B6~~ | ~~Las 4 listas cacheadas de `MainWindow` **no las usa nadie**~~ ✅ **Ya no es cierto (comprobado el 2026-10-27), así que no se retira nada.** Desde el rediseño alimentan los contadores de la barra lateral y la cola inicial de `EpisodeRefresher`, y la ficha y «Pendientes» las releen al cambiar un estado ([trampa 31](10-invariantes-y-trampas.md)). Las vistas siguen leyendo de la BD, pero las listas no son código muerto | `main_window.py` (`counter_providers` de `load_sidebar_buttons()`, `__on_startup_loaded`), `anime_window.py`, `pendingAnimes.py` |
| ~~B7~~ | ~~`remove_from_finished` mueve a *pendiente* en BD pero **borra el póster sin recrearlo** en `pending/`~~ ✅ **Cerrado el 2026-10-27**: ver [§4 → Resuelto](#-resuelto) | `utils.py` (`sync_status_posters`), `anime_window.py` (`sync_saved_posters_async`) |
| ~~B8~~ | ~~`time.sleep(0.1)` en el hilo de UI × 7~~ ✅ **Cerrado con el rediseño (2026-08-21)**: `git grep -n "time.sleep" -- src/` solo devuelve las dos esperas entre reintentos de scraping, que van en hilo daemon. Verificado el 2026-09-01 | [07 §5](07-concurrencia-e-hilos.md) |
| ~~B10~~ | ~~El buscador de las vistas de estado va **contra la red**, no contra la BD~~ ✅ **Cerrado (2026-08-16)**: búsqueda **local** primero, la web solo suma. Era peor de lo diagnosticado —no era solo «no funciona sin conexión», sino que **perdía animes** según el proveedor puesto ([trampa 26](10-invariantes-y-trampas.md)) | `utilsButtons.py:23-166` |
| B11 | **Los iconos de la sidebar y los GIF de carga son de origen desconocido**, y muy probablemente incompatibles con la GPL-3.0 del proyecto. ⚠️ **No crece**: el rediseño no añadió ni un PNG — sus diez glifos se dibujan con PIL | `resources/images/utils/` |
| ~~B12~~ | ~~Solo se refrescan los episodios de las ≤3 filas de la banda «Retomar»~~ ✅ **Cerrado el 2026-10-27**: ver [§4 → Resuelto](#-resuelto) | `gui/episode_refresher.py` |
| ~~**B13**~~ | ~~**Cambiar de vista bloquea la interfaz 270-620 ms.**~~ ✅ **Cerrada con medida el 2026-10-28** (0.5.0): ver [§4 → Resuelto](#-resuelto) | `main_window.py` (`show_view`), las seis vistas |
| ~~**B18**~~ | ~~**17 widgets de CustomTkinter sin `font=` pueden congelar la aplicación.**~~ ✅ **Cerrada el 2026-10-29** (en `release/0.5.0`): ver [§4 → Resuelto](#-resuelto) | los once ficheros de la trampa 77 |

> **B12 — hasta dónde llevar el refresco** (abierto el 2026-09-01, cerrado el 2026-10-27). Se
> descartaron dos salidas: refrescar solo la fila del `SidePanel` (que ya se salvaba casi siempre por
> estar en la banda) y refrescar toda la biblioteca en cada arranque (~36 peticiones, «Finalizados»
> incluido). Se eligió «Viendo» + «Pendientes» con **un servicio común** en vez de copiar el patrón de
> la banda dos veces más. La antigua advertencia de «no refrescar al arrancar» se refería a
> **retrasar** el arranque: el refresco de ahora empieza con la portada ya pintada
> ([03 §11](03-flujos-de-ejecucion.md)).

> **B11 — origen de los recursos gráficos** (abierto el 2026-08-17). El proyecto pasó a GPL-3.0 ese
> día (`bec0fbc` + sección «Licencia» del `README.md`), y eso convierte la procedencia de los recursos
> en un problema real: **el autor no recuerda de dónde salieron**.
>
> 📖 **Evidencia recogida de los metadatos PNG** (`PIL.Image.open(...).info`):
>
> | Fichero | Tamaño | `Software` | DPI |
> |---|---|---|---|
> | `buscar.png`, `favoritos.png`, `no_favoritos.png`, `finalizados.png`, `recientes.png`, `viendo.png`, `pendientes.png` (+ variantes `_light`/`_dark`) | 512×512 | `www.inkscape.org` | 95.99 / 96.01 / 89.99 / 94.26 / **768** — **distintos entre sí** |
> | `fijado_*.png`, `no_fijado_*.png` | 64×64 | *(ninguno)* | — |
> | `loading-image.gif` | 400×400 | *(ninguno)* | — |
> | `loading-image-3.gif` | **320×319** | *(ninguno)* | — |
>
> ⚠️ **Inferencia, no prueba.** El patrón 512×512 + exportado con Inkscape + DPI inconsistentes entre
> ficheros es la firma del *pipeline* de descarga de **Flaticon**: SVGs de origen distinto bajados en
> momentos distintos, no un set dibujado de una vez. El contraste lo refuerza: `fijado_*` y
> `no_fijado_*`, que **sí** se generaron con PIL en este proyecto (2026-08-06), no llevan tag
> `Software` — la ausencia de metadatos es la huella de «generado aquí».
>
> **Por qué no basta con un `ATTRIBUTIONS.md`.** La licencia gratuita de Flaticon no solo exige
> crédito: **no permite sublicenciar**. La GPL-3.0 obliga a que todo lo distribuido sea
> redistribuible bajo sus términos, y un icono de Flaticon empaquetado en el `.exe` no lo es. Un
> fichero de atribuciones documentaría el conflicto, no lo resolvería.
>
> **Soluciones posibles, en orden de probabilidad:**
>
> 1. 🎯 **Redibujarlos con PIL** — *la vía elegida como más probable*, y **cada vez menos hipótesis**:
>    el rediseño de interfaz (2026-08-20/21) dibujó así **diez glifos más** sin añadir un solo PNG —el
>    pin (2026-08-06), las estrellas de la calificación, los cuatro glifos de estado y los dos iconos
>    de estado vacío—, todos supermuestreados a 8x y reducidos con LANCZOS. La receta está probada, en
>    `gui/components/status_pill.py` y `gui/components/empty_state.py`, y recogida en
>    [11 §5](11-playbooks.md). Procedencia limpia por construcción, cero dependencias nuevas y control
>    total del par claro/oscuro. **Lo que queda son los ~7 glifos de la barra lateral y los 2 GIF**,
>    que es lo único gráfico del proyecto que sigue siendo de origen desconocido.
> 2. **Sustituirlos por un set con licencia compatible** — Lucide (ISC), Bootstrap Icons (MIT) o
>    Material Symbols (Apache-2.0). Las tres son compatibles con GPL-3.0 y no exigen crédito visible.
>    Más rápido que dibujar, a cambio de aceptar el estilo del set.
> 3. **Búsqueda inversa en Flaticon** para recuperar autor y atribuir en regla. Recupera los iconos
>    actuales, pero es tedioso para 8 ficheros y **no resuelve la incompatibilidad** de sublicencia:
>    solo sirve si el proyecto dejara de ser GPL.
>
> 🔴 **Los dos GIF son el caso peor y no tienen metadatos que ayuden**: sin tags, en modo paleta, y
> uno con recorte `320×319` — la marca de algo recortado a mano y descargado de Giphy/Tenor. Si son
> fotogramas de un anime, son obra con copyright, están commiteados y viajan dentro del `.exe`. La
> pantalla de carga ya tiene barra de progreso (`show_loading_screen()`), así que **quitar el GIF o
> sustituirlo por un spinner propio** es la opción barata.

> **B7, alcance medido el 2026-07-30** ✅ *(cerrada el 2026-10-27; se conserva el diagnóstico)*. Es un caso particular de algo más general: la BD fuerza la
> exclusividad viendo/finalizado/pendiente (`_set_status`), pero la GUI solo gestiona el póster **del
> estado que pulsas**. Consecuencias, contadas sobre la biblioteca real (25 animes):
>
> - **6 pósters huérfanos** en `resources/images/watching/` — animes que salieron de «viendo» y dejaron
>   su fichero atrás. Solo gastan disco; las vistas filtran por BD.
> - La variante **visible** es únicamente `remove_from_finished`: mueve el anime a *pendiente* en BD y
>   borra el póster de `finished/` sin crearlo en `pending/`, así que la vista de pendientes muestra el
>   recuadro gris de `load_image`. ⚠️ Hoy no se da en los datos del usuario: 0 animes marcados sin
>   póster en su carpeta.

| **B14** 🆕 | **Hosters que siguen abriendo el navegador.** El reproductor solo resuelve zilla («HLS»), MP4Upload, y Desu, Magi y Desuka de JKAnime. **Aplazados**: Voe, Byse, YourUpload, StreamTape, VidHide, UPNShare, DoodStream y Netu; **bloqueado de verdad**: Mega (cifrado de extremo a extremo); y Okru, que solo llega en JKAnime. Funcionan —abren el navegador, como antes del plan—, pero llevan ↗. Cobertura medida el 2026-09-24: los resueltos cubren **7/7** episodios muestreados en cada proveedor | `APIs/resolvers/registry.py` · receta en [11 §9](11-playbooks.md), tabla en [05 §9](05-proveedores-y-scraping.md) |

| ~~**B15**~~ | ✅ **Cerrada el 2026-10-21**: `LOAD_TIMEOUT_S = 30` en `video_player.py`, contado desde `play()` hasta el primer `playback-restart`; al vencer para mpv y llama a `on_error`. Verificado con el `VideoPlayer` real y un servidor local lento (error a los 30,0 s, mpv parado; sin falsos positivos con un medio que arranca en 0,2 s; el plazo se reinicia con cada `play()`). Lo que había: ~~**«Cargando» no tiene tope propio.**~~ El único plazo es el `network-timeout` de mpv (15 s **por petición**), así que un hoster que responde despacio deja la tarjeta de «Cargando» un minuto o más sin caer al navegador. ✅ Visto el 2026-10-20 con zilla: ~70 s hasta abrir el medio ([trampa 54](10-invariantes-y-trampas.md)). Arreglo: un plazo desde `play()` hasta el primer `playback-restart` que, al vencer, haga lo mismo que `on_error` | `video_player.py` (`play`, `__handle_event`), `anime_window.py` (`__on_player_error`) |
| ~~**B16**~~ | ~~**Las peticiones no reutilizan conexión.**~~ ✅ **Cerrada el 2026-10-27**: ver [§4 → Resuelto](#-resuelto) | `utils/http_session.py`, `animeav1.py` (`_fetch`), `utils.py` (descargas) |
| ~~**B17**~~ | ~~**El `<Configure>` atado a la raíz se dispara con el de cualquier widget.**~~ ✅ **Cerrada el 2026-10-27**: ver [§4 → Resuelto](#-resuelto) | `main_window.py` (`__bind_window_configure`) |

> **B14 — por qué no es urgente.** Con zilla **o** MP4Upload en AnimeAV1, y Desu **o** Magi en
> JKAnime, todo episodio muestreado se veía dentro. Lo que más valdría es un **segundo hoster por
> proveedor que no dependa del mismo origen**: zilla estuvo caído **tres días** en septiembre, y
> MP4Upload servía ese día a 110-260 KB/s, por debajo del bitrate de su propio AV1 1080p.

### 🟢 Baja

| # | Problema | Dónde |
|---|---|---|
| ~~C1~~ | ~~Errata en `__module__`: `animesPersistence` sin `.py`~~ ✅ **Cerrado el 2026-10-27** (v2.5). Las otras dos (`anime_wnidow.py`, `animeProvider.py`) ya estaban corregidas | `animesPersistence.py` |
| ~~C2~~ | ~~`update_gif` suelto, muerto y roto~~ ✅ **Retirado el 2026-10-27**, con el `import tkinter` que solo usaba él. No tenía llamantes; la `update_gif` local de la pantalla de carga es otra y sigue | `utils.py` (v0.4) |
| ~~C3~~ | ~~`removeprefix` devuelve `None` si los tipos difieren~~ ✅ **Retirado el 2026-10-27**: era un *backport* para Python <3.9 y el proyecto exige 3.10. Sus cuatro llamadas (una en AnimeAV1, tres en AnimeFLV) usan `str.removeprefix`, y los proveedores ya no importan nada de `utils/`. [Trampa 20](10-invariantes-y-trampas.md) | `animeav1.py` (v0.5), `animeflv.py` (v0.4) |
| ~~C4~~ | ~~`SearchButton` duplicado (widget vs vista)~~ ✅ **Desaparecido con el rediseño**: `utilsButtons.py` ya no lo define y solo queda la vista. Comprobado el 2026-10-27 | `searchAnimes.py` |
| ~~C5~~ | ~~Nomenclatura mixta `show_*` / `__show_*` en las vistas~~ ✅ **Cerrado el 2026-10-27**: `show_favourite_animes`, `show_watching_animes`, `show_pending_animes` y `show_finished_animes` eran públicos, y el de la portada, `__show_animes_recientes`, estaba en español. Los cinco pasan a privados en inglés (`__show_recent_animes` el último): solo los usaban su constructor y su `show_frame()`, que sigue siendo la única entrada pública | las 5 vistas que no son «Buscar» |
| ~~C6~~ | ~~`AccordionFilterButton` crea un frame nuevo en cada expansión~~ ✅ **Desaparecido con el rediseño (2026-08-21)**: la clase ya no existe en `src/`. Comprobado el 2026-10-27 | — |
| ~~C7~~ | ~~`info_frame` con `fg_color="white"` fijo, no respeta el tema~~ ✅ **Desaparecido con el rediseño**: no queda ningún `"white"` en `src/`, y la ficha pinta con tokens de `Theme`. Comprobado el 2026-10-27 | — |
| ~~C8~~ | ~~`-> (bool, list)` como anotación de tipo~~ ✅ **Cerrado el 2026-10-27**: eran dos, no una. `query_sql` y `insert_record_db` anotan `Tuple[bool, list]` y `Tuple[bool, int]` | `sqlite.py` (v1.2) |
| ~~C9~~ | ~~Comentario «24 primeros» donde el código dice 25~~ ✅ **Desaparecido**: el comentario ya no existe y el corte es la constante `EPISODES_SHOWN = 25`. Comprobado el 2026-10-27 | `anime_window.py` |
| ~~C10~~ | ~~`README.md` describe funciones inexistentes~~ ✅ **Cerrado del todo el 2026-08-18** (ver abajo) | §3 |
| ~~C11~~ | ~~La BD del desarrollador se empaqueta en el `.exe`~~ ✅ **Cerrado el 2026-08-17** junto con A3 | `MiBibliotecaAnime.spec` |
| **C12** 🆕 | **`libmpv-2.dll` no está en el repositorio** (120 MB, por encima del límite de GitHub; `vendor/` en `.gitignore`). Un clon limpio arranca —todo servidor abre el navegador— pero **no compila el `.exe`** sin el paso 4 del `README.md`. Si algún día pesa: Git LFS o un script de descarga que compruebe el sha256 | `.gitignore`, `MiBibliotecaAnime.spec:12-14`, [trampa 18f](10-invariantes-y-trampas.md) |
| ~~**C13**~~ | ~~**Dos funciones con la misma regla de sello.**~~ ✅ **Cerrada el 2026-10-29**: ver [§4 → Resuelto](#-resuelto) | `anime_window.py` (`library_status`), `searchAnimes.py` |

> **C10 — el árbol de directorios del `README.md`** ✅ **cerrado el 2026-08-18**. El 2026-08-17 se
> corrigieron los reclamos falsos (calificaciones, «dropeado», «100 % offline») y quedó pendiente el
> árbol. Resultó que **sí se había actualizado** en `a3d4331` —ya lista `APIs/common/`,
> `APIs/animeav1/` y `APIs/jkanime/`— pero con **dos erratas de copiar-pegar** que sobrevivieron:
>
> | Decía | Es |
> |---|---|
> | `animeav1/ └── animeav.py` | **`animeav1.py`** |
> | `finishedAnimes/ └── favouriteAnimes.py # Botón y vista: favoritos` | **`finishedAnimes.py`** · *finalizados* |
>
> Corregidas ambas, arreglado un `└──` duplicado al final del bloque y añadidos `LICENSE`,
> `LEEME.txt` y `THIRD-PARTY-NOTICES.txt`, que desde `e337d20` forman parte de la distribución.
> Contrastado contra `git ls-files src/`: **los 19 módulos reales coinciden ya uno a uno**.

### ✅ Resuelto

| # | Problema | Resuelto | Cómo |
|---|---|---|---|
| A1 | **Sin migraciones de BD** — `start()` (`animesPersistence.py:221-227`) solo creaba la tabla si el `.db` no existía. Cualquier columna nueva desalineaba silenciosamente las lecturas en instalaciones con datos previos (trampas 1 y 2). Bloqueaba el TODO #4 y medio roadmap | 2026-07-30 | Esquema declarativo `AnimesPersistence.SCHEMA` (lista de `TableSchema`) + `validate_db_integrity()`, llamado desde `start()`. Motor genérico en `utils/db/sqlite.py` (v1.1): `sqlite_affinity()`, `TableSchema`, `SqlUtils.execute_transaction/get_table_names/get_table_columns`, `ServiceDB.validate_schema/diff_table/apply_table_migration/backup_db`. Escala de `CREATE TABLE` → `ALTER TABLE ADD COLUMN` → reconstrucción transaccional copiando **por nombre de columna**. Copia de seguridad en `resources/DB/backups/` antes de la primera modificación. ✅ Verificado con 57 comprobaciones sobre copias de la BD real (24 filas): retipado, columna al final, columna en medio, desorden, tabla nueva, BD desde cero, idempotencia y rollback |
| A2 | **`attrs` no declarada** — `searchAnimes.py:15` hacía `from attr import dataclass` de un paquete ausente de `requirements.txt`, presente solo como transitiva de `selenium → trio → outcome → attrs`. Entorno limpio → `ModuleNotFoundError: No module named 'attr'` | 2026-07-28 | Sustituido por `from dataclasses import dataclass` (stdlib). Se elimina la dependencia en vez de declararla; `src/` ya no referencia `attrs` ni `selenium`. ✅ Verificado importando el módulo e instanciando `AnimeSearch` |
| A5 | **Mojibake de AnimeAV1** — el sitio responde sin `charset`, requests aplicaba el defecto de la RFC 2616 (ISO-8859-1) y el texto mal decodificado llegaba a `AnimeInfo.synopsis`, a la pantalla **y a la BD**. Afectaba también a `title` (extremo que la trampa 14 daba por no comprobado) | 2026-07-30 `94b497e` | Helper `_fetch()` (`animeav1.py:37-56`) que fija UTF-8 **solo si el servidor no declara charset**; las 5 llamadas de scraping pasan por él. v0.2 → v0.3. ✅ Verificado contra el sitio real (ficha, portada y búsqueda: 0 marcadores). **Datos ya guardados**: 3 de 25 filas reparadas re-descargando la ficha, con copia previa en `resources/DB/backups/` |
| B5 | **`AnimeWindowViewer(mw, None)` petaba** — el constructor iteraba `.episodes` sin guarda y las 6 vistas pasaban directo el retorno de `get_anime_info`, que es `None` si fallan todos los proveedores. Tkinter se tragaba el `AttributeError`: el clic no hacía nada y la app parecía colgada | 2026-07-30 `1bfdf0f` | `show_anime_info_error()` (`anime_window.py:200-216`) con log y `messagebox`; guarda en los 6 puntos de clic; contrato en el constructor (`:77-105`): `None` → `ValueError`, `episodes=None` → `dataclasses.replace` sobre **una copia**. Corregido además `recentAnimes.py`, que comprobaba el `None` pero caía de vuelta al objeto obsoleto con `.episodes` a `None`. ✅ Verificado simulando la caída total de proveedores |
| A4 | **Póster a 20×20 al descargar** — la rama de red de `get_anime_image` construía el `CTkImage` sin `size=`, y ese parámetro (no el tamaño del PIL) es lo que se pinta; su defecto es `(20, 20)`, así que el `.resize()` se hacía y se tiraba | 2026-07-30 `83a8448` | `ctk.CTkImage(Image.open(...), size=image_size)` sin `.resize()`, igual que `load_image()`. Se añadió `timeout=_REQUEST_TIMEOUT`: era la única petición del módulo sin timeout y corre en el hilo de UI. `utils.py` v0.1 → v0.2. ✅ Verificado contra un póster real: `(195, 275)` |
| B9 | **Stub muerto `WatchingAnimeButton`** — `watchingAnimes/__init__.py` definía una clase vacía con el mismo nombre que la real. `main_window.py:25` importa desde el **módulo**, así que nunca llegó a usarse, pero `from gui.sidebarButtons.watchingAnimes import WatchingAnimeButton` habría cogido el stub sin error de importación | 2026-08-07 `e6d1a73` | Fichero vaciado. ✅ Los **18** `__init__.py` de `src/` están hoy todos a 0 bytes. Ver [trampa 19](10-invariantes-y-trampas.md) |
| B2 | **La ordenación por géneros nunca se aplicaba** — `get_anime_by_genre_and_order` comparaba `order` contra el **enum**, y su único llamante (`AccordionFilterButton`) le pasaba el `str` del desplegable. El llamante **desapareció con el rediseño** (2026-08-21), así que el método quedó sin uso, pero la trampa seguía armada: la vista «Buscar» y los tres proveedores manejan el orden como `value` | 2026-10-21 | El método acepta las dos formas (`order in (POR_DEFECTO, POR_DEFECTO.value)`), que es lo que hace el resto del código; firma `AnimeOrderFilter \| str`. ✅ Verificado sobre **copia** de la BD en los cuatro estados (14, 4, 21 y 4 filas): enum y `str` dan el mismo orden, descendente por coincidencias; sha256 de la BD real intacto. Trampa 6 |
| B1 | **`get_anime_image` no buscaba en `watching/`** — provocaba una descarga redundante y, combinado con A4, el póster diminuto en la ficha de un anime que solo estuviera en «viendo» | 2026-07-30 `83a8448` | `watching` añadido a `subfolders` (`utils.py:168`), ahora las 6 categorías. ✅ Verificado con `one-piece-gyojin-touhen` (solo en `watching/` en la BD real): resuelve desde disco aun pasándole una URL inválida |
| B18 | **17 widgets de CustomTkinter sin `font=`** — cada uno creaba su propio `CTkFont` en un ciclo de referencias, y si el recolector lo liberaba en un hilo recién creado por el de Tk, la aplicación se congelaba sin error ([trampa 77](10-invariantes-y-trampas.md)). Se reprodujo con «Reintentar» de «Te puede interesar» | 2026-10-29 | `font=Theme.font(*Theme.T_UI)` —la fuente compartida de la caché— en los 17, aunque no lleven texto. ✅ Un recorrido de `src/` con `ast` no encuentra ninguno sin `font=`; tras abrir tres fichas, tres vistas y seis tarjetas del reproductor, el recolector libera **0** fuentes huérfanas (eran **24**); 2 555 widgets en 11 pantallas con la misma geometría y capturas idénticas píxel a píxel |
| C13 | **Dos funciones con la misma regla de sello** — `library_status()` de la ficha y `SearchButton.__saved_status()` de «Buscar» | 2026-10-29 | «Buscar» llama a `library_status()` y su copia desaparece. ✅ Las dos reglas daban lo mismo en las 55 filas de la biblioteca y en «no guardado» |

| B12 | **Solo se refrescaban los episodios de las ≤3 filas de la banda «Retomar»** — el resto de la biblioteca enseñaba el recuento del día que abriste su ficha, así que un anime en emisión mentía en las barras de «Viendo», en su subtítulo «M episodios pendientes» y en la duración de «Pendientes» ([trampa 38](10-invariantes-y-trampas.md)). Al cerrarla había un caso vivo en la biblioteca real: «Dragon Ball Super: Beerus», 2 guardados y 3 servidos | 2026-10-27 | `EpisodeRefresher` (`gui/episode_refresher.py`): cola por proveedor con un hilo cada uno, comprobación válida 30 min, proveedor caído tras 2 fallos seguidos, `strict=True`, relectura de la fila antes de escribir. Lo piden la portada tras pintarse y la banda, «Viendo» y «Pendientes» al entrar, con prioridad; repintan en el sitio con `update_record()`. Y la ficha que trae la reaprovecha `open_saved_anime()`. ✅ 21/21 comprobaciones del servicio aislado; ✅ GUI sobre copia con 5 filas rebajadas: las 5 se corrigen en pantalla y en la BD solo cambia `episodes`; ✅ entrar en «Viendo» cuesta igual que en `develop`; ✅ One Piece abre en 772 ms en vez de ~1 060. ⚠️ «Finalizados» queda fuera a propósito |

| B7 | **El póster no seguía a los estados que la BD cambia por su cuenta** — la ficha solo bajaba o borraba el del botón pulsado, pero `_set_status` y `update_anime_to_not_finished` mueven otros. «Quitar de Finalizados» dejaba el anime en «Pendientes» sin póster en `pending/` (cuadro gris si no había copia en otra carpeta), y pasar entre «Viendo», «Pendientes» y «Finalizados» dejaba huérfanos. De paso, **los cuatro `add_to_*` bajaban el póster con `requests.get` en el hilo de Tk** —con un servidor lento, la ventana se congelaba hasta 10 s, y si fallaba la excepción cortaba el método a medias con la BD ya escrita— | 2026-10-27 | `sync_status_posters()` (`utils.py`, v0.5) deja el póster **en las carpetas de los estados activos y solo en ésas**: completa primero —copiando de cualquier carpeta antes que descargar— y borra después, así que nunca queda sin copia. `sync_saved_posters_async()` (`anime_window.py`, v0.12) **relee la fila** en un hilo daemon y la llama bajo un cerrojo, para que con dos clics seguidos el último en correr deje el disco como la BD. La llaman `__after_status_change()` —los ocho `add_to_*` / `remove_from_*`— y «Empezar» de «Pendientes» (v0.9, que sustituye a `__cache_poster_async`). `remove_anime_poster_by_status` se retira. ✅ 17/17 comprobaciones sobre una **copia** de `resources/`: quitar de Finalizados copia a `pending/` sin red, «Empezar» mueve de `pending/` a `watching/`, un huérfano se limpia al tocar su anime, sin copia descarga a 248 × 372, dos clics seguidos acaban como la BD, una descarga caída no lanza ni deja ficheros, y el `resources/` real queda intacto (sha256 del árbol). ⚠️ **Los huérfanos que ya había no se limpian solos**: solo al tocar ese anime. Medido el mismo día: **11** huérfanos (8 en `pending/`, 2 en `watching/`, 1 en `finished/`) y 1 que falta (One Piece en `favourite/`, cubierto por su copia en `watching/`). ✅ **Probado por el usuario en la GUI**, y medido en la app real sobre una copia de `resources/`, con una ficha abierta por `open_saved_anime()`: cada clic tarda **34-45 ms** con repintado incluido, igual con la sincronización que sin ella, y el bucle de Tk no pasa de 34 ms de hueco en los 3 s siguientes |

| B16 | **Las peticiones no reutilizaban conexión** — AnimeAV1 y las cuatro descargas de pósters usaban `requests.get` suelto, así que cada petición repetía TCP + TLS. No se había hecho por no compartir una `Session` entre los hilos de precarga, ficha, búsqueda, refresco y pósters, porque requests no garantiza que sea segura entre hilos | 2026-10-27 | `thread_session()` (`utils/http_session.py`, nuevo, v0.1): una `requests.Session` **por hilo** en un `threading.local`, **sin cookies** para que cada petición se comporte como antes. La usan `_fetch` (`animeav1.py` v0.6) y `utils.py` (v0.6), con su timeout. Fuera, a propósito: la `Session` de la ficha de JKAnime (necesita las cookies del CSRF), AnimeFLV y los resolutores. ✅ En la app real sobre una copia de `resources/`, tres arranques antes y tres después: a `animeav1.com`, **28 handshakes → 3** y **181 → 146 ms** por petición; precarga de 20 fichas **3 769 → 2 951 ms**; pósters, **20 → 8** handshakes y **66 → 38 ms** cada uno. ⚠️ **Lo que no gana**: un hilo de una sola petición —abrir una ficha, pedir servidores, buscar— abre su conexión como antes. Y los ~90 ms estimados el 2026-10-21 fueron **~35** con esta red ([07 §1c](07-concurrencia-e-hilos.md)) |
| B17 | **El `<Configure>` de la raíz pasaba a Python con el de cualquier widget** — por los *bindtags*, cada cambio de vista entraba **232 veces** en `__on_window_configure` para descartarlas todas con `event.widget is self`. ✅ Al medirlo salió que **CustomTkinter hace lo mismo**: `CTk` ata `_update_dimensions_event` a la raíz sin filtro, otras 232 veces, y cada una pregunta a Tk el ancho y el alto | 2026-10-27 | `MainWindow.__bind_window_configure()` (`main_window.py` v0.8) sustituye el `<Configure>` de la raíz por un script Tcl que compara `%W` con la raíz **antes** de llamar a Python, y dentro del filtro llama a los dos: al de CTk y al propio. Sigue atado a la raíz, así que el caso de cambiar solo el alto se conserva. ✅ En la app real: llamadas a Python por cambio de vista **464 → 0**; `_substitute` en «Favoritos» **947 → 151** llamadas; bajo `cProfile` eran **8-17 ms** por vista (1,5-1,9 %). ✅ Reproductor abierto y solo el alto de 910 a 650: el vídeo pasa de **511 a 381 px** y vuelve a 511, igual que antes; maximizar, restaurar y `geometry()` dejan las dimensiones de CTk iguales a las reales. ⚠️ **No se nota a ojo**: el tiempo de un cambio de vista queda dentro del ruido; lo que lo hace lento sigue siendo B13 |
| B13 | **Cambiar de vista bloqueaba la interfaz 226-466 ms** —crear de nuevo los widgets de CustomTkinter de la vista entera en cada visita (rediagnosticada el 2026-10-21: ~70 % era `_tkinter.call`)— | 2026-10-28 | **Las vistas se conservan** (`main_window.py` v0.9, fase 5 del plan de la 0.5.0): cada una tiene **su página** en `content_frame`, que `clear_frame()` esconde con `grid_remove()`, y `show_view(vista, firma)` la reutiliza si la **firma de datos** —lo que la vista pinta, sacado de lo que ya lee al entrar— coincide; si no, la vacía y se construye como antes. Ningún camino de escritura tiene que invalidar nada ([03 §18](03-flujos-de-ejecucion.md)). De paso, la barra lateral solo repinta los ítems que cambian (23 ms por cambio de vista). ✅ Medido sobre copia, mediana de las vueltas 2-6 a 1440 × 910 (antes → después): Nuevos 299 → **87** · Favoritos 466 → **136** · Viendo 428 → **107** · Pendientes 333 → **92** · Finalizados 351 → **93** · Buscar 226 → **37** ms. ⚠️ **El objetivo de < 50 ms solo lo cumple Buscar**: lo que queda son ~12 ms de Python y el resto, Tk repintando los ~1 100 lienzos de la página ([trampa 74](10-invariantes-y-trampas.md)). El siguiente escalón sería **menos widgets por vista**, que es otra tarea. Coste: ~30 MB y ~1 100 ventanas de Tk más, **una vez**; ventanas, imágenes y comandos iguales de la vuelta 2 a la 10. La primera visita no cambia |

> Los identificadores retirados (`A2`, `A4`, `A5`, `B1`, `B2`, `B5`, `B6`, `B7`, `B9`, `B12`, `B13`, `B16`, `B17` y de `C1` a `C9`) **no se reutilizan**: otros
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

⚠️ **Lo que sigue vivo** es el arranque (hilo #3 de [07 §1](07-concurrencia-e-hilos.md)). 🆕 La llamada
de servidores salió el 2026-09-24, y el reproductor trajo un hilo **ajeno** —el de eventos de mpv— con
una regla más estricta todavía: ni `after()` ([07 §1b](07-concurrencia-e-hilos.md)). Es código
anterior y no se ha tocado: la regla del proyecto es no propagar el patrón heredado, no reescribirlo
de golpe.

---

## 6. El roadmap traducido a impacto técnico

Roadmap declarado en `.claude/CLAUDE.md` y `README.md:143-149`. *(Revisada el 2026-10-27: las filas
pendientes llevan las referencias actuales, porque el rediseño movió casi todas.)*

| Punto del roadmap | Módulos a tocar | Requisitos previos | Docs a actualizar |
|---|---|---|---|
| ~~**Renombrar «recientes» → «nuevos lanzamientos»**~~ | ✅ **Hecho el 2026-08-20**, fase 1 del rediseño | — | [06](06-gui-y-vistas.md) |
| ~~**Quitar «Anime» de los nombres de pestañas**~~ | ✅ **Hecho el 2026-08-20**, fase 1 del rediseño: ningún destino de la barra lateral lleva ya la palabra | — | [06](06-gui-y-vistas.md) |
| ~~**Selector de proveedor con preferencia persistida**~~ | ✅ **Hecho el 2026-07-30**: `userPersistence.py` (nuevo), `animeProviderMgr.py` v0.2, `main_window.py`, `anime_window.py` v0.2 y los 6 puntos de clic | — | **[13](13-selector-de-proveedor.md)** |
| ~~**Separar «usar ahora» de «fijar como predeterminado»**~~ | ✅ **Hecho el 2026-08-06** con un **pin** junto al desplegable: `main_window.py` v0.2, `anime_window.py` v0.3 (se retira el selector de la ficha), `userPersistence.py` v0.2, 4 iconos nuevos | — | **[13 §12](13-selector-de-proveedor.md)** |
| ~~**Columna `provider_id` en `ANIMES`**~~ | ✅ **Hecha el 2026-08-16**: `models.py` (`AnimeProviderId`, `ProviderInfo`), `animeProviderMgr.py` v0.3, `animesPersistence.py` v2.3, `main_window.py` v0.4, `anime_window.py` v0.6, `utilsButtons.py` v0.2, `utils.py` v0.3, los 3 proveedores y las 6 vistas | — | **[13 §14](13-selector-de-proveedor.md)**, [04 §8](04-modelo-de-datos.md) |
| ~~**Calificación personal en favoritos + ordenar por ella**~~ | ✅ **Hecho el 2026-08-20/21**, fase 5 del rediseño: columna `rating` (0-10) en `ANIMES`, `RatingStars` y orden «Mi calificación» / título persistido en `USER_SETTINGS` | — | [04 §3b](04-modelo-de-datos.md), [06](06-gui-y-vistas.md) |
| ~~**Paginar favoritos/viendo/pendientes/finalizados de 10 en 10**~~ | ✅ **Hecho con el rediseño (fases 2, 5 y 6)**, y no de 10 en 10: desde el 2026-09-02 la página es `columnas × ROWS_PER_PAGE` (2 filas llenas), con `PosterGrid` + `Pager`. «Viendo» y «Pendientes» son cascadas y no paginan | — | [06](06-gui-y-vistas.md) |
| ~~**«Viendo» en cascada con el último capítulo visto**~~ | ✅ **Hecho el 2026-08-20**, fase 3 del rediseño: `AnimeRow` + `SidePanel`; desde el 2026-09-01 su botón abre la ficha **por ese episodio** | — | [06](06-gui-y-vistas.md), [03 §12](03-flujos-de-ejecucion.md) |
| ~~**Rediseño completo de la interfaz**~~ | ✅ **Hecho entre el 2026-08-20 y el 2026-08-21**, en 9 fases (`plan-rediseno/`). No estaba en la lista: se cruzó por delante y cerró las cinco filas anteriores | — | todos los de la GUI |
| ~~**Reproducir los episodios dentro de la aplicación**~~ | ✅ **Hecho entre el 2026-09-23 y el 2026-10-20**, en 7 fases (`plan-reproductor/`). Deja **B14** y **C12** | — | [05 §9](05-proveedores-y-scraping.md), [06 §12](06-gui-y-vistas.md), [03 §13](03-flujos-de-ejecucion.md) |
| ~~**Bloque «Si te ha gustado X…» (4 animes del mismo género)**~~ | ✅ **Hecho el 2026-10-28** (0.5.0, fase 4): pestaña «Te puede interesar» de la ficha, una búsqueda por género **del proveedor** al abrirla, `PosterGrid` con sello. Sin recomendaciones de fuera (AniList, Jikan) | — | [03 §17](03-flujos-de-ejecucion.md), [06 §8](06-gui-y-vistas.md) |
| ~~**Temporadas y relacionados en la ficha**~~ | ✅ **Hecho el 2026-10-28** (0.5.0, fases 1-3; `plan-050/`): `RelatedAnime` y formato en los proveedores, `FranchiseService`, pestañas, carrusel, «← Volver a …» y la tarjeta de fin con la secuela. No estaba en la lista. Las relaciones **no se persisten** | — | [04 §1c](04-modelo-de-datos.md), [05 §3 y §3b](05-proveedores-y-scraping.md), [03 §15-§16](03-flujos-de-ejecucion.md), [06 §8](06-gui-y-vistas.md) |
| **Aviso de «nueva temporada» en lo finalizado** (P5, **aparcado**) | `FranchiseService` ya sabe recorrer la línea; faltaría lanzarlo para las filas de «Finalizados» (¿al entrar?, ¿con tope?) y pintar el aviso en la rejilla. 🔴 **Regla ya fijada por el usuario el 2026-10-28**: **no avisar si esa temporada ya está en la biblioteca**, en cualquier estado | decidir cuándo se pide (son peticiones que el usuario no ha pedido) | [03 §15](03-flujos-de-ejecucion.md), [06](06-gui-y-vistas.md) |
| **Convivencia anime + manga** | 🔴 **transversal**: `models.py` (¿`MediaInfo`?, y `ProviderInfo` gana el tipo de medio), `AnimeProvider` (¿`MediaProvider`?), `AnimeField`, las 6 vistas, `anime_window.py` (el TODO «alternar entre el manga y el anime») | decidir si se generalizan los modelos o se duplican | **todos** |
| **Nuevos lanzamientos a dos columnas (animes / mangas) si se eligen ambos** | `recentAnimes.py` (dos `PosterGrid` en vez de uno) | modelo de manga. ⚠️ El tamaño de la caché de pósters **ya no está en 4 sitios**: es `(248, 372)` y está duplicado a mano en `utils.py:27` y `Metrics.POSTER_CACHE_SIZE` (`theme.py:288`) | [06 §4](06-gui-y-vistas.md), [10](10-invariantes-y-trampas.md) |
| **Filtro Animes/Mangas/Ambos en las 4 vistas** | ~~`utilsButtons.AccordionFilterButton`~~ desapareció de las cuatro con el rediseño; el sitio sería junto a `GenreChips` o el `OrderMenu` de cada vista | modelo de manga | [06](06-gui-y-vistas.md) |
| **Desplegable global anime/manga/ambos (esquina inferior izquierda)** | `gui/components/sidebar.py` (junto a `__build_provider_block` / `__build_appearance_block`), y su modo plegado | modelo de manga; la preferencia va en `USER_SETTINGS`, sin migración ([11 §2c](11-playbooks.md)) | [06](06-gui-y-vistas.md), [01](01-arquitectura.md) |
| ~~**Integrar JKAnime**~~ | ✅ **Hecho el 2026-08-06**: `APIs/jkanime/jkanime.py` (nuevo, v0.1), `main_window.py`, `MiBibliotecaAnime.spec` | — | **[05 §3b](05-proveedores-y-scraping.md)**, [02](02-mapa-de-modulos.md), trampas 23-25 |
| **Integrar MonosChinos2, TioAnime** | `APIs/<sitio>/` nuevos, miembro nuevo en `AnimeProviderId`, registro en `main_window.py` y `hiddenimports` del `.spec`; si sus hosters no los cubre `APIs/resolvers/`, abrirán el navegador | ninguno — sigue mitigando R2 | [05](05-proveedores-y-scraping.md), [11 §3](11-playbooks.md) |
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
3. ~~**Arreglar B2**~~ — ✅ **hecho el 2026-10-21**. Para entonces el fallo ya no se veía: el
   rediseño se había llevado su único llamante. Se arregló en la persistencia para que no reaparezca
   con las recomendaciones por género.
4. ~~**Sacar la llamada de servidores del hilo de Tkinter**~~ — ✅ **hecho el 2026-09-24**, como fase 2
   del plan del reproductor, que la necesitaba antes de añadir una **segunda** petición en el mismo
   punto (la resolución del medio).
4b. ~~**Reproducir dentro de la aplicación**~~ — ✅ **hecho entre el 2026-09-23 y el 2026-10-20**, en
   7 fases (`plan-reproductor/`). No estaba en esta lista: se cruzó
   por delante, igual que el rediseño. Deja **B14** (hosters sin resolver) y **C12** (la DLL fuera del
   repo), y fuera de alcance a propósito: **recordar el minuto donde lo dejaste** (una columna más en
   `ANIMES`, no pedida) y elegir calidad o subtítulos (los playlists no ofrecen alternativas).
4c. ~~**Versión 0.5.0: temporadas, relacionados, «Te puede interesar» y B13**~~ — ✅ **hecha el
   2026-10-28**, en 6 fases (`plan-050/`). Deja **B18** (17 widgets sin `font=`), **C13** y el aviso de
   nueva temporada (**P5**, aparcado con su regla). **B18 y C13 se cerraron el 2026-10-29**, antes de
   publicarla, en `release/0.5.0`.
5. **Entonces** abordar la convivencia anime/manga, que es la refactorización grande. `ProviderInfo`
   ya tiene dónde llevar el tipo de medio, y `USER_SETTINGS` dónde guardar la preferencia.

> ~~**Selector de proveedor con preferencia persistida** (TODO #4)~~ — ✅ **hecho el 2026-07-30**
> ([13](13-selector-de-proveedor.md)) y **cerrado del todo el 2026-08-06** con el pin. Estrenó la
> infraestructura de esquema declarativo con **una BD nueva** (`DB_user.db`) y dejó el sitio donde
> guardar la futura preferencia anime/manga.

~~**A3** queda fuera de ese orden porque su urgencia depende de si vas a distribuir el `.exe`~~
✅ **Resuelto el 2026-08-17**, antes de que llegara a bloquear nada (§4 y §7).

Con R1 resuelto, cualquier punto del roadmap que necesite columnas o tablas nuevas (preferencia de
proveedor, calificación personal) es ya abordable sin riesgo para los datos existentes.

⚠️ Este orden es una **recomendación**, no una decisión tomada. Las prioridades son del usuario.

---

## 7. Licencia y cumplimiento de la distribución *(nueva, 2026-08-17)*

El proyecto pasó a ser formalmente **GPL-3.0-or-later** el 2026-08-17. Antes de esa fecha el
`README.md` lucía una *badge* de GPL **sin que existiera el fichero `LICENSE`**: es decir, no se
había concedido ninguna licencia y el código era, por defecto, «todos los derechos reservados».

### Qué se hizo

| # | Acción | Dónde | Por qué |
|---|---|---|---|
| L1 | `LICENSE` con el texto GPL-3.0 íntegro (674 líneas) | raíz, `bec0fbc` | Sin él la *badge* no respaldaba nada |
| L2 | Aviso de copyright a nombre del autor + sección «Licencia» | `README.md` | El `LICENSE` por sí solo no dice **de quién** es la obra; la §4 de la GPL obliga a conservar avisos, y no había ninguno que conservar |
| L3 | `LEEME.txt` junto al `.exe` | raíz → `dist/` | **§6**: toda distribución binaria debe indicar cómo obtener el código fuente correspondiente |
| L4 | `THIRD-PARTY-NOTICES.txt` (14 componentes; **20** desde el 2026-10-20) | raíz → `dist/` | MIT, BSD, Apache-2.0, HPND y MPL-2.0 **exigen** reproducir sus avisos en redistribuciones binarias |
| L5 | Reclamos falsos corregidos | `README.md` | Ver §3: «100 % offline» y «sin dependencias web» en una app que vive del scraping |
| 🆕 L4b | **Seis componentes más** en `THIRD-PARTY-NOTICES.txt` (fase 5 del reproductor, 2026-10-20): `python-mpv` y libmpv, que son nuevos, y **cuatro que ya viajaban** en el `.exe` sin aviso —brotli 1.1.0 (MIT), PySocks 1.7.1 (BSD-3), pyparsing 3.1.4 (MIT) y el `pkg_resources` de setuptools 63.2.0 (MIT)—. Contrastado contra el `PYZ-00.toc` del build nuevo **y** del anterior: los cuatro ya faltaban antes | raíz → `dist/` | Se descubrieron al contrastar el binario, no `requirements.txt` |
| 🆕 L4c | **La §6 de la GPL para `libmpv-2.dll`**: los avisos dan la versión exacta y los enlaces al fuente de mpv (`6fd80b2003`), FFmpeg (`7d14defcc`) y la receta de compilación (`mpv-winbuild-cmake`, etiqueta `20260923`), **más una oferta de facilitar el fuente** si esos enlaces caen, pidiéndolo en las *Issues* del repositorio. `LEEME.txt` remite ahí. ✅ **Corregido el 2026-10-21**: decía que la receta daba «la versión exacta de cada biblioteca», y **no la da** (L12). Ahora cada biblioteca lleva su origen y su versión, exacta o reconstruida | `THIRD-PARTY-NOTICES.txt`, `LEEME.txt` | La DLL es GPL y viaja en binario: la §6 obliga a dar acceso al fuente correspondiente. ⚠️ **La oferta compromete al autor**: el usuario decidió el 2026-10-21 **mantenerla** (en vez de alojar copias). Cumplirla es posible porque cada versión está identificada |

### Compatibilidad de licencias ✅

Comprobado el 2026-08-17 leyendo los `LICENSE` reales de `biblio_anime_env/Lib/site-packages`, con
la lista de paquetes contrastada contra `build/MiBibliotecaAnime/Analysis-00.toc` — **lo que
PyInstaller mete de verdad en el binario**, no lo que declara `requirements.txt`:

| Componente | Licencia | ¿Compatible con GPL-3.0? |
|---|---|---|
| requests 2.32.3, packaging 24.1 | Apache-2.0 | ✅ (con GPLv3, no con GPLv2) |
| urllib3, charset-normalizer, beautifulsoup4, soupsieve, customtkinter | MIT | ✅ |
| idna, darkdetect | BSD-3-Clause | ✅ |
| Pillow 11.0.0 | MIT-CMU (HPND) | ✅ |
| typing_extensions | PSF-2.0 | ✅ |
| **certifi 2024.8.30** | **MPL-2.0** | ✅ vía cláusula 3.3 (*Secondary Licenses*) |
| CPython, Tcl/Tk | PSF-2.0 / BSD-style | ✅ |
| PyInstaller (bootloader) | GPL-2.0 **con excepción** | ✅ no contamina el `.exe` |
| 🆕 brotli 1.1.0, pyparsing 3.1.4, setuptools 63.2.0 (`pkg_resources`) | MIT | ✅ |
| 🆕 PySocks 1.7.1 | BSD-3-Clause | ✅ |
| 🆕 **python-mpv 1.0.8** | **GPL-2.0-or-later o LGPL-2.1-or-later**, a elegir | ✅ (la ficha de la fase 5 lo daba por MIT: no lo es) |
| 🆕 **libmpv-2.dll** (mpv `v0.41.0-1055-g6fd80b200` + FFmpeg `N-126773-g7d14defcc`) | **GPL-3.0-or-later en conjunto**: mpv compilado sin `-Dgpl=false` y FFmpeg con `--enable-gpl --enable-version3`, sin `nonfree` | ✅ misma licencia que el proyecto; obliga a la §6 (L4c) |

Dos apuntes que costaron una comprobación extra:

- **`customtkinter`**: sus metadatos declaran `CC0`, pero el fichero `LICENSE` real del paquete es
  **MIT © 2023 Tom Schimansky**. Manda el fichero → sí lleva atribución.
- ✅ **`selenium`, `pythonnet` y `shiboken2` están en el venv pero NO viajan en el `.exe`.** Se
  comprobó expresamente: `shiboken2` es GPL/LGPL/comercial y habría sido un conflicto real.

### Qué queda abierto

| # | Pendiente | Gravedad |
|---|---|---|
| **B11** | Origen desconocido de los iconos y los GIF de carga → probable incompatibilidad con la GPL (§4 🟡) | 🟡 |
| L6 | Descargo de responsabilidad sobre el origen de los datos | 🟢 criterio, no obligación |
| L7 | Cabeceras `SPDX-License-Identifier` de una línea en los `.py` | 🟢 cosmético |
| L8 | Diálogo «Acerca de» con versión, copyright y licencia — lo sugiere el propio apéndice de la GPL para programas con GUI | 🟢 |
| L9 | El generador de `THIRD-PARTY-NOTICES.txt` vive en el scratchpad, no en el repo. 🆕 La fase 5 usó otro, `notices_add.py`, que **añade** secciones en vez de regenerar desde cero: tampoco está en el repo. ✅ **La sección de libmpv sí tiene generador en el repo desde el 2026-10-21**: `tools/actualizar_libmpv.py` (ver L10). Lo de Python sigue a mano | 🟢 el fichero caduca al tocar `requirements.txt` |
| ~~**L10**~~ | ~~**No se reproducen íntegros** los avisos de las ~45 bibliotecas enlazadas **dentro** de libmpv ni los de los paquetes que `pkg_resources` lleva vendorizados~~ ✅ **Cerrado el 2026-10-21.** Eran **89** fuentes, no ~45, más 3 submódulos y 71 crates de Rust (las de `subrandr`). La sección de libmpv la genera ahora `tools/actualizar_libmpv.py` entre marcas: lista cada biblioteca con origen, versión y nota, y reproduce **144 textos propios** (avisos MIT/BSD/ISC/zlib…, deduplicados) y **una sola copia** de cada licencia estándar (GPL-2.0, LGPL-2.0/2.1/3.0, Apache-2.0, MPL-2.0; la GPL-3.0 es el `LICENSE`). Los 9 paquetes de `pkg_resources` (versiones de su `vendored.txt`) van íntegros en la sección de setuptools. `THIRD-PARTY-NOTICES.txt`: 2 460 → 16 810 líneas | — |
| ~~**L11**~~ | ~~**La receta de FFmpeg se leyó de `master`**~~ ✅ **Cerrado el 2026-10-21**: leída en la etiqueta `20260923` (commit `05a60b3c`): `--enable-gpl --enable-version3`, sin `--enable-nonfree`. La DLL lo confirma: lleva x264 y x265 y no lleva `fdk-aac` | — |
| **L12** 🆕 | **Las versiones de las bibliotecas de la DLL son reconstruidas, no certificadas.** La receta clona cada una en la punta de su rama al compilar y no lo anota (ni la release ni la compilación de CI lo publican). La herramienta toma el último commit de esa rama **anterior al arranque de la compilación**; ✅ **coincide con el hash real de mpv y de FFmpeg** en las dos releases probadas (`20260923` y `20261020`), que son los únicos que se pueden contrastar. Los avisos lo dicen así y mantienen la **oferta escrita** como respaldo. La única forma de tenerlas certificadas sería compilar la DLL con versiones fijas | 🟢 asumido y declarado |
| **L13** 🆕 | **No se ha auditado la compatibilidad de cada biblioteca por separado**: la del conjunto (GPL-3.0) se apoya en que FFmpeg se configura con `--enable-version3` y en las licencias de los ficheros. Casos a mirar si algún día importa: `davs2` (GPL-2, sin comprobar si «o posterior») y los submódulos, que pueden ser solo de pruebas | 🟢 |

⚠️ **`THIRD-PARTY-NOTICES.txt` caduca**: hay que regenerarlo cada vez que cambie una dependencia.
El paso está en el playbook de empaquetado ([11 §6](11-playbooks.md)).
