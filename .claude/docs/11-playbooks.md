# 11 — Playbooks

| | |
|---|---|
| **Fecha** | 2026-08-16 · **Commit** `54fb3d6` · árbol **sucio** (columna `provider_id`, 16 ficheros) |
| **Última revisión** | 2026-08-16: §2 reescrito con el **caso real ya ejecutado** (`provider_id` en medio del enum, con reconstrucción de tabla) y §3 con el paso 0 nuevo — añadir un proveedor empieza por `AnimeProviderId` |
| **Cubre** | recetas operativas sobre los 19 módulos de `src/` + `MiBibliotecaAnime.spec` |

Procedencia: ✅ verificado en ejecución · 📖 leído en código · ⚠️ sin verificar.

> Cada receta lista **los ficheros exactos** a tocar y termina con un **checklist de verificación**.
> Antes de empezar cualquiera, lee [10-invariantes-y-trampas.md](10-invariantes-y-trampas.md).

---

## §1 — Añadir una vista de sidebar

**Ficheros a tocar**

| Fichero | Acción |
|---|---|
| `src/gui/sidebarButtons/<vista>/__init__.py` | crear **vacío** |
| `src/gui/sidebarButtons/<vista>/<vista>.py` | crear (plantilla en [08 §7.2](08-convenciones-y-estilo.md)) |
| `resources/images/utils/<icono>.png` | añadir el icono |
| `src/gui/main_window.py` | importar (`:20-25`) e instanciar (`:159-164`) |
| `MiBibliotecaAnime.spec` | añadir a `hiddenimports` (`:21-36`) |

**Pasos**

1. Copia la plantilla de [08 §7.2](08-convenciones-y-estilo.md). El módulo **debe** llevar la cabecera
   `__author__/__subsystem__/__module__/__version__/__info__` con `__subsystem__ = "sidebarButtons"`.
2. Hereda de `utilsButtons.SidebarButton`; implementa **`show_frame()`** (punto de entrada
   programático) y `show_<vista>()` (el `command`).
3. Respeta el reparto de filas de `content_frame` ([06 §4](06-gui-y-vistas.md)): la rejilla de
   resultados va en `row=5`.
4. Registra en `main_window.py:159-164` con `sidebar_button_row + 7`:

   ```python
   self.__mi_vista_button: MiVistaButton = MiVistaButton(self, icon_path,
                                                         sidebar_button_row + 7,
                                                         sidebar_button_column)
   ```

5. ⚠️ **Desplaza los controles del fondo de la sidebar.** Reparto real hoy (con
   `sidebar_button_row = 1`), corregido el 2026-08-06:

   | Fila | Contenido |
   |---|---|
   | `+7` (**8**) | ⚠️ **espaciador con `weight=1`** — no metas nada aquí |
   | `+8` (9) | etiqueta «Proveedor de anime:» |
   | `+9` (10) | frame con el desplegable de proveedor **y su pin** |
   | `+10` (11) | etiqueta «Apariencia:» |
   | `+11` (12) | desplegable de tema |

   Una séptima vista va en `+7`… que es justo el espaciador: hay que mover **las cinco filas** de
   abajo una posición y reconfigurar el `grid_rowconfigure(8, weight=1)` de `create_sidebar_frame()`
   a la fila nueva. No basta con tocar el selector de apariencia.
6. Si la vista muestra pósters propios, decide su carpeta en `resources/images/<categoría>/` y
   **añádela a `get_anime_image` (`utils.py:185-196`)** o el póster se bajará de la red cada vez
   (trampa 15). Esa lista tiene hoy las 6 categorías existentes; se olvidó `watching` durante meses,
   así que es un paso fácil de saltarse. Si además creas un `AnimeStatus` nuevo, la carpeta sale de
   `status.name.lower()` (`utils.py:53-60`, y ahora también `move_anime_poster_by_status:62-79`) y el olvido es aún más silencioso.

**Checklist**

- [ ] El botón aparece en la sidebar, con icono y texto.
- [ ] El selector de apariencia sigue visible y no se solapa.
- [ ] `show_frame()` funciona llamado a mano desde `MainWindow`.
- [ ] La rejilla recalcula columnas al redimensionar y volver a entrar.
- [ ] Cambiar a otra vista y volver **no** deja widgets huérfanos.
- [ ] La carpeta de pósters está en `.gitignore` si se genera en runtime.
- [ ] `hiddenimports` actualizado.

