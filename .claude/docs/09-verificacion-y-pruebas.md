# 09 — Verificación y pruebas

| | |
|---|---|
| **Fecha** | 2026-08-16 · **Commit** `a3d4331` (2026-08-17, rama `main`) · árbol **limpio** |
| **Última revisión** | 2026-08-16 (**columna `provider_id`**): **§3c nuevo** — las 8 tandas de comprobaciones de la fase 8, **351 sin fallos**; checklist de §7 puesto al día con lo que ha cambiado de comportamiento |
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
«Mi Biblioteca de Anime». Único mensaje en consola:

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

✅ **Verificado el 2026-07-28**: la ventana abre con título «Mi Biblioteca de Anime», el arranque
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

### Arranque
- [ ] GIF + barra avanzan 0→40→90→100 %.
- [ ] La sidebar aparece **solo** al terminar la carga.
- [ ] Sin conexión: sale el `messagebox` de aviso y la vista de recientes vacía.

### Animes recientes
- [ ] Rejilla con ~20 pósters, título bajo cada uno.
- [ ] Clic → cursor «watch» → ficha (instantánea si ya estaba precargada).
- [ ] Redimensionar la ventana y volver a entrar: cambia el número de columnas.

### Favoritos / Finalizados / Viendo / Pendientes
- [ ] Muestra los animes con ese flag.
- [ ] ⚠️ Los pósters se leen de `resources/images/<categoría>/`; si faltan, salen **grises**.
- [ ] «Abrir filtro de animes» despliega los 40 géneros y los 3 órdenes.
- [ ] «Aplicar Filtros» filtra por género (⚠️ el **orden** no se aplica — trampa 6).
- [ ] 🆕 El buscador encuentra **con el cable desenchufado**: es local. Escribir «one piece»
      devuelve One Piece **con cualquiera de los tres proveedores seleccionado** (trampa 26).
- [ ] 🆕 Con conexión, buscar «Solo Leveling» devuelve también «Ore dake Level Up na Ken» si lo
      tienes guardado: eso solo lo aporta la búsqueda web, y **se suma**, nunca quita.
- [ ] 🆕 Clic en un anime **NO congela la ventana**: cursor «watch» y la UI sigue respondiendo.
- [ ] 🆕 Bajo el título de cada anime aparece **el proveedor** en gris; vacío si la fila no lo
      declara (no debe poner «desconocido»).

### Buscador
- [ ] Búsqueda por texto → GIF → rejilla + paginación.
- [ ] Filtro por géneros + orden → resultados.
- [ ] «Siguiente »» / «1» / última página navegan.
- [ ] Salir del buscador y volver: se restaura la última búsqueda (`last_search_instance`).
- [ ] ⚠️ Pulsar «Buscar» dos veces rápido lanza dos búsquedas (trampa/carrera C4).

### Ficha de detalle
- [ ] Póster, título, sinopsis y géneros.
- [ ] El póster se ve a tamaño correcto también en un anime que **solo** esté en «viendo»
      (regresión de las trampas 15 y 16, resueltas en `83a8448`).
- [ ] Sinopsis de AnimeAV1 **con tildes correctas** («título», no «tÃ­tulo») — regresión de la
      trampa 14, resuelta en `94b497e`. Ver [05 §7](05-proveedores-y-scraping.md).
- [ ] Con la red caída, hacer clic en un anime muestra un **diálogo de error** y no deja la app
      muda — regresión de la trampa 10, resuelta en `1bfdf0f`.
- [ ] Los 4 botones cambian de texto y de acción al pulsarlos.
- [ ] Activar «viendo» desactiva «finalizado» y «pendiente» en la propia UI.
- [ ] Aparecen **25** episodios como máximo.
- [ ] Botón de orden alterna «Mayor a menor ↓» / «Menor a mayor ↑».
- [ ] Buscar un número de episodio muestra ese episodio + navegación anterior/siguiente.
- [ ] Marcar el episodio 10 marca del 1 al 10; desmarcar el 5 desmarca **solo** el 5.
- [ ] Salir de la ficha y volver: el estado de los switches se restaura desde BD.
- [ ] Clic en un episodio despliega los servidores (⚠️ congela la ventana mientras carga: es la
      única llamada HTTP que sigue en el hilo de Tkinter, [07 C5](07-concurrencia-e-hilos.md)).
- [ ] Elegir un servidor abre el navegador.

### Tema
- [ ] Light / Dark / System cambian el aspecto.
- [ ] ⚠️ Arrancando en modo oscuro, el texto de la sidebar nace **negro** hasta que se cambia a mano
      (deuda observada en `utilsButtons.py:69`; **no** es un TODO del código — ver [06 §5](06-gui-y-vistas.md)).

### Proveedor JKAnime *(2026-08-06)*

- [ ] El desplegable de la sidebar ofrece **tres** proveedores: AnimeAV1, JKAnime y AnimeFLV.
- [ ] Al elegir **JKAnime**, la portada se recarga con sus animes recientes y **los pósters son
      carátulas, no fotogramas de episodio** (trampa 23).
- [ ] Abrir una ficha desde ahí: sinopsis, géneros y lista de episodios rellenos, y la etiqueta
      «Proveedor» de la ficha dice **JKAnime**.
- [ ] En esa ficha, un episodio ofrece servidores de vídeo con **nombres reales** (Desu, Magi…),
      no «Opción 1».
- [ ] Buscar algo desde la lupa con JKAnime activo: salen resultados y **no aparece paginación**
      más allá de la primera página.

### Selector de proveedor y pin *(2026-07-30, reformado el 2026-08-06, [13](13-selector-de-proveedor.md))*

