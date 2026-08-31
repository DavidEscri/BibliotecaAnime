# 09 — Verificación y pruebas

| | |
|---|---|
| **Fecha** | 2026-08-31 · rama `feature/ui-redisign` · árbol **con el arreglo del fondo de la pantalla de carga sin commitear** |
| **Última revisión** | 2026-08-31 (**fondo de la pantalla de carga**): §7.1 gana la comprobación del fondo del arranque —que a ojo se falla— y la receta de captura de §8 usa el título real de la ventana. Antes, 2026-08-16 (**columna `provider_id`**): **§3c nuevo** — las 8 tandas de comprobaciones de la fase 8, **351 sin fallos**; checklist de §7 puesto al día con lo que ha cambiado de comportamiento |
| **Cubre** | procedimiento; scripts ejecutados el 2026-07-28 contra el código de `src/` |

Procedencia: ✅ verificado en ejecución · 📖 leído en código · ⚠️ sin verificar.

> **No hay suite de tests, ni linter, ni formateador.** `TESTS/` está en `.gitignore` y contiene
> ejemplos de terceros y scripts sueltos de scraping — **no es del proyecto**. No inventes comandos de
> test ni tomes `TESTS/` como referencia.

---

## 0. Reglas inquebrantables

1. 🔴 **`resources/DB/DB_Animes.db` es la biblioteca real del usuario.** Nunca escribas en ella desde
   un script. Cópiala al scratchpad y **parchea `get_resource_path`** (§3).
2. 🔴 **Los scripts desechables van al scratchpad**, nunca al repositorio.
3. 🟡 **Sé educado con los sitios scrapeados**: 1-2 llamadas por método, en serie, con `sleep(2)`.
   Es verificación, no benchmarking.

---

## 1. Arrancar la app

```bash
cd "D:\Proyectos Python\BibliotecaAnime"
biblio_anime_env\Scripts\python.exe src/app.py
```

📖 Debe lanzarse **como script**: eso pone `src` en `sys.path` y hace funcionar los imports absolutos.
`python -m src.app` **no** funciona. El cwd es irrelevante (`get_resource_path`), pero los ejemplos de
este documento asumen la raíz del repo.

`.vscode/launch.json` y `tasks.json` ya lo lanzan con el intérprete de `biblio_anime_env/`.

✅ **Resultado esperado** (verificado el 2026-07-28): GIF de carga con barra de progreso →
0 %→40 % (BD) → 90 % → 100 % (pósters) → rejilla de recientes y sidebar visible. Título de ventana
«**Mi Biblioteca**» — perdió el «de Anime» en la fase 1 del rediseño. Único mensaje en consola:

```
No se pudo borrar la imagen Chi.: [WinError 2] El sistema no puede encontrar el archivo
especificado: '…\resources\images\recent_animes\Chi.'
```

⚠️ Ese aviso es un fichero huérfano preexistente en la caché ([03 §9](03-flujos-de-ejecucion.md)); no
indica un fallo del arranque.

---

## 2. Probar los proveedores sin GUI

Guarda como `<scratchpad>\v1_providers.py`:

```python
# Verificacion: proveedores contra el sitio real. Peticiones en serie, con pausas.
import sys, time
sys.path.insert(0, r"D:\Proyectos Python\BibliotecaAnime\src")

from APIs.animeflv.animeflv import AnimeFLVSingleton
from APIs.animeav1.animeav1 import AnimeAV1Singleton
from APIs.common.models import AnimeGenreFilter, AnimeOrderFilter

def show(label, obj, n=3):
    print(f"\n=== {label} ===")
    if isinstance(obj, tuple):
        lst, last = obj; print(f"  last_page={last}"); obj = lst
    print(f"  len={len(obj)}")
    for x in obj[:n]: print("   ", x)

for name, prov in (("AnimeAV1", AnimeAV1Singleton()), ("AnimeFLV", AnimeFLVSingleton())):
    print(f"\n############ {name} ({prov.BASE_URL}) ############")
    probe = "one-piece" if name == "AnimeAV1" else "one-piece-tv"
    try:
        show("get_recent_animes", prov.get_recent_animes())
    except Exception as e: print("  EXC:", type(e).__name__, e)
    time.sleep(2)

    info = prov.get_anime_info(probe)
    print(f"\n=== get_anime_info({probe}) ===")
    if info:
        print("   title   =", repr(info.title))
        print("   poster  =", repr(info.poster))
        print("   synopsis=", repr((info.synopsis or "")[:100]))
        print("   genres  =", info.genres)
        print("   n_eps   =", len(info.episodes or []))
        print("   ORDEN   :", [e.id for e in (info.episodes or [])[:3]], "…",
                              [e.id for e in (info.episodes or [])[-3:]])
    time.sleep(2)

    show("search_animes_by_query('naruto',1)", prov.search_animes_by_query("naruto", 1))
    time.sleep(2)
    show("search_by_genres_and_order", prov.search_animes_by_genres_and_order(
        [AnimeGenreFilter.ACCIÓN, AnimeGenreFilter.AVENTURA],
        AnimeOrderFilter.ALFABÉTICAMENTE.value, 1))
    time.sleep(2)
    show(f"get_anime_episode_servers({probe}, 1)", prov.get_anime_episode_servers(probe, 1), n=8)
    time.sleep(2)
```

