# Estado del rediseño

> Este fichero es la memoria del plan entre sesiones. Lo lee y lo escribe `/fase`.
> Si contradice al árbol de trabajo, **gana el árbol**: `git log --oneline` y `git status` mandan.

| | |
|---|---|
| **Fase actual** | — · **el plan está terminado**: las 9 fases en ✅ |
| **Situación** | ✅ **plan cerrado el 2026-08-21**. Las 9 fases terminadas y verificadas con la app real |
| **Último paso completado** | Fase 9 entera, commiteada en `7606def` |
| **Siguiente paso** | Ninguno de este plan. Lo que recomienda el cierre (§ *Qué queda*, al final): **sacar la petición de servidores del hilo de Tkinter** |
| **Rama** | ✅ `feature/ui-redisign` (**no** `feature/rediseno-ui`: ya existía, ver Decisiones) |
| **Base** | `bd25742` (fase 1) → fases 2 a **9** encima, en `feature/ui-redisign`. El plan partió de `6377b92`, no de `4f9e429`. ⚠️ **La rama no se ha fusionado con `main`**: eso lo decide el usuario |
| **Commits** | automáticos (uno al cerrar cada fase) |
| **Actualizado** | 2026-08-21 |

---

## Tablero

| # | Fase | Situación | Commit | Verificada |
|---|---|---|---|---|
| 1 | Cimientos | ✅ terminada | `bd25742` | ✅ app ejecutada y **mirada** (desplegada y plegada) + 73 comprobaciones |
| 2 | Nuevos lanzamientos | ✅ terminada | `ef9f4d4` | ✅ app ejecutada y **mirada** (4 arranques + recorrido de las 6 vistas) + 48 + 14 comprobaciones |
| 3 | Viendo | ✅ terminada | `3198f12` | ✅ app ejecutada y **mirada** (3 arranques reales + recorrido de las 6 vistas + ficha abierta por las 3 vías) + 42 + 29 comprobaciones |
| 4 | Pendientes | ✅ terminada | `3b06dd0` | ✅ app real ejecutada y **mirada** (3 arranques: portada, Pendientes y Pendientes con orden y hover + recorrido de las 6 vistas) + 61 comprobaciones sobre **copia** de la BD |
| 5 | Favoritos | ✅ terminada | `580333b` | ✅ app real ejecutada y **mirada** (2 arranques: portada, Favoritos, calificar con el ratón, orden guardado y recorrido de las 6 vistas) + **59 comprobaciones sobre copia** de la BD + **15 sobre la real** + **56 con CTk real** |
| 6 | Finalizados | ✅ terminada | `bfbad7d` | ✅ app real ejecutada y **mirada** (4 arranques: Finalizados en oscuro y en claro, Favoritos, ficha abierta con clic sintético + recorrido de las 6 vistas) + **22 comprobaciones** sobre la app en marcha + **10** de casos límite del sello + **3** de los glifos, **mirados ampliados x10** |
| 7 | Buscar | ✅ terminada | `b68b5b4` | ✅ app real ejecutada y **mirada** (2 arranques, **11 capturas**: buscar por texto, dos géneros, «Más géneros» desplegado, paginador con 50 páginas, página 2, fallback a JKAnime, tema claro y cambio de vista en vuelo) + **51 comprobaciones** de la vista con CTk real + **28** de `GenreChips` |
| 8 | Ficha del anime | ✅ terminada | `5bf0b3f` | ✅ app real ejecutada y **mirada** (3 arranques, **8 capturas**: portada, Viendo, ficha de One Piece, servidores desplegados, barra plegada, tema claro, pendiente de AnimeFLV e identidad partida forzada con JKAnime) + **93 comprobaciones** con CTk real sobre **copia** de la BD, con red de verdad en servidores y migración |
| 9 | Cohesión | ✅ terminada | `7606def` | ✅ app real ejecutada y **mirada** (4 arranques: biblioteca **vacía** y **copia de la real**, en oscuro y en claro, **54 capturas** de las 7 vistas × 2 temas × 2 estados de barra) + **116 comprobaciones** con CTk real + **`pyinstaller` compilado y el `.exe` arrancado** + `python src/app.py` sin un solo `Traceback` |

**Situación**: ⬜ no empezada · 🟡 en curso · ✅ terminada · ⚠️ terminada sin verificar · ❌ revertida

### Qué quedó sin verificar

Lo que no se ha podido ejecutar en cada fase, para que nadie lo dé por probado.

