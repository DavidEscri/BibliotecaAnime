# 04 — Modelo de datos

| | |
|---|---|
| **Fecha** | 2026-08-16 · **Commit** `54fb3d6` · árbol **sucio**: 16 ficheros de `src/` con la columna `provider_id` sin commitear |
| **Última revisión** | 2026-08-16 — **`provider_id` implementada**: columna nueva en `ANIMES` (§2, §3), `AnimeProviderId` y `ProviderInfo` en `models.py` (§1b), `migrate_anime_identity()` y `get_all_animes()` (§8). La migración automática se ha ejecutado **sobre la BD real** por primera vez (§3) |
| **Cubre** | `src/APIs/common/models.py`, `src/dataPersistence/animesPersistence.py`, `src/dataPersistence/userPersistence.py`, `src/utils/db/sqlite.py` |

Procedencia: ✅ verificado en ejecución (sobre una **copia** de la BD real, 24-28 filas) · 📖 leído en
código · ⚠️ sin verificar.

---

## 0. Las dos bases de datos

✅ Desde el 2026-07-30 hay **dos** ficheros SQLite en `resources/DB/`, cada uno con su clase derivada
de `ServiceDB` y su propia lista `SCHEMA`. El motor de migración de `utils/db/sqlite.py` es genérico y
sirve a las dos por igual.

| BD | Clase | Tablas | Naturaleza |
|---|---|---|---|
| `DB_Animes.db` | `AnimesPersistence` | `ANIMES` | La **biblioteca real** del usuario. Irrecuperable: nunca escribir desde un script |
| `DB_user.db` | `UserPersistence` | `USER_SETTINGS` | Preferencias. **Desechable**: se puede borrar y se regenera vacía |

### `USER_SETTINGS` — clave/valor

📖 `userPersistence.py`. Esquema deliberadamente genérico: añadir una preferencia es **una fila nueva**,
no una migración.

| # | Columna | Tipo | Contenido |
|---|---|---|---|
| 1 | `setting_key` | `VARCHAR(100)` | Valor de `UserSettingKey`. **PRIMARY KEY** |
| 2 | `setting_value` | `TEXT` | Valor, siempre como texto; quien lee convierte |
| 3 | `updated_at` | `VARCHAR(30)` | ISO-8601 de la última escritura, para depurar |

Claves declaradas en `UserSettingKey`:

| Clave | Valor | Estado |
|---|---|---|
| `default_anime_provider` | **`AnimeProviderId.value`** (`"animeav1"`, `"jkanime"`, `"animeflv"`) | ✅ en uso |
| `default_manga_provider` | `value` del proveedor de manga | 🔮 reservada (comentada en el enum) |

> ⚠️ **Frontera enum ↔ texto.** Desde el 2026-08-16 el proveedor es un enum (`AnimeProviderId`, §1b) en
> todo el código, y solo se convierte a texto en **dos** sitios, los dos de persistencia:
>
> | Frontera | Ida | Vuelta |
> |---|---|---|
> | `USER_SETTINGS.default_anime_provider` | `main_window.py:307` (`.value` al guardar el pin) | `main_window.py:264` (`AnimeProviderId(saved_value)`) |
> | `ANIMES.provider_id` | `AnimeRecord.to_db_dict` (`animesPersistence.py:94`) | `AnimeRecord._provider_id_from_db` (`:153-171`) |
>
> Las dos vueltas toleran basura: un valor que ya no corresponde a ningún miembro del enum se ignora
> con un aviso por consola (preferencia obsoleta → se usa el predeterminado del registro; fila con
> proveedor desconocido → se trata como si no tuviera). **Nunca lanzan**: un proveedor retirado del
> código no puede impedir arrancar ni leer la biblioteca. ✅ Verificado con valores inventados.

`set_setting()` hace **upsert** (`INSERT … ON CONFLICT(setting_key) DO UPDATE`), así que la primera
escritura y las siguientes son la misma operación. ✅ Verificado: escribir 4 veces deja 1 fila.