```powershell
$env:PYTHONIOENCODING="utf-8"
biblio_anime_env\Scripts\python.exe <scratchpad>\v1_providers.py
```

✅ **Resultados del 2026-07-28** — úsalos como línea base:

| Método | AnimeAV1 | AnimeFLV |
|---|---|---|
| `get_recent_animes` | 20 | 24 |
| `get_anime_info` | 1171 eps, **ascendentes** | 1167 eps, **descendentes** |
| `search_animes_by_query("naruto")` | 19, `last_page=1` | 12, `last_page=1` |
| `search_by_genres_and_order` | 20, `last_page=50` | 24, `last_page=79` |
| `get_anime_episode_servers` | **5** | **0** ❌ |

`PYTHONIOENCODING=utf-8` es necesario o la consola de Windows peta con los títulos y tildes.

---

## 3. Probar la persistencia — **sobre una copia**

El truco clave: **parchear `get_resource_path` antes de importar la persistencia**, y verificar con
un `assert` que la ruta apunta al sandbox.

```python
import os, shutil, sqlite3, sys

REPO    = r"D:\Proyectos Python\BibliotecaAnime"
SCRATCH = os.path.dirname(os.path.abspath(__file__))
SANDBOX = os.path.join(SCRATCH, "sandbox")
os.makedirs(os.path.join(SANDBOX, "resources", "DB"), exist_ok=True)

REAL_DB = os.path.join(REPO, "resources", "DB", "DB_Animes.db")
COPY_DB = os.path.join(SANDBOX, "resources", "DB", "DB_Animes.db")
if os.path.exists(REAL_DB):
    shutil.copy2(REAL_DB, COPY_DB)          # ← COPIA, nunca la original

sys.path.insert(0, os.path.join(REPO, "src"))

# --- Redirigir get_resource_path ANTES de importar la persistencia ---
import utils.utils as u
u.get_resource_path = lambda rel: os.path.normpath(os.path.join(SANDBOX, rel))
import dataPersistence.animesPersistence as dp
dp.get_resource_path = u.get_resource_path          # ← el import 'from' ya copió el símbolo

from dataPersistence.animesPersistence import AnimesPersistence, AnimeRecord, AnimeStatus
from APIs.common.models import AnimeInfo, EpisodeInfo

p = AnimesPersistence()
assert SANDBOX in p.path_db, "ABORTADO: apuntaría a la BD real"   # ← red de seguridad
p.start()

# Esquema real
con = sqlite3.connect(p.path_db)
print([c[1] for c in con.execute("PRAGMA table_info(ANIMES)")] == AnimesPersistence.FIELDS)
con.close()

TEST_ID = "__test-anime-doc__"
info = AnimeInfo(id=TEST_ID, title="Prueba", poster="http://x/p.jpg", synopsis="s",
                 genres=["accion"], episodes=[EpisodeInfo(id=i, anime=TEST_ID) for i in range(1, 11)])

# 1. Alta + exclusión mutua
p.update_anime_to_watching(info)
def flags(t):
    r = p.get_anime_by_anime_id(TEST_ID)
    print(f"{t:<28} fav={int(r.is_favourite)} w={int(r.is_watching)} "
          f"f={int(r.is_finished)} p={int(r.is_pending)}")
flags("watching"); p.update_anime_to_finished(info); flags("finished")
p.update_anime_to_pending(info);  flags("pending")
p.update_anime_to_not_finished(TEST_ID); flags("not_finished")

# 2. Round-trip de watched_episodes discontinuos
p.update_watched_episodes(TEST_ID, {1, 2, 3, 5, 9})
con = sqlite3.connect(p.path_db)
print("RAW:", con.execute("SELECT watched_episodes, last_watched_episode FROM ANIMES "
                          "WHERE anime_id=?", (TEST_ID,)).fetchone())
con.close()
print("leído:", sorted(p.get_watched_episodes(TEST_ID)))

# 3. Round-trip de episodes: ¿mismo orden?
r = p.get_anime_by_anime_id(TEST_ID)
print("entrada:", [e.id for e in info.episodes], "→ leído:", r.episodes)
```

✅ **Resultados del 2026-07-28** — la línea base a comparar:

| Comprobación | Resultado |
|---|---|
| Orden de columnas == `FIELDS` | **`True`** |
| Exclusión mutua watching/finished/pending | **respetada en las 8 transiciones** |
| `FAVOURITE` independiente | **sí** |
| `{1,2,3,5,9}` → BD | **`[[1, 3], [5, 5], [9, 9]]`**, `last_watched = 9` |
| `set()` → BD | `[]`, `last_watched = 0` |
| `episodes` entrada `[1..10]` → leído | **`[10..1]`** — ⚠️ **NO conserva el orden** |
| `update_watched_episodes` sobre inexistente | `False` |
| `update_anime_episodes` sobre inexistente | ⚠️ **`True`** (no mira `rowcount`) |

