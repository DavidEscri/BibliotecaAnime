# Estado del rediseño

> Este fichero es la memoria del plan entre sesiones. Lo lee y lo escribe `/fase`.
> Si contradice al árbol de trabajo, **gana el árbol**: `git log --oneline` y `git status` mandan.

| | |
|---|---|
| **Fase actual** | 4 — Pendientes |
| **Situación** | ⬜ no empezada |
| **Último paso completado** | Paso 3.3 — montar la vista (**fase 3 cerrada**) |
| **Siguiente paso** | Paso 4.1 — leer la ficha de la fase 4 y `pendingAnimes.py`; reutiliza `AnimeRow` **sin tocarla** (`poster_size=Metrics.ROW_PENDING_POSTER`, `show_progress=False`, acción «Empezar») |
| **Rama** | ✅ `feature/ui-redisign` (**no** `feature/rediseno-ui`: ya existía, ver Decisiones) |
| **Base** | `bd25742` (fase 1) → fase 2 → fase 3 encima, en `feature/ui-redisign`. El plan partió de `6377b92`, no de `4f9e429` |
| **Commits** | automáticos (uno al cerrar cada fase) |
| **Actualizado** | 2026-08-20 |

---

## Tablero

| # | Fase | Situación | Commit | Verificada |
|---|---|---|---|---|
| 1 | Cimientos | ✅ terminada | `bd25742` | ✅ app ejecutada y **mirada** (desplegada y plegada) + 73 comprobaciones |
| 2 | Nuevos lanzamientos | ✅ terminada | `ef9f4d4` | ✅ app ejecutada y **mirada** (4 arranques + recorrido de las 6 vistas) + 48 + 14 comprobaciones |
| 3 | Viendo | ✅ terminada | `3198f12` | ✅ app ejecutada y **mirada** (3 arranques reales + recorrido de las 6 vistas + ficha abierta por las 3 vías) + 42 + 29 comprobaciones |
| 4 | Pendientes | ⬜ no empezada | — | — |
| 5 | Favoritos | ⬜ no empezada | — | — |
| 6 | Finalizados | ⬜ no empezada | — | — |
| 7 | Buscar | ⬜ no empezada | — | — |
| 8 | Ficha del anime | ⬜ no empezada | — | — |
| 9 | Cohesión | ⬜ no empezada | — | — |

**Situación**: ⬜ no empezada · 🟡 en curso · ✅ terminada · ⚠️ terminada sin verificar · ❌ revertida

### Qué quedó sin verificar

Lo que no se ha podido ejecutar en cada fase, para que nadie lo dé por probado.

| Fase | Sin verificar | Por qué |
|---|---|---|
| 2 | **El gesto completo de «marcar el episodio 3 en la ficha, cerrar y reabrir»** | Hace falta un clic humano en la ficha. Se probaron **las dos mitades por separado**: `push_last_watched_id()` con 14 comprobaciones sobre una `DB_user.db` temporal (incluida la supervivencia al reinicio), y el pintado de la banda en la app real con la preferencia poblada con tres animes de la biblioteca. **La costura entre ambas —la llamada de `__toggle_episode_switch`— está leída, no ejecutada** |
| 2 | El **hover** de las celdas y de las tarjetas | No hay puntero que pasar por encima |
| 3 | El hover **con un ratón de verdad** | Sigue sin haber puntero que mover. Sí se ejecutó el mecanismo entero: se emiten `<Enter>`/`<Leave>` **sobre el canvas interno**, que es lo que toca el ratón, y se comprobó que la píldora aparece, que el fondo cambia a `CARD_HOVER`, que pasar del marco a un hijo **no** lo apaga y que la fila no se mueve |
| 3 | La **suma de resultados de la búsqueda web** | Se probó con el proveedor devolviendo vacío —que es exactamente el caso «sin conexión»— y con las tres consultas llegando al proveedor. Que un resultado web **añada** un anime que el título guardado no encuentra sigue sin ejecutarse: haría falta un alias real («Solo Leveling») entre los animes que estás viendo, y hoy solo hay One Piece |

