# 10 — Invariantes y trampas

| | |
|---|---|
| **Fecha** | 2026-10-28 · rama `release/0.5.0` · sobre **`7bbbb3c`** |
| **Cubre** | los **43** módulos con contenido de `src/` (42 + `app.py`) + `MiBibliotecaAnime.spec` + `requirements.txt` |
| **Última revisión** | 2026-10-29 (**clic en las tarjetas**): trampa **81** nueva —`CTkFrame.winfo_children()` oculta su lienzo, así que el fondo de las tarjetas de relacionados y el margen de las pestañas no respondían al clic—, resuelta; la **73** corregida, que daba los lienzos por atados. Antes, 2026-10-28 (**versión 0.5.0**: temporadas, relacionados, «Te puede interesar» y vistas conservadas): **22 trampas nuevas, de la 59 a la 80**, en cinco apartados: **relaciones y franquicia** (59-66: tipos que no son lo que parecen, parseo del payload de AnimeAV1 y de la sección de JKAnime, reintentos, el mismo slug en otro sitio, el 429 de JKAnime y los géneros con O), **verificar fuera de la aplicación** (67-70), **lo que cuesta pintar con CustomTkinter** (71-76: un marco de 1 px no pinta, ~3,5 ms por widget, el `bind` doble, volver a una página no es gratis…), **hilos y recolección** (77, 🔴 **un widget sin `font=` puede congelar la aplicación** al lanzar un hilo, con 17 pendientes; y 78) y **ficha con pestañas y vistas conservadas** (79-80). Al día la **11** (cuatro atributos obligatorios), la **13** (los wrappers nuevos validan), la **29** (el ancho por defecto de 200 px), la **32** (las vistas componen en su página) y la **37** (el separador de `EpisodeRow` desapareció). Antes, 2026-10-27 (**refresco de episodios**): la trampa **38** pasa a **resuelta** —«Viendo» y «Pendientes» se refrescan con `EpisodeRefresher`, en segundo plano y repintando en el sitio— salvo en «Finalizados», que queda fuera a propósito. Antes, 2026-10-26 (**temporadas distintas**): trampa **58** nueva, en un apartado propio —dos temporadas del mismo anime se parecen como texto más que el umbral de «es el mismo», y la 3.ª de Kusuriya escribía en la fila de la 2.ª—, resuelta con `title_similarity()`, que exige que coincidan los números del título. Antes, 2026-10-21 (**auditoría de rendimiento**): **3 trampas nuevas** (55-57) en un apartado propio, «Ciclo de vida de los widgets de CustomTkinter», las tres con el mismo patrón —algo de larga vida sigue apuntando a un widget ya destruido y lo retiene con todo su árbol—: un `CTkImage` que vive más que su widget (**55**, la fuga que crecía ~2,4 MB por cambio de vista), un `CTkOptionMenu` destruido que se queda en el registro de escalado (**56**) y `unbind_all()`, que no borra el comando de `bind_all()` (**57**). Las tres medidas y resueltas el mismo día, desde el código del proyecto y sin parchear CustomTkinter. Antes, 2026-10-20 (**reproductor in-app**, plan de 7 fases en `plan-reproductor/`): **12 trampas nuevas** (43-54) en un apartado propio, más la **18f** (la DLL de libmpv y dónde la busca `python-mpv`), que es de empaquetado y va con las demás de la 18. Tres familias: **hosters** (43-45: cabeceras que uno exige y otro rechaza, URLs que caducan o van atadas a la IP), **mpv** (46-48: sus eventos llegan en otro hilo, el final no es un evento y un corte parece un final) y **la superficie nativa dentro de Tk** (49-52), donde tres de las cinco **corrigen** lo que el plan daba por hecho: encima del vídeo **sí** se ve un widget hermano, y el ratón y el teclado **sí** llegan a Tk. La **54** —un hoster **lento** deja «Cargando» sin tope— salió en la propia prueba de humo de la fase 6 y sigue **abierta**. La **53** es el bug de los servidores repetidos («B1» del plan del reproductor, que **no** es el B1 de [12 §4](12-deuda-tecnica-y-roadmap.md)), ya resuelto. Antes, 2026-09-02 (**rejillas adaptables y sinopsis**): **2 trampas nuevas**, las dos con el mismo patrón —un widget que *parece* medir el sitio que tiene y no lo mide—: la **41**, una rejilla colocada con `sticky="w"` mide **su propio contenido**, así que calcular columnas de su ancho es un punto fijo que nunca cambia; y la **42**, `wraplength` **no puede deshacer un `\n`** que traiga el texto, por ancha que sea la ventana. Las dos estuvieron vivas y calladas desde el rediseño. La **32** gana su segunda mitad: los pesos `uniform` de `PosterGrid` también sobreviven a destruir las celdas. Antes, 2026-09-01 (**abrir la ficha por un episodio**): trampa **40** nueva —un `bind()` sin `add="+"` **borra** el manejador que el widget ya tenía, y excluir un botón de un recorrido **no excluye su interior**—, en un apartado propio; es la que explica por qué «Empezar» **nunca** movió un anime a «Viendo». La **37** gana la corrección de por qué `AnimeRow` sigue sin sufrirla. Antes, 2026-09-01 (**ancho de las fichas de género**): trampa **39** nueva —un `CTkButton` no respeta el `width` que se le pide: su rejilla interna propaga tamaño y el ancho *pedido* gana—, en un apartado propio, con la aritmética exacta de lo que reserva por dentro. Antes, 2026-09-01 (**refresco de la banda «Retomar»**): trampa **38** nueva —una fila guardada no refresca sus episodios sola, así que un anime en emisión miente hasta que abres su ficha—, **resuelta solo para las ≤3 tarjetas de la portada** y viva en el resto de la biblioteca. Antes, 2026-09-01 (**hover de la lista de episodios**): trampa **37** nueva —un hijo sin `bind` es una salida de la que no llega ningún `<Leave>`, la complementaria de la **34**—, con la nota de que **no se reproduce moviendo el ratón deprisa**. Antes, 2026-08-31 (**fondo de la pantalla de carga**): trampa **36** nueva —un widget sin `fg_color` sale del gris por defecto de CustomTkinter, no de `Theme`—, con el `minsize` que sobrevive a `grid_forget()` y el GIF transparente como medias trampas; la **33** gana un aviso: el comentario que la anclaba en el código ya no está. Antes, 2026-08-21 (**rediseño de interfaz**): **7 trampas nuevas** (29-35), todas de CustomTkinter y de layout, en un apartado propio; la **33** nace ya resuelta. La trampa **22** queda cerrada: la ficha ya no calcula anchos a mano. Antes, 2026-08-17 (**licencia y empaquetado**): la trampa **18** se subdivide en **a-e** — **18d cerrada** (`datas` ya no lleva datos de usuario; PyInstaller **ignora en silencio las carpetas vacías**) y **18e nueva** (los destinos de `datas` caen dentro de `_internal/`, no junto al `.exe`). Antes, 2026-08-16 (**columna `provider_id`**): **3 trampas nuevas** (26, 27, 28), trampa **21 reescrita** —ahora se puede provocar a voluntad y la ficha la señala en pantalla—, trampas **4** y **13** ampliadas, y anclas de `anime_window.py` (647→1156) y `animesPersistence.py` reubicadas |

Procedencia: ✅ verificado en ejecución · 📖 leído en código · ⚠️ sin verificar.

> **Este es el documento que hay que leer antes de tocar nada.** Cada entrada es «si tocas esto, se
> rompe aquello», con el **síntoma observable** que verás cuando lo rompas.

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

### 4. `episodes` se guarda **invertido** y no se des-invierte al leer ✅

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

### 5. `update_*` devuelve `True` aunque no modifique ninguna fila ✅

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

### 6. `get_anime_by_genre_and_order` recibe un `str` donde espera un enum ✅ *(resuelta, 2026-10-21)*

> ✅ **Resuelta en la persistencia.** El llamante de abajo **desapareció con el rediseño**
> (2026-08-21), así que desde entonces el método no tiene llamantes y el fallo no se veía. Pero el
> resto del código —la vista «Buscar» y los tres proveedores— maneja el orden como **`value`**
> (`str`), así que el siguiente que lo usara caería igual. Desde el 2026-10-21 el método **acepta las
> dos formas** (`order in (POR_DEFECTO, POR_DEFECTO.value)`). ✅ Verificado sobre copia de la BD en
> los cuatro estados: con el enum y con el `str` sale el mismo orden por coincidencias. Lo de abajo es
> la historia.

`AccordionFilterButton.__apply_filters` (`utilsButtons.py:341`) pasa `self.selected_order.get()` →
`"default"`. La comparación `order != AnimeOrderFilter.POR_DEFECTO` (`animesPersistence.py:384`) es
entonces **siempre `True`** → *return* temprano → **la ordenación por coincidencias de género nunca
se aplica desde la GUI**.

✅ Verificado: con el enum ordena; con el `str` no.

**Síntoma**: el filtro por género funciona, pero los resultados salen en orden de inserción en BD.

**Al arreglarlo**: convierte en el llamante (`AnimeOrderFilter(self.selected_order.get())`) **o**
compara por valor en la persistencia — no ambos. *(Se eligió lo segundo: es lo que hace el resto del
código.)*

---

### 7. Marcar episodios de un anime sin estado no persiste nada ✅

`update_watched_episodes` devuelve `False` sin escribir si el anime no está en `ANIMES`
(`animesPersistence.py:358`). Un anime solo entra en BD al pulsar uno de los 4 botones de estado
(`_set_status:483-491`).

**Síntoma**: el usuario marca episodios en la ficha de un anime recién descubierto, sale, vuelve, y
los switches están todos apagados. **Sin ningún mensaje.**

---

## Ficha de detalle

### 8. Solo se muestran los **25** primeros episodios 📖

`anime_window.py:453` → `self.anime_info.episodes[:25]`. (El comentario de `:447` dice «24»; el
código dice 25.)

**Interactúa con la trampa 4**: ✅ con AnimeAV1 (ascendente) verás los episodios **1-25**; con
AnimeFLV (descendente) los **25 más recientes**. El mismo anime, dos cortes distintos.

**Síntoma**: en un anime de 1171 episodios no hay forma de llegar al 600 salvo por el buscador de
episodios (`:508-522`).

---

### 9. El marcado de episodios es acumulativo; el desmarcado, unitario 📖

`__toggle_episode_switch` (`:544-597`):

- **Marcar** el episodio N marca **todos los ≤ N en orden real ascendente** (`:586-589`) y
  **conserva** los > N que ya estaban vistos en BD (`:591`).
- **Desmarcar** quita **solo** ese episodio (`:595`).

**Si lo cambias**: se pierde el caso de uso principal («voy por el 340»), que evita 340 clics.

⚠️ **Riesgo latente**: los pasos visuales indexan `self.episode_switches[index]` (`:559-562`, `:566`) con
un `index` calculado sobre `anime_info.episodes` **completo** (`:547`). Con la lista filtrada a un
episodio (`__search_episodes:508`) hay solo 1 switch → posible `IndexError`. Camino leído, no
reproducido.

---

### ~~10. `AnimeInfo.episodes` no puede ser `None` al abrir la ficha~~ ✅ **Resuelto (2026-07-30, `1bfdf0f`)**

Era el bug B5. El constructor iteraba `self.anime_info.episodes` sin ninguna guarda, y **las 6 vistas**
pasaban directamente el resultado de `get_anime_info`, que devuelve `None` cuando fallan *todos* los
proveedores. Síntoma: `AttributeError: 'NoneType' object has no attribute 'episodes'`, que Tkinter se
tragaba — así que el clic simplemente **no hacía nada**, sin ningún mensaje.

**Contrato vigente** (📖 `anime_window.py:30-65`), en tres capas:

| Capa | Dónde | Qué hace |
|---|---|---|
| Aviso al usuario | `show_anime_info_error()` `anime_window.py:200-216` | `print` + `messagebox.showerror` |
| Guarda en los 6 clics | `favouriteAnimes.py:134-139` y homólogos | `if anime_clicked is None: show_anime_info_error(...); return` |
| Contrato del constructor | `anime_window.py:78-106` | `None` → `ValueError`; `episodes=None` → `replace(…, episodes=[])` |

**Si lo rompes**: al añadir una vista nueva, olvidar la guarda devuelve el síntoma original. La única
señal será el `ValueError` en consola, porque Tkinter sigue tragándose la excepción del callback.