---

## 3b. Probar una migración de esquema

🔴 **Sobre una copia de la BD real, nunca sobre `resources/DB/DB_Animes.db`.** El patrón es
independiente de la GUI: se instancia `AnimesPersistence` sin pasar por `__init__` y se le inyecta la
ruta de la copia.

```python
import os, shutil, sqlite3, sys
sys.path.insert(0, r"D:\Proyectos Python\BibliotecaAnime\src")
from dataPersistence.animesPersistence import AnimesPersistence, AnimeField
from utils.db.sqlite import SqlUtils, TableSchema

shutil.copy(r"D:\Proyectos Python\BibliotecaAnime\resources\DB\DB_Animes.db", "copia.db")

p = AnimesPersistence.__new__(AnimesPersistence)   # sin __init__: no toca get_resource_path
p.path_db, p._db = "copia.db", SqlUtils("copia.db")

# Simular el esquema futuro sin tocar AnimeField
p.SCHEMA = [TableSchema("ANIMES",
                        [(f.column, f.sql_type) for f in AnimeField] + [("user_rating", "INTEGER")],
                        f"{AnimeField.ID.column} AUTOINCREMENT",
                        defaults={"user_rating": 0})]

print(p.diff_table(p.SCHEMA[0]))       # qué va a hacer, antes de hacerlo
print(p.validate_db_integrity())       # aplicarlo
print([c[1] for c in sqlite3.connect("copia.db").execute("PRAGMA table_info(ANIMES)")])
print(p.diff_table(p.SCHEMA[0])["needs_migration"])   # False → idempotente
```

**Qué comprobar siempre**:

- `diff_table()` **antes** de migrar: `missing` / `extra` / `retyped` / `reordered` dicen qué ruta se
  tomará (`ADD COLUMN` si solo hay `missing` en el sufijo; reconstrucción en cualquier otro caso).
- El **número de filas** no cambia y una fila conocida conserva sus valores campo a campo (una
  reconstrucción mal hecha desplaza columnas sin lanzar error — trampa 1).
- El orden físico coincide con `FIELDS`.
- Segunda pasada → `needs_migration == False` y **ninguna copia de seguridad nueva**.
- Existe la copia en `<dir de la BD>/backups/`.

✅ **Resultados del 2026-07-30** (`scratchpad/test_migraciones.py`, 57 comprobaciones, 0 fallos):
retipado de `anime_id` sobre la BD real con 24 filas (datos idénticos, `sqlite_sequence` conservado),
columna al final por `ADD COLUMN`, columna en medio por reconstrucción, desorden de columnas, tabla
nueva `CONFIG`, BD desde cero, idempotencia y rollback ante SQL inválido.

---

## 3c. Cómo se verificó la columna `provider_id` *(2026-08-16)*

**351 comprobaciones en 8 scripts, 0 fallos.** Todos en el scratchpad de la sesión —**no en el
repo**—, todos sobre una **copia** de la BD real. Sirven de plantilla para el siguiente cambio grande.

| Script | Comprobaciones | Qué cubre |
|---|---:|---|
| `test_fase1.py` | 31 | `AnimeProviderId` / `ProviderInfo`, `provider_info()`, validación de `__init_subclass__`, los 3 proveedores registrando bien |
| `test_fase2.py` | 50 | la columna: esquema, migración sobre copia, serialización, `update_anime_provider_id` |
| `test_fase3.py` | 20 | estampado (`__stamp_provider`) en las 3 formas de resultado + autorrelleno |
| `test_fase4.py` | 44 | `provider_for_saved_anime()` y los 4 casos del orden de prioridad |
| `test_fase5.py` | 26 | el proveedor visible en las vistas y en la ficha |
| `test_buscador.py` | 49 | `filter_animes_by_title`, `match_animes_from_search`, `SavedAnimeSearch` |
| `test_fase6.py` | 105 | migración de identidad, aviso de duplicado, movimiento de pósters |
| `test_fase6_gui.py` | 26 | **CTk real** (`withdraw()`): los 4 estados del bloque de proveedor, su posición en el grid y el `wraplength` |

### Las cinco técnicas que hicieron falta

1. **Dobles de las dependencias que no se pueden ejercitar sin usuario.** `MessageBoxFalso` registra
   qué diálogo se abriría y devuelve la respuesta programada; `HiloFalso` ejecuta el `target` en el
   acto, así que un flujo con hilo + `after()` se prueba de forma **síncrona y determinista**.
2. **CTk real, pero con la ventana oculta.** `root.withdraw()` + `get_anime_image` parcheada permite
   comprobar el layout de verdad —a qué `row`/`column` fue cada widget— sin abrir una ventana.
   ⚠️ En una ventana oculta `winfo_width()` no vale: hay que **capturar el ancho en el momento de
   pintar**, no leerlo después.