| Fase | Sin verificar | Por qué |
|---|---|---|
| 2 | **El gesto completo de «marcar el episodio 3 en la ficha, cerrar y reabrir»** | Hace falta un clic humano en la ficha. Se probaron **las dos mitades por separado**: `push_last_watched_id()` con 14 comprobaciones sobre una `DB_user.db` temporal (incluida la supervivencia al reinicio), y el pintado de la banda en la app real con la preferencia poblada con tres animes de la biblioteca. **La costura entre ambas —la llamada de `__toggle_episode_switch`— está leída, no ejecutada** |
| 2 | El **hover** de las celdas y de las tarjetas | No hay puntero que pasar por encima |
| 3 | El hover **con un ratón de verdad** | Sigue sin haber puntero que mover. Sí se ejecutó el mecanismo entero: se emiten `<Enter>`/`<Leave>` **sobre el canvas interno**, que es lo que toca el ratón, y se comprobó que la píldora aparece, que el fondo cambia a `CARD_HOVER`, que pasar del marco a un hijo **no** lo apaga y que la fila no se mueve |
| 3 | El caso **literal** del checklist: «un anime guardado desde AnimeFLV abierto con AnimeAV1 seleccionado» | ⚠️ **`one-piece-tv` ya no existe en la BD**: la fila de One Piece es hoy `one-piece` con `provider_id = animeav1`, así que ese caso concreto no se puede reproducir. Se probó **la misma mecánica**: fila de AnimeAV1 abierta con **JKAnime** seleccionado en el desplegable → desviación → se re-localiza por título (`similitud 1.00`) → la ficha sale con el ⚠ y «En tu biblioteca: AnimeAV1» → **29 filas antes y 29 después, idénticas**. Se eligió JKAnime y no AnimeFLV porque AnimeFLV lleva tiempo sin servir datos |
| 3 | La **suma de resultados de la búsqueda web** | Se probó con el proveedor devolviendo vacío —que es exactamente el caso «sin conexión»— y con las tres consultas llegando al proveedor. Que un resultado web **añada** un anime que el título guardado no encuentra sigue sin ejecutarse: haría falta un alias real («Solo Leveling») entre los animes que estás viendo, y hoy solo hay One Piece |
| 4 | El **hover con un ratón de verdad** | Tercera fase seguida sin puntero. Se ejecutó el mecanismo entero (el resaltado y la píldora «Empezar» aparecen, y la fila no cambia de ancho) y **se ha mirado en la app real**: la captura del tercer arranque lleva la primera fila resaltada y su píldora encendida |
| 4 | **«Empezar» sobre la biblioteca real** | La ficha de la fase mandaba probarlo en `DB_Animes.db` y deshacerlo después; la **regla 2 de `/fase`** dice que solo la fase 5 escribe ahí, y gana. El flujo se ejecutó **entero y de verdad** sobre una **copia** (`Given: Uragawa no Sonzai` movido de pendientes a viendo: 29 filas antes y después, flags correctos, ficha abierta, póster encolado). Sobre la real solo se ha **mirado** la vista: hash y mtime de `DB_Animes.db` **idénticos** al terminar |
| 4 | El desplegable de orden **abierto con el ratón** | Los tres criterios se ejecutaron por su `command`, que es lo que el desplegable llama, y dos de ellos se han mirado en la app real. Desplegar la lista en sí no se ha hecho |
| 5 | El desplegable de orden **abierto con el ratón** (otra vez) | Su lista es un *toplevel* aparte de la ventana principal, así que ni el clic sintético lo abre ni `PrintWindow` lo captura. Se ejercitó **todo lo demás**: el `command` con los dos criterios (56 comprobaciones con CTk real), y en la **app real** se comprobó el extremo que sí importa —que la preferencia **guardada** se aplica al entrar en la pestaña: con `favourites_order = title` escrito en `DB_user.db`, la pestaña sale con «Título (A-Z)» puesto y la rejilla alfabética |
| 5 | El **hover** de las celdas | Cuarta fase seguida sin puntero que pasear. Las estrellas no tienen estado de hover —solo cursor de mano—, así que aquí no hay mecanismo que probar |
| 6 | Los **botones del paginador pulsados con el ratón** | Se ejecutó su `command` (`__go(2)`), que es lo que el botón llama, y la página 2 se comprobó entera: 6 celdas y «Mostrando 13-18 de 18». Pulsar el botón en sí, no |
| 6 | El **hover** de las celdas | Quinta fase seguida sin puntero. La rejilla **no tiene** estado de hover —solo cursor de mano, comprobado: `hand2`—, así que aquí no hay mecanismo que probar |
| 6 | El sello sobre un finalizado **sin lista de episodios** en la biblioteca real | No existe esa fila hoy: los 18 finalizados tienen lista. La rama se probó con `AnimeRecord` sintéticos (6 casos, incluidos «más vistos que episodios» y «sin lista pero con vistos»), no sobre la BD |
| 7 | El desplegable de **orden abierto con el ratón** (tercera fase seguida) | Su lista es un *toplevel* aparte y `PrintWindow` no lo captura. Sí se ejecutó su `command` con los dos criterios y se comprobó que el valor viaja al proveedor (`search_animes_by_genres_and_order(..., order="title", ...)`). El de **apariencia** sí se abrió con el ratón, capturando la **pantalla entera** en vez de la ventana: es la receta si hace falta otra vez |
| 7 | El **hover** de las fichas de género y de las celdas | Sexta fase seguida sin puntero. Las fichas usan el `hover_color` de `CTkButton`, que es de la librería |
| 7 | Un resultado sellado **abierto con el ratón**, comprobando que la ficha sale como guardada | Se ejecutó `__on_anime_click()` con el `AnimeWindowViewer` sustituido y se comprobó que **recibe el `AnimeRecord` correcto** (`ore-dake-level-up-na-ken`, la fila de AnimeFLV, desde un resultado de AnimeAV1). Abrirlo de verdad y mirar la ficha, no: es la vista que rehace la **fase 8** |
| 7 | La **búsqueda por texto paginada** | AnimeAV1 devuelve las búsquedas por texto **en una sola página** (`last_page = 1`, 14 resultados) y JKAnime igual (22). El paginador se probó con la búsqueda por géneros, que sí pagina: **50 páginas de 20** |
| 6 | El **añadido de la búsqueda web** en esta pestaña | Igual que en las fases 3 y 5: el proveedor no devolvió nada para las consultas probadas, que es el caso «sin conexión». Que un resultado web **sume** un anime que el título guardado no encuentra sigue sin ejecutarse en ninguna vista |
| 8 | **Todo lo que escribe, sobre la biblioteca real** | Séptima vez que se aplica la receta de la fase 4, y aquí la ficha de la fase pedía lo contrario («cambiar los 4 estados y devolverlos a como estaban» en `DB_Animes.db`); manda la **regla 2 de `/fase`**. Los cuatro estados, el marcado de episodios y la migración se ejecutaron **enteros y de verdad** sobre una copia (30 filas antes y después). Sobre la real solo se ha **mirado**: `sha256 24288986ac92…` **idéntico** tras los tres arranques y las ocho capturas |
| 8 | El **hover** de las filas de episodio con un ratón de verdad | Séptima fase seguida sin puntero. El mecanismo es el mismo de `AnimeRow` —incluido `__pointer_inside()`, que evita el parpadeo al pasar del marco a un hijo— y se ha visto funcionando el **resaltado permanente** de la fila desplegada, que usa la misma vía (`set_expanded`) |
| 8 | El botón «Actualizar a …» **pulsado con el ratón** | La migración se ejecutó entera por su método (`__confirm_and_migrate`, con los diálogos sustituidos por «sí»): la fila se reapunta, conserva los 5 episodios vistos y las cuatro categorías, anota el proveedor nuevo y **no duplica**. Pulsar el botón en sí, no; sí se ha **mirado** en la captura 08, con el ⚠ ámbar al lado |
| 8 | Marcar un episodio **desde la ficha, cerrar la app y reabrirla** | Es lo que quedó suelto de la fase 2 y sigue suelto. Las dos mitades están ejecutadas —`push_last_watched_id()` recibe el `persistence_anime_id` correcto y la preferencia queda escrita en la `DB_user.db` de copia— pero la costura con el arranque siguiente no se ha recorrido de una vez |

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
| 4 | ✅ **`AnimeRow` NO se bifurcó**: la fase 4 costó **un** parámetro, `meta_text`, que **sustituye** al proveedor en la columna derecha. Pendientes lo usa para «N episodios · Proveedor». Las fases 5-7 tienen ahí un sitio donde poner lo suyo sin tocar el componente |
| 4 | **Una fila sin lista de episodios no es «corta», es desconocida**: va **al final en los dos sentidos** de la duración. Encabezar «más cortos primero» con lo que no se sabe cuánto dura es lo contrario de lo que se ha pedido. Pasa con las filas guardadas sin llegar a abrir su ficha |
| 4 | **El orden elegido NO se persiste.** Vive en memoria: no está entre las tres preferencias que `DISENO.md` §8 manda guardar, y añadir una fila a `USER_SETTINGS` por esto es ampliar la fase por mi cuenta. Si se quiere, es un miembro más de `UserSettingKey` |
| 4 | 🔴 **Los contadores de la barra salen de las listas cacheadas del hub, y esas listas solo se llenan al arrancar.** «Empezar» relee `pending_animes` y `watching_animes` **antes** de `refresh_sidebar_counts()`; sin eso el número no se movía. ⚠️ **La ficha sigue sin hacerlo**: cambiar un estado desde `anime_window.py` no repinta los contadores hasta el siguiente arranque. Es de la **fase 8** |
| 4 | **La descarga del póster de «Empezar» va en hilo daemon.** Es una petición HTTP y quien la lanza es el hilo de Tkinter. Nadie la espera: `find_cached_poster_path()` recorre las seis carpetas, así que hasta que caiga en `watching/` la imagen se sigue encontrando en `pending/` |
| 4 | **«Empezar» abre la ficha, no el episodio 1.** Misma decisión que la píldora «Episodio N →» de la fase 3 y por el mismo motivo: abrir por un episodio concreto es de la **fase 8**, la que rehace la lista |
| 4 | **Los 113 px de la fila de pendientes incluyen el separador** (112 de cuerpo + 1 de línea). La última fila de la lista, que va sin separador, mide 112. Vale igual para los 132 de la fila de «Viendo» |
| 4 | **Verificar una fase que escribe en la biblioteca se hace sobre una copia.** La ficha de la fase 4 pedía probar «Empezar» en `DB_Animes.db` y deshacerlo; la regla 2 de `/fase` lo prohíbe fuera de la fase 5. Se apunta la persistencia a una copia (`persistence.path_db` + `SqlUtils`) y se comprueba al final que el hash de la real no ha cambiado. **Receta reutilizable para cualquier fase futura** |