---

## Decisiones tomadas sobre la marcha

Aquí va lo que se decide durante una fase y afecta a las siguientes. Una línea por decisión, con la
fase que la tomó. Empieza vacío a propósito: las decisiones de partida están en
[DISENO.md](DISENO.md).

| Fase | Decisión |
|---|---|
| 1 | **La rama es `feature/ui-redisign`, no `feature/rediseno-ui`.** Ya existía al empezar, creada por el usuario, y es donde vive el commit `6377b92` que trajo este plan. Renombrarla no está autorizado y el nombre es suyo. Todas las fases commitean ahí |
| 1 | **Las medidas de `DISENO.md` §3 también viven en `theme.py`**, en una clase `Metrics` junto a `Theme`. Mismo motivo que los colores: que un número del diseño no se copie a mano en cinco vistas y luego solo se corrija en tres |
| 1 | **`utils/utils.py` duplica el valor de `POSTER_CACHE_SIZE` a propósito.** `docs/01 §2` le prohíbe importar de `gui/**`, así que no puede leer `Metrics.POSTER_CACHE_SIZE`. El comentario de `utils.py:24-33` lo dice y nombra a su pareja: si cambia uno, cambia el otro |
| 1 | **Borrar las 6 carpetas de pósters NO era inocuo.** Las 4 vistas de estado pintan con `load_image()`, que **no sale a la red**: sin fichero se quedan con el placeholder gris hasta que el usuario vuelva a marcar el estado a mano. Se regeneraron los 39 pósters desde `poster_url` con un script del scratchpad (BD abierta en `?mode=ro`). `recent_animes/` y `search/` sí se rellenan solas. **Si una fase futura vuelve a vaciar la caché, tiene que repetir esa regeneración** |
| 1 | **`get_anime_image()` sigue con su `(195, 275)` por defecto.** Subirlo a los 248 × 372 de la ficha es cosa de la **fase 8**, que es la que rehace `anime_window.py` |
| 1 | 🔴 **`SidebarButton` ya no es un widget.** Pasó de `CTkButton` a clase llana: solo describe el destino (`sidebar_text`, `sidebar_command`, `sidebar_icon(size)`). Quien pinta es `Sidebar`. La firma del constructor **no cambió**, así que las 6 vistas heredan igual sin tocarlas. Si una fase futura necesita el botón como widget, no existe: lo que hay es el `_NavItem` de la barra |
| 1 | 🔴 **Un `CTkFrame` sin hijos conserva su tamaño por defecto (200 × 200)** como tamaño pedido, y estira la fila que lo contenga. Costó una tarde: la barrita de acento de 2 px inflaba la fila a 200 y el icono y la etiqueta caían en `y=86`, **fuera de la parte visible** — la barra salía con los seis destinos en blanco, sin ningún error. **Todo `CTkFrame` decorativo o todavía vacío necesita `height=` explícito** (`controls_frame` de `ViewHeader` nace con `height=1` por esto). Aplica a `PosterGrid`, `Pager`, `AnimeRow`, `SidePanel`… — es decir, a casi todo lo que construyen las fases 2-8 |
| 1 | **El ancho de la barra necesita `grid_propagate(False)` *y* `minsize` en la columna 0 del padre.** Solo con el primero, la rejilla de `MainWindow` le roba píxeles cuando el contenido pide más ancho del que cabe (medido: 219 en vez de 224). Lo pone `Sidebar.__apply_collapsed_layout()` en cada plegado |
| 1 | **Las etiquetas de los destinos viven en cada vista**, en su `super().__init__` (`"Favoritos"`, `"Viendo"`…), no en la barra. La barra las lee de `sidebar_text`. Renombrar una pestaña es tocar su vista, no `Sidebar` |
| 1 | **El orden de la barra cambió**: Nuevos · Favoritos · Viendo · Pendientes · Finalizados · Buscar. Antes finalizados iba delante de viendo y pendientes. Lo fija la lista `destinations` de `load_sidebar_buttons()` |
| 2 | **Una celda de `PosterGrid` es un `CTkFrame` propio y ocupa UNA fila de la rejilla.** Las vistas de hoy pintan póster y título sueltos en `row*2` / `row*2+1`, y las de estado necesitaron una tercera fila para el proveedor (`row*3`…). Con la celda como marco, añadir o quitar una línea bajo el título no toca ningún índice — que es justo lo que la ficha de la fase 2 avisaba que costaría |
| 2 | **`Pager` es dueño del corte de la lista** (`slice_bounds()`), no solo de los botones. Si cada vista calculara su propio `[inicio:fin]`, el texto «Mostrando A-B de N» y lo que se ve en pantalla podrían discrepar |
| 2 | 🔴 **`wraplength` NO limita a dos líneas y un `CTkLabel` NO se recorta a su `height`**: envuelve todas las líneas que necesite y crece. Por eso existe `Theme.ellipsize(texto, fuente, ancho, líneas)`, que mide con `font.measure()` y corta con puntos suspensivos. **Todo título de ancho fijo tiene que pasar por ahí** — `AnimeRow` (fase 3), las rejillas de las fases 5-7 y la ficha (fase 8) |
| 2 | **La portada ya no duerme.** El `time.sleep(0.1)` tras `clear_frame()` solo servía para que `winfo_width()` no valiera 1 al calcular columnas; con seis fijas sobra. Las otras cinco vistas lo conservan hasta que les toque su fase: quitarlo es parte de reescribir la vista, no un cambio suelto |
| 2 | **La preferencia `last_watched_anime_ids` guarda identificadores, no filas.** Quien la pinte tiene que tolerar que el anime ya no esté en la biblioteca (`get_anime_by_anime_id()` → `None`) y descartarlo en silencio |
| 3 | 🔴 **El acordeón «Abrir filtro de animes» desaparece de las vistas de estado.** No está en el diseño —la cabecera de `#viendo` solo lleva buscador— y filtrar por género seis animes que ya son tuyos no aporta. **Aplica también a las fases 4, 5 y 6**: las cuatro vistas lo tenían igual. Si el filtrado por género vuelve, el sitio es `GenreChips` (fase 7), no un acordeón por pestaña |
| 3 | **`AnimeRow` se parametriza, no se bifurca.** `poster_size`, `show_progress`, `action`, `on_click`, `provider_name`, `text_width` y `show_separator`. La fase 4 la usa **sin tocar el fichero**: `Metrics.ROW_PENDING_POSTER`, `show_progress=False` y un `RowAction("Empezar", …)` |
| 3 | 🔴 **CustomTkinter no ata `bind()` al widget que crees.** `CTkFrame.bind()` va a su `_canvas`; `CTkLabel.bind()`, al `_label` **y** al canvas; `CTkEntry.bind()`, al `_entry`; `CTkButton.bind()`, al canvas y a sus etiquetas. Con el ratón real da igual —lo que se toca es el canvas—, pero **`widget.event_generate()` sobre el objeto CTk no dispara nada**: cualquier prueba futura de hover o de clic tiene que emitir sobre el hijo interno |
| 3 | 🔴 **Un `<Leave>` no significa que el ratón se haya ido.** Tk lo manda también al pasar del marco a uno de sus hijos, así que apagar el hover ahí hace parpadear la fila y la píldora se escapa justo al ir a pulsarla. `AnimeRow.__pointer_inside()` compara `winfo_pointerxy()` con el rectángulo real de la fila antes de apagar nada. Lo mismo va a hacer falta en cualquier fila o tarjeta con acción en hover |
| 3 | **El hueco de la acción se reserva siempre**, con un marco de tamaño fijo y `grid_propagate(False)`; la píldora solo se muestra y se esconde. Si se creara al entrar el ratón, la fila cambiaría de ancho debajo del cursor |
| 3 | **Los 290 px del panel lateral son 248 + 21 × 2**, no un número redondo: 248 es el ancho al que se guarda el póster en disco, así que se pinta a tamaño natural. **Toda línea de la tarjeta tiene que medirse contra 248**; el pie «Lo dejaste en el episodio 1163 · AnimeAV1» mide 249 y, sin controlarlo, era él quien decidía el ancho de la tarjeta |
| 3 | **Cuando un texto no cabe, primero se dice más corto y solo después se recorta.** El pie del panel pasa a «Episodio 1163 · AnimeAV1» (y a «Sin empezar · X» si no has visto nada): los puntos suspensivos se comían justo el nombre del proveedor, que es la mitad del dato |
| 3 | **La píldora «Episodio N →» abre la ficha, no el episodio.** Dejarla abierta por ese episodio es de la **fase 8**: es la que rehace la lista de episodios y la única que puede quitarle el tope de `[:25]`, sin el cual un «Episodio 1164» no tiene dónde caer |
| 3 | **El panel lateral recorre los tres identificadores de `last_watched_anime_ids`**, no solo el primero. Si el más reciente ya no está en «Viendo» (lo marcaste como finalizado), el siguiente también es algo que estabas viendo. Si no cuadra ninguno, el primero de la lista |
| 2 | **Los pósters se cargan con `load_rounded_image()`, no con `load_image()`.** CustomTkinter no redondea la `image` de un widget por mucho `corner_radius` que tenga: el recorte hay que traerlo hecho desde PIL. De paso reduce con LANCZOS, que es para lo que la fase 1 subió la caché a 248 px |