⚠️ La normalización de `episodes` se hace sobre **una copia** (`dataclasses.replace`), no muta el
`AnimeInfo` recibido. Es deliberado: el `None` del objeto cacheado en `main_window.recent_animes` es
justo lo que marca que aún le falta la precarga (`main_window.py:442`), y ponerlo a `[]` lo daría por
precargado para siempre.

> **Corrección a la versión anterior de esta trampa**: decía que `recentAnimes.py` «sí lo comprueba
> antes». Solo a medias — comprobaba el `None` pero luego caía de vuelta al objeto obsoleto, cuyo
> `.episodes` es precisamente `None`, así que petaba igual por la otra puerta. Ahora muestra el error y
> no abre la ficha (`recentAnimes.py:92-107`), y además restaura el cursor `watch` antes de cualquier
> salida — antes se quedaba clavado si la construcción de la ficha fallaba.

✅ Verificado el 2026-07-30 simulando la caída total de proveedores sobre el `__on_anime_click` real de
`favouriteAnimes`: sale el diálogo y no se propaga excepción.

---

## Proveedores

### 11. `__init_subclass__` exige los 4 atributos a **toda** subclase ✅

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

### 12. El fallback trata «vacío» igual que «error» ✅

`__is_empty_result` (`:231-240`): `None`, `[]` y `([], N)` cuentan como vacío → se prueba el siguiente
proveedor.

**Consecuencias**:

- Una búsqueda **legítimamente sin resultados** desencadena una petición extra a cada proveedor.
- La GUI **no distingue** «sitio caído» de «no hay resultados»: en ambos casos recibe `[]`.
- El `last_page` de una tupla vacía se **descarta** (`([], 7)` → se ignora el 7).
- Los wrappers devuelven `([], 1)` con **`1` constante** (`:314`, `:320`) → la paginación se colapsa.

---

### 13. `provider_id` desconocido + `strict=True` usa el primer proveedor registrado ✅

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

### ~~14. AnimeAV1 devuelve texto mal codificado~~ ✅ **Resuelto (2026-07-30, `94b497e`)**

Era el bug A5. `animeav1.com` responde `Content-Type: text/html` **sin `charset`**, así que requests
aplicaba el defecto de la RFC 2616 (`ISO-8859-1`) y `response.text` salía con mojibake:

```
"…One Piece y el tÃ­tulo de Rey de los Piratas que lo acompaÃ±a."
```

**Arreglo**: todo el scraping pasa por `_fetch()` (📖 `animeav1.py:37-56`), que fija UTF-8 **solo si el
servidor no declara charset**, de modo que si algún día lo declara se respeta el suyo:

```python
response = thread_session().get(url, **kwargs)   # requests.get hasta el 2026-10-27 (B16)
if "charset" not in response.headers.get("Content-Type", "").lower():
    response.encoding = "utf-8"
```

**Invariante que queda**: debe haber **exactamente una** petición en el módulo, la de dentro de
`_fetch`. Añadir una petición directa —con `requests.get` o con `thread_session().get`—
reintroduce el bug solo en esa ruta.

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
> y corre **en el hilo de UI** (`anime_window.py:218`), así que un servidor de imágenes colgado
> congelaba la aplicación indefinidamente.

---

### 17. La purga de pósters borra lo que no está en la lista actual ✅

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

### 18. Trampas de empaquetado y de entorno

**a) ~~`MiBibliotecaAnime.spec` está desactualizado~~** — ✅ **`hiddenimports` resuelto (2026-08-07)** 📖:

| Problema | Estado |
|---|---|
| Faltaba `APIs.animeav1.animeav1` | ✅ añadido |
| Faltaba `APIs.common.animeProviderMgr` | ✅ añadido |
| Faltaba `APIs.common.models` | ✅ añadido |
| Faltaba `dataPersistence.userPersistence` | ✅ añadido |
| Faltaba `APIs.jkanime.jkanime` | ✅ añadido con el proveedor |
| Declaraba `gui.anime_windows` (el módulo real es `gui.anime_window`) | ✅ corregido |
| Declaraba `gui.sidebarButtons.sidebarButton` (**no existía** tal módulo) | ✅ **retirado en `ae126fd`** |

✅ **Los 18 nombres de `hiddenimports` corresponden hoy a módulos reales**, comprobado uno a uno contra
`src/` el 2026-08-07: ningún fantasma, y el único módulo de `src/` que no figura es `app.py`, que es el
*script de entrada* y no debe figurar.

**Síntoma que tenía**: `ModuleNotFoundError` al arrancar el `.exe`, no al compilar.

✅ **Verificado compilando el 2026-08-17.** Hasta esa fecha la lista solo se había corregido leyendo
los `import` reales. Ese día se compiló (`pyinstaller MiBibliotecaAnime.spec`) **y se arrancó el
`.exe` resultante**: build sin errores y aplicación operativa. El problema **grave** del `.spec` —que
`datas` empaquetaba `resources/DB`— también quedó cerrado ese día
([12 §4 → A3](12-deuda-tecnica-y-roadmap.md)).

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

**d) ~~`datas` del `.spec` incluye `resources/DB`~~** ✅ **Resuelto el 2026-08-17**: se
**empaquetaba la BD del desarrollador** dentro del ejecutable, junto con las 6 carpetas de pósters.
Medido antes de quitarlo sobre el build de v0.2.0: `DB_Animes.db` (77 KB), `DB_user.db`, la carpeta
`backups/` **y 85 pósters** viajaban en el `.exe`.

> **Por qué parecía obligatorio** — y es la parte que hay que recordar: **PyInstaller no puede
> empaquetar una carpeta vacía**; una entrada de `datas` que apunta a un directorio sin ficheros se
> ignora en silencio. La única forma de que esas rutas «aparecieran» en el build era enviarlas
> llenas, lo que da la impresión falsa de que el `.exe` las necesita.
>
> **No las necesita**: la app crea cada uno de esos directorios en tiempo de ejecución —
> `sqlite.py:233-235` (padre del `.db`), `utils.py:55-56`, `:91-92`, `:127-128` (pósters) — y
> `get_anime_image` **salta** las carpetas ausentes (`utils.py:190-191`) en vez de fallar.
> ✅ Comprobado arrancando el `.exe` ya sin ellas: `resources/DB/DB_Animes.db` aparece a los 3 s.
>
> `datas` conserva **solo** `resources/images/utils`, que sí son recursos de solo lectura.

**e) Los destinos de `datas` se resuelven dentro de `_internal/`, no junto al `.exe`** ✅
*(añadida el 2026-08-17)*

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

**f) `libmpv-2.dll` va en `binaries` con destino `vendor`, y `python-mpv` no la busca ahí** ✅
*(añadida el 2026-10-20, fases 0 y 5 del reproductor)*

**Por qué**: `python-mpv` localiza la DLL con `ctypes.util.find_library`, que en Windows **solo mira
`%PATH%`**, no la carpeta del script ni la del `.exe`. Sin ella en la ruta, `import mpv` lanza
`OSError: Cannot find mpv-1.dll, mpv-2.dll or libmpv-2.dll`. Por eso `load_mpv()`
(`video_player.py:68`) antepone `get_resource_path("vendor")` a `os.environ["PATH"]` —y la pasa a
`os.add_dll_directory()` para sus dependencias— **antes** del `import`.

Y en el `.exe` esa ruta es `_internal/vendor`, por la misma mecánica que la **18e**: el destino de
`binaries` cae dentro de `_internal/`. De ahí que el `.spec` diga `('vendor/libmpv-2.dll', 'vendor')`
y no `'.'`, como proponía el plan. Con `'.'` la DLL acabaría en `_internal/` a secas y `load_mpv()` no
la vería sin tocar `src/` (⚠️ esa variante no se compiló).

**Síntoma observable**: **ningún error**. El `.exe` arranca perfecto, la ficha monta el panel del
reproductor y **todos los servidores acaban en el navegador** con la tarjeta «No se ha podido cargar
aquí». `load_mpv()` no lanza —es la degradación diseñada— y su `print` no se ve, porque el `.exe` va
con `console=False` (**18c**). Parece que han caído todos los hosters a la vez.

**Además**: la DLL **no está en el repositorio** (120 MB, por encima del límite de GitHub; `vendor/`
está en `.gitignore`). Un clon limpio no puede compilar sin el paso 4 del `README.md`, y por eso el
`.spec` **para con `SystemExit`** si falta, en vez de compilar un `.exe` que lo abriría todo fuera.

**Cómo comprobarlo**: con el `.exe` reproduciendo, `Get-Process -Module` del proceso tiene que
listar `…\_internal\vendor\libmpv-2.dll`. ✅ Verificado el 2026-10-20 desde una carpeta fuera del
repo y **sin la DLL en `%PATH%`**.

---

### ~~19. `watchingAnimes/__init__.py` contiene un stub que suplanta la clase real~~ ✅ **Resuelto (2026-08-07, `e6d1a73`)**

Era la deuda B9. El fichero contenía:

```python
# src/gui/sidebarButtons/watchingAnimes/__init__.py
class WatchingAnimeButton:
    pass
```

`main_window.py:25` importa desde `…watchingAnimes.watchingAnimes` (el módulo), así que nunca llegó a
usarse. Pero `from gui.sidebarButtons.watchingAnimes import WatchingAnimeButton` habría importado el
stub **sin ningún error de importación**, con síntoma `TypeError` al construir, o un botón que no
aparece en la sidebar.

**Invariante vivo**: ✅ los **18** `__init__.py` de `src/` están hoy **todos vacíos** (0 bytes),
comprobado el 2026-08-07. Mantenlo así: un `__init__.py` con contenido puede ensombrecer al módulo
homónimo del paquete y el fallo no se manifiesta al importar, sino al usar.

---

### 20. `removeprefix()` devuelve `None` si los tipos no coinciden ✅ *(desaparecida, 2026-10-27)*

> ✅ **El helper ya no existe.** Era un *backport* para Python <3.9 y el proyecto exige 3.10, así que
> sus cuatro llamadas pasaron a `str.removeprefix`, que no tiene este defecto. Se conserva el texto
> porque otros documentos citan el número.

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

### Qué cambió el 2026-08-16 ⚠️ *(sigue viva, y ahora es provocable a voluntad)*

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

## Columna `provider_id` *(añadidas 2026-08-16)*

### 26. Buscar en la biblioteca preguntando al proveedor no encuentra lo que tienes guardado ✅

**El bug**: las cuatro vistas de estado buscaban así — pedir la búsqueda al proveedor seleccionado y
quedarse con los resultados cuyo `anime_id` estuviera en la BD. Cruzar **por slug**.

**Por qué falla**: el `anime_id` guardado es el slug **de quien guardó la fila**. One Piece estaba
guardado como `one-piece-tv` (AnimeFLV) y es `one-piece` en los otros dos, así que con AnimeAV1
seleccionado —el predeterminado— buscar «One Piece» en favoritos **no devolvía One Piece**. Y al
revés: con AnimeFLV seleccionado desaparecían de la búsqueda los animes que ese sitio no tiene.

**Síntoma**: un anime que estás viendo en la rejilla desaparece en cuanto escribes su nombre en el
buscador de esa misma pestaña. Sin error, y sin patrón aparente — depende del proveedor que tengas
puesto y de quién guardó cada fila.

**Regla**: **los datos son locales, la búsqueda también.** `filter_animes_by_title`
(`utilsButtons.py:23-56`) compara contra los títulos guardados, normalizados, sin red y sin mirar el
proveedor. La búsqueda web se **suma** encima (`SavedAnimeSearch`, `:97-166`) porque aporta algo que
un título guardado no puede saber —que «Solo Leveling» es «Ore dake Level Up na Ken»—, pero **nunca
quita** resultados.

**Invariante**: cualquier filtro sobre la biblioteca del usuario debe funcionar con el cable
desenchufado. Si depende del proveedor seleccionado, está mal.

---

### 27. `provider_id` dice **quién sirve el slug**, no de dónde salió el anime ⚠️

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

### 28. Reapuntar una fila a otro proveedor puede duplicarla en silencio ✅

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

---

## Rediseño de interfaz *(añadidas 2026-08-21, fases 1-9; la 36, el 2026-08-31; la 37, el 2026-09-01)*

Siete trampas de **CustomTkinter y de layout**. Ninguna da error: todas se manifiestan como algo que
sale mal colocado, invisible o parpadeando, y todas costaron al menos una tarde.

