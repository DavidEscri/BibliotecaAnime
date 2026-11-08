# 10 — Invariantes y trampas

| | |
|---|---|
| **Fecha** | 2026-11-08 · rama `feature/reproductor-uso-diario` · sobre **`2578546`** |
| **Cubre** | los **43** módulos con contenido de `src/` (42 + `app.py`) + `MiBibliotecaAnime.spec` + `requirements.txt` |
| **Última revisión** | 2026-11-08 (**depuración**): se borran las trampas que ya no pueden darse con el código actual, las resueltas cuya causa sigue viva —la librería, Windows o los sitios— pasan a **reglas** condensadas (R1-R24) y todo se renumera: **54 trampas y 24 reglas**. La numeración anterior (1-84) está en el historial de git, en `2578546`; los planes de `.claude/plan-*` la siguen usando |

Procedencia: ✅ verificado en ejecución · 📖 leído en código · ⚠️ sin verificar.

> **Este es el documento que hay que leer antes de tocar nada.** Cada trampa es «si tocas esto, se
> rompe aquello», con el **síntoma observable** que verás cuando lo rompas. Las **reglas** del final
> son problemas que el código ya evita, pero que vuelven en cuanto se escribe código nuevo sin
> tenerlos en cuenta.

---

## Persistencia

### 1. El orden de `AnimeField` debe coincidir con el de las columnas físicas 📖

**Por qué**: todas las consultas son `SELECT *` y `SqlUtils.query_sql` (`utils/db/sqlite.py:122-144`)
empareja `fila[i] → FIELDS[i]` **por posición**, no por nombre.

**Si lo rompes**: reordenar `AnimeField` (`animesPersistence.py:28-57`), o insertar un miembro en
medio, desplaza todos los valores posteriores.

**Síntoma**: ningún error. Títulos donde deberían ir sinopsis, `is_favourite` con el valor de
`last_watched_episode`, JSON que no parsea y géneros que salen `[]`.

**Cómo comprobarlo**: `PRAGMA table_info(ANIMES)` y comparar con `AnimesPersistence.FIELDS`
([09 §3](09-verificacion-y-pruebas.md)). ✅ Hoy coinciden.

> ✅ **Mitigada desde 2026-07-30**: `validate_db_integrity()` (regla R1) detecta el desorden y
> reconstruye la tabla realineándola con el orden declarado, copiando los datos por nombre de columna.
> El invariante sigue vigente — el orden de `AnimeField` **es** el contrato — pero reordenarlo ya no
> corrompe una BD existente: se corrige en el siguiente arranque.

---

### 2. `watched_episodes` se guarda como rangos comprimidos ✅

**Formato**: `{1,2,3,5,9}` → `[[1,3],[5,5],[9,9]]` (`_episodes_to_ranges:210-224`).

**Nunca escribas ese campo a mano.** Un elemento con longitud ≠ 2 se **descarta en silencio**
(`_ranges_to_episodes:233-234`).

**Síntoma**: episodios vistos que desaparecen sin error al recargar la ficha.

**Además**: `last_watched_episode` se recalcula siempre como `max(watched)` (`:409`); si escribes uno
a mano, el siguiente `update_watched_episodes` lo pisa.

**Y es lo único irrecuperable de la biblioteca**: título, póster, sinopsis, géneros y episodios se
vuelven a bajar de la red; esto no. Por eso `migrate_anime_identity` lo conserva
([04 §8](04-modelo-de-datos.md)).

---

### 3. `episodes` se guarda **invertido** y no se des-invierte al leer ✅

`to_db_dict:90` hace `list(reversed(...))`; `update_anime_episodes:519-520` hace `[::-1]`;
`from_db_dict` **no** deshace nada.

✅ Verificado: entrada `[1..10]` → BD `[10..1]` → leído `[10..1]`.

**Agravante**: el orden depende del **proveedor**. AnimeAV1 devuelve episodios **ascendentes**
(`animeav1.py:227`), AnimeFLV **descendentes** (`animeflv.py:222-223`). Es decir, el mismo anime
guardado desde un proveedor u otro queda **al revés** en BD.

**Síntoma**: `anime_record.episodes[0]` es el último episodio, no el primero. Lógicas de «por dónde
voy» que salen invertidas.

⚠️ **Ampliación 2026-08-16 — la asimetría muerde al escribir código nuevo.** Ahora hay dos orígenes
para la lista de episodios y **solo uno de ellos debe invertirse**:

| Origen | ¿Invertir? | Por qué |
|---|---|---|
| `anime_info.episodes` (recién bajado de la red) | **sí** | Es el sentido normal de `to_db_dict` |
| `record.episodes` (releído de la BD) | **no** | **Ya viene invertido**; invertirlo otra vez lo deja al derecho, que aquí es «al revés» |

`migrate_anime_identity` (`animesPersistence.py:487-488`) es el primer sitio que mezcla los dos, y por
eso lo hace explícito: `new_episode_ids[::-1] if new_episode_ids else record.episodes`. Cualquier
método nuevo que caiga a «lo que ya había» tiene el mismo problema.

**Síntoma**: migrar un anime a otro proveedor que no devuelve episodios deja la lista **invertida
respecto a antes**, y la ficha muestra el episodio 1 arriba donde antes estaba el último. Sin error.

---

### 4. `update_*` devuelve `True` aunque no modifique ninguna fila ✅

`SqlUtils.update_sql` (`sqlite.py:106-120`) **nunca consulta `cursor.rowcount`**. `True` significa «el
SQL se ejecutó sin excepción».

| Método | Anime inexistente |
|---|---|
| `update_watched_episodes` | `False` ✅ (comprueba antes) |
| `update_anime_to_not_watching` / `not_finished` | `False` ✅ |
| `update_anime_provider_id` / `migrate_anime_identity` | `False` ✅ (2026-08-16, comprueban antes) |
| `update_anime_episodes` | ⚠️ **`True`** |
| `update_anime_to_not_favourite` / `not_pending` | ⚠️ **`True`** |

**Esto contradice `CLAUDE.md`**, que afirma que todos devuelven `False`.

**Síntoma**: código que confía en el `bool` cree que guardó y no guardó nada.

---

### 5. Marcar episodios de un anime sin estado no persiste nada ✅

`update_watched_episodes` devuelve `False` sin escribir si el anime no está en `ANIMES`
(`animesPersistence.py:358`). Un anime solo entra en BD al pulsar uno de los 4 botones de estado
(`_set_status:483-491`).

**Síntoma**: el usuario marca episodios en la ficha de un anime recién descubierto, sale, vuelve, y
los switches están todos apagados. **Sin ningún mensaje.**

---

## Ficha de detalle

### 6. Solo se muestran los **25** primeros episodios 📖

`EPISODES_SHOWN = 25` (`anime_window.py`): la lista enseña los 25 primeros **tal y como llegan** del
proveedor.

**Interactúa con la trampa 3**: ✅ con AnimeAV1 (ascendente) verás los episodios **1-25**; con
AnimeFLV (descendente) los **25 más recientes**. El mismo anime, dos cortes distintos.

**Síntoma**: en un anime de 1171 episodios no hay forma de llegar al 600 salvo por el buscador de
episodios (`__search_episodes`), o abriendo la ficha por ese episodio desde «Viendo» o
«Pendientes», que lo enseña solo con sus botones de navegación.

---

### 7. El marcado de episodios es acumulativo; el desmarcado, unitario 📖

`__set_episode_watched()` (`anime_window.py`), al que llegan el interruptor de cada episodio, el final
de un episodio en el reproductor y «Siguiente episodio» —el de la barra y el de la columna, que dan
por visto el que se deja—:

- **Marcar** el episodio N marca **todos los ≤ N en orden real ascendente** —no en el de la lista,
  que depende del botón de orden— y **conserva** los > N que ya estaban vistos en BD.
- **Desmarcar** quita **solo** ese episodio.

**Si lo cambias**: se pierde el caso de uso principal («voy por el 340»), que evita 340 clics, y
terminar o saltar un episodio en el reproductor dejaría huecos en lo visto.

**Solo escribe si el anime ya tiene fila** (trampa 5): el reproductor nunca crea una.

---

## Proveedores

### 8. `__init_subclass__` exige los 4 atributos a **toda** subclase ✅

La condición es `if ABC not in cls.__bases__` (`animeProviderMgr.py:52`), y solo `AnimeProvider`
lista `ABC` entre sus bases directas. Desde el 2026-10-28 (0.5.0) son **cuatro**: `PROVIDER_ID`,
`PROVIDER_NAME`, **`PROVIDER_SHORT_NAME`** (las siglas, `AV1`/`JK`/`FLV`) y `BASE_URL`.

**Si lo rompes**: crear una base intermedia (`class ProveedorHTMLBase(AnimeProvider)`) sin esos
atributos, o un proveedor nuevo sin `PROVIDER_SHORT_NAME`, **impide importar el módulo**.

**Síntoma**: `NotImplementedError: ProveedorHTMLBase debe definir el atributo de clase 'PROVIDER_ID'`
(o `'PROVIDER_SHORT_NAME'`) **al importar**, no al usar.

`RELATIONS_CARRY_FORMAT` **no** está en la lista: es opcional y vale `False` por defecto
([05 §1](05-proveedores-y-scraping.md)).

---

### 9. El fallback trata «vacío» igual que «error» ✅

`__is_empty_result` (`:231-240`): `None`, `[]` y `([], N)` cuentan como vacío → se prueba el siguiente
proveedor.

**Consecuencias**:

- Una búsqueda **legítimamente sin resultados** desencadena una petición extra a cada proveedor.
- La GUI **no distingue** «sitio caído» de «no hay resultados»: en ambos casos recibe `[]`.
- El `last_page` de una tupla vacía se **descarta** (`([], 7)` → se ignora el 7).
- Los wrappers devuelven `([], 1)` con **`1` constante** (`:314`, `:320`) → la paginación se colapsa.