---

## Bitácora

Una entrada por paso completado, **la más reciente arriba**. Formato:

```
### Fase N · Paso N.M — <qué se hizo>          (AAAA-MM-DD)
- Ficheros: ruta/uno.py, ruta/dos.py
- Verificado: sí/no · cómo
- Pendiente que deja: …
```

<!-- nuevas entradas aquí arriba -->

### Fase 3 · Paso 3.3 — Montar la vista «Viendo»          (2026-08-20)
- Ficheros: `src/gui/sidebarButtons/watchingAnimes/watchingAnimes.py` (reescrito)
- `ViewHeader` («Viendo» + «N animes a medias · M episodios pendientes» + buscador) → cuerpo en dos
  columnas: cascada de `AnimeRow` (flexible) y `SidePanel` (290 fijos). **Sin paginador.**
- El **buscador local (`SavedAnimeSearch`) se reutiliza tal cual**, como mandaba la ficha; solo
  cambia el aspecto del control y ahora responde también a **Enter**. El panel lateral **no** se
  repinta al buscar: enseña lo último que veías, no el filtro.
- 🔴 **Fuera el acordeón «Abrir filtro de animes»** (ver Decisiones). Es lo único que esta vista
  pierde, y el diseño no lo tiene.
- ✅ Fuera el `time.sleep(0.1)` del hilo de UI: esta vista ya no mide `winfo_width()`. Van dos de
  seis; las cuatro restantes lo conservan hasta su fase.