| 5 | **La escala de calificación es un entero de 0 a 10**, dos puntos por estrella, y **`NULL` no es 0**. Guardar los medios puntos como enteros evita flotantes en SQLite y en la comparación del orden; distinguir «sin calificar» de «cero estrellas» es lo que permite mandar las filas sin calificar **al final** del orden por calificación. `AnimeRecord.RATING_MAX` es el tope |
| 5 | **La única forma de dejar sin calificar algo ya calificado es volver a pulsar la misma calificación.** No hay botón de borrar: el gesto de repetir es lo que uno prueba antes de buscarlo. Si una fase futura añade un menú contextual a la celda, ahí es donde iría el «Quitar calificación» explícito |
| 5 | 🔴 **Calificar NO reordena la rejilla.** La celda se actualiza sola y el anime se queda donde estaba, aunque el orden sea por calificación: si la lista se recolocara bajo el cursor, la segunda estrella se pulsaría sobre otro anime. El orden se aplica al pintar la vista y al cambiar el criterio. Vale para cualquier control que edite el criterio por el que está ordenada su propia lista |
| 5 | **El pie del proveedor se queda en la celda de favoritos**, aunque el diseño maquetado no lo pinte ahí: `DISENO.md` §6 pide el proveedor **siempre** en las vistas de biblioteca y es la especificación la que manda. La fase 6 se encuentra la misma disyuntiva en finalizados; que haga lo mismo |
| 5 | **`StatusPill` en favoritos dice qué *más* es el anime**, nunca «Favorito». La ficha de la fase lo daba por estrenado aquí pero ningún paso lo colocaba: el sitio es el sello superpuesto al póster (`badge` + `badge_colors`, que `PosterGrid` ya sabía pintar desde la fase 2), y el dato es el estado excluyente de la fila. Repetir «Favorito» en las diez celdas sería el dato duplicado que prohíbe `DISENO.md` §6. **La fase 6 lo reutiliza** para el sello «Finalizado» |
| 5 | **`PosterGrid` gana `extra_builder`, no una subclase.** La celda numera sus filas sobre la marcha: si una vista no pone fila libre, el pie sube y no queda hueco. El widget que devuelve el constructor **no hereda el clic de la celda** —los eventos de Tk no burbujean—, que es justo lo que hace que pulsar una estrella no abra la ficha |
| 5 | **Las estrellas se dibujan con PIL en tiempo de ejecución**, no son PNG en `resources/`. Un polígono de 10 vértices a 8x reducido con LANCZOS, y el medio punto es un rectángulo recortado con la máscara de ese polígono. Es la misma salida que se eligió para el pin, y aquí además evita la deuda **B11**: estos iconos son nuestros. `CTkImage(light_image=…, dark_image=…)` resuelve el tema sin reconfigurar nada |
| 6 | 🔴 **El sello va arriba a la IZQUIERDA y con fondo oscuro, no con el color pastel del estado.** Es lo que dice el diseño (`.mark`: `top:9px;left:9px`, `rgba(10,12,16,.78)`, texto blanco y el color del estado **solo en el glifo**) y es lo único que se lee sobre una carátula clara: la verificación de la fase pide justo comprobar la legibilidad en tema claro, y un `FIN_BG` (`#E3F3EA`) sobre un póster blanco no la pasa. Tokens nuevos `Theme.BADGE_BG` / `BADGE_INK`, opacos porque **Tk no sabe pintar un fondo con alfa** |
| 6 | **`badge_colors` conserva su firma**, así que «Favoritos» sigue con su píldora pastel de la fase 5 sin tocar el fichero: la fase 6 tiene «las otras vistas» en su *No toca*. Solo hereda el cambio de esquina. ⚠️ **Queda una incoherencia visible**: en Favoritos el sello pastel sobre pósters claros se lee mal, y ahora está en la esquina más brillante. **Es trabajo de la fase 9** (repaso claro/oscuro): pasar `favouriteAnimes.py` al sello por defecto es borrar su `badge_colors=` y añadir `badge_icon=StatusPill.icon(status)` |
| 6 | **El glifo del sello lo sirve `StatusPill.icon()`**, dibujado con PIL como las estrellas y el pin. Están los **tres estados excluyentes** (ojo, ✓, lista) y no solo el ✓ que usa esta fase: son exactamente los que `other_status()` puede devolver y los que la fase 7 va a pedir, así que dejar dos sin dibujar obligaría a reabrir el módulo. «Favorito» devuelve `None` a propósito |
| 6 | ⚠️ **El glifo se tiñe con la variante OSCURA del color del estado en los dos temas.** El sello es una superficie oscura siempre —va sobre la carátula, no sobre el fondo de la app—, así que `FIN_TXT[0]` (un verde oscuro) desaparecería justo en tema claro. Vale para cualquier cosa que se pinte sobre `BADGE_BG` |
| 6 | **El hueco entre el glifo y el texto va dentro del propio dibujo** (`_ICON_GAP`). Tk pega imagen y texto cuando una etiqueta lleva las dos (`compound="left"`) y `CTkLabel` no expone su padding interno; sin ese margen transparente el ✓ toca la cifra |
| 6 | **Un sello sin lista de episodios dice «Finalizado», no «0 / 0».** Pasa con las filas guardadas sin llegar a abrir su ficha: ahí no hay «totales» que enseñar y el cero doble parecería un fallo de la vista. Con lista, los números son **los reales y sin corregir**, aunque falten episodios por marcar |
| 7 | **«Buscar» no lleva `ViewHeader`.** Es la única vista sin título: el diseño (`DISENO-VISUAL#buscar`) pone el campo de 620 px arriba del todo y nada más, y con «Buscar» ya marcado en la barra lateral un título que repitiera la palabra sería el dato duplicado que prohíbe `DISENO.md` §6. El campo **es** la cabecera |
| 7 | **El botón «Buscar» se queda, aunque el diseño no lo pinte.** La maqueta enseña la caja sola con el cursor dentro; quitar el botón dejaría la búsqueda accesible **solo con Enter**, que es una función menos que hoy. Es la única desviación deliberada respecto de `#buscar` |
| 7 | 🔴 **Texto y géneros son dos búsquedas distintas y no se combinan: manda el último gesto.** `search_animes_by_query()` y `search_animes_by_genres_and_order()` son métodos distintos del contrato y ninguno acepta lo del otro. Buscar por texto **vacía las fichas** y tocar una ficha (o el orden) **vacía el texto**, para que lo que se ve en pantalla sea exactamente lo que se ha pedido. El diseño los pinta a la vez, pero la capa de proveedores no lo permite y **la fase no toca `APIs/`** |
| 7 | **Tocar una ficha de género busca en el acto**, sin botón de aplicar. Es lo que implica una ficha: si hubiera que confirmar, valdría más el acordeón que sustituye. Las peticiones no se solapan porque cada una lleva su número de generación y **solo pinta la última** |
| 7 | **`Pager` gana un segundo modo en vez de una subclase**: `set_pages(última_página, página)` para cuando **trocea el proveedor**. `set_total()` sigue igual para las otras cinco vistas. En el modo nuevo no hay `slice_bounds()` que valga y el total de resultados **no se sabe** —el contrato devuelve la última página, no cuántos hay—, así que el pie dice «Página 2 de 50» y no «Mostrando 21-40 de 1000», que sería inventárselo |
| 7 | **De quién son los resultados se lee del propio resultado, no del desplegable.** El manager estampa el `provider_id` en cada `AnimeInfo` al responder (`__stamp_provider`), así que la línea dice el sitio de verdad cuando entra el fallback **sin tocar `APIs/`** ni añadir un `..._with_provider` a los wrappers de búsqueda. ✅ Visto en la app: una consulta sin resultados en AnimeAV1 salió como «1 resultado en **JKAnime**» |
| 7 | **El sello reutiliza `find_saved_duplicate()` de `anime_window.py`** (umbral 0,9), no una comparación propia. Sellar un resultado y avisar al guardarlo son **la misma pregunta**: con dos umbrales distintos, la rejilla podría no sellar algo que el guardado sí frena como duplicado. Primero se cruza por *slug* (exacto) y solo si falla, por título |
| 7 | 🔴 **Un resultado sellado abre la ficha con `anime_record=`.** Es la [trampa 21](../docs/10-invariantes-y-trampas.md) y esta vista la tenía abierta: el cruce que decide el sello es el mismo que da la identidad de persistencia, así que ya no cuesta nada. Sin él, marcar un estado sobre un anime guardado desde otro proveedor creaba una **fila duplicada** |
| 7 | **El texto de las fichas sale de `refactor_genre_text(genre.name)`, no de `.value`.** Los `value` del enum son *slugs* sin tildes (`ciencia-ficcion`) y la interfaz va en español con tildes. El acordeón usaba `.value` y pintaba «Accion» |
| 7 | **Las fichas se colocan con `place()`, no con `grid()`.** Las columnas de una rejilla son **comunes a todas las filas**: envolver texto con `grid` hace que la tercera ficha de cada fila comparta ancho —el de la más larga— y la fila se abra en huecos. Con `place()` el marco no pide alto, así que `show()` se lo fija. Vale para cualquier fila que envuelva por ancho |
| 7 | **Mientras se busca no hay GIF, hay una línea de texto.** La vista vieja pintaba el GIF de carga a 300 × 300; el diseño no lo contempla y ese GIF es de la deuda **B11** (origen desconocido). Ahora la línea de resultados dice «Buscando animes…» y la rejilla se vacía |
| 8 | 🔴 **La ficha devuelve a cero los pesos de filas y columnas del `content_frame`.** Ese marco lo comparten las siete vistas y su configuración de rejilla **sobrevive al `clear_frame()`**: la ficha vieja repartía peso entre cuatro columnas y cuatro filas, y una columna con peso **y sin widgets también recibe el espacio sobrante**, así que la vista siguiente pintaba en una columna 0 estrecha. Cualquier vista que reparta peso tiene que deshacerlo |
| 8 | 🔴 **Un `CTkFrame` con `fg_color="transparent"` no pinta su borde.** No dibuja su rectángulo, y con él se va también el `border_width`: las fichas de género salían como texto suelto. Y aunque se le dé color, **una etiqueta transparente encima lo tapa** —hermana y del mismo tamaño lo borra entero; hija con el alto por defecto (28 > 26) le come los tramos rectos y deja solo las esquinas—. La receta que funciona: marco con `fg_color=BG` + borde, y la etiqueta **dentro**, más baja que él |
| 8 | 🔴 **CustomTkinter rechaza `width=` y `height=` dentro de `place()`** con un `ValueError`, al revés que Tk pelado: el tamaño se le da al construir el widget. Lo tropezó el separador de 1 px de `EpisodeRow` |
| 8 | **El `wraplength` de la sinopsis se resuelve recalculando en `<Configure>`**, no cambiando de contenedor (la ficha de la fase dejaba las dos puertas abiertas). La columna de información se ata a un `<Configure>` con umbral de 8 px y de ahí salen el envuelto del título, el de la sinopsis y el reenvuelto de los géneros. Es lo que cierra la [trampa 22](../docs/10-invariantes-y-trampas.md): ya no hay ningún número calculado a mano sobre el ancho del `content_frame` |
| 8 | **La sinopsis se corta a 74 caracteres de ancho, no al ancho disponible.** Es lo que pide el diseño (`.syn`: `max-width:74ch`) y por eso plegar la barra lateral **no** la ensancha: con 1 356 px la línea sería incómoda de leer. Un «ch» se mide con `font.measure("0")` |
| 8 | **Los cuatro botones de estado tienen un solo `command`, `__toggle_status()`**, que mira cómo está la fila y llama al `add_to_*` o al `remove_from_*` de siempre. Los seis métodos públicos no cambian; lo que desaparece es el botón que cambiaba de texto para decir cuál de los dos tocaba |
| 8 | **Los cuatro booleanos sueltos (`__anime_is_favourite`…) pasan a ser un diccionario `__status_state`.** Los botones se pintan recorriéndolo, así que encender uno de los tres excluyentes y apagar los otros dos es una vuelta de bucle (`__set_exclusive_status`) en vez de tres asignaciones repetidas en cada método |
| 8 | ✅ **La ficha ya refresca los contadores de la barra lateral**, que era la deuda que dejó la fase 4. Relee las cuatro listas cacheadas del hub y llama a `refresh_sidebar_counts()` después de cada cambio de estado: sin releerlas, la barra seguía diciendo lo de antes hasta el siguiente arranque |
| 8 | **Las filas de episodio van en las posiciones PARES de la rejilla y los servidores en la impar de debajo.** Desplegarlos no empuja nada ni obliga a repintar la lista, y la fila impar mide cero mientras está vacía. La lista vieja los metía en `current_row + 1`, que era la fila del episodio siguiente |
| 8 | **El botón de orden dice el orden que llega del proveedor**, en vez de decir siempre «Mayor a menor». No es el mismo en todos —AnimeAV1 sirve ascendente y AnimeFLV descendente—, así que el control mentía en la mitad de las fichas. **La lista no se reordena al abrir**: el corte de 25 sigue siendo exactamente el que era ([trampa 8](../docs/10-invariantes-y-trampas.md)) |
| 8 | **Cuando hay más de 25 episodios, la lista lo dice** («Se muestran 25 de 1 174 episodios · usa "Ir al episodio…" para llegar a los demás»). El corte es viejo y sigue en pie; enseñarlo es lo que convierte el buscador de al lado en la salida evidente en vez de en un control que nadie sabe para qué está |
| 8 | ⚠️ **La petición de servidores sigue en el hilo de Tkinter.** Es lo que hacía la ficha vieja y la fase solo recoloca, así que no se ha movido; lo único que se ha añadido es el cursor de espera, porque si no la ventana se queda quieta un par de segundos sin explicar por qué. **Es el último sitio de la GUI que sale a la red desde el hilo de la interfaz** — candidato claro para la fase 9 |
| 8 | **`EpisodeRow` sustituye a `utilsButtons.EpisodeButton`**, que era un botón de ancho completo con «\<título del anime\> - Episodio N» repetido veinticinco veces. Con `SearchButton`, `ApplyFiltersButton` y `AccordionFilterButton`, **son cuatro clases huérfanas** en `utilsButtons.py` para la fase 9 |
| 8 | **El póster de la ficha se carga con `load_rounded_image()` desde la caché**, como las seis vistas, y solo cae en `get_anime_image()` —que sale a la red— si el anime todavía no tiene fichero en disco. Es la misma decisión de la fase 2 aplicada al último sitio que quedaba con esquinas cuadradas |
| 8 | ✅ **Ya no queda ni un color literal en `src/` fuera de `theme.py`.** El `WARN` del aviso de identidad partida era el último (`("#B45309", "#FBBF24")` a mano en `anime_window.py`); ahora es `Theme.WARN`. `git grep -nE "#[0-9A-Fa-f]{6}" -- src/` devuelve **vacío** fuera del módulo de tokens, así que ese punto del paso 9.2 ya está cerrado |
| 9 | 🔴 **«Probar con otro proveedor» no se puede ofrecer, y la ficha de la fase lo pedía.** `call_with_fallback()` recorre **todo** el registro cuando el elegido devuelve vacío, así que una rejilla de «Buscar» sin resultados significa que **ya se han probado los tres**. El botón sería repetir lo que la aplicación acaba de hacer sola. En su lugar se ofrece lo único que cambia el resultado —«Borrar la búsqueda» o «Quitar los filtros»— y la pista dice la verdad: «Han respondido los 3 proveedores y ninguno lo tiene» |
| 9 | **Un `EmptyState` son cuatro piezas, no tres**: icono, frase, **pista** y acción. La pista es lo que llevaban los `CTkLabel` viejos en su segunda línea («Marca uno con el corazón desde su ficha»), y perderla al pasar al componente habría sido cambiar una explicación por un botón en vez de sumarlos |
| 9 | **`EmptyState` recibe el icono ya construido**, no un nombre. Así los cuatro estados de biblioteca reutilizan `StatusPill.icon()` —el mismo glifo que llevan sus sellos— y el módulo solo dibuja los dos que no existían. `StatusPill.icon()` gana `gap=0` para que el glifo salga **cuadrado** cuando va solo y centrado |
| 9 | **La línea de estado de «Buscar» se queda en blanco cuando no hay resultados.** Lo dice el estado vacío, con su icono y su salida; repetirlo arriba sería el dato duplicado que prohíbe `DISENO.md` §6 |
| 9 | **Los cuatro PNG «light/dark» de viendo y pendientes se quedan sin usar, y el código comentado se retira.** No son un par claro/oscuro: **los dos dibujos de cada par son de tinta negra**, así que en tema oscuro el suyo sería invisible. El icono único funciona porque es bicolor —silueta negra y relleno blanco— y se lee sobre los dos fondos. Si alguna vez se quieren pares de verdad, hay que **redibujarlos**, que es justo la salida de la deuda B11 |
| 9 | **`utilsButtons.py` se queda con el nombre pero ya no tiene ni un botón.** Contiene el cruce por título, `SavedAnimeSearch` y el descriptor `SidebarButton`. Renombrarlo se deja fuera del plan a propósito: el rediseño es solo interfaz y esto vive en `utils/` |
| 9 | 🔴 **`badge_colors` desaparece de `PosterItem`.** «Favoritos» era el único que lo usaba —con el par pastel de la píldora, ilegible sobre una carátula clara y encima en la esquina más brillante desde la fase 6— y pasa al sello por defecto, como Finalizados y Buscar. El sello del diseño es **siempre** superficie oscura opaca con el color del estado solo en el glifo: no hay nada que elegir, y dejar el parámetro invitaba a repetir el error |
| 9 | **La navegación desde el contenido pasa por `MainWindow.navigate_to(etiqueta)`**, que delega en `Sidebar.navigate_to()`. Busca por la **etiqueta** del destino —la misma clave que ya usa `counter_providers`— y deja la barra marcando el destino, como si se hubiera pulsado allí. Devuelve `False` en vez de lanzar: un estado vacío no puede tumbar la aplicación por una cadena mal escrita |

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

