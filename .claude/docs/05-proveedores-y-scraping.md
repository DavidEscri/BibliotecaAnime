# 05 — Proveedores y scraping

| | |
|---|---|
| **Fecha** | 2026-10-28 · rama `release/0.5.0` · último commit de código **`7bbbb3c`** |
| **Última revisión** | 2026-10-28 (**versión 0.5.0**): §1 gana el **cuarto atributo obligatorio** (`PROVIDER_SHORT_NAME`), el atributo opcional `RELATIONS_CARRY_FORMAT` y **dos métodos no abstractos** (`get_anime_relations` y `genre_filters`, con su gancho `_genre_from_slug`); §3 gana **«Relaciones, formato y géneros»** (los códigos de `relations`, `category.malId`, el recorte del array y el *fallback* al DOM; el catálogo y sus géneros con **O**); §3b gana **«Temporadas y relacionados»** (la sección con `id` repetidos, el paréntesis que no siempre es formato, la ficha ligera de **una** petición y el 429 del directorio). Antes, 2026-10-20 (**reproductor in-app**): **§9 nuevo**, los **hosters**: qué entrega cada uno, con qué cabeceras y con qué caducidad, por qué la resolución **no** es un método de `AnimeProvider` y cómo se diagnostica uno que dejó de resolver. §6 gana la fila que remite allí. JKAnime convierte en absolutas las URLs de servidor relativas (Okru, `urljoin`). Antes, 2026-08-16: `PROVIDER_ID` deja de ser una cadena y pasa a ser **`AnimeProviderId`** (§1); `provider_info()` nuevo; el fallback ahora **estampa** quién respondió (§5) |
| **Cubre** | `src/APIs/common/animeProviderMgr.py`, `src/APIs/common/models.py`, `src/APIs/animeav1/animeav1.py`, `src/APIs/animeflv/animeflv.py`, `src/APIs/jkanime/jkanime.py`, `src/APIs/resolvers/` |

Procedencia: ✅ verificado en ejecución contra los sitios reales el 2026-07-28 · 📖 leído en código ·
⚠️ sin verificar.

---

## 1. El contrato `AnimeProvider`

📖 `animeProviderMgr.py:26-176`.

```python
class MiProveedor(AnimeProvider):
    PROVIDER_ID         = AnimeProviderId.MISITIO   # ← ENUM, no una cadena (2026-08-16)
    PROVIDER_NAME       = "MiSitio"                 # nombre legible para la UI
    PROVIDER_SHORT_NAME = "MS"                      # siglas (2026-10-28): marcan lo que aporta este sitio
    BASE_URL            = "https://misitio.com"
    RELATIONS_CARRY_FORMAT = False                  # opcional: sus relacionados traen formato

    def search_animes_by_genres_and_order(self, genres: List[AnimeGenreFilter],
                                          order: str = None,
                                          page: int = None) -> Tuple[List[AnimeInfo], int]: ...
    def search_animes_by_query(self, query: str = None,
                               page: int = None) -> Tuple[List[AnimeInfo], int]: ...
    def get_anime_episode_servers(self, anime_id, episode_id: int) -> List[ServerInfo]: ...
    def get_recent_animes(self) -> List[AnimeInfo]: ...
    def get_anime_info(self, anime_id) -> AnimeInfo | None: ...
```

**Cinco métodos abstractos**, ni uno más. `is_available(timeout=5.0)` (`:165-175`) tiene
implementación por defecto (un `GET BASE_URL`) y es opcional sobrescribirla.

🆕 **Y desde el 2026-10-28, dos métodos no abstractos más**, que un proveedor sobrescribe solo si le
compensa:

