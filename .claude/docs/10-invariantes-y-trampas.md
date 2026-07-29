# 10 — Invariantes y trampas

| | |
|---|---|
| **Fecha** | 2026-07-28 · **Commit** `a972850` · árbol **sucio** |
| **Cubre** | los 18 módulos con contenido de `src/` + `MiBibliotecaAnime.spec` + `requirements.txt` |

Procedencia: ✅ verificado en ejecución · 📖 leído en código · ⚠️ sin verificar.

> **Este es el documento que hay que leer antes de tocar nada.** Cada entrada es «si tocas esto, se
> rompe aquello», con el **síntoma observable** que verás cuando lo rompas.

---

## Persistencia

### 1. El orden de `AnimeField` debe coincidir con el de las columnas físicas 📖

**Por qué**: todas las consultas son `SELECT *` y `SqlUtils.query_sql` (`utils/db/sqlite.py:57-63`)
empareja `fila[i] → FIELDS[i]` **por posición**, no por nombre.

**Si lo rompes**: reordenar `AnimeField` (`animesPersistence.py:28-47`), o insertar un miembro en
medio, desplaza todos los valores posteriores.

**Síntoma**: ningún error. Títulos donde deberían ir sinopsis, `is_favourite` con el valor de
`last_watched_episode`, JSON que no parsea y géneros que salen `[]`.

**Cómo comprobarlo**: `PRAGMA table_info(ANIMES)` y comparar con `AnimesPersistence.FIELDS`
([09 §3](09-verificacion-y-pruebas.md)). ✅ Hoy coinciden.

> ✅ **Mitigada desde 2026-07-30**: `validate_db_integrity()` (trampa 2) detecta el desorden y
> reconstruye la tabla realineándola con el orden declarado, copiando los datos por nombre de columna.
> El invariante sigue vigente — el orden de `AnimeField` **es** el contrato — pero reordenarlo ya no
> corrompe una BD existente: se corrige en el siguiente arranque.

---

### 2. Las migraciones son automáticas — declara el esquema, no el `ALTER TABLE` ✅ *(resuelta 2026-07-30)*

**Antes**: `start()` solo creaba la tabla si el `.db` no existía, así que una BD con datos nunca se
alteraba. Añadir un miembro a `AnimeField` desalineaba silenciosamente todas las lecturas (trampa 1)
**solo en las instalaciones con biblioteca previa** — funcionaba para quien escribía el cambio y
rompía para quien ya tenía datos.

**Ahora**: `start()` llama a `validate_db_integrity()` (`animesPersistence.py`), que compara la BD
física con `AnimesPersistence.SCHEMA` y aplica la corrección mínima: `CREATE TABLE` si falta la tabla,
`ALTER TABLE ADD COLUMN` si solo faltan columnas al final, y reconstrucción de la tabla (copiando **por
nombre de columna**, en una transacción) si cambia el orden o la afinidad de tipo. Copia de seguridad
en `resources/DB/backups/` antes de la primera modificación.

**Qué sigue siendo tu responsabilidad**:

- **Declarar el cambio en el sitio correcto.** Una columna nueva es un miembro de `AnimeField`; una
  tabla nueva es un `TableSchema` más en `SCHEMA`. Lo que no está declarado no se migra.
- **Actualizar `AnimeRecord`** (`to_db_dict` / `from_db_dict`) — la migración toca el esquema, no la
  serialización.
- **Valor por defecto**: una columna añadida a registros existentes llega a `NULL` salvo que se declare
  en `TableSchema.defaults`. `from_db_dict` debe tolerar `None`.
- **Columnas que ya existen en BD pero no en `SCHEMA` se descartan** al reconstruir (con aviso por
  consola; quedan en la copia de seguridad).

**Si lo rompes**: el único camino que sigue siendo peligroso es cambiar `AnimeField` y **no** ejecutar
la app antes de leer datos, o llamar a `query_sql` desde un proceso que no haya pasado por `start()`.