- Estado vacío propio («Todavía no estás viendo ningún anime…»), pendiente de sustituirse por
  `EmptyState` en la fase 9.
- Verificado: sí · **29 comprobaciones** sobre la vista montada en una ventana Tk real (cabecera,
  6 filas, sin paginador, panel único de 290, alturas y anchos iguales, el panel intacto durante la
  búsqueda, biblioteca vacía y tres repintados seguidos sin duplicar widgets).
- Pendiente que deja: nada.

### Fase 3 · Paso 3.2 — `SidePanel`          (2026-08-20)
- Ficheros: `src/gui/components/side_panel.py` (nuevo)
- Panel de 290 px con póster a ancho completo (248 × 372, ratio 2:3), título, «Lo dejaste en el
  episodio N · Proveedor», barra de progreso con «vistos / total» en monoespaciada y botón `ACCENT`
  «Seguir por el N».
- Se alimenta de la **misma** preferencia que la banda de la portada y del **mismo**
  `resume_progress()`. Con todo visto el botón pasa a «Abrir la ficha»; sin nada visto, a «Seguir
  por el 1» y el pie dice que no has empezado —nunca «Episodio 0»—.
- 🔴 Dos ajustes de ancho que costaron las dos únicas medidas que no cuadraban: una
  `CTkProgressBar` **pide 200 px por defecto** (con el contador al lado, la tarjeta reclamaba 330) y
  el pie **mide 249 px** con un episodio de cuatro cifras. Ver Decisiones.
