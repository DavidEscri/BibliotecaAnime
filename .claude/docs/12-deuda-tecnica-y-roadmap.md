# 12 — Deuda técnica y roadmap

| | |
|---|---|
| **Fecha** | 2026-07-28 · **Commit** `a972850` · árbol **sucio** |
| **Cubre** | `src/**`, `.claude/CLAUDE.md`, `README.md`, `requirements.txt`, `MiBibliotecaAnime.spec` |

Procedencia: ✅ verificado en ejecución · 📖 leído en código · ⚠️ sin verificar.

---

## 1. Estado del árbol de trabajo

📖 `git status` en `a972850` (rama `develop`):

| Fichero | Cambio |
|---|---|
| `src/gui/anime_window.py` | +1 línea: TODO «alternar entre manga y anime» (`:25`) |
| `src/gui/main_window.py` | +5 líneas: TODOs de renombrado y selector de proveedor (`:30-34`) |
| `src/gui/sidebarButtons/recentAnimes/recentAnimes.py` | +1 línea: TODO «nuevos lanzamientos» (`:19`) |
| `src/gui/sidebarButtons/searchAnimes/searchAnimes.py` | **cambio funcional**: `from attr import dataclass` → `from dataclasses import dataclass` (arreglo de A2, ver §4) |
| `src/utils/buttons/utilsButtons.py` | ±1 línea: TODO color de texto en modo oscuro (`:56`) |
| `resources/images/utils/pendientes_dark.png` | **sin trackear** |
| `resources/images/utils/pendientes_light.png` | **sin trackear** |
| `resources/images/utils/viendo_dark.png` | **sin trackear** |
| `resources/images/utils/viendo_light.png` | **sin trackear** |
| `.vscode/` | **sin trackear** |
| `.claude/` | **sin trackear** (incluye esta documentación) |

Salvo el arreglo de A2 en `searchAnimes.py` (cambio de import, sin efecto en el comportamiento),
**los cambios en `src/` son comentarios `TODO`**. Ninguna lógica se ha modificado respecto a
`a972850`.

---

## 2. TODOs reales en el código

📖 Los 6 que existen, con `fichero:línea`:

| # | Ubicación | Contenido | Documento afectado |
|---|---|---|---|
| 1 | `gui/anime_window.py:22-23` | Al final de la lista de episodios, frame «Si te ha gustado X, te puede interesar…» con 4 animes del mismo género | [06](06-gui-y-vistas.md), [03](03-flujos-de-ejecucion.md) |
| 2 | `gui/anime_window.py:25` | Botón para alternar entre manga y anime | [06](06-gui-y-vistas.md), [01](01-arquitectura.md) |
| 3 | `gui/main_window.py:30` | Quitar la palabra «Anime» de los nombres de botones y del título | [06](06-gui-y-vistas.md) |
| 4 | `gui/main_window.py:31-34` | `CTkOptionMenu` para elegir proveedor, con preferencia persistida en **una tabla nueva** de configuración; preparado para proveedores de manga | [04](04-modelo-de-datos.md), [05](05-proveedores-y-scraping.md), [11 §2](11-playbooks.md) |
| 5 | `utils/buttons/utilsButtons.py:56` | El color del texto debe cambiar a blanco en apariencia oscura | [06 §5](06-gui-y-vistas.md) |
| 6 | `gui/sidebarButtons/recentAnimes/recentAnimes.py:19` | Renombrar «recientes» a «nuevos lanzamientos» | [06](06-gui-y-vistas.md) |

> El TODO #4 es el más caro: implica **la primera tabla nueva** del proyecto y, por tanto, resolver
> antes la ausencia de migraciones ([11 §2](11-playbooks.md)).

---

## 3. Discrepancias entre `CLAUDE.md` y el código

Auditado punto por punto. Donde el código contradice a `CLAUDE.md`, **gana el código**.