**Cómo comprobarlo**: `PRAGMA table_info(ANIMES)` frente a `AnimesPersistence.FIELDS`
([09 §3](09-verificacion-y-pruebas.md)). ✅ Verificado sobre copias de la BD real (24 filas) en los
seis escenarios de migración, incluida la idempotencia y el rollback.

---

### 3. `watched_episodes` se guarda como rangos comprimidos ✅

**Formato**: `{1,2,3,5,9}` → `[[1,3],[5,5],[9,9]]` (`_episodes_to_ranges:177-192`).

**Nunca escribas ese campo a mano.** Un elemento con longitud ≠ 2 se **descarta en silencio**
(`_ranges_to_episodes:199-200`).

**Síntoma**: episodios vistos que desaparecen sin error al recargar la ficha.

**Además**: `last_watched_episode` se recalcula siempre como `max(watched)` (`:319`); si escribes uno
a mano, el siguiente `update_watched_episodes` lo pisa.

---

### 4. `episodes` se guarda **invertido** y no se des-invierte al leer ✅

`to_db_dict:88` hace `list(reversed(...))`; `update_anime_episodes:331` hace `[::-1]`;
`from_db_dict` **no** deshace nada.

✅ Verificado: entrada `[1..10]` → BD `[10..1]` → leído `[10..1]`.

**Agravante**: el orden depende del **proveedor**. AnimeAV1 devuelve episodios **ascendentes**
(`animeav1.py:205`), AnimeFLV **descendentes** (`animeflv.py:222-223`). Es decir, el mismo anime
guardado desde un proveedor u otro queda **al revés** en BD.

**Síntoma**: `anime_record.episodes[0]` es el último episodio, no el primero. Lógicas de «por dónde
voy» que salen invertidas.

---

### 5. `update_*` devuelve `True` aunque no modifique ninguna fila ✅

`SqlUtils.update_sql` (`sqlite.py:32-46`) **nunca consulta `cursor.rowcount`**. `True` significa «el
SQL se ejecutó sin excepción».

| Método | Anime inexistente |
|---|---|
| `update_watched_episodes` | `False` ✅ (comprueba antes) |
| `update_anime_to_not_watching` / `not_finished` | `False` ✅ |
| `update_anime_episodes` | ⚠️ **`True`** |
| `update_anime_to_not_favourite` / `not_pending` | ⚠️ **`True`** |

**Esto contradice `CLAUDE.md`**, que afirma que todos devuelven `False`.

**Síntoma**: código que confía en el `bool` cree que guardó y no guardó nada.

---

### 6. `get_anime_by_genre_and_order` recibe un `str` donde espera un enum ✅

`AccordionFilterButton.__apply_filters` (`utilsButtons.py:187`) pasa `self.selected_order.get()` →
`"default"`. La comparación `order != AnimeOrderFilter.POR_DEFECTO` (`animesPersistence.py:294`) es
entonces **siempre `True`** → *return* temprano → **la ordenación por coincidencias de género nunca
se aplica desde la GUI**.

✅ Verificado: con el enum ordena; con el `str` no.

**Síntoma**: el filtro por género funciona, pero los resultados salen en orden de inserción en BD.

**Al arreglarlo**: convierte en el llamante (`AnimeOrderFilter(self.selected_order.get())`) **o**
compara por valor en la persistencia — no ambos.

---

### 7. Marcar episodios de un anime sin estado no persiste nada ✅

`update_watched_episodes` devuelve `False` sin escribir si el anime no está en `ANIMES`
(`animesPersistence.py:314-315`). Un anime solo entra en BD al pulsar uno de los 4 botones de estado
(`_set_status:439-447`).

**Síntoma**: el usuario marca episodios en la ficha de un anime recién descubierto, sale, vuelve, y
los switches están todos apagados. **Sin ningún mensaje.**

---