**Tolerancia a fallos por diseño**: si `DB_user.db` no se puede abrir, `UserPersistence.available`
queda a `False`, `get_setting()` devuelve el valor por defecto que le pasen y `set_setting()` devuelve
`False`. La aplicación arranca igual con el proveedor predeterminado del código. ✅ Verificado con una
ruta imposible.

Razonamiento de por qué es una BD aparte y no una tabla de `DB_Animes.db`:
[13 D1](13-selector-de-proveedor.md).

---

## 1. `AnimeInfo` (red) vs `AnimeRecord` (BD)

**No son intercambiables.** `AnimeInfo` es lo que devuelve un proveedor; `AnimeRecord` es una fila de
`ANIMES`. Confundirlos es el error más frecuente en este repo.

| `AnimeInfo` (`models.py:118-131`) | `AnimeRecord` (`animesPersistence.py:63-83`) | Trampa |
|---|---|---|
| `id: Union[str,int]` | **`anime_id: str`** | ⚠️ **nombres distintos** |
| — | `id: Optional[int]` = **PK autoincremental** | ⚠️ `AnimeInfo.id` ≠ `AnimeRecord.id` |
| `title: str` | `title: str` | |
| **`poster: str`** | **`poster_url: str`** | ⚠️ nombres distintos |
| `synopsis: Optional[str]` | `synopsis: Optional[str]` | |
| `genres: Optional[List[str]]` | `genres: List[str]` (default `[]`) | `None` vs `[]` |
| **`episodes: Optional[List[EpisodeInfo]]`** | **`episodes: List[int]`** | ⚠️ **objetos vs enteros** |
| **`provider_id: Optional[AnimeProviderId]`** | **`provider_id: Optional[AnimeProviderId]`** | 🆕 el **único** campo con el mismo nombre y el mismo tipo en los dos |
| — | `watched_episodes: Set[int]` | solo en BD |
| — | `last_watched_episode: int` | solo en BD |
| — | `is_favourite/is_watching/is_finished/is_pending: bool` | solo en BD |

### Cheatsheet

```python
anime_info.id          ==  anime_record.anime_id     # el slug: "one-piece"
anime_info.poster      ==  anime_record.poster_url   # la URL
anime_info.provider_id ==  anime_record.provider_id  # AnimeProviderId en ambos
[e.id for e in anime_info.episodes]  ~=  anime_record.episodes   # ¡pero ver §4!
anime_record.id        # PK de SQLite — NO existe en AnimeInfo
```

> ⚠️ **`anime_id` sin `provider_id` no identifica nada.** Un slug es local a un sitio: el mismo anime es
> `one-piece` en AnimeAV1 y JKAnime, y `one-piece-tv` en AnimeFLV; y `dandadan` existe en los tres. La
> pareja **(`provider_id`, `anime_id`)** es lo que identifica de verdad una fila, aunque la tabla no lo
> declare (§3, «lo que NO impone el esquema»). Buscar en la biblioteca por slug es la trampa **26**.

### Conversión

| Dirección | Método | Línea |
|---|---|---|
| `AnimeInfo` → `AnimeRecord` | `AnimeRecord.from_anime_info(info, provider_id=None, is_*=...)` | `:176-207` |
| fila BD → `AnimeRecord` | `AnimeRecord.from_db_dict(dict)` | `:112-150` |
| `AnimeRecord` → dict para INSERT | `record.to_db_dict()` | `:88-110` |
| `AnimeRecord` → `AnimeInfo` | **no existe** ⚠️ | — |

`from_anime_info()` acepta `provider_id` explícito y, si no se le pasa, **toma el del propio
`AnimeInfo`** (`:205`), que es el que estampa el manager al responder (§1b). Quien inserta no tiene
que acordarse de nada.

> ⚠️ **No hay conversión de vuelta.** Por eso las vistas de favoritos/finalizados/viendo/pendientes,
> que tienen `AnimeRecord`, siguen haciendo una petición de red al hacer clic en un anime en vez de
> reutilizar lo que ya tienen en BD. Lo que sí ha cambiado (2026-08-16) es **a quién** se le pide: las
> cuatro vistas llaman a `open_saved_anime()` (`anime_window.py:108-193`), que usa el `provider_id` de
> la fila en vez de disparar el fallback a ciegas.