**Sidebar — desplegable**
- [ ] Arranque con `DB_user.db` borrada: se crea, el desplegable muestra **AnimeAV1** y el pin nace
      **gris**. El log debe decir «Sin proveedor fijado, se usa animeav1».
- [ ] Cambiar de proveedor → la portada de recientes se repuebla y se navega a esa vista.
- [ ] 🔴 **La prueba que da sentido a la reforma**: cambiar de proveedor **sin** tocar el pin, cerrar y
      reabrir → la app arranca con el proveedor **anterior**, no con el que se probó, y
      `SELECT * FROM USER_SETTINGS` no ha cambiado.

**Sidebar — pin**
- [ ] Con el desplegable desviado, el pin está **gris**; al pulsarlo se pone **azul** y la fila de
      `USER_SETTINGS` pasa a ese proveedor. Cerrar y reabrir → arranca con él.
- [ ] Pulsar el pin estando **azul** → se pone gris, `setting_value` queda a `NULL` y **el proveedor
      en uso no cambia**. Cerrar y reabrir → arranca con AnimeAV1 (el del registro).
- [ ] Cambiar el desplegable estando el pin azul → el pin pasa a gris **sin** escribir en BD.
- [ ] Con `DB_user.db` no disponible, pulsar el pin avisa con `messagebox` y **no** se pone azul.
- [ ] El bloque desplegable + pin no se solapa con el selector de apariencia (la fila 8 del sidebar es
      el espaciador con `weight=1`) — compruébalo con una **captura**, que el layout no avisa por
      consola.
- [ ] En tema claro y en oscuro el pin se ve (usa `light_image`/`dark_image`, no `update_icon()`).

**Ficha de detalle**
- [ ] Abrir una ficha desde **cada una** de las 6 vistas: la etiqueta «Proveedor: X» dice quién sirvió
      los datos. ⚠️ Ya **no** hay desplegable en la ficha.
- [ ] La sinopsis **no** queda recortada por la derecha (trampa 22).
- [ ] Desplegar servidores → son los del proveedor de la etiqueta (compruébalo por el dominio de la
      URL); si ese proveedor no ofrece ninguno, sale un aviso y no un selector vacío.
- [ ] `SELECT COUNT(*) FROM ANIMES` antes y después de toda la sesión → **el mismo número**.

> 🗑️ Se han retirado las pruebas de «cambiar de proveedor dentro de la ficha»: ese control ya no
> existe. La **trampa 21** sigue viva, y desde el 2026-08-16 **vuelve a poder dispararse a mano** —
> ver el bloque siguiente.

### Columna `provider_id` *(2026-08-16, [13 §14](13-selector-de-proveedor.md))*

**Abrir un anime guardado**
- [ ] Con **AnimeAV1** seleccionado (la referencia), abrir un anime guardado desde AnimeFLV: el bloque
      dice `Proveedor: AnimeFLV` / `En tu biblioteca: AnimeFLV`, **en gris y sin ⚠**.
- [ ] Con **JKAnime** seleccionado, el mismo anime: `Proveedor: JKAnime` /
      `⚠ En tu biblioteca: AnimeFLV`, **en ámbar**. Los datos vienen de JKAnime.
- [ ] 🔴 En ese estado, pulsar un botón de estado **no crea una fila nueva**:
      `SELECT COUNT(*) FROM ANIMES` no cambia. Es la [trampa 21](10-invariantes-y-trampas.md), que
      llegó a reintroducirse una vez.
- [ ] Un anime guardado **antes** de existir la columna: al abrirlo por primera vez, su `provider_id`
      pasa de `NULL` al proveedor que lo sirvió. Al reabrirlo, **no vuelve a escribirse**.

**Migrar a otro proveedor**
- [ ] El botón «Actualizar a X» aparece siempre que el proveedor seleccionado difiera del de la fila
      — **no solo** cuando hay discrepancia. (Fue el fallo reportado por el usuario.)
- [ ] Confirmar la migración: el diálogo enumera proveedor, identificador y título, y dice **cuántos
      episodios vistos se conservan**.
- [ ] Tras migrar: `anime_id` y `provider_id` cambiados, **`watched_episodes` idéntico**, los cuatro
      estados intactos, y el póster sigue viéndose (renombrado, no re-descargado).
- [ ] Si el `anime_id` destino ya lo ocupa otra fila → **aviso y no se toca nada**.
- [ ] Si el proveedor destino no tiene el anime → `showinfo` y el anime sigue guardado igual.

**Aviso de duplicado**
- [ ] Abrir un anime desde un proveedor distinto al que lo guardó y pulsar «Añadir a favoritos»: sale
      el aviso nombrando **«tu Biblioteca de Favoritos»** (la sección pulsada), dónde está el
      duplicado y desde qué proveedor.
- [ ] Aceptar crea de verdad la segunda fila; cancelar **no escribe nada**.

**Regresión global**
- [ ] `SELECT COUNT(*) FROM ANIMES` antes y después de toda la sesión → el mismo número, salvo lo que
      hayas añadido a propósito.
- [ ] `SELECT COUNT(*) FROM ANIMES WHERE provider_id IS NULL` → cuenta que **solo baja**, nunca sube.

---

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
$win = Get-Process | Where-Object { $_.MainWindowTitle -eq "Mi Biblioteca de Anime" }
# Capturar con PrintWindow(h, hdc, 2) -> PW_RENDERFULLCONTENT: funciona aunque
# la ventana este tapada y NO la trae al frente.
```

⚠️ **No** hagas una captura de pantalla completa para esto: recoge todo lo que el usuario tenga abierto.