- Verificado: sí · dentro de las 42 comprobaciones del paso 3.1, con la fila real de One Piece
  (1163/1174) y con un anime sin empezar.
- Pendiente que deja: nada.

### Fase 3 · Paso 3.1 — `AnimeRow`          (2026-08-20)
- Ficheros: `src/gui/components/anime_row.py` (nuevo)
- Póster 70 × 100 · título a **una** línea · géneros en MAYÚSCULAS separados por ` · ` · barra de
  progreso con «N de M episodios» · proveedor a la derecha · separador `LINE_SOFT` · fondo
  `CARD_HOVER` al pasar el ratón · píldora de acción que aparece en hover. Alto medido: **132 px**,
  el del diseño.
- El progreso sale de `resume_progress()` sobre la fila guardada: **la vista funciona sin conexión**.
- 🔴 Tres trampas nuevas por el camino, todas en Decisiones: `bind()` de CustomTkinter no va al
  widget que crees, un `<Leave>` no significa que el ratón se haya ido, y el hueco de la acción hay
  que reservarlo o la fila se mueve sola.
- Verificado: sí · **42 comprobaciones** con Tk real: geometría, textos, hover completo (aparecer,
  resaltar, pasar a un hijo, salir), clic desde el título, clic en la píldora, y **5 casos límite**
  (sin episodios, sin nada visto, todo visto, título kilométrico, con huecos → el siguiente es el
  primero sin ver, no el posterior al último).
- Pendiente que deja: la fase 4 tiene que poder usarla **sin tocar el fichero**. Los parámetros que
  necesita ya están (`poster_size`, `show_progress=False`, `action`).

### Fase 2 · Paso 2.4 — Montar la vista          (2026-08-20)
- Ficheros: `src/gui/sidebarButtons/recentAnimes/recentAnimes.py` (reescrito), `src/gui/theme.py`
- La portada pasa a ser `ViewHeader` («Nuevos lanzamientos» + «N estrenos · Proveedor») → banda de
  retomar → `PosterGrid` de 6 → `Pager` de 12. **`ViewHeader` se estrena aquí**: la fase 1 lo dejó
  construido y sin usar.
- ✅ **Fuera el `time.sleep(0.1)` del hilo de UI.** Solo existía para que `winfo_width()` devolviera
  algo distinto de 1, porque de ahí salía el número de columnas (`// 150`). Con seis fijas no se
  mide nada. **Es la única vista que ya no duerme**; las otras cinco lo conservan hasta su fase.
- También fuera el bucle que ponía `weight=1` en las columnas 0..N de `content_frame`. Se comprobó
  que no afectaba a las otras vistas: las cuatro de estado pintan dentro de su propio
  `__episodes_frame`, cuyas columnas nunca llevaron peso.
- 🔴 **`Theme.ellipsize()`** nuevo: `wraplength` **no** limita a dos líneas —envuelve las que hagan
  falta— y un `CTkLabel` **crece por encima de su `height`** en vez de recortarse. Con títulos de
  tres líneas la fila quedaba desnivelada y las tres tarjetas de retomar, descuadradas. Mide con
  `font.measure()` y corta con puntos suspensivos. Lo usan `PosterGrid` y `ResumeCard`, y lo van a
  necesitar `AnimeRow` (fase 3) y la ficha (fase 8).
- Verificado: sí · **4 arranques reales con captura de la ventana** (la app se manda al fondo con
  `SetWindowPos` y se captura con `PrintWindow`, sin robarle el foco a nadie) + **48
  comprobaciones** de geometría + recorrido por código de **las 6 vistas**, todas se abren sin
  excepción. Ver «Qué quedó sin verificar» más abajo.
- Pendiente que deja: el buscador de la cabecera **se pospone a la fase 9** — esta vista no tenía
  ninguno que conservar, así que no hay regresión.