### Fase 9 · Paso 9.5 — Documentación          (2026-08-21)
- Ficheros: **11 documentos** de `.claude/` — `docs/06` (**reescrito entero**), `docs/09` (§7
  reescrita entera), `docs/10` (+7 trampas), `docs/02`, `04`, `11`, `12`, `13`, `docs/README.md`,
  `CLAUDE.md`, y la fecha de cabecera sincronizada en los 14
- Verificado: **enlaces internos comprobados con un barrido: 0 rotos** de los ~450 que hay en
  `.claude/`. Los nombres de API citados (`get_sidebar_collapsed`, `push_last_watched_id`,
  `get_favourites_order`…) **cotejados uno a uno contra `userPersistence.py`**, no de memoria
- **`docs/06-gui-y-vistas.md` reescrito de cero** (516 → 297 líneas, y dice mucho más): mapa del
  árbol `gui/`, `theme.py`, las 11 fichas de componente, las 6 vistas en tabla, la ficha, y los
  apartados de tema y de concurrencia
- **`docs/09 §7` reescrita**: checklist de **7 vistas × 2 temas × 2 estados de barra**, con un
  apartado propio para los estados vacíos y cómo provocarlos sin tocar la biblioteca. Lo que decía
  de «Abrir filtro de animes», de los botones que cambian de texto y del GIF de búsqueda ya no
  existía
- **7 trampas nuevas en `docs/10`** (29-35), todas de CustomTkinter y de layout, en su apartado: el
  `CTkFrame` de 200 × 200, `wraplength`, los contadores cacheados, la rejilla que sobrevive a
  `clear_frame()`, **la pantalla de carga** (nace ya resuelta), el `<Leave>` mentiroso y
  `bind()` vs `event_generate()`. La **22** queda cerrada
- 🔴 **`docs/11 §5` decía lo contrario de lo que hay que hacer**: mandaba descomentar dos líneas
  para activar los iconos claro/oscuro. Reescrita: hay que **redibujarlos**, con la receta de PIL
  que ya usan diez glifos del proyecto. Y **§1b nueva**: añadir un componente compartido
- **`CLAUDE.md`**: sección de GUI rehecha, roadmap con **cinco puntos tachados** por el rediseño,
  el recuento de TODO corregido a **4**, `hiddenimports` a **30**, la caché de pósters a 248 × 372,
  y la nota de los iconos claro/oscuro invertida
- ✅ **Prueba de humo final**: `python src/app.py` desde la raíz — ventana en **1 s**, viva a los
  **41 s**, **sin un solo `Traceback` ni `invalid command name`** en la salida sin bufferizar, y
  `sha256 af3c89ec0665…` **idéntico** antes y después
- Pendiente que deja: nada. La fase está lista para cerrarse

### Fase 9 · Paso 9.4 — Limpieza, `.spec` y `.exe`          (2026-08-21)
- Ficheros: `src/utils/buttons/utilsButtons.py` (0.2 → 0.3, **361 → 205 líneas**),
  `MiBibliotecaAnime.spec`, `watchingAnimes.py`, `pendingAnimes.py`,
  `src/gui/components/sidebar.py`, `src/gui/anime_window.py` (una referencia caduca)
- Verificado: sí · **`pyinstaller MiBibliotecaAnime.spec` termina sin errores** y el `.exe`
  resultante **se lanza, abre su ventana en 1 s y sigue vivo a los 40 s**, con la carga terminada
- 🔴 **Cinco clases retiradas** de `utilsButtons.py`: `BaseButton`, `EpisodeButton`,
  `SearchButton`, `ApplyFiltersButton` y `AccordionFilterButton`. Ninguna la usaba nadie desde que
  las fases 3-8 estrenaron sus componentes. El módulo se queda con **tres piezas** —el cruce por
  título, `SavedAnimeSearch` y `SidebarButton`— y con un docstring que explica que el nombre del
  fichero es lo único que queda de lo que fue
- ✅ **`hiddenimports` completo y sin fantasmas**: **30** nombres. Auditado en las dos direcciones
  con AST — los 30 resuelven a un fichero real de `src/`, y **ningún módulo de `src/` queda sin
  declarar** salvo `app.py`, que es el script de entrada. Se añadieron `gui.theme` y los **11**
  `gui.components.*`
- ✅ **`datas` sigue llevando solo `resources/images/utils`**: el `.exe` creó **su propia**
  `DB_Animes.db` y `DB_user.db` dentro de `_internal/resources/DB/`, así que no distribuye la
  biblioteca del desarrollador ([trampas 18d y 18e](../docs/10-invariantes-y-trampas.md))
- **Los iconos `viendo_light/dark.png` y `pendientes_light/dark.png` NO se activan**: los dos
  dibujos de cada par son de **tinta negra sobre transparente**, así que como par (claro, oscuro)
  el del tema oscuro sería invisible. El icono único sí vale porque es bicolor. Se retiró el
  código comentado y se dejó el porqué en su sitio. **Los cuatro PNG siguen sin trackear en
  `resources/images/utils/`; no se han borrado** (son del usuario y son deuda **B11**)