## Ficha de detalle

### 8. Solo se muestran los **25** primeros episodios 📖

`anime_window.py:263` → `self.anime_info.episodes[:25]`. (El comentario de `:302` dice «24»; el
código dice 25.)

**Interactúa con la trampa 4**: ✅ con AnimeAV1 (ascendente) verás los episodios **1-25**; con
AnimeFLV (descendente) los **25 más recientes**. El mismo anime, dos cortes distintos.

**Síntoma**: en un anime de 1171 episodios no hay forma de llegar al 600 salvo por el buscador de
episodios (`:363-377`).

---

### 9. El marcado de episodios es acumulativo; el desmarcado, unitario 📖

`__toggle_episode_switch` (`:399-452`):

- **Marcar** el episodio N marca **todos los ≤ N en orden real ascendente** (`:441-444`) y
  **conserva** los > N que ya estaban vistos en BD (`:446`).
- **Desmarcar** quita **solo** ese episodio (`:450`).

**Si lo cambias**: se pierde el caso de uso principal («voy por el 340»), que evita 340 clics.

⚠️ **Riesgo latente**: los pasos visuales indexan `self.episode_switches[index]` (`:417`, `:421`) con
un `index` calculado sobre `anime_info.episodes` **completo** (`:402`). Con la lista filtrada a un
episodio (`__search_episodes:373`) hay solo 1 switch → posible `IndexError`. Camino leído, no
reproducido.

---

### 10. `AnimeInfo.episodes` no puede ser `None` al abrir la ficha 📖

`anime_window.py:33` itera `self.anime_info.episodes` en el constructor.

`recentAnimes.py:86` sí lo comprueba antes; **las otras 5 vistas no** — llaman a `get_anime_info` y
pasan el resultado directamente (`favouriteAnimes.py:131-132` y homólogos). Si el manager devuelve
`None` (todos los proveedores fallan), `AnimeWindowViewer(mw, None)` peta en `:31`.

**Síntoma**: `TypeError: 'NoneType' object is not iterable` o
`AttributeError: 'NoneType' object has no attribute 'episodes'` al hacer clic sin conexión.

---

## Proveedores

### 11. `__init_subclass__` exige los 3 atributos a **toda** subclase ✅

La condición es `if ABC not in cls.__bases__` (`animeProviderMgr.py:59`), y solo `AnimeProvider`
lista `ABC` entre sus bases directas.

**Si lo rompes**: crear una base intermedia (`class ProveedorHTMLBase(AnimeProvider)`) sin
`PROVIDER_ID`/`PROVIDER_NAME`/`BASE_URL` **impide importar el módulo**.

**Síntoma**: `NotImplementedError: ProveedorHTMLBase debe definir el atributo de clase 'PROVIDER_ID'`
**al importar**, no al usar.

---

### 12. El fallback trata «vacío» igual que «error» ✅

`__is_empty_result` (`:193-202`): `None`, `[]` y `([], N)` cuentan como vacío → se prueba el siguiente
proveedor.

**Consecuencias**:

- Una búsqueda **legítimamente sin resultados** desencadena una petición extra a cada proveedor.
- La GUI **no distingue** «sitio caído» de «no hay resultados»: en ambos casos recibe `[]`.
- El `last_page` de una tupla vacía se **descarta** (`([], 7)` → se ignora el 7).
- Los wrappers devuelven `([], 1)` con **`1` constante** (`:262`, `:268`) → la paginación se colapsa.

---

### 13. `provider_id` desconocido + `strict=True` usa el primer proveedor registrado ✅

`_ordered_providers` (`:186-191`) no valida el `provider_id`: si no está registrado, simplemente no
antepone a nadie. Con `strict=True` se toma `[:1]` → **el primero por orden de registro**.

**Síntoma**: pides datos «solo de JKAnime», JKAnime no está registrado, y recibes datos de AnimeAV1
sin ningún aviso. `get()` sí lanza `UnknownProviderError` (`:169-170`) — pero los wrappers no usan
`get()`.