3. **`check(nombre, condición, detalle)` en vez de `assert`.** Una comprobación rota no puede ocultar
   las 40 siguientes. ⚠️ Y el `print` del detalle debe pasar por
   `.encode("ascii", "replace").decode("ascii")`: la consola de Windows es **cp1252** y no puede
   imprimir `⚠`, así que un fallo con ese carácter revienta el propio informe y **enmascara el fallo
   real**. Pasó de verdad.
4. **Guardas que comprueban la premisa, no solo el resultado.** Una comprobación de «el póster se ha
   renombrado» sobre un anime que no está en ninguna categoría **pasa siempre**, porque no hay nada
   que renombrar. Un `check` previo de «la fila de prueba está en alguna categoría» es lo que destapó
   dos comprobaciones vacías.
5. **Demostrar el bug antes de arreglarlo.** La sección 6b de `test_fase6.py` construye el viewer
   **como estaba** y comprueba que un solo clic crea la fila duplicada. Sin eso, «lo arreglé» es una
   afirmación sin respaldo.

> ⚠️ **Estos scripts no están en el repo y no son una suite.** No hay `TESTS/` del proyecto y esto no
> lo cambia: son verificaciones de una sesión. Si el siguiente cambio los necesita, se reescriben.

---

## 3d. Verificar un proveedor nuevo contra el sitio real *(2026-08-06)*

Un proveedor no toca la BD, así que aquí **sí se ejecuta contra la red**. Sé educado: peticiones en
serie y `time.sleep(1.5)` entre ellas ([README §4](README.md)).

El patrón que se usó para JKAnime — un `check(nombre, condición, detalle)` que cuenta aciertos y
acumula fallos, en vez de `assert`, para que una comprobación rota no oculte las 40 siguientes:

```python
import sys, time
sys.path.insert(0, r"D:\Proyectos Python\BibliotecaAnime\src")
from APIs.common.models import AnimeGenreFilter, AnimeInfo, AnimeOrderFilter
from APIs.jkanime.jkanime import JKAnimeSingleton

ok, fallos = 0, []
def check(nombre, condicion, detalle=""):
    global ok
    if condicion: ok += 1;            print(f"  OK   {nombre} {detalle}")
    else:         fallos.append(nombre); print(f"  FALLO {nombre} {detalle}")

p = JKAnimeSingleton()
check("no quedan metodos abstractos", not getattr(type(p), "__abstractmethods__", None))
info = p.get_anime_info("hunter-x-hunter-2011")
check("episodios", len(info.episodes or []) == 148, f"({len(info.episodes or [])})")
```

**Qué comprobar siempre**, más allá de «devuelve algo»:

| Comprobación | Por qué |
|---|---|
| Los 40 `AnimeGenreFilter` traducen a un slug **que existe en el sitio** | Una traducción inventada devuelve listas vacías en silencio |
| `AnimeInfo.id` es un slug, **sin `/` ni `http`** | Si se cuela una URL entera, se duplican filas en la biblioteca |
| El póster es el del **anime**, no una miniatura de episodio | Ver trampa 23 |
| **Orden** de `episodes` y numeración 1…N | Afecta al corte `[:25]` y a lo que se guarda en BD |
| Página 2 ≠ página 1 (comparando ids, no longitudes) | Un paginador roto suele devolver la misma página |
| Anime y episodio **inexistentes** → `None` / `[]` | El manager trata la excepción como «probar el siguiente» |
| Los ids reservados (`directorio`, `buscar`, `top`…) no aparecen como animes | Los sitios enlazan sus propias secciones desde las rejillas |

⚠️ **Cuidado con las aserciones de orden alfabético.** Los sitios ordenan con la colación de su base
de datos, no con la de Python: exigir `titulos == sorted(titulos, key=str.lower)` dio un **falso
fallo** con JKAnime porque coloca la puntuación inicial en otro sitio. Comprobar la propiedad que
importa (que sea ascendente), no la igualdad exacta.

✅ **Resultados del 2026-08-06** (`scratchpad/jkanime/`): **50/50** en `verificar_proveedor.py`
(contrato, géneros, los 5 métodos y casos límite) y **12/12** en `verificar_registro.py` (registro
de los 3 proveedores, orden del fallback, `set_default` y datos reales a través del manager).

Encontró un fallo real: `filtro=nombre` ordenaba de la Z a la A por faltarle `orden=asc`.

---

## 4. Probar el fallback de proveedores (sin red)

Proveedores falsos: uno que explota, uno que devuelve vacío y uno que devuelve datos.

