# 05 — Proveedores y scraping

| | |
|---|---|
| **Fecha** | 2026-08-06 · **Commit** `fd53056` · árbol **sucio** |
| **Última revisión** | 2026-08-06: **JKAnime integrado** como tercer proveedor (§3b). Tabla comparativa a 3 columnas y §2 con la primera traducción de géneros real del proyecto |
| **Cubre** | `src/APIs/common/animeProviderMgr.py`, `src/APIs/common/models.py`, `src/APIs/animeav1/animeav1.py`, `src/APIs/animeflv/animeflv.py`, `src/APIs/jkanime/jkanime.py` |

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

✅ AnimeAV1 y AnimeFLV verificados el 2026-07-28; **JKAnime el 2026-08-06** (50/50 comprobaciones,
[09 §3d](09-verificacion-y-pruebas.md)).

| | **AnimeAV1** (por defecto) | **JKAnime** | **AnimeFLV** |
|---|---|---|---|
| `PROVIDER_ID` | `animeav1` | `jkanime` | `animeflv` |
| `BASE_URL` | `https://animeav1.com` | `https://jkanime.net` | `https://www3.animeflv.net` |
| Tecnología del sitio | **SvelteKit** | **Laravel** | HTML clásico |
| Técnica de parseo | regex sobre payload JS + DOM | **las dos**: CSS en portada/búsqueda/ficha, payload JS en directorio y episodios | selectores CSS |
| Formato de `anime_id` | slug: `one-piece` | slug: `one-piece` | slug: `one-piece-tv` |
| `get_recent_animes` | ✅ 20 resultados | ✅ 49 resultados | ✅ 24 resultados |
| `get_anime_info` | ✅ 1171 eps, 4 géneros | ✅ 1172 eps (One Piece); 148 eps y 4 géneros en Hunter x Hunter | ✅ 1167 eps, 7 géneros |
| **Orden de `episodes`** | ✅ **ascendente** 1…N (`:227`) | ✅ **ascendente** 1…N | ✅ **descendente** N…1 (`:222-223`) |
| `search_animes_by_query` | ✅ 19 res., `last_page=1` | ✅ 22 res. («one piece»), `last_page=1`, **tope 30** | ✅ 12 res., `last_page=1` |
| ¿La búsqueda pagina? | ⚠️ no en la práctica | ❌ **no, por diseño** (rejilla 6×5) | ⚠️ no en la práctica |
| `search_..._by_genres_and_order` | ✅ 20 res., `last_page=50` | ✅ 30 res., `last_page=58` (acción); catálogo de 4864 en 163 págs. | ✅ 24 res., `last_page=79` |
| `get_anime_episode_servers` | ✅ 5 servidores | ✅ 3 servidores (varía por episodio) | ❌ **`[]`** |
| Orden `ALFABÉTICAMENTE` | cliente, `sorted(title.lower())` (`:350-351`) | servidor, `filtro=nombre&orden=asc` | servidor, `&order=title` |
| Orden `CALIFICACIÓN` | ⚠️ **no soportado**, avisa y devuelve el orden del sitio (`:352-357`) | ⚠️ se sirve con **popularidad**, que no es lo mismo | servidor, `&order=rating` |
| Filtrar por varios géneros | ✅ sí, repite `genre=` | ❌ **solo el primero** (el `<select>` del sitio es de selección única) | ✅ sí |
| Traducción de géneros | ❌ no la necesita | ✅ **10 de 40** | ❌ no la necesita |
| Reintentos en `get_anime_info` | 3, timeout 5 s, `sleep(1)` (`:184-241`) | ninguno (1 intento) | 3, timeout 2 s, `sleep(1)` (`:186-233`) |
| Estado general | **operativo** | **operativo** | **caído / en desuso** (confirmado por el usuario) |

> ✅ **JKAnime es el primer proveedor que sí traduce géneros.** AnimeAV1 y AnimeFLV usan literalmente
> los slugs de `AnimeGenreFilter`; JKAnime coincide en 30 de los 40 y difiere en 10, que
> `_GENRE_TRANSLATIONS` mapea: `carreras→autos`, `ciencia-ficcion→sci-fi`, `demencia→dementia`,
> `escolares→colegial`, `espacial→space`, `infantil→nios`, `policia→policial`,
> `recuentos-de-la-vida→cosas-de-la-vida`, `superpoderes→super-poderes`, `suspenso→thriller`.
> El diccionario **solo lista las excepciones**; `__translate_genre()` cae al valor del enum para el
> resto. ✅ Verificado que los 40 producen un slug que existe entre los 45 reales del sitio.