---

## §2 — Añadir una columna a la BD

> ✅ **Ya no hay que escribir la migración a mano** (desde 2026-07-30). `validate_db_integrity()` la
> deduce del esquema declarado. Lee la trampa 2 para saber qué sigue siendo tu responsabilidad.

> ✅ **Ejecutado de verdad el 2026-08-16** con `provider_id`, y por el camino caro: **en la posición 2**,
> no al final. Lo que sigue ya no es teoría.

**Ficheros a tocar**

| Fichero | Acción |
|---|---|
| `src/dataPersistence/animesPersistence.py` | miembro nuevo en `AnimeField` + campo en `AnimeRecord` + `to_db_dict` + `from_db_dict` |
| `.claude/docs/04-modelo-de-datos.md` | actualizar la tabla de esquema |

**Pasos**

1. **Añade el miembro a `AnimeField`** (`:28-57`). Al final es más barato: la migración usa
   `ALTER TABLE ADD COLUMN` sin mover datos. En medio **también funciona** —reconstruye la tabla en una
   transacción, copiando por nombre de columna— y a veces es lo correcto: `provider_id` fue en segunda
   posición porque forma parte de la identidad de la fila, y el coste lo paga el motor una sola vez.

   ```python
   USER_RATING = ("user_rating", "INTEGER")
   ```

   `SCHEMA` se deriva de `AnimeField`, así que no hay que tocarla.

2. Añade el campo a `AnimeRecord` (`:63-83`), **con valor por defecto** y **después** de los que ya
   tienen default (regla de las dataclasses). ⚠️ Aquí el orden **no** tiene que coincidir con el del
   enum: `provider_id` está el penúltimo en la dataclass y el segundo en el enum, y es correcto. Lo que
   importa posicionalmente es `FIELDS`, no los atributos de Python. Ojo: `id` es el último campo
   hoy (`:83`).
3. Añádelo a `to_db_dict()` (`:88-110`) en la **misma posición** que en el enum. Esta sí es
   posicional (trampa 1).
4. Añádelo a `from_db_dict()` (`:112-150`) con un default tolerante — los registros que ya existían
   recibirán `NULL`: `data.get(AnimeField.USER_RATING.column, 0) or 0`.

   💡 Si el campo es un **enum**, no lo conviertas ahí: hazle un helper que degrade a `None` ante un
   valor desconocido, como `_provider_id_from_db` (`:153-171`). Un valor huérfano en una fila no puede
   impedir leer la biblioteca entera.
5. **Opcional**: si quieres que los registros existentes reciban un valor concreto en vez de `NULL`,
   declara el default en el `TableSchema` de `SCHEMA` (`:250-256`). El valor es una **expresión SQL
   literal**, así que las cadenas van entrecomilladas:

   ```python
   TableSchema(
       name        = TABLE_NAME,
       fields      = [(f.column, f.sql_type) for f in AnimeField],
       primary_key = PRIMARY_KEY,
       defaults    = {"user_rating": 0, "media_type": "'anime'"},
   )
   ```

6. Arranca la app una vez (`python src/app.py`). La migración se aplica en `start()` y deja la copia de
   seguridad en `resources/DB/backups/`.

**Checklist**

- [ ] `PRAGMA table_info(ANIMES)` devuelve las columnas **en el mismo orden** que
      `AnimesPersistence.FIELDS`.
- [ ] La consola muestra la línea `Migración: …` en el primer arranque y **nada** en el segundo
      (idempotencia).
- [ ] Existe la copia en `resources/DB/backups/`.
- [ ] Probado sobre una **copia de la BD real con datos** (no solo una BD vacía) —
      `scratchpad/test_migraciones.py` de la sesión del 2026-07-30 es la plantilla.
- [ ] **Recuento de filas antes = después**, y las columnas que no tocas **idénticas fila a fila**.
      Es lo único que distingue «se ha migrado» de «se ha migrado sin perder nada»; con una columna
      en medio, la tabla se reescribe entera. ✅ Así se validó `provider_id`: 25 filas antes y
      después, 12 columnas intactas ([04 §3](04-modelo-de-datos.md)).