- ✅ **Inventario de tareas pendientes: 4**, no 5 — `jkanime.py:191,264` y
  `anime_window.py:134,137`. El quinto que contaba el grep era un comentario de `sidebar.py` que
  hablaba de una ya cerrada; reescrito para que no falsee la cuenta. **`CLAUDE.md` dice 5 y hay
  que corregirlo en el paso 9.5**
- ⚠️ **La biblioteca real cambió durante la pausa de esta sesión, y no fue por los scripts**: 32
  filas frente a las 29 de `backups/DB_Animes_20260820_224943.db`, **3 añadidas y 0 borradas**, y
  de las 29 compartidas solo cambió *One Piece Film Red*, migrado de AnimeFLV a AnimeAV1. Es uso
  normal de la aplicación. La nueva referencia es `sha256 af3c89ec0665…`
- Pendiente que deja: nada del paso. Queda el 9.5 y el cierre

### Fase 9 · Pasos 9.2 y 9.3 — repaso claro/oscuro y barra plegada          (2026-08-21)
- Ficheros: `src/gui/sidebarButtons/favouriteAnimes/favouriteAnimes.py` (sello unificado),
  `src/gui/components/poster_grid.py` (0.2 → 0.3, `badge_colors` **retirado**),
  `src/gui/sidebarButtons/recentAnimes/recentAnimes.py` (dos imports muertos)
- Verificado: sí · **app real arrancada 2 veces —oscuro y claro— sobre una copia de la
  biblioteca real (15 favoritos · 2 viendo · 4 pendientes · 18 finalizados · 20 estrenos), con
  28 capturas miradas**: las 7 vistas × 2 temas × 2 estados de barra
- 🔴 **La biblioteca real no se toca**: `sha256 5e29fbc6a81e…` **idéntico** antes y después de
  los dos recorridos, y de los dos de la biblioteca vacía del paso 9.1
- ✅ **Ningún color literal fuera de `theme.py`**: `git grep -nE "#[0-9A-Fa-f]{6}" -- src/`
  devuelve **solo** `src/gui/theme.py` (los 20 tokens). Lo dejó cerrado la fase 8 y se ha vuelto
  a comprobar
- ✅ **Texto sobre `ACCENT`**: los **8** sitios que pintan `fg_color=Theme.ACCENT` usan
  `ACCENT_INK`, y los **4** que usan `ACCENT_SOFT` usan `ACCENT`. Auditado con AST, no a ojo
- 🔴 **El sello de «Favoritos» pasa al sello por defecto**, que era la deuda que dejó anotada la
  fase 6: fondo oscuro opaco y color del estado solo en el glifo. Mirado sobre las dos carátulas
  claras de la biblioteca (*Dragon Ball Daima* y *One Piece Fan Letter*): el pastel `FAV_BG` no
  se leía y ahora sí, en los dos temas. De paso **`badge_colors` desaparece de `PosterItem`**:
  ya no lo usaba nadie y dejarlo invitaba a repetir el error
- ✅ **Barra plegada en las 7**: medido el ancho real del contenido contra el disponible en cada
  vista. Desplegada, **1 200 / 1 200**; plegada, **1 340 / 1 340** (Buscar y la ficha se quedan
  28 px por debajo, que es su margen). **Nada se sale ni se recorta**
- ✅ **Sin imports muertos** en `src/`: barrido con AST sobre los 49 módulos. Solo aparecieron
  dos, en `recentAnimes.py` (`ctk` y `Theme`), que dejó de usar el paso 9.1
- Pendiente que deja: nada de los pasos. Para el 9.4, las cinco clases huérfanas y el `.spec`

### Fase 9 · Paso 9.1 — `EmptyState` en las 7 vistas          (2026-08-21)
- Ficheros: `src/gui/components/empty_state.py` (nuevo, 224 líneas),
  `src/gui/components/status_pill.py` (0.3 → 0.4, parámetro `gap`),
  `src/gui/components/sidebar.py` (0.1 → 0.2, `navigate_to()`),
  `src/gui/main_window.py` (0.4 → 0.5, `navigate_to()`, `retry_recent_animes()` y **el arreglo
  de la pantalla de carga**), y las **6** vistas (todas 0.3 → 0.4)
- Verificado: sí · **app real arrancada 2 veces —oscuro y claro— contra una biblioteca vacía, con
  26 capturas miradas** + **116 comprobaciones** con CTk real (ventana oculta) + los dos glifos
  nuevos **mirados ampliados x10** sobre los dos fondos
- 🔴 **La biblioteca real no se toca**: las dos persistencias se repuntan a `DB_Animes.db` y
  `DB_user.db` **nuevas y vacías** en el scratchpad antes de construir `MainWindow` (receta de la
  fase 4, octava vez). `sha256 5e29fbc6a81e…` **idéntico** antes y después de los dos arranques
- 🔴 **Fallo real encontrado y arreglado**: `download_images_and_show_animes()` solo retiraba la
  pantalla de carga en la rama de éxito, así que **un arranque sin red dejaba el GIF tapando la
  portada para siempre** — el estado vacío de «Nuevos lanzamientos» no llegaba a verse nunca. Se
  ve en la primera captura del día. De paso, la pantalla ahora se **destruye** en vez de
  `place_forget()`: mientras seguía viva, su animación se reprogramaba cada 100 ms durante toda la
  sesión repintando un GIF de 400 × 400
- **Los seis textos**, uno por vista: «No se han podido cargar los estrenos» (Reintentar) ·
  «Todavía no has marcado ningún favorito» (Ir a Nuevos lanzamientos) · «No tienes nada a medias»
  (Ir a Pendientes) · «No tienes nada en la cola» (Buscar un anime) · «Aún no has terminado
  ninguno» (Ir a Viendo) · «Sin resultados para «X»» (Borrar la búsqueda / Quitar los filtros)
- **Iconos**: los cuatro de biblioteca reutilizan el glifo de su propio estado
  (`StatusPill.icon(..., gap=0)`, teñido de `TXT_3`); los dos que faltaban —nube tachada y lupa—
  se dibujan con PIL en `empty_state.py`, como el pin y las estrellas. **Cero PNG nuevos**, así
  que la deuda B11 no crece
- Pendiente que deja: nada del paso. Para el 9.4, las **cinco** clases huérfanas de
  `utilsButtons.py` (`BaseButton` incluida) y el `.spec`

### Fase 8 · Pasos 8.1, 8.2 y 8.3 — la ficha del anime entera          (2026-08-21)
- Ficheros: `src/gui/anime_window.py` (reescrito, 1 114 → 1 733 líneas, 0.6 → 0.7)
- Verificado: sí · **app real arrancada tres veces y mirada, con 8 capturas** + **93
  comprobaciones** con CTk real sobre **copia** de las dos BD, con red de verdad en los servidores
  y en la migración + `python src/app.py` a pelo 35 s sin un solo `Traceback` ni un
  `invalid command name`
- **Recuento de filas**: 30 antes y 30 después, en la copia. En la **real**, `sha256
  24288986ac92…` **idéntico** antes y después de los tres arranques y las ocho capturas: la
  biblioteca del usuario no se ha tocado
- **El `wraplength` de la sinopsis se resolvió recalculando en `<Configure>`**, no cambiando de
  contenedor. La columna de información lleva su propio manejador con umbral de 8 px y de ahí salen
  el envuelto del título, el de la sinopsis y el reenvuelto de los géneros. Medido: con la barra
  desplegada la columna mide 866 y con la ventana estrecha 426, y el envuelto la sigue; plegar la
  barra la lleva a 1 006 y la sinopsis **se queda en 592**, que es su tope de 74ch
- **Qué animes se tocaron y cómo se dejaron**: en la **copia**, *One Piece* (`one-piece`) — se le
  cambiaron los cuatro estados, se le marcó del episodio 1 al 5, se le desmarcó el 3 y se migró su
  fila a `one-piece-en-jkanime`. En la **real**, ninguno: solo se abrieron fichas (*One Piece*, *Ao
  no Hako*) y se desplegaron servidores, que no escriben
- **Lo que se ha visto en la app real**, con la biblioteca real:
  - **One Piece desde Viendo**: póster 248 × 372 con esquinas redondeadas, «Proveedor: AnimeAV1» y
    «En tu biblioteca: AnimeAV1» en gris, título a 30, sinopsis a 74ch, las cuatro fichas de género
    con su contorno, **«1163 de 1174 vistos»** con su barra al 99 %, y los cuatro botones con
    **Favorito y Viendo encendidos** (fucsia y turquesa) y Pendiente y Finalizado apagados
  - **Servidores**: la fila del episodio se resalta con `CARD`, el número pasa a `ACCENT`, la línea
    de estado dice «Servidores disponibles» y debajo sale el `CTkSegmentedButton` con **HLS ·
    TeraBox · MP4Upload · Mega**. Volver a pulsar los repliega
  - **Barra plegada**: la ficha se ensancha a 1 356 px y **la sinopsis no se recorta** — se queda en
    su tope de lectura, que es justo lo que pide el último punto del checklist
  - **Tema claro**: los dos botones encendidos salen en pastel sobre blanco y los apagados con borde
    `LINE`; el ⚠ ámbar y las fichas de género se leen bien
  - **Identidad partida forzada**: con **JKAnime** en el desplegable, *One Piece* —cuya fila es de
    AnimeAV1— se re-localiza por título (`similitud 1.00`), la ficha sale con «Proveedor: JKAnime»,
    **«⚠ En tu biblioteca: AnimeAV1»** en ámbar y el botón **«Actualizar a JKAnime»** arriba a la
    derecha. La identidad de persistencia siguió siendo `one-piece`