---

## 3. AnimeAV1 — el payload de hidratación

📖 `animeav1.py:1-8` y `:34`. El sitio no sirve HTML navegable por selectores estables: SvelteKit
inyecta los datos como **objeto JS (no JSON estricto)** dentro de un `<script>` que contiene
`kit.start(app, element, {`.

### Cómo se extrae

```python
# animeav1.py:250-259
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
| `title` | **payload** `re.search(r'title:\s*"(.+?)",')` | `:199,203-204` | ✅ `"One Piece"` |
| `synopsis` | **payload** `r'synopsis:\s*"(.*?)",'` + des-escape `\n` y `\"` | `:200,205-206` | ✅ |
| `episodes` | **payload** `r'episodesCount:\s*(\d+),'` → `[1..N]` | `:201,207-208,227` | ✅ 1171 |
| `poster` | **DOM** `main figure img` → `src` | `:219-220` | ✅ (en el payload es `poster:null`) |
| `genres` | **DOM** `main a[href*='genre=']` → `?genre=` | `:222`, `:314-331` | ✅ `['accion','aventura','fantasia','shounen']` |
| `id` | el `anime_id` que se pasó | `:230` | ✅ |
| servidores | **payload** `r"embeds:\s*.*?SUB:\s*(\[.*?\])"` | `:148` | ✅ 5 servidores |

> ⚠️ **Nota**: los géneros **están en el payload** (`genres:[{…,slug:"accion",…}]`) pero el código los
> saca del **DOM**. Si algún día el DOM cambia y el payload no, hay un origen alternativo ya
> disponible.

### Fallbacks al DOM

📖 `:210-222`. Si el payload no da un campo:

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

## 3b. JKAnime — las dos técnicas a la vez *(2026-08-06)*

✅ Verificado contra el sitio real. `jkanime.py:1-19` explica el porqué en el propio módulo.

**Lo que hay que entender antes de tocarlo**: jkanime.net **no se parsea de una sola manera**.
Es la primera vez en el proyecto que un proveedor mezcla las dos técnicas, y confundirlas es
perder el tiempo mirando el DOM equivocado.

| Superficie | Cómo llega el dato | Se parece a |
|---|---|---|
| Portada (`/`) | HTML servidor, `div.card` | AnimeFLV |
| Búsqueda (`/buscar/<q>`) | HTML servidor, `div.anime__item` | AnimeFLV |
| Ficha (`/<slug>`) | HTML servidor, `div.anime_info` | AnimeFLV |
| **Directorio** (`/directorio?p=N`) | **payload JS incrustado** | AnimeAV1 |
| **Episodios** | **JSON por `POST /ajax/episodes/<id>/`** | — |

### El directorio: rejillas vacías que NO son un fallo

⚠️ **La trampa principal.** Los tres `div.row.page_directorio` (modos de vista 1/2/3) llegan
**vacíos** en el HTML. Es tentador concluir que hace falta renderizar JS o encontrar un endpoint
AJAX. **Las dos conclusiones son falsas**, y ambas se probaron:

- No existe endpoint: `/ajax/directorio`, `/ajax/filtros`, `/ajax/filter` y `/ajax/animes`
  devuelven 404 o 405.
- El servidor **ya incrusta el payload completo** en un `<script>` de la propia página. El bundle
  lo delata: `render_animes()` hace `$.each(animes.data, …)` sobre una variable ya presente.

Se extrae buscando `animes = {` y **contando llaves**, respetando cadenas y escapes
(`__extract_directory_payload`). Una expresión regular perezosa cortaría por el sitio equivocado:
las sinopsis llevan comillas dentro.

El objeto es un **paginador de Laravel** (`current_page`, `data`, `last_page`, `per_page`, `total`),
así que `last_page` viene dado y no hay que deducirlo del DOM como en los otros dos proveedores.

✅ `total = 4864` animes en 163 páginas de 30. Los elementos traen `title`, `synopsis`, `image` y
`url` ya resueltos: **el listado del directorio no necesita una segunda petición** para completarse,
al contrario que las tarjetas de AnimeAV1 y AnimeFLV.

