# Especificación del rediseño

Todo lo que hace falta para implementar **sin abrir el diseño visual**. Lo que está aquí manda.

Si necesitas resolver una duda que esta especificación no cierra, el diseño está en
[`DISENO-VISUAL.html`](DISENO-VISUAL.html), en esta misma carpeta: **ábrelo en el navegador, no con
`Read`** — son ~1 350 líneas de maquetación y no contienen nada que no esté aquí. Hay una copia en
la nube en https://claude.ai/code/artifact/69458b98-88bd-479c-960c-2b441d56344a, pero el fichero
local es el que no depende de la red ni de que el enlace siga vivo.

Los colores van en **tuplas `(claro, oscuro)`**, que es lo que aceptan todos los parámetros de color
de CustomTkinter. Los tamaños son píxeles a escala 1.

---

## 1. Colores

| Token | Claro | Oscuro | Dónde |
|---|---|---|---|
| `BG` | `#F4F5F7` | `#14161A` | fondo del área de contenido |
| `PANEL` | `#E9EBEF` | `#0F1115` | barra lateral |
| `CARD` | `#FFFFFF` | `#1B1E24` | tarjetas, fila activa, controles |
| `CARD_HOVER` | `#EFF1F5` | `#232730` | hover de fila y tarjeta |
| `LINE` | `#DCDFE5` | `#262A33` | bordes de control y tarjeta |
| `LINE_SOFT` | `#E7EAEF` | `#1D212A` | separador entre filas de lista |
| `TXT` | `#171A1F` | `#ECEEF2` | títulos y texto principal |
| `TXT_2` | `#525A66` | `#A6AEBA` | secundario (sinopsis, ítems inactivos) |
| `TXT_3` | `#7C8593` | `#6F7885` | terciario (géneros, contadores, subtítulos) |
| `ACCENT` | `#3A55C9` | `#6D8AF0` | selección, progreso, acción principal |
| `ACCENT_SOFT` | `#E4E9FA` | `#222A44` | fondo de acento (globo del contador, ficha activa) |
| `ACCENT_INK` | `#FFFFFF` | `#0C1020` | texto **sobre** `ACCENT` |
| `WARN` | `#B45309` | `#FBBF24` | ⚠ identidad partida — **ya existe en `anime_window.py`, no inventar otro** |

Píldoras y sellos de estado:

| Token | Texto claro / oscuro | Fondo claro / oscuro |
|---|---|---|
| `FAV` | `#8E3F86` / `#D18ACB` | `#F6E9F5` / `#2C1A2E` |
| `SEE` (viendo) | `#1F6F85` / `#5FC6DE` | `#E2F1F6` / `#12303A` |
| `PEN` (pendiente) | `#8A6420` / `#D6A852` | `#F7EEDC` / `#332714` |
| `FIN` (finalizado) | `#2E7D5B` / `#68C888` | `#E3F3EA` / `#14321F` |

**Regla**: ningún color literal fuera de `theme.py`. Si un widget necesita un color que no está en la
tabla, se añade el token primero.

---

## 2. Tipografía

**Segoe UI**, que viene con Windows. No se empaqueta ninguna fuente. Números en columna:
**Cascadia Mono**, también de serie.

| Rol | Tamaño | Peso | Uso |
|---|---|---|---|
| `T_VIEW` | 24 | bold | título de vista («Viendo») |
| `T_SHEET` | 30 | bold | título en la ficha del anime |
| `T_ROW` | 17 | bold | título de anime en una fila de lista |
| `T_CARD` | 19 | bold | título en la tarjeta de retomar |
| `T_BODY` | 15 | normal | sinopsis |
| `T_UI` | 13 | normal | controles, ítems de nav, texto de tarjeta |
| `T_SUB` | 13 | normal | subtítulo de vista, proveedor · usa `TXT_3` |
| `T_LABEL` | 11 | bold | etiqueta de sección en MAYÚSCULAS · usa `TXT_3` |
| `T_META` | 11 | normal | géneros, contadores, sellos |
| `T_NUM` | 12 | normal | Cascadia Mono · «12 / 24», paginación |

CustomTkinter no admite tamaños fraccionarios: todo son enteros.

---

## 3. Medidas