### 29. Un `CTkFrame` sin hijos conserva 200 × 200 como tamaño pedido 🔴 ✅

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

### 30. `wraplength` no limita a dos líneas, y un `CTkLabel` no se recorta a su `height` 🔴 ✅

`wraplength` envuelve **todas** las líneas que necesite el texto, y el `CTkLabel` **crece** por
encima de su `height` en vez de recortarse. Reservar alto no sirve de nada.

**Síntoma observable**: un título de anime de tres líneas desnivelaba la fila entera de la rejilla, y
las celdas de debajo bailaban.

**Invariante**: **todo título de ancho fijo pasa por `Theme.ellipsize(texto, fuente, ancho,
líneas)`**, que reproduce el reparto por palabras de Tk midiendo con `font.measure()` y corta la
última línea con puntos suspensivos. Aplica a `AnimeRow`, a las tres rejillas y a la ficha.

---

### 31. Los contadores de la barra salen de listas que solo se llenan al arrancar 🔴 ✅

`MainWindow.recent_animes`, `favourite_animes`, `watching_animes`, `pending_animes` y
`finished_animes` son **cachés en memoria** que se pueblan en `load_animes()`.
`refresh_sidebar_counts()` hace `len()` sobre ellas: **no consulta la BD**.

**Síntoma observable**: cambiar un estado movía la fila en la BD y en la vista, pero el número de la
barra lateral seguía diciendo lo de antes hasta el siguiente arranque.

**Invariante**: quien cambie un estado **relee las listas afectadas del hub y solo después** llama a
`refresh_sidebar_counts()`. Lo hacen «Empezar» (`pendingAnimes.py`) y la ficha (`anime_window.py`,
desde la fase 8).

---

### 32. La configuración de rejilla del `content_frame` sobrevive a `clear_frame()` 🔴 ✅

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

### 33. La pantalla de carga solo se retiraba si había estrenos 🔴 ✅ *(resuelta 2026-08-21)*

`download_images_and_show_animes()` llamaba a `loading_frame.place_forget()` **únicamente en la rama
de éxito**. Con la lista de estrenos vacía, la función avisaba, pintaba la portada por debajo y
volvía **sin retirar la pantalla de carga**.

**Síntoma observable**: un arranque sin conexión —o con los tres proveedores caídos— dejaba el GIF de
carga tapando la portada **para siempre**, y el estado vacío de «Nuevos lanzamientos» no llegaba a
verse nunca. Solo aparece si se prueba el arranque **sin red**, que es justo lo que nadie prueba.

**Y una segunda mitad**: `place_forget()` **no destruye**. El widget seguía vivo, así que
`update_gif()` se reprogramaba con `after(100, …)` durante toda la sesión, repintando un GIF de
400 × 400 cada décima de segundo por detrás de la aplicación.

**Invariante**: la pantalla de carga se **`destroy()`** —no se esconde— y se retira en **todas** las
salidas de la función. La animación comprueba `winfo_exists()` antes de repintarse; sin esa guarda,
destruir el marco produce `invalid command name`.

> ⚠️ **El comentario que anclaba esta trampa dentro de `update_gif()` ya no está en el código**
> (2026-08-31). El invariante sigue vigente y la guarda `winfo_exists()` sigue ahí, pero quien lea
> `show_loading_screen()` ya no encuentra escrito por qué. Ese mismo arranque tenía **otro** defecto
> visual, independiente de éste: la **trampa 36**, más abajo.

---

### 34. Un `<Leave>` no significa que el ratón se haya ido 🔴 ✅

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

🔴 **Léela junto a la trampa 37**:
esta trampa dice que sobran `<Leave>`, y la otra que **faltan**. Comprobar el puntero antes de apagar
—lo que arregla ésta— es justo lo que hace que un `<Leave>` que no llega deje la fila encendida para
siempre. Las dos se arreglan juntas o no se arregla ninguna.

---

### 35. `bind()` y `event_generate()` no hablan del mismo widget en CustomTkinter 🔴 ✅

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

### 36. Un widget sin `fg_color` no es del tema de la aplicación 🔴 ✅ *(resuelta 2026-08-31)*

**Por qué**: un **marco** sin `fg_color` **no nace transparente ni hereda del padre** — eso solo lo
hace `CTkLabel`. Toma el color de la paleta de la librería (`blue.json`), que no es la de `Theme`:

| Widget | `fg_color` por defecto (claro, oscuro) |
|---|---|
| `CTkFrame` | `gray86` / `gray17` → `#DBDBDB` / `#2B2B2B` |
| `CTk` (la raíz) | `gray92` / `gray14` → `#EBEBEB` / `#242424` |
| `CTkProgressBar` | canal `#939BA2` / `#4A4D50`, progreso `#3B8ED0` / `#1F6AA5` |
| `CTkLabel` | `transparent` — **este sí** hereda |

Un widget al que se le olvide el `fg_color` **no falla ni avisa**: sale de otro color y ya.

Le pasaba a la pantalla de carga: `loading_frame` era un `CTkFrame(self, corner_radius=0)` a secas,
del tamaño justo de su contenido. El arranque enseñaba **tres fondos a la vez**, medidos sobre la
captura:

| Zona | Color | De dónde salía |
|---|---|---|
| El bloque de carga | `#2B2B2B` | gris por defecto de `CTkFrame` |
| Franja izquierda de 224 px | `#242424` | gris por defecto de la raíz `CTk` |
| El resto de la ventana | `#14161A` | `Theme.BG`, el bueno |

**Síntoma observable**: al arrancar, el título «Cargando biblioteca de anime», el GIF y la barra
salen dentro de un **rectángulo gris recortado** sobre el fondo de la aplicación, con una **banda
vertical** de un tercer gris a la izquierda. Ningún error por consola. Se ve en los dos temas.

**Y dos medias trampas más, las dos silenciosas:**

- **El GIF no tiene fondo propio.** `loading-image.gif` es paleta con `transparency = 1`: Tk compone
  su alfa contra el fondo del `CTkLabel` que lo sostiene. Cambiarle el color al marco **le cambia el
  fondo al GIF**; buscar el problema dentro del `.gif` es perder la tarde.
- **El `minsize` de una columna sobrevive a `grid_forget()`.** `Sidebar` reserva la columna 0 con
  `grid_columnconfigure(0, weight=0, minsize=width)` (`sidebar.py:418`). `show_loading_screen()`
  retira la barra con `grid_forget()`, pero la columna **sigue midiendo 224 px**, y en esa franja se
  ve el fondo de la raíz de Tk. Retirar un widget no libera el hueco que su columna tiene reservado.

**Invariante**: **todo marco de fondo lleva su `fg_color` explícito**, salido de `Theme`, y eso
incluye la **raíz de Tk** (`self.configure(fg_color=Theme.BG)` en `__config_main_window()`,
`main_window.py:104`). Lo mismo para el canal de un `CTkProgressBar` (`fg_color` + `progress_color`)
y para el `text_color` de una etiqueta. La comprobación de `git grep -nE "#[0-9A-Fa-f]{6}" -- src/`
**no detecta esto**: el defecto no es un literal de color, es la **ausencia** de uno.

**Cómo comprobarlo**: capturar la ventana durante el arranque y muestrear píxeles, no mirarla a ojo
—dos grises oscuros parecidos se distinguen mal—. Con la app en marcha, todos los puntos de fondo
deben dar `#14161A` en oscuro y `#F4F5F7` en claro ([09 §7.1](09-verificacion-y-pruebas.md)).

**De paso**: el bloque se centraba con `x = winfo_width() * 2.5`, y `winfo_width()` vale **1** antes
de que la ventana esté dibujada. Acertaba por casualidad. Hoy se centra con
`place(relx=0.5, rely=0.5, anchor=CENTER)` dentro de un marco transparente.

---

### 37. Un hijo sin `bind` es un agujero por el que el hover se queda encendido 🔴 ✅ *(resuelta 2026-09-01)*

Es **la complementaria de la trampa 34**: aquella dice que un `<Leave>` de más no significa que el
ratón se haya ido; ésta, que **hay salidas de las que no llega ningún `<Leave>`**.

**Por qué**, en tres pasos que hay que encadenar para verlo:

1. `CTkFrame.bind()` **no ata al marco**: ata a su `_canvas` interno
   (trampa 35).
2. Ese canvas es **hermano** de los demás hijos del marco, **no su ancestro**.
3. Tk manda los *leaves* virtuales solo a los **ancestros** del widget que se abandona. Así que si el
   puntero sale de la fila **desde un hijo que no tiene `bind`**, el canvas —que ya recibió su
   `<Leave>` al entrar el puntero en ese hijo, y lo ignoró por la trampa 34— **no recibe ninguno
   más**. Nadie apaga la fila.

Le pasaba a `EpisodeRow` (`anime_window.py:469-629`), que ataba el hover a la fila y a sus dos
etiquetas y dejaba fuera **el interruptor «Visto» y el separador de 1 px**. El separador va con
`place(rely=1.0, relwidth=1.0)`: ocupa **toda la última fila de píxeles** de cada episodio, así que
bajar de un episodio al siguiente **obliga a cruzarlo**.

**Síntoma observable**: pasar el ratón por **un solo** episodio y salir funciona. **Recorrer la
lista** deja encendidos todos los episodios por los que has pasado, y siguen encendidos con el ratón
fuera de la ventana; volver a entrar y salir de uno lo apaga solo a él. Ningún error por consola.

⚠️ **Y no se reproduce moviendo el ratón deprisa**: un salto de 2 px se salta el separador y todo
parece correcto. Hace falta el paso de **1 px** —un ratón lento de verdad— para cruzarlo.