### Los episodios: la única petición con CSRF

📖 `__get_episodes`. Laravel responde **419** si falta el token. Hacen falta tres cosas, y las tres
salen del HTML de la ficha:

1. el **id numérico interno** (`429` para `hunter-x-hunter-2011`), que se saca de la propia URL
   `/ajax/episodes/(\d+)` que aparece en la página;
2. el token de `<meta name="csrf-token">`;
3. las cookies de sesión — por eso `get_anime_info` abre una `requests.Session()` propia y encadena
   ficha y AJAX en ella.

> ⚠️ **Dos identidades**, igual de traicioneras que las de la ficha de detalle: el **slug**
> (`hunter-x-hunter-2011`) es lo que viaja en `AnimeInfo.id` y en las URL; el **id numérico** (`429`)
> solo sirve para ese endpoint. No son intercambiables y el numérico no aparece en ninguna URL
> navegable.

La respuesta es otro paginador de Laravel, pero **solo se usa su `total`**: los episodios están
numerados de 1 a N, así que no hace falta recorrer sus páginas para reconstruir la lista.

Si esa segunda llamada falla, `get_anime_info` **devuelve la ficha igualmente** con `episodes=[]`,
en vez de perder también título, sinopsis y géneros que sí se leyeron.

### La búsqueda no pagina, y es por diseño

✅ `/buscar/<q>` devuelve **como mucho 30** resultados: la rejilla del sitio es de 6×5. No es una
carencia que se pueda sortear con parámetros:

- `/buscar/<q>/1/` → **404**;
- `?p=1`, `?p=2` y `?p=3` devuelven listas **idénticas** (comparadas título a título);
- `/directorio?buscar=<q>` no filtra: el título de la página solo refleja el parámetro.

Por eso `search_animes_by_query` devuelve siempre `last_page=1`, y ante `page>1` devuelve `[]`
**en vez de la primera página disfrazada de segunda** — que haría paginar en bucle a quien llame.
Para recorrer el catálogo está el directorio.

✅ El separador de palabras es **indiferente**: `one%20piece`, `one+piece`, `one-piece` y el espacio
crudo devuelven los mismos 22 resultados. No hace falta lógica de separadores.

### Tarjetas: dos imágenes por `<img>` en la portada

⚠️ Las tarjetas de la portada son de **episodio**, no de anime, y su `<img>` lleva dos imágenes:

| Atributo | Contenido |
|---|---|
| `src` | captura del episodio (`.../animes/video/image/jkvideo_*.jpg`) |
| `data-animepic` | **póster del anime** (`.../animes/image/<slug>.jpg`) ← el que se usa |

Usar `src` llenaría la biblioteca de fotogramas sueltos en vez de pósters. En la **búsqueda** el
póster tampoco está en un `<img>`: va en `data-setbg` de `.anime__item__pic`.

### El orden del directorio necesita dos parámetros

✅ `filtro` dice **por qué** ordenar y `orden` dice **en qué sentido**, y sin el segundo el sitio
devuelve de la Z a la A:

| `AnimeOrderFilter` | Parámetros | Nota |
|---|---|---|
| `ALFABÉTICAMENTE` | `filtro=nombre&orden=asc` | sin `orden=asc` → **descendente** |
| `CALIFICACIÓN` | `filtro=popularidad` | **adrede sin `orden`**: `asc` lo invierte y pone delante los menos populares |
| `POR_DEFECTO` | ninguno | |

> ⚠️ El orden alfabético del sitio usa la **colación de MySQL**, que coloca la puntuación inicial
> de otra forma que Python. Comprobar el resultado con `sorted(key=str.lower)` da un falso
> negativo: `.hack//G.U. Trilogy` va primero allí y tercero aquí. Verificar que es **ascendente**,
> no que coincide carácter a carácter.

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

✅ Orden de registro actual (`main_window.py`), verificado el 2026-08-06:

```
animeav1  (predeterminado)  →  jkanime  →  animeflv
```

**JKAnime va antes que AnimeFLV a propósito**: hasta ahora el fallback tenía una sola parada y
estaba muerta, así que en la práctica no había fallback. Ahora la primera parada funciona.

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

## 5b. Elegir proveedor: sesión vs. predeterminado *(2026-07-30, reformado el 2026-08-06)*

Desde la tarea del selector ([13](13-selector-de-proveedor.md)) el proveedor ya no lo decide solo el
registro de `MainWindow`: hay **tres niveles**, de menos a más específico.