- **Dos defectos vistos en las capturas y arreglados en el sitio**: las fichas de género salían
  **sin borde** (un `CTkFrame` transparente no lo pinta, y la etiqueta encima tapaba lo que quedaba)
  y el botón de orden **decía «Mayor a menor» sobre una lista ascendente**. Los dos están en la
  tabla de Decisiones
- **Lo que NO se ha tocado**, que es la mitad del trabajo de esta fase: la identidad congelada, el
  aviso de identidad partida, `__confirm_save()`, el marcado acumulativo y el `strict=True` de los
  servidores. Se recolocaron y se comprobaron uno a uno
- Pendiente que deja: para la **fase 9**, la petición de servidores en el hilo de Tkinter, las
  **cuatro** clases huérfanas de `utilsButtons.py` y los géneros sin tildes que sirve el proveedor
  («Accion», «Fantasia»)

### Fase 8 · Paso 8.0 — Preparar los glifos y las medidas que faltaban          (2026-08-21)
- Ficheros: `src/gui/components/status_pill.py` (0.2 → 0.3), `src/gui/theme.py`
- Verificado: sí · los cuatro glifos **dibujados y mirados ampliados x10** (el corazón nuevo sale
  simétrico, con hendidura y punta limpias a 14 px); el módulo importa sin errores
- `StatusPill.icon()` gana un parámetro **`color`** con un par `(claro, oscuro)`. Sin él se comporta
  **exactamente como antes** —la variante oscura del estado en los dos temas, que es lo que necesita
  un sello sobre la carátula—, así que las dos vistas que ya lo usan (Finalizados y Buscar) no
  cambian de comportamiento. Con él, el glifo se dibuja **dos veces**, una por tema, que es lo que
  hacen falta en los botones de estado de la ficha: van sobre el fondo de la aplicación, no sobre un
  póster
- 🔴 **«Favorito» ya tiene glifo.** Hasta ahora `_GLYPHS` solo traía los tres excluyentes y
  `icon(FAVOURITE)` devolvía `None` (decisión de la fase 6). El botón «Favorito» de la ficha necesita
  su corazón, así que se ha añadido. Que la pestaña de favoritos no se selle a sí misma lo sigue
  garantizando `other_status()`, que nunca devuelve FAVOURITE. **Efecto colateral visible y buscado**:
  el sello «Favorito» de **Buscar** —el único sitio que lo pinta, cuando un resultado está guardado
  solo como favorito— pasa a llevar corazón como los otros tres llevan el suyo
- `Metrics` gana `STATUS_BUTTON_RADIUS = 9` y `STATUS_BUTTON_GAP = 10`, que estaban en `DISENO.md` §3
  («Botón de estado de la ficha | alto 40 · radio 9 · 4 en fila con hueco 10») y no en `theme.py`
- **`src/gui/anime_window.py` sigue intacto**: la app arranca exactamente igual que en `a41c699`
- Pendiente que deja: los pasos 8.1, 8.2 y 8.3 enteros

### Fase 7 · Pasos 7.2, 7.3 y 7.4 — sello «ya lo tienes», paginación real y la vista          (2026-08-21)
- Ficheros: `src/gui/sidebarButtons/searchAnimes/searchAnimes.py` (reescrito, 372 → 455 líneas),
  `src/gui/components/pager.py` (+ `set_pages()`)
- Verificado: sí · **app real, dos arranques y 11 capturas miradas** + **51 comprobaciones** de la
  vista con CTk real (ventana oculta, proveedor sustituido, sin red) + **3 peticiones reales** a los
  sitios para medir el tamaño de página
- **Lo que se ha visto en la app real**, con la biblioteca real:
  - «level up» → **14 resultados en AnimeAV1 · 2 ya están en tu biblioteca**, y los dos *Ore dake
    Level Up na Ken* con su sello **✓ Finalizado**. Uno empareja por *slug* y **el otro por título**:
    la temporada 2 está guardada desde **JKAnime** con el slug
    `ore-dake-level-up-na-ken-season-2-arise-from-the-shadow` y AnimeAV1 la sirve como
    `ore-dake-level-up-na-ken-season-2`
  - «one piece» → **20 resultados · 5 ya están en tu biblioteca**: One Piece con **👁 Viendo** y
    cuatro películas con **✓ Finalizado**. *One Piece: Gyojin Tou-hen* **no** se sella, y es correcto:
    su fila tiene los cuatro estados a 0
  - **Acción** → 20 resultados y el paginador de verdad: «**Página 1 de 50**» con `‹ 1 2 3 4 … 50 ›`.
    Pulsar el **2** trae otros veinte distintos y el pie pasa a «Página 2 de 50»
  - **Acción + Fantasía** (la segunda, desplegando «Más géneros») → los mismos que devuelve
    `search_animes_by_genres_and_order()` a pelo. Los 40 géneros envuelven en **5 filas**
  - **El fallback, en directo**: una consulta que AnimeAV1 no supo responder salió como «**1 resultado
    en JKAnime**». La línea dice quién ha servido de verdad, que es justo lo que pedía la ficha
  - **Tema claro**: el sello oscuro se lee sobre carátulas casi blancas (*One Piece Fan Letter*).
    ⚠️ El sello pastel de **Favoritos** sigue leyéndose mal ahí — es la deuda de la **fase 9**
  - **Cambiar de vista a los 0,25 s de lanzar una búsqueda**: la app sigue viva y el log no tiene
    **ni un** `invalid command name` ni un `Traceback`
- **Tamaño de página de cada proveedor** (medido): AnimeAV1 devuelve las búsquedas **por texto en una
  sola página** (14 resultados, `last_page = 1`) y las de **género de 20 en 20 con 50 páginas**;
  JKAnime, por texto, 22 resultados y `last_page = 1`. Es decir: **el paginador solo aparece
  filtrando por género**
- `AccordionFilterButton` **ya estaba huérfana** antes de esta fase (la retiraron las fases 3-6 de las
  cuatro vistas de estado). Ahora se quedan también sin uso `utilsButtons.SearchButton` y
  `ApplyFiltersButton`: **son tres para la fase 9**
- La biblioteca real **no se ha tocado**: `sha256 e5b4f2e0…` y `mtime` **idénticos** antes y después
  de los dos arranques, de las once capturas y de todas las pruebas
- Pendiente que deja: nada de la fase. Para la 9, las tres clases huérfanas y el sello de Favoritos

### Fase 7 · Paso 7.1 — `GenreChips`, las fichas de género          (2026-08-21)
- Ficheros: `src/gui/components/genre_chips.py` (nuevo, 300 líneas)
- Verificado: sí · **28 comprobaciones con CTk real** (ventana oculta): 7 fichas + «Más géneros
  (33)» plegado, 41 desplegado, la seleccionada va **primera** con `ACCENT_SOFT` + borde `ACCENT` +
  ✕, `on_change` solo en el clic (`set_selected()` no lo dispara), orden del enum al seleccionar,
  envuelto en 3 filas sin solapes y **ninguna ficha fuera de los 1 160 px**, alto del marco = filas
- Las fichas se colocan con **`place()`, no con `grid()`**: las columnas de una rejilla son comunes
  a todas las filas, así que la tercera ficha de la primera fila y la de la segunda compartirían
  ancho —el de la más larga— y la fila se abriría en huecos. Envolver texto pide posición absoluta,
  y con `place()` el marco no pide alto: se lo fija `show()` a mano
- El texto sale de **`refactor_genre_text(genre.name)`**, no de `.value`: los `value` del enum son
  slugs sin tildes (`ciencia-ficcion`) y la interfaz va en español con tildes. Da «Acción»,
  «Ciencia ficción», «Recuentos de la vida»
- Las seleccionadas **cuentan** dentro de las 7 visibles, como en el diseño: dos activas y cinco por
  elegir, no siete además de las activas
- ✕ y chevrón dibujados con PIL, como las estrellas, el pin y los sellos. Estos **sí** cambian con
  el tema (van sobre el fondo de la app, no sobre una carátula): `CTkImage(light_image=, dark_image=)`
- Pendiente que deja: el sello y la paginación (7.2 y 7.3), y montar la vista (7.4)

### Fase 6 · Paso 6.2 — Montar la vista «Finalizados»          (2026-08-21)
- Ficheros: `src/gui/sidebarButtons/finishedAnimes/finishedAnimes.py` (reescrito, 140 → 245 líneas)
- Verificado: sí · **app real ejecutada y mirada** en los dos temas (2 capturas) + **22
  comprobaciones** sobre la app en marcha (paginación, buscador, recorrido de las 6 vistas) + **10**
  sobre los casos límite del sello + la ficha de un finalizado abierta con un clic real
- `ViewHeader` («Finalizados» · «18 animes · 7 episodios vistos») + `PosterGrid(6)` a 176 × 264 +
  `Pager(12)` + `SavedAnimeSearch`. Fuera el acordeón de géneros (decisión de la fase 3); se queda
  el pie del proveedor (decisión de la fase 5, `DISENO.md` §6)
- 🔴 **Tu biblioteca tiene 18 finalizados, no 9**: el paginador **sí** aparece (dos páginas), al
  contrario de lo que preveía la ficha. Y **16 de los 18 están marcados como terminados sin ningún
  episodio marcado**, así que la rejilla se llena de «0 / N». Es el dato real y el sello lo enseña
  sin corregirlo
- La biblioteca real **no se ha tocado**: `sha256 e5b4f2e0…` y `mtime` idénticos antes y después de
  tres arranques y de abrir una ficha
- Pendiente que deja: nada de la fase. Para la 9, unificar el sello de «Favoritos» con este