| Pieza | Valor |
|---|---|
| Ventana | 1440 × 910 (**sin cambios**) |
| Barra lateral | **224** desplegada · **84** plegada |
| Ítem de nav | alto 38 · padding-x 18 · hueco icono-texto 11 · icono 16 |
| Ítem de nav plegado | 48 × 48 · radio 11 · icono 20 · globo de contador 15 arriba-derecha |
| Cabecera de vista | alto 80 |
| Padding lateral del contenido | 28 |
| Rejilla de 6 (nuevos, finalizados, buscar) | póster **176 × 264** · hueco 20 × 24 · radio 9 |
| Rejilla de 5 (favoritos) | póster **216 × 324** · hueco 20 × 24 · radio 9 |
| 🆕 Columnas de una rejilla *(2026-09-02)* | **no son fijas**: `ancho // (póster + hueco)`. Los 6 y 5 de arriba son lo que sale a 1440; a 1920 son 8 y 7 |
| Fila de viendo | póster **70 × 100** · alto de fila 132 · padding 16 × 12 |
| Fila de pendientes | póster **56 × 80** · alto de fila 113 |
| Tarjeta «Retomar» (nuevos) | 3 en fila · póster 84 × 118 · radio 7 · tarjeta radio 12 |
| Panel «Lo último que veías» (viendo) | ancho 290 · póster a ancho completo, ratio 2:3 |
| Póster de la ficha | **248 × 372** · radio 11 |
| Barra de progreso | alto 4 · radio 2 |
| Botón de estado de la ficha | alto 40 · radio 9 · 4 en fila con hueco 10 |
| Fila de episodio | alto 52 |
| Radios generales | control 7 · tarjeta 12 · píldora = alto ÷ 2 |

---

## 4. Caché de pósters — decisión que afecta a todo

Hoy `download_animes_poster()` guarda los JPG a **130 × 185** y `get_anime_image()` los pide a ese
tamaño. El rediseño necesita hasta 248 × 372, y ampliar un JPG de 130 px se ve borroso.

**Decisión: la caché pasa a guardarse a 248 × 372** (el mayor tamaño que pide cualquier vista) y cada
vista pide su `size=` al construir el `CTkImage`, que reduce con calidad. Consecuencias:

- Hay que **borrar una vez** las 6 carpetas de `resources/images/`. Están en `.gitignore` y se
  regeneran solas al arrancar; no se pierde nada del usuario.
- El coste en disco es despreciable (~30 KB por póster × 28 filas).
- ⚠️ `get_anime_image()` pasa `size=` **explícito** en la rama de descarga desde red. Sin él,
  `CTkImage` pinta a 20 × 20 ([trampa 17](../docs/10-invariantes-y-trampas.md)). Sigue haciendo falta.

Lo aplica la **fase 1**.

---

## 5. Componentes compartidos

Van en `src/gui/components/`. Cada uno nace en la fase que lo necesita primero y las siguientes lo
reutilizan **sin bifurcarlo**: si una vista necesita una variante, se añade un parámetro, no una copia.

| Componente | Nace en | Anatomía |
|---|---|---|
| `Sidebar` | 1 | 6 destinos con icono + etiqueta + contador. Estado activo: fondo `CARD` + barra de 2 px `ACCENT` a la izquierda. Abajo: proveedor (con pin) y apariencia. Botón de plegado en la esquina superior derecha |
| `ViewHeader` | 1 | Título `T_VIEW` + subtítulo `T_SUB` a la izquierda; controles a la derecha (buscador, orden). Alto fijo 80 |
| `PosterGrid` | 2 | N columnas parametrizable. Celda: póster + título a 2 líneas (`TXT_2`, `T_UI`). Admite un sello superpuesto con `place()` y una fila extra bajo el título |
| `Pager` | 2 | «Mostrando A–B de N» a la izquierda, botones de página a la derecha. Se muestra **solo** si `N > tamaño_de_página` |
| `ResumeCard` | 2 | Póster + título + «Siguiente: episodio N de M» + barra de progreso |
| `AnimeRow` | 3 | Póster + título + géneros + (opcional) progreso + proveedor a la derecha. Pendientes la usa sin progreso |
| `SidePanel` | 3 | Panel de 290 px con la tarjeta grande de retomar y su botón de acción |
| `StatusPill` | 5 | Píldora de estado con los 4 pares de color de la tabla 1 |
| `GenreChips` | 7 | Fila de fichas seleccionables; las activas usan `ACCENT_SOFT` + borde `ACCENT` |
| `EmptyState` | 9 | Icono, frase y acción. Sustituye al `CTkLabel` suelto de hoy |

---

## 6. Reglas de composición