| # | `CLAUDE.md` afirma | Realidad | Evidencia |
|---|---|---|---|
| D1 | «el resto de updates asumen que ya está en BD y **devuelven `False`** si no» | ✅ Solo 3 de 6 lo hacen. `update_anime_episodes`, `update_anime_to_not_favourite` y `update_anime_to_not_pending` devuelven **`True`** | `sqlite.py:32-46` no mira `rowcount` |
| D2 | Registro: «`AnimeFLVSingleton(), default=True` … `AnimeAV1Singleton()`» en el ejemplo del docstring | 📖 En el código real es al revés: **AnimeAV1 por defecto** | `animeProviderMgr.py:126-127` (docstring) vs `main_window.py:48-49` |
| D3 | «`get_anime_image()` busca en `favourite`, `finished`, `pending`, `recent_animes` y `search`» | Correcto **como descripción**, pero omite señalar que **falta `watching`**, y eso es un bug ✅ | `utils.py:168` |
| D4 | «la ficha de detalle los pide a `(195, 275)`» | ✅ Cierto salvo en la rama de red, que devuelve **20×20** por no pasar `size=` | `utils.py:176-177` |
| D5 | «`AnimeAV1` … usa el DOM solo como *fallback*» | 📖 Matiz: **`poster` y `genres` salen SIEMPRE del DOM**, no del payload — aunque los géneros están en el payload | `animeav1.py:197-200` |
| D6 | «`episodes` se guarda invertido» | ✅ Cierto, pero no dice que **el orden de partida depende del proveedor** (AV1 ascendente, FLV descendente), así que el resultado en BD es opuesto según quién sirvió el dato | `animeav1.py:205` vs `animeflv.py:222-223` |
| D7 | «Muestra … la lista de episodios (**los 25 primeros**, `[:25]`)» | ✅ Correcto. El comentario del propio código dice «24» (`anime_window.py:302`) | `anime_window.py:263` |
| D8 | Lista los TODOs de `main_window.py`, `anime_window.py`, `recentAnimes.py`, `utilsButtons.py` | ✅ Correcto y completo (6 TODOs) | §2 |
| D9 | «`.spec` … no incluye `APIs.animeav1.animeav1`, `APIs.common.animeProviderMgr` ni `APIs.common.models`, y declara `gui.anime_windows`» | ✅ Correcto. **Además** declara `gui.sidebarButtons.sidebarButton`, que tampoco existe | `MiBibliotecaAnime.spec:30` |
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
| A1 | **Sin migraciones de BD** | `animesPersistence.py:221-227` | Cualquier columna nueva rompe silenciosamente las instalaciones con datos. Bloquea el TODO #4 |
| A3 | **`.spec` desactualizado** | `MiBibliotecaAnime.spec:21-36` | El `.exe` falla en runtime, no al compilar |
| A4 | **Póster a 20×20 al descargar** | `utils.py:176-177` | Visible para el usuario en cada ficha no cacheada |
| A5 | **Mojibake en la sinopsis de AnimeAV1** | `animeav1.py:169` | Texto roto en pantalla **y persistido en BD** |
| A6 | **Widgets Tk desde hilos daemon** | `main_window.py:211-220`, `searchAnimes.py:219-223`, `utils.py:127-128` | Riesgo de cuelgue; funciona por suerte estructural |

### 🟡 Media

| # | Problema | Dónde |
|---|---|---|
| B1 | `get_anime_image` no busca en `watching/` | `utils.py:168` |
| B2 | La ordenación por géneros nunca se aplica (`str` vs enum) | `utilsButtons.py:187` |
| B3 | Guard antidoble-búsqueda inoperante (`.start()` → `None`) | `searchAnimes.py:205,211,329` |
| B4 | HTTP en el hilo de UI: servidores y clic desde 5 de las 6 vistas | `anime_window.py:459`, `favouriteAnimes.py:131`… |
| B5 | `AnimeWindowViewer(mw, None)` peta si el manager devuelve `None` | `anime_window.py:33` + las 5 vistas |
| B6 | Las 4 listas cacheadas de `MainWindow` **no las usa nadie** | `main_window.py:59-62` vs `favouriteAnimes.py:75` |
| B7 | `remove_from_finished` mueve a *pendiente* en BD pero **borra el póster sin recrearlo** en `pending/` | `anime_window.py:213-214` |
| B8 | `time.sleep(0.1)` en el hilo de UI × 7 | [07 §5](07-concurrencia-e-hilos.md) |
| B9 | Stub muerto `WatchingAnimeButton` | `watchingAnimes/__init__.py` |
| B10 | El buscador de las vistas de estado va **contra la red**, no contra la BD | `favouriteAnimes.py:82` y homólogos |