```python
import sys
sys.path.insert(0, r"D:\Proyectos Python\BibliotecaAnime\src")
from APIs.common.animeProviderMgr import AnimeProvider, AnimeProviderManager
from APIs.common.models import AnimeInfo

class FakeBase(AnimeProvider):
    # OJO: __init_subclass__ los exige INCLUSO en una base intermedia
    PROVIDER_ID = "fake-base"; PROVIDER_NAME = "FakeBase"; BASE_URL = "http://fake.invalid"
    def search_animes_by_genres_and_order(self, g, o=None, p=None): return self._r("genres")
    def search_animes_by_query(self, q=None, p=None): return self._r("query")
    def get_anime_episode_servers(self, a, e): return self._r("servers")
    def get_recent_animes(self): return self._r("recent")
    def get_anime_info(self, a): return self._r("info")
    def is_available(self, timeout=5.0): return True

class Boom(FakeBase):
    PROVIDER_ID = "boom"; PROVIDER_NAME = "Boom"; BASE_URL = "http://boom.invalid"
    def _r(self, what): raise RuntimeError(f"explota en {what}")

class Empty(FakeBase):
    PROVIDER_ID = "empty"; PROVIDER_NAME = "Empty"; BASE_URL = "http://empty.invalid"
    def _r(self, what):
        return ([], 7) if what in ("query", "genres") else (None if what == "info" else [])

class Good(FakeBase):
    PROVIDER_ID = "good"; PROVIDER_NAME = "Good"; BASE_URL = "http://good.invalid"
    def _r(self, what):
        a = AnimeInfo(id="x", title="X", poster="p")
        if what in ("query", "genres"): return ([a], 3)
        if what == "info": return a
        return [a]

m = AnimeProviderManager()
m.register(Boom(), default=True); m.register(Empty()); m.register(Good())
print(m.call_with_fallback("get_recent_animes"))          # → ([AnimeInfo…], 'good')
print(m.get_recent_animes(strict=True))                   # → []
print(m.search_animes_by_query("q", 1, strict=True))      # → ([], 1)
print(m.get_anime_info("x", strict=True))                 # → None
print(m.get_recent_animes(provider_id="no-existe", strict=True))  # → [] (usa el 1º registrado)
```

✅ Todos los casos verificados. Semántica completa en [05 §5](05-proveedores-y-scraping.md).

---

## 5. Probar la caché de pósters

```python
import os, sys, time
from PIL import Image
REPO = r"D:\Proyectos Python\BibliotecaAnime"
SANDBOX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sandbox")
sys.path.insert(0, os.path.join(REPO, "src"))
import utils.utils as u
u.get_resource_path = lambda rel: os.path.normpath(os.path.join(SANDBOX, rel))
from APIs.common.models import AnimeInfo

d = os.path.join(SANDBOX, "resources", "images", "recent_animes")
animes = [AnimeInfo(id="one-piece", title="One Piece", poster="https://cdn.animeav1.com/covers/197.jpg"),
          AnimeInfo(id="naruto",    title="Naruto",    poster="https://cdn.animeav1.com/covers/190.jpg")]

t = time.time(); u.download_animes_poster(d, animes); print(f"1ª descarga: {time.time()-t:.1f}s")
for f in sorted(os.listdir(d)):
    print(f, os.path.getsize(os.path.join(d, f)), Image.open(os.path.join(d, f)).size)

t = time.time(); u.download_animes_poster(d, animes); print(f"2ª (cacheado): {time.time()-t:.2f}s")
u.download_animes_poster(d, animes[:1]); print("tras purga:", sorted(os.listdir(d)))
```

✅ **Resultados**:

| Comprobación | Resultado |
|---|---|
| Tamaño en disco | **130×185 JPEG** exacto |
| Segunda llamada (ya cacheado) | **0,00 s**, `mtime` intacto |
| Llamada con lista reducida | el póster sobrante **se borra** |
| `get_anime_image` con el póster solo en `watching/` | ✅ **0,01 s desde disco**, `(195, 275)` — desde `83a8448`. Antes iba a la red (0,12 s) y devolvía **20×20** |
| `get_anime_image` con el póster en `favourite/` | 0,009 s, `(195, 275)` ✅ |
| `load_image` con ruta inexistente | placeholder gris `(130, 185)` |
| `os.remove` con un `CTkImage` vivo | **`PermissionError`** hasta `del` + `gc.collect()` |

---

## 6. Prueba de humo con GUI

```powershell
cd "D:\Proyectos Python\BibliotecaAnime"
biblio_anime_env\Scripts\python.exe -u src/app.py *> <scratchpad>\gui_smoke.log
# en otra consola, tras ~20 s:
Get-Process python | Select-Object Id, MainWindowTitle
Stop-Process -Id <id>
```

✅ **Verificado el 2026-07-28**: la ventana abre con título «Mi Biblioteca de Anime» —hoy «Mi
Biblioteca»—, el arranque
completa, no hay traceback, y **`DB_Animes.db` no cambia de `LastWriteTime`** (el arranque solo lee).

⚠️ **Lo que NO se verificó con GUI** — requiere interacción manual y no se hizo:

- Clic en un anime y apertura de la ficha.
- Marcar/desmarcar episodios en pantalla.
- Los 4 botones de estado.
- Buscador, filtros de género, paginación.
- Cambio de tema claro/oscuro.

Todo lo de esa lista está marcado como 📖 en el resto de documentos.

---

## 7. Checklist de regresión manual por vista

Sin tests automáticos, esto es lo que hay. Marca lo que compruebes.

> ✅ **Reescrito el 2026-08-21** tras el rediseño de interfaz (fases 1-9). Lo que decía antes de
> «Abrir filtro de animes», de los botones que cambian de texto o del GIF de búsqueda ya no existe.

### 7.0 Las cuatro dimensiones

El recorrido completo es **7 vistas × 2 temas × 2 estados de barra**. No es tanto como parece: el
tema y el plegado no cambian de vista, así que se hacen dos pasadas de siete.

| Dimensión | Valores |
|---|---|
| Vistas | Nuevos lanzamientos · Favoritos · Viendo · Pendientes · Finalizados · Buscar · Ficha |
| Tema | `Light` · `Dark` · y **`System`**, que es el valor de fábrica |
| Barra | desplegada (224 px) · plegada (84 px) |
| Biblioteca | con datos · **vacía** (los estados vacíos solo se ven así) |

### 7.1 Arranque
- [ ] GIF + barra avanzan 0→40→90→100 %.
- [ ] La barra lateral aparece **solo** al terminar la carga.
- [ ] 🆕 **El fondo del arranque es uno solo, y el mismo que el de la portada.** Ni recuadro gris
      alrededor del GIF, ni banda vertical a la izquierda. Es la
      [trampa 36](10-invariantes-y-trampas.md), y **a ojo se falla**: capturar la ventana y muestrear
      píxeles. Todo punto de fondo debe dar `#14161A` en oscuro y `#F4F5F7` en claro.
- [ ] 🆕 **La pantalla de carga desaparece**. Si se queda, es la [trampa 33](10-invariantes-y-trampas.md).
- [ ] 🔴 **Sin conexión**: sale el aviso, **la pantalla de carga se retira igual** y la portada
      muestra su estado vacío con «Reintentar». Es el caso que nadie prueba y el que estuvo roto.
- [ ] 🆕 La barra recuerda si la dejaste plegada (`sidebar_collapsed` en `DB_user.db`).

### 7.2 Barra lateral
- [ ] Los seis destinos en este orden: Nuevos lanzamientos · Favoritos · Viendo · Pendientes ·
      Finalizados · Buscar. **Ninguno lleva la palabra «Anime»**.
- [ ] El activo tiene fondo `CARD` y la barrita de 2 px en `ACCENT` a la izquierda.
- [ ] 🔴 **Los seis se ven**. Si salen en blanco, es la [trampa 29](10-invariantes-y-trampas.md).
- [ ] Los contadores cuadran con lo que hay en cada pestaña.
- [ ] 🆕 Marcar un estado desde la ficha **mueve el contador en el acto**
      ([trampa 31](10-invariantes-y-trampas.md)).
- [ ] Plegar (««»): la barra baja a 84 px, quedan los iconos a 48 × 48 y el contador pasa a globo
      arriba a la derecha. El pie pierde las etiquetas y el desplegable de apariencia.
- [ ] Desplegar la devuelve exactamente a como estaba.
- [ ] El **pin** sale azul si el proveedor que usas es tu predeterminado, gris si te has desviado.

### 7.3 Nuevos lanzamientos
- [ ] Rejilla de **6 columnas**, pósters de 176 × 264 con esquinas redondeadas.
- [ ] Paginador de **12** al pie: «Mostrando 1-12 de 20».
- [ ] Banda «Retomar donde lo dejaste» arriba con hasta **3** tarjetas, cada una con «Siguiente:
      episodio N de M» y su barra de progreso.
- [ ] 🆕 **La banda no se pinta si no hay nada que retomar**: ni etiqueta ni hueco.
- [ ] Clic en una tarjeta de «Retomar» abre la ficha **del anime guardado**, no la de un homónimo.
- [ ] Clic en la rejilla → cursor «watch» → ficha.

### 7.4 Favoritos
- [ ] Rejilla de **5 columnas**, pósters de 216 × 324 — los más grandes de la aplicación.
- [ ] Paginador de **10**.
- [ ] Cinco estrellas bajo cada título, con **medios puntos**, y la cifra a su derecha.
- [ ] Pulsar la mitad izquierda de la tercera estrella pone 2,5; la derecha, 3,0.
- [ ] 🔴 **Calificar NO reordena la rejilla**: el anime se queda donde estaba aunque el orden sea por
      calificación. Si se recolocara, la segunda estrella caería sobre otro anime.
- [ ] Volver a pulsar la misma calificación la **quita** (vuelve a «sin calificar», que no es cero).
- [ ] El desplegable ofrece «Mi calificación» y «Título (A-Z)», y **la elección sobrevive al
      reinicio** (`favourites_order`).
