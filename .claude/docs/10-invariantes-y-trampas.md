# 10 — Invariantes y trampas

| | |
|---|---|
| **Fecha** | 2026-08-06 · **Commit** `fd53056` · árbol **sucio** |
| **Cubre** | los 19 módulos con contenido de `src/` + `MiBibliotecaAnime.spec` + `requirements.txt` |
| **Última revisión** | 2026-08-06: **trampas 23, 24 y 25** (JKAnime), en una sección nueva de proveedores concretos |

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
(`animeav1.py:227`), AnimeFLV **descendentes** (`animeflv.py:222-223`). Es decir, el mismo anime
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

`anime_window.py:294` → `self.anime_info.episodes[:25]`. (El comentario de `:302` dice «24»; el
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

### ~~10. `AnimeInfo.episodes` no puede ser `None` al abrir la ficha~~ ✅ **Resuelto (2026-07-30, `1bfdf0f`)**

Era el bug B5. El constructor iteraba `self.anime_info.episodes` sin ninguna guarda, y **las 6 vistas**
pasaban directamente el resultado de `get_anime_info`, que devuelve `None` cuando fallan *todos* los
proveedores. Síntoma: `AttributeError: 'NoneType' object has no attribute 'episodes'`, que Tkinter se
tragaba — así que el clic simplemente **no hacía nada**, sin ningún mensaje.

**Contrato vigente** (📖 `anime_window.py:30-64`), en tres capas:

| Capa | Dónde | Qué hace |
|---|---|---|
| Aviso al usuario | `show_anime_info_error()` `anime_window.py:30-46` | `print` + `messagebox.showerror` |
| Guarda en los 6 clics | `favouriteAnimes.py:132-134` y homólogos | `if anime_clicked is None: show_anime_info_error(...); return` |
| Contrato del constructor | `anime_window.py:51-59` | `None` → `ValueError`; `episodes=None` → `replace(…, episodes=[])` |

**Si lo rompes**: al añadir una vista nueva, olvidar la guarda devuelve el síntoma original. La única
señal será el `ValueError` en consola, porque Tkinter sigue tragándose la excepción del callback.

⚠️ La normalización de `episodes` se hace sobre **una copia** (`dataclasses.replace`), no muta el
`AnimeInfo` recibido. Es deliberado: el `None` del objeto cacheado en `main_window.recent_animes` es
justo lo que marca que aún le falta la precarga (`main_window.py:235`), y ponerlo a `[]` lo daría por
precargado para siempre.

> **Corrección a la versión anterior de esta trampa**: decía que `recentAnimes.py` «sí lo comprueba
> antes». Solo a medias — comprobaba el `None` pero luego caía de vuelta al objeto obsoleto, cuyo
> `.episodes` es precisamente `None`, así que petaba igual por la otra puerta. Ahora muestra el error y
> no abre la ficha (`recentAnimes.py:90-101`), y además restaura el cursor `watch` antes de cualquier
> salida — antes se quedaba clavado si la construcción de la ficha fallaba.

✅ Verificado el 2026-07-30 simulando la caída total de proveedores sobre el `__on_anime_click` real de
`favouriteAnimes`: sale el diálogo y no se propaga excepción.

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

### ~~14. AnimeAV1 devuelve texto mal codificado~~ ✅ **Resuelto (2026-07-30, `94b497e`)**

Era el bug A5. `animeav1.com` responde `Content-Type: text/html` **sin `charset`**, así que requests
aplicaba el defecto de la RFC 2616 (`ISO-8859-1`) y `response.text` salía con mojibake:

```
"…One Piece y el tÃ­tulo de Rey de los Piratas que lo acompaÃ±a."
```

**Arreglo**: todo el scraping pasa por `_fetch()` (📖 `animeav1.py:37-56`), que fija UTF-8 **solo si el
servidor no declara charset**, de modo que si algún día lo declara se respeta el suyo:

```python
response = requests.get(url, **kwargs)
if "charset" not in response.headers.get("Content-Type", "").lower():
    response.encoding = "utf-8"
```

**Invariante que queda**: debe haber **exactamente una** aparición de `requests.get` en el módulo, la de
dentro de `_fetch`. Añadir una petición directa reintroduce el bug solo en esa ruta.

**Corrección de alcance**: la versión anterior de esta trampa decía que solo afectaba a `synopsis` y
daba `title` por no comprobado. ✅ Verificado el 2026-07-30: **también afectaba a `title`**, porque
`__parse_anime_cards` lo saca del DOM (`animeav1.py:293`), que sale del mismo `response.text`. No
afectaba a `genres` (slugs ASCII) ni a los `id`.

✅ Verificado contra el sitio real: ficha, portada y búsqueda, 0 marcadores `Ã`/`Â` en los tres casos.

> **Datos ya contaminados**: 3 de las 25 filas de la BD real tenían la sinopsis rota de antes del
> arreglo. Se repararon el 2026-07-30 re-descargando la ficha con el scraper ya corregido (copia previa
> en `resources/DB/backups/DB_Animes_20260730_013507.db`). La diferencia de longitud coincidió
> exactamente con el número de marcadores en las 3, confirmando que el texto solo cambió en eso.
> **Si el scraper vuelve a romperse así, la BD se contamina otra vez**: el arreglo del código no
> repara lo ya guardado.

---

## Imágenes y recursos

### ~~15. `get_anime_image()` **no** busca en `resources/images/watching/`~~ ✅ **Resuelto (2026-07-30, `83a8448`)**

Era el bug B1. La lista de `utils.py:168` omitía `watching`, pese a que
`download_anime_poster_by_status(AnimeStatus.WATCHING, …)` guarda ahí (`utils.py:53-60`,
`status.name.lower()` → `"watching"`). Ahora incluye las **6** categorías:

```python
subfolders = ["favourite", "watching", "finished", "pending", "recent_animes", "search"]
```

**Invariante que queda**: toda carpeta a la que escriba `download_anime_poster_by_status` debe estar en
esta lista. Como el nombre sale de `AnimeStatus.name.lower()`, **añadir un estado nuevo obliga a tocar
`utils.py:168`** ([11 §1](11-playbooks.md)).

✅ Verificado el 2026-07-30 con `one-piece-gyojin-touhen`, que en la BD real está **solo** en
`watching/`: se resuelve desde disco pasándole a propósito una URL inválida — si hubiera caído a la
rama de red, habría fallado la conexión.

---

### ~~16. La rama de red de `get_anime_image()` olvida `size=`~~ ✅ **Resuelto (2026-07-30, `83a8448`)**

Era el bug A4. La trampa de fondo **sigue viva para cualquier código nuevo**: `CTkImage` maneja dos
tamaños independientes.

| | Qué es | Quién lo fija |
|---|---|---|
| PIL interno | píxeles reales de la imagen | `Image.open(...)` / `.resize(...)` |
| `size=` | **lo que se pinta**; defecto `(20, 20)` | el parámetro de `CTkImage` |

`.resize((195, 275))` sin `size=` producía un PIL de 195×275 renderizado a 20×20: el redimensionado se
hacía y se tiraba. Ahora (`utils.py:176-177`) la rama de red se comporta igual que `load_image()`:

```python
response = requests.get(anime.poster, timeout=_REQUEST_TIMEOUT)
return ctk.CTkImage(Image.open(BytesIO(response.content)), size=image_size)
```

Se pasa el PIL **sin redimensionar** a propósito: del escalado se encarga CTk, y conservar la
resolución original se ve mejor en HiDPI, que es justo para lo que existe `size=`.

**Si lo rompes**: cualquier `CTkImage(...)` sin `size=` en código nuevo sale a 20×20. El síntoma es un
cuadradito diminuto, **no un error**.

✅ Verificado el 2026-07-30 contra un póster real de AnimeAV1: `(195, 275)` pintado, PIL de origen
225×350 conservado.

> En el mismo cambio se añadió `timeout=_REQUEST_TIMEOUT`: era la única petición del módulo sin timeout
> y corre **en el hilo de UI** (`anime_window.py:107`), así que un servidor de imágenes colgado
> congelaba la aplicación indefinidamente.

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

**a) ~~`MiBibliotecaAnime.spec` está desactualizado~~** — 🚧 **casi resuelto (2026-08-06)** 📖:

