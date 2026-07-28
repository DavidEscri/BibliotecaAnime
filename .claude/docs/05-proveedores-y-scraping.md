# 05 — Proveedores y scraping

| | |
|---|---|
| **Fecha** | 2026-07-28 · **Commit** `a972850` · árbol **sucio** |
| **Cubre** | `src/APIs/common/animeProviderMgr.py`, `src/APIs/common/models.py`, `src/APIs/animeav1/animeav1.py`, `src/APIs/animeflv/animeflv.py` |

Procedencia: ✅ verificado en ejecución contra los sitios reales el 2026-07-28 · 📖 leído en código ·
⚠️ sin verificar.

---

## 1. El contrato `AnimeProvider`

📖 `animeProviderMgr.py:21-107`.

```python
class MiProveedor(AnimeProvider):
    PROVIDER_ID   = "misitio"          # clave del registro, corta y estable
    PROVIDER_NAME = "MiSitio"          # nombre legible para la UI
    BASE_URL      = "https://misitio.com"

    def search_animes_by_genres_and_order(self, genres: List[AnimeGenreFilter],
                                          order: str = None,
                                          page: int = None) -> Tuple[List[AnimeInfo], int]: ...
    def search_animes_by_query(self, query: str = None,
                               page: int = None) -> Tuple[List[AnimeInfo], int]: ...
    def get_anime_episode_servers(self, anime_id, episode_id: int) -> List[ServerInfo]: ...
    def get_recent_animes(self) -> List[AnimeInfo]: ...
    def get_anime_info(self, anime_id) -> AnimeInfo | None: ...
```

**Cinco métodos abstractos**, ni uno más. `is_available(timeout=5.0)` (`:92-104`) tiene
implementación por defecto (un `GET BASE_URL`) y es opcional sobrescribirla.

### Validación en `__init_subclass__`

✅ Verificado. `:54-64`. Si falta cualquiera de los 3 atributos de clase, salta
`NotImplementedError` **en el momento del import**, no al usar la clase:

```
NotImplementedError: Incompleto debe definir el atributo de clase 'PROVIDER_ID'
```

> ✅ **Trampa poco intuitiva**: la condición es `if ABC not in cls.__bases__` (`:59`). Solo
> `AnimeProvider` lista `ABC` entre sus bases directas. Por tanto **cualquier** subclase —incluida una
> clase base intermedia que quieras dejar abstracta— está obligada a definir los 3 atributos.
> No puedes hacer `class ProveedorHTMLBase(AnimeProvider): ...` sin darle valores de relleno.

### Reglas que toda implementación debe cumplir

1. 📖 Devolver **siempre** tipos de `APIs.common.models`, nunca tipos propios del sitio (`:27-30`).
2. 📖 Las búsquedas devuelven **`Tuple[List[AnimeInfo], int]`** = (resultados, última página).
3. 📖 Si el sitio usa slugs de género distintos a `AnimeGenreFilter`, **traducirlos dentro del
   proveedor** (`:31-35`). Quien llama siempre pasa el enum común.
4. ⚠️ *No escrito en el contrato, pero asumido por la GUI*: en los **listados**, `synopsis`, `genres`
   y `episodes` valen `None`; solo `get_anime_info` los rellena. La precarga de recientes
   (`main_window.py:235`) y `recentAnimes.py:86` dependen de ello.

---

## 2. Tabla comparativa

✅ Todo verificado el 2026-07-28.