### Fase 2 · Paso 2.3 — `ResumeCard` y la banda «Retomar donde lo dejaste»          (2026-08-20)
- Ficheros: `src/gui/components/resume_card.py` (nuevo), `src/utils/utils.py`
- `ResumeCard` (póster 84×118, título, «Siguiente: episodio N de M» y barra de progreso) y
  `ResumeBand` (etiqueta + hasta 3 tarjetas en columnas iguales). `has_content()` es lo que decide
  si la banda entra en la rejilla: sin nada que retomar **no se pinta ni la etiqueta**.
- `resume_progress()` es el **único** sitio donde se calcula por dónde iba el usuario. Ordena los
  episodios antes de mirar nada porque salen invertidos de la BD ([trampa 2]) y devuelve
  `(siguiente, total, fracción)`. Casos cubiertos: todo visto → «Lo has visto entero», fila sin
  episodios → `last_watched_episode + 1` sin prometer total, y huecos → el primero sin ver, no el
  siguiente al último.
- `find_cached_poster_path()` nuevo en `utils/utils.py`, extraído de `get_anime_image()`: devuelve
  la ruta del póster en las 6 carpetas **sin salir a la red**, así que se puede llamar desde el hilo
  de Tkinter. `get_anime_image()` pasa a usarlo y conserva su `size=` explícito (trampa 17).
- Verificado: sí · dentro de las 48 comprobaciones del paso 2.4, más la app real con la banda
  poblada con tres animes de la biblioteca (One Piece → «Siguiente: episodio 1164 de 1174», que
  cuadra con el `last_watched_episode = 1163` de la fila).
- Pendiente que deja: nada.

### Fase 2 · Paso 2.2 — La preferencia `LAST_WATCHED_ANIME_IDS`          (2026-08-20)
- Ficheros: `src/dataPersistence/userPersistence.py`, `src/gui/anime_window.py`
- Miembro nuevo en `UserSettingKey` (valor `last_watched_anime_ids`) más
  `get_last_watched_ids()` / `push_last_watched_id()` y la constante `MAX_LAST_WATCHED = 3`.
  Sin migración: la tabla es clave/valor. Se persiste como slugs separados por comas, el más
  reciente primero; `push` sube el que ya estaba en vez de duplicarlo.
- `anime_window.py`: **una** llamada en `__toggle_episode_switch`, con dos guardas — solo al
  **marcar** (desmarcar no es «seguir viendo») y solo si `update_watched_episodes()` devolvió
  `True`, que es `False` cuando el anime **no está en la biblioteca**. Sin esa segunda guarda,
  ver un episodio de un anime no guardado dejaría en «Retomar» una tarjeta sin fila que pintar.
  Usa `persistence_anime_id` (trampa 21).
- Verificado: sí · **14 comprobaciones** en el scratchpad sobre una `DB_user.db` temporal (orden,
  tope de 3, sin duplicados, supervivencia al reinicio, no-op al repetir el primero, y que el pin
  y el plegado de la fase 1 siguen intactos).
- Pendiente que deja: nada.

### Fase 2 · Paso 2.1 — `PosterGrid` y `Pager`          (2026-08-20)
- Ficheros: `src/gui/components/poster_grid.py`, `src/gui/components/pager.py` (nuevos),
  `src/utils/utils.py`
- `PosterGrid(parent, columns=6, poster_size=..., on_click=...)` + la dataclass `PosterItem`
  (`key`, `title`, `poster_path`, `badge`, `badge_colors`, `footer`). Las fases 5, 6 y 7 lo
  reutilizan cambiando parámetros: el sello de finalizados y el «ya lo tienes» de buscar entran
  por `badge`, y el proveedor de las vistas de biblioteca por `footer`.
- `Pager(parent, page_size, on_page)`: «Mostrando A-B de N» + flechas y números, con ventana y
  puntos suspensivos por encima de 7 páginas. Se **esconde solo** con `grid_remove()` si
  `total <= page_size`. Expone `slice_bounds()` para que el corte de la lista y el texto no
  puedan discrepar.