---

## 1b. `AnimeProviderId` y `ProviderInfo` — el proveedor como tipo

📖 `models.py:18-47`. Antes de 2026-08-16 el proveedor era una **cadena suelta** (`"animeav1"`) que
viajaba por las firmas del manager. Al persistirlo hacía falta algo con nombre:

```python
class AnimeProviderId(Enum):     # models.py:18-31
    ANIMEAV1 = "animeav1"        # el value es lo que se guarda en BD
    JKANIME  = "jkanime"
    ANIMEFLV = "animeflv"

@dataclass(frozen=True)
class ProviderInfo:              # models.py:34-47
    id: AnimeProviderId
    name: str                    # "AnimeFLV" — lo que ve el usuario
    base_url: str
```

| Pieza | Dónde vive | Para qué |
|---|---|---|
| `AnimeProviderId` | `models.py:18` | Tipo del proveedor en **todas** las firmas, en `AnimeInfo.provider_id` y en la columna `ANIMES.provider_id` |
| `ProviderInfo` | `models.py:35` | Ficha de identidad que consume la GUI (el desplegable). `frozen` porque describe una constante del código |
| `AnimeProvider.provider_info()` | `animeProviderMgr.py:78-85` | La construye desde los atributos de clase del proveedor, para que **no exista una lista paralela de nombres** que mantener |

**Añadir un proveedor implica añadir un miembro aquí**, además de la clase y el registro. Sin él,
`__init_subclass__` (`animeProviderMgr.py:71-75`) revienta al importar con `NotImplementedError`: el
registro indexa por enum, así que una cadena suelta registraría el proveedor bajo una clave que nadie
busca y el fallo no aparecería hasta el primer `get()` fallido. ✅ Verificado.

### Quién rellena `AnimeInfo.provider_id`

**No los proveedores: el manager.** `call_with_fallback` (`animeProviderMgr.py:325`) llama a
`__stamp_provider()` (`:263-283`) justo antes de devolver, y sella el `AnimeProviderId` de quien
realmente respondió sobre cada `AnimeInfo` del resultado. Dos motivos:

1. Es el único que sabe **cuál** de ellos acabó respondiendo cuando entra el fallback.
2. Los proveedores no tienen que acordarse de rellenar el campo — uno que se olvide no rompe nada.

Cubre las tres formas en que viaja un `AnimeInfo` por esa capa: suelto (`get_anime_info`), en lista
(`get_recent_animes`) y dentro de la tupla `(lista, última_página)` de las búsquedas. Cualquier otro
resultado (`ServerInfo`) se ignora en silencio.

> `provider_id = None` en un `AnimeInfo` significa **«no pasó por el manager»** (lo construyó alguien a
> mano, como la referencia que se le pasa a `resolve_anime_in_provider`). No significa «no se sabe».

---

## 2. `AnimeField` → `FIELDS` / `FIELD_TYPES`

📖 `animesPersistence.py:28-57` y `:242-244`.

```python
class AnimeField(Enum):
    ID = ("id", "INTEGER")          # value = (columna, tipo SQLite)
    ...
    @property
    def column(self)   -> str: return self.value[0]
    @property
    def sql_type(self) -> str: return self.value[1]

FIELDS      = [f.column   for f in AnimeField]   # :242
FIELD_TYPES = [f.sql_type for f in AnimeField]   # :243
PRIMARY_KEY = "id AUTOINCREMENT"                 # :244
```

**Añadir una columna = añadir un miembro al enum.** Nada más… en una BD *nueva*. Ver §3.

| Miembro | Columna | Tipo declarado hoy |
|---|---|---|
| `ID` | `id` | `INTEGER` (PK autoincremental) |
| 🆕 `PROVIDER_ID` | `provider_id` | `VARCHAR(50)` — `AnimeProviderId.value`, o `NULL` |
| `ANIME_ID` | `anime_id` | `VARCHAR(100)` |
| `TITLE` | `title` | `VARCHAR(100)` |
| `POSTER_URL` | `poster_url` | `VARCHAR(200)` |
| `SYNOPSIS` | `synopsis` | `TEXT` |
| `GENRES` | `genres` | `JSON` |
| `EPISODES` | `episodes` | `JSON` |
| `WATCHED_EPISODES` | `watched_episodes` | `JSON` |
| `LAST_WATCHED_EPISODE` | `last_watched_episode` | `INTEGER` |
| `IS_FAVOURITE` | `is_favourite` | `BOOLEAN` |
| `IS_WATCHING` | `is_watching` | `BOOLEAN` |
| `IS_FINISHED` | `is_finished` | `BOOLEAN` |
| `IS_PENDING` | `is_pending` | `BOOLEAN` |