---

### 14. AnimeAV1 devuelve texto mal codificado ✅

`animeav1.com` responde `Content-Type: text/html` **sin `charset`** → `requests` asume `ISO-8859-1` →
`response.text` sale con mojibake y llega así a `AnimeInfo.synopsis`.

```
"…One Piece y el tÃ­tulo de Rey de los Piratas que lo acompaÃ±a."
```

**Alcance** ✅: afecta a `synopsis` (se muestra **y se persiste en BD**). No afecta a `genres` (slugs
ASCII) ni a los `id`. ⚠️ Afectaría a `title` con tildes; no comprobado.

**Síntoma**: sinopsis con `Ã­`, `Ã±`, `Ã³` en la ficha y en la BD.

Detalle y arreglo sugerido en [05 §7](05-proveedores-y-scraping.md).

---

## Imágenes y recursos

### 15. `get_anime_image()` **no** busca en `resources/images/watching/` ✅

`utils.py:168`:

```python
subfolders = ["favourite", "finished", "pending", "recent_animes", "search"]
```

**Falta `watching`** — pese a que `download_anime_poster_by_status(AnimeStatus.WATCHING, …)` guarda
ahí (`:53-60`, `status.name.lower()` → `"watching"`).

✅ Verificado: con el póster **solo** en `watching/`, `get_anime_image` **va a la red** (0,12 s) en vez
de leerlo del disco.

**Síntoma**: la ficha de un anime que solo está en «viendo» tarda más y depende de la conexión.
Combinado con la trampa 16, se ve además diminuto.

---

### 16. La rama de red de `get_anime_image()` olvida `size=` ✅

```python
# utils.py:176-177
response = requests.get(anime.poster)
return ctk.CTkImage(Image.open(BytesIO(response.content)).resize(image_size))
#                   ↑ redimensiona el PIL, pero NO pasa size= al CTkImage
```

`CTkImage` sin `size=` usa su valor por defecto. ✅ Verificado: devuelve un `CTkImage` de **20×20** en
vez de `(195, 275)`.

**Síntoma**: en la ficha de detalle, el póster aparece como un **cuadradito diminuto** siempre que
haya que descargarlo (es decir, siempre que el anime solo esté en «viendo», o no esté cacheado).

**Arreglo**: `ctk.CTkImage(Image.open(BytesIO(response.content)), size=image_size)`.

---

### 17. La purga de pósters borra lo que no está en la lista actual ✅

`download_animes_poster:97-105` y `download_images_progress:155-163` eliminan **todo** fichero del
directorio que no corresponda a un anime de la lista recibida.

**Consecuencias verificadas**:

- ✅ `resources/images/search` se **vacía en cada búsqueda** (`searchAnimes.py:229`).
- ✅ `load_image` (`utils.py:181`) deja el fichero **abierto** (PIL perezoso) → `os.remove` lanza
  `PermissionError` en Windows mientras el `CTkImage` viva. Está capturado, así que solo imprime.
- ✅ En la caché real del usuario hay un huérfano `Chi.` (0 bytes) que `os.listdir` lista pero
  `os.remove` no puede borrar → **aviso en cada arranque**:
  `No se pudo borrar la imagen Chi.: [WinError 2]…`
  ⚠️ El origen exacto de ese fichero no está verificado.

**Si llamas a estas funciones con una lista parcial, borras el resto de la caché.**

---

### 18. Trampas de empaquetado y de entorno

**a) `MiBibliotecaAnime.spec` está desactualizado** 📖 (`:21-36`):

| Problema | Línea |
|---|---|
| Falta `APIs.animeav1.animeav1` | — |
| Falta `APIs.common.animeProviderMgr` | — |
| Falta `APIs.common.models` | — |
| Declara `gui.anime_windows` (el módulo real es `gui.anime_window`) | `:31` |
| Declara `gui.sidebarButtons.sidebarButton` (**no existe** tal módulo) | `:30` |

