# Fase 1 — Capa de resolución `APIs/resolvers/`

| | |
|---|---|
| **Objetivo** | De la URL de *embed* a la URL del medio, con sus cabeceras. Capa nueva, **sin GUI**: al terminar, un script resuelve y descarga bytes de vídeo de los 4 hosters que cubren el 100 % |
| **Investigación** | §3 (matriz proveedor × hoster), §4.1 a §4.5 (las fichas de resolución), §4.6 (los dos bugs latentes), §7 (dónde encaja en la arquitectura) |
| **Estrena** | `MediaSource`, `Resolver`, el registro y 3 resolutores |
| **Toca** | `src/APIs/resolvers/` (nuevo: `__init__.py`, `base.py`, `zilla.py`, `jkplayer.py`, `mp4upload.py`, `registry.py`), `src/APIs/jkanime/jkanime.py` (B2), `src/gui/anime_window.py` (B1) |
| **No toca** | `APIs/common/animeProviderMgr.py`, `APIs/common/models.py`, `animesPersistence.py`, `gui/` salvo las 3 líneas de B1 |
| **Riesgo** | Medio — el código es sencillo; lo frágil son los sitios |
| **Depende de** | Nada de la fase 0. **Se puede hacer aunque mpv se caiga**: la contingencia usa la misma capa |

---

## 🔴 Lo que NO se toca en esta fase

La investigación (§7) cerró estas cuatro y no se reabren:

- **`AnimeProvider` NO gana un sexto método abstracto.** Son 5, y un sexto obligaría a implementarlo
  en las tres subclases, incluida **AnimeFLV, que está muerta** y necesitaría un stub. Además la
  resolución se indexa por **dominio del hoster**, no por proveedor.
- **`ServerInfo` no cambia.** Sigue siendo `(server, url)`.
- **`AnimeProviderManager` ni se entera.** `call_with_fallback()` prueba **otros proveedores**; aquí
  no tiene sentido (si MP4Upload cae, JKAnime no sirve ese anime). El manager conserva su invariante
  de no propagar excepciones porque **ni siquiera participa**.
- **No se resuelve al listar servidores.** Resolver los 5 servidores por adelantado multiplica las
  peticiones por cinco y los tokens de JKAnime caducan en ~3 h. Se resuelve **al pulsar play**, que
  es de la fase 3.

---

## Antes de empezar

Lectura obligatoria, en este orden:

1. [`docs/10-invariantes-y-trampas.md`](../../docs/10-invariantes-y-trampas.md) — las **35**.
2. [`docs/01-arquitectura.md`](../../docs/01-arquitectura.md) — **qué puede importar qué**. La capa
   nueva vive bajo `APIs/` y **no puede importar de `gui/`**.
3. [`docs/05-proveedores-y-scraping.md`](../../docs/05-proveedores-y-scraping.md) §3b — cómo parsea
   JKAnime y cómo se diagnostica un sitio que cambió.
4. [`docs/08-convenciones-y-estilo.md`](../../docs/08-convenciones-y-estilo.md) — cabecera
   obligatoria y plantillas copiables.
5. De la investigación: **§4.1, §4.2, §4.3 y §4.4** (una ficha por resolutor) y **§4.6** (los bugs).

Y leer `src/APIs/common/models.py` entero y `get_anime_episode_servers()` de
`src/APIs/jkanime/jkanime.py` y de `src/APIs/animeav1/animeav1.py`.

**Trampas que van a morder en esta fase:**

- 🔴 **La política de cabeceras es POR HOSTER y no admite un valor por defecto global.** MP4Upload
  necesita `Referer: https://www.mp4upload.com/` (el del **propio hoster**, no el del sitio que lo
  embebe) y **jkplayers.com devuelve 410 Gone si le mandas `Referer`**. Un `Referer` «por si acaso»
  en la capa base rompe un hoster de cada dos.
- ⚠️ **`Sec-Fetch-Site: same-origin` solo hace falta en los segmentos de zilla**, no en el playlist,
  y **solo vale ese valor exacto**. Va en `MediaSource.headers` igualmente: quien reproduce no
  distingue playlist de segmento.
- 🔴 **Las URLs de JKAnime caducan (~3 h) y las de jkplayers están atadas a la IP** (✅ la URL
  incrusta la IP pública del cliente). Consecuencia: `expires_at` en `MediaSource`, **no cachear
  entre equipos**, y resolver desde la misma máquina que reproduce.