---

### 10. `provider_id` desconocido + `strict=True` usa el primer proveedor registrado ✅

`_ordered_providers` (`:249-259`) no valida el `provider_id`: si no está registrado, simplemente no
antepone a nadie. Con `strict=True` se toma `[:1]` → **el primero por orden de registro**.

**Síntoma**: pides datos «solo de JKAnime», JKAnime no está registrado, y recibes datos de AnimeAV1
sin ningún aviso. `get()` sí lanza `UnknownProviderError` (`:196-203`) — pero los wrappers no usan
`get()`.

✅ **Mitigada en parte desde 2026-08-16**, no resuelta. Al pasar `PROVIDER_ID` de cadena a
`AnimeProviderId` (`models.py:18`), el error frecuente —una errata (`"animeflb"`), o un id que nunca
existió— ya no llega hasta aquí: `AnimeProviderId("animeflb")` lanza `ValueError` en el sitio donde se
escribió. Lo que **sigue vivo** es el caso real: un miembro del enum que existe pero **no está
registrado** en este arranque. Eso pasa el tipado y cae otra vez en el primer proveedor, en silencio.

**Dónde importa hoy**: `resolve_anime_in_provider` sí valida y devuelve `None` con un aviso; desde
el 2026-10-28 también **`get_anime_relations`** y **`genre_filters`**, los dos wrappers que trajo la
0.5.0. Los wrappers de `call_with_fallback`, no. Si añades un método nuevo al manager, valida como
esos tres.

---

## Imágenes y empaquetado

### 11. La purga de pósters borra lo que no está en la lista actual ✅

`download_animes_poster:97-105` y `download_images_progress:155-163` eliminan **todo** fichero del
directorio que no corresponda a un anime de la lista recibida.

**Consecuencias verificadas**:

- ✅ `resources/images/search` se **vacía en cada búsqueda** (`searchAnimes.py:236`).
- ✅ `load_image` (`utils.py:181`) deja el fichero **abierto** (PIL perezoso) → `os.remove` lanza
  `PermissionError` en Windows mientras el `CTkImage` viva. Está capturado, así que solo imprime.
- ✅ En la caché real del usuario hay un huérfano `Chi.` (0 bytes) que `os.listdir` lista pero
  `os.remove` no puede borrar → **aviso en cada arranque**:
  `No se pudo borrar la imagen Chi.: [WinError 2]…`
  ⚠️ El origen exacto de ese fichero no está verificado.

**Si llamas a estas funciones con una lista parcial, borras el resto de la caché.**

---

### 12. Trampas de empaquetado y de entorno

**a) Todo módulo nuevo bajo `src/` va en `hiddenimports`** 📖

Un módulo de `src/` sin declarar compila sin error y revienta con `ModuleNotFoundError` **al
arrancar el `.exe`**, no al compilar. Hoy son 43 nombres: los 42 módulos de `src/` —todos salvo
`app.py`, que es el script de entrada— y `mpv`, que `load_mpv()` importa dentro de la función.

**b) `console=False` en el `.spec`** 📖: todos los `print` desaparecen en el `.exe`. Para
depurar el empaquetado, cambia temporalmente a `console=True`.

**c) `datas` lleva solo `resources/images/utils`** ✅

No lleva la BD ni las carpetas de pósters: hasta la 0.2.0 las empaquetaba, y el `.exe` distribuía
la biblioteca y las preferencias del desarrollador. Parecían obligatorias porque **PyInstaller
ignora en silencio una entrada de `datas` que apunta a una carpeta vacía**, así que la única forma
de que aparecieran era enviarlas llenas. No hacen falta: la app las crea al arrancar y
`find_cached_poster_path()` salta las que no existen. No las vuelvas a añadir.

**d) Los destinos de `datas` se resuelven dentro de `_internal/`, no junto al `.exe`** ✅

**Solución aplicada** (`MiBibliotecaAnime.spec`, tras `COLLECT`): el `.spec` es Python y se ejecuta
de arriba abajo, así que el código posterior a `COLLECT` corre con la carpeta ya montada y puede
copiar al primer nivel usando la variable `DISTPATH` que inyecta PyInstaller:

```python
_dist_dir = os.path.join(DISTPATH, f'MiBibliotecaAnime_v{APP_VERSION}')
for _legal_file in ('LICENSE', 'LEEME.txt', 'THIRD-PARTY-NOTICES.txt'):
    shutil.copy(_legal_file, _dist_dir)
```

⚠️ **Importa más allá de la comodidad**: esos tres ficheros son los que hacen que la distribución
binaria cumpla la GPL-3.0 (§4 avisos, §6 oferta de código fuente) y las licencias MIT/BSD/Apache/MPL
de las dependencias. En `_internal/` no cumplirían su función.

**e) `libmpv-2.dll` va en `binaries` con destino `vendor`, y `python-mpv` no la busca ahí** ✅

**Por qué**: `python-mpv` localiza la DLL con `ctypes.util.find_library`, que en Windows **solo mira
`%PATH%`**, no la carpeta del script ni la del `.exe`. Sin ella en la ruta, `import mpv` lanza
`OSError: Cannot find mpv-1.dll, mpv-2.dll or libmpv-2.dll`. Por eso `load_mpv()`
antepone `get_resource_path("vendor")` a `os.environ["PATH"]` —y la pasa a
`os.add_dll_directory()` para sus dependencias— **antes** del `import`.

Y en el `.exe` esa ruta es `_internal/vendor`, por la misma mecánica que la **12d**: el destino de
`binaries` cae dentro de `_internal/`. De ahí que el `.spec` diga `('vendor/libmpv-2.dll', 'vendor')`
y no `'.'`, como proponía el plan. Con `'.'` la DLL acabaría en `_internal/` a secas y `load_mpv()` no
la vería sin tocar `src/` (⚠️ esa variante no se compiló).

**Síntoma observable**: **ningún error**. El `.exe` arranca perfecto, la ficha monta el panel del
reproductor y **todos los servidores acaban en el navegador** con la tarjeta «No se ha podido cargar
aquí». `load_mpv()` no lanza —es la degradación diseñada— y su `print` no se ve, porque el `.exe` va
con `console=False` (**12b**). Parece que han caído todos los hosters a la vez.

**Además**: la DLL **no está en el repositorio** (120 MB, por encima del límite de GitHub; `vendor/`
está en `.gitignore`). Un clon limpio no puede compilar sin el paso 4 del `README.md`, y por eso el
`.spec` **para con `SystemExit`** si falta, en vez de compilar un `.exe` que lo abriría todo fuera.

**Cómo comprobarlo**: con el `.exe` reproduciendo, `Get-Process -Module` del proceso tiene que
listar `…\_internal\vendor\libmpv-2.dll`. ✅ Verificado el 2026-10-20 desde una carpeta fuera del
repo y **sin la DLL en `%PATH%`**.