### 🟢 Baja

| # | Problema | Dónde |
|---|---|---|
| C1 | Erratas en `__module__` (`anime_wnidow.py`, `animeProvider.py`, falta `.py`) | [08 §1](08-convenciones-y-estilo.md) |
| C2 | `update_gif` suelto, muerto y roto | `utils.py:48-51` |
| C3 | `removeprefix` devuelve `None` si los tipos difieren | `utils.py:24-38` |
| C4 | `SearchButton` duplicado (widget vs vista) | `utilsButtons.py:37` y `searchAnimes.py:34` |
| C5 | Nomenclatura mixta `show_*` / `__show_*` en las vistas | [06 §3](06-gui-y-vistas.md) |
| C6 | `AccordionFilterButton` crea un frame nuevo en cada expansión | `utilsButtons.py:122-128` |
| C7 | `info_frame` con `fg_color="white"` fijo, no respeta el tema | `anime_window.py:79` |
| C8 | `-> (bool, list)` como anotación de tipo | `sqlite.py:48` |
| C9 | Comentario «24 primeros» donde el código dice 25 | `anime_window.py:302` |
| C10 | `README.md` describe funciones inexistentes | §3 |
| C11 | La BD del desarrollador se empaqueta en el `.exe` | `MiBibliotecaAnime.spec:12` |

### ✅ Resuelto

| # | Problema | Resuelto | Cómo |
|---|---|---|---|
| A2 | **`attrs` no declarada** — `searchAnimes.py:15` hacía `from attr import dataclass` de un paquete ausente de `requirements.txt`, presente solo como transitiva de `selenium → trio → outcome → attrs`. Entorno limpio → `ModuleNotFoundError: No module named 'attr'` | 2026-07-28 | Sustituido por `from dataclasses import dataclass` (stdlib). Se elimina la dependencia en vez de declararla; `src/` ya no referencia `attrs` ni `selenium`. ✅ Verificado importando el módulo e instanciando `AnimeSearch` |

> Los identificadores retirados (`A2`) **no se reutilizan**: otros documentos los citan.

---

## 5. Los 3 riesgos que más preocupan

### R1 — La ausencia de migraciones bloquea todo el roadmap

Cada punto interesante del roadmap (calificación personal, preferencia de proveedor, convivencia
anime/manga) necesita **columnas o tablas nuevas**. Hoy, añadirlas corrompe silenciosamente las
instalaciones existentes ([10, trampa 2](10-invariantes-y-trampas.md)) — y la BD del usuario, con 24
animes reales, es exactamente ese caso. **Es la primera deuda a pagar**, antes que cualquier
funcionalidad.

### R2 — Dependencia de un único proveedor sano

AnimeAV1 es el por defecto y **el único operativo**: AnimeFLV ya no sirve servidores de vídeo. El
mecanismo de fallback existe pero hoy no tiene a dónde caer. Además, el parseo de AnimeAV1 depende de
**regex sobre un payload JS no estructurado**: cualquier despliegue del sitio puede romperlo sin
aviso, y el fallback al DOM solo cubre `title`, `synopsis` y el conteo de episodios — **no** los
servidores. Integrar un tercer proveedor es una medida de resiliencia, no un capricho.

### R3 — Manipulación de widgets Tk desde hilos daemon

El arranque construye **toda** la vista de recientes desde un hilo secundario
(`main_window.py:220`), y el buscador hace lo mismo con cada resultado. Tkinter no es thread-safe.
✅ Hoy funciona, pero es el tipo de fallo que aparece como un cuelgue esporádico e irreproducible en
la máquina del usuario, imposible de depurar sin logs (y `console=False` en el `.exe` los borra).

---

## 6. El roadmap traducido a impacto técnico

Roadmap declarado en `.claude/CLAUDE.md` y `README.md:124-130`.