| Problema | Estado |
|---|---|
| Faltaba `APIs.animeav1.animeav1` | ✅ añadido |
| Faltaba `APIs.common.animeProviderMgr` | ✅ añadido |
| Faltaba `APIs.common.models` | ✅ añadido |
| Faltaba `dataPersistence.userPersistence` | ✅ añadido |
| Faltaba `APIs.jkanime.jkanime` | ✅ añadido con el proveedor |
| Declaraba `gui.anime_windows` (el módulo real es `gui.anime_window`) | ✅ corregido |
| Declara `gui.sidebarButtons.sidebarButton` (**no existe** tal módulo) | ⚠️ **pendiente** |

**Síntoma**: `ModuleNotFoundError` al arrancar el `.exe`, no al compilar.

⚠️ **La corrección no se verificó compilando**: se hizo leyendo los `import` reales. Sigue siendo
obligatorio arrancar el `.exe` antes de distribuir. Y el problema **grave** del `.spec` no es este,
sino que `datas` empaqueta `resources/DB` ([12 §4 → A3](12-deuda-tecnica-y-roadmap.md)); eso **no se
ha tocado**.

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

Lo usan `animeflv.py:63,112,172` y `animeav1.py:280` para construir el `anime_id`.

**Síntoma**: `anime.id` vale `None` → el póster se guarda como `None.jpg` y la ficha no carga.
⚠️ No reproducido; con las entradas actuales ambos argumentos son siempre `str`.

---

## Proveedor seleccionable *(añadidas 2026-07-30)*

### 21. En la ficha, `anime_info.id` **no** es la clave de la biblioteca ✅

`AnimeWindowViewer` maneja **dos identidades** del mismo anime, y confundirlas **escribe filas
duplicadas en la biblioteca real del usuario**:

| Atributo | Qué es | Puede diferir del otro |
|---|---|---|
| `self.anime_info.id` | slug del proveedor que **sirvió** la ficha | **sí** |
| `self.persistence_anime_id` | slug con el que se **abrió** la ficha | **no, nunca cambia** |

`AnimeInfo.id` es el slug del sitio, no un identificador universal: el mismo anime es
`one-piece-gyojin-touhen` en AnimeAV1 y `one-piece` en AnimeFLV.

**Regla**: en `anime_window.py`, **toda** llamada a `animes_persistence` y a
`download/remove_anime_poster_by_status` usa `self.persistence_anime_id` o
`self.__persistence_anime_info()`. Nunca `self.anime_info` a secas.

**Síntoma si se incumple**: pulsas «Añadir a favoritos» y el anime aparece **dos veces** en la vista
de favoritos, con dos pósters en disco; o pulsas «Eliminar de favoritos» y no desaparece, porque se ha
desmarcado una fila distinta de la que ve la vista.

⚠️ **Sigue viva aunque la ficha ya no permita cambiar de proveedor** (el desplegable se retiró el
2026-08-06, [13 §12](13-selector-de-proveedor.md)). Lo que la dispara ahora no es un clic del usuario
sino el **fallback**: si el proveedor en uso falla, `call_with_fallback` sirve la ficha desde otro y
`anime_info.id` deja de coincidir con la fila guardada, sin que nada lo anuncie salvo la etiqueta
«Proveedor:». Volverá a poder provocarse a voluntad con la columna `provider_id`
([13 §8](13-selector-de-proveedor.md)).

✅ Verificado el 2026-07-30 sobre una copia de la BD real (25 filas): tras cambiar de proveedor y
pulsar los 8 botones de estado, siguen habiendo 25 filas y ninguna con el slug del otro proveedor.
Ver [13 D5](13-selector-de-proveedor.md) y el script de [09](09-verificacion-y-pruebas.md).

### 22. El `wraplength` de la ficha se calcula sobre el `content_frame`, no sobre la celda 📖

La sinopsis y los géneros fijan `wraplength = content_frame.winfo_width() - 275`. Ese número **no sabe
nada del reparto real de columnas**, así que cualquier widget nuevo que reserve ancho en las columnas
1-3 hace que el texto se pinte más ancho que su celda y **se recorte por la derecha**.

**Síntoma**: la sinopsis aparece cortada a media palabra en el borde derecho (`…termina a bordo`,
`…Luffy es un`) sin ningún error por consola.

✅ Ocurrió de verdad al colocar el selector de proveedor en `row=0, column=2, columnspan=2`. La
solución fue darle **su propia fila** abarcando las columnas 1-3, que no obliga a ninguna columna a
reservar ancho. Si añades algo a la derecha del título, compruébalo con una captura, no a ojo:
el layout no lanza ningún aviso.

⚠️ La colocación se mantiene aunque el 2026-08-06 aquel desplegable pasara a ser una **etiqueta**, que
ocupa menos: lo que dispara la trampa no es el ancho del widget, sino **en qué columnas se declara**.
Re-verificado por captura ese día: la sinopsis sigue ocupando el ancho completo.

**Invariante vivo**: mientras el `wraplength` siga siendo un número calculado a mano, la fila 0 de la
ficha es el único sitio seguro para meter controles a la derecha.

---

## Proveedores concretos

### 23. En JKAnime, el `<img>` de la portada lleva **dos** imágenes ✅

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

### 24. Las rejillas vacías de JKAnime no significan «hace falta renderizar JS» ✅

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

### 25. En JKAnime, el slug y el id numérico no son intercambiables ✅

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

Es la misma clase de confusión que la **trampa 21**, pero dentro de un proveedor en vez de en la
ficha de detalle.

---

## Resumen: las 5 que más duelen

1. **Trampa 21** — en la ficha, `anime_info.id` no es la clave de la BD; confundirlas duplica filas
   en la biblioteca real.
2. **Trampa 4** — el orden de `episodes` depende del proveedor y se invierte al guardar.
3. **Trampa 7** — marcar episodios sin estado asignado no guarda nada, sin avisar.
4. **Trampa 6** — la ordenación por géneros nunca se aplica desde la GUI (`str` vs enum).
5. **Trampa 17** — la purga de pósters borra todo lo que no esté en la lista actual.

*(Cae de la lista la trampa 8 —solo 25 episodios—, que sigue vigente pero duele menos que la 21.)*

> **Trampas retiradas de esta lista el 2026-07-30**, todas por estar resueltas: **1** y **2**
> (desalineación de columnas y ausencia de migraciones, mitigadas por `validate_db_integrity()`),
> **15** y **16** (el póster a 20×20 y la carpeta `watching/` olvidada), **10** (clic sin comprobar
> `None`) y **14** (mojibake de AnimeAV1).
>
> Las entradas **no se renumeran ni se borran**: otros documentos las citan por número. Una trampa
> resuelta se marca tachada y conserva su invariante vigente, si le queda alguno.