- [ ] Ordenando por calificación, **lo no calificado va al final**, nunca primero.
- [ ] 🆕 El sello sobre el póster dice qué **más** es el anime (Viendo / Pendiente / Finalizado), y
      **nunca «Favorito»**: sería el dato repetido que prohíbe el diseño.
- [ ] 🔴 **El sello se lee sobre una carátula blanca** (prueba con *Dragon Ball Daima*), en los dos
      temas. Fondo oscuro opaco, texto blanco, color del estado solo en el glifo.

### 7.5 Viendo
- [ ] Cascada de una fila por anime, póster de 70 × 100, fila de 132 px.
- [ ] **Sin paginador**: caben de una vez.
- [ ] Panel de 290 px a la derecha con «Lo último que veías» y su botón.
- [ ] 🆕 El panel recorre los **tres** identificadores guardados: si el más reciente ya no está en
      esta pestaña, enseña el siguiente.
- [ ] Barra de progreso y «N / M vistos» en cada fila.
- [ ] **Hover**: la fila se resalta con `CARD_HOVER` y aparece la píldora «Episodio N →».
- [ ] 🔴 **La píldora no se apaga al ir a pulsarla**, y la fila **no cambia de ancho**
      ([trampa 34](10-invariantes-y-trampas.md)).
- [ ] El proveedor de cada fila aparece a la derecha.

### 7.6 Pendientes
- [ ] Cascada con póster de 56 × 80, fila de 113 px, **sin barra de progreso**.
- [ ] A la derecha, «N episodios · Proveedor».
- [ ] Desplegable de orden: **Más cortos primero** (por defecto) · Más largos primero · Título (A-Z).
- [ ] 🔴 **Lo que no tiene lista de episodios va al final en los dos sentidos**: «no se sabe cuánto
      dura» no es «dura poco».
- [ ] ⚠️ El orden **no** se persiste: al volver a entrar vuelve a «Más cortos primero».
- [ ] **Hover** → píldora «Empezar»; pulsarla mueve el anime a «Viendo», **mueve los contadores de la
      barra** y abre su ficha.

### 7.7 Finalizados
- [ ] Rejilla de **6**, paginador de **12**.
- [ ] Sello «✓ N / M» sobre cada póster, arriba a la izquierda.
- [ ] 🆕 Un finalizado **sin lista de episodios** dice «Finalizado», **no «0 / 0»**.
- [ ] Los números son los **reales y sin corregir**: un «3 / 12» significa que lo marcaste a mano.

### 7.8 Buscar
- [ ] **No tiene título de vista**: el campo de 620 px con la lupa dentro *es* la cabecera.
- [ ] Fila de fichas de género: 7 visibles + «Más géneros (33)».
- [ ] Las fichas dicen **«Acción» y «Ciencia ficción», con tildes** (salen de `.name`, no de `.value`).
- [ ] Tocar una ficha busca **en el acto**, sin botón de aplicar; la seleccionada pasa **primera**,
      con `ACCENT_SOFT`, borde `ACCENT` y una ✕.
- [ ] 🔴 **Texto y géneros no se combinan: manda el último gesto.** Buscar por texto apaga las fichas;
      tocar una ficha vacía el texto.
- [ ] Mientras busca, la línea de estado dice «Buscando animes…» y la rejilla se vacía. **No hay GIF.**
- [ ] La línea de resultados dice **quién respondió de verdad**: con una consulta que AnimeAV1 no
      tenga, debe salir «… en JKAnime» (el fallback), no el proveedor del desplegable.
- [ ] Sello «ya lo tienes» sobre los resultados guardados, **también cuando el slug no coincide** y
      el cruce es por título.
- [ ] 🔴 Abrir un resultado sellado y marcarle un estado **no crea una fila duplicada**
      ([trampa 21](10-invariantes-y-trampas.md)).
- [ ] Paginador: con un género («Acción») debe salir «Página 1 de 50» y los botones deben traer
      resultados distintos.
- [ ] Salir y volver: se restaura la última búsqueda sin repetir la petición.

### 7.9 Ficha del anime
- [ ] Póster de 248 × 372 redondeado, título a 30, sinopsis y fichas de género **con su contorno**.
- [ ] Sinopsis de AnimeAV1 **con tildes correctas** («título», no «tÃ­tulo»).
- [ ] 🆕 Los **4 botones de estado se encienden y se apagan**; ya no cambian de texto.
- [ ] Encender «Viendo» apaga «Finalizado» y «Pendiente» en la propia interfaz.
- [ ] Encendidos van con el color pastel de su estado; apagados, con borde `LINE`.
- [ ] 🆕 Las filas de episodio dicen **«Episodio N»**, sin repetir el título del anime.
- [ ] Aparecen **25** como máximo, y **la lista lo dice** cuando hay más.
- [ ] 🆕 El botón de orden dice **el orden que llega del proveedor**, no siempre «Mayor a menor».
- [ ] Marcar el episodio 10 marca del 1 al 10; desmarcar el 5 desmarca **solo** el 5.
- [ ] Clic en un episodio despliega los servidores debajo **sin empujar la lista**; volver a pulsar
      los repliega (⚠️ congela la ventana mientras carga: es la única llamada HTTP que sigue en el
      hilo de Tkinter, [07 C5](07-concurrencia-e-hilos.md)).