- `load_rounded_image()` nuevo en `utils/utils.py`: reduce con **LANCZOS** (que es para lo que se
  guarda la caché a 248 px) y redondea las esquinas con una máscara alfa de PIL. Hacía falta:
  el `corner_radius` de un widget de CustomTkinter **no** recorta su `image`.
- Verificado: parcialmente · sintaxis e importación. El pintado real se comprueba en el paso 2.4,
  que es el que los cuelga de una ventana.
- Pendiente que deja: medir que las 6 columnas caben de verdad en el `content_frame`
  (1216 px menos la barra de desplazamiento) sin recortar la sexta.

### Fase 1 · Paso 1.5 — `ViewHeader` y cableado de `MainWindow`          (2026-08-20)
- Ficheros: `src/gui/components/view_header.py` (nuevo), `src/gui/main_window.py`
- `ViewHeader`: título `T_VIEW` + subtítulo `T_SUB` a la izquierda y `controls_frame` vacío a la
  derecha, alto 80. **Todavía no lo usa ninguna vista**: lo estrena la fase 2.
- `MainWindow`: fuera `create_sidebar_frame()`; `sidebar_frame` pasa a ser la `Sidebar` y se
  construye en `load_sidebar_buttons()` (necesita el gestor de proveedores y las preferencias, que
  no existen en `__config_main_frames()`). `content_frame` estrena `fg_color=Theme.BG`.
- `change_appearance_mode_event()` pasa de 10 líneas recorriendo widgets a **una**: con tuplas
  `(claro, oscuro)` el tema lo cambia CustomTkinter solo.
- Métodos nuevos del hub para las fases siguientes: **`refresh_sidebar_counts()`** (llámalo tras
  guardar o quitar un anime) y **`set_active_sidebar_destination()`** (para la navegación que no
  viene de un clic — el arranque y la recarga de proveedor).
- ✅ El `# TODO:` de `main_window.py:32` **está cerrado**: la ventana se titula «Mi Biblioteca» y
  ninguna pestaña lleva ya la palabra «Anime». Quedan **4** `TODO` en `src/` (2 en `jkanime.py`,
  2 en `anime_window.py`).
- Verificado: sí · app real + las tres baterías del scratchpad. Las **11** comprobaciones de
  `smoke_provider.py` cubren el punto del checklist que faltaba: pin fijar/desfijar (icono **y** fila
  en BD), cambio de proveedor que **no** escribe en BD y pone el pin en gris, y el fondo `CARD` del
  ítem activo aguantando el salto claro↔oscuro sin reconfigurar nada.
- Pendiente que deja: nada.

### Fase 1 · Paso 1.4 — `Sidebar`          (2026-08-20)
- Ficheros: `src/gui/components/__init__.py` y `sidebar.py` (nuevos),
  `src/utils/buttons/utilsButtons.py`, `src/utils/utils.py`,
  `src/dataPersistence/userPersistence.py`, y **una línea** en cada una de las 6 vistas (solo la
  etiqueta).
- `Sidebar` (`CTkFrame`) sustituye a los 6 `SidebarButton` sueltos y al pie. 6 destinos con icono +
  etiqueta + contador, activo con fondo `CARD` y barra de 2 px `ACCENT`, plegado a 84 px con globo
  de contador. Proveedor con pin y apariencia **con el mismo comportamiento de antes**, solo
  cambia el aspecto.
- `SidebarButton` deja de ser `CTkButton` (ver Decisiones). `update_icon()` desaparece: el icono es
  un único `CTkImage` con `light_image`/`dark_image` y lo cambia CustomTkinter.
- `load_dual_image()` nuevo en `utils/utils.py`.
- `UserSettingKey.SIDEBAR_COLLAPSED` + `get_sidebar_collapsed()` / `set_sidebar_collapsed()`.
  Sin migración: la tabla es clave/valor. Persistido como `"1"`/`"0"`.