**Síntoma**: `ModuleNotFoundError` al arrancar el `.exe`, no al compilar.

**b) `attrs` no declarada** — ✅ **RESUELTO (2026-07-28)**:

`searchAnimes.py:15` hacía `from attr import dataclass`, del paquete **`attrs`** (24.2.0), ausente de
`requirements.txt` y presente en el entorno solo por accidente, como transitiva de
`selenium → trio → outcome → attrs`. En un entorno limpio creado solo con `requirements.txt` daba
`ModuleNotFoundError: No module named 'attr'` al importar `main_window`.

**Arreglo aplicado**: sustituido por `from dataclasses import dataclass` (stdlib), consistente con
`models.py:13` y `animesPersistence.py:9`. `AnimeSearch` solo usa defaults simples, así que el
comportamiento no cambia. ✅ Verificado: el módulo importa, `dataclasses.is_dataclass(AnimeSearch)`
es `True` y la instancia se construye. `src/` ya no referencia `attrs` ni `selenium`.

> **Ojo si vuelves a ver este import**: `attr.dataclass` **no** es `dataclasses.dataclass`, sino
> `functools.partial(attrs, auto_attribs=True)`. Es un alias no documentado que los IDE ofrecen en
> el autocompletado — fue justo el origen de este fallo.

**c) `console=False` en el `.spec`** 📖 (`:60`): todos los `print` desaparecen en el `.exe`. Para
depurar el empaquetado, cambia temporalmente a `console=True`.

**d) `datas` del `.spec` incluye `resources/DB`** 📖 (`:12`): se **empaqueta la BD del desarrollador**
dentro del ejecutable. ⚠️ No verificado qué ocurre al distribuirlo, pero es un problema de privacidad
evidente.

---

### 19. `watchingAnimes/__init__.py` contiene un stub que suplanta la clase real 📖

```python
# src/gui/sidebarButtons/watchingAnimes/__init__.py
class WatchingAnimeButton:
    pass
```

`main_window.py:25` importa desde `…watchingAnimes.watchingAnimes` (el módulo), así que **hoy no se
usa**. Pero `from gui.sidebarButtons.watchingAnimes import WatchingAnimeButton` importaría el stub
**sin ningún error de importación**.

**Síntoma**: `TypeError` al construir, o un botón que no aparece en la sidebar.

**Los otros 15 `__init__.py` están vacíos.** Mantenlo así.

---

### 20. `removeprefix()` devuelve `None` si los tipos no coinciden 📖

```python
# utils.py:34-38
if type(text) is type(prefix_text):
    ...
# ← falta el else: devuelve None implícitamente
```

Lo usan `animeflv.py:63,112,172` y `animeav1.py:258` para construir el `anime_id`.

**Síntoma**: `anime.id` vale `None` → el póster se guarda como `None.jpg` y la ficha no carga.
⚠️ No reproducido; con las entradas actuales ambos argumentos son siempre `str`.

---

## Resumen: las 5 que más duelen

1. **Trampa 4** — el orden de `episodes` depende del proveedor y se invierte al guardar.
2. **Trampa 16** — el póster se ve a 20×20 cada vez que hay que descargarlo.
3. **Trampa 7** — marcar episodios sin estado asignado no guarda nada, sin avisar.
4. **Trampa 15** — `get_anime_image()` no busca en `watching/`, así que va a la red sin necesidad.
5. **Trampa 6** — la ordenación por géneros nunca se aplica desde la GUI (`str` vs enum).

> Las trampas **1** y **2** (desalineación de columnas y ausencia de migraciones) encabezaban esta
> lista hasta el 2026-07-30. `validate_db_integrity()` las mitiga; el invariante del orden de
> `AnimeField` sigue vigente, pero ya no corrompe datos en silencio.