> ⚠️ **El orden de `AnimeField` debe coincidir con el de las columnas físicas.** Todas las consultas
> son `SELECT *` y `SqlUtils.query_sql` (`sqlite.py:122-144`) empareja `fila[i] → FIELDS[i]` **por
> posición**. Si se descuadra, los valores acaban en la clave equivocada **sin error alguno**.
> ✅ Hoy coinciden — reverificado el 2026-08-16 tras insertar `PROVIDER_ID` **en segunda posición**,
> que es el caso peligroso (columna nueva en medio, no al final: obliga a reconstruir la tabla).
> Trampa 1.

**Por qué `provider_id` va en la posición 2 y no al final**, que habría sido más barato de migrar: es
parte de la **identidad** de la fila, y las columnas de identidad van juntas al principio. Quien lea
un `SELECT *` en el intérprete debe ver `(id, provider_id, anime_id, title, …)` y entender de un
vistazo que el slug pertenece a un sitio concreto. El coste —una reconstrucción de tabla— lo paga el
motor de migración una sola vez, y era justo lo que ese motor existía para poder hacer.

---

## 3. Esquema **real** de la tabla `ANIMES`

✅ Extraído con `PRAGMA table_info` de la BD real del usuario **el 2026-08-16**, ya migrada:

```sql
CREATE TABLE "ANIMES" (
  id INTEGER, provider_id VARCHAR(50), anime_id VARCHAR(100), title VARCHAR(100),
  poster_url VARCHAR(200), synopsis TEXT, genres JSON, episodes JSON, watched_episodes JSON,
  last_watched_episode INTEGER, is_favourite BOOLEAN, is_watching BOOLEAN,
  is_finished BOOLEAN, is_pending BOOLEAN,
  PRIMARY KEY (id AUTOINCREMENT)
)
```

Coincide **exactamente** con `AnimeField`, en orden y en tipos declarados. Las comillas de `"ANIMES"`
son la firma de una tabla reconstruida por `validate_db_integrity()`.

### La migración automática, ejecutada de verdad ✅

El 2026-08-16 el motor de migraciones de 2026-07-30 hizo su **primer trabajo real sobre la biblioteca
del usuario**: `provider_id` entró en la posición 2, que es el caso caro (columna en medio →
reconstrucción completa de la tabla, no `ALTER TABLE`).

| Comprobación | Resultado |
|---|---|
| Filas antes / después | **25 / 25** — ninguna perdida ✅ |
| Columnas de datos (las 12 que no son `provider_id`) | idénticas fila a fila ✅ |
| `watched_episodes` de `one-piece-tv` (`[[1, 1158]]`) | intacto ✅ |
| Copia previa | `resources/DB/backups/DB_Animes_20260816_124630.db` (25 filas, **sin** `provider_id`) ✅ |
| Segundo arranque | no vuelve a tocar nada ni crea copia — idempotente ✅ (verificado sobre copia en `test_fase1.py`) |

**Estado hoy**: 28 filas, **0 con `provider_id` a `NULL`**; reparto `animeflv` 19 · `animeav1` 8 ·
`jkanime` 1.

