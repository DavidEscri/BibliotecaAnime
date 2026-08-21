# Estado del rediseño

> Este fichero es la memoria del plan entre sesiones. Lo lee y lo escribe `/fase`.
> Si contradice al árbol de trabajo, **gana el árbol**: `git log --oneline` y `git status` mandan.

| | |
|---|---|
| **Fase actual** | 8 — Ficha del anime |
| **Situación** | ⬜ no empezada |
| **Último paso completado** | Paso 7.4 — montar la vista (**fase 7 cerrada**) |
| **Siguiente paso** | Paso 8.1 — leer la ficha de la fase 8. Es la más grande del plan (`anime_window.py`, 1 155 líneas) y la única que puede quitar el tope de `[:25]` episodios. Se le han quedado **dos deudas explícitas**: los contadores de la barra no se repintan al cambiar un estado desde la ficha (fase 4) y abrir «por un episodio concreto» (fases 3 y 4) |
| **Rama** | ✅ `feature/ui-redisign` (**no** `feature/rediseno-ui`: ya existía, ver Decisiones) |
| **Base** | `bd25742` (fase 1) → fases 2, 3, 4, 5 y 6 encima, en `feature/ui-redisign`. El plan partió de `6377b92`, no de `4f9e429` |
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
| 7 | Buscar | ✅ terminada | `COMMIT7` | ✅ app real ejecutada y **mirada** (2 arranques, **11 capturas**: buscar por texto, dos géneros, «Más géneros» desplegado, paginador con 50 páginas, página 2, fallback a JKAnime, tema claro y cambio de vista en vuelo) + **51 comprobaciones** de la vista con CTk real + **28** de `GenreChips` |
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