- [ ] Elegir un servidor abre el navegador.
- [ ] Con la red caída, el clic muestra un **diálogo de error** y no deja la app muda.
- [ ] **Identidad partida**: con JKAnime seleccionado, abrir un anime guardado desde AnimeAV1 debe
      sacar «⚠ En tu biblioteca: AnimeAV1» en ámbar y el botón «Actualizar a JKAnime».
- [ ] Migrar **conserva los episodios vistos y las cuatro categorías**, y **no duplica**.
- [ ] 🔴 **Salir de la ficha y entrar en otra vista**: la vista siguiente ocupa el ancho completo. Si
      sale apretada a la izquierda, es la [trampa 32](10-invariantes-y-trampas.md).

### 7.10 Estados vacíos 🆕

Solo se ven con la biblioteca vacía o sin red. La receta para provocarlos sin tocar tus datos está en
[§3](#3-probar-la-persistencia--sobre-una-copia): repuntar las dos persistencias a ficheros nuevos
del scratchpad **antes** de construir `MainWindow`.

- [ ] Las **6** vistas tienen icono, frase y un botón que lleva a alguna parte.
- [ ] 🔴 **La portada no dice «no tienes nada»**: dice «No se han podido cargar los estrenos» y
      ofrece «Reintentar». El catálogo no es del usuario.
- [ ] «Buscar» **no ofrece «prueba con otro proveedor»**: el gestor ya los ha probado todos. Ofrece
      borrar la búsqueda o quitar los filtros.
- [ ] Los botones navegan de verdad y **la barra lateral marca el destino** al llegar.

### 7.11 Tema y plegado
- [ ] `Light`, `Dark` y `System` cambian el aspecto **sin reiniciar** y sin dejar textos negros sobre
      negro.
- [ ] 🆕 El texto de la barra lateral nace correcto en los dos temas: los colores son tuplas
      `(claro, oscuro)` y los resuelve CustomTkinter. *(La deuda que había aquí murió con la fase 1.)*
- [ ] Texto sobre `ACCENT` legible en los dos temas (`ACCENT_INK`: blanco en claro, casi negro en
      oscuro).
- [ ] Con la barra **plegada**, las 7 vistas se ensanchan a 1 356 px y **nada se sale ni se recorta**.
- [ ] La sinopsis de la ficha **no** se ensancha al plegar: tiene tope de 74 caracteres a propósito.

### 7.12 Regresión global
- [ ] `SELECT COUNT(*) FROM ANIMES` antes y después de toda la sesión → el mismo número, salvo lo que
      hayas añadido a propósito.
- [ ] `SELECT COUNT(*) FROM ANIMES WHERE provider_id IS NULL` → cuenta que **solo baja**, nunca sube.
- [ ] 🆕 `sha256` de `DB_Animes.db` idéntico si la sesión era de solo mirar.
- [ ] `git grep -nE "#[0-9A-Fa-f]{6}" -- src/` devuelve **solo** `src/gui/theme.py`.


## 8. Limpieza

Al terminar cualquier verificación:

```powershell
git status    # debe mostrar SOLO lo que tenías antes de empezar
```

- Ningún script de prueba dentro del repo.
- `resources/DB/DB_Animes.db` con el `LastWriteTime` original.
- ⚠️ Si has ejecutado la app, `resources/images/recent_animes/` **habrá cambiado** (se re-cachean
  pósters). Está en `.gitignore`, así que no ensucia `git status`.
- ⚠️ Si has ejecutado la app, `resources/DB/DB_user.db` **existirá** (se crea en el primer arranque).
  Es desechable y está en `.gitignore`. Para volver al estado prístino basta con borrar sus filas:
  `DELETE FROM USER_SETTINGS`.
- ⚠️ Si has lanzado la app desde un script en segundo plano, **comprueba que no queda ningún proceso
  vivo**: `Get-Process python`. La app no termina sola y una instancia huérfana sigue sirviendo la
  ventana y bloqueando la BD.

### Capturar la ventana de la app sin robar el foco

Útil para verificar layout (es la única forma de detectar la trampa 22, que no lanza ningún error):

```powershell
# El objeto de Start-Process no publica MainWindowHandle con Tk: buscar por titulo.
$win = Get-Process | Where-Object { $_.MainWindowTitle -eq "Mi Biblioteca" }
# Capturar con PrintWindow(h, hdc, 2) -> PW_RENDERFULLCONTENT: funciona aunque
# la ventana este tapada y NO la trae al frente.
```

⚠️ **No** hagas una captura de pantalla completa para esto: recoge todo lo que el usuario tenga abierto.