- 🔴 **Dos fallos encontrados y corregidos por el camino**, los dos silenciosos: el ancho robado por
  la rejilla (219 en vez de 224) y —el gordo— los seis destinos **en blanco** porque un `CTkFrame`
  sin hijos conserva su alto por defecto de 200. Los dos están en Decisiones porque van a repetirse.
- Verificado: sí · **38 comprobaciones** de la barra (medidas, contadores, activo, plegado ida y
  vuelta, persistencia, proveedor, apariencia, ocultar/mostrar) y **24** de las vistas, todas en
  verde; más **captura de la ventana real** desplegada y plegada.
- Pendiente que deja: nada.

### Fase 1 · Paso 1.3 — Caché de pósters a 248 × 372          (2026-08-20)
- Ficheros: `src/utils/utils.py`
- Qué cambia: constante nueva `POSTER_CACHE_SIZE = (248, 372)` y los **tres** `.resize((130, 185))`
  pasan a usarla (`download_anime_poster_by_status`, `download_animes_poster._download_single`,
  `download_images_progress._download_single`). `load_image()` conserva su `(130, 185)` por defecto
  —es el tamaño **pintado**, y las 6 vistas siguen siendo las de hoy— y `get_anime_image()` su
  `(195, 275)`, con su `size=` explícito intacto (trampa 17/16).
- Caché: las 6 carpetas de `resources/images/` se movieron al scratchpad y **se regeneraron los 39
  pósters de las 4 carpetas de estado** a 248 × 372 desde `poster_url`. **39 OK, 0 fallidos.**
- ⚠️ `watching/` tenía **7** ficheros y ahora tiene **1**: la BD solo declara un anime con
  `is_watching = 1`. Los otros 6 eran huérfanos de estados anteriores. La caché queda **más**
  alineada con la BD que antes, no menos.
- ✅ De paso desaparece el huérfano `Chi.` (0 bytes) que provocaba el aviso de cada arranque
  (trampa 17).
- **`DB_Animes.db` NO se tocó**: abierta con `file:...?mode=ro`; mtime sigue en 2026-08-17 21:04.
- ⚠️ La BD tiene **29 filas**, no las 28 que dicen `CLAUDE.md` y el README del plan. Solo lectura,
  nada que corregir aquí, pero **la fase 5 debe contar 29 antes y después**.
- Verificado: sí · script del scratchpad; muestra comprobada con PIL → `(248, 372)`.
- Pendiente que deja: nada.

### Fase 1 · Paso 1.2 — `src/gui/theme.py`          (2026-08-20)
- Ficheros: `src/gui/theme.py` (nuevo)
- Qué trae: clase `Theme` con los 13 tokens de color de `DISENO.md` §1 en tuplas `(claro, oscuro)`,
  los 4 pares de píldora de estado, los 10 roles tipográficos de §2 como tuplas
  `(tamaño, negrita, mono)` y `Theme.font(size, bold, mono)` con caché. Clase `Metrics` con las
  medidas de §3.
- `WARN` es el `("#B45309", "#FBBF24")` que ya usaba `anime_window.py:441`, no uno nuevo.
- Las fuentes se construyen dentro de `font()`, nunca a nivel de módulo: un `CTkFont` necesita que
  ya exista la raíz de Tk.
- Verificado: sí · import + construcción de fuentes con una raíz CTk real (familia, tamaño, peso,
  caché y la monoespaciada).
- Pendiente que deja: nadie lo usa todavía. Lo estrena el paso 1.5.

### Fase 1 · Paso 1.1 — Orientación y rama          (2026-08-20)
- Ficheros: ninguno.
- Rama: **ya existía** `feature/ui-redisign` con el plan commiteado en `6377b92`. No se crea
  `feature/rediseno-ui` (ver Decisiones). `src/` estaba intacto respecto a `4f9e429`.
- Foto del «antes»: ✅ **la app arranca entera** — valida las dos BD, aplica el proveedor fijado
  (`animeav1`), baja los pósters y pinta la portada.
- Verificado: sí · `python -u src/app.py`, log en el scratchpad.
- Pendiente que deja: nada.