| | **AnimeAV1** (por defecto) | **AnimeFLV** (fallback) |
|---|---|---|
| `PROVIDER_ID` | `animeav1` | `animeflv` |
| `BASE_URL` | `https://animeav1.com` | `https://www3.animeflv.net` |
| Tecnología del sitio | **SvelteKit** (payload de hidratación) | HTML clásico |
| Técnica de parseo | **regex sobre el payload JS** + DOM como fallback | selectores CSS |
| Formato de `anime_id` | slug: `one-piece` | slug: `one-piece-tv` |
| `get_recent_animes` | ✅ 20 resultados | ✅ 24 resultados |
| `get_anime_info` | ✅ 1171 eps, 4 géneros | ✅ 1167 eps, 7 géneros |
| **Orden de `episodes`** | ✅ **ascendente** 1…N (`:205`) | ✅ **descendente** N…1 (`:222-223`) |
| `search_animes_by_query("naruto")` | ✅ 19 res., `last_page=1` | ✅ 12 res., `last_page=1` |
| `search_..._by_genres_and_order` | ✅ 20 res., `last_page=50` | ✅ 24 res., `last_page=79` |
| `get_anime_episode_servers` | ✅ 5 servidores | ❌ **`[]`** |
| Orden `ALFABÉTICAMENTE` | cliente, `sorted(title.lower())` (`:328-329`) | servidor, `&order=title` |
| Orden `CALIFICACIÓN` | ⚠️ **no soportado**, avisa y devuelve el orden del sitio (`:330-335`) | servidor, `&order=rating` |
| Reintentos en `get_anime_info` | 3, timeout 5 s, `sleep(1)` (`:162-219`) | 3, timeout 2 s, `sleep(1)` (`:186-233`) |
| Estado general | **operativo** | **caído / en desuso** (confirmado por el usuario) |

> ✅ **Los géneros de ambos sitios ya coinciden con los slugs de `AnimeGenreFilter`**
> (`accion`, `aventura`, `fantasia`, `shounen`…). Hoy **ninguno de los dos necesita traducir**. Un
> proveedor nuevo sí podría necesitarlo.

---

## 3. AnimeAV1 — el payload de hidratación

📖 `animeav1.py:1-8` y `:34`. El sitio no sirve HTML navegable por selectores estables: SvelteKit
inyecta los datos como **objeto JS (no JSON estricto)** dentro de un `<script>` que contiene
`kit.start(app, element, {`.

### Cómo se extrae

```python
# animeav1.py:228-240
for script in soup.find_all("script"):
    content = script.string or script.get_text() or ""
    if "kit.start(app, element, {" in content:      # :34, :236
        match = re.search(r"data:(.+\]),", content, re.DOTALL)   # :237
        if match:
            return match.group(1)
return None
```

### Forma **real** del payload

✅ Muestra tomada de `GET https://animeav1.com/media/one-piece` (script de ~32 000 caracteres,
fragmento extraído de ~31 200):

```js
[null,
 {type:"data",data:{user:null},uses:{dependencies:["https://animeav1.com/media/auth"]}},
 {type:"data",data:{media:{
     id:197, categoryId:1, title:"One Piece", aka:{"ja-jp":"ONE PIECE"},
     genres:[{id:1,name:"Acción",type:0,slug:"accion",malId:1},
             {id:2,name:"Aventura",type:0,slug:"aventura",malId:2}, …],
     synopsis:"Apenas sobreviviendo en un barril…",
     poster:null, backdrop:null, trailer:"-tviZNY6CSw", status:2, runtime:null,
     startDate:"1999-10-20", nextDate:null, endDate:null, waitDays:7,
     featured:true, mature:false,
     episodesCount:1171, score:8.73, votes:1445355,
     slug:"one-piece", malId:21, seasons:null, createdAt:"2025-02-22 07:34:09…"
 }}}]
```

En la página de **episodio** (`/media/{slug}/{n}`) aparece además:

```js
embeds:{SUB:[{server:"HLS",url:"https://player.zilla-networks.com/play/76016…"},
             {server:"UPNShare",url:"https://animeav1.uns.bio/#3zq51b"},
             {server:"Mega",url:"https://mega.nz/embed/D3hnjLDb#…"},
             {server:"MP4Upload",url:"https://www.mp4upload.com/embed-78kpt…"},
             {server:"TeraBox",url:"https://terabox.com/sharing/embed?surl=…"}]},
downloads:{SUB…
```