### Fase 6 · Paso 6.1 — El sello superpuesto de `PosterGrid`          (2026-08-21)
- Ficheros: `src/gui/theme.py`, `src/gui/components/status_pill.py`, `src/gui/components/poster_grid.py`
- Verificado: sí · los tres glifos dibujados a 12 px y **mirados** ampliados x10 sobre el
  fondo real del sello; `StatusPill.icon()` devuelve `(17, 12)` para los tres estados
  excluyentes y `None` para «Favorito»; `PosterItem(badge=…, badge_icon=…)` construido con
  CTk real
- El sello se mueve a **arriba a la izquierda** (`DISENO-VISUAL` `.mark`: `top:9px;left:9px`) y
  cambia de aspecto por defecto: superficie oscura `BADGE_BG` + texto blanco `BADGE_INK`, con el
  color del estado en el **glifo**. Es lo que lo hace legible sobre una carátula clara con el
  tema en claro, que es justo lo que manda comprobar la verificación de la fase
- `badge_colors` **sigue existiendo con la misma firma**, así que «Favoritos» conserva su
  píldora pastel sin tocar el fichero. Solo hereda el cambio de esquina
- Pendiente que deja: montar la vista (paso 6.2)

### Fase 5 · Paso 5.4 — Montar la vista «Favoritos»          (2026-08-21)
- Ficheros: `src/gui/sidebarButtons/favouriteAnimes/favouriteAnimes.py` (reescrito)
- `ViewHeader` («Favoritos» + «14 animes · N calificados» + orden + buscador) → `PosterGrid` de
  **5 columnas** con póster **216 × 324** → `Pager` de **10**. Con 14 favoritos el paginador
  **se ve de verdad** (2 páginas), que es la primera vez en el plan.
- Cada celda: póster con **sello del otro estado**, título a 2 líneas, **estrellas** y pie con
  el proveedor. El sello nunca dice «Favorito» (ver Decisiones).
- 🔴 Fuera el acordeón «Abrir filtro de animes», como en las fases 3 y 4. Van **tres de las
  cuatro** vistas de estado; queda finalizados.
- ✅ Fuera el `time.sleep(0.1)` del hilo de UI. Van **cuatro de seis** vistas.
- El buscador local (`SavedAnimeSearch`) se reutiliza tal cual y responde a **Enter**. Cambiar el
  orden **no deshace el filtro**: se guarda la última lista sin ordenar y el orden se aplica al
  pintar. Sin resultados aparece un mensaje que se esconde con `grid_remove()`, no se destruye.
- Verificado: sí, y en la **app real con la biblioteca real**:
  - **56 comprobaciones con CTk real** (ventana oculta, BD en sandbox): layout, 10 celdas,
    estrellas en la fila 2, pie en la 3, los dos órdenes, `NULL` al final, el paginador, los
    clics de media estrella, el sello y el buscador. 0 fallos.
  - **App real, dos arranques**: calificar *Dandadan* con el ratón (**4,0** → **2,0** → **1,5**,
    cada clic escrito en `DB_Animes.db`), **cerrar la app y reabrirla**: la calificación **seguía
    ahí** y la media estrella se pinta bien. Después se **quitó** con el mismo gesto: la
    biblioteca queda como estaba, **29 filas y 0 calificados**.
  - Las **6 vistas** se abren; ninguna traza de error en el log de los dos arranques.
- ⚠️ Tk **no atiende los clics publicados con `PostMessage`** ni al toplevel ni al HWND hijo:
  para ejercitar la interfaz real hace falta entrada de ratón de verdad. El script del scratchpad
  (`clic_real.py`) roba el foco un segundo y **devuelve el cursor** donde estaba. Y ojo: la
  captura incluye la barra de título, así que **hay 30 px de desfase** entre la imagen y las
  coordenadas de cliente.
- Pendiente que deja: nada.

### Fase 5 · Paso 5.3 — Estrellas, sello de estado y orden persistido          (2026-08-20)
- Ficheros: `src/dataPersistence/userPersistence.py`,
  `src/gui/components/rating_stars.py` (nuevo), `src/gui/components/status_pill.py` (nuevo).
- `FAVOURITES_ORDER` es un miembro más de `UserSettingKey` (sin migración: `USER_SETTINGS` es
  clave/valor) con su par tipado `get_favourites_order()` / `set_favourites_order()`. Valores
  persistidos `"rating"` / `"title"`; **el texto del desplegable vive en la vista**, para que
  renombrar una opción no invalide lo guardado. Por defecto, `"rating"`.
- **`RatingStars`**: 5 estrellas + la cifra («4,5»), escala entera 0-10. Las estrellas se
  **dibujan con PIL** (polígono de 10 vértices a 8x, reducido con LANCZOS) en vez de traer PNG
  al repositorio o depender de un glifo del sistema; el medio punto es un rectángulo recortado
  con la máscara del polígono. `CTkImage(light_image=…, dark_image=…)` resuelve el tema solo.
- El **medio punto sale de dónde se pulsa** (mitad izquierda / derecha). Cada estrella ocupa
  17 px aunque el dibujo mida 14: el aire entre estrellas es zona pulsable, o cada mitad
  quedaría en 7 px. ⚠️ La mitad se mide con `event.widget.winfo_width()`, **no** con el ancho
  pedido: `CTkLabel.bind()` ata a la etiqueta interna y al canvas, que no miden lo mismo
  (Decisiones, fase 3).
- **Pulsar la calificación que ya estaba la borra** (vuelve a `NULL`): es la única forma de
  dejar sin calificar algo ya calificado.
- **`StatusPill`**: los 4 pares de color de `DISENO.md` §1 en un sitio. Sirve como widget y
  como par de colores (`text()` / `colors()`), que es como lo usa la rejilla a través de
  `badge` + `badge_colors` de `PosterGrid`. `other_status()` responde «además de favorito,
  ¿qué más es?».
- **`PosterGrid` gana `extra_builder`** en vez de una subclase: construye la fila libre bajo el
  título (fila 2, `pady=(7, 0)`) y **numera las filas sobre la marcha**, así que el pie del
  proveedor baja a la 3 solo si hay fila libre. Como los eventos de Tk **no burbujean**, pulsar
  una estrella no abre la ficha: la celda ni se entera.
- Verificado: sí · con **raíz Tk oculta** (`withdraw()`): formato de la cifra, `set_value()`, el
  par de colores y `other_status()`; y luego dentro de las **56 comprobaciones** del paso 5.4,
  que incluyen los clics de media estrella emitidos sobre el `_label` interno.
- Pendiente que deja: nada.

### Fase 5 · Paso 5.2 — 🔴 Migrar `DB_Animes.db`, la biblioteca real          (2026-08-20)
- Ficheros: ninguno. Dos scripts en el **scratchpad**, no en el repo:
  `test_fase5_migracion.py` (sobre copia) y `migrar_bd_real.py` (sobre la real).
- 🔴 **Filas: 29 antes y 29 después**, en la copia y en la real. Y las **14 columnas
  anteriores × 29 filas = 406 valores idénticos**, comparados uno a uno **por nombre de
  columna**, no por posición.
- **La vía fue la barata**: `ALTER TABLE ADD COLUMN`, sin reconstruir la tabla. `diff_table()`
  lo dijo **antes** de tocar nada (`missing: ['rating']`, `extra: []`, `retyped: []`,
  `reordered: False`) — que es exactamente lo que se buscaba poniendo `RATING` al final.
- **Copias de seguridad, tres**: la manual del scratchpad
  (`backup/DB_Animes_pre_fase5_20260820_224547.db`, **fuera del repo**, `sha256`
  `3754a94c01de7413…`), la que hizo `validate_db_integrity()` en
  `resources/DB/backups/DB_Animes_20260820_224943.db`, y la de la copia del sandbox.
- **59 comprobaciones sobre la copia** + **15 sobre la real**, 0 fallos. Cubren: recuento,
  columnas, orden físico == `FIELDS`, idempotencia (segunda pasada sin copia nueva),
  `watched_episodes` sigue leyéndose como rangos, `episodes` en el mismo orden, `provider_id`
  intacto en las 29 filas, y que calificar **solo toca la columna `rating`**.
- Ningún anime real quedó calificado: todas las filas siguen a `NULL`. Las calificaciones de
  prueba se hicieron sobre la **copia** y sobre una fila `__test-fase5__` que se borró.
- ⚠️ La consola de Windows es **cp1252** y reventó el script en un `print` con `→` — la trampa
  que avisa `docs/09 §3c`, pero en la cabecera de sección, no en el detalle de un `check`. Se
  arregla con `sys.stdout.reconfigure(encoding="utf-8", errors="replace")` al principio.
- Verificado: sí · los dos scripts ejecutados de verdad, en ese orden.
- Pendiente que deja: nada.

### Fase 5 · Paso 5.1 — La columna `rating`          (2026-08-20)
- Ficheros: `src/dataPersistence/animesPersistence.py`
- `RATING = ("rating", "INTEGER")` **al final** de `AnimeField` (columna 15); `rating` en
  `AnimeRecord` con `to_db_dict()` / `from_db_dict()` a mano —la migración es automática, la
  serialización no— y `update_anime_rating(anime_id, rating)` nuevo.
- **Escala: entero de 0 a 10**, dos puntos por estrella. `AnimeRecord.RATING_MAX = 10`.
- 🔴 `RATING_MAX` es un **`ClassVar[int]`**. Dentro de un `@dataclass`, una anotación normal es
  un **campo más**: `RATING_MAX: int = 10` habría metido un decimoquinto parámetro en el
  `__init__` de `AnimeRecord`. Comprobado con `dataclasses.fields()`.