- [ ] Si el campo se rellena solo a posteriori (como `provider_id`), **decidido y documentado quién
      lo rellena y cuándo**, y comprobado que **no pisa** un valor ya escrito.

---

## §2b — Añadir una tabla nueva

1. Declara su `TableSchema` y añádelo a `AnimesPersistence.SCHEMA` (`:250-256`):

   ```python
   TableSchema(
       name        = "CONFIG",
       fields      = [("key", "VARCHAR(50)"), ("value", "VARCHAR(200)")],
       primary_key = "key",
   )
   ```

2. Añade los métodos de acceso en `AnimesPersistence`. **No reutilices `self.FIELDS`**: es la lista de
   columnas de `ANIMES`. Pasa a `query_sql` la lista de columnas de *esa* tabla — el emparejamiento es
   posicional (trampa 1).
3. Arranca la app: `validate_db_integrity()` crea la tabla, también en BDs que ya tenían datos.

✅ Verificado con una tabla `CONFIG` sobre una copia de la BD real: se crea sin tocar `ANIMES`, y queda
usable para `insert_sql` / `query_sql`.
- [ ] Un anime antiguo se lee sin campos desplazados: título, sinopsis y géneros correctos.
- [ ] Alta de un anime nuevo → la columna se rellena.
- [ ] Round-trip del campo nuevo (escribir → leer → mismo valor).
- [ ] La BD real del usuario **no** se tocó durante las pruebas.

---

## §2c — Añadir una preferencia de usuario

✅ Desde el 2026-07-30 existe `DB_user.db` ([04 §0](04-modelo-de-datos.md),
[13](13-selector-de-proveedor.md)). Es una tabla **clave/valor**, así que una preferencia nueva **no es
una migración**: son 3 pasos y ninguno toca el esquema.

1. Añade un miembro a `UserSettingKey` en `userPersistence.py`:

   ```python
   class UserSettingKey(Enum):
       DEFAULT_ANIME_PROVIDER = "default_anime_provider"
       MEDIA_TYPE_FILTER      = "media_type_filter"   # ← nueva
   ```

2. Si la preferencia se usa desde varios sitios, añade un **atajo tipado** en `UserPersistence` en vez
   de dejar `get_setting(UserSettingKey.…)` disperso por la GUI:

   ```python
   def get_media_type_filter(self) -> Optional[str]:
       return self.get_setting(UserSettingKey.MEDIA_TYPE_FILTER)

   def set_media_type_filter(self, value: str) -> bool:
       return self.set_setting(UserSettingKey.MEDIA_TYPE_FILTER, value)
   ```

3. Léela donde haga falta vía `main_window.user_persistence`. **Si el widget que la muestra se
   construye en `load_sidebar_buttons()`, la lectura tiene que estar hecha antes** — por eso
   `UserPersistence.start()` se llama de forma síncrona en `__init__` ([13 D7](13-selector-de-proveedor.md)).

💡 **Si la preferencia se puede «desactivar»**, no añadas un `DELETE`: `set_setting(clave, None)` deja
`setting_value` a `NULL` y `get_setting()` devuelve entonces el `default` que se le pase. Es lo que
hace el pin al desfijar el proveedor ([13 §12](13-selector-de-proveedor.md)); el atajo tipado debe
aceptar `Optional[str]` para permitirlo.

⚠️ **Separa «usar ahora» de «fijar»** si la preferencia tiene un control visible. Que cambiar el
widget persista de inmediato impide probar nada sin reescribir la configuración: es exactamente el
defecto que hubo que corregir en el selector de proveedor. El patrón que quedó: el widget cambia solo
la sesión, y un **pin** al lado escribe en `DB_user.db`.

**Checklist**

- [ ] El valor se guarda como **texto**; si es booleano o número, la conversión es de quien lee.
- [ ] Cambiar el widget **sin** confirmar no deja rastro en `DB_user.db`.
- [ ] La aplicación arranca con `DB_user.db` **borrada** (se regenera vacía).
- [ ] La aplicación arranca con la preferencia guardada **inválida** (p.ej. un `provider_id` que ya no
      existe): debe avisar por consola y seguir con el valor por defecto, no petar.