### Qué campo sale de dónde

| Campo de `AnimeInfo` | Origen | Línea | Verificado |
|---|---|---|---|
| `title` | **payload** `re.search(r'title:\s*"(.+?)",')` | `:177,181-182` | ✅ `"One Piece"` |
| `synopsis` | **payload** `r'synopsis:\s*"(.*?)",'` + des-escape `\n` y `\"` | `:178,183-184` | ✅ |
| `episodes` | **payload** `r'episodesCount:\s*(\d+),'` → `[1..N]` | `:179,185-186,205` | ✅ 1171 |
| `poster` | **DOM** `main figure img` → `src` | `:197-198` | ✅ (en el payload es `poster:null`) |
| `genres` | **DOM** `main a[href*='genre=']` → `?genre=` | `:200`, `:292-309` | ✅ `['accion','aventura','fantasia','shounen']` |
| `id` | el `anime_id` que se pasó | `:208` | ✅ |
| servidores | **payload** `r"embeds:\s*.*?SUB:\s*(\[.*?\])"` | `:126` | ✅ 5 servidores |

> ⚠️ **Nota**: los géneros **están en el payload** (`genres:[{…,slug:"accion",…}]`) pero el código los
> saca del **DOM**. Si algún día el DOM cambia y el payload no, hay un origen alternativo ya
> disponible.

### Fallbacks al DOM

📖 `:188-203`. Si el payload no da un campo:

| Campo | Fallback | Línea |
|---|---|---|
| `title` | `main h1`; si tampoco, `str(anime_id)` | `:189-191` |
| `synopsis` | `main div.entry p` → `main article p`; si no, `None` | `:193-195` |
| `episodesCount` | `__count_episodes_from_dom`: `max` de los `/media/{id}/{n}` del DOM | `:202-203`, `:311-324` |

### Parseo de tarjetas de listado

📖 `__parse_anime_cards` (`:242-276`): `main article` → `a[href*='/media/']` → `h3` (título) →
`figure img` (póster). **Descarta** los enlaces a episodio concreto: si tras quitar `/media/` el
resto contiene `/`, se salta (`:259`). Deduplica con `seen_ids`.

📖 `__get_last_page` (`:278-290`): `max` de todos los `?page=N` de la página, sin depender del
paginador. ✅ Devolvió 50 para acción+aventura.

---

## 4. AnimeFLV — selectores CSS (el punto de rotura)

📖 Los selectores concretos, que son exactamente lo que se rompe cuando el sitio cambia:

| Uso | Selector | Línea |
|---|---|---|
| Tarjetas (búsqueda/browse) | `div.Container ul.ListAnimes li article` | `:46`, `:96` |
| Tarjetas (portada) | `ul.ListAnimes li article` | `:163` |
| Paginación | `div.Container div.NvCnAnm ul.pagination li` | `:45`, `:95` |
| `id` de la tarjeta | `div.Description a.Button` → `href[1:]` sin prefijo `anime/` | `:63`, `:112`, `:172` |
| Título de la tarjeta | `div.Title` (`.string`) | `:64`, `:113`, `:173` |
| Póster de la tarjeta | `div.Image figure img` → `src` | `:65`, `:114`, `:174` |
| Título de la ficha | `div.Container h1.Title` | `:196` |
| Póster de la ficha | `div.Image figure img` | `:197` |
| Sinopsis | `div.Description p` | `:198` |
| Géneros | `main.Main section.WdgtCn nav.Nvgnrs a` → `href.split("=")[1]` | `:201-205` |
| Episodios | `<script>` con `var anime_info = [` y `var episodes = [` | `:214-219` |
| Servidores | `<script>` con `var videos = {` → `json["SUB"]` | `:136-138` |