> ⚠️ **Ese reparto no dice de dónde salió cada anime originalmente.** Las 23 filas anteriores a la
> columna se rellenaron con el **autorrelleno** de la ficha (§8), que anota **quién sirvió la ficha la
> primera vez que la abriste**. Cuando el slug existe en varios sitios —`dandadan` está igual en los
> tres— el que queda anotado es simplemente el que tenías seleccionado ese día. La columna responde
> «**quién sirve este slug**», no «quién lo trajo». Para el uso que se le da —a quién preguntar al
> reabrir— es la respuesta correcta; para una estadística de origen, no. Trampa 27.
>
> Se escribió un barrido de detección previo (`barrido_provider_id.py`, en el scratchpad de la sesión,
> **no en el repo**) que preguntaba a cada proveedor por el slug en el orden de la aplicación. Su
> resultado difiere del estado actual justo en esas filas de slug compartido, y por el mismo motivo:
> ambos son ciertos, y el primero que responde depende del orden en que se pregunte.

### Discrepancias históricas BD real ↔ `AnimeField` (migración de 2026-07-30)

| Columna | En la BD real (pre-migración) | En `AnimeField` | Veredicto |
|---|---|---|---|
| `anime_id` | **`INTEGER`** | `VARCHAR(100)` | Afinidad distinta (INTEGER vs TEXT) → **se reconstruye la tabla** |
| `poster_url` | **`VARCHAR(100)`** | `VARCHAR(200)` | Misma afinidad TEXT → **se ignora**, es cosmético |

✅ La divergencia de `anime_id` **no causó daño** gracias al tipado dinámico de SQLite: los 24
`anime_id` almacenados tenían `typeof(anime_id) = 'text'` aunque la columna se declarase `INTEGER`.
El riesgo era a futuro: un slug puramente numérico se habría guardado como entero y
`WHERE anime_id = ?` con un `str` habría dejado de encontrarlo. Hoy `poster_url` ya figura como
`VARCHAR(200)` porque la reconstrucción de `provider_id` reescribió la tabla entera con los tipos
declarados.

### Lo que el esquema **no** impone ⚠️

| No hay | Consecuencia |
|---|---|
| `UNIQUE` sobre `anime_id` | Nada impide dos filas con el mismo slug. Es lo que obliga a `migrate_anime_identity()` a comprobarlo a mano (§8) |
| `UNIQUE` sobre `(provider_id, anime_id)` | Ídem, para la identidad real |
| `NOT NULL` en `provider_id` | `NULL` es un estado legítimo: «fila anterior a la columna, o proveedor que ya no existe en el código» |
| `FOREIGN KEY` / `CHECK` de `provider_id` | Un valor no reconocido se degrada a `None` al leer (`_provider_id_from_db`), no revienta |

Ninguna de estas restricciones se añadió a propósito: `SqlUtils` no distingue un fallo de constraint
de cualquier otro error (imprime y devuelve `False`), así que una violación se vería como «no se pudo
guardar» sin más. La comprobación explícita en Python puede explicar qué pasa.

### Política de migraciones ✅

Desde 2026-07-30 el esquema declarado es `AnimesPersistence.SCHEMA` (lista de `TableSchema`, derivada
de `AnimeField` para la tabla `ANIMES`) y `start()` llama a `validate_db_integrity()` en todo arranque.

| Escenario | Qué ocurre |
|---|---|
| BD nueva (fichero ausente) | Se crean **todas** las tablas de `SCHEMA` ✅ |
| BD existente + miembro nuevo al final del enum | `ALTER TABLE … ADD COLUMN`, sin mover datos ✅ |
| BD existente + miembro nuevo **en medio** del enum | Reconstrucción: el orden físico se realinea con el declarado, copiando por nombre de columna ✅ |
| BD existente + tipo cambiado (afinidad distinta) | Reconstrucción ✅ |
| BD existente + tipo cambiado (misma afinidad) | Se ignora, no se toca la BD ✅ |
| `TableSchema` nuevo añadido a `SCHEMA` | `CREATE TABLE` sobre la BD existente ✅ |
| Columna en BD **no declarada** en `SCHEMA` | Se descarta en la reconstrucción, con aviso por consola; queda en la copia de seguridad ⚠️ |

La comparación de tipos es **por afinidad SQLite** (`sqlite_affinity()` en `utils/db/sqlite.py`), no
por texto literal. Antes de la primera modificación se copia el `.db` a
`resources/DB/backups/DB_Animes_<timestamp>.db`. El proceso es idempotente: sin diferencias no toca la
BD ni crea copias.

**Receta al añadir una columna** → [11 §2](11-playbooks.md).