- [ ] Round-trip: escribir → cerrar → abrir → sigue ahí.
- [ ] `DB_Animes.db` no se ha tocado.

---

## §3 — Añadir un proveedor nuevo

**Ficheros a tocar**

| Fichero | Acción |
|---|---|
| `src/APIs/common/models.py` | 🆕 **miembro nuevo en `AnimeProviderId`** (`:18-31`) |
| `src/APIs/<sitio>/__init__.py` | crear **vacío** |
| `src/APIs/<sitio>/<sitio>.py` | crear (plantilla en [08 §7.3](08-convenciones-y-estilo.md)) |
| `src/gui/main_window.py` | importar (`:14-16`) y registrar (`:47-49`) |
| `MiBibliotecaAnime.spec` | `hiddenimports` (`:21-36`) |

**Pasos**

0. 🆕 **Añade el miembro a `AnimeProviderId`** (`models.py:18-31`). Desde el 2026-08-16 `PROVIDER_ID`
   es un enum, no una cadena, y su `value` es **lo que se persiste** en `ANIMES.provider_id` y en
   `USER_SETTINGS`:

   ```python
   class AnimeProviderId(Enum):
       ANIMEAV1     = "animeav1"
       JKANIME      = "jkanime"
       ANIMEFLV     = "animeflv"
       MONOSCHINOS2 = "monoschinos2"   # ← nuevo
   ```

   ⚠️ **Ese `value` es para siempre.** En cuanto un usuario guarde un anime desde ese proveedor, el
   texto queda escrito en su biblioteca; cambiarlo después convierte esas filas en «proveedor
   desconocido» (se degradan a `None`, [04 §4](04-modelo-de-datos.md)). Elige el slug corto y estable
   a la primera y no lo toques.

   Saltarse este paso no compila: `__init_subclass__` (`animeProviderMgr.py:71-75`) rechaza un
   `PROVIDER_ID` que no sea miembro del enum, **al importar** el módulo.
1. Explora el sitio **antes** de escribir código: ¿HTML clásico (selectores CSS) o framework JS
   (payload embebido)? Es la decisión que determina toda la implementación
   ([05 §3 y §4](05-proveedores-y-scraping.md)).

   ⚠️ **No asumas una sola respuesta para todo el sitio.** JKAnime usa las **dos** técnicas según la
   superficie: HTML servidor en portada, búsqueda y ficha; payload JS en el directorio; JSON por
   AJAX en los episodios ([05 §3b](05-proveedores-y-scraping.md)). Explora **cada una de las cuatro
   superficies** que necesitan los 5 métodos, no solo la portada.

   ⚠️ **Una rejilla vacía no significa que haga falta un navegador.** Antes de concluir que el sitio
   necesita renderizado JS, busca el payload en el HTML crudo (`grep 'animes *= *{'`). Es la
   **trampa 24**, y descartó una tarde de trabajo mal enfocado.
2. Crea la clase con los **3 atributos obligatorios** ya en el esqueleto — sin ellos el módulo no
   importa (trampa 11).
3. Implementa los **5 métodos**. Devuelve siempre tipos de `APIs.common.models`.
4. 🟡 **Fija la codificación** si el sitio no envía `charset` (trampa 14). Copia el patrón ya
   implantado en `animeav1.py:37-56`: un `_fetch()` de módulo por el que pasen **todas** las peticiones,
   en vez de repetir la línea en cada método.

   ```python
   def _fetch(url: str, **kwargs) -> requests.Response:
       response = requests.get(url, **kwargs)
       if "charset" not in response.headers.get("Content-Type", "").lower():
           response.encoding = "utf-8"
       return response
   ```

   Comprobar el header primero respeta el charset del servidor si algún día lo declara. **No uses
   `apparent_encoding`**: es detección estadística, cuesta en páginas grandes y puede fallar; si has
   verificado el encoding real del sitio, escríbelo.

   Cómo detectar que hace falta: `r.encoding` vale `ISO-8859-1` mientras `r.apparent_encoding` dice
   `utf-8`, y el texto sale con `Ã­`/`Ã±`/`Ã³`. Afecta a **todo** lo que salga de `response.text`,
   títulos incluidos — no solo a la sinopsis.