- **Rejilla donde se mira, cascada donde se decide.** Nuevos, favoritos y finalizados son rejilla;
  viendo y pendientes son lista. No se mezclan.
- **La paginación aparece solo donde hace falta**: nuevos (24), favoritos (12) y buscar (variable).
  Viendo (6), pendientes (7) y finalizados (9) caben de una vez y **no llevan paginador**. El tamaño
  de página es **10** salvo en las rejillas de 6 columnas, que usan **12** para no dejar filas cojas.

  > 🆕 **Generalizado el 2026-09-02.** Esta regla se escribió con las columnas fijas, y con ellas los
  > números 10 y 12 *eran* la regla. Desde que `PosterGrid` calcula sus columnas del ancho, lo que se
  > conserva es la **intención** —una página son **dos filas llenas**, nunca una llena y otra coja—:
  > cada vista declara `ROWS_PER_PAGE = 2` y el tamaño de página sale de `columnas × 2`. A 1440, el
  > ancho con el que se dibujó este documento, siguen saliendo exactamente 12 y 10.
  > «Buscar» queda fuera, como siempre: allí trocea el proveedor.
- **Ningún dato repetido en la misma pantalla.** Los contadores viven en la barra lateral y no se
  repiten en el contenido. En «Viendo» no hay columna de estado ni de último visto.
- **El proveedor se enseña siempre en las vistas de biblioteca**, porque una fila puede ser de un
  sitio distinto al seleccionado. En la ficha se conservan las tres líneas actuales.

---

## 7. Cambios de comportamiento (no son solo aspecto)

Cada uno se implementa en su fase y se anota como tal:

| Cambio | Fase |
|---|---|
| La barra lateral se pliega y recuerda su estado | 1 |
| Las pestañas pierden la palabra «Anime»; «Animes recientes» pasa a «Nuevos lanzamientos» | 1 |
| Se guardan los 3 últimos animes vistos y sobreviven al cierre de la app | 2 |
| Pendientes se ordena por duración y ofrece «Empezar» sin abrir la ficha | 4 |
| Los favoritos tienen calificación personal y se pueden ordenar por ella | 5 |
| Los resultados de búsqueda avisan de que ya están guardados | 7 |
| Los botones de estado de la ficha pasan de cambiar de texto a encenderse y apagarse | 8 |
| Las filas de episodio dejan de repetir el título del anime | 8 |

---

## 8. Preferencias nuevas en `USER_SETTINGS`

Filas nuevas en `DB_user.db`, **sin migración de esquema** — es clave/valor
([docs/11 §2c](../docs/11-playbooks.md)).

⚠️ **Las claves no son cadenas libres.** `get_setting()` y `set_setting()` reciben un
**`UserSettingKey`**, que hoy tiene un único miembro (`DEFAULT_ANIME_PROVIDER`). Añadir una
preferencia es **añadir un miembro a ese enum** (`userPersistence.py:40`), igual que añadir un
proveedor es añadir un miembro a `AnimeProviderId`. El propio docstring del enum lo dice.

| Miembro nuevo de `UserSettingKey` | Valor persistido | Valor | Fase |
|---|---|---|---|
| `SIDEBAR_COLLAPSED` | `"sidebar_collapsed"` | `"0"` / `"1"` | 1 |
| `LAST_WATCHED_ANIME_IDS` | `"last_watched_anime_ids"` | hasta 3 `anime_id` separados por comas, el más reciente primero | 2 |
| `FAVOURITES_ORDER` | `"favourites_order"` | `"rating"` / `"title"` | 5 |

Conviene envolver cada una en un par `get_*`/`set_*` tipado en `UserPersistence`, como ya se hizo
con `get_default_provider_id()` / `set_default_provider_id()`: la GUI no debería manejar cadenas
sueltas.

**`DB_user.db` es desechable**: si algo sale mal, se borra y se regenera
([docs/13 §4](../docs/13-selector-de-proveedor.md)).

---

## 9. Lo único que toca la biblioteca real

La calificación de favoritos, en la **fase 5**: un miembro nuevo `RATING` **al final** de
`AnimeField`. Al ir al final, `validate_db_integrity()` lo resuelve por la vía barata
(`ALTER TABLE ADD COLUMN`, sin reconstruir la tabla). Detalle y precauciones en
[fases/5-favoritos.md](fases/5-favoritos.md).

Ninguna otra fase escribe en `DB_Animes.db` fuera de lo que la app ya hacía.