---

## 4. Serializaciones

### `provider_id` → texto, o `NULL`

📖 `to_db_dict:94` → `self.provider_id.value if self.provider_id else None`.
`from_db_dict:137` → `_provider_id_from_db()` (`:153-171`).

| En BD | Al leer | Significado |
|---|---|---|
| `"animeav1"` | `AnimeProviderId.ANIMEAV1` | normal |
| `NULL` / `""` | `None` | fila anterior a la columna, o proveedor borrado a propósito |
| `"monoschinos"` (no está en el enum) | `None` + aviso por consola | proveedor retirado del código |

Los dos últimos casos **se tratan igual a propósito**: los dos significan «no se sabe de quién es esta
fila», y quien lo consume (`provider_for_saved_anime`) ya sabe qué hacer con eso — caer al proveedor de
referencia. ✅ Verificado que un valor inventado no lanza y deja la fila legible.

### `genres` → JSON plano

📖 `:98`. `json.dumps(self.genres)` → `["accion", "aventura"]` ✅ verificado en BD.
Las consultas por género usan `LIKE '%"accion"%'` (`:369`) — de ahí que las comillas del JSON
importen.

### `episodes` → JSON **invertido**

📖 `to_db_dict:90` → `list(reversed(self.episodes))`. `update_anime_episodes:519-520` → `[::-1]`.
`from_db_dict` **no** deshace la inversión.

✅ **Round-trip verificado — NO conserva el orden:**

| Entrada | RAW en BD | Leído por `from_db_dict` |
|---|---|---|
| `[1,2,…,10]` (ascendente) | `[10,9,…,1]` | `[10,9,…,1]` |
| `[1,2,3,4,5]` vía `update_anime_episodes` | `[5,4,3,2,1]` | `[5,4,3,2,1]` |

⚠️ **Esto interactúa con el proveedor.** ✅ Verificado:

| Proveedor | Orden de `get_anime_info().episodes` | Tras guardar en BD |
|---|---|---|
| **AnimeAV1** | **ascendente** 1…1171 (`animeav1.py:227`) | descendente |
| **AnimeFLV** | **descendente** 1167…1 (`animeflv.py:222-223`) | ascendente |

Es decir: **el orden en BD depende de qué proveedor sirvió el dato**. La inversión solo tiene sentido
histórico para AnimeFLV. Trampa 4.

### `watched_episodes` → JSON de **rangos comprimidos**

📖 `_episodes_to_ranges:210-224` / `_ranges_to_episodes:227-236`.

✅ Round-trip verificado con conjunto discontinuo:

| Conjunto en memoria | RAW en BD | `last_watched_episode` |
|---|---|---|
| `{1, 2, 3, 5, 9}` | `[[1, 3], [5, 5], [9, 9]]` | `9` |
| `set()` | `[]` | `0` |
| (real del usuario, `one-piece-tv`) | `[[1, 1158]]` | `1158` |

**Nunca escribas este campo a mano.** Un elemento con longitud ≠ 2 se descarta en silencio
(`:233-234`), y `last_watched_episode` siempre se recalcula como `max(watched)` (`:409`).

> Este es el campo que `migrate_anime_identity()` **no toca** (§8): es el único dato de la fila que no
> se puede volver a bajar de ningún sitio.

---

## 5. Máquina de estados

📖 `AnimeStatus` (`:21-25`) — el **valor** del enum es el nombre de la columna, y se interpola
directamente en el SQL (`:406`, `:421`).

```mermaid
stateDiagram-v2
    direction LR
    [*] --> SinEstado : no está en BD
    SinEstado --> Watching : update_anime_to_watching (INSERT)
    SinEstado --> Finished : update_anime_to_finished (INSERT)
    SinEstado --> Pending : update_anime_to_pending (INSERT)
    SinEstado --> SoloFav : update_anime_to_favourite (INSERT)

    Watching --> Finished : to_finished
    Watching --> Pending : to_pending
    Watching --> Ninguno : to_not_watching
    Finished --> Watching : to_watching
    Finished --> Pending : to_pending
    Finished --> Pending2 : to_not_finished  ⚠️ pasa a PENDIENTE
    Pending --> Watching : to_watching
    Pending --> Finished : to_finished
    Pending --> Ninguno : to_not_pending

    note right of SoloFav
        FAVOURITE es INDEPENDIENTE:
        se combina con cualquiera
        de los otros tres.
    end note
    note right of Pending2
        update_anime_to_not_finished
        pone is_pending = 1 y RESTAURA
        is_watching al valor previo.
    end note
```