5. Si los slugs de género del sitio difieren de `AnimeGenreFilter`, **traduce dentro del proveedor**
   con un diccionario privado. Quien llama siempre pasa el enum común.

   ✅ Ejemplo real en `jkanime.py` (`_GENRE_TRANSLATIONS`): lista **solo las 10 excepciones** y deja
   que un helper caiga al valor del enum para las 30 que ya coinciden. Un diccionario con los 40 se
   desincroniza en cuanto el catálogo común crezca.

   Verifica la tabla **contra los slugs reales del sitio**, no a ojo: una traducción inventada no
   lanza ningún error, simplemente devuelve listas vacías ([09 §3d](09-verificacion-y-pruebas.md)).
6. **Documenta el orden de `episodes`** que devuelve `get_anime_info` — afecta al corte `[:25]` de la
   ficha y a lo que se guarda en BD (trampas 4 y 8).
7. Crea el `<Sitio>Singleton` (patrón en `animeav1.py:361-367`).
8. Registra en `main_window.py:47-49`. **El orden importa**: define la secuencia de fallback.

   ```python
   self.anime_provider_mgr.register(AnimeAV1Singleton(), default=True)
   self.anime_provider_mgr.register(MiSitioSingleton())
   self.anime_provider_mgr.register(AnimeFLVSingleton())
   ```

9. Añade `APIs.<sitio>.<sitio>` a `hiddenimports`.

**Checklist**

- [ ] `AnimeProviderId` tiene su miembro, y su `value` es el que quieres para siempre.
- [ ] El módulo **importa** sin `NotImplementedError`.
- [ ] El desplegable de la sidebar lo muestra **sin tocar la GUI**: sale de `list_provider_infos()`,
      que se deriva de los proveedores registrados. Si has tenido que editar `main_window.py` para que
      aparezca el nombre, algo está mal.
- [ ] Los 5 métodos verificados con el script de [09 §2](09-verificacion-y-pruebas.md) y las
      comprobaciones de [09 §3d](09-verificacion-y-pruebas.md).
- [ ] `get_recent_animes` y las búsquedas devuelven `synopsis/genres/episodes = None` (contrato
      implícito de los listados). *Excepción documentada*: el directorio de JKAnime **sí** trae
      `synopsis`, porque su payload la incluye y no cuesta una petición extra.
- [ ] `get_anime_info` rellena los tres.
- [ ] **Orden de `episodes` anotado** (ascendente o descendente).
- [ ] `search_*` devuelve `(lista, last_page)` con un `last_page` real.
- [ ] Si una búsqueda **no pagina**, devolver `[]` para `page>1` en vez de la primera página
      disfrazada de segunda: quien llame paginaría en bucle.
- [ ] Los géneros devueltos son slugs de `AnimeGenreFilter`, **comprobados contra el sitio**.
- [ ] `AnimeInfo.id` es un slug limpio, sin `/` ni `http` (si no, se duplican filas en la
      biblioteca).
- [ ] El póster de los listados es la **carátula del anime**, no una miniatura de episodio
      (trampa 23).
- [ ] **Tildes correctas** en `synopsis` y `title`.
- [ ] Fallback probado: fuerza un fallo del por defecto y comprueba que entra el tuyo
      ([09 §4](09-verificacion-y-pruebas.md)).
- [ ] **Posición en el registro decidida** conscientemente: es el orden del fallback.
- [ ] `hiddenimports` actualizado.

> ✅ **JKAnime (2026-08-06) es el recorrido completo de este playbook**, y el único que ha ejercitado
> los pasos 5 (traducción de géneros) y 8 (posición en el fallback). Si vas a añadir MonosChinos2 o
> TioAnime, lee antes [05 §3b](05-proveedores-y-scraping.md) y las trampas 23-25.

---

## §4 — Añadir un campo al modelo (`AnimeInfo` / `EpisodeInfo` / `ServerInfo`)

**Ficheros a tocar**

| Fichero | Acción |
|---|---|
| `src/APIs/common/models.py` | campo nuevo, **con default** |
| `src/APIs/animeav1/animeav1.py` + `animeflv.py` | rellenarlo (o dejarlo en el default) |
| `src/dataPersistence/animesPersistence.py` | solo si debe persistirse → **haz también §2** |
| las vistas que lo muestren | |