- ⚠️ **El servidor `Okru` de JKAnime devuelve una URL relativa** (`/jkokru.php?u=…`). Es el bug B2.
- **`Desu` y `Magi` son el mismo stream** (✅ `um` y `umv` devuelven la misma URL de medio): no son
  dos fuentes, así que no vale como «segundo intento».

---

## Pasos

### Paso 1.1 — `base.py`: `MediaSource` y `Resolver`

Módulo nuevo con la cabecera obligatoria. Dos tipos y nada más:

```python
@dataclass
class MediaSource:
    url: str
    headers: dict[str, str]          # vacío si el hoster no pide ninguna
    kind: str                        # 'hls' | 'mp4'
    expires_at: float | None = None  # epoch; None = no caduca (zilla)

class Resolver(ABC):
    @abstractmethod
    def matches(self, url: str) -> bool: ...
    @abstractmethod
    def resolve(self, url: str) -> MediaSource | None: ...
```

- `matches()` decide **por dominio**, que es como se indexa esto (§7). Un resolutor de MP4Upload
  servirá gratis a MonosChinos2 y TioAnime cuando lleguen.
- 🔴 **`resolve()` nunca lanza**: devuelve `None`. Es la misma invariante que ya tiene el manager, y
  lo que hace posible la regla 2 del plan (caer al navegador).
- Las peticiones HTTP con el mismo estilo que ya usan los proveedores (`requests` + `User-Agent` de
  navegador). **Sin reintentos en bucle** (regla 6).

### Paso 1.2 — `zilla.py` — el servidor `HLS` de AnimeAV1 ⭐

**El más importante: cubre AnimeAV1 entero (7/7) y la receta es una sustitución de cadena.**

- `matches`: host `player.zilla-networks.com`.
- `resolve`: `play/<hash32hex>` → `m3u8/<hash32hex>`. Validar que el último segmento del path mide
  **32 caracteres**; si no, devolver `None` (es lo que hace el propio bundle del sitio).
- `headers`: `{"Sec-Fetch-Site": "same-origin"}`. `kind='hls'`. `expires_at=None` — ✅ la URL es
  determinista, sin token ni expiración.
- **No hace falta pedir la página del embed**: la receta es sintáctica. Menos peticiones, menos
  Cloudflare.

### Paso 1.3 — `jkplayer.py` — `Desu`/`Magi` y `Desuka`/`Xtreme S`

Un módulo, dos rutas del **mismo dominio** (`jkanime.net`), que se comportan distinto:

- **`/jkplayer/um` y `/umv`** (7/7 en JKAnime): GET con
  `Referer: https://jkanime.net/<slug>/<ep>/` → HTML de ~17 KB. La URL del medio aparece **dos
  veces**: dentro de un `atob('…')` y sin codificar en `hls.loadSource(...)`. **Implementar los dos
  caminos**: regex sobre `https?://…\.m3u8[^\s'"<>]*` y, si falla, `atob()` + base64. Si uno se
  rompe, el otro sigue. `kind='hls'`, `headers={}`, `expires_at` del parámetro `e=` de la URL.
- **`/jkplayer/jk`** (2/7): la URL sale en claro en `url: '…'` → `jkplayers.com/stream/jkmedia/…`.
  `kind='mp4'`, `headers={}` y 🔴 **jamás `Referer`**: rompe la petición con **410 Gone**. Dejarlo
  escrito en un comentario del código, no solo aquí.
- ⚠️ El GET al redirector sí necesita `User-Agent` de navegador — es lo que 📖 `jkanime.py` ya hace
  en `_fetch()`; reutilizar ese criterio, no inventar otro.

### Paso 1.4 — `mp4upload.py` — la red de seguridad de AnimeAV1

- `matches`: host `mp4upload.com` (con y sin `www.`).
- `resolve`: GET al embed → la fuente está en claro en la inicialización de video.js
  (`player.src({ type: "video/mp4", src: "https://a4.mp4upload.com:183/d/<token>/video.mp4" })`).
  Cloudflare Rocket Loader renombra los `type` de los `<script>` pero **no ofusca el contenido**.
- 🔴 `headers`: `User-Agent` **y** `Referer: https://www.mp4upload.com/`. Con el referer de
  `animeav1.com` da **403**; con el suyo, **206**.
- `kind='mp4'`. ⚠️ Tratar como **no cacheable**: el token del path parece de sesión.
- ⚠️ Sirve en el **puerto no estándar 183**, que algunas redes bloquean. Si el `GET` no conecta,
  `None` y a otra cosa — no es un bug del resolutor.