> ✅ **Asimetría intencionada del póster**: `get_recent_animes` (`:174`) y `get_anime_info` (`:197`)
> **prefijan** `BASE_URL`; las dos búsquedas (`:65`, `:114`) **no**. Es correcto: verificado que en la
> portada el `src` es relativo (`/uploads/animes/covers/4388.jpg`) y en `/browse` es absoluto
> (`https://animeflv.net/uploads/…`). **No "arregles" esta inconsistencia sin comprobarlo.**

> ✅ **Rotura activa**: `get_anime_episode_servers` devuelve `[]` porque el marcador `var videos = {`
> (`:136`) ya no aparece en `/ver/{slug}-{n}`. El usuario confirma que **el sitio está caído / en
> desuso**; no se invierte más esfuerzo en diagnosticarlo. Los otros 4 métodos seguían respondiendo
> el 2026-07-28.

---

## 5. Semántica exacta del fallback

📖 `call_with_fallback` (`:204-242`). ✅ **Todos los casos de esta sección verificados** con
proveedores falsos (`Boom` lanza excepción, `Empty` devuelve vacío, `Good` devuelve datos).

### Qué cuenta como «resultado vacío»

📖 `__is_empty_result` (`:193-202`):

| Valor devuelto | ¿Vacío? |
|---|---|
| `None` | **sí** |
| `[]` | **sí** |
| `([], 7)` — tupla cuyo primer elemento es lista vacía | **sí** (¡el `7` se pierde!) |
| `([anime], 3)` | no |
| `0`, `""`, `False` | **no** (no son `None`, ni lista, ni tupla-con-lista) |

### Orden de intento

📖 `_ordered_providers` (`:180-191`): primero el `provider_id` pedido (o el por defecto), luego
**todos los demás por orden de registro**.

> ✅ **Trampa**: si `provider_id` **no está registrado**, no se lanza ningún error — simplemente no se
> antepone nadie y se prueban todos en orden de registro. Con `strict=True` eso significa que se usa
> **el primer proveedor registrado**, no el que pediste ni el por defecto. Silencioso.

### Qué devuelve cada wrapper cuando todo falla

✅ Verificado:

| Wrapper | Línea | Si todos fallan |
|---|---|---|
| `get_recent_animes` | `:250-252` | **`[]`** |
| `get_anime_info` | `:254-256` | **`None`** |
| `search_animes_by_query` | `:258-262` | **`([], 1)`** ⚠️ el `1` es constante, no la página real |
| `search_animes_by_genres_and_order` | `:264-268` | **`([], 1)`** ⚠️ ídem |
| `get_anime_episode_servers` | `:270-274` | **`[]`** |
| `call_with_fallback` directo | `:242` | **`(None, None)`** |

**El manager nunca lanza excepciones** desde estos wrappers. `UnknownProviderError` solo sale de
`get()` (`:164-171`) y `set_default()` (`:156-159`), que la GUI no usa.

### `strict=True`

📖 `:218-219` → `providers_to_try = providers_to_try[:1]`. Desactiva el fallback: solo se intenta el
primer proveedor de la lista ordenada. ✅ Verificado que con `strict=True` sobre un proveedor que
explota, el wrapper devuelve el valor vacío correspondiente sin probar a nadie más.

### Diagnóstico por consola

📖 El manager imprime, y esos mensajes son la mejor pista al depurar:

```
[animeav1] Fallo en 'get_recent_animes': <excepción>              # :228
[animeav1] 'get_recent_animes' no devolvió resultados, probando…  # :232-233
Todos los proveedores fallaron en 'get_recent_animes': <exc>      # :239
Ningún proveedor devolvió resultados para 'get_recent_animes'     # :241
```

---

## 6. Síntomas típicos de rotura y cómo diagnosticarlos