**Pasos**

1. Añade el campo **al final** de la dataclass y **con valor por defecto** (`models.py:86-93`), o
   romperás todas las construcciones posicionales existentes.
2. `AnimeInfo` se construye en: `animeflv.py:62,111,171,228`, `animeav1.py:229,269`. Revisa los seis.
3. Si debe persistirse, **no basta con el modelo**: hay que tocar `AnimeField`, `AnimeRecord`,
   `to_db_dict`, `from_db_dict` y `from_anime_info` (`:151-172`) — sigue §2. La migración de la BD ya
   es automática.
4. Si es opcional y un proveedor no lo tiene, déjalo en `None` — es el patrón de `synopsis`,
   `genres` y `episodes`.

**Checklist**

- [ ] `AnimeInfo(id=…, title=…, poster=…)` sigue funcionando sin el campo nuevo.
- [ ] Los dos proveedores construyen sin `TypeError`.
- [ ] Si se persiste: checklist de §2 completo.
- [ ] La ficha de detalle no peta cuando el campo vale `None`.

---

## §5 — Activar los iconos claro/oscuro

Los PNG **ya existen** en `resources/images/utils/` (`viendo_light/dark.png`,
`pendientes_light/dark.png`) pero están **sin trackear en git** y su uso está **comentado**.

**Ficheros a tocar**: `src/gui/sidebarButtons/watchingAnimes/watchingAnimes.py:23-25` y
`src/gui/sidebarButtons/pendingAnimes/pendingAnimes.py:23-25`.

```python
# Descomentar estas dos:
icon_path_light = os.path.join(icon_path, "viendo_light.png")
icon_path_dark  = os.path.join(icon_path, "viendo_dark.png")
# y borrar esta:
# icon_path_light = icon_path_dark = os.path.join(icon_path, "viendo.png")
```

⚠️ **Los 4 PNG están sin trackear** (`?? resources/images/utils/…`). Hay que **añadirlos a git**
antes o el `.exe` y cualquier clon se quedarán sin ellos. (Yo no ejecuto comandos de git — te toca.)

Para el resto de vistas hay que **crear** las variantes primero; hoy las 6 pasan el mismo fichero
para claro y oscuro, así que `update_icon()` (`utilsButtons.py:78-80`) no cambia nada visible.

**Checklist**

- [ ] Los PNG están trackeados en git.
- [ ] Light → Dark → System cambia el icono de «viendo» y «pendientes».
- [ ] El icono se ve bien sobre ambos fondos.
- [ ] `resources/images/utils` sigue en `datas` del `.spec` (`:19`) — ya lo está.

---

## §6 — Empaquetar con PyInstaller

**Pasos**

1. **Revisa `hiddenimports`.** ✅ **Ya no hay nada pendiente aquí.** Entre el 2026-08-06 y el
   2026-08-07 se añadieron `APIs.animeav1.animeav1`, `APIs.jkanime.jkanime`,
   `APIs.common.animeProviderMgr`, `APIs.common.models` y `dataPersistence.userPersistence`; se
   corrigió `gui.anime_windows` → `gui.anime_window` (`d99a2ee`) y se retiró el fantasma
   `gui.sidebarButtons.sidebarButton` (`ae126fd`).

   ✅ Comprobado el 2026-08-07: los **18** nombres declarados resuelven a ficheros reales de `src/`.
   El único módulo de `src/` que no figura es `app.py`, y es correcto: es el *script de entrada*, no
   un import oculto.

   Al añadir un módulo nuevo, añádelo aquí también — este playbook es el sitio donde se comprueba.

   ✅ **Comprobado compilando el 2026-08-17**: `pyinstaller MiBibliotecaAnime.spec` termina sin
   errores y el `.exe` resultante arranca. Hasta esa fecha la lista solo se había verificado
   resolviendo cada nombre a su fichero.

2. Sube `APP_VERSION` (`:3`) — determina el nombre de `dist/MiBibliotecaAnime_v<X>/`.
3. ✅ **`datas` ya no empaqueta datos de usuario.** Desde el 2026-08-17 contiene **solo**
   `resources/images/utils`. No vuelvas a añadir `resources/DB` ni las carpetas de pósters: la app
   las crea sola en el primer arranque, y empaquetarlas distribuye la biblioteca personal del
   desarrollador ([10 § trampa 18d](10-invariantes-y-trampas.md)).