**Invariante**: `is_watching`, `is_finished` e `is_pending` son **mutuamente excluyentes**; activar
uno pone los otros dos a 0 (`_set_status:457-485`). `is_favourite` es ortogonal.

✅ Verificado en la BD real del usuario: **0 filas** con más de uno de los tres activos
(`SELECT COUNT(*) … WHERE (is_watching+is_finished+is_pending) > 1` → `0`).
Reparto real: 13 favoritos, 2 viendo, 13 finalizados, 6 pendientes sobre 24 filas.

Tabla de transiciones completa con líneas → [03 §5](03-flujos-de-ejecucion.md).

---

## 6. Valores de retorno: cuándo `False` significa algo

✅ Verificado. Esto **contradice a `CLAUDE.md`**, que afirma que los updates devuelven `False` si el
anime no está en BD:

| Método | Anime inexistente | Por qué |
|---|---|---|
| `update_watched_episodes` | **`False`** ✅ | comprueba explícitamente (`:404-405`) |
| `update_anime_to_not_watching` | **`False`** ✅ | comprueba (`:546-560`) |
| `update_anime_to_not_finished` | **`False`** ✅ | comprueba (`:566-581`) |
| 🆕 `update_anime_provider_id` | **`False`** ✅ | comprueba (`:433-434`) |
| 🆕 `migrate_anime_identity` | **`False`** ✅ | comprueba, y además rechaza el destino ocupado (`:477-486`) |
| `update_anime_episodes` | **`True`** ⚠️ | `UPDATE` puro; `update_sql` no mira `rowcount` |
| `update_anime_to_not_favourite` | **`True`** ⚠️ | `_update_flag`, `UPDATE` puro |
| `update_anime_to_not_pending` | **`True`** ⚠️ | ídem |

**Regla**: `True` de esta capa significa «el SQL se ejecutó sin excepción», **no** «se modificó una
fila». `SqlUtils.update_sql` (`sqlite.py:32-46`) nunca consulta `cursor.rowcount`.

Los dos métodos nuevos comprueban a mano **precisamente por eso**: los dos existen para reescribir algo
que ya está, así que un `True` que en realidad no ha tocado ninguna fila sería una mentira con
consecuencias (la GUI daría por migrado un anime que sigue igual).

---

## 7. Consultas por género y orden

📖 `get_anime_by_genre_and_order(status, genres, order)` (`:266-302`).

```sql
-- con géneros (:278-284)
SELECT * FROM ANIMES
WHERE ((genres LIKE '%"accion"%' OR genres LIKE '%"aventura"%') AND is_favourite = 1)
-- sin géneros (:286)
SELECT * FROM ANIMES WHERE is_favourite = 1
```

Si hay géneros **y** el orden es `AnimeOrderFilter.POR_DEFECTO`, ordena por número de géneros
coincidentes, descendente (`:294-302`).

> ✅ **Bug verificado**: el único llamante, `AccordionFilterButton.__apply_filters`
> (`utilsButtons.py:341`), pasa `self.selected_order.get()`, que es un **`str`** (`"default"`). La
> comparación `order != AnimeOrderFilter.POR_DEFECTO` (`:294`) es entonces **siempre `True`** → *return*
> en `:295` → **la ordenación por coincidencias nunca se aplica desde la GUI**. Con el enum sí
> funciona. Trampa 6.

⚠️ El `LIKE` no está parametrizado (`:369`): los valores se interpolan en el SQL. Hoy es seguro
porque solo pueden venir de `AnimeGenreFilter`, pero no aceptes ahí texto libre.

---

## 8. La identidad de una fila, y cómo se reescribe 🆕

