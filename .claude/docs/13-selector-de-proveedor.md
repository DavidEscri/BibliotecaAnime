# 13 — Selector de proveedor y preferencias de usuario (`DB_user.db`)

| | |
|---|---|
| **Fecha** | 2026-07-30 · **Commit base** `c337fb9` · rama `develop` · **sin commitear** |
| **Estado** | ✅ **Implementado** (fases 1-6). Lo escrito antes de implementar se conserva; los resultados están en [§9](#9-verificación) |
| **Cierra** | TODO #4 (borrado de `main_window.py`) y el punto «Selector de proveedor con preferencia persistida» del roadmap ([12 §6](12-deuda-tecnica-y-roadmap.md)) |
| **Mitiga** | **R2** — dependencia de un único proveedor sano ([12 §5](12-deuda-tecnica-y-roadmap.md)) |

Procedencia: ✅ verificado en ejecución · 📖 leído en código · ⚠️ sin verificar.

> **Para futuras sesiones**: este documento es la **fuente de verdad del alcance**. Empieza por
> [§3 Decisiones de diseño](#3-decisiones-de-diseño) para no re-litigar lo ya decidido, por
> [§8](#8-fase-4-diferida-columna-provider_id-en-animes) para lo que quedó fuera a propósito, y por
> [§9](#9-verificación) para saber **qué está verificado y qué no**.
>
> Lo más importante que dejó esta tarea son dos invariantes nuevos:
> **[trampa 21](10-invariantes-y-trampas.md)** (dos identidades del anime en la ficha) y
> **[trampa 22](10-invariantes-y-trampas.md)** (el `wraplength` a mano recorta la sinopsis).

---

## 1. Qué se pide

Petición del usuario, literal en lo esencial:

1. **Desplegable de proveedor** — un selector al estilo del de apariencia (claro/oscuro/sistema) para
   elegir qué proveedor de anime se usa.
2. **Predeterminado persistido entre arranques** — y para eso, **una base de datos nueva llamada
   `DB_user.db`** donde guardar preferencias y configuraciones del usuario. Hoy la única preferencia
   prevista es el proveedor predeterminado.
3. **Cambio de proveedor por anime, incluso dentro del propio viewer** — «por si se quieren usar sus
   servidores o catálogo».

Requisito heredado del TODO #4: debe quedar **preparado para mangas**, de forma que cuando se
integren, el desplegable ofrezca proveedores de manga si lo que se está viendo son mangas.

---

## 2. El problema de fondo: la identidad de un anime es específica del proveedor

📖 Esto es lo que convierte «un desplegable» en una tarea con alcance real. Cadena de hechos:

| Hecho | Dónde |
|---|---|
| `AnimeInfo.id` es el **slug del sitio**, no un identificador universal | `models.py:88`, `animeav1.py:177`, `animeflv.py:179` |
| La tabla `ANIMES` está **cauterizada a ese slug**: `anime_id` es la clave con la que se busca todo | `animesPersistence.py:276-285` |
| `EpisodeInfo.anime` también es el slug, y es lo que se pasa a `get_anime_episode_servers` | `models.py:83`, `anime_window.py:490` |
| Los pósters en disco se llaman `{anime_id}.jpg` | `utils.py:57,84,134,173` |

Consecuencia: **el mismo anime tiene un `id` distinto en cada proveedor.** AnimeAV1 sirve
`one-piece-gyojin-touhen`; AnimeFLV serviría `one-piece`. Por tanto:

- **Cambiar el proveedor predeterminado no basta con llamar a `set_default()`.** Todos los animes ya
  guardados llevan el slug del proveedor que los sirvió. Al pinchar uno, las vistas de estado hacen
  `get_anime_info(anime_record.anime_id)` (📖 los 6 puntos de clic de [§5](#5-cambios-por-fichero)), que
  con el proveedor nuevo **no resolvería**.
  → **Lo salva el fallback**: `call_with_fallback` reintenta con el resto de proveedores registrados,
  así que el clic sigue funcionando a costa de una petición HTTP fallida (~1-3 s ⚠️). Por eso
  [D3](#d3) mantiene el fallback **activo** para la preferencia global.
- **Cambiar de proveedor dentro de la ficha no puede reutilizar el `id`.** Hay que **re-resolver** el
  anime en el proveedor destino ([D6](#d6)).
- **Si tras cambiar de proveedor se pulsa «añadir a favoritos», se insertaría una fila nueva** con el
  slug del proveedor nuevo → el mismo anime duplicado en la biblioteca, con pósters duplicados en
  disco. Es el riesgo más serio de la tarea y lo neutraliza [D5](#d5).

---

## 3. Decisiones de diseño

Cada decisión lleva la alternativa descartada, para no reabrir el debate en la siguiente sesión.

### D1 — BD separada `DB_user.db`, no una tabla nueva en `DB_Animes.db`

**Decidido**: `resources/DB/DB_user.db`, con su propia clase `UserPersistence(ServiceDB)` y su propio
`SCHEMA`.

*Alternativa descartada*: añadir `USER_SETTINGS` a `AnimesPersistence.SCHEMA` (que es lo que insinuaba
el TODO #4 original, «una tabla nueva»). Se descarta porque:

- **Aísla la configuración de la biblioteca.** `DB_Animes.db` son 25 animes reales e irrecuperables;
  la configuración es desechable. Mezclarlas hace que cada migración de configuración dispare una
  copia de seguridad de la biblioteca entera.
- Es lo que pide el usuario explícitamente.
- El motor de migración de `utils/db/sqlite.py` es **genérico**: `ServiceDB.validate_schema()` no sabe
  nada de animes. Una segunda BD no cuesta infraestructura nueva ([04 §3](04-modelo-de-datos.md)).
- `resources/DB/backups/` es compartido, pero el nombre del fichero de copia lleva el *stem* de la BD
  (`sqlite.py:401-403`), así que `DB_user_<ts>.db` y `DB_Animes_<ts>.db` no colisionan. 📖

⚠️ **Efecto colateral en el empaquetado**: `MiBibliotecaAnime.spec:12` mete `resources/DB` en `datas`,
así que el `.exe` distribuiría **también** el `DB_user.db` del desarrollador. Es el mismo defecto ya
registrado como **A3/C11** ([12 §4](12-deuda-tecnica-y-roadmap.md)), ahora con un fichero más. No se
arregla aquí, pero súmalo a la lista cuando se toque el `.spec`.

### D2 — Tabla clave/valor genérica, no una columna por preferencia

**Decidido**: una sola tabla `USER_SETTINGS` de tres columnas, con las claves declaradas en un enum
`UserSettingKey`. Esquema completo en [§4](#4-esquema-de-db_userdb).

*Alternativa descartada*: una tabla `USER_CONFIG` de una única fila con una columna por preferencia
(al estilo de `AnimeField`). Se descarta porque cada preferencia nueva sería una migración de esquema,
mientras que con clave/valor es **una fila nueva y cero migraciones**. La configuración es justo el
caso donde el esquema rígido no aporta nada.

*Coste asumido*: se pierde el tipado en BD — todo es `TEXT` y quien lee convierte. Se compensa con el
enum `UserSettingKey` (las claves no son *strings* sueltos) y con métodos con nombre
(`get_default_provider_id()`), no `get_setting("...")` disperso por la GUI.

### D3 — La preferencia global fija el predeterminado del manager, **con fallback activo**

**Decidido**: elegir proveedor en la sidebar equivale a
`AnimeProviderManager.set_default(provider_id)` + persistir la preferencia. **No** se activa
`strict=True` de forma global.

*Por qué*: por lo explicado en [§2](#2-el-problema-de-fondo-la-identidad-de-un-anime-es-específica-del-proveedor)
— sin fallback, elegir un proveedor distinto al que sirvió cada anime guardado **rompería el clic** en
las 4 vistas de estado. Con fallback, degrada a una petición perdida.

*Consecuencia honesta que hay que documentar en la UI*: si el usuario elige AnimeFLV (hoy caído para
servidores, [05 §2](05-proveedores-y-scraping.md)) puede acabar viendo datos de AnimeAV1 sin saberlo.
Lo compensa [D4](#d4): el selector **de la ficha** muestra qué proveedor sirvió realmente ese anime.

### D4 — El selector de la ficha es `strict=True` y de ámbito local

**Decidido**: el desplegable de `AnimeWindowViewer` usa `strict=True` en todas sus llamadas, **no**
toca el predeterminado global y **no** se persiste. Al abrir otra ficha se vuelve a partir del
predeterminado.

*Por qué `strict`*: si el usuario pide explícitamente «los servidores de X» y el fallback le sirve los
de Y, el selector **miente**. Aquí el silencio del fallback es un defecto, no una virtud.

*Por qué no persistir*: es una acción exploratoria («a ver si este otro sitio tiene servidores que
funcionen»), no una preferencia. Persistirla convertiría un clic de curiosidad en un cambio de
configuración global.

### D5 — Identidad de **visualización** vs. identidad de **persistencia**

**La decisión central de la tarea.** `AnimeWindowViewer` pasa a distinguir dos identidades:

| | Qué es | De dónde sale | Para qué se usa |
|---|---|---|---|
| **Visualización** | `self.anime_info` | El proveedor **actualmente seleccionado** en la ficha | Título, sinopsis, géneros, lista de episodios, servidores |
| **Persistencia** | `self.persistence_anime_id` + `self.persistence_poster_url` | El `AnimeInfo` con el que se **abrió** la ficha, y nunca cambia | **Todas** las operaciones de BD y **todos** los ficheros de póster |

Al cambiar de proveedor se sustituye la primera y **se congela la segunda**. Así:

- No se duplican filas en `ANIMES` ni pósters en disco.
- Los episodios vistos y los 4 estados siguen apuntando a la misma fila.
- El póster cacheado se sigue encontrando (`get_anime_image` busca `{id}.jpg`, `utils.py:173`).

*Implicación práctica*: la fila de BD queda con el slug del proveedor que **descubrió** el anime.
Es una elección arbitraria pero estable y sin pérdida de datos.

*Alternativa descartada*: añadir una columna `provider_id` a `ANIMES` y re-clavar la identidad al
proveedor activo. Es la solución «correcta» a largo plazo pero implica **migrar la BD real del
usuario** y decidir qué hacer con las 25 filas existentes (`provider_id` a `NULL`). Se aparta a
[§8 Fase 4 diferida](#8-fase-4-diferida-columna-provider_id-en-animes).

⚠️ **Supuesto que asume D5**: los **números** de episodio coinciden entre proveedores (episodio 5 es
el episodio 5 en los dos sitios), así que los `watched_episodes` guardados siguen siendo válidos tras
cambiar de proveedor. Es cierto para series normales; **no** necesariamente para animes partidos en
temporadas con numeración distinta por sitio. Sin verificar.

### D6 — Resolución *cross-provider* por búsqueda de título + similitud

**Decidido**: método nuevo `AnimeProviderManager.resolve_anime_in_provider(anime_info, provider_id)`.
Algoritmo:

1. `search_animes_by_query(anime_info.title, provider_id=..., strict=True)`.
2. Normalizar títulos: minúsculas, sin tildes, sin caracteres no alfanuméricos.
3. Coincidencia normalizada **exacta** → gana. Si no, mejor `difflib.SequenceMatcher.ratio()` con
   **umbral 0.75**; por debajo se considera «no encontrado».
4. `get_anime_info(match.id, provider_id=..., strict=True)` para traer la ficha completa.
5. Devuelve `AnimeInfo` o `None`. Nunca lanza.

*Por qué en el manager y no en la GUI*: es lógica de identidad entre proveedores, capa `APIs/`. La GUI
no debe saber que los slugs difieren ([01 §dependencias](01-arquitectura.md)).

*Coste*: **2 peticiones HTTP** por cambio de proveedor → obligatoriamente en hilo daemon con cursor
`watch` ([07](07-concurrencia-e-hilos.md)).

⚠️ El umbral 0.75 es una estimación sin calibrar. Hay que probarlo con títulos reales antes de darlo
por bueno (ver [§9](#9-verificación)).

### D7 — La preferencia se lee de forma **síncrona** en `MainWindow.__init__`

**Decidido**: `UserPersistence.start()` + lectura de la preferencia ocurren en `__init__`, **antes** de
`load_sidebar_buttons()`.

*Por qué*: el desplegable tiene que nacer ya mostrando el valor guardado, y el predeterminado tiene
que estar aplicado antes del `get_recent_animes()` del hilo de carga (`main_window.py:209`). Meterlo en
`load_animes()` (que corre en el hilo daemon) llegaría tarde para el widget.

*Coste*: abre y cierra una conexión SQLite local en el arranque del hilo de UI. Son milisegundos y
**no es red** — no viola la regla de «nada de HTTP en el hilo de Tk».

### D8 — Al cambiar el predeterminado se recarga la lista de recientes

**Decidido**: cambiar el proveedor en la sidebar relanza `get_recent_animes()` +
`download_animes_poster()` en un hilo daemon y repinta la vista de recientes si está activa.

*Por qué*: sin esto el selector **parece no hacer nada** — la portada seguiría mostrando el catálogo
del proveedor anterior hasta reiniciar. Se usa `download_animes_poster` (`utils.py:71`), la variante
sin barra de progreso, que ya existe y además limpia del disco los pósters que dejan de estar en la
lista.

*Guarda necesaria*: un flag para que dos cambios rápidos de proveedor no lancen dos hilos que se
pisen al escribir `self.recent_animes`.

---

## 4. Esquema de `DB_user.db`

Módulo nuevo: **`src/dataPersistence/userPersistence.py`**. Espeja la estructura de
`animesPersistence.py` (enum de campos → `TableSchema` → `ServiceDB`), así que se lee igual.

### Tabla `USER_SETTINGS`

| # | Columna | Tipo SQLite | Contenido |
|---|---|---|---|
| 1 | `setting_key` | `VARCHAR(100)` | Clave, valor de `UserSettingKey`. **PRIMARY KEY** |
| 2 | `setting_value` | `TEXT` | Valor serializado como texto |
| 3 | `updated_at` | `VARCHAR(30)` | ISO-8601 de la última escritura, para depurar |

> Se evita a propósito llamar a las columnas `key` y `value`: no son palabras reservadas en SQLite,
> pero `VALUES` sí lo es y la confusión no aporta nada.

### Claves previstas

| Clave | Valor | Estado |
|---|---|---|
| `default_anime_provider` | `PROVIDER_ID` (`"animeav1"`, `"animeflv"`, …) | **Se implementa ahora** |
| `default_manga_provider` | `PROVIDER_ID` del proveedor de manga | 🔮 Reservada, ver [§10](#10-preparación-para-la-convivencia-animemanga) |

### API pública de `UserPersistence`

```
start()                                   # crea la BD si no existe + validate_db_integrity()
validate_db_integrity()                   # delega en ServiceDB.validate_schema(SCHEMA)
get_setting(key, default=None) -> str|None
set_setting(key, value) -> bool           # UPSERT (INSERT … ON CONFLICT DO UPDATE)
get_all_settings() -> Dict[str, str]
get_default_provider_id() -> str|None     # atajo tipado sobre get_setting
set_default_provider_id(provider_id)      # atajo tipado sobre set_setting
```

Más `UserPersistenceSingleton`, con el mismo patrón que el resto: `__new__` devuelve la **instancia
real**, no la envoltura ([08 §2](08-convenciones-y-estilo.md)).

**Invariante que hereda gratis**: el orden de `FIELDS` debe coincidir con el orden físico de las
columnas, porque `SqlUtils.query_sql` empareja **por posición** (trampa 1 de
[10](10-invariantes-y-trampas.md)). `validate_db_integrity()` lo garantiza en cada arranque.

**Tolerancia a fallos**: si `DB_user.db` no se puede abrir o crear, la app **debe arrancar igual** con
el predeterminado de código (AnimeAV1). Una preferencia perdida no puede impedir usar la biblioteca.

---

## 5. Cambios por fichero

| Fichero | Cambio | Fase |
|---|---|---|
| **`dataPersistence/userPersistence.py`** | 🆕 Módulo completo: `UserSettingField`, `UserSettingKey`, `UserSetting`, `UserPersistence`, `UserPersistenceSingleton` | 1 |
| **`APIs/common/animeProviderMgr.py`** | `get_provider_name()`, `get_provider_names()` (`{id: PROVIDER_NAME}` para poblar los desplegables), `get_anime_info_with_provider()` (expone el `provider_id` que `call_with_fallback` ya devuelve y los wrappers tiraban), `resolve_anime_in_provider()` ([D6](#d6)). Corregir de paso el docstring **D2** de [12 §3](12-deuda-tecnica-y-roadmap.md) (el ejemplo pone AnimeFLV por defecto; el código real usa AnimeAV1) | 1-2 |
| **`gui/main_window.py`** | `UserPersistence` en `__init__` + aplicar preferencia ([D7](#d7)); desplegable en `load_sidebar_buttons()`; `change_anime_provider_event()`; recarga de recientes ([D8](#d8)); **borrar los TODO de `:31-34`** | 3 |
| **`gui/anime_window.py`** | `__init__(…, provider_id=None)`; identidad doble ([D5](#d5)); desplegable en la ficha; `provider_id=…, strict=True` en `get_anime_episode_servers` (`:490`) — **hoy usa el predeterminado global, que es un bug latente en cuanto exista el selector**; todas las llamadas a BD y a los helpers de póster pasan a la identidad de persistencia | 4 |
| **`gui/sidebarButtons/recentAnimes/recentAnimes.py`** | `:91` → `get_anime_info_with_provider`, propagar `provider_id` al viewer | 5 |
| **`gui/sidebarButtons/favouriteAnimes/favouriteAnimes.py`** | `:131` ídem | 5 |
| **`gui/sidebarButtons/finishedAnimes/finishedAnimes.py`** | `:131` ídem | 5 |
| **`gui/sidebarButtons/watchingAnimes/watchingAnimes.py`** | `:133` ídem | 5 |
| **`gui/sidebarButtons/pendingAnimes/pendingAnimes.py`** | `:133` ídem | 5 |
| **`gui/sidebarButtons/searchAnimes/searchAnimes.py`** | `:341` ídem | 5 |

**Las 4 vistas de estado son idénticas línea por línea en este punto** (`favourite`, `finished`,
`watching`, `pending`): el cambio de `:131`/`:133` es el mismo texto en las cuatro. No arregles una
sola.

**Qué NO se toca**: `models.py`, `animesPersistence.py`, `utils/db/sqlite.py`, `animeav1.py`,
`animeflv.py`, `utilsButtons.py`. La tarea **no altera `DB_Animes.db`**.

---

## 6. Ubicación de los dos desplegables

**Sidebar** (`main_window.py`) — encima del selector de apariencia, mismo estilo `CTkOptionMenu`:

```
┌─ sidebar ──────────────┐
│ Biblioteca de Anime    │
│ [6 botones de vista]   │
│ …                      │
│ Proveedor de anime:    │  ← label nuevo
│ [ AnimeAV1        ▾ ]  │  ← CTkOptionMenu nuevo, poblado con PROVIDER_NAME
│                        │
│ [ System          ▾ ]  │  ← el de apariencia, ya existente
└────────────────────────┘
```

**Ficha de detalle** (`anime_window.py`) — arriba a la derecha, sobre la fila de botones de estado,
usando las columnas 2-3 del `content_frame` que ya están configuradas y hoy están vacías
(`anime_window.py:103-104`):

```
┌─ content_frame ─────────────────────────────────────────────┐
│ ┌────────┐  Título del anime            Proveedor:          │
│ │ póster │  Sinopsis…                   [ AnimeAV1     ▾ ]  │
│ │        │  Géneros: …                                      │
│ └────────┘                                                  │
│ [Favoritos] [Finalizados] [Viendo] [Pendiente]              │
│ Lista de episodios …                                        │
└─────────────────────────────────────────────────────────────┘
```

El valor mostrado es **el proveedor que sirvió realmente esta ficha**, no el predeterminado — es lo
que hace visible el fallback silencioso de [D3](#d3).

---

## 7. Fases de entrega

Cada fase deja la app **arrancable**. Si retomas la tarea, mira aquí dónde estás.

| Fase | Qué entra | Estado |
|---|---|---|
| **1** | `userPersistence.py` + `DB_user.db` | ✅ 23/23 comprobaciones |
| **2** | Métodos nuevos del manager (`get_provider_names`, `get_provider_id_by_name`, `get_anime_info_with_provider`, `normalize_title`, `resolve_anime_in_provider`) | ✅ 26/26 |
| **3** | Desplegable de la sidebar + persistencia + recarga de recientes ([D7](#d7), [D8](#d8)) | ✅ verificado con la app real |
| **4** | Desplegable de la ficha + identidad doble ([D5](#d5)) + `strict` en servidores | ✅ 25/25 sobre copia de la BD real |
| **5** | Propagar `provider_id` en los 6 puntos de clic | ✅ escrito; ⚠️ no probado clic a clic |
| **6** | Actualizar [02](02-mapa-de-modulos.md), [04](04-modelo-de-datos.md), [05](05-proveedores-y-scraping.md), [06](06-gui-y-vistas.md), [09](09-verificacion-y-pruebas.md), [10](10-invariantes-y-trampas.md), [11](11-playbooks.md), [12](12-deuda-tecnica-y-roadmap.md) | ✅ hecho |

### Lo que se hizo distinto de lo planeado

| Planeado | Lo que se hizo | Por qué |
|---|---|---|
| Selector de la ficha en `row=0, column=2, columnspan=2` (mock de [§6](#6-ubicación-de-los-dos-desplegables)) | `row=0, column=1, columnspan=3, sticky=E`, en **su propia fila**; título, sinopsis, géneros, estados y episodios bajan una fila (0-2/3/4 → 1-3/4/5) | Reservar ancho en las columnas 2-3 **recortaba la sinopsis**: su `wraplength` va calculado a mano sobre el ancho del `content_frame`, no de la celda. Detectado por captura, no a ojo → **[trampa 22](10-invariantes-y-trampas.md)** |
| — | `main_window` lleva un **contador de generación** de la lista de recientes | Sin él, la precarga en segundo plano de un proveedor seguía escribiendo por índice en la lista del proveedor nuevo. Carrera preexistente que el selector habría hecho fácil de disparar |
| — | Etiqueta «Apariencia:» en el selector de tema, que estaba vacía | Con una etiqueta «Proveedor de anime:» justo encima, un desplegable sin etiquetar parecía roto |
| — | `__toggle_servers_frame` avisa si el proveedor no da servidores | Efecto de `strict=True`: antes el fallback tapaba el caso y se pintaba un selector de servidores vacío |
| — | Erratas de cabecera corregidas: `animeProvider.py` → `animeProviderMgr.py`, `anime_wnidow.py` → `anime_window.py` | Parte de C1 en [12 §4](12-deuda-tecnica-y-roadmap.md); ya se estaba tocando la cabecera para subir la versión |

---

## 8. Fase 4 diferida: columna `provider_id` en `ANIMES`

**No entra en esta iteración.** Queda escrito aquí para que la siguiente sesión no lo redescubra.

*Qué resolvería*: que cada fila de `ANIMES` recuerde de qué proveedor es su `anime_id`, para que el
clic en una vista de estado use directamente el proveedor correcto (`provider_id=record.provider_id`)
en vez de depender del fallback ([§2](#2-el-problema-de-fondo-la-identidad-de-un-anime-es-específica-del-proveedor)).

*Qué costaría*:

- Un miembro nuevo **al final** de `AnimeField` → `validate_db_integrity()` lo resuelve con
  `ALTER TABLE ADD COLUMN`, sin mover datos ([11 §2](11-playbooks.md)).
- `AnimeRecord.to_db_dict()` / `from_db_dict()` / `from_anime_info()` **a mano** — la migración de
  esquema es automática, la del dataclass no.
- Decidir qué hacer con las **25 filas existentes**: se propone dejarlas a `NULL` y tratar `NULL` como
  «desconocido → usar el predeterminado con fallback», que es exactamente el comportamiento de hoy.
  Cero escrituras de datos, cero riesgo.
- Probar **sobre una copia** de `DB_Animes.db` ([09 §3b](09-verificacion-y-pruebas.md)).

*Por qué se difiere*: es la única parte que toca la BD real del usuario, y el fallback ya cubre el
caso funcionalmente. Separarla mantiene esta iteración en «solo crea una BD nueva».

---

## 9. Verificación

**No hay tests en el proyecto.** Lo que se ejecuta, se ejecuta a mano ([09](09-verificacion-y-pruebas.md)).
El checklist manual quedó incorporado a [09 §7](09-verificacion-y-pruebas.md); aquí queda **qué se
ejecutó de verdad el 2026-07-30 y qué no**.

### ✅ Verificado

| Qué | Cómo | Resultado |
|---|---|---|
| `UserPersistence` completo | Script en scratchpad con `get_resource_path` parcheado a un sandbox | **23/23**: creación, esquema y orden físico de columnas, upsert (4 escrituras → 1 fila), persistencia entre instancias, idempotencia de `validate_db_integrity()` (no crea copia si no hay nada que migrar), y degradación con ruta imposible |
| Emparejamiento de títulos y registro | Script con un **proveedor falso** (catálogo fijo, cero red) | **26/26**: `normalize_title` (tildes, guiones, signos), `get_provider_names`/`_by_name`, `get_anime_info_with_provider` devuelve `(ficha, id)` y `(None, None)`, resolución exacta, y los 3 casos negativos (proveedor desconocido, título vacío, título sin relación → 0.35 rechazado) |
| Umbral de similitud | Título con una letra menos | 0.968 → aceptado con 0.75, rechazado con 0.99 |
| Resolución contra el sitio real | AnimeAV1, 3 peticiones en serie con pausas | `Kimetsu no Yaiba Movie 1: Mugenjou-hen - Akaza Sairai` resuelve al mismo slug, similitud **1.00**, con episodios |
| 🔴 **[D5](#d5) — no duplicar filas** | Script sobre una **copia** de `DB_Animes.db` (25 filas), con los helpers de póster espiados (cero red, cero escritura de imágenes) | **25/25**: tras cambiar de proveedor y pulsar los **8** botones de estado, **25 filas antes y 25 después**, ninguna con el slug del otro proveedor, la fila original correctamente marcada/desmarcada, y los episodios vistos bajo la identidad de persistencia |
| Arranque real de la app | `python src/app.py`, log capturado | Sin excepciones. `DB_user.db` creada con las 3 columnas y `setting_key` como PK. `DB_Animes.db`: «esquema correcto, no hay nada que migrar» → **ni migración ni copia de seguridad** |
| Preferencia entre arranques | Guardar `animeflv`, relanzar la app, leer el log | «Proveedor predeterminado del usuario: animeflv». Estado restaurado a prístino después |
| Layout de la sidebar | Captura de la ventana | «Proveedor de anime: AnimeAV1» sobre «Apariencia: System», sin solaparse con el espaciador de la fila 8 |
| Layout de la ficha | Captura, **con y sin** el selector (control) | Detectó y confirmó la corrección de la [trampa 22](10-invariantes-y-trampas.md): con la colocación inicial la sinopsis se recortaba; con la definitiva es idéntica al control |

### ⚠️ NO verificado — lo que falta por probar a mano

1. **Resolución *cross-provider* real entre dos proveedores distintos.** AnimeFLV está en desuso, así
   que no hay un segundo proveedor sano. Se ha probado con un proveedor falso y resolviendo *en el
   mismo* proveedor, que recorre el mismo código, pero **el umbral 0.75 no está calibrado con datos
   reales de dos sitios**. Recalíbralo al integrar el tercer proveedor.
2. **Interacción de ratón con los dos desplegables.** No se pudo automatizar el clic; el widget se ha
   verificado por captura, no pulsándolo.
3. **Cambiar de proveedor con la red caída** (mensaje de aviso + el desplegable vuelve atrás). El
   camino está probado en el script (`__on_provider_resolved(provider_id, None)` no toca nada) pero no
   con la red real caída.
4. **Abrir una ficha desde cada una de las 6 vistas.** El cambio es el mismo texto en las 6 y compila,
   pero solo se ha ejercitado la de recientes.
5. **Servidores de vídeo tras cambiar de proveedor.** Requiere dos proveedores sanos; ver el punto 1.

---

## 10. Preparación para la convivencia anime/manga

Lo que esta tarea deja listo (y lo que no) para el punto grande del roadmap:

| Preparado | Cómo |
|---|---|
| Preferencia por tipo de medio | La clave es `default_anime_provider`, no `default_provider`. `default_manga_provider` es una fila más, **sin migración** |
| Cualquier preferencia futura | Clave/valor genérico ([D2](#d2)): el desplegable global anime/manga/ambos de la esquina inferior izquierda ya tiene dónde guardarse |
| Poblar el desplegable | `get_provider_names()` es la única fuente del contenido del widget; cuando existan proveedores de manga se filtra por tipo de medio ahí, no en la GUI |

**Lo que NO resuelve**: `AnimeProviderManager` registra proveedores en un único diccionario plano, sin
noción de tipo de medio. Cuando entren los de manga habrá que decidir si se generaliza a
`MediaProvider` o se registran en manager aparte — decisión abierta en
[12 §6](12-deuda-tecnica-y-roadmap.md), y esta tarea **no la prejuzga**.

---

## 11. Riesgos de esta tarea

| # | Riesgo | Mitigación |
|---|---|---|
| 1 | **Duplicar animes en `ANIMES`** al cambiar de proveedor con la ficha abierta | [D5](#d5) + la prueba 6 y 9 de [§9](#9-verificación). Es el fallo que más daño haría: escribe en la biblioteca real |
| 2 | Resolución *cross-provider* con **falso positivo** (te abre otro anime parecido) | Umbral de similitud + coincidencia exacta preferente; hay que calibrar con títulos reales |
| 3 | Reconstruir la ficha desde un hilo daemon agrava **A6/R3** (widgets Tk fuera del hilo de UI) | El código nuevo marshalliza con `main_window.after(0, …)` en vez de tocar widgets desde el hilo. No se propaga el patrón heredado ([07](07-concurrencia-e-hilos.md)) |
| 4 | El usuario elige un proveedor caído y la app parece rota | Fallback activo en el ámbito global ([D3](#d3)) + el selector de la ficha muestra quién sirvió de verdad |
| 5 | `DB_user.db` corrupta impide arrancar | La preferencia es opcional por diseño: sin ella se usa el predeterminado de código |