| Síntoma en la app | Causa probable | Cómo confirmarlo |
|---|---|---|
| «No se pudo obtener la lista de animes recientes» | ambos proveedores devuelven `[]` | ejecutar el script de [09 §2](09-verificacion-y-pruebas.md) y mirar `len()` |
| Ficha con **título = el slug** y sin sinopsis | el payload de SvelteKit cambió; entró el fallback DOM (`:189-191`) | comprobar si `__extract_svelte_payload` devuelve `None` |
| Ficha con **0 episodios** | falló `episodesCount:` **y** el conteo por DOM | buscar `episodesCount` en el HTML crudo |
| Lista de episodios correcta pero **sin servidores** | regex `embeds:…SUB:` no casa, o el sitio está caído | buscar `embeds:` en el payload de `/media/{slug}/{n}` |
| Sinopsis y géneros **vacíos solo en AnimeAV1** | el sospechoso es **el payload**, no los selectores | ver §3 |
| Búsquedas vacías pero la portada funciona | cambió la ruta `/catalogo` o el nombre del parámetro (`search`, `genre`, `page`) | abrir la URL construida en el navegador |
| Paginación colapsada a 1 página | todos los proveedores fallaron → `([], 1)` | ver los `print` del manager |
| **Tildes rotas** en la sinopsis | ver §7 | |

**Regla de oro**: si AnimeAV1 empieza a devolver campos vacíos, **el sospechoso es el payload de
hidratación, no los selectores CSS**.

---

## 7. ⚠️ Bug de codificación en AnimeAV1 (visible para el usuario)

✅ **Verificado end-to-end el 2026-07-28.**

`animeav1.com` responde `Content-Type: text/html` **sin `charset`**. `requests` aplica entonces el
valor por defecto de HTTP, `ISO-8859-1`, aunque el contenido real es UTF-8
(`r.apparent_encoding == 'utf-8'`). Como `animeav1.py:169` hace
`BeautifulSoup(response.text, "html.parser")` sobre un texto **ya mal decodificado**, el mojibake
llega intacto a `AnimeInfo.synopsis`:

```
AnimeAV1Singleton().get_anime_info("one-piece").synopsis
# → "…One Piece y el tÃ­tulo de Rey de los Piratas que lo acompaÃ±a."
#      esperado:      "título"                            "acompaña"
```

**Alcance**:

- ✅ Afecta a `synopsis` (se muestra en la ficha **y se persiste en BD** al guardar un estado).
- ✅ **No** afecta a `genres` (slugs ASCII: `accion`, `fantasia`) ni a los `id`.
- ⚠️ Afectaría a `title` en animes con tildes; no comprobado con un título acentuado concreto.
- ⚠️ No comprobado si AnimeFLV tiene el mismo problema.

**Arreglo de una línea** (fuera del alcance de esta documentación — no se ha aplicado):
fijar `response.encoding = response.apparent_encoding` (o `"utf-8"`) antes de leer `response.text`.

---

## 8. Receta: añadir un proveedor nuevo

Pasos detallados con checklist en [11 §3](11-playbooks.md). Resumen:

1. Crear `src/APIs/<sitio>/__init__.py` (vacío) y `src/APIs/<sitio>/<sitio>.py`.
2. Cabecera de módulo obligatoria ([08 §1](08-convenciones-y-estilo.md)).
3. `class MiSitio(AnimeProvider)` con `PROVIDER_ID`, `PROVIDER_NAME`, `BASE_URL` **y los 5 métodos**.
4. Devolver siempre `AnimeInfo` / `EpisodeInfo` / `ServerInfo` de `APIs.common.models`.
5. Traducir géneros dentro del proveedor si los slugs difieren de `AnimeGenreFilter`.
6. Crear `MiSitioSingleton` siguiendo el patrón de `animeav1.py:339-345`.
7. Registrarlo en `gui/main_window.py:48-49`.
8. Añadir `APIs.<sitio>.<sitio>` a `hiddenimports` de `MiBibliotecaAnime.spec` ([trampa 18](10-invariantes-y-trampas.md)).
9. Verificar con el script de [09 §2](09-verificacion-y-pruebas.md), incluido el **orden de
   `episodes`** (afecta al corte `[:25]` y a lo que se guarda en BD).