4. Revisa que toda carpeta nueva de recursos **de solo lectura** esté en `datas` (`:11-13`).
   ⚠️ Los destinos son relativos a `_internal/`, no a la carpeta del `.exe`
   ([10 § trampa 18e](10-invariantes-y-trampas.md)).
5. **Si añades un fichero que el usuario final deba ver** (licencias, LÉEME), no lo pongas en
   `datas`: añádelo al bucle posterior a `COLLECT` (`:83-86`), que copia al primer nivel usando
   `DISTPATH`. Hoy copia `LICENSE`, `LEEME.txt` y `THIRD-PARTY-NOTICES.txt`.
6. **Regenera `THIRD-PARTY-NOTICES.txt` si has tocado `requirements.txt`** — caduca en cuanto cambia
   una dependencia. Se construye leyendo los `LICENSE` reales de `biblio_anime_env/Lib/site-packages`,
   con la lista de paquetes contrastada contra `build/MiBibliotecaAnime/Analysis-00.toc` (lo que
   PyInstaller mete de verdad en el binario, no lo que declara `requirements.txt`).
7. Compila:

   ```bash
   pyinstaller MiBibliotecaAnime.spec
   ```

8. Para depurar: cambia `console=False` → `console=True` (`:60`) y verás los `print`.

**Checklist**

- [ ] `hiddenimports` corregido y completo.
- [ ] El `.exe` arranca y muestra la pantalla de carga.
- [ ] Las 6 vistas de la sidebar abren sin `ModuleNotFoundError`.
- [ ] El **buscador** abre.
- [ ] Los iconos y el GIF de carga se ven (→ `datas` correcto).
- [ ] La ficha de detalle abre y los servidores cargan.
- [ ] Comprobado en una máquina **sin** el entorno de desarrollo.
- [ ] `dist/MiBibliotecaAnime_v<X>/` **no** contiene ningún `.db` ni `.jpg`
      (`find dist/… -name "*.db" -o -name "*.jpg"` → 0).
- [ ] `LICENSE`, `LEEME.txt` y `THIRD-PARTY-NOTICES.txt` están **junto al `.exe`**, no en `_internal/`.
- [ ] `THIRD-PARTY-NOTICES.txt` refleja las dependencias actuales.

---

## §7 — Diagnosticar «no salen los animes recientes»

**Síntoma**: `messagebox` de aviso al arrancar y rejilla vacía.

1. Mira la consola: los `print` del manager dicen quién falló y por qué
   ([05 §5](05-proveedores-y-scraping.md)).
2. Ejecuta el script de [09 §2](09-verificacion-y-pruebas.md) y compara con la línea base
   (AnimeAV1 → 20, AnimeFLV → 24).
3. Si **ambos** devuelven `[]` pero las URLs cargan en el navegador → cambió el HTML.
   - AnimeAV1: el sospechoso es el **payload de hidratación** (`kit.start(app, element, {`), no los
     selectores.
   - AnimeFLV: revisa los selectores de [05 §4](05-proveedores-y-scraping.md).
4. Si solo falla uno, el fallback debería taparlo: comprueba que el otro esté registrado
   (`main_window.py:48-49`).

---

## §8 — Reproducir un problema de episodios vistos

1. **Copia la BD** al scratchpad y parchea `get_resource_path` ([09 §3](09-verificacion-y-pruebas.md)).
   Nunca trabajes sobre la real.
2. Inspecciona el valor crudo:

   ```sql
   SELECT anime_id, watched_episodes, last_watched_episode, episodes
   FROM ANIMES WHERE anime_id = 'one-piece-tv';
   ```

3. Recuerda: `watched_episodes` son **rangos** (`[[1,1158]]`, no una lista de episodios) y `episodes`
   está **invertido** respecto a lo que devolvió el proveedor.
4. Si el usuario dice «marqué episodios y no se guardaron», comprueba primero que el anime **tenga
   algún estado asignado**: sin fila en `ANIMES`, `update_watched_episodes` devuelve `False` en
   silencio (trampa 7).