| Punto del roadmap | Módulos a tocar | Requisitos previos | Docs a actualizar |
|---|---|---|---|
| **Renombrar «recientes» → «nuevos lanzamientos»** | `recentAnimes.py:19,24`, `main_window.py:30` | ninguno — es el más barato | [06](06-gui-y-vistas.md), [02](02-mapa-de-modulos.md) |
| **Quitar «Anime» de los nombres de pestañas** | las 6 vistas + `main_window.py:105` | ninguno | [06](06-gui-y-vistas.md) |
| **Selector de proveedor con preferencia persistida** | `main_window.py:144-151`, **tabla nueva** en `animesPersistence.py` | 🔴 **R1: migraciones** | [04](04-modelo-de-datos.md), [05](05-proveedores-y-scraping.md), [11 §2](11-playbooks.md) |
| **Calificación personal en favoritos + ordenar por ella** | `AnimeField`, `AnimeRecord`, `anime_window.py`, `favouriteAnimes.py` | 🔴 **R1** + arreglar B2 (`str` vs enum) | [04](04-modelo-de-datos.md), [06](06-gui-y-vistas.md) |
| **Paginar favoritos/viendo/pendientes/finalizados de 10 en 10** | las 4 vistas de estado; reutilizar `searchAnimes.py:267-324` | extraer la paginación a `utilsButtons.py` | [06](06-gui-y-vistas.md), [03](03-flujos-de-ejecucion.md) |
| **«Viendo» en cascada con el último capítulo visto** | `watchingAnimes.py` | ya está en BD (`last_watched_episode`) — barato | [06](06-gui-y-vistas.md) |
| **Bloque «Si te ha gustado X…» (4 animes del mismo género)** | `anime_window.py:22-23`, `get_anime_by_genre_and_order` | arreglar B2 primero | [03](03-flujos-de-ejecucion.md), [06](06-gui-y-vistas.md) |
| **Convivencia anime + manga** | 🔴 **transversal**: `models.py` (¿`MediaInfo`?), `AnimeProvider` (¿`MediaProvider`?), `AnimeField`, las 6 vistas, `anime_window.py:25` | 🔴 R1 + decidir si se generalizan los modelos o se duplican | **todos** |
| **Nuevos lanzamientos a dos columnas, 3 por fila, pósters grandes** | `recentAnimes.py:39,55-80`, tamaños de `utils.py:59,87,137` | el redimensionado a `(130,185)` está **hardcodeado en 4 sitios** | [06 §4](06-gui-y-vistas.md), [10](10-invariantes-y-trampas.md) |
| **Filtro radio Animes/Mangas/Ambos en las 4 vistas** | `utilsButtons.AccordionFilterButton` | modelo de manga | [06](06-gui-y-vistas.md) |
| **Desplegable global anime/manga/ambos (esquina inferior izquierda)** | `main_window.py:137-151` | modelo de manga + preferencia persistida → R1 | [06](06-gui-y-vistas.md), [01](01-arquitectura.md) |
| **Integrar JKAnime, MonosChinos2, TioAnime** | `APIs/<sitio>/` nuevos + `main_window.py:48-49` | ninguno — **es lo que más mitiga R2** | [05](05-proveedores-y-scraping.md), [11 §3](11-playbooks.md) |
| **Proveedores de manga** | contrato nuevo o generalización de `AnimeProvider` | decisión de diseño de la convivencia | [01](01-arquitectura.md), [05](05-proveedores-y-scraping.md) |
| **Capítulo de manga por el que continuar tras el anime** | requiere mapeo anime↔manga | modelo de manga + fuente de datos del mapeo | [04](04-modelo-de-datos.md) |

### Orden sugerido

1. **Pagar A3, A4, A5** — son arreglos pequeños con impacto visible o de despliegue.
   (~~A2~~ ya pagada: ver [§4 → Resuelto](#-resuelto).)
2. **Resolver R1 (migraciones)** — desbloquea todo lo demás.
3. **Integrar un tercer proveedor** — mitiga R2 y valida que la abstracción aguanta.
4. **Entonces** abordar la convivencia anime/manga, que es la refactorización grande.

⚠️ Este orden es una **recomendación**, no una decisión tomada. Las prioridades son del usuario.