⚠️ **Esa copia en `_internal/vendor` es nueva en cada compilación**, y su primera carga tarda segundos
porque el antivirus la revisa: es la [regla R24](#r24-load_mpv-solo-desde-un-hilo-daemon).

---

## Proveedor seleccionable

### 13. En la ficha, `anime_info.id` **no** es la clave de la biblioteca ✅

`AnimeWindowViewer` maneja **dos identidades** del mismo anime, y confundirlas **escribe filas
duplicadas en la biblioteca real del usuario**:

| Atributo | Qué es | Puede diferir del otro |
|---|---|---|
| `self.anime_info.id` / `self.provider_id` | identidad de **visualización**: quién sirvió esta ficha | **sí** |
| `self.persistence_anime_id` / `persistence_provider_id` / `persistence_poster_url` | identidad de **persistencia**: la fila guardada | **no, nunca cambia mientras la ficha está en pantalla** |

`AnimeInfo.id` es el slug del sitio, no un identificador universal: el mismo anime es `one-piece` en
AnimeAV1 y `one-piece-tv` en AnimeFLV.

**Regla**: en `anime_window.py`, **toda** llamada a `animes_persistence`, a
`download/move_anime_poster_by_status` y a `sync_saved_posters_async` usa `self.persistence_anime_id` o
`self.__persistence_anime_info()`. Nunca `self.anime_info` a secas.

**Síntoma si se incumple**: pulsas «Añadir a favoritos» y el anime aparece **dos veces** en la vista
de favoritos, con dos pósters en disco; o pulsas «Eliminar de favoritos» y no desaparece, porque se ha
desmarcado una fila distinta de la que ve la vista.

#### Tres formas de partir la identidad

Con la columna `provider_id` hay **tres** formas de partir la identidad, no una:

| Cómo | Slugs | Quién lo provoca |
|---|---|---|
| **Fallback** | iguales | nadie: el proveedor de la fila falló y respondió otro |
| **Desviación del desplegable** | **distintos** | el usuario, eligiendo otro proveedor en la sidebar |
| **Migración a medias** | — | imposible hoy: `__confirm_and_migrate` reconstruye la ficha entera al terminar |

La segunda es nueva y es la peligrosa: `open_saved_anime()` **re-localiza el anime por título** en el
proveedor elegido (`anime_window.py:212-234`), así que `anime_info.id` es directamente el slug de otro
sitio.

> 🔴 **Esto reintrodujo el bug una vez, durante la propia fase 4.** `open_saved_anime()` construía el
> viewer con el `AnimeInfo` resuelto y **sin** pasar la fila, así que la identidad de persistencia
> pasaba a ser el slug desviado: la ficha mostraba el anime como no guardado y cualquier botón de
> estado insertaba una **fila duplicada**. Se detectó al implementar la fase 6 y se arregló añadiendo
> el parámetro `anime_record` al constructor (`:232-233`). ✅ Reproducido en `test_fase6.py` §6b: con
> el constructor antiguo, **un solo clic** crea la fila duplicada.

**La regla nueva**: quien abra una ficha de un anime que **puede venir de otro proveedor** está
obligado a pasar `anime_record=`. Sin él, `AnimeWindowViewer` asume que lo que ve es lo que hay
guardado — cierto al abrir desde recientes o desde una búsqueda, falso al abrir desde la biblioteca.

**Ahora se ve en pantalla**: la ficha muestra `⚠ En tu biblioteca: <proveedor>` en ámbar cuando las dos
identidades no coinciden ([06](06-gui-y-vistas.md)). Es la primera vez que esta trampa tiene un
síntoma visible **antes** de romper algo.

✅ Verificado el 2026-07-30 sobre una copia de la BD real (25 filas): tras cambiar de proveedor y
pulsar los 8 botones de estado, siguen habiendo 25 filas y ninguna con el slug del otro proveedor.
✅ Re-verificado el 2026-08-16 con las tres formas de partir la identidad (`test_fase6.py`, 105
comprobaciones). Ver [13 D5](13-selector-de-proveedor.md) y [09](09-verificacion-y-pruebas.md).

---

## Proveedores concretos

### 14. En JKAnime, el `<img>` de la portada lleva **dos** imágenes ✅

Las tarjetas de la portada (`div.card`) son de **episodio**, no de anime, y su `<img>` trae dos
rutas distintas:

| Atributo | Contenido |
|---|---|
| `src` | captura del episodio (`.../animes/video/image/jkvideo_*.jpg`) |
| `data-animepic` | **póster del anime** (`.../animes/image/<slug>.jpg`) |

Leer `src`, que es lo que haría cualquiera copiando el patrón de los otros dos proveedores, llena la
biblioteca de **fotogramas sueltos** en vez de carátulas.

**Síntoma**: los animes recientes se ven con imágenes borrosas y apaisadas, distintas cada vez que
sale un episodio nuevo, y el póster cambia solo al recargar. Ningún error por consola.

📖 `jkanime.py` lo resuelve con `img_el.get("data-animepic") or img_el.get("src", "")`. En la
**búsqueda** el problema es otro: ahí el póster no está en un `<img>` sino en el atributo
`data-setbg` de `.anime__item__pic`.

**Invariante**: al añadir un proveedor, comprobar de dónde sale el póster de un listado **mirando la
URL resultante**, no solo que la imagen no esté vacía.

---

### 15. Las rejillas vacías de JKAnime no significan «hace falta renderizar JS» ✅

Los tres `div.row.page_directorio` del directorio llegan **vacíos** en el HTML. La conclusión
intuitiva —que hay que renderizar JavaScript o encontrar un endpoint AJAX— es **falsa**, y cuesta
horas comprobarlo: `/ajax/directorio`, `/ajax/filtros`, `/ajax/filter` y `/ajax/animes` devuelven
404 o 405.

El servidor **ya incrusta el listado completo** en un `<script>` de la propia página, como una
variable `animes = {…}` que jQuery se limita a pintar. El dato está en el HTML que devuelve
`requests`; solo hay que recortarlo contando llaves ([05 §3b](05-proveedores-y-scraping.md)).

**Síntoma de haber caído en la trampa**: se concluye que el proveedor necesita un navegador y se
descarta o se degrada `search_animes_by_genres_and_order` sin motivo.

**Invariante**: ante una rejilla vacía, buscar primero el payload en el HTML crudo —
`grep 'animes *= *{'` — antes de asumir que el contenido llega por red.

---

### 16. En JKAnime, el slug y el id numérico no son intercambiables ✅

Un anime tiene **dos identificadores**: el *slug* (`hunter-x-hunter-2011`), que es el que viaja en
las URL y en `AnimeInfo.id`, y un **id numérico interno** (`429`) que solo sirve para
`POST /ajax/episodes/<id>/`. El numérico **no aparece en ninguna URL navegable**: hay que sacarlo
del HTML de la ficha.

Esa llamada además exige token CSRF (`<meta name="csrf-token">`) y cookies de sesión, o Laravel
responde **419**.

**Síntoma**: fichas que se abren con título, sinopsis, géneros y póster correctos pero con **cero
episodios**, sin más aviso que un `print`.

📖 `get_anime_info` devuelve la ficha igualmente en ese caso, con `episodes=[]`, en vez de perder
también lo que sí se leyó. Es deliberado: [05 §3b](05-proveedores-y-scraping.md).

Es la misma clase de confusión que la **trampa 13**, pero dentro de un proveedor en vez de en la
ficha de detalle.

---

## Columna `provider_id`

### 17. `provider_id` dice **quién sirve el slug**, no de dónde salió el anime ⚠️

Las filas anteriores a la columna se rellenan solas al abrirlas ([04 §8](04-modelo-de-datos.md)),
anotando **quién sirvió la ficha esa vez**. Cuando el slug existe en varios sitios —`dandadan` está
igual en los tres— el que queda anotado es el que tuvieras seleccionado ese día.

**Síntoma**: el reparto por proveedor de la biblioteca cambia según cómo hayas navegado, no según de
dónde vinieran los animes. ✅ Comprobado en la BD real: 19 filas dicen `animeflv` mientras que un
barrido independiente, preguntando en el orden de la aplicación, había concluido `animeav1` para 12 de
ellas. **Las dos respuestas son ciertas**; solo cambia quién contestó primero.

**Por qué no es un bug**: para lo que se usa la columna —a quién preguntar al reabrir este anime— la
respuesta es correcta, porque ese proveedor **sí** sirve ese slug. Lo que no puedes hacer es
interpretarla como procedencia, ni fiarte de ella para estadísticas.

**Si algún día hace falta la procedencia real**, es un dato distinto y necesita su propia columna; no
lo saques de esta.

---

### 18. Reapuntar una fila a otro proveedor puede duplicarla en silencio ✅

`ANIMES` **no tiene `UNIQUE` sobre `anime_id`** ([04 §3](04-modelo-de-datos.md)). Un
`UPDATE … SET anime_id = ?` hacia un slug que ya ocupa otra fila se ejecuta **sin error** y deja dos
filas del mismo anime, cada una con sus propios episodios vistos y sin forma de desempatarlas.

**Cuándo pasa de verdad**: tienes One Piece guardado desde AnimeFLV (`one-piece-tv`) **y** desde
AnimeAV1 (`one-piece`) porque en su día lo añadiste dos veces; migras el primero a AnimeAV1.

**Cómo está tapado**, en dos capas a propósito:

| Capa | Línea | Qué hace |
|---|---|---|
| GUI | `anime_window.py:670-680` | Comprueba antes y lo **explica** con un diálogo: «ya hay otra entrada de este anime en X» |
| Persistencia | `animesPersistence.py:478-481` | Vuelve a comprobarlo y devuelve `False` |

La segunda no es redundante: `migrate_anime_identity` es pública y no puede fiarse de que quien la
llame haya mirado. La primera existe porque un `False` a secas no le dice nada al usuario.

**Invariante**: cualquier escritura que cambie `anime_id` de una fila existente comprueba primero que
el destino esté libre. La BD no lo va a hacer por ti.

---

## CustomTkinter y layout

Ninguna da error: todas se manifiestan como algo que sale mal colocado, invisible o parpadeando.
Las reglas R7, R8 y R10-R13 son de la misma familia.

### 19. Un `CTkFrame` sin hijos conserva 200 × 200 como tamaño pedido 🔴 ✅

Un marco vacío —o que solo tiene widgets colocados con `place()`, que no piden sitio— **no mide
cero**: conserva el tamaño por defecto de `CTkFrame` y **estira la fila o la columna que lo
contenga**.

**Síntoma observable**: la barra lateral salió **con los seis destinos en blanco y sin ningún
error**. La barrita de acento de 2 px inflaba la fila del ítem a 200 px; el marco se quedaba en 38 px
por fuera, pero su rejilla interna centraba icono y etiqueta en `y=86`, **fuera de la parte visible**.

**Invariante**: todo `CTkFrame` decorativo, todavía vacío, o cuyos hijos van con `place()`, necesita
`height=` explícito. `ViewHeader.controls_frame` nace con `height=1` por esto, y `GenreChips.show()`
se fija el alto a mano.

**Hermana de la anterior**: el alto de una fila se fija con **`grid_rowconfigure(..., minsize=)`**, no
con `height=` + `grid_propagate(False)`. Medido: esa combinación deja el marco al alto pedido por
fuera, pero su rejilla interna sigue centrando los hijos como si midiera 200.

**Y el ancho fijo necesita dos cosas**: `grid_propagate(False)` **y** `minsize` en la columna del
padre. Solo con el primero, la rejilla de `MainWindow` le roba píxeles a la barra cuando el contenido
pide más ancho del que cabe — medido, 219 px en vez de 224.

> 🆕 **Y el ancho, igual** (2026-10-28, fase 3 de la 0.5.0): un `CTkFrame` sin `width` pide **200 px de
> ancho** aunque lleve `height=1` y `sticky="ew"`. La pestaña «Episodios» de `TabBar` medía 200 px y su
> contador quedaba a 40 px del texto. **`width=1`** en todo marco que deba medir lo que mida su
> contenido o su `sticky`; las páginas de las vistas (`show_view()`) nacen con `width=1, height=1`.

---

### 20. `wraplength` no limita a dos líneas, y un `CTkLabel` no se recorta a su `height` 🔴 ✅

`wraplength` envuelve **todas** las líneas que necesite el texto, y el `CTkLabel` **crece** por
encima de su `height` en vez de recortarse. Reservar alto no sirve de nada.

**Síntoma observable**: un título de anime de tres líneas desnivelaba la fila entera de la rejilla, y
las celdas de debajo bailaban.

**Invariante**: **todo título de ancho fijo pasa por `Theme.ellipsize(texto, fuente, ancho,
líneas)`**, que reproduce el reparto por palabras de Tk midiendo con `font.measure()` y corta la
última línea con puntos suspensivos. Aplica a `AnimeRow`, a las tres rejillas y a la ficha.

---

### 21. Los contadores de la barra salen de listas que solo se llenan al arrancar 🔴 ✅

`MainWindow.recent_animes`, `favourite_animes`, `watching_animes`, `pending_animes` y
`finished_animes` son **cachés en memoria** que se pueblan en `load_animes()`.
`refresh_sidebar_counts()` hace `len()` sobre ellas: **no consulta la BD**.

**Síntoma observable**: cambiar un estado movía la fila en la BD y en la vista, pero el número de la
barra lateral seguía diciendo lo de antes hasta el siguiente arranque.

**Invariante**: quien cambie un estado **relee las listas afectadas del hub y solo después** llama a
`refresh_sidebar_counts()`. Lo hacen «Empezar» (`pendingAnimes.py`) y la ficha (`anime_window.py`,
desde la fase 8).

---

### 22. La configuración de rejilla del `content_frame` sobrevive a `clear_frame()` 🔴 ✅

`clear_frame()` destruye los **hijos**, no la configuración de filas y columnas del contenedor. Y una
columna **con peso y sin widgets también recibe el espacio sobrante**.

**Síntoma observable**: después de visitar la ficha —que repartía peso entre cuatro columnas y cuatro
filas—, la vista siguiente pintaba todo apretado en una columna 0 estrecha, con la mitad derecha de
la pantalla en blanco.

**Invariante**: toda vista que reparta peso entre varias columnas o filas **tiene que devolverlo a
cero al salir**. Hoy solo la ficha reparte; si otra lo hace, hereda la obligación.

> 🆕 **Segunda mitad, 2026-09-02**: lo mismo pasa **dentro** de un componente. Desde que
> `PosterGrid` calcula sus columnas del ancho, le da `weight=1` y un grupo `uniform` a cada una — y
> esos pesos sobreviven a destruir las celdas igual que los del `content_frame`. Al pasar de 8
> columnas a 3, las cinco que sobran seguirían reclamando su parte del ancho y los tres pósters
> saldrían apiñados a la izquierda de una fila vacía. Por eso `__configure_columns()` no solo pone
> peso: **se lo quita** a `range(columnas, self.__weighted_columns)`. Quien añada otro componente que
> configure columnas según los datos hereda la obligación de destejerlo.

> 🆕 **Desde el 2026-10-28 (fase 5 de la 0.5.0) las vistas no componen en `content_frame`**: cada una
> construye en **su página** (un `CTkFrame` en la fila 0, columna 0 de `content_frame`, con la columna
> 0 de peso), que `clear_frame()` **esconde** en vez de destruir. La ficha sigue componiendo en
> `content_frame` directamente y sigue siendo la única que reparte peso ahí, así que la obligación
> sigue siendo suya; su reparto no toca la columna 0 de las páginas.

---

### 23. Un `<Leave>` no significa que el ratón se haya ido 🔴 ✅

Tk manda `<Leave>` al marco **también cuando el puntero pasa a uno de sus propios hijos**.

**Síntoma observable**: la fila parpadeaba al mover el ratón por encima, y la píldora de acción
(«Empezar», «Episodio N →») **se apagaba justo al ir a pulsarla**, porque el puntero entraba en ella
saliendo del marco.

**Invariante**: antes de apagar un estado de hover, comprobar dónde está el puntero de verdad.
`AnimeRow.__pointer_inside()` compara `winfo_pointerxy()` con el rectángulo real de la fila. Vale
para cualquier fila o tarjeta con acción en hover.

**Hermana**: el hueco de la acción **se reserva siempre**, con tamaño fijo y `grid_propagate(False)`;
la píldora solo se muestra y se esconde. Si se creara al entrar el ratón, la fila cambiaría de ancho
bajo el cursor.

🔴 **Léela junto a la regla R8**:
esta trampa dice que sobran `<Leave>`, y la otra que **faltan**. Comprobar el puntero antes de apagar
—lo que arregla ésta— es justo lo que hace que un `<Leave>` que no llega deje la fila encendida para
siempre. Las dos se arreglan juntas o no se arregla ninguna.

---

### 24. `bind()` y `event_generate()` no hablan del mismo widget en CustomTkinter 🔴 ✅

Un widget de CustomTkinter es un marco de Tk con hijos dentro, y `bind()` **reenvía** el atajo a esos
hijos: `CTkFrame.bind()` va a su `_canvas`; `CTkLabel.bind()`, al `_label` **y** al canvas;
`CTkEntry.bind()`, al `_entry`; `CTkButton.bind()`, al canvas y a sus etiquetas.

Con el ratón real da igual —lo que se toca es el canvas—, pero **`widget.event_generate()` sobre el
objeto CTk no dispara nada**.

**Síntoma observable**: una prueba automática que emite `<Return>` sobre un `CTkEntry`, o `<Enter>`
sobre una fila, «pasa» sin que ocurra nada, y se da por verificado algo que no se ha ejecutado.

**Invariante**: para ejercitar un gesto sin ratón, emitir sobre el **hijo interno**
(`entry._entry.event_generate(...)`) o —mejor— invocar directamente el `command` o el manejador.

**Tres más de CustomTkinter**, de la misma familia:

- Un `CTkFrame` con `fg_color="transparent"` **no pinta su borde**: no dibuja su rectángulo, y con él
  se va el `border_width`. Y aunque se le dé color, **una etiqueta transparente encima lo tapa**. La
  receta que funciona: marco con `fg_color=BG` + borde, y la etiqueta **dentro**, más baja que él.
- CustomTkinter **rechaza `width=` y `height=` dentro de `place()`** con un `ValueError`, al revés
  que Tk pelado: el tamaño se le da al construir el widget.
- CustomTkinter **no redondea la `image` de un widget** por mucho `corner_radius` que tenga. El
  recorte hay que traerlo hecho desde PIL (`load_rounded_image()`).

---

## Reproductor in-app

Lo que tienen en común casi todas: **fallan cayendo al navegador**, que es la degradación
diseñada (`plan-reproductor/README.md`, regla 2). Así que el
síntoma típico **no** es un error, sino «este servidor se abre fuera cuando debería verse aquí», y
eso se confunde fácilmente con que el hoster haya cambiado. Antes de tocar un resolutor, descarta
las de este apartado.

La capa y el reproductor se describen en [06 §12](06-gui-y-vistas.md) y
[05 §9](05-proveedores-y-scraping.md); el flujo entero, en [03 §13](03-flujos-de-ejecucion.md).

### 25. Los segmentos de zilla dan 403 sin `Sec-Fetch-Site: same-origin` 🔴 ✅

**Por qué**: el playlist `https://player.zilla-networks.com/m3u8/<hash>` (el servidor «HLS» de
AnimeAV1) responde 200 a cualquiera. Los **segmentos** —`segs/<hash>/NNN.html`, que pese a la
extensión son fMP4 y empiezan por `styp`— exigen la cabecera `Sec-Fetch-Site: same-origin`,
**exactamente con ese valor**. Es la forma que tiene el sitio de comprobar que la petición sale de su
propio reproductor.

**Síntoma observable**: mpv baja el playlist, pide el primer segmento, recibe 403 y acaba en
`end-file` con `reason=4`. En pantalla, la tarjeta de «Cargando» dura un instante y el episodio **se
abre en el navegador** con «No se ha podido cargar aquí». Parece que zilla está caído, y no lo está.

⚠️ **No confundirlo con una caída real**, que también pasa (tres días seguidos en septiembre de
2026, con **522** de Cloudflare): entonces mpv espera el `network-timeout` de 15 s y la caída al
navegador tarda **~20 s**. **Instantáneo → cabecera; ~20 s → origen caído.** Y si responde, pero
**despacio**, cae a los **30 s**, por el tope propio del reproductor: [regla R15](#r15-un-hoster-lento-no-da-error-load_timeout_s).

**Invariante**: las cabeceras viajan en `MediaSource.headers` y `VideoPlayer.play()`
(`video_player.py:680`) las pasa a mpv como `http_header_fields` —todas salvo `User-Agent`, que va a
su propiedad—. El cliente `curl` de mpv las aplica a **cada** petición, playlist y segmentos. Nunca
se ponen solo en la petición del playlist.

**Cómo comprobarlo**: un segmento con y sin la cabecera ([09 §6h](09-verificacion-y-pruebas.md)).
✅ 2026-09-23 contra un servidor local con la misma regla (los segmentos llegan con la cabecera) y ✅
2026-10-20 contra zilla real: **200 con ella, 403 sin ella**, y `dandadan` ep. 1 visto en la app.

---

### 26. Cada hoster quiere sus cabeceras, y lo que uno exige otro lo rechaza 🔴 ✅

**Por qué**: no hay una política de cabeceras común que valga para todos:

| Medio | Cabeceras que funcionan | Lo que lo rompe |
|---|---|---|
| zilla (HLS de AnimeAV1) | `Sec-Fetch-Site: same-origin` | quitarla → 403 en los segmentos ([trampa 25](#25-los-segmentos-de-zilla-dan-403-sin-sec-fetch-site-same-origin--)) |
| MP4Upload | UA de navegador + `Referer: https://www.mp4upload.com/` (**el suyo**) | el `Referer` del sitio que lo embebe (`https://animeav1.com/`) → **403** |
| `jkplayers.com` (`/jkplayer/jk`, «Desuka») | **ninguna** | **cualquier `Referer` → 410 Gone** |
| `playmudos` (`/jkplayer/um` y `umv`, «Desu» y «Magi») | ninguna | — |

**Síntoma observable**: añadir una cabecera «por si acaso» en un sitio común —en `base.py` o en
`VideoPlayer.play()`— **rompe en silencio un hoster que funcionaba**. Un `Referer` genérico deja
Desuka cayendo al navegador sin un solo error.

**Invariante**: las cabeceras son del **resolutor** que conoce el hoster, y el reproductor manda
**exactamente** las de `MediaSource.headers`, ni una más. Por eso `base.py` no tiene cabeceras por
defecto, y por eso el UA de navegador está **duplicado a propósito** en `base.py` respecto a
`jkanime.py`: la capa de resolución no importa de `APIs.<sitio>` ([01](01-arquitectura.md)).

✅ Medido el 2026-09-24 (fase 1): `jkplayers` con `Referer` → 410; MP4Upload con el de AnimeAV1 →
403 y con el suyo → 206.

---

### 27. Una URL de medio no se guarda: caduca o va atada a tu IP 🔴 ✅

**Por qué**:

- **playmudos** (Desu, Magi) lleva un parámetro `e=` que es un *epoch* **~3 h** después de
  resolver. El resolutor lo copia a `MediaSource.expires_at`.
- **`jkplayers.com`** (Desuka) **incrusta la IP pública del cliente en el path**: se resuelve en una
  máquina y no se reproduce en otra, ni en la misma tras cambiar de red o encender una VPN.
- **MP4Upload** lleva un token en el path que no declara caducidad (`expires_at=None`) y parece de
  sesión.

⚠️ `expires_at=None` significa «la URL no la declara», **no** «no caduca».

**Síntoma observable**: funciona en el momento y falla horas después, al día siguiente o tras una
VPN, siempre como 403 o 410 y siempre cayendo al navegador.

**Invariante**: se resuelve **al pulsar el servidor**, nunca al listarlos —`ServerInfo` guarda la
URL del *embed*, no la del medio— y `registry` **no tiene caché a propósito**. No guardes un
`MediaSource` para reutilizarlo.

⚠️ **La única reutilización que hay** es «repetir» con el episodio terminado, que vuelve a cargar el
mismo `MediaSource` (`VideoPlayer.toggle_pause()`). Tras horas parado en la tarjeta de fin, repetir
fallaría y caería al navegador. No se ha visto; se deduce del código.

---

### 28. Los eventos de mpv llegan en su hilo, y desde ahí ni `after()` es seguro 🔴

**Por qué**: los observadores (`observe_property`) y los callbacks de evento (`event_callback`) de
`python-mpv` se ejecutan en el hilo **`MPVEventHandlerThread`** (✅ fase 0), no en el de Tk. Tocar
un widget desde ahí es la regla de siempre ([07](07-concurrencia-e-hilos.md)). Lo nuevo es que
**tampoco** basta con `after(0, …)`, la receta del resto de la aplicación. `after()` llamado desde
otro hilo **espera** a que el hilo de Tk lo atienda, y `terminate()`, llamado desde Tk al cerrar el
reproductor, **espera** a que acabe el hilo de eventos. Si coinciden, se esperan el uno al otro.

**Síntoma**: la aplicación se congela al cerrar el reproductor («← Volver a la ficha», cambiar de
vista o cerrar la ventana). Con `time-pos` llegando a 13-24 veces por segundo, «si coinciden» es
casi siempre. ⚠️ **No se ha reproducido aposta**: el diseño lo evitó desde la fase 3. Lo que sí está
medido es que `after(0)` **funciona** mientras nadie cierre (24 repintados/s sin errores en la fase
0), y eso es justo lo que hace que la trampa parezca innecesaria.

**Invariante**: los callbacks de mpv **solo asignan atributos** (posición, duración, pausa) **o
meten en una `queue.Queue`** (`start-file`, `playback-restart`, `end-file`, `eof`). El hilo de Tk los
recoge con un sondeo cada `POLL_MS` = 100 ms (`VideoPlayer.__poll`, `video_player.py:816`). Si
añades un observador, sigue ese patrón. Los callbacks hacia el dueño (`on_started`, `on_end`,
`on_error`) ya llegan en el hilo de Tk.

---

### 29. El final de un vídeo no es un evento: `end-file` llega también al parar, y con `keep-open` no llega al terminar 🔴 ✅

**Por qué**, en dos mitades:

- `end-file.reason` vale **0** al llegar al final, **2** al `stop()` **y** al cargar otro medio
  encima, **3** al `terminate()` y **4** con error (✅ fase 0). Parar a mano y cambiar de servidor
  dan el mismo código, y el `end-file` del medio anterior puede llegar **después** de haber pedido el
  nuevo.
- El reproductor va con **`keep-open=yes`**, porque sin él la superficie se queda **negra** al
  terminar y la ✕ de la tarjeta de fin no tendría último fotograma que enseñar. Y con `keep-open` el
  final **no manda `end-file`**: llega `eof-reached=True` con el medio en pausa (✅ fase 4, *spike*
  con `lavfi`).

**Síntoma observable**: si se trata cualquier `end-file` como fin, sale la tarjeta de «Has terminado»
al volver a la ficha o al cambiar de servidor, **y el episodio se marca como visto en la
biblioteca**. Si se espera solo `reason == 0`, la tarjeta no sale nunca y no se marca nada.

**Invariante** (`__handle_event`, `video_player.py:832`): el fin es `eof-reached`, con
`end-file` / `reason 0` de respaldo, y **solo** si el medio había empezado (`playback-restart`). Un
`end-file` que llega antes del `start-file` del medio nuevo es del anterior y se ignora
(`__awaiting_start`). `reason 4` es error → navegador.

---

### 30. Un fin de fichero a mitad de episodio es un corte, no el final 🔴 📖

**Por qué**: un servidor que corta el stream a mitad deja a mpv en fin de fichero, **igual que el
final de verdad**. Y desde la fase 4 el final **escribe en la biblioteca**: marca el episodio como
visto, con la semántica acumulativa ([trampa 7](#7-el-marcado-de-episodios-es-acumulativo-el-desmarcado-unitario-)).

**Síntoma** (si se quita la guarda): un episodio que se corta en el minuto 8 queda marcado como visto,
**y con él todos los anteriores**.

**Invariante**: `__reach_end()` (`video_player.py:860`) compara posición y duración. Si faltan más
de `END_TOLERANCE_S` = 15 s, lo trata como error (`on_error` → navegador) y **no marca nada**.
📖 Rama leída, **no ejecutada**: en las pruebas ningún servidor cortó.

---

### 31. Un widget dentro del frame del vídeo no se ve; uno hermano encima, sí 🔴 ✅

**Por qué**: mpv pinta en la ventana nativa del frame cuyo `winfo_id()` recibe como `wid`. Los
**hijos** de ese frame quedan tapados (**0 %** de sus píxeles visibles, ✅ fase 0). Un **hermano**
—mismo padre, misma celda, `lift()`— **sí** se ve (92 %), y opaco, porque Tk no tiene transparencia
por widget.

Esto **corrige** a la investigación, que decía «ningún widget encima del vídeo». Es lo que hace
posibles las tarjetas: en `VideoPlayer`, `__card_frame` es hermano de `__surface` dentro de
`__stage`. La de «Cargando» va **encima** de la superficie mapeada, porque mpv necesita la ventana
puesta para crear su salida de vídeo. Las tarjetas finales sí quitan la superficie
(`grid_remove()`).

Por la misma razón el panel **no vive dentro del `CTkScrollableFrame`**. `player_frame`
(`main_window.py:127`) es hermano de `content_frame`: fila 0 y fila 1 de la columna de contenido.
⚠️ El síntoma que se temía allí —el vídeo pintándose fuera del área visible— **no aparece** (✅
fase 0: la superficie se recorta y se desplaza con el lienzo), pero el vídeo se iría con el scroll de
la ficha, que no es lo que pide el diseño.

**Síntoma observable**: un control creado **dentro** de `__surface` se ve hasta que mpv pinta el
primer fotograma, y luego desaparece.

**Invariante**: nada dentro de `__surface`. Lo que vaya encima va como **hermano** en `__stage`, y
opaco. Lo que tenga que flotar sobre la imagen a pantalla completa son ventanas aparte
([trampa 34](#34-la-barra-flotante-y-el-deslizador-de-volumen-son-ventanas-aparte-siempre-encima--)).

---

### 32. El ratón y el teclado sobre el vídeo llegan a Tk, no a mpv 🔴 ✅

**Por qué**: al revés de lo que esperaba el plan. Con `input-vo-keyboard` encendido **o** apagado,
39-40 de 40 `<Motion>` sobre el vídeo llegan al frame de Tk; `Esc` y `q` los recibe `bind_all`; los
*bindings* de mpv y su propiedad `mouse-pos` **no reciben nada** (✅ fase 0). Además, libmpv trae
**apagados** `input-default-bindings`, `input-vo-keyboard` y `osc`: no hay atajos propios, ni `Esc`,
ni la `q` que cierra, ni barra en pantalla.

**Consecuencias**:

- «Mover el ratón muestra la barra» y los atajos de pantalla completa —`Esc` sale, Espacio pausa o
  reanuda, ← y → saltan 10 s, y un clic sobre el vídeo pausa o reanuda— se atan **en Tk**. Las
  teclas, con `bind_all()` solo mientras dura la pantalla completa, para no pisar los campos de
  texto, y se quitan al salir con su `deletecommand()` (regla R18). El clic, en `__stage` y
  `__surface`, no en `__card_frame`, cuyas tarjetas tienen sus botones. ✅ Comprobado con mpv
  reproduciendo y clics reales: un clic, un cambio.
- **`cursor-autohide` no sirve**, porque mpv no ve el ratón. El cursor lo oculta Tk con `cursor="none"`
  sobre `__stage`, `__surface` y `__card_frame` (`__set_cursor_hidden`).
- `<Motion>` se ata **dos veces** por widget, con `tkinter.Frame.bind` y con el `bind` de CTk
  (en `VideoPlayer.__init__`), porque `CTkFrame.bind()` solo ata el lienzo interno
  ([trampa 24](#24-bind-y-event_generate-no-hablan-del-mismo-widget-en-customtkinter--)). ⚠️ No se
  probó a quitar una de las dos.

**Síntoma**: un atajo definido en mpv no hace nada; con `cursor-autohide` el cursor no se oculta
nunca.

---

### 33. `-fullscreen` lleva la ventana al monitor principal 🔴 ✅

**Por qué**: `attributes("-fullscreen", True)` movió la ventana del monitor secundario (`2028, 91`)
al principal (`0, 0, 1920, 1080`), y al salir la devolvió a su sitio (✅ fase 0). También acabaron en
el principal `-fullscreen` seguido de `geometry` y `geometry` seguido de `-fullscreen`. Quitar el
marco con `SetWindowLong` colocaba bien, pero descolocaba la ventana al salir.

**Síntoma observable**: con dos monitores, «pantalla completa» sale en el que no estás mirando.

**Invariante**: `MainWindow.enter_player_fullscreen()` **no** usa `-fullscreen`:

1. Lee el rectángulo del monitor de la ventana con `MonitorFromWindow(…, MONITOR_DEFAULTTONEAREST)` y
   `GetMonitorInfoW`.
2. Pone `overrideredirect(True)` y la geometría con **`tkinter.Tk.wm_geometry`**, no con la de CTk,
   que aplica el escalado de DPI a un rectángulo que ya viene en píxeles físicos.
3. Justo después de `overrideredirect()` —al entrar **y** al salir— corrige dos efectos de Tk, que
   recrea la ventana nativa: `__keep_taskbar_button()` le devuelve el botón de la barra de tareas,
   Alt+Tab y minimizar —sin marco queda como ventana de herramientas, y tapada no habría forma de
   volver a ella—, y `__drop_topmost()` la saca de «siempre encima», que hereda si la ventana que
   tenía encima lo es (la barra flotante, el deslizador de volumen o la barra de tareas). ✅ Medido:
   sin lo segundo, la ventana se quedaba encima de todo también al salir.
4. Guarda la geometría, el maximizado y el `minsize` de la columna de la barra lateral, y pone ese
   `minsize` a 0. Sin eso quedaría una franja a la izquierda del vídeo, porque ese `minsize`
   **sobrevive a quitar la barra** ([regla R7](#r7-todo-marco-de-fondo-lleva-fg_color-explícito)).
   `exit_player_fullscreen()` lo restaura todo.

⚠️ En la aplicación solo se probó en el monitor **principal**. La receta se probó en el secundario
con la ventana de la fase 0.

---

### 34. La barra flotante y el deslizador de volumen son ventanas aparte, siempre encima 🔴 ✅

**Por qué**: a pantalla completa no hay rejilla donde poner la barra sin encoger el vídeo. Por decisión
del usuario es un `Toplevel` sin marco y con `-topmost`, igual que el deslizador de volumen
(`_VolumePopup`). Ser ventanas aparte trae tres problemas, los tres vistos:

| Problema | Síntoma | Remedio |
|---|---|---|
| **`-topmost` sobrevive a `Alt+Tab`** | la barra se queda flotando **encima de la otra aplicación** (✅ visto encima de la terminal) | `__check_foreground()` mira `GetForegroundWindow()` cada `FOREGROUND_CHECK_MS` = 150 ms y la retira si el primer plano no es de este proceso. `__on_motion` tampoco la saca en ese caso |
| **Mostrarla con `update_idletasks()`** | **el primer clic sobre la barra se pierde**: no está mapeada del todo | `update()` al crearla y al volver a enseñarla |
| **Salir del icono hacia el deslizador dispara `<Leave>`** | el deslizador **se cierra** al ir a por él | margen de `VOLUME_GRACE_MS` = 300 ms (`schedule_volume_check`), y solo se cierra si el puntero no está ni en el icono ni en el deslizador |

**Invariante**: cualquier ventana flotante nueva tiene que pasar por las tres guardas: retirarse
cuando el primer plano no es nuestro, mostrarse con `update()` y tener margen de gracia para llegar a
ella.

---

## Relaciones y franquicia

Las trae el plan de la 0.5.0 (temporadas, relacionados y «Te puede interesar»). Las cuatro primeras
son de **parseo**: cada sitio anuncia las relaciones a su manera, y equivocarse no da error, sino
relacionados de menos o una franquicia mal montada.

### 35. «Historia principal» y «Predecesor» no son precuelas ✅

AnimeAV1 (`type:8`, «Historia principal») y JKAnime («Predecesor») las usan para apuntar **de una
película, OVA o especial a su serie madre**, no a la temporada anterior.

**Síntoma si se traducen a `PREQUEL`**: el recorrido de la franquicia mete **la serie entera** como
temporada anterior de una película, y «◀ Temporada anterior» de la película 1 de SnK lleva a la serie.

**Invariante**: solo el código `1` de AnimeAV1 y la etiqueta «Precuela» de JKAnime son `PREQUEL`. Todo
lo que no sea precuela, secuela o versión alternativa es `OTHER` (decisión P3/P8 del usuario: solo
cuatro tipos). Un código de AnimeAV1 que no esté en la tabla cae en `OTHER` **con un `print`**, nunca
en excepción ([05 §3](05-proveedores-y-scraping.md)).

---

### 36. Un título de relación puede llevar corchetes y comillas escapadas ✅

El array `relations` del payload de AnimeAV1 es JavaScript, no JSON, y sus títulos pueden contener
`]` («[Oshi no Ko]») y `\"`.

**Síntoma con una regex perezosa hasta `]`**: el array se corta en el primer título con corchete y se
pierden **en silencio** todos los relacionados siguientes.

**Invariante**: `AnimeAV1.__extract_js_array()` recorta el array **contando corchetes y respetando las
cadenas**, y cada cadena se des-escapa con `json.loads`. ✅ Probado offline con `[Oshi no Ko]`, `\"`,
un código 99 y un payload sin `relations`.

---

### 37. En JKAnime, todos los `<h5>` de «Temporadas y relacionados» llevan el mismo `id` ✅

Cada bloque de tipo es `<h5 id="aditional">Secuela</h5>` seguido de sus enlaces, y **todos** repiten
`id="aditional"`. Además, `li[rel='tipo']` (el formato del propio anime) sale **dos veces** en la
página, en dos bloques de información.

**Síntoma**: un selector por `#aditional` devuelve solo el primer bloque, y ninguno distingue tipos.

**Invariante**: se recorren **en orden** los hermanos `h5`/`a` del `<h3>Temporadas y relacionados</h3>`;
el tipo de cada enlace es el texto del último `<h5>` visto. Del formato vale el primer `li[rel='tipo']`.

---

### 38. En JKAnime, el paréntesis final del enlace no siempre es el formato ✅

Los enlaces son «Título (Serie)», pero también «Hunter x Hunter (2011)».

**Síntoma**: separar siempre el último paréntesis deja «Hunter x Hunter» sin año y con un formato
«2011» que no existe.

**Invariante**: solo se separa si el paréntesis es un formato conocido (Serie, OVA, Pelicula —sin
tilde—, Especial, ONA). Si no, se queda en el título.

---

### 39. `get_anime_relations` de AnimeAV1 hereda los 3 reintentos de su ficha ✅

En AnimeAV1 la ficha ligera **es** `get_anime_info`, que reintenta tres veces con 1 s de espera.

**Síntoma**: sin red, cada salto fallido del recorrido tarda ~3 s; ante un 403 serían **tres
peticiones** al sitio en vez de una.

**Mitigación**: el recorrido se corta en el primer fallo y no repite esa página en 2 min
(`FranchiseService.RETRY_FAILED_AFTER_S`). Si molesta, la salida es sobrescribir `get_anime_relations`
en AnimeAV1 sin reintentos; no se ha hecho.

---

### 40. El mismo slug en el otro proveedor puede ser otro anime ✅

`request_formats` pide **una** ficha al otro proveedor con el mismo slug para completar formatos. El
slug coincide muchas veces entre sitios, pero no siempre significa lo mismo.

**Síntoma sin comprobarlo**: los relacionados se pintan con los formatos **de otra franquicia**.

**Invariante**: la página del otro proveedor se descarta si `title_similarity()` con el título propio
queda por debajo de `TITLE_MATCH_THRESHOLD` (es la [regla R19](#r19-toda-identidad-por-título-pasa-por-title_similarity)
aplicada a un slug).

---

### 41. El directorio de JKAnime responde 429 con su propio texto ✅

Tras las peticiones de una sesión anterior del mismo día, `jkanime.net/directorio` devolvió **429**
con «Estas realizando demasiadas peticiones… el bloqueo dura 60 segundos».

**Síntoma**: `search_animes_by_genres_and_order` cae en `raise_for_status()` y devuelve `([], 1)`; la
búsqueda **parece vacía** (trampa 9: el manager no distingue vacío de error).

**Invariante**: no reintentar solo. «Te puede interesar» trata un `([], 1)` como error y ofrece
**«Reintentar» a mano** ([09 §7.9](09-verificacion-y-pruebas.md)).

---

### 42. En AnimeAV1, dos géneros del catálogo se combinan con O, no con Y ✅

`catalogo?genre=accion&genre=romance` trae animes que solo tienen **uno** de los dos.

**Síntoma**: quien espere una intersección recibe animes que comparten un género, no los dos.

**Invariante**: es lo que da el sitio. «Te puede interesar» lo asume —cada resultado comparte **al
menos uno**— y, si tras filtrar faltan, pide **la página siguiente**, no «el primer género solo», que
con O sería un subconjunto de lo ya pedido.

---

## Verificar fuera de la aplicación

Las cuatro mienten a un **script de verificación**, no a la aplicación. Las cuatro hicieron perder
tiempo durante el plan de la 0.5.0.

### 43. `after()` desde un hilo sin `mainloop()` en el principal no avisa ✅

Con un `tk.Tk()` oculto y `root.update()` en bucle, `after()` desde un hilo lanza
`RuntimeError: main thread is not in main loop`, y `FranchiseService` (como `EpisodeRefresher`) lo
traga como «la ventana se cerró».

**Síntoma**: el script **se queda esperando el callback para siempre**, sin error.

**Cómo evitarlo**: en los scripts, esperar con `root.mainloop()` y `root.quit()` en el callback. En la
aplicación no pasa: Tk está en `mainloop()`.

---

### 44. `requests.get()` llega a `Session.request` con el método en minúsculas ✅

`requests.get()` pasa `'get'`; la `Session` de JKAnime y `thread_session()`, `'GET'`.

**Síntoma**: un contador de peticiones que compare `== "GET"` da falsos «ha habido un POST».

**Cómo evitarlo**: normalizar con `.upper()` al contar.

---

### 45. Las listas del hub se reasignan al terminar la carga del arranque ✅

`MainWindow.finished_animes` y compañía se **reasignan** (no se mutan) cuando acaba la carga.

**Síntoma**: un script que guarda `app.finished_animes` justo tras crear la ventana se queda con la
lista vacía de antes de cargar.

**Cómo evitarlo**: leerlas en el momento de usarlas, nunca guardarlas al arrancar. Es la misma
familia que la [trampa 21](#21-los-contadores-de-la-barra-salen-de-listas-que-solo-se-llenan-al-arrancar--).

---

### 46. `CTkScrollbar._draw()` llama a `update_idletasks()` por dentro ✅

**Síntoma**: en `cProfile`, el repintado de toda una página aparece como **80 ms en
`CTkScrollbar.set`**, y parece que lo caro es la barra de desplazamiento.

**Cómo leerlo**: el `set` lo dispara el cambio de alto del contenido y **arrastra todo el repintado
pendiente** de Tk. Lo que mide es el coste de Tk, no el de la barra.

---

## Lo que cuesta pintar con CustomTkinter

### 47. Un `CTkFrame` de `height=1` no pinta nada 🔴 ✅

CustomTkinter 5.2.2 redondea el alto **a par** al dibujar: uno de 1 px no pinta, uno de 3 pinta 2.

**Síntoma**: una raya de 1 px hecha con `CTkFrame` no aparece, sin error. **El separador de
`EpisodeRow` (`height=1`) no se vio nunca**: comprobado leyendo píxeles, y por eso se quitó en la fase
3 ([regla R8](#r8-el-hover-se-ata-a-todos-los-hijos)).

**Cómo evitarlo**: rayas de 2 px. Si tiene que verse 1, se coloca con `place(..., y=1)` medio fuera de
su marco, que la recorta. Es lo que hace la raya de `TabBar`.

---

### 48. Cada widget de CustomTkinter cuesta ~3,5 ms al abrir una pantalla 🔴 ✅

Crearlo, pintarlo en el `update()` y destruirlo en el siguiente `clear_frame()`. El código Python que
lo construye es lo de menos.

**Síntoma**: la primera versión de la ficha con pestañas tardaba **40-75 ms más** que `develop` por
~13 widgets de la barra y 6-7 por enlace de temporada, aunque `__build_tabs` solo sumaba 5 ms de
Python.

**Cómo evitarlo**: contar widgets, no líneas; nada de marcos intermedios en lo que se pinta al abrir.
Y medirlo **contra `develop` en la misma tanda, alternando** (un *worktree* en el scratchpad): entre
arranques la línea base se mueve 15-30 ms ([09 §6l](09-verificacion-y-pruebas.md)).

---

### 49. Atar todo un subárbol con el `bind` de CustomTkinter ejecuta el clic dos veces ✅

`CTkBaseClass.bind()` reenvía a los hijos internos del widget. Si además se recorre el árbol entero
atando cada widget, los internos quedan atados **dos veces**.

**Síntoma**: el clic en una tarjeta abre dos fichas, o pide dos veces lo mismo.

**Invariante**: `ClickableCard.bind_card()` (`franchise_cards.py`) ata con **`tkinter.Misc.bind(w, …,
"+")`** cada widget del subárbol, internos de CTk incluidos —**lienzos de los `CTkFrame` también**,
que es lo que el recorrido se saltaba hasta el 2026-10-29 ([regla R21](#r21-para-recorrer-un-ctkframe-tkintermiscwinfo_children))—. Ata exactamente ese widget, y así
`event_generate("<Button-1>")` sobre el marco también dispara
([trampa 24](#24-bind-y-event_generate-no-hablan-del-mismo-widget-en-customtkinter--)).

---

### 50. Volver a mostrar una página conservada no es gratis ✅

Tk repinta cada lienzo de CustomTkinter al volver a colocar la página: ~0,1 ms por widget.

**Síntoma**: «Favoritos» tarda **136 ms** en volver con solo 12 ms de Python. Por debajo de 50 ms solo
baja «Buscar», la vista con menos widgets.

**Consecuencia**: el siguiente escalón de B13 es **pintar menos widgets por vista**, no conservar
mejor ([12 §4](12-deuda-tecnica-y-roadmap.md)).

---

### 51. Una página recién creada mide 1 px de ancho 🔴 ✅

Hasta el siguiente paso de geometría, y `PosterGrid` saca sus columnas del ancho de su contenedor
([regla R12](#r12-quien-mide-su-contenedor-tiene-que-estar-estirado-hasta-él)).

**Síntoma**: la primera visita a una rejilla con la ventana maximizada pinta las columnas del diseño y
repinta al momento: el doble de coste.

**Invariante**: `MainWindow.show_view()` hace `update_idletasks()` **solo** cuando la página aún no
mide nada.

---

## Hilos y recolección de basura

### 52. Un hilo de póster retiene la ficha entera hasta que termina su descarga ✅

Guarda el método de entrega (`deliver`), y con él `self`: la ficha.

**Síntoma**: en un bucle rápido de aperturas, las imágenes de Tk «crecen» de 35 a 67 y luego se
estabilizan. Era una fila con póster de AnimeFLV, que tarda 10 s en fallar.

**No es una fuga**: dura lo que el *timeout*. Para medir memoria, usar pósters que no dependan de un
sitio lento, o esperar a los hilos ([09 §6j](09-verificacion-y-pruebas.md)). Con pósters que no
cuelgan: **26 imágenes sin la pestaña y 32 con ella**, iguales en 25 vueltas.

---

## Ficha con pestañas y vistas conservadas

### 53. Desplazarse hasta un episodio con otra pestaña delante mide un widget sin colocar ✅

El reproductor desplaza la ficha al cambiar de episodio, y «Viendo» abre la ficha por un episodio.

**Síntoma**: con «Temporadas y relacionados» delante, la ficha salta a cualquier sitio.

**Invariante**: `__scroll_to_episode()` (`anime_window.py`) no hace nada si la pestaña activa no es
«Episodios».

---

### 54. La firma de una vista conservada tiene que ser una copia 🔴 ✅

Las vistas modifican sus filas en memoria; por ejemplo, la calificación de «Favoritos».

**Síntoma sin copia**: la firma cambia a la vez que la fila y siempre coincide. Tras calificar, volver
a «Favoritos» **no reordenaría**.

**Invariante**: `MainWindow.show_view()` hace `deepcopy` de la firma al guardarla, y solo cuando
reconstruye. Comparar la lectura nueva no copia nada.

---

## Reglas que sostienen arreglos

Problemas que ya no se dan porque el código los evita, pero cuya causa sigue ahí: vuelven en cuanto
alguien escribe código nuevo sin tenerlos en cuenta. Solo la regla; la historia completa de cada uno
está en el historial de git.

### R1. La migración es automática; la serialización no

`start()` → `validate_db_integrity()` lleva la BD a lo declarado en `AnimeField` / `SCHEMA`, con copia
previa en `resources/DB/backups/`. No actualiza `AnimeRecord.to_db_dict` / `from_db_dict`, ni da valor
a las filas que ya había: llegan a `NULL` salvo que se declare en `TableSchema.defaults`, y
`from_db_dict` debe tolerar `None`. Las columnas de la BD que no estén en `SCHEMA` se descartan al
reconstruir. Leer con `query_sql` sin pasar por `start()` sigue expuesto a la trampa 1.

### R2. `get_anime_info()` puede devolver `None`

Cuando fallan todos los proveedores. Todo clic que abra una ficha lo comprueba y llama a
`show_anime_info_error()`: Tk se traga la excepción del callback, y sin la guarda el clic no hace
nada. El constructor de `AnimeWindowViewer` lanza `ValueError` con `None` y normaliza
`episodes=None` sobre una **copia**, porque ese `None` en el objeto cacheado marca «falta la precarga».

### R3. AnimeAV1 no declara `charset`: toda petición pasa por `_fetch()`

Sin `charset`, `requests` decodifica como ISO-8859-1 y títulos y sinopsis salen con mojibake. `_fetch()`
fija UTF-8 solo si el servidor no declara otro. Una petición directa en `animeav1.py` reintroduce el
fallo en esa ruta, y lo que se guarde mal se queda mal en la BD.

### R4. Toda carpeta de pósters está en `POSTER_FOLDERS`

`find_cached_poster_path()` solo busca en `POSTER_FOLDERS` (`utils/utils.py`), y las carpetas de estado
salen de `AnimeStatus.name.lower()`: un estado nuevo obliga a añadir la suya, o sus pósters no se
encuentran.

### R5. Un `CTkImage` sin `size=` se pinta a 20 × 20

`size=` es lo que se pinta; los píxeles del PIL son otra cosa. Sin él sale un cuadradito, sin error.

### R6. Los filtros de la biblioteca son locales

El `anime_id` guardado es el slug de quien guardó la fila, distinto en cada sitio: filtrar la biblioteca
preguntando al proveedor seleccionado hace desaparecer animes que sí tienes. `filter_animes_by_title()`
compara títulos guardados, sin red; la búsqueda web (`SavedAnimeSearch`) solo suma, nunca quita.
Cualquier filtro nuevo sobre la biblioteca tiene que funcionar sin conexión.

### R7. Todo marco de fondo lleva `fg_color` explícito

Un `CTkFrame` sin `fg_color` no es transparente ni hereda del padre —eso solo lo hace `CTkLabel`—: sale
del gris de la paleta de CustomTkinter. Lleva su token de `Theme`, y también la raíz y el canal de un
`CTkProgressBar`. El `git grep` de colores literales no lo detecta, porque el defecto es la ausencia
de uno. Y el `minsize` de una columna sobrevive a quitar su widget con `grid_forget()`.

### R8. El hover se ata a todos los hijos

`CTkFrame.bind()` ata a su lienzo, que es hermano de los demás hijos y no su ancestro: salir de la
fila por un hijo sin atar no manda ningún `<Leave>`, y el resaltado se queda encendido. En
`EpisodeRow` el hover va a sus cuatro hijos y el clic a tres (el interruptor tiene su comando), y
`EpisodeRow.__hovered` es de clase para que no pueda haber dos filas encendidas. Un hijo nuevo,
atado. Se lee junto a la trampa 23.

### R9. `ANIMES.episodes` es una foto: la refresca `EpisodeRefresher`

Dice cuántos episodios servía el proveedor la última vez que se miró. La banda «Retomar», «Viendo» y
«Pendientes» los refresca `EpisodeRefresher` con `strict=True`, sin escribir si la respuesta viene
vacía y releyendo la fila antes de escribir (trampa 17). «Finalizados», las filas sin `provider_id` y
las de un proveedor caído se quedan con el dato viejo. Para refrescar otra vista, `refresh()` del
servicio; no copiar su patrón.

### R10. Un `CTkButton` mide lo que pide su rejilla interna, no su `width`

Por dentro es una rejilla de 5 × 5 con propagación. Quien coloque botones con `place()` y lleve la
cuenta del ancho suma lo que reserva: `max(corner_radius, border_width + 1, border_spacing)` por lado,
1 px por lado de la etiqueta, 6 px entre texto e icono y 2 px por lado del icono. Se mide con
`winfo_reqwidth()`, no con `cget("width")`. Lo hace `GenreChips.__chip_width()`, con los números de
customtkinter 5.2.2. Familia de las trampas 19 y 20.

### R11. Todo `bind()` encima de un widget de CustomTkinter va con `add="+"`

Sin él sustituye, y CustomTkinter monta sus manejadores (`_clicked`, su hover) en el lienzo y la
etiqueta internos. Para excluir un widget de un recorrido que ata clics hay que excluir **su
subárbol**, no el widget: si no, la fila pisa el `command` de su propia píldora. Se comprueba
pulsando y contando qué manejador corre ([09 §6e](09-verificacion-y-pruebas.md)).

### R12. Quien mide su contenedor tiene que estar estirado hasta él

Con `sticky="w"` un widget mide su contenido, y sacar columnas de ese `winfo_width()` es un punto
fijo. `PosterGrid` va con `sticky="ew"` y peso en la columna del padre; el sobrante se reparte con
`weight=1` + `uniform`, y al encoger se **quita** el peso (trampa 22). Se comprueba midiendo a dos
anchos de ventana ([09 §6f](09-verificacion-y-pruebas.md)).

### R13. `wraplength` no deshace un `\n`

Un salto dentro del texto corta siempre. Todo texto de la red que se pinte con `wraplength` pasa antes
por una normalización: `wrap_synopsis()` vuelve espacio los saltos sueltos y conserva los dobles, que
son párrafos. Se hace al pintar, no al raspar.

### R14. Las etiquetas de servidor pasan por `__server_url_map()`

JKAnime puede ofrecer varios «Desu» en un mismo episodio, y un `{s.server: s.url}` se queda con el
último. `AnimeWindowViewer.__server_url_map()` numera los repetidos («Desu 2»).

### R15. Un hoster lento no da error: `LOAD_TIMEOUT_S`

El `network-timeout` de mpv cuenta por petición, y un servidor que contesta todo despacio deja
«Cargando» sin fin (zilla tardó ~70 s). `VideoPlayer` corta a los 30 s desde `play()` hasta el primer
`playback-restart`: para mpv y cae al navegador. Se cancela al empezar, en `stop_media()` y en `close()`.

### R16. Un `CTkImage` no sobrevive a sus widgets

`CTkLabel` y `CTkButton` no se desapuntan de su `CTkImage` al destruirse, así que uno compartido retiene
el árbol entero (49 → 239 MB en 75 cambios de vista). Las cachés guardan el dibujo PIL y devuelven un
`CTkImage` nuevo; los datos llevan el estado, no la imagen; compartir solo dentro de un componente que
muere entero. Se mide como dice [09 §6j](09-verificacion-y-pruebas.md).

### R17. Un desplegable que se destruye es un `OrderMenu`

El `DropdownMenu` de un `CTkOptionMenu` se queda en el registro de escalado al destruirse.
`ctk.CTkOptionMenu` a secas, solo en widgets que viven toda la sesión (los dos de la barra lateral).

### R18. `unbind_all()` no borra el comando de `bind_all()`

El comando Tcl, y todo lo que referencie, vive hasta que muere la raíz. Se guarda el *funcid* y se
llama a `deletecommand()` después de `unbind_all()`, como `VideoPlayer.set_fullscreen()` con sus
`__key_bindings`.

### R19. Toda identidad por título pasa por `title_similarity()`

Dos temporadas se parecen más que cualquier umbral («… 3rd Season» / «… 2nd Season»: 0,939).
`AnimeProviderManager.title_similarity()` da 0 si no coinciden los números del título («2nd»,
«Season 2» y «II» cuentan igual). La usan `find_saved_duplicate()`, `match_animes_from_search()` y
`resolve_anime_in_provider()`; `filter_animes_by_title()` no, a propósito, porque eso es buscar.
Nunca un `SequenceMatcher` suelto.

### R20. Todo widget de CustomTkinter lleva `font=`, aunque no tenga texto

Sin él crea su `CTkFont` en un ciclo de referencias. Si el recolector lo libera en un hilo recién
lanzado desde Tk, `Font.__del__` espera a Tk mientras Tk espera a que el hilo arranque: la aplicación
se congela sin error. `font=Theme.font(...)` siempre; se comprueba recorriendo `src/` con `ast`.

### R21. Para recorrer un `CTkFrame`, `tkinter.Misc.winfo_children()`

`CTkFrame.winfo_children()` oculta su `_canvas`, que es casi toda su superficie: atar eventos
recorriéndolo deja el fondo sin clic. `_walk()` de `franchise_cards.py` y `TabBar.__bind_tab()` usan el
de Tk; `PosterGrid.__clear_cells()` cuenta con lo contrario, para no destruir el lienzo. Se comprueba
pulsando con el ratón real en el fondo: `event_generate` sobre el marco no lo detecta.

### R22. Una vista conservada recoloca su hover al volver

Tk no manda `<Leave>` a un widget que deja de verse, así que la fila pulsada volvía encendida.
«Viendo» y «Pendientes» llaman a `AnimeRow.refresh_hover()` al reutilizar su página; una vista
conservada nueva con hover propio, igual.

### R23. Una celda nueva de `PosterGrid` pide 200 px un instante

Al repintar, el contenido encoge y el lienzo recorta el desplazamiento a 0. `__show_rec_items()` fija
el `minsize` de la fila de la rejilla mientras repinta. ⚠️ El paginador de las vistas no lo hace:
allí cambiar de página puede devolverte arriba.

### R24. `load_mpv()` solo desde un hilo daemon

La primera carga de una copia nueva de `libmpv-2.dll` —cada compilación crea una— la revisa el
antivirus 4,5-13 s, y mientras tanto Windows bloquea cualquier otra carga de DLL del proceso. La
ficha la carga en el hilo del resolutor, con la tarjeta «Cargando las librerías del reproductor». No
se precarga: dentro del proceso solo cambia de sitio el congelado; la vía medida sería un proceso hijo.

---

## Resumen: las 5 que más duelen

1. **Trampa 13** — en la ficha, `anime_info.id` no es la clave de la BD; confundirlas duplica filas
   en la biblioteca real. **La única que ya se ha reintroducido una vez.**
2. **Trampa 18** — reapuntar una fila a otro proveedor puede duplicarla: la BD no tiene `UNIQUE`.
3. **Trampa 3** — el orden de `episodes` depende del proveedor y se invierte al guardar; y hay una
   lista que **no** hay que invertir.
4. **Trampa 5** — marcar episodios sin estado asignado no guarda nada, sin avisar.
5. **Trampa 11** — la purga de pósters borra todo lo que no esté en la lista actual.

> **Cómo se mantiene este documento**: una trampa que ya no puede darse con el código actual se
> **borra**; una que el código evita pero cuya causa sigue viva pasa a **regla**. Al hacerlo se
> renumera y se actualizan las citas de `.claude/` (no las de los planes, que son historia).