| Nivel | Quién lo fija | Fallback | Persiste |
|---|---|---|---|
| Registro en código | `main_window.__init__` → `register(AnimeAV1Singleton(), default=True)` | — | — |
| **Predeterminado del usuario** | el **pin** de la sidebar → `DB_user.db`; se aplica en el arranque | **activo** | ✅ sí |
| **Sesión** | desplegable de la sidebar → solo `set_default()` | **activo** | ❌ no |

**Por qué el ámbito global conserva el fallback**: `ANIMES.anime_id` guarda el *slug* del
proveedor que sirvió cada anime. Si el usuario elige un proveedor distinto y se usara `strict`, el clic
en un anime guardado dejaría de resolver. Con fallback degrada a una petición perdida.

> 🗑️ **El nivel «puntual, por ficha» ya no existe.** El desplegable de la ficha de detalle, que
> llamaba con `strict=True` y re-resolvía el anime por título, se retiró el 2026-08-06: con el
> desplegable de la sidebar valiendo solo para la sesión, hacía lo mismo con más código.
>
> Lo que **sí** sobrevive de aquel nivel: `get_anime_episode_servers` se sigue llamando con
> `provider_id=self.provider_id, strict=True` desde la ficha, para que los servidores sean los del
> proveedor que la sirvió y no los de un fallback silencioso. Si ese proveedor no da servidores, se
> avisa en vez de pintar un selector vacío.
>
> ⚠️ El orden de prioridad que vendrá con la columna `provider_id` (desviación del desplegable >
> `provider_id` en BD > pin > registro) está decidido en [13 §8](13-selector-de-proveedor.md).

### Identidad de un anime entre proveedores

`AnimeInfo.id` es el *slug* del sitio: el mismo anime es `one-piece-gyojin-touhen` en AnimeAV1 y
`one-piece` en AnimeFLV. **No se puede reutilizar el id al cambiar de proveedor.**
`resolve_anime_in_provider(anime_info, provider_id)` hace la traducción:

1. `search_animes_by_query(título, provider_id=…, strict=True)`.
2. Compara con `normalize_title()` (minúsculas, sin tildes, resto a espacios).
3. Coincidencia exacta normalizada → gana; si no, mejor `difflib.SequenceMatcher.ratio()` ≥
   `TITLE_MATCH_THRESHOLD` (**0.75**).
4. `get_anime_info(match.id, provider_id=…, strict=True)`.

Prefiere **no encontrar** a encontrar mal: por debajo del umbral devuelve `None`.

✅ Verificado el 2026-07-30: con un proveedor falso, un título con una letra menos da 0.968 (se acepta)
y un título sin relación 0.35 (se rechaza). Contra AnimeAV1 real, un título largo con puntuación
(`Kimetsu no Yaiba Movie 1: Mugenjou-hen - Akaza Sairai`) resuelve al mismo slug con similitud 1.00.

⚠️ **Lo que no se ha podido verificar**: una resolución cruzada real entre **dos** proveedores
distintos. AnimeFLV está en desuso, así que hoy no hay un segundo proveedor sano contra el que probarlo.
El umbral 0.75 sigue siendo, por tanto, una estimación calibrada solo con datos sintéticos: revísalo al
integrar el tercer proveedor.

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
| **JKAnime**: directorio vacío, el resto bien | cambió el nombre de la variable `animes` del payload | buscar `animes = {` en el HTML de `/directorio` |
| **JKAnime**: fichas sin episodios pero con sinopsis | el POST a `/ajax/episodes/` da 419 (CSRF) o cambió el `<meta name="csrf-token">` | ver §3b |
| **JKAnime**: la biblioteca se llena de fotogramas | se está leyendo `src` en vez de `data-animepic` | ver §3b |
| **JKAnime**: el directorio sale de la Z a la A | falta `orden=asc` junto a `filtro=nombre` | ver §3b |

**Regla de oro**: si AnimeAV1 empieza a devolver campos vacíos, **el sospechoso es el payload de
hidratación, no los selectores CSS**. En **JKAnime** la regla es distinta y depende de la
superficie: portada, búsqueda y ficha se rompen por selectores; directorio y episodios, por el
payload. Ver la tabla de §3b antes de decidir dónde mirar.

---