### Paso 1.5 — `registry.py`

- `resolve(url) -> MediaSource | None`: recorre los resolutores registrados y devuelve el primero
  cuyo `matches()` diga que sí. Si ninguno casa, o si el que casa devuelve `None`, **`None`**.
- Registro explícito en el módulo, como hace `MainWindow` con los proveedores. El orden no importa:
  los `matches()` son disjuntos por dominio.
- **Sin caché.** Dos de los cuatro hosters caducan y uno está atado a la IP; una caché aquí es un
  bug esperando fecha. Si alguna vez se quiere, el sitio es `expires_at`, que ya está en el tipo.

### Paso 1.6 — Los dos bugs de §4.6

Van aquí porque los dos son de una línea y los dos se manifiestan **hoy**:

- **B1 · Servidores duplicados se pierden.** 📖 `anime_window.py:1716` construye
  `server_url_map = {s.server: s.url for s in servers_info}`. ✅ En JKAnime, One Piece ep 1 devuelve
  **5 servidores con solo 3 nombres** (`Desu`, `Magi`, `Desu`, `Magi`, `Desuka`): el dict **descarta
  2 de 5** y `CTkSegmentedButton` con valores repetidos es de comportamiento indefinido.
  Deduplicar **antes** del dict, numerando los repetidos («Desu 2») o quedándose con el primero de
  cada nombre — pero de forma **explícita**, no por accidente del dict.
- **B2 · URL relativa a `webbrowser.open()`.** ✅ `Okru` devuelve `/jkokru.php?u=…`, sin esquema ni
  host, y 📖 `__play_video()` se lo pasa tal cual. Falta `urljoin(BASE_URL, url)` en
  📖 `jkanime.py:246` (dentro de `get_anime_episode_servers()`), **en el proveedor**, que es donde
  se conoce la `BASE_URL`.

---

## Terminado cuando

- [ ] Los 6 ficheros de `APIs/resolvers/` existen, con cabecera de módulo correcta.
- [ ] `registry.resolve()` devuelve un `MediaSource` para zilla, `um`/`umv`, `jk` y mp4upload, y
      **`None`** para Mega, Voe, Byse y Okru — sin lanzar en ninguno de los ocho casos.
- [ ] Las cabeceras son **las de cada hoster**: `Sec-Fetch-Site` solo en zilla, el `Referer` propio
      solo en mp4upload, y **`{}` en jkplayers** (con el comentario del 410 en el código).
- [ ] B1 arreglado: los 5 servidores de One Piece ep 1 en JKAnime **se ven los 5**.
- [ ] B2 arreglado: la URL de `Okru` llega absoluta.
- [ ] `git grep -n "resolvers" -- src/gui/` no devuelve nada: **la GUI todavía no la usa**.
- [ ] La app sigue arrancando y pulsar un servidor sigue abriendo el navegador, como hoy.

## Verificación

**Sin GUI**, con un script del scratchpad (regla 7 del plan: los desechables no van al repo):

1. Recorrer **3 animes × 2 proveedores** (AnimeAV1 y JKAnime), pedir sus servidores y resolver cada
   uno con el registro.
2. Para cada `MediaSource`, un `GET` con `Range: bytes=0-2047` **y sus cabeceras**, comprobando:
   - **200 o 206**;
   - el *magic number*: `#EXTM3U` en los HLS, `ftyp` en los MP4;
   - y en el HLS de zilla, bajar además **un segmento** para comprobar que la cabecera hace su
     trabajo — es el único sitio donde el playlist es abierto y los segmentos no.
3. La prueba negativa: el mismo segmento de zilla **sin** `Sec-Fetch-Site` tiene que dar **403**, y
   `jkplayers` **con** `Referer` tiene que dar **410**. Si las dos negativas no fallan, la capa no
   está haciendo lo que dice.

🔴 **Espaciar las peticiones** y no reintentar (regla 6). Con 3 animes basta; no hacen falta 7.

Anotar cuántos hosters resolvieron y cuáles no: es la foto de cobertura del día, y estos sitios
cambian.

## Qué anotar en ESTADO.md

Cobertura real medida (hoster por hoster, con la fecha) · qué anclaje funcionó en JKAnime (regex o
`atob`) · si alguna cabecera cambió respecto a la investigación · cómo se resolvió B1 (numerar o
quedarse con el primero) · y cualquier hoster que ya no resuelva, que **no es un fallo de la fase**
sino el dato que la fase existe para descubrir.