| Método | Por defecto | Quién lo sobrescribe |
|---|---|---|
| `get_anime_relations(anime_id)` (`:122-132`) | `get_anime_info(anime_id)` | **JKAnime**: su ficha completa cuesta dos peticiones (la página y el POST de episodios) y para leer relaciones basta la primera ([§3b](#3b-jkanime--las-dos-técnicas-a-la-vez-2026-08-06)) |
| `genre_filters(genres)` (`:134-152`), **sin red** | traduce cada slug con `_genre_from_slug()` (`:154-163`), que es `AnimeGenreFilter(slug)`; lo que no tenga equivalente se descarta con **un** aviso por (proveedor, slug) y sesión | **JKAnime** sobrescribe solo el gancho `_genre_from_slug` con `_GENRES_FROM_SLUG`, la inversa de su tabla de traducción |

`get_anime_relations` devuelve una ficha **sin garantía de episodios**: sirve para título, formato,
póster y relacionados. Lo usa el recorrido de la franquicia (`gui/franchise_service.py`,
[03 §15](03-flujos-de-ejecucion.md)). `RELATIONS_CARRY_FORMAT = True` declara que los relacionados de
la ficha **traen su propio formato** (hoy solo JKAnime): es lo que permite al servicio pedir **una**
ficha a ese sitio para completar los formatos que no sabe otro.

En el manager, sus dos wrappers **validan el proveedor** antes de nada (trampa 13): 
`get_anime_relations(anime_id, provider_id)` (`:396-411`) va **siempre** con `strict=True` y sin
parámetro `strict` —un slug solo significa algo en el sitio que lo dio— y `genre_filters(genres,
provider_id)` (`:427-438`) devuelve `[]` si el proveedor no está registrado.

🆕 `provider_info()` (`:65-72`) es un `classmethod` **ya implementado**: devuelve un `ProviderInfo`
construido desde los 4 atributos de clase. No hay que escribirlo, y es lo que consume la GUI para
poblar el desplegable — así no existe en ningún sitio una lista paralela de nombres que mantener.

### 🆕 `PROVIDER_ID` es un `AnimeProviderId`, no una cadena *(2026-08-16)*

Cambió al persistirse el proveedor en `ANIMES.provider_id`: un dato que se guarda necesita un
conjunto cerrado de valores legales y una degradación definida para los que dejen de serlo
([04 §1b](04-modelo-de-datos.md)). El `value` del miembro es exactamente lo que se escribe en BD, así
que **elegirlo bien es una decisión permanente**.

### Validación en `__init_subclass__`

✅ Verificado. `:50-63`. Dos comprobaciones, las dos **en el momento del import**, no al usar la clase:

1. Falta cualquiera de los **4** atributos de clase (`PROVIDER_SHORT_NAME` desde el 2026-10-28) →
   `NotImplementedError: Incompleto debe definir el atributo de clase 'PROVIDER_ID'`
2. 🆕 `PROVIDER_ID` no es un miembro de `AnimeProviderId` (`:71-75`) →
   `NotImplementedError: MiProveedor.PROVIDER_ID debe ser un miembro de AnimeProviderId, no str`

La segunda existe porque el registro **indexa por enum**: dejar ahí la cadena `"misitio"` registraría
el proveedor bajo una clave que nadie busca, y el fallo no aparecería hasta el primer `get()` fallido
—probablemente en otra sesión, y sin relación aparente con la causa—.

> ✅ **Trampa poco intuitiva**: la condición es `if ABC not in cls.__bases__` (`:52`). Solo
> `AnimeProvider` lista `ABC` entre sus bases directas. Por tanto **cualquier** subclase —incluida una
> clase base intermedia que quieras dejar abstracta— está obligada a definir los 4 atributos.
> No puedes hacer `class ProveedorHTMLBase(AnimeProvider): ...` sin darle valores de relleno.

### Reglas que toda implementación debe cumplir

1. 📖 Devolver **siempre** tipos de `APIs.common.models`, nunca tipos propios del sitio (`:27-30`).
2. 📖 Las búsquedas devuelven **`Tuple[List[AnimeInfo], int]`** = (resultados, última página).
3. 📖 Si el sitio usa slugs de género distintos a `AnimeGenreFilter`, **traducirlos dentro del
   proveedor** (`:31-35`). Quien llama siempre pasa el enum común.
4. ⚠️ *No escrito en el contrato, pero asumido por la GUI*: en los **listados**, `synopsis`, `genres`
   y `episodes` valen `None`; solo `get_anime_info` los rellena. La precarga de recientes
   (`main_window.py:296`) y `recentAnimes.py:87` dependen de ello.
5. 🆕 *(2026-10-28)* En la **ficha** (`get_anime_info` / `get_anime_relations`), `related` es una
   lista —`[]` si el anime no tiene relacionados— y `format` el formato, o `None` si no se reconoce.
   **`related = None` significa «este proveedor no sabe dar relaciones»** (AnimeFLV, y todos los
   listados): la ficha distingue «no tiene» de «no lo sé» y en el segundo caso **no pinta la pestaña**.
   Lo que no sea precuela, secuela o versión alternativa se traduce a `OTHER` **dentro del proveedor**
   ([trampa 59](10-invariantes-y-trampas.md)).
6. 🆕 **No rellenes `AnimeInfo.provider_id`.** Lo estampa el manager al responder (§5), que es el único
   que sabe cuál de los proveedores acabó contestando cuando entra el fallback. Un proveedor que lo
   rellenara a mano mentiría en cuanto alguien llamara a su método directamente.

---

## 2. Tabla comparativa

✅ AnimeAV1 y AnimeFLV verificados el 2026-07-28; **JKAnime el 2026-08-06** (50/50 comprobaciones,
[09 §3d](09-verificacion-y-pruebas.md)).

| | **AnimeAV1** (por defecto) | **JKAnime** | **AnimeFLV** |
|---|---|---|---|
| `PROVIDER_ID` | `AnimeProviderId.ANIMEAV1` | `AnimeProviderId.JKANIME` | `AnimeProviderId.ANIMEFLV` |
| `PROVIDER_ID.value` (lo que se persiste) | `animeav1` | `jkanime` | `animeflv` |
| `BASE_URL` | `https://animeav1.com` | `https://jkanime.net` | `https://www3.animeflv.net` |
| 🆕 `PROVIDER_SHORT_NAME` | `AV1` | `JK` | `FLV` |
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
| Reintentos en `get_anime_info` | 3, timeout 5 s, `sleep(1)` (`:201-276`) | ninguno (1 intento) | 3, timeout 2 s, `sleep(1)` (`:186-233`) |
| 🆕 `related` / `format` de la ficha | payload `relations` + `category.malId`; **sin formato** en la relación, **con** año y póster | sección «Temporadas y relacionados» + `li[rel='tipo']`; **con** formato en la relación, sin año ni póster | ❌ `None` (no sabe darlas) |
| 🆕 `get_anime_relations` | = `get_anime_info` (1 GET, **3 reintentos**) | **1 GET**, sin el POST | = `get_anime_info` |
| 🆕 Varios géneros en el catálogo | se combinan con **O** | solo el primero | ⚠️ sin comprobar |
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

### Relaciones, formato y géneros 🆕 *(2026-10-28, versión 0.5.0)*

✅ Inventariado el 2026-10-28 contra 9 fichas reales y cotejado con la etiqueta del DOM de cada
tarjeta. 📖 `animeav1.py:39-63` (tablas) y `:371-497` (extracción).

**Relacionados** — el payload que `get_anime_info` **ya descarga** trae al final un array:

```js
relations:[{type:2,destination:{id:317,slug:"kusuriya-no-hitorigoto-2nd-season",
            title:"Kusuriya no Hitorigoto 2nd Season",startDate:"2025-01-10"}}]
```

| `type` | Etiqueta del DOM | `AnimeRelationType` |
|---|---|---|
| `1` | Precuela | `PREQUEL` |
| `2` | Secuela | `SEQUEL` |
| `4` | Versión Alternativa | `ALTERNATIVE` |
| `6`, `7`, `8`, `10` | Resumen, Historia completa, **Historia principal**, Otro | `OTHER`, sin aviso |
| cualquier otro | — | `OTHER` **con un `print`** (⚠️ el 3, el 5 y el 9 no han salido en ninguna muestra) |

⚠️ «Historia principal» (`8`) apunta de una película u OVA **a la serie madre**: no es una precuela
([trampa 59](10-invariantes-y-trampas.md)).

- **El array se recorta contando corchetes y respetando las cadenas** (`__extract_js_array`,
  `:464-497`), porque hay títulos con `]` («[Oshi no Ko]», [trampa 60](10-invariantes-y-trampas.md)).
  Cada entrada se parte por `{type:` y sus campos salen con **regex independientes del orden**; las
  cadenas se des-escapan con `json.loads` (`_unescape_js`).
- **Año**: los cuatro primeros dígitos de `startDate`. **Póster**: `cdn.animeav1.com/covers/{id}.jpg`
  con el `id` de `destination` (`COVER_URL`, `:30`), gratis y sin petición extra.
- **La relación no trae formato**: el de cada relacionado solo se sabe abriendo su ficha, o
  preguntando a otro sitio (`RELATIONS_CARRY_FORMAT` queda en `False`).
- **Fallback**: si el payload no trae `relations`, `__extract_relations_from_dom` (`:430-462`) lee la
  sección «Relacionados» del DOM (`main h2` → `section` → `article`, con `header h3`, `header span`,
  `a[href^='/media/']` e `img`). ✅ Probado offline: da **exactamente** lo mismo que el payload en 3
  fichas (29 relacionados en One Piece). ⚠️ No se ha visto actuar en vivo.
- Sin sección, `related = []` (no `None`): AnimeAV1 **sí sabe** dar relaciones.

**Formato del propio anime** — `category:{id:…,name:"TV Anime",slug:"tv-anime",malId:"TV"}`, leído
de **`malId`**, que es un código estable (`__extract_format`, `:371-384`):

| `malId` | `AnimeFormat` |
|---|---|
| `TV` | `SERIES` |
| `Movie` | `MOVIE` |
| `OVA` | `OVA` |
| `TV Special` | `SPECIAL` (✅ es lo que da el sitio; no `Special`) |
| `Special`, `ONA` | `SPECIAL`, `ONA` — ⚠️ por si acaso, no han salido |

**Géneros del catálogo** — ✅ 2026-10-28: `catalogo?genre=…` trae en su payload los **46 géneros**
del sitio, y **33 son idénticos** a los `value` de `AnimeGenreFilter`, así que AnimeAV1 usa el
`_genre_from_slug` por defecto. Los 13 que solo existen allí (`antropomorfico`, `detectives`,
`elenco-adulto`, `gore`, `gourmet`, `idols-hombre`, `idols-mujer`, `isekai`, `juegos-estrategia`,
`mahou-shoujo`, `mitologia`, `shoujo-ai`, `shounen-ai`) se descartan con un aviso por sesión. Del enum
faltan en el sitio `demencia`, `demonios`, `juegos`, `magia`, `policia`, `yaoi` y `yuri`.

🔴 **Dos géneros en el catálogo se combinan con O, no con Y** ([trampa 66](10-invariantes-y-trampas.md)):
«acción + romance» trae animes de solo romance. 20 resultados por página. El catálogo **no ordena por
calificación** (`__apply_client_side_order` ordena en el cliente lo que sabe); admite `order` en la
URL, pero ⚠️ sus valores no salen en el HTML y no se investigaron. Ningún resultado de búsqueda trae
sus géneros (la tarjeta y su payload: `id`, `title`, `synopsis`, `categoryId`, `slug`).

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
   ⚠️ **Esa sesión no puede ser la de `thread_session()`** (2026-10-27): la del hilo **no guarda
   cookies a propósito**, y con ella el AJAX daría 419. JKAnime se quedó fuera de B16 por eso y
   porque el resto de sus peticiones son de una en una por hilo, donde reutilizar no gana nada.

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

### Temporadas y relacionados 🆕 *(2026-10-28, versión 0.5.0)*

✅ Inventariado el 2026-10-28. 📖 `jkanime.py:69-87` (tablas) y `:482-553` (extracción).

La ficha trae una sección `<h3>Temporadas y relacionados</h3>` con bloques
`<h5 id="aditional">Secuela</h5>` seguidos de `<a href="https://jkanime.net/<slug>/">Título (Serie)</a><br>`.

- **Todos los `<h5>` llevan el mismo `id="aditional"`** ([trampa 61](10-invariantes-y-trampas.md)):
  `__extract_relations` recorre **en orden** los hermanos `h5`/`a` del `<h3>`, y el tipo de cada
  enlace es el del último `<h5>`.
- Tipos vistos y su traducción (etiqueta normalizada con `normalize_title()`, sin tildes, como las
  escribe el sitio): **Precuela** → `PREQUEL`, **Secuela** → `SEQUEL`, **Version alternativa** →
  `ALTERNATIVE`; Adicional, Derivado, Resumen, Personaje incluido, Otro, **Predecesor** y **Version
  completa** → `OTHER` sin aviso; cualquier otro, `OTHER` con un `print`. «Predecesor» es la historia
  madre, no una precuela ([trampa 59](10-invariantes-y-trampas.md)).
- **Formato en el paréntesis final** (Serie, OVA, Pelicula, Especial, ONA), que `__split_format` solo
  separa **si es un formato conocido**: «Hunter x Hunter (2011)» se queda entero
  ([trampa 62](10-invariantes-y-trampas.md)). Por eso `RELATIONS_CARRY_FORMAT = True`.
- **Sin año ni póster** en la relación. Los de la línea principal salen de las páginas que el
  recorrido ya descarga (`og:image`); los «otros» van sin póster.
- **Formato del propio anime**: `<li rel="tipo"><span>Tipo:</span> Serie</li>`, que aparece **dos
  veces** en la página; vale la primera (`__extract_format`).

**La ficha ligera es una petición.** `get_anime_info` = `__get_anime_page()` (`:317-359`, la página)
**+** el POST de episodios con CSRF; `get_anime_relations` (`:303-310`) se queda en la primera. ✅
Medido: el recorrido de SnK (7 temporadas) son **6 GET y ningún POST**.

**Géneros al enum común**: `_genre_from_slug` (`:365-372`) usa `_GENRES_FROM_SLUG` (`:56`), la inversa
de `_GENRE_TRANSLATIONS`: `colegial` → `ESCOLARES`, `sci-fi` → `CIENCIA_FICCIÓN`, `autos` → `CARRERAS`,
`nios` → `INFANTIL`. El directorio admite **un solo** género, así que «Te puede interesar» busca por el
primero.

🔴 **El directorio responde 429 con su propio texto** si se le pide de seguido («Estas realizando
demasiadas peticiones… el bloqueo dura 60 segundos»), también tras las peticiones de una sesión
anterior del mismo día. La búsqueda devuelve `([], 1)` y parece vacía
([trampa 65](10-invariantes-y-trampas.md)).

---

## 4. AnimeFLV — selectores CSS (el punto de rotura)

🆕 *(2026-10-28)* En desuso: **no se le añadieron relaciones**. Su `related` queda en `None` («no lo
sé») y la ficha no enseña la pestaña de temporadas; solo ganó `PROVIDER_SHORT_NAME = "FLV"`.

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

📖 `call_with_fallback` (`:293-334`). ✅ **Todos los casos de esta sección verificados** con
proveedores falsos (`Boom` lanza excepción, `Empty` devuelve vacío, `Good` devuelve datos).

### Qué cuenta como «resultado vacío»

📖 `__is_empty_result` (`:285-291`):

| Valor devuelto | ¿Vacío? |
|---|---|
| `None` | **sí** |
| `[]` | **sí** |
| `([], 7)` — tupla cuyo primer elemento es lista vacía | **sí** (¡el `7` se pierde!) |
| `([anime], 3)` | no |
| `0`, `""`, `False` | **no** (no son `None`, ni lista, ni tupla-con-lista) |

### Orden de intento

📖 `_ordered_providers` (`:249-259`): primero el `provider_id` pedido (o el por defecto), luego
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
| `get_recent_animes` | `:340-342` | **`[]`** |
| `get_anime_info` | `:344-348` | **`None`** |
| `search_animes_by_query` | `:363-368` | **`([], 1)`** ⚠️ el `1` es constante, no la página real |
| `search_animes_by_genres_and_order` | `:370-375` | **`([], 1)`** ⚠️ ídem |
| `get_anime_episode_servers` | `:377-382` | **`[]`** |
| `call_with_fallback` directo | `:334` | **`(None, None)`** |

**El manager nunca lanza excepciones** desde estos wrappers. `UnknownProviderError` solo sale de
`get()` (`:196-203`) y `set_default()` (`:188-191`), que la GUI no usa.

⚠️ Ojo: `set_default()` **sí** la lanza, y `__apply_saved_provider_preference` la captura a propósito
(`main_window.py:270-275`) — una preferencia guardada que apunte a un proveedor retirado del código no
puede impedir arrancar.

### 🆕 El sello del proveedor *(2026-08-16)*

📖 `__stamp_provider` (`:262-283`), llamado desde `call_with_fallback` en `:325`, **justo antes de
devolver**. Escribe el `AnimeProviderId` de quien realmente respondió sobre cada `AnimeInfo` del
resultado.

| Forma del resultado | Método | ¿Se sella? |
|---|---|---|
| `AnimeInfo` suelto | `get_anime_info` | ✅ |
| `List[AnimeInfo]` | `get_recent_animes` | ✅ cada elemento |
| `(List[AnimeInfo], int)` | las dos búsquedas | ✅ cada elemento de la lista |
| `List[ServerInfo]` | `get_anime_episode_servers` | ❌ se ignora en silencio |

**Lo hace el manager y no cada proveedor** por dos motivos: es el único que sabe cuál acabó
respondiendo cuando entra el fallback, y así los proveedores no tienen que acordarse de nada.

*Consecuencia útil*: un `AnimeInfo` ya sabe de dónde viene, así que quien lo abra no tiene que
arrastrar el `provider_id` por parámetro. Es lo que permite que `AnimeWindowViewer` caiga a
`anime_info.provider_id` (`anime_window.py:303`) en vez de asumir el predeterminado — que era lo que
hacía antes al abrir un anime **precargado**, y mentía si lo había servido otro.

### `strict=True`

📖 `:308-309` → `providers_to_try = providers_to_try[:1]`. Desactiva el fallback: solo se intenta el
primer proveedor de la lista ordenada. ✅ Verificado que con `strict=True` sobre un proveedor que
explota, el wrapper devuelve el valor vacío correspondiente sin probar a nadie más.

### Diagnóstico por consola

📖 El manager imprime, y esos mensajes son la mejor pista al depurar:

```
[animeav1] Fallo en 'get_recent_animes': <excepción>              # :317
[animeav1] 'get_recent_animes' no devolvió resultados, probando…  # :321-322
Todos los proveedores fallaron en 'get_recent_animes': <exc>      # :330-331
Ningún proveedor devolvió resultados para 'get_recent_animes'     # :333
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
| 🆕 **Por anime guardado** | `ANIMES.provider_id` de la fila | **activo** | ✅ sí |

**Por qué el ámbito global conserva el fallback**: `ANIMES.anime_id` guarda el *slug* del
proveedor que sirvió cada anime. Si el usuario elige un proveedor distinto y se usara `strict`, el clic
en un anime guardado dejaría de resolver. Con fallback degrada a una petición perdida.

🆕 **Y el nivel «por anime» también lo conserva**, por un motivo distinto: la propiedad de un slug
**caduca**. Hay animes guardados que su proveedor original ya no sirve, así que abrirlos con
`strict=True` convertiría uno que hoy se abre despacio en uno que no se abre.

> 🗑️ **El nivel «puntual, por ficha» ya no existe.** El desplegable de la ficha de detalle, que
> llamaba con `strict=True` y re-resolvía el anime por título, se retiró el 2026-08-06: con el
> desplegable de la sidebar valiendo solo para la sesión, hacía lo mismo con más código.
>
> Lo que **sí** sobrevive de aquel nivel: `get_anime_episode_servers` se sigue llamando con
> `provider_id=self.provider_id, strict=True` desde la ficha, para que los servidores sean los del
> proveedor que la sirvió y no los de un fallback silencioso. Si ese proveedor no da servidores, se
> avisa en vez de pintar un selector vacío.
>
> ✅ **El orden de prioridad ya está implementado** (2026-08-16): desviación del desplegable >
> `provider_id` en BD > pin > registro. Vive en `MainWindow.provider_for_saved_anime()`
> (`main_window.py:345-372`) y lo consume `open_saved_anime()`. Detalle en
> [13 §8](13-selector-de-proveedor.md).

### Identidad de un anime entre proveedores

`AnimeInfo.id` es el *slug* del sitio: el mismo anime es `one-piece-gyojin-touhen` en AnimeAV1 y
`one-piece` en AnimeFLV. **No se puede reutilizar el id al cambiar de proveedor.**
`resolve_anime_in_provider(anime_info, provider_id)` hace la traducción:

1. `search_animes_by_query(título, provider_id=…, strict=True)`.
2. Compara con `title_similarity()`: `normalize_title()` (minúsculas, sin tildes, resto a espacios)
   y, si los **números** del título no coinciden (`title_numbers()`: «2nd», «Season 2» y «II» son
   todos 2), similitud **0**.
3. Coincidencia exacta normalizada → gana; si no, mejor `difflib.SequenceMatcher.ratio()` ≥
   `TITLE_MATCH_THRESHOLD` (**0.75**).
4. `get_anime_info(match.id, provider_id=…, strict=True)`.

Prefiere **no encontrar** a encontrar mal: por debajo del umbral devuelve `None`.

✅ Verificado el 2026-07-30: con un proveedor falso, un título con una letra menos da 0.968 (se acepta)
y un título sin relación 0.35 (se rechaza). Contra AnimeAV1 real, un título largo con puntuación
(`Kimetsu no Yaiba Movie 1: Mugenjou-hen - Akaza Sairai`) resuelve al mismo slug con similitud 1.00.

✅ **Resolución cruzada real, verificada el 2026-08-16** — lo que faltaba desde julio. Con los tres
sitios en marcha:

| Anime (fila del usuario) | Destino | Resultado |
|---|---|---|
| `one-piece-tv` (AnimeFLV) | AnimeAV1 / JKAnime | `one-piece`, similitud **1.00** |
| `ore-dake-level-up-na-ken-season-2-…` | los otros dos | resuelto, similitud **1.00** |
| `one-piece-heroines` | los otros dos | resuelto, similitud **1.00** |

**El umbral 0.75 no ha necesitado moverse.** Los títulos coinciden literalmente entre sitios mucho más
a menudo de lo que se suponía —los tres normalizan igual el título de MyAnimeList—, así que el margen
sobra. Lo que el umbral protege no es la variación ortográfica sino los **falsos positivos de saga**
(«One Piece» vs. «One Piece Film: Red»), y para eso 0.75 ya es holgado.

🔴 **Corrección del 2026-10-26: para las temporadas no era holgado.** Cada temporada es un anime aparte
en los dos sitios, y como texto se parecen más que el umbral: «Kusuriya no Hitorigoto» frente a «… 2nd
Season» da 0.80, y la 2.ª frente a la 3.ª, 0.939. Ningún umbral las separa sin rechazar variantes
legítimas, así que ahora las separan los **números** del título ([trampa 58](10-invariantes-y-trampas.md)).
✅ Relocalizando las 46 filas de la biblioteca en el otro proveedor, **0** cambian de elección
respecto al criterio anterior.

⚠️ **Lo que sigue sin verificarse**: un título que difiera **de verdad** entre sitios (un nombre
localizado frente al romaji). No ha aparecido ninguno en la biblioteca del usuario. Si algún día
falla, el síntoma es «*X no tiene este anime*» sobre algo que sí está: bájale el umbral **con datos**,
no a ojo.

> 📌 `resolve_anime_in_provider` **valida** que el proveedor esté registrado y devuelve `None` con un
> aviso (`:418-420`). Es la excepción entre los métodos del manager, y conviene copiar el patrón:
> los wrappers de `call_with_fallback` no validan y caen en la [trampa 13](10-invariantes-y-trampas.md).

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
| Hay servidores, pero uno que **se veía en la app ahora se abre en el navegador** | el **hoster** cambió, caducó la URL o faltan cabeceras: no es el proveedor | ver §9 |

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
    kwargs.setdefault("timeout", 10)
    response = thread_session().get(url, **kwargs)
    if "charset" not in response.headers.get("Content-Type", "").lower():
        response.encoding = "utf-8"
    return response
```

🆕 *(2026-10-27, B16)* Pide con **`thread_session()`** (`utils/http_session.py`) en vez de
`requests.get`: una `requests.Session` **por hilo**, que reutiliza la conexión TCP + TLS entre las
peticiones de un mismo hilo —la precarga de la portada y el refresco de episodios piden ~20 fichas
seguidas— y **no guarda cookies**, así que cada petición se comporta como el `requests.get` suelto de
antes. El arreglo del charset no cambia: es sobre la respuesta, no sobre cómo se pide
([07 §1c](07-concurrencia-e-hilos.md)).

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
([§2](#2-tabla-comparativa)), así que no se ha diagnosticado.

> **Invariante**: debe haber **exactamente una** petición en `animeav1.py`, la de dentro de `_fetch`.
> Comprobable con `git grep -nE "requests\.(get|post)|\.get\(url" -- src/APIs/animeav1/` → solo
> la línea de `thread_session().get(url, **kwargs)`. *(Hasta el 2026-10-27 era `requests.get`.)*
>
> **Y el código no repara lo ya guardado**: al arreglarlo había 3 filas con la sinopsis rota en la BD
> real, que hubo que re-descargar aparte ([12 §1](12-deuda-tecnica-y-roadmap.md)).

---

## 8. Receta: añadir un proveedor nuevo

Pasos detallados con checklist en [11 §3](11-playbooks.md). Resumen:

0. 🆕 **Añadir su miembro a `AnimeProviderId`** (`models.py:18-31`). Su `value` es lo que quedará
   escrito en la biblioteca de los usuarios: **elígelo bien, porque no se puede cambiar** sin dejar
   filas huérfanas.
1. Crear `src/APIs/<sitio>/__init__.py` (vacío) y `src/APIs/<sitio>/<sitio>.py`.
2. Cabecera de módulo obligatoria ([08 §1](08-convenciones-y-estilo.md)).
3. `class MiSitio(AnimeProvider)` con `PROVIDER_ID` (**el miembro del enum**), `PROVIDER_NAME`,
   `BASE_URL` **y los 5 métodos**. `provider_info()` ya viene implementado.
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

---

## 9. Hosters: de la URL del servidor al vídeo *(2026-10-20)*

Un **proveedor** es el sitio que lista animes y episodios (AnimeAV1, JKAnime…). Un **hoster** es quien
sirve el vídeo: zilla, MP4Upload, playmudos… `ServerInfo.url` es la URL del **reproductor incrustado**
(*embed*) del hoster, no la del vídeo. Pasar de una a otra es **resolver**, y lo hace la capa
`src/APIs/resolvers/`. Hasta el 2026-09-24 la app no resolvía nada: abría el *embed* en el navegador.

### Por qué es una capa aparte y no un sexto método de `AnimeProvider`

- **Un hoster no es de un proveedor.** MP4Upload lo embebe AnimeAV1 y lo embeben también los
  proveedores pendientes (MonosChinos2, TioAnime). La resolución se indexa **por dominio del
  hoster**, así que un resolutor escrito una vez sirve a todos.
- **El *fallback* del manager no pinta nada aquí.** Si un hoster no resuelve, la salida es **el
  navegador**, no preguntar a otro proveedor. Meterlo en el contrato habría arrastrado a la
  resolución la semántica de «vacío = error» del manager ([trampa 12](10-invariantes-y-trampas.md)).
- **`ServerInfo` no cambia**, y se resuelve **al pulsar**, no al listar: varias URLs de medio caducan
  o van atadas a la IP ([trampa 45](10-invariantes-y-trampas.md)).

Las dependencias de la capa están en [01 §2](01-arquitectura.md): solo stdlib, `requests` y ella
misma. **No importa de `APIs.<sitio>` ni de `gui/`.**

### La API

| Pieza | Qué es |
|---|---|
| `MediaSource(url, headers, kind, expires_at)` (`base.py`) | El medio ya resuelto. `headers` hay que mandarlas en **cada** petición del medio, segmentos incluidos; `kind` es `"hls"` o `"mp4"`; `expires_at` es un *epoch* o `None` si la URL **no declara** caducidad |
| `Resolver` (`base.py`) | ABC con dos métodos: `matches(url)` —**sin red**— y `resolve(url)`, que **nunca lanza** y devuelve `None` si no puede |
| `registry.has_resolver(url)` | ¿Hay resolutor para su hoster? **Sin red**: es lo que pone la ↗ a los servidores que se abrirán fuera. Es una promesa *a priori*: uno con resolutor puede acabar igualmente en el navegador |
| `registry.resolve(url)` | El único punto de entrada. **Sin caché a propósito** |
| `url_host(url)`, `BROWSER_USER_AGENT`, `REQUEST_TIMEOUT` = 10 s (`base.py`) | Utilidades comunes. El UA está **duplicado a propósito** respecto a `jkanime.py` |

«Nunca lanza» va en **dos capas**: cada resolutor captura `RequestException`, y `registry` captura
cualquier otra excepción de `matches()` o `resolve()` y devuelve `None`.

### Qué entrega cada hoster

✅ Medido contra los sitios el 2026-09-24 (fase 1), 3 episodios por proveedor; zilla, el 2026-10-20.

| Servidor (proveedor) | URL del *embed* | Resolutor y cómo | Medio | Cabeceras | Caducidad | Cobertura |
|---|---|---|---|---|---|---|
| **HLS** (AnimeAV1) | `player.zilla-networks.com/play/<hash 32 hex>` | `ZillaResolver`, **sintáctico**: `play/` → `m3u8/`, sin pedir la página | HLS **fMP4**, AV1 1080p | `Sec-Fetch-Site: same-origin` ([trampa 43](10-invariantes-y-trampas.md)) | no declarada | 0/3 el 2026-09-24 (**origen caído**, 522); ✅ vuelve el 2026-10-20 |
| **MP4Upload** (AnimeAV1) | `www.mp4upload.com/embed-<id>.html` | `MP4UploadResolver`: baja el *embed* y saca la URL de `player.src({…})` de video.js | MP4 en `aN.mp4upload.com:183`, **AV1 1080p** (no H.264) | UA de navegador + `Referer: https://www.mp4upload.com/` ([trampa 44](10-invariantes-y-trampas.md)) | token de sesión, `None` | 3/3 |
| **Desu**, **Magi** (JKAnime) | `jkanime.net/jkplayer/um?…` y `umv?…` | `JKPlayerResolver`: baja la página (con `Referer: https://jkanime.net/`) y busca el `.m3u8` **en claro** (`hls.loadSource(…)`); si no, dentro de los `atob()` | HLS **MPEG-TS** de `nika.playmudos.com`, H.264 720p, subtítulos incrustados | ninguna | `e=` → **~3 h** | 7/7 |
| **Desuka** (JKAnime) | `jkanime.net/jkplayer/jk?…` | `JKPlayerResolver`: `url: '…'` de la página | MP4 de `jkplayers.com/stream/jkmedia/…` | **ninguna** — con `Referer` da **410** | **atado a la IP** del cliente | 1/1 |

**Sin resolutor** (abren el navegador y llevan ↗): UPNShare, Voe, Mega, YourUpload, DoodStream,
Netu, VidHide y StreamTape en AnimeAV1; Okru en JKAnime. Mega está bloqueado de verdad (cifrado de
extremo a extremo); el resto, **aplazado** ([12 §4](12-deuda-tecnica-y-roadmap.md)).

⚠️ **Okru llega con ruta relativa** (`/jkokru.php?u=…`). Hasta la fase 1 se abría tal cual y el
navegador no sabía resolverla; ahora `JKAnime.get_anime_episode_servers()` la hace absoluta con
`urljoin(f"{BASE_URL}/", …)` («B2» del plan del reproductor, que no es el B2 de [12 §4](12-deuda-tecnica-y-roadmap.md)). Sin un `Okru` real a mano, se verificó con HTML sintético.

⚠️ **Cuesta en CPU**: el AV1 1080p de zilla y MP4Upload no tiene decodificación por hardware en la
máquina de pruebas (GTX 1070) y va por software (dav1d): **0,2-0,33 núcleos**, sin un fotograma
perdido. El H.264 de JKAnime va por `d3d11va`.

### Diagnosticar un hoster que dejó de resolver

Lo primero: **un hoster que falla no da error, abre el navegador** —es la degradación diseñada—.
Lo que dice qué ha pasado es **la consola** (con `python src/app.py`; el `.exe` no la tiene,
[trampa 18c](10-invariantes-y-trampas.md)) y **cuánto tarda en caer**:

| Lo que ves | Lo que dice la consola | Causa probable | Qué hacer |
|---|---|---|---|
| Cae al navegador **al instante**, sin «Cargando» apreciable | `[zilla] URL de embed sin hash reconocible` · `[mp4upload] El embed no trae la URL del vídeo` · `[jkplayer] El reproductor um no trae ninguna URL .m3u8` | cambió el formato del *embed* o de su página | bajar **una vez** la página y comparar con la regex del resolutor ([09 §6h](09-verificacion-y-pruebas.md)) |
| Igual, pero | `No se pudo descargar …` con **403** | Cloudflare | **parar**: no reintentar en bucle (la IP ya se bloqueó una vez, el 2026-08-23) |
| «Cargando» un instante y navegador | `mpv no pudo reproducir el medio (error …)` | el medio rechaza la petición: cabeceras o caducidad | [trampas 43-45](10-invariantes-y-trampas.md) |
| «Cargando» **~20 s** y navegador | idem, tras el `network-timeout` de 15 s | el origen del hoster está **caído** | esperar; no es el resolutor |
| «Cargando» **30 s** y navegador | `El medio no ha empezado a verse en 30 s: …` y `[reproductor] …: El servidor tarda demasiado en entregar el vídeo` | el hoster **responde, pero lento** (zilla, 2026-10-20: ~70 s hasta abrir) | ya cae solo al navegador; si se repite, el hoster va lento ese día ([trampa 54](10-invariantes-y-trampas.md), B15 cerrada) |
| **Todos** los servidores al navegador | `No se pudo cargar libmpv…` | falta la DLL | [trampa 18f](10-invariantes-y-trampas.md) |
| Se ve, pero **a tirones** | — (mpv: `paused-for-cache`) | el hoster sirve por debajo del bitrate (MP4Upload, 110-260 KB/s el 2026-09-24) | nada en la app |
| Navegador tras ver **un buen rato** | `El medio terminó en … : se trata como un corte del servidor` | el stream se cortó antes del final | [trampa 48](10-invariantes-y-trampas.md): no marca el episodio |

**Regla de oro**: se arregla **el resolutor de ese hoster**, no el resto de la capa. Y añadir uno
nuevo es [11 §9](11-playbooks.md).