> 🆕 **2026-10-28 (fase 3 de la 0.5.0): el separador ya no existe.** No se había pintado nunca —un
> `CTkFrame` de 1 px no pinta ([trampa 71](#71-un-ctkframe-de-height1-no-pinta-nada--))— y costaba
> ~2 ms por fila al abrir la ficha. Quedan **cuatro** hijos atados: la fila, sus dos etiquetas y el
> interruptor. La lección sigue valiendo para cualquier hijo que se le añada.

**Invariante**: el **hover se ata a todos los hijos** del widget que se resalta; el **clic**, solo a
los que deban responder a él. En `EpisodeRow` son dos bucles distintos y a propósito
(`EpisodeRow.__bind_interactions()`): el interruptor recibe `<Enter>` / `<Leave>` pero **no** `<Button-1>`,
porque tiene su propio comando y marcar un episodio no debe abrir sus servidores.

**Y un cinturón además de los tirantes**: `EpisodeRow.__hovered` (`anime_window.py:477`) es un
atributo **de clase** con la fila resaltada; la que se enciende apaga a la anterior
(`__handle_enter` → `__release_hover`). Aunque en el futuro se pierda un `<Leave>`, **no puede haber
dos filas encendidas a la vez**.

**Por qué `AnimeRow` no lo sufre**: su separador está **fuera** del cuerpo que se resalta
(`anime_row.py:143-144` lo mete en la fila, no en `__body`), y `__bind_interactions()` ata el hover a
**todos** los descendientes de `__body` — píldora de acción incluida, con su canvas y su etiqueta
dentro. No es suerte: es la estructura. `EpisodeRow` metió el separador **dentro** con `place()` para
no gastar una fila de rejilla, y ahí nació el agujero.

⚠️ **Que el hover llegue a todos no significa que el clic también**, y desde el 2026-09-01 son dos
listas distintas: el clic **salta la píldora entera** ([trampa 40](#40-un-bind-sin-add-borra-el-manejador-que-el-widget-ya-tenía---resuelta-2026-09-01)).
Quitarle también el hover reabriría este agujero por la píldora.

**Cómo comprobarlo**: no a ojo y no con la mano. Se monta una pila de `EpisodeRow` reales en una
ventana suelta y se recorre con `SetCursorPos` **de píxel en píxel**, contando cuántas filas tienen
`fg_color != Theme.TRANSPARENT` en cada paso ([09 §6b](09-verificacion-y-pruebas.md)). Debe ser
**siempre 1**, y **0** al salir de la pila. Antes del arreglo daba **5 de 5**, y la primera se quedaba
pegada exactamente en el píxel del separador.

**Hermana, del mismo arreglo**: al **plegar** los servidores, `set_expanded(False)` devolvía la fila
a `TRANSPARENT` aunque el puntero siguiera encima — el resaltado se apagaba justo debajo del ratón.
Ahora consulta `__pointer_inside()` (`anime_window.py:620`).

---

## Frescura de los datos guardados *(añadida 2026-09-01)*

### 38. Una fila guardada no refresca sus episodios sola 🔴 ✅ *(resuelta en la portada el 2026-09-01; en «Viendo» y «Pendientes», el 2026-10-27)*

`ANIMES.episodes` es una **foto del día en que abriste la ficha de ese anime**, no «los episodios que
hay». Durante mucho tiempo el **único** sitio que la reescribía fue `__load_anime_status()`
(`anime_window.py:647-648`), y solo al abrir la ficha.

**Síntoma observable**: un anime **en emisión** miente cuando sale un capítulo nuevo. El caso real que
la destapó: «One Piece» y «Mushoku Tensei III» estrenan los domingos; abriendo la aplicación ese mismo
domingo, la banda «Retomar donde lo dejaste» decía **«Lo has visto entero»** con el capítulo nuevo ya
publicado. Entrabas en el anime —lo que reescribía la fila— y al volver a la portada ya salía bien.
Ningún error por consola: el dato es coherente, solo viejo.

✅ **Reproducida sobre copia** el 2026-09-01: fila con 9 episodios y los 9 vistos, proveedor sirviendo
10 → tarjeta «Lo has visto entero · 9 episodios», barra al 100 %.

**Resuelta en dos pasos.** `704e894` arregló solo **las ≤3 filas de la banda** de la portada. El
2026-10-27, `EpisodeRefresher` (`gui/episode_refresher.py`, [03 §11](03-flujos-de-ejecucion.md))
sustituyó ese arreglo y lo extendió a «Viendo» y «Pendientes»: barras, `SidePanel`, el subtítulo «M
episodios pendientes», la duración «N episodios» y la píldora «Episodio N →», que **aparece** en una
fila que estaba vista entera cuando sale un capítulo. ✅ Comprobado sobre copia con cinco filas
rebajadas a mano: las cinco se corrigen en pantalla sin reconstruir la vista, y en la BD cambia **solo**
`episodes`. Y ✅ en tu biblioteca real había un caso vivo al cerrarla: «Dragon Ball Super: Beerus»
guardaba 2 episodios y AnimeAV1 sirve 3.

| Dónde | Sigue mintiendo |
|---|---|
| Sello «vistos / totales» de «Finalizados» | **sí, a propósito**: lo terminado casi nunca crece, y serían 24 peticiones más por arranque |
| Filas de un proveedor caído (hoy, las dos de AnimeFLV) | **sí**: con `strict=True` no hay a quién más preguntar. La salida es «Actualizar a X» desde la ficha |
| Filas sin `provider_id` | **sí**: no se sabe a quién preguntar sin arriesgar la trampa 27 |

**Invariante**: `AnimeRecord.episodes` responde «cuántos episodios servía el proveedor **la última vez
que miré**». Cualquier vista que presente un total, un porcentaje o un «lo has visto entero» está
afirmando algo que puede llevar días caducado.

🔴 **Y ampliarlo no es gratis.** Refrescar más filas significa **escribir en la biblioteca del usuario
sin que lo haya pedido**, y ahí entra la **trampa 27** (más arriba, en «Columna `provider_id`»):
el mismo *slug* puede existir en otro sitio con otra cuenta de episodios, así que la petición tiene
que ir con **`strict=True`** —al proveedor de la fila y a ninguno más— y **no escribir nunca** si la
respuesta viene vacía. Es justo al revés que `open_saved_anime()`, que sí quiere *fallback* porque
solo lee. `EpisodeRefresher` las lleva las dos, más una tercera: **relee la fila antes de escribir** y
no toca nada si entretanto cambió de proveedor. Quien quiera refrescar otra vista (p. ej.
«Finalizados») tiene que pedírselo al servicio con `refresh()`, **no** copiar su patrón.

---

## Medir un widget de CustomTkinter *(añadida 2026-09-01)*

### 39. Un `CTkButton` no respeta el `width` que se le pide 🔴 ✅ *(resuelta 2026-09-01)*

Pasarle `width=` a un `CTkButton` fija el ancho **del marco**, no el del widget. Por dentro es un
`tkinter.Frame` con una rejilla de 5×5 (`ctk_button.py::_create_grid`) y **propagación de tamaño
activada**: si esa rejilla necesita más, el ancho *pedido* del botón pasa a ser el suyo. Y cuando el
botón se coloca con `place(x=…)` sin ancho explícito, Tk lo pinta a su ancho **pedido**.

No hay forma de forzarlo desde fuera: `CTkBaseClass.place()` **lanza `ValueError`** si le pasas
`width` o `height` («must be passed to the constructor»), así que la única salida es **contar bien**.

Lo que la rejilla reserva y no aparece en ningún sitio:

| Concepto | px | De dónde sale |
|---|---|---|
| Columnas 0 y 4 | `max(corner_radius, border_width + 1, border_spacing)` por lado | `_create_grid()`. En una **píldora manda el radio**: 14 px con `CHIP_H = 29` |
| Etiqueta del texto | 1 por lado | la crea con `padx=0, pady=0, **borderwidth=1**` |
| Hueco texto ↔ icono | `CTkButton._image_label_spacing` = **6** | `minsize` de la columna 2, solo si hay texto **e** imagen |
| Etiqueta del icono | 2 por lado | se crea sin argumentos → `borderwidth` 2 por defecto de Tk. Su `padx` **no** cuenta: Tk solo se lo suma al texto |

**Síntoma observable**: en «Buscar», **al seleccionar un género la ficha se metía encima de la de al
lado y le tapaba la ✕**. Ningún error. Lo delataba la selección porque es la que más sobra: la
seleccionada estrena icono, y de paso va en negrita.

✅ **Medido** el 2026-09-01, con la raíz de Tk oculta, comparando `cget("width")` con
`winfo_reqwidth()` de cada ficha ya colocada:

```
texto              contado  pintado  delta
Acción (activa)         73       89    +16   ← se come los 8 px de CHIP_GAP y solapa 8
Más géneros (33)       125      141    +16   ← también lleva glifo
Comedia                 69       75     +6   ← quedaba 2 px de hueco: no se ve
```

Una ficha sin icono sobraba 6 px y aún dejaba hueco; **al seleccionarla el sobrante saltaba a 16 y se
comía la separación entera**. Como las seleccionadas se pintan **las primeras** y `place()` apila
encima lo que se coloca después, quien tapaba la ✕ era la ficha siguiente.

**Invariante**: quien coloque `CTkButton` con `place()` y lleve él mismo la cuenta del ancho tiene que
sumar la rejilla interna, no solo `font.measure(texto)` y su propio relleno. Y el relleno efectivo es
`max(el del diseño, corner_radius)`: pedir menos no encoge nada.

**Resuelta** en `GenreChips.__chip_width()` (`genre_chips.py:278-301`, con las tres constantes en
`:57-69`), que suma las cuatro filas de la tabla y pregunta al `CTkImage` por su `size` en vez de
recalcularlo. ✅ Verificado: 4 estados de
selección y los 41 chips desplegados en 4 anchos → **0 descuadres, 0 solapes, hueco exactamente
`CHIP_GAP`**, y el alto pedido por el marco coincide al píxel con el real. ✅ Confirmado también
**mirando la aplicación** por el usuario.

⚠️ **Los números salen de customtkinter 5.2.2.** Si algún día sube la versión, lo primero que hay que
volver a medir es esto: el síntoma no da error y no lo detecta ningún `grep`.

**Primas hermanas**: la **29** (un `CTkFrame` no mide cero) y la **30** (un `CTkLabel` no se recorta a
su `height`). Las tres son la misma idea — **en CustomTkinter, `width` y `height` son una petición, no
un contrato**.

⚠️ **La ficha de detalle se libra por otro camino**: `__place_genre_tags()` (`anime_window.py:828-893`)
también envuelve fichas con `place()`, pero las suyas son `CTkFrame` con la etiqueta **dentro**, y un
hijo colocado con `place()` **no** propaga tamaño al padre. Por eso ahí el `width=` sí se respeta.

---

## Atar eventos encima de CustomTkinter *(añadida 2026-09-01)*

### 40. Un `bind()` sin `add="+"` borra el manejador que el widget ya tenía 🔴 ✅ *(resuelta 2026-09-01)*

Es la **tercera** de la familia de la [trampa 35](#35-bind-y-event_generate-no-hablan-del-mismo-widget-en-customtkinter--)
y la [trampa 37](#37-un-hijo-sin-bind-es-un-agujero-por-el-que-el-hover-se-queda-encendido---resuelta-2026-09-01):
todas salen de que **un widget de CustomTkinter es un marco de Tk con hijos dentro**, y de que el
código de la aplicación trata ese marco como si fuera un widget atómico.

**Por qué**, dos hechos que por separado son inofensivos y juntos borran una funcionalidad entera:

1. **`bind(seq, func)` sin `add="+"` sustituye**, no suma. Es Tk, no CustomTkinter, y está
   documentado — pero no se piensa en ello cuando se ata un manejador propio a un widget ajeno.
2. **Excluir un widget de un recorrido no excluye su interior.** Un `CTkButton` es un marco con un
   `CTkCanvas` y un `Label` dentro, y CustomTkinter monta **ahí** sus manejadores: `_clicked` en
   `<Button-1>` y su hover en `<Enter>` / `<Leave>`. Esos dos hijos **no son** el botón, así que un
   `if widget is boton: continue` los deja pasar — y son justo donde cae el ratón, porque tapan el
   marco entero.

Le pasaba a `AnimeRow.__bind_interactions()` (`anime_row.py:278-312`), que recorre los descendientes
de `__body` para atarles el clic de la fila —los eventos de Tk no burbujean— y saltaba **solo**
`self.__action_button`. Resultado: la fila **pisaba el `_clicked` de su propia píldora**.

Se ve en una línea, comparando la atadura antes y después de que la fila haga su `bind()`:

```
CTkButton recién creado:   canvas -> ..._clicked...    label -> ..._clicked...
tras un bind() de la fila: canvas -> ...<lambda>...    label -> ...<lambda>...
con add="+":               canvas -> ..._clicked... y luego ...<lambda>...
```

**Síntoma observable**: la píldora se pinta, se resalta al pasar por encima y **responde al clic**…
pero ejecutando el `on_click` de la fila en vez de su propio `command`. Como los dos abrían la ficha
del mismo anime, durante diez días **pareció que funcionaba**. Lo que no funcionaba, y nadie
relacionó, es que **«Empezar» no movía el anime a «Viendo»**: esa parte vive en la acción, que no se
ejecutaba nunca. Ningún error por consola, y el anime abría su ficha con normalidad.

Salió a la luz el 2026-09-01, al hacer que la acción y el clic dejaran de hacer lo mismo
([03 §12](03-flujos-de-ejecucion.md)): la píldora prometía llevar a un episodio y llevaba al anime.

**Invariante**, dos mitades:

- **Para excluir un widget de un recorrido recursivo, hay que excluir su subárbol**, no el widget.
  `self.__descendants(self.__action_button)` y `not in`, no `is not`.
- **Todo lo que se ate encima de un widget de CustomTkinter va con `add="+"`.** No hay forma de saber
  desde fuera si la librería ya puso algo suyo ahí, y perderlo no da error: da un widget que parece
  entero y no lo está.

⚠️ **El hover sigue atándose a la píldora entera, y tiene que seguir así**: si un hijo suyo se queda
sin `<Leave>`, salir de la fila por ahí deja el resaltado encendido para siempre — la
[trampa 37](#37-un-hijo-sin-bind-es-un-agujero-por-el-que-el-hover-se-queda-encendido---resuelta-2026-09-01)
otra vez. Por eso el arreglo **no** es quitarle las ataduras a la píldora: es `add="+"` en el hover y
el subárbol fuera del clic.

**De paso se recuperó su hover propio**: `AnimeRow` también estaba pisando el `<Enter>` / `<Leave>`
que CustomTkinter monta en el canvas y la etiqueta, así que la píldora nunca se pintó con su
`hover_color`. Nadie lo había notado porque la fila entera se resalta al mismo tiempo.

**Los otros cinco sitios que atan clics están bien**, y por la misma razón: `poster_grid.py:394`,
`resume_card.py:138`, `sidebar.py:145`, `side_panel.py:174` y `EpisodeRow`
(`anime_window.py:446-454`) atan a **listas explícitas** de marcos y etiquetas y no entran en ningún
botón. `AnimeRow` era el único que recorría en profundidad. Y `SidePanel` deja el botón fuera **a
mano** y con un comentario que lo dice — por eso «Seguir por el N» fue el único de los tres que
funcionó a la primera.

**Cómo comprobarlo**: [09 §6e](09-verificacion-y-pruebas.md#6e-pulsar-de-verdad-un-botón-que-vive-dentro-de-otro-widget-2026-09-01). No basta con leer el código; se pulsa
el interior de la píldora y se cuenta **cuál de los dos manejadores ha corrido**.

---

## Medir el sitio que tienes *(añadida 2026-09-02)*

Las dos de este apartado son el mismo error visto desde dos capas: **un widget que parece que se
adapta al espacio disponible y en realidad nunca llega a mirarlo.** Ninguna da error, ninguna se ve
a 1440 —el tamaño con el que se diseñó y con el que se prueba— y las dos aparecen en cuanto alguien
maximiza la ventana.

### 41. Una rejilla con `sticky="w"` mide su propio contenido, no el hueco que tiene 🔴 ✅ *(resuelta 2026-09-02)*

**Por qué**: `sticky` no decide solo dónde se pega un widget, decide **cuánto mide**. Con
`sticky="ew"` la celda de la rejilla lo estira hasta el ancho que le toca; sin la `e` y la `w`, el
widget se queda con su **tamaño pedido**, que es el de lo que él mismo ha pintado. `winfo_width()`
devuelve entonces el ancho del contenido, no el del contenedor.

Es inofensivo mientras nadie lo consulte. Deja de serlo en cuanto **el propio widget calcula algo a
partir de ese número**: `columnas = ancho // (póster + hueco)` sobre un ancho que sale de haber
pintado esas mismas columnas es un **punto fijo**. La cuenta se hace, sale bien, y siempre devuelve
lo que ya había.

```
sticky="w"   ancho = 6 * 196 = 1176  ->  1176 // 196 = 6  ->  pinta 6  ->  ancho = 1176  ...
sticky="ew"  ancho = 1662 (el de la ventana)  ->  1662 // 196 = 8  ->  pinta 8
```

**Síntoma observable**: al maximizar, las cuatro vistas de rejilla —Nuevos lanzamientos, Favoritos,
Finalizados y Buscar— seguían pintando 6 y 5 columnas pegadas a la izquierda, con **casi 500 px de
fondo vacío a la derecha**. Las de cascada (Viendo, Pendientes) sí se ensanchaban, porque sus filas
ya iban con `sticky="ew"` — y esa diferencia entre vistas es justo lo que hacía que pareciera un
descuido de una vista concreta y no una regla que faltaba.

Estuvo así desde el rediseño (2026-08-21) hasta el 2026-09-02. No dio ni un error: una franja de
fondo del color correcto es indistinguible de una decisión de diseño.

**Invariante**, en dos mitades y las dos obligatorias:

- **Quien mida su contenedor tiene que estar estirado hasta él.** `sticky="ew"` en el widget **y**
  `weight` en la columna del padre. Si falta cualquiera de las dos, la medida es del contenido.
- **Lo que sobra del reparto entero hay que repartirlo**, o vuelve la franja vacía —más pequeña, pero
  vuelve—. `weight=1` + un mismo `uniform` en las columnas en uso y la celda con `sticky="n"`: la
  celda queda centrada en su columna y el sobrante sale como huecos iguales. Es el equivalente en Tk
  de `repeat(auto-fill, minmax(póster, 1fr))`.
  ⚠️ Y hay que **quitar** el peso al encoger: [trampa 32](#32-la-configuración-de-rejilla-del-content_frame-sobrevive-a-clear_frame--).

⚠️ **La fórmula descuenta el margen izquierdo y no el derecho**, y no es un descuido: a 1440 el
diseño deja el último póster a ~11 px del borde, no a 28. Reservar los 28 por simetría daría **5**
columnas a 1440 y sería una regresión respecto al propio diseño. El margen derecho lo acaba poniendo
el reparto del sobrante.

⚠️ **Repintar es caro**: cada celda abre su JPG y lo reescala con PIL, y son ~350 ms para 16 celdas
**en el hilo de la interfaz**. Por eso `__on_configure()` descarta todo `<Configure>` que no cambie
el número de columnas —el reparto del sobrante lo hace Tk gratis— y los que quedan pasan por una
espera de `RELAYOUT_DELAY_MS`, que junta un arrastre entero en un solo repintado.

**Cómo comprobarlo**: [09 §6f](09-verificacion-y-pruebas.md#6f-comprobar-que-una-rejilla-se-adapta-al-ancho-2026-09-02). Leer el código no vale: hay
que **medir** `winfo_width()` de la rejilla a dos tamaños de ventana y ver que el número cambia.

---

### 42. `wraplength` no puede deshacer un `\n` que traiga el texto 🔴 ✅ *(resuelta 2026-09-02)*

**Por qué**: `wraplength` dice **dónde se puede** partir una línea, no dónde hay que juntarlas. Un
`\n` dentro del texto es un corte **incondicional**: Tk lo respeta con cualquier `wraplength` y con
cualquier ancho de ventana. No hay opción de `CTkLabel` que lo desactive.

Y la sinopsis llega con saltos propios del sitio: AnimeAV1 los trae escapados dentro de su payload de
hidratación y `animeav1.py:206` los convierte en saltos de verdad (`.replace('\\n', '\n')`), que es
lo correcto — el modelo guarda el texto que escribió su autor.

**Síntoma observable**: la sinopsis de la ficha conservaba los renglones del proveedor **por ancha
que fuera la ventana**, mientras el título y las fichas de género de al lado sí se reajustaban. ✅ En
la biblioteca real son **13 de 35** sinopsis: 18 saltos dobles y 2 sueltos.

Lo confuso es que `__relayout_text()` **sí** recalculaba el `wraplength` en cada `<Configure>`, así
que el código parecía correcto y el fallo parecía de layout. No lo era: era del texto.

**Invariante**: **todo texto que venga de la red y se pinte con `wraplength` pasa por una
normalización antes de llegar al widget.** Hoy lo hace `wrap_synopsis()` (`anime_window.py`).

⚠️ **Normalizar no es aplastar.** La regla es la del HTML y se eligió mirando los datos: un salto
suelto es un corte de renglón y se vuelve espacio; **dos son un párrafo y se conservan**, porque los
puso quien redactó el texto. Colapsarlo todo a un bloque también quita el síntoma, y de paso quita
información.

⚠️ **Se hace al pintar, no al raspar.** `AnimeInfo.synopsis` sigue siendo el texto íntegro del
proveedor —cómo se reparte en renglones es cosa de la GUI—, y así salen bien también las filas que ya
estaban guardadas, sin migrar la BD.

**Cómo comprobarlo**: [09 §6g](09-verificacion-y-pruebas.md#6g-comprobar-la-normalización-de-la-sinopsis-2026-09-02). Se compara `texto.split()`
antes y después: la normalización no puede perder ni inventar una sola palabra.

---

## Reproductor in-app *(añadidas 2026-10-20, fases 0-5 del plan del reproductor)*

Lo que tienen en común casi todas: **fallan cayendo al navegador**, que es la degradación
diseñada (`plan-reproductor/README.md`, regla 2). Así que el
síntoma típico **no** es un error, sino «este servidor se abre fuera cuando debería verse aquí», y
eso se confunde fácilmente con que el hoster haya cambiado. Antes de tocar un resolutor, descarta
las de este apartado.

La capa y el reproductor se describen en [06 §12](06-gui-y-vistas.md) y
[05 §9](05-proveedores-y-scraping.md); el flujo entero, en [03 §13](03-flujos-de-ejecucion.md).

### 43. Los segmentos de zilla dan 403 sin `Sec-Fetch-Site: same-origin` 🔴 ✅

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
**despacio**, cae a los **30 s**, por el tope propio del reproductor: [trampa 54](#54-un-hoster-lento-deja-cargando-sin-tope---resuelta-2026-10-21).

**Invariante**: las cabeceras viajan en `MediaSource.headers` y `VideoPlayer.play()`
(`video_player.py:680`) las pasa a mpv como `http_header_fields` —todas salvo `User-Agent`, que va a
su propiedad—. El cliente `curl` de mpv las aplica a **cada** petición, playlist y segmentos. Nunca
se ponen solo en la petición del playlist.

**Cómo comprobarlo**: un segmento con y sin la cabecera ([09 §6h](09-verificacion-y-pruebas.md)).
✅ 2026-09-23 contra un servidor local con la misma regla (los segmentos llegan con la cabecera) y ✅
2026-10-20 contra zilla real: **200 con ella, 403 sin ella**, y `dandadan` ep. 1 visto en la app.

---

### 44. Cada hoster quiere sus cabeceras, y lo que uno exige otro lo rechaza 🔴 ✅

**Por qué**: no hay una política de cabeceras común que valga para todos:

| Medio | Cabeceras que funcionan | Lo que lo rompe |
|---|---|---|
| zilla (HLS de AnimeAV1) | `Sec-Fetch-Site: same-origin` | quitarla → 403 en los segmentos ([43](#43-los-segmentos-de-zilla-dan-403-sin-sec-fetch-site-same-origin--)) |
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

### 45. Una URL de medio no se guarda: caduca o va atada a tu IP 🔴 ✅

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

### 46. Los eventos de mpv llegan en su hilo, y desde ahí ni `after()` es seguro 🔴

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

### 47. El final de un vídeo no es un evento: `end-file` llega también al parar, y con `keep-open` no llega al terminar 🔴 ✅

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

### 48. Un fin de fichero a mitad de episodio es un corte, no el final 🔴 📖

**Por qué**: un servidor que corta el stream a mitad deja a mpv en fin de fichero, **igual que el
final de verdad**. Y desde la fase 4 el final **escribe en la biblioteca**: marca el episodio como
visto, con la semántica acumulativa ([trampa 9](#9-el-marcado-de-episodios-es-acumulativo-el-desmarcado-unitario-)).

**Síntoma** (si se quita la guarda): un episodio que se corta en el minuto 8 queda marcado como visto,
**y con él todos los anteriores**.

**Invariante**: `__reach_end()` (`video_player.py:860`) compara posición y duración. Si faltan más
de `END_TOLERANCE_S` = 15 s, lo trata como error (`on_error` → navegador) y **no marca nada**.
📖 Rama leída, **no ejecutada**: en las pruebas ningún servidor cortó.

---

### 49. Un widget dentro del frame del vídeo no se ve; uno hermano encima, sí 🔴 ✅

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
([52](#52-la-barra-flotante-y-el-deslizador-de-volumen-son-ventanas-aparte-siempre-encima--)).

---

### 50. El ratón y el teclado sobre el vídeo llegan a Tk, no a mpv 🔴 ✅

**Por qué**: al revés de lo que esperaba el plan. Con `input-vo-keyboard` encendido **o** apagado,
39-40 de 40 `<Motion>` sobre el vídeo llegan al frame de Tk; `Esc` y `q` los recibe `bind_all`; los
*bindings* de mpv y su propiedad `mouse-pos` **no reciben nada** (✅ fase 0). Además, libmpv trae
**apagados** `input-default-bindings`, `input-vo-keyboard` y `osc`: no hay atajos propios, ni `Esc`,
ni la `q` que cierra, ni barra en pantalla.

**Consecuencias**:

- «Mover el ratón muestra la barra» y el `Esc` de salir se atan **en Tk**, como en cualquier otro
  widget. No hace falta pasar nada desde el hilo de mpv.
- **`cursor-autohide` no sirve**, porque mpv no ve el ratón. El cursor lo oculta Tk con `cursor="none"`
  sobre `__stage`, `__surface` y `__card_frame` (`__set_cursor_hidden`, `video_player.py:1222`).
- `<Motion>` se ata **dos veces** por widget, con `tkinter.Frame.bind` y con el `bind` de CTk
  (`video_player.py:673-675`), porque `CTkFrame.bind()` solo ata el lienzo interno
  ([trampa 35](#35-bind-y-event_generate-no-hablan-del-mismo-widget-en-customtkinter--)). ⚠️ No se
  probó a quitar una de las dos.

**Síntoma**: un atajo definido en mpv no hace nada; con `cursor-autohide` el cursor no se oculta
nunca.

---

### 51. `-fullscreen` lleva la ventana al monitor principal 🔴 ✅

**Por qué**: `attributes("-fullscreen", True)` movió la ventana del monitor secundario (`2028, 91`)
al principal (`0, 0, 1920, 1080`), y al salir la devolvió a su sitio (✅ fase 0). También acabaron en
el principal `-fullscreen` seguido de `geometry` y `geometry` seguido de `-fullscreen`. Quitar el
marco con `SetWindowLong` colocaba bien, pero descolocaba la ventana al salir.

**Síntoma observable**: con dos monitores, «pantalla completa» sale en el que no estás mirando.

**Invariante**: `MainWindow.enter_player_fullscreen()` (`main_window.py:214`) **no** usa
`-fullscreen`:

1. Lee el rectángulo del monitor de la ventana con `MonitorFromWindow(…, MONITOR_DEFAULTTONEAREST)` y
   `GetMonitorInfoW`.
2. Pone `overrideredirect(True)` y la geometría con **`tkinter.Tk.wm_geometry`**, no con la de CTk,
   que aplica el escalado de DPI a un rectángulo que ya viene en píxeles físicos.
3. Guarda la geometría, el maximizado y el `minsize` de la columna de la barra lateral, y pone ese
   `minsize` a 0. Sin eso quedaría una franja a la izquierda del vídeo, porque ese `minsize`
   **sobrevive a quitar la barra** ([trampa 36](#36-un-widget-sin-fg_color-no-es-del-tema-de-la-aplicación---resuelta-2026-08-31)).
   `exit_player_fullscreen()` lo restaura todo.

⚠️ En la aplicación solo se probó en el monitor **principal**. La receta se probó en el secundario
con la ventana de la fase 0.

---

### 52. La barra flotante y el deslizador de volumen son ventanas aparte, siempre encima 🔴 ✅

**Por qué**: a pantalla completa no hay rejilla donde poner la barra sin encoger el vídeo. Por decisión
del usuario es un `Toplevel` sin marco y con `-topmost`, igual que el deslizador de volumen
(`_VolumePopup`). Ser ventanas aparte trae tres problemas, los tres vistos:

| Problema | Síntoma | Remedio |
|---|---|---|
| **`-topmost` sobrevive a `Alt+Tab`** | la barra se queda flotando **encima de la otra aplicación** (✅ visto encima de la terminal) | `__check_foreground()` (`video_player.py:1210`) mira `GetForegroundWindow()` cada `FOREGROUND_CHECK_MS` = 150 ms y la retira si el primer plano no es de este proceso. `__on_motion` tampoco la saca en ese caso |
| **Mostrarla con `update_idletasks()`** | **el primer clic sobre la barra se pierde**: no está mapeada del todo | `update()` al crearla y al volver a enseñarla |
| **Salir del icono hacia el deslizador dispara `<Leave>`** | el deslizador **se cierra** al ir a por él | margen de `VOLUME_GRACE_MS` = 300 ms (`schedule_volume_check`, `video_player.py:554`), y solo se cierra si el puntero no está ni en el icono ni en el deslizador |

**Invariante**: cualquier ventana flotante nueva tiene que pasar por las tres guardas: retirarse
cuando el primer plano no es nuestro, mostrarse con `update()` y tener margen de gracia para llegar a
ella.

---

### 53. Dos servidores con el mismo nombre se pisan en un dict ✅ *(resuelta 2026-09-24, «B1» del plan del reproductor)*

**Por qué**: un mismo episodio de JKAnime puede ofrecer varios «Desu» con URLs distintas (cambian
`t=` y `op=`). Un `{s.server: s.url for s in servers}` se queda solo con el último.

**Síntoma**: sale un único «Desu» y el otro es inaccesible, o pulsar «Desu» abre la URL de otro.

**Invariante**: todo mapa etiqueta → URL pasa por `AnimeWindowViewer.__server_url_map()`
(`anime_window.py:1894`), que numera los repetidos («Desu», «Desu 2»). La columna del reproductor y
la navegación entre episodios —que prefiere **el mismo nombre** de servidor— usan esas etiquetas.
Si vuelve a aparecer un `{s.server: …}` en `src/`, es este bug. ✅ Visto con One Piece ep. 1 de
JKAnime: 5 botones, y cada uno abre su URL.

---

### 54. Un hoster lento deja «Cargando» sin tope 🔴 ✅ *(resuelta, 2026-10-21)*

> ✅ **Resuelta el 2026-10-21** (deuda **B15**): `VideoPlayer` lleva un plazo propio,
> **`LOAD_TIMEOUT_S = 30`**, contado desde `play()` hasta el primer `playback-restart`. Si vence, para
> mpv **antes** de avisar —para que un medio que arranca tarde no suene detrás de la tarjeta— y llama a
> `on_error` («El servidor tarda demasiado en entregar el vídeo»): navegador y tarjeta con otro
> servidor, como cualquier error. Se cancela al empezar, en `stop_media()` y en `close()`, y cada
> `play()` lo reinicia. 30 s es ~10 veces un arranque normal (2-4 s) y queda **por encima** de los
> ~20 s con los que ya cae un servidor caído, así que solo actúa sobre los lentos. ✅ Verificado con el
> `VideoPlayer` real y un servidor local que gotea un byte cada 3 s: error a los **30,0 s** con mpv
> parado; un medio que arranca en 0,2 s no dispara nada en 40 s; y un segundo `play()` a los 15 s
> lleva el vencimiento a los **45,0 s**. Lo de abajo es la historia.

**Por qué**: el único plazo que hay es el `network-timeout` de mpv (15 s), y cuenta **por petición**,
no para el arranque entero. Un servidor que contesta cada petición en menos de 15 s —pero contesta a
todas despacio— nunca da error: mpv sigue abriendo el medio y la tarjeta de «Cargando» sigue puesta.
La aplicación **no tiene un tope propio** para pasar de «Cargando» a otra cosa.

**Síntoma observable**: ✅ visto en la prueba de humo de la fase 6 (2026-10-20) con `dandadan` ep. 1
por `HLS`. El log de mpv: el playlist de zilla tardó **13 s** (a `requests`, un minuto antes, **0,4 s**),
el segmento `init` 6 s, y la sonda del formato **47 s** más; el medio se abrió a los **~70 s**. Durante
todo ese rato, «Cargando el episodio 1» y ningún aviso. La degradación al navegador **no llega**,
porque técnicamente nada ha fallado. Ese mismo día AnimeAV1 tampoco dio la portada.

**Lo que salva al usuario hoy**: la columna sigue viva —puede pulsar otro servidor o «← Volver a la
ficha»— y la petición nueva deja obsoleta la vieja (número de petición). No se queda atrapado; se
queda **sin saber** si esperar.

**Lo que falta** (deuda **B15**, [12 §4](12-deuda-tecnica-y-roadmap.md)): un plazo propio de la
aplicación para la tarjeta de «Cargando» —contado desde `play()` hasta el primer `playback-restart`—
que, al vencer, haga lo mismo que un error: navegador y tarjeta con otro servidor. 🔴 Cambia `src/` y
**no es de la fase de documentación**: queda para una tarea aparte.

**Cómo comprobarlo**: el log de mpv (`log_handler` + `loglevel="v"`) dice cuánto tarda cada
`curl: Opening …`; si cada una baja de 15 s y la suma pasa de 20, es esto y no una caída.

---

## Ciclo de vida de los widgets de CustomTkinter *(añadidas 2026-10-21, auditoría de rendimiento)*

Las tres se destaparon midiendo, no usando la aplicación: **no se ve nada raro** y la velocidad apenas
cambia, solo crecen la memoria, los handles GDI y las imágenes de Tk con cada cambio de vista. El
patrón común: algo que vive toda la sesión sigue apuntando a un widget destruido, y ese widget retiene
a su `master`, el `master` a sus pósters, y así hasta la vista entera. Cómo se midió y con qué:
[09 §6j](09-verificacion-y-pruebas.md).

### 55. Un `CTkImage` que vive más que su widget lo retiene, con todo su árbol 🔴 ✅ *(resuelta 2026-10-21)*

**Por qué**: `CTkLabel` y `CTkButton` se apuntan en la lista de callbacks del `CTkImage` que reciben
(`_update_image`), y su `destroy()` **no se desapunta** —CustomTkinter 5.2.2, `ctk_label.py:146` y
`ctk_button.py:178`—, aunque su `configure(image=…)` sí lo hace con la imagen vieja. Así que un
`CTkImage` que sobrevive al widget lo mantiene vivo, y por la cadena de `master` también a la celda,
a la rejilla y a sus pósters.

**Síntoma**: ✅ medido, 75 cambios de vista → memoria privada de **49 a 239 MB**, GDI de 133 a 441,
imágenes de Tk de 59 a 367 y **6 893 widgets muertos** en memoria; ~2,4 MB más por cambio de vista. Una
estrella de 14 × 14 acumulaba **705** callbacks de widgets destruidos. Extrapolando, el tope de 10 000
GDI por proceso llegaría hacia los ~2 200 cambios de vista (⚠️ no reproducido).

**Dónde estaba**, en tres formas:

- las cinco cachés de iconos (`rating_stars`, `status_pill`, `empty_state`, `genre_chips` y
  `video_player`, con su aro de «Cargando») guardaban **el `CTkImage`** a nivel de módulo y lo
  compartían entre todos los widgets de la sesión;
- `PosterItem.badge_icon` metía un `CTkImage` en un dato que la vista conserva para paginar;
- `PosterGrid.__images`, en la rejilla ya destruida que la vista sigue guardando en un atributo.

**Invariante**: **un `CTkImage` no sobrevive a sus widgets.**

- Las cachés guardan **el dibujo PIL** (claro, oscuro), que es lo caro, y devuelven un `CTkImage`
  **nuevo** en cada llamada.
- Los datos llevan el **estado**, no la imagen: `PosterItem.badge_status`, y la rejilla dibuja el
  glifo.
- Compartir un `CTkImage` solo vale **dentro de un componente que muere entero**: `RatingStars`
  reparte sus ≤3 imágenes entre sus cinco estrellas, y `_ring_frames()` da una lista nueva por
  tarjeta.
- Un componente que guarda imágenes las suelta en su `destroy()` (`PosterGrid`).

**Cómo comprobarlo**: tras varias vueltas por las vistas, `len(img._configure_callback_list)` de cada
`CTkImage` vivo debe ser 1, y los `tkinter.Misc` con `winfo_exists() == 0` en `gc.get_objects()` no
deben crecer. ✅ Tras el arreglo, 75 cambios de vista: memoria privada **57-59 MB** plana, GDI 94,
imágenes de Tk 20 y **75 zombis constantes**. Esos 75 son los últimos widgets que cada vista guarda en
atributos (`__poster_grid`, `__pager`…), acotados. ⚠️ Una caché nueva de `CTkImage` a nivel de
módulo reintroduce la fuga entera, y no se nota en una prueba de humo.

---

### 56. Un `CTkOptionMenu` destruido se queda en el registro de escalado ✅ *(resuelta 2026-10-21)*

**Por qué**: el menú desplegable que lleva dentro, `DropdownMenu`
(`core_widget_classes/dropdown_menu.py:46-52`), no llama a `CTkScalingBaseClass.destroy()` al
destruirse. Su `_set_scaling` se queda en `ScalingTracker.window_widgets_dict` para siempre, y con él
el desplegable y su árbol.

**Síntoma**: ✅ +3 entradas en el registro de escalado por cada vuelta por las vistas, una por cada
desplegable de orden (Favoritos, Pendientes y Buscar); 44-45 `DropdownMenu` muertos tras 15 vueltas.

**Invariante**: un desplegable que **se destruye** es un `OrderMenu`
(`gui/components/order_menu.py`), cuyo `destroy()` saca su menú del registro. Un `ctk.CTkOptionMenu` a
secas solo vale en widgets que viven toda la sesión, como los dos de la barra lateral. ✅ Tras el
arreglo, el registro se queda en 88 entradas en las 15 vueltas.

---

### 57. `unbind_all()` no borra el comando que creó `bind_all()` ✅ *(resuelta 2026-10-21)*

**Por qué**: tkinter registra el callable de `bind_all()` y de `bind_class()` como **comando Tcl sin
limpieza** (`needcleanup=0`, `tkinter/__init__.py:1435`), y `unbind_all()` (`:1437`) solo quita la
atadura. El comando, y lo que referencie, vive hasta que muere la raíz. Un `bind()` normal no lo sufre:
sus comandos se borran al destruir el widget.

**Síntoma**: cada entrada en pantalla completa dejaba un `VideoPlayer` vivo, con su árbol, porque el
comando era el método ligado `__on_escape`. ✅ Reproducido con la misma secuencia: 50 ciclos → **+50
comandos Tcl y 50 objetos vivos**.

**Invariante**: guardar el *funcid* que devuelve `bind_all()` y llamar a `deletecommand(funcid)` tras
`unbind_all()`, como hace `VideoPlayer.set_fullscreen()` con `__escape_funcid`. ✅ Tras el arreglo, 50
ciclos → +0 comandos. ⚠️ La pantalla completa real no se ha vuelto a probar a mano después del cambio.

---

## Identidad de un anime por su título *(añadida 2026-10-26)*

### 58. Dos temporadas del mismo anime se parecen más que el umbral de «es el mismo» 🔴 ✅ *(resuelta 2026-10-26)*

**El bug**: lo único común entre proveedores es el título, así que la aplicación decide «esta fila
guardada es este anime» por **parecido de texto**. Y dos temporadas se parecen muchísimo como texto:

| Pareja | Parecido | Umbral que la confundía |
|---|---|---|
| «Kusuriya no Hitorigoto **3rd** Season» / «… **2nd** Season» | **0,939** | 0,9 (`DUPLICATE_TITLE_THRESHOLD`) |
| «Kusuriya no Hitorigoto» / «… 2nd Season» | **0,800** | 0,75 (`TITLE_MATCH_THRESHOLD`) |
| «Overlord II» / «Overlord III» | 0,957 | los dos |
| «Shingeki no Kyojin: The Final Season Part 2» / «… Part 3» | 0,976 | los dos |

**Síntoma** (reportado por el usuario el 2026-10-26): con la 2.ª temporada en «Viendo», al buscar la
3.ª en «Buscar» la rejilla le ponía el sello **«Viendo»**, y marcarla «Pendiente» **sacaba de
«Viendo» a la 2.ª**. No se creaba fila nueva: `find_saved_duplicate()` cruzaba la 3.ª con la fila de
la 2.ª, la búsqueda abría la ficha con ese `anime_record=` y la ficha escribía en **la fila de la
2.ª** (trampa 21). Como los estados
excluyentes se apagan entre sí, parecía que una temporada **pisaba** a la otra. Por el mismo camino,
con el desplegable desviado `resolve_anime_in_provider()` podía elegir otra temporada si al destino le
faltaba la buena, y «Actualizar a X» habría reescrito la identidad de la fila con ella.

**Por qué no lo frenaba el umbral**: subirlo no sirve. Lo que distingue dos temporadas es **un
carácter**, y cualquier umbral que lo separe rechaza también variantes legítimas del mismo título.

**Regla**: toda decisión de identidad por título pasa por **`AnimeProviderManager.title_similarity()`**
(`animeProviderMgr.py:486-505`), que da **0** si los números del título no coinciden.
`title_numbers()` (`:467-485`) los saca ordenados: dígitos de cada palabra («2nd» → 2, «Season 2» → 2) y
los romanos II-IX de `ROMAN_NUMERALS` (`:196-197`), **sin «i» ni «x»**, que sueltos son palabras
(«Hunter x Hunter»). La usan los tres sitios que deciden identidad:

| Sitio | Umbral |
|---|---|
| `find_saved_duplicate()` (`anime_window.py:275-306`): sello de «Buscar» y aviso al guardar | 0,9 |
| `match_animes_from_search()` (`utilsButtons.py:59-89`): búsqueda web de las cuatro vistas de estado | 0,75 |
| `resolve_anime_in_provider()` (`animeProviderMgr.py:506-560`): desviación del desplegable y «Actualizar a X» | 0,75 |

⚠️ **`filter_animes_by_title()` no la usa, y es a propósito**: eso es buscar, no identificar.
Escribir «kusuriya» en una vista de estado tiene que seguir encontrando **las tres** temporadas.

✅ **Verificado** sobre la BD real en solo lectura (46 filas) y contra AnimeAV1 y JKAnime:

- la 3.ª temporada ya no se cruza con ninguna fila, y la 1.ª y la 2.ª siguen cruzándose con la suya;
- en la biblioteca solo cambian de veredicto **3 pares**, y los tres eran errores: las dos temporadas
  de Kusuriya, «Shiguang Dailiren» / «… III» y «Jujutsu Kaisen 0 Movie» / «Jujutsu Kaisen (TV)»;
- relocalizando cada una de las 46 filas en el otro proveedor, **0** eligen un anime distinto que con
  el criterio anterior;
- ✅ el usuario guardó la 3.ª como pendiente y comprobó que conviven las tres.

**Lo que se pierde**: el mismo anime titulado con año en un sitio y sin año en otro («Hunter x Hunter
(2011)» / «Hunter x Hunter») ya no se reconoce como duplicado. No hay ningún caso en la biblioteca del
usuario, y equivocarse por ese lado deja una fila de más a la vista, no una fila pisada en silencio.

**Invariante**: si añades otro sitio que decida «esta fila es este anime» por título, usa
`title_similarity()`; nunca un `SequenceMatcher` suelto.

---

## Relaciones y franquicia *(añadidas 2026-10-28, versión 0.5.0)*

Las trae el plan de la 0.5.0 (temporadas, relacionados y «Te puede interesar»). Las cuatro primeras
son de **parseo**: cada sitio anuncia las relaciones a su manera, y equivocarse no da error, sino
relacionados de menos o una franquicia mal montada.

### 59. «Historia principal» y «Predecesor» no son precuelas ✅

AnimeAV1 (`type:8`, «Historia principal») y JKAnime («Predecesor») las usan para apuntar **de una
película, OVA o especial a su serie madre**, no a la temporada anterior.

**Síntoma si se traducen a `PREQUEL`**: el recorrido de la franquicia mete **la serie entera** como
temporada anterior de una película, y «◀ Temporada anterior» de la película 1 de SnK lleva a la serie.

**Invariante**: solo el código `1` de AnimeAV1 y la etiqueta «Precuela» de JKAnime son `PREQUEL`. Todo
lo que no sea precuela, secuela o versión alternativa es `OTHER` (decisión P3/P8 del usuario: solo
cuatro tipos). Un código de AnimeAV1 que no esté en la tabla cae en `OTHER` **con un `print`**, nunca
en excepción ([05 §3](05-proveedores-y-scraping.md)).

### 60. Un título de relación puede llevar corchetes y comillas escapadas ✅

El array `relations` del payload de AnimeAV1 es JavaScript, no JSON, y sus títulos pueden contener
`]` («[Oshi no Ko]») y `\"`.

**Síntoma con una regex perezosa hasta `]`**: el array se corta en el primer título con corchete y se
pierden **en silencio** todos los relacionados siguientes.

**Invariante**: `AnimeAV1.__extract_js_array()` recorta el array **contando corchetes y respetando las
cadenas**, y cada cadena se des-escapa con `json.loads`. ✅ Probado offline con `[Oshi no Ko]`, `\"`,
un código 99 y un payload sin `relations`.

### 61. En JKAnime, todos los `<h5>` de «Temporadas y relacionados» llevan el mismo `id` ✅

Cada bloque de tipo es `<h5 id="aditional">Secuela</h5>` seguido de sus enlaces, y **todos** repiten
`id="aditional"`. Además, `li[rel='tipo']` (el formato del propio anime) sale **dos veces** en la
página, en dos bloques de información.

**Síntoma**: un selector por `#aditional` devuelve solo el primer bloque, y ninguno distingue tipos.

**Invariante**: se recorren **en orden** los hermanos `h5`/`a` del `<h3>Temporadas y relacionados</h3>`;
el tipo de cada enlace es el texto del último `<h5>` visto. Del formato vale el primer `li[rel='tipo']`.

### 62. En JKAnime, el paréntesis final del enlace no siempre es el formato ✅

Los enlaces son «Título (Serie)», pero también «Hunter x Hunter (2011)».

**Síntoma**: separar siempre el último paréntesis deja «Hunter x Hunter» sin año y con un formato
«2011» que no existe.

**Invariante**: solo se separa si el paréntesis es un formato conocido (Serie, OVA, Pelicula —sin
tilde—, Especial, ONA). Si no, se queda en el título.

### 63. `get_anime_relations` de AnimeAV1 hereda los 3 reintentos de su ficha ✅

En AnimeAV1 la ficha ligera **es** `get_anime_info`, que reintenta tres veces con 1 s de espera.

**Síntoma**: sin red, cada salto fallido del recorrido tarda ~3 s; ante un 403 serían **tres
peticiones** al sitio en vez de una.

**Mitigación**: el recorrido se corta en el primer fallo y no repite esa página en 2 min
(`FranchiseService.RETRY_FAILED_AFTER_S`). Si molesta, la salida es sobrescribir `get_anime_relations`
en AnimeAV1 sin reintentos; no se ha hecho.

### 64. El mismo slug en el otro proveedor puede ser otro anime ✅

`request_formats` pide **una** ficha al otro proveedor con el mismo slug para completar formatos. El
slug coincide muchas veces entre sitios, pero no siempre significa lo mismo.

**Síntoma sin comprobarlo**: los relacionados se pintan con los formatos **de otra franquicia**.

**Invariante**: la página del otro proveedor se descarta si `title_similarity()` con el título propio
queda por debajo de `TITLE_MATCH_THRESHOLD` (es la [trampa 58](#58-dos-temporadas-del-mismo-anime-se-parecen-más-que-el-umbral-de-es-el-mismo---resuelta-2026-10-26)
aplicada a un slug).

### 65. El directorio de JKAnime responde 429 con su propio texto ✅

Tras las peticiones de una sesión anterior del mismo día, `jkanime.net/directorio` devolvió **429**
con «Estas realizando demasiadas peticiones… el bloqueo dura 60 segundos».

**Síntoma**: `search_animes_by_genres_and_order` cae en `raise_for_status()` y devuelve `([], 1)`; la
búsqueda **parece vacía** (trampa 12: el manager no distingue vacío de error).

**Invariante**: no reintentar solo. «Te puede interesar» trata un `([], 1)` como error y ofrece
**«Reintentar» a mano** ([09 §7.9](09-verificacion-y-pruebas.md)).

### 66. En AnimeAV1, dos géneros del catálogo se combinan con O, no con Y ✅

`catalogo?genre=accion&genre=romance` trae animes que solo tienen **uno** de los dos.

**Síntoma**: quien espere una intersección recibe animes que comparten un género, no los dos.

**Invariante**: es lo que da el sitio. «Te puede interesar» lo asume —cada resultado comparte **al
menos uno**— y, si tras filtrar faltan, pide **la página siguiente**, no «el primer género solo», que
con O sería un subconjunto de lo ya pedido.

---

## Verificar fuera de la aplicación *(añadidas 2026-10-28)*

Las cuatro mienten a un **script de verificación**, no a la aplicación. Las cuatro hicieron perder
tiempo durante el plan de la 0.5.0.

### 67. `after()` desde un hilo sin `mainloop()` en el principal no avisa ✅

Con un `tk.Tk()` oculto y `root.update()` en bucle, `after()` desde un hilo lanza
`RuntimeError: main thread is not in main loop`, y `FranchiseService` (como `EpisodeRefresher`) lo
traga como «la ventana se cerró».

**Síntoma**: el script **se queda esperando el callback para siempre**, sin error.

**Cómo evitarlo**: en los scripts, esperar con `root.mainloop()` y `root.quit()` en el callback. En la
aplicación no pasa: Tk está en `mainloop()`.

### 68. `requests.get()` llega a `Session.request` con el método en minúsculas ✅

`requests.get()` pasa `'get'`; la `Session` de JKAnime y `thread_session()`, `'GET'`.

**Síntoma**: un contador de peticiones que compare `== "GET"` da falsos «ha habido un POST».

**Cómo evitarlo**: normalizar con `.upper()` al contar.

### 69. Las listas del hub se reasignan al terminar la carga del arranque ✅

`MainWindow.finished_animes` y compañía se **reasignan** (no se mutan) cuando acaba la carga.

**Síntoma**: un script que guarda `app.finished_animes` justo tras crear la ventana se queda con la
lista vacía de antes de cargar.

**Cómo evitarlo**: leerlas en el momento de usarlas, nunca guardarlas al arrancar. Es la misma
familia que la [trampa 31](#31-los-contadores-de-la-barra-salen-de-listas-que-solo-se-llenan-al-arrancar--).

### 70. `CTkScrollbar._draw()` llama a `update_idletasks()` por dentro ✅

**Síntoma**: en `cProfile`, el repintado de toda una página aparece como **80 ms en
`CTkScrollbar.set`**, y parece que lo caro es la barra de desplazamiento.

**Cómo leerlo**: el `set` lo dispara el cambio de alto del contenido y **arrastra todo el repintado
pendiente** de Tk. Lo que mide es el coste de Tk, no el de la barra.

---

## Lo que cuesta pintar con CustomTkinter *(añadidas 2026-10-28)*

### 71. Un `CTkFrame` de `height=1` no pinta nada 🔴 ✅

CustomTkinter 5.2.2 redondea el alto **a par** al dibujar: uno de 1 px no pinta, uno de 3 pinta 2.

**Síntoma**: una raya de 1 px hecha con `CTkFrame` no aparece, sin error. **El separador de
`EpisodeRow` (`height=1`) no se vio nunca**: comprobado leyendo píxeles, y por eso se quitó en la fase
3 ([trampa 37](#37-un-hijo-sin-bind-es-un-agujero-por-el-que-el-hover-se-queda-encendido---resuelta-2026-09-01)).

**Cómo evitarlo**: rayas de 2 px. Si tiene que verse 1, se coloca con `place(..., y=1)` medio fuera de
su marco, que la recorta. Es lo que hace la raya de `TabBar`.

### 72. Cada widget de CustomTkinter cuesta ~3,5 ms al abrir una pantalla 🔴 ✅

Crearlo, pintarlo en el `update()` y destruirlo en el siguiente `clear_frame()`. El código Python que
lo construye es lo de menos.

**Síntoma**: la primera versión de la ficha con pestañas tardaba **40-75 ms más** que `develop` por
~13 widgets de la barra y 6-7 por enlace de temporada, aunque `__build_tabs` solo sumaba 5 ms de
Python.

**Cómo evitarlo**: contar widgets, no líneas; nada de marcos intermedios en lo que se pinta al abrir.
Y medirlo **contra `develop` en la misma tanda, alternando** (un *worktree* en el scratchpad): entre
arranques la línea base se mueve 15-30 ms ([09 §6l](09-verificacion-y-pruebas.md)).

### 73. Atar todo un subárbol con el `bind` de CustomTkinter ejecuta el clic dos veces ✅

`CTkBaseClass.bind()` reenvía a los hijos internos del widget. Si además se recorre el árbol entero
atando cada widget, los internos quedan atados **dos veces**.

**Síntoma**: el clic en una tarjeta abre dos fichas, o pide dos veces lo mismo.

**Invariante**: `ClickableCard.bind_card()` (`franchise_cards.py`) ata con **`tkinter.Misc.bind(w, …,
"+")`** cada widget del subárbol, internos de CTk incluidos —**lienzos de los `CTkFrame` también**,
que es lo que el recorrido se saltaba hasta el 2026-10-29 ([trampa 81](#81-ctkframewinfo_children-oculta-su-lienzo-y-el-lienzo-es-casi-toda-la-tarjeta---resuelta-2026-10-29))—. Ata exactamente ese widget, y así
`event_generate("<Button-1>")` sobre el marco también dispara
([trampa 35](#35-bind-y-event_generate-no-hablan-del-mismo-widget-en-customtkinter--)).

### 74. Volver a mostrar una página conservada no es gratis ✅

Tk repinta cada lienzo de CustomTkinter al volver a colocar la página: ~0,1 ms por widget.

**Síntoma**: «Favoritos» tarda **136 ms** en volver con solo 12 ms de Python. Por debajo de 50 ms solo
baja «Buscar», la vista con menos widgets.

**Consecuencia**: el siguiente escalón de B13 es **pintar menos widgets por vista**, no conservar
mejor ([12 §4](12-deuda-tecnica-y-roadmap.md)).

### 75. Una página recién creada mide 1 px de ancho 🔴 ✅

Hasta el siguiente paso de geometría, y `PosterGrid` saca sus columnas del ancho de su contenedor
([trampa 41](#41-una-rejilla-con-stickyw-mide-su-propio-contenido-no-el-hueco-que-tiene---resuelta-2026-09-02)).

**Síntoma**: la primera visita a una rejilla con la ventana maximizada pinta las columnas del diseño y
repinta al momento: el doble de coste.

**Invariante**: `MainWindow.show_view()` hace `update_idletasks()` **solo** cuando la página aún no
mide nada.

### 76. Repintar los seis ítems de la barra en cada cambio de vista costaba 23 ms ✅ *(resuelta 2026-10-28)*

Más que el Python de reutilizar una página. Invisible a ojo; sale en el perfil de una vuelta
conservada.

**Invariante**: `_NavItem.set_active()` (`sidebar.py`) no repinta si el estado no cambia. Quien añada
estado a un ítem de la barra, que lo compare antes de repintar.

---

## Hilos y recolección de basura *(añadidas 2026-10-28)*

### 77. Un widget sin `font=` puede congelar la aplicación al lanzar un hilo 🔴 ✅ *(mitigada 2026-10-28)*

**La cadena**, en cuatro pasos:

1. Un widget de CustomTkinter **sin `font=`** crea su propio `CTkFont`, que queda en un **ciclo de
   referencias** con él.
2. Al destruir el widget, esa fuente solo la libera el **recolector de basura**, en el hilo en el que
   toque correr.
3. `tkinter.font.Font.__del__` llama a Tcl, y desde otro hilo eso **espera al de Tk**.
4. Si ese hilo es uno que el de Tk acaba de crear, el de Tk está esperando en `Thread.start()` a que
   arranque. **Se bloquean los dos.**

**Síntoma**: la aplicación **se congela sin error y con la CPU a 0** justo al pulsar algo que destruye
widgets y lanza un hilo. Le pasaba a «Reintentar» de «Te puede interesar» en 2 de 3 ejecuciones con
red. Pila con `faulthandler`: el de Tk en `threading.py … start` ← `__request_recommendations`; el
hilo nuevo en `_bootstrap_inner` → `tkinter/font.py … __del__`. ✅ Aislado en un experimento: 20
etiquetas sin fuente → **20** `Font.__del__` en el hilo que recoge; con fuente compartida, 0.

**Invariante**: `font=Theme.font(...)` (de la caché) en **todo** widget de CustomTkinter, **aunque no
lleve texto**. Arreglado en `PosterGrid` y en `_poster_slot()` de `franchise_cards.py`.

🔴 **Siguen 17 widgets sin `font=`** (inventario con AST del 2026-10-28; se citan por fichero porque
las líneas se mueven): 2 en `anime_window.py`, 1 en `main_window.py`, `anime_row.py`, `empty_state.py`,
`rating_stars.py`, `resume_card.py`, 3 en `sidebar.py`, `side_panel.py`, 5 en `video_player.py` y 1 en
`searchAnimes.py`. Pueden colgar la aplicación igual; no se ha intentado reproducirlo fuera de esa
pestaña. Es la deuda **B18** ([12 §4](12-deuda-tecnica-y-roadmap.md)).

### 78. Un hilo de póster retiene la ficha entera hasta que termina su descarga ✅

Guarda el método de entrega (`deliver`), y con él `self`: la ficha.

**Síntoma**: en un bucle rápido de aperturas, las imágenes de Tk «crecen» de 35 a 67 y luego se
estabilizan. Era una fila con póster de AnimeFLV, que tarda 10 s en fallar.

**No es una fuga**: dura lo que el *timeout*. Para medir memoria, usar pósters que no dependan de un
sitio lento, o esperar a los hilos ([09 §6j](09-verificacion-y-pruebas.md)). Con pósters que no
cuelgan: **26 imágenes sin la pestaña y 32 con ella**, iguales en 25 vueltas.

---

## Ficha con pestañas y vistas conservadas *(añadidas 2026-10-28)*

### 79. Desplazarse hasta un episodio con otra pestaña delante mide un widget sin colocar ✅

El reproductor desplaza la ficha al cambiar de episodio, y «Viendo» abre la ficha por un episodio.

**Síntoma**: con «Temporadas y relacionados» delante, la ficha salta a cualquier sitio.

**Invariante**: `__scroll_to_episode()` (`anime_window.py`) no hace nada si la pestaña activa no es
«Episodios».

### 80. La firma de una vista conservada tiene que ser una copia 🔴 ✅

Las vistas modifican sus filas en memoria; por ejemplo, la calificación de «Favoritos».

**Síntoma sin copia**: la firma cambia a la vez que la fila y siempre coincide. Tras calificar, volver
a «Favoritos» **no reordenaría**.

**Invariante**: `MainWindow.show_view()` hace `deepcopy` de la firma al guardarla, y solo cuando
reconstruye. Comparar la lectura nueva no copia nada.

### 81. `CTkFrame.winfo_children()` oculta su lienzo, y el lienzo es casi toda la tarjeta 🔴 ✅ *(resuelta 2026-10-29)*

CustomTkinter sobrescribe `winfo_children()` en `CTkFrame` para quitar de la lista su `_canvas`,
el que pinta fondo y borde. Un recorrido que ata eventos con `widget.winfo_children()` **se salta el
lienzo de cada marco**: el de la tarjeta y el de cada marco intermedio.

**Síntoma**: en «Temporadas y relacionados», pulsar un relacionado **a veces no hace nada**, y el
segundo clic, un poco más allá, lo abre al instante. Solo respondían el póster y los textos, ~30 % de
una tarjeta de 377 × 88: el centro, la derecha vacía y los márgenes, no. El cursor de mano y el
resaltado sí salían en toda la tarjeta, así que parecía un clic perdido. Igual en el margen de las
pestañas de la ficha. Se destapó el 2026-10-29 registrando cada `<ButtonPress-1>` con `bind_all`:
la pulsación llegaba a `…relatedcard.!ctkframe.!ctkcanvas` y el manejador no se ejecutaba.
⚠️ **`event_generate("<Button-1>")` sobre el marco no lo detecta**, porque dispara en el marco, que
sí está atado: hay que pulsar con el ratón real **en el fondo**.

**Invariante**: `_walk()` (`franchise_cards.py`) y el recorrido de `TabBar.__bind_tab()` usan
**`tkinter.Misc.winfo_children(widget)`**, que sí incluye los lienzos. `AnimeRow` no lo sufre porque
ata con el `bind()` de CustomTkinter, que en un `CTkFrame` ya ata su lienzo
([trampa 73](#73-atar-todo-un-subárbol-con-el-bind-de-customtkinter-ejecuta-el-clic-dos-veces-)).
Y al revés: `PosterGrid.__clear_cells()` **cuenta** con que el lienzo no salga, para no destruirlo.

---

## Resumen: las 5 que más duelen

1. **Trampa 21** — en la ficha, `anime_info.id` no es la clave de la BD; confundirlas duplica filas
   en la biblioteca real. **La única que ya se ha reintroducido una vez** (fase 4, 2026-08-16).
2. **Trampa 26** — buscar en la biblioteca por slug hace desaparecer animes que sí tienes guardados,
   según qué proveedor tengas puesto.
3. **Trampa 4** — el orden de `episodes` depende del proveedor y se invierte al guardar; y ahora hay
   una lista que **no** hay que invertir.
4. **Trampa 7** — marcar episodios sin estado asignado no guarda nada, sin avisar.
5. **Trampa 17** — la purga de pósters borra todo lo que no esté en la lista actual.

*(Caen de la lista la trampa 8 —solo 25 episodios— y la 6 —`str` vs enum en la ordenación—, las dos
vigentes pero menos dañinas que las de arriba.)*

> 🆕 **Fuera de la lista, pero a vigilar** (2026-10-28): la **trampa 77**. No toca la biblioteca, pero
> **congela la aplicación** sin error, y quedan 17 widgets que pueden provocarla. Todo widget nuevo de
> CustomTkinter lleva `font=`.

> **Trampas retiradas de esta lista el 2026-07-30**, todas por estar resueltas: **1** y **2**
> (desalineación de columnas y ausencia de migraciones, mitigadas por `validate_db_integrity()`),
> **15** y **16** (el póster a 20×20 y la carpeta `watching/` olvidada), **10** (clic sin comprobar
> `None`) y **14** (mojibake de AnimeAV1).
>
> Las entradas **no se renumeran ni se borran**: otros documentos las citan por número. Una trampa
> resuelta se marca tachada y conserva su invariante vigente, si le queda alguno.
