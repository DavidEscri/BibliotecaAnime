# 09 — Verificación y pruebas

| | |
|---|---|
| **Fecha** | 2026-07-30 · **Commit** `83a8448` · árbol **sucio** |
| **Última revisión** | 2026-07-30: resultados de `get_anime_image` y checklist de la ficha, tras `83a8448` y `94b497e` |
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
- [ ] El buscador va **contra la red**, no contra la BD: sin conexión no encuentra nada.
- [ ] Clic en un anime **congela la ventana** durante la petición (es el comportamiento actual).

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
- [ ] Clic en un episodio despliega los servidores (⚠️ congela la ventana mientras carga).
- [ ] Elegir un servidor abre el navegador.

### Tema
- [ ] Light / Dark / System cambian el aspecto.
- [ ] ⚠️ Arrancando en modo oscuro, el texto de la sidebar nace **negro** hasta que se cambia a mano
      (TODO en `utilsButtons.py:56`).

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

> 🗑️ Se han retirado las pruebas de «cambiar de proveedor dentro de la ficha» (duplicado de filas,
> reversión del desplegable al fallar, servidores tras el cambio): ese control ya no existe. La
> **trampa 21** sigue viva —el fallback puede servir la ficha desde otro proveedor—, pero desde la
> GUI ya no se puede disparar a mano; volverá a poder probarse con la columna `provider_id`
> ([13 §8](13-selector-de-proveedor.md)).

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