Desde el 2026-08-16 una fila tiene **identidad compuesta**: el par (`provider_id`, `anime_id`). Hay
tres operaciones que la tocan, y conviene no confundirlas.

| Operación | Método | Qué cambia | Cuándo |
|---|---|---|---|
| **Anotar** | `update_anime_provider_id` (`:419-440`) | solo `provider_id` | La fila estaba a `NULL` y ahora se sabe quién sirve su slug |
| **Migrar** | `migrate_anime_identity` (`:442-516`) | `provider_id` **y** `anime_id`, más los datos descargables | El usuario pulsa «Actualizar a …» en la ficha |
| **Insertar** | `_set_status` → `_insert_anime` (`:614+`) | crea la fila entera | Primer estado que se marca sobre un anime nuevo |

### Autorrelleno: cómo dejaron de existir los `NULL`

No hubo script de migración de datos. El `provider_id` de las filas antiguas se rellena solo, desde
**dos puertas**, y las dos escriben únicamente si la columna está a `NULL`:

| Puerta | Línea | Cuándo dispara |
|---|---|---|
| Abrir la ficha | `anime_window.py:341-345` | Cada vez que se abre un anime guardado |
| Marcar un estado | `animesPersistence.py:643-644` (dentro de `_set_status`) | Al pulsar favoritos/viendo/… sobre una fila que ya existía |

La segunda es redundante con la primera en el flujo normal —para pulsar un estado hay que tener la
ficha abierta—, y está a propósito: hace que el invariante «*una fila que se toca sabe de dónde
viene*» no dependa de por qué puerta se haya entrado. ✅ Verificado que ninguna de las dos pisa un
proveedor ya declarado: cambiarlo es una decisión explícita del usuario, no un efecto de abrir algo.

### `migrate_anime_identity()` — la única reescritura de identidad

```
conserva:      watched_episodes · last_watched_episode · los 4 estados · la PK (id)
sobrescribe:   provider_id · anime_id · title · poster_url · synopsis · genres · episodes
```

Existe porque **un slug no es universal ni eterno**: el mismo anime es `one-piece` en AnimeAV1 y
`one-piece-tv` en AnimeFLV, y hay slugs guardados que su proveedor original ya no sirve. Sin esto la
única salida sería borrar el anime y volver a añadirlo, perdiendo los episodios vistos — que es justo
lo irrecuperable.

Tres detalles que no se ven leyendo la firma:

1. **Se niega a migrar si el `anime_id` destino ya lo ocupa otra fila** (`:478-481`). Como no hay
   `UNIQUE` (§3), el `UPDATE` pasaría sin error y dejaría **dos filas del mismo anime**, cada una con
   sus propios episodios vistos y sin forma de desempatarlas. La GUI comprueba lo mismo antes, para
   poder explicarlo con un diálogo; esta capa lo comprueba igualmente porque no puede fiarse de que
   quien llame lo haya hecho.
2. **Los episodios no se re-invierten** (`:487-488`). `anime_info.episodes` viene de la red → se
   invierte como en cualquier inserción; pero si el destino no trae episodios se conserva
   `record.episodes`, que **ya viene invertido de la BD**. Invertirlo otra vez lo dejaría al revés.
   Trampa 4 otra vez, ahora por el otro lado.
3. **Cada campo cae a lo que había** (`:501-506`): `anime_info.title or record.title`, etc. Una ficha
   destino incompleta degrada la fila lo mínimo, en vez de vaciarle la sinopsis.

✅ Verificado sobre copia de la BD real: migrar conserva los 1158 episodios vistos de One Piece y sus
estados; el destino ocupado devuelve `False` sin tocar nada. ✅ Y **en producción**: la fila
`one-piece-tv` (AnimeFLV) del usuario es hoy `one-piece` (AnimeAV1), con sus episodios intactos.

### `get_all_animes()`

📖 `:319-331`. `SELECT *` sin filtro. Existe para la detección de duplicados por título
(`find_saved_duplicate`, `anime_window.py:69-105`), que necesita ver **también** las filas sin ningún
estado activo: siguen ocupando una fila, y si no se miran se acaba creando un duplicado de algo que ya
está. Es la única consulta de la clase que no filtra por estado ni por id.