- `_rating_from_db()` se comporta como `_provider_id_from_db()`: **nunca lanza**. `NULL`, texto
  o un valor fuera de escala se degradan a `None` — una calificación rara no puede impedir leer
  la biblioteca.
- Verificado: sí · dentro de las 59 comprobaciones del paso 5.2.
- Pendiente que deja: nada.

### Fase 4 · Paso 4.4 — Montar la vista «Pendientes»          (2026-08-20)
- Ficheros: `src/gui/sidebarButtons/pendingAnimes/pendingAnimes.py` (reescrito)
- `ViewHeader` («Pendientes» + «N animes en cola · M episodios» + **orden** + buscador) → cascada de
  `AnimeRow` a ancho completo. **Sin paginador** y **sin panel lateral**: aquí no hay nada que
  retomar. El título se recorta a **660 px** (`TITLE_W`) en vez de a los 420 de «Viendo», porque sin
  panel sobra sitio.
- El **buscador local (`SavedAnimeSearch`) se reutiliza tal cual**, igual que en la fase 3, y también
  responde a **Enter**. Cambiar el orden **no deshace el filtro**: `__display_animes` guarda la
  última lista sin ordenar y el orden se aplica al pintar.
- 🔴 **Fuera el acordeón «Abrir filtro de animes»**, como en la fase 3 (ver Decisiones). Van dos de
  las cuatro vistas de estado; quedan favoritos y finalizados.
- ✅ Fuera el `time.sleep(0.1)` del hilo de UI. Van **tres de seis** vistas; las otras tres lo
  conservan hasta su fase.
- Estado vacío propio («No tienes ningún anime en la cola…»), pendiente de `EmptyState` en la fase 9.
- Verificado: sí · dentro de las **61 comprobaciones** del paso 4.1 y **mirado en la app real**
  (segundo arranque).
- Pendiente que deja: nada.

### Fase 4 · Paso 4.3 — «Empezar»          (2026-08-20)
- Ficheros: `src/gui/sidebarButtons/pendingAnimes/pendingAnimes.py`
- Píldora de acción en hover que encadena lo que ya existía: `update_anime_to_watching()` —que apaga
  finalizado y pendiente él solo—, el póster a `watching/`, los contadores y la ficha.
- ⚠️ El `AnimeInfo` se construye desde la **fila guardada** ([trampa 21]): su `anime_id` es el slug
  del proveedor que la guardó. Comprobado que **no se crea ninguna fila nueva** (29 antes y 29
  después en la copia) y que el anime conserva su `provider_id`.
- 🔴 Dos cosas que la ficha de la fase no preveía, las dos en Decisiones: los **contadores** salen de
  listas cacheadas que solo se llenan al arrancar —hay que releerlas antes de refrescar— y la
  **descarga del póster es HTTP**, así que sale del hilo de Tkinter en un hilo daemon.
- «Empezar» abre la **ficha**, no el episodio 1: eso es de la fase 8, igual que la píldora de Viendo.
- Verificado: sí · flujo completo ejecutado sobre una **copia** de `DB_Animes.db`
  (`Given: Uragawa no Sonzai`, 1 episodio): sale de pendientes, entra en viendo, `is_finished` sigue
  a 0, sin episodios vistos heredados, contadores refrescados una vez, la ficha se abre con el
  `anime_id` correcto y el póster se encola **fuera** del hilo de Tkinter. Al volver a Pendientes
  quedan 4 filas y el subtítulo dice «4 animes en cola · 43 episodios».
- Pendiente que deja: la ficha (`anime_window.py`) **sigue sin refrescar los contadores** al cambiar
  un estado. Es de la fase 8.

### Fase 4 · Paso 4.2 — Orden por duración          (2026-08-20)
- Ficheros: `src/gui/sidebarButtons/pendingAnimes/pendingAnimes.py`
- `CTkOptionMenu` en la zona de controles de la cabecera con los tres criterios: **Más cortos
  primero** (por defecto) · Más largos primero · Título (A-Z). Se resuelve **en memoria**, sin
  volver a la BD ni tocar `animesPersistence.py`.
- 🔴 Las filas **sin lista de episodios** van al final en los dos sentidos de la duración (ver
  Decisiones). Hoy no hay ninguna así entre los pendientes, pero las hay en cuanto se guarda un
  anime sin abrir su ficha.
- El orden **no se persiste** (ver Decisiones): `DISENO.md` §8 no lo pide.
- Verificado: sí · los tres criterios, con la lista real y con una fila sin episodios inyectada;
  y **mirado en la app real** con «Más largos primero» (12, 12, 11, 8, 1).
- Pendiente que deja: nada.

### Fase 4 · Paso 4.1 — `AnimeRow` sin progreso          (2026-08-20)
- Ficheros: `src/gui/components/anime_row.py` (**un** parámetro nuevo), `pendingAnimes.py`
- ✅ **`AnimeRow` sigue siendo un solo componente.** La fase costó `meta_text`, que sustituye al
  proveedor en la columna derecha por «N episodios · Proveedor», más la constante `META_W = 170`
  («1163 episodios · AnimeAV1» no cabe en los 90 px del proveedor a secas). El resto ya estaba:
  `poster_size=ROW_PENDING_POSTER` y `show_progress=False`, que dejó preparados la fase 3.
- Cada mitad del meta se cae sola si no se sabe, sin dejar el ` · ` colgando.
- Medido: **113 px de fila** —los de `DISENO.md` §3— contando el separador; póster 56 × 80; ninguna
  `CTkProgressBar` en la vista.
- Verificado: sí · **61 comprobaciones** con Tk real sobre una **copia** de `DB_Animes.db`
  (geometría, meta, separadores, los tres órdenes, fila sin episodios, hover, «Empezar» de punta a
  punta, vuelta a la vista, buscador, tres repintados seguidos, cola vacía) y **hash de la
  biblioteca real idéntico** al terminar. Más 3 arranques de la app real con captura y el recorrido
  de las **6 vistas**, que se abren todas.
- Pendiente que deja: nada.

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

---

## Cierre del plan *(2026-08-21)*

Las **9 fases** están terminadas, verificadas con la aplicación real y commiteadas en
`feature/ui-redisign`, de `bd25742` a `7606def`. ⚠️ **La rama no se ha fusionado con `main`**: el plan
no lo autorizaba y esa decisión es del usuario.

### Qué quedó fuera

Lo que el plan declaró fuera de alcance desde el principio y sigue fuera: la convivencia anime +
manga, el bloque «Si te ha gustado X…», los proveedores nuevos (MonosChinos2, TioAnime) y redibujar
los iconos de origen dudoso (deuda **B11**).

Lo que se decidió **durante** el plan y no llegó a entrar:

| Qué | Por qué | Dónde retomarlo |
|---|---|---|
| ⚠️ **La petición de servidores sigue en el hilo de Tkinter** | Es un cambio de concurrencia, no de aspecto; la fase 9 no podía ampliarse por su cuenta | `anime_window.py`. **Es el último sitio de la GUI que sale a la red desde el hilo de la interfaz** |
| **El orden de «Pendientes» no se persiste** | No estaba entre las tres preferencias que `DISENO.md` §8 mandaba guardar | Un miembro más de `UserSettingKey` ([13 §4](../docs/13-selector-de-proveedor.md)) |
| **Texto y géneros no se combinan en «Buscar»** | El contrato de proveedores no lo permite y la fase 7 no tocaba `APIs/` | Haría falta un método nuevo en `AnimeProvider`, o filtrar en cliente |
| **Los 4 PNG `viendo_light/dark` y `pendientes_light/dark`** | Comprobado: los dos dibujos de cada par son de tinta negra, así que no sirven como par claro/oscuro | Hay que **redibujarlos** ([11 §5](../docs/11-playbooks.md)) |
| **`utilsButtons.py` conserva un nombre que ya no describe lo que hace** | Renombrarlo es refactor, no interfaz | Vive en `utils/` y solo tiene 3 piezas |

### Qué fases se cerraron sin verificar

**Ninguna.** Las nueve se ejecutaron con la aplicación real y se miraron. Lo que sí quedó sin
ejercitar, fase por fase, está en la tabla **«Qué quedó sin verificar»** de más arriba; el patrón se
repite y conviene leerlo entero antes de fiarse de nada:

1. **El hover con un ratón de verdad** — ocho fases seguidas sin puntero. El mecanismo se ejecutó
   emitiendo eventos **sobre el canvas interno** (que es lo que toca el ratón), pero mover el ratón,
   no.
2. **Los desplegables abiertos con el ratón** — su lista es un *toplevel* aparte y `PrintWindow` no la
   captura. Se ejercitó su `command`, que es lo que el desplegable llama.
3. **Todo lo que escribe, sobre la biblioteca real** — se hizo **sobre copias**, por la regla 2 de
   `/fase`. La real solo se ha mirado, y su `sha256` se comprobó idéntico en cada sesión.
4. **Marcar un episodio, cerrar la app y reabrirla** — las dos mitades están ejecutadas; la costura
   entre ellas, no.

### Qué recomendaría como siguiente tarea

**Sacar la petición de servidores del hilo de Tkinter.** Es pequeño, está localizado en
`anime_window.py`, y es lo único que queda de la aplicación que congela la ventana; además cierra el
apartado de concurrencia de [`docs/07`](../docs/07-concurrencia-e-hilos.md), que hoy lo lista como
riesgo vivo.

Después, del roadmap del usuario: la **convivencia anime + manga**, que el rediseño ha dejado a medio
camino sin proponérselo —las pestañas ya no dicen «Anime», ya paginan, «Viendo» ya es una cascada con
el último capítulo y «Favoritos» ya tiene calificación—, así que lo que falta es el desplegable de
tipo y el filtro.