## 7. Codificación: por qué todo el scraping pasa por `_fetch()`

✅ **Resuelto el 2026-07-30** (commit `94b497e`). Diagnosticado el 2026-07-28; se documenta el porqué
porque la causa **sigue estando en el sitio**, no en el código: si alguien añade una petición directa,
el bug vuelve.

`animeav1.com` responde `Content-Type: text/html` **sin `charset`**. Ante esa ausencia, `requests`
aplica el defecto de la RFC 2616, `ISO-8859-1`, aunque el contenido real es UTF-8
(`r.apparent_encoding == 'utf-8'`). Todo lo que saliera de `response.text` llegaba mal decodificado:

```
AnimeAV1Singleton().get_anime_info("one-piece").synopsis
# antes → "…One Piece y el tÃ­tulo de Rey de los Piratas que lo acompaÃ±a."
# ahora → "…One Piece y el título de Rey de los Piratas que lo acompaña."
```

**El helper** (`animeav1.py:37-56`) — lo usan las **5** llamadas de scraping del módulo:

```python
def _fetch(url: str, **kwargs) -> requests.Response:
    response = requests.get(url, **kwargs)
    if "charset" not in response.headers.get("Content-Type", "").lower():
        response.encoding = "utf-8"
    return response
```

Se fija UTF-8 **solo si el servidor no declara charset**, para respetar el suyo si algún día empieza a
declararlo. No se usa `apparent_encoding` (detección estadística): es más lento en páginas grandes y
puede acertar mal, mientras que aquí el encoding real del sitio es un hecho verificado.

**Alcance del bug, ya cerrado**:

| Campo | ¿Afectado? | |
|---|---|---|
| `synopsis` | ✅ sí | se mostraba **y se persistía en BD** |
| `title` | ✅ sí | sale del DOM (`animeav1.py:293`), del mismo `response.text`. La versión anterior de esta sección lo daba por no comprobado |
| `genres` | ✅ no | slugs ASCII (`accion`, `fantasia`) |
| `id` | ✅ no | slugs ASCII |

⚠️ Sigue sin comprobarse si AnimeFLV tiene el mismo problema — está en desuso y no sirve servidores
([§2](#2-estado-de-los-proveedores)), así que no se ha diagnosticado.

> **Invariante**: debe haber **exactamente una** aparición de `requests.get` en `animeav1.py`, la de
> dentro de `_fetch`. Comprobable con `grep -c "requests.get" src/APIs/animeav1/animeav1.py` → `1`.
>
> **Y el código no repara lo ya guardado**: al arreglarlo había 3 filas con la sinopsis rota en la BD
> real, que hubo que re-descargar aparte ([12 §1](12-deuda-tecnica-y-roadmap.md)).

---

## 8. Receta: añadir un proveedor nuevo

Pasos detallados con checklist en [11 §3](11-playbooks.md). Resumen:

1. Crear `src/APIs/<sitio>/__init__.py` (vacío) y `src/APIs/<sitio>/<sitio>.py`.
2. Cabecera de módulo obligatoria ([08 §1](08-convenciones-y-estilo.md)).
3. `class MiSitio(AnimeProvider)` con `PROVIDER_ID`, `PROVIDER_NAME`, `BASE_URL` **y los 5 métodos**.
4. Devolver siempre `AnimeInfo` / `EpisodeInfo` / `ServerInfo` de `APIs.common.models`.
5. Traducir géneros dentro del proveedor si los slugs difieren de `AnimeGenreFilter`.
6. Crear `MiSitioSingleton` siguiendo el patrón de `animeav1.py:361-367`.
7. Registrarlo en `gui/main_window.py` (bloque de `register`), **decidiendo dónde**: el orden de
   registro es el orden del fallback.
8. Añadir `APIs.<sitio>.<sitio>` a `hiddenimports` de `MiBibliotecaAnime.spec` ([trampa 18](10-invariantes-y-trampas.md)).
9. Verificar con el script de [09 §2](09-verificacion-y-pruebas.md), incluido el **orden de
   `episodes`** (afecta al corte `[:25]` y a lo que se guarda en BD).

> ✅ **JKAnime (2026-08-06) es el ejemplo trabajado más completo de esta receta**, y el único que
> ejercita los pasos 5 (traducción de géneros) y 7 (posición en el fallback). Su implementación está
> en `jkanime.py` y el porqué de cada decisión, en §3b.
