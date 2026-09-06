# 06 — GUI y vistas

| | |
|---|---|
| **Fecha** | 2026-09-02 · rama `feature/ui-redisign` · último commit **`9083a32`** (documentación) |
| **Última revisión** | 2026-09-02 (**rejillas adaptables y sinopsis**): `PosterGrid` deja de tener un número fijo de columnas y lo **calcula del ancho**, con `on_columns_changed` para que la vista repagine; `Pager` estrena `set_page_size()`; el tamaño de página pasa de ser una constante a ser `columnas × 2 filas`. La ficha quita el tope de 74 caracteres de la sinopsis y estrena `wrap_synopsis()`, porque `wraplength` no puede con los saltos que trae el proveedor ([trampas 41 y 42](10-invariantes-y-trampas.md)). Antes, 2026-09-01 (**abrir la ficha por un episodio**): la ficha estrena `focus_episode` / `force_ascending` y dos métodos (`__focus_on_episode`, `__scroll_to_episode`); `AnimeRow` corrige sus ataduras —el clic saltaba el botón pero no su interior, así que la píldora **nunca ejecutó su `command`** ([trampa 40](10-invariantes-y-trampas.md))—; «Viendo» y «Pendientes» dejan de llevar al anime y llevan al episodio. Antes, 2026-09-01 (**ancho de las fichas de género**): `GenreChips` explica **quién decide el ancho de una ficha** y por qué el componente tiene que contarlo él ([trampa 39](10-invariantes-y-trampas.md)); se añade la regla general de que en CustomTkinter `width` es una petición, no un contrato. Antes, 2026-09-01 (**refresco de la banda «Retomar»**): `ResumeBand` y `ResumeCard` estrenan `update_record()`; la portada pasa a ser la **única vista que sale a la red por datos ya guardados**, y se explica por qué va sin *fallback*. Antes, 2026-09-01 (**hover de la lista de episodios**): `EpisodeRow` ata el hover a todos sus hijos y guarda la fila resaltada en un atributo de clase; se explica por qué `AnimeRow` no sufre lo mismo, y la regla de `bind()` gana su consecuencia con el ratón real. Antes, 2026-08-31 (**fondo de la pantalla de carga**): el apartado *Arranque* explica que la pantalla de carga es la ventana entera pintada de `Theme.BG`, y qué se veía antes. Antes, 2026-08-21 (**rediseño de interfaz, fases 1-9**): documento **reescrito entero**. Nacen `gui/theme.py` y los **11** componentes de `gui/components/`; la barra lateral pasa de seis botones sueltos a un `Sidebar` plegable; `SidebarButton` deja de ser un widget; las 6 vistas se rehacen y la ficha crece de 1 156 a 1 734 líneas |
| **Cubre** | `src/gui/theme.py`, `src/gui/components/**`, `src/gui/main_window.py`, `src/gui/anime_window.py`, `src/gui/sidebarButtons/**`, `src/utils/buttons/utilsButtons.py` |

Procedencia: ✅ verificado en ejecución (arranque real de la GUI) · 📖 leído en código · ⚠️ sin verificar.

> La **especificación** visual —tokens, medidas, reglas de composición— vive en
> [`.claude/plan-rediseno/DISENO.md`](../plan-rediseno/DISENO.md), y el histórico de por qué cada
> cosa es como es, en [`ESTADO.md`](../plan-rediseno/ESTADO.md). Este documento describe **el código
> que resultó**, no el diseño.

---

## 0. El mapa, de un vistazo

```
gui/
├── theme.py                 Theme (colores + tipografía) y Metrics (medidas). NADIE define un color fuera
├── components/              piezas compartidas; una vista no dibuja nada que ya esté aquí
│   ├── sidebar.py           Sidebar + _NavItem — la barra entera, plegable
│   ├── view_header.py       ViewHeader — título + subtítulo + zona de controles, alto fijo 80
│   ├── poster_grid.py       PosterGrid + PosterItem — rejilla que ajusta sus columnas al ancho
│   ├── pager.py             Pager — dos modos: trocear una lista, o paginar al proveedor
│   ├── anime_row.py         AnimeRow + RowAction — fila en cascada, con acción en hover
│   ├── side_panel.py        SidePanel — los 290 px de la derecha en «Viendo»
│   ├── resume_card.py       ResumeBand + resume_progress() — «Retomar donde lo dejaste»
│   ├── rating_stars.py      RatingStars — las cinco estrellas con medios puntos
│   ├── status_pill.py       StatusPill — texto, colores y glifo de cada estado
│   ├── genre_chips.py       GenreChips — fichas de género seleccionables
│   └── empty_state.py       EmptyState — icono, frase y acción cuando no hay nada que enseñar
├── main_window.py           el hub
├── anime_window.py          AnimeWindowViewer + EpisodeRow + open_saved_anime()
└── sidebarButtons/<vista>/  las 6 vistas: solo deciden qué datos van en cada componente
```

**La regla que sostiene todo lo demás**: una vista **compone**, no dibuja. Si necesita una variante
de un componente, se le añade un parámetro; **no se bifurca el fichero**. Se ha cumplido: `AnimeRow`
la comparten «Viendo» y «Pendientes» con dos parámetros de diferencia, y `PosterGrid` sirve a las
tres rejillas.

---

## 1. `gui/theme.py` — la única fuente de color y medida

Dos clases sin estado:

- **`Theme`** — 20 tokens de color, cada uno una tupla `(claro, oscuro)`, más los roles
  tipográficos. Pasar la tupla a CustomTkinter es lo que hace que **el cambio de tema no requiera
  recorrer widgets**: lo resuelve la librería.
- **`Metrics`** — las medidas de `DISENO.md` §3: anchos de barra, tamaños de póster, altos de fila,
  radios.

Tres cosas que no son obvias:

| | |
|---|---|
| `Theme.font(size, bold, mono)` | Las fuentes **no** son constantes de módulo: un `CTkFont` necesita que ya exista la raíz de Tk, así que a nivel de módulo el import reventaría. Se cachean por `(tamaño, negrita, mono)` |
| `Theme.ellipsize(texto, fuente, ancho, líneas)` | 🔴 `wraplength` **no** limita a dos líneas, y un `CTkLabel` **no** se recorta a su `height`: envuelve todo lo que haga falta y crece. Todo título de ancho fijo pasa por aquí ([trampa 30](10-invariantes-y-trampas.md)) |
| `Metrics.POSTER_CACHE_SIZE` | Está **duplicado a mano** en `utils/utils.py:24-33`, con un comentario que nombra a su pareja. `utils/` no puede importar de `gui/` ([01 §2](01-arquitectura.md)) |

✅ Verificado el 2026-08-21: `git grep -nE "#[0-9A-Fa-f]{6}" -- src/` devuelve **solo**
`src/gui/theme.py`. Ni un color literal en el resto del árbol.

---

## 2. `MainWindow` como hub

Sigue sin haber router ni gestor de vistas: `MainWindow` (CTk) es un objeto compartido que cada
vista muta directamente.

**Qué mantiene**:

| Atributo | Qué es |
|---|---|
| `content_frame` | Un **único** `CTkScrollableFrame` que las 7 vistas reutilizan. `clear_frame()` destruye sus hijos |
| `sidebar_frame` | La instancia de `Sidebar`. `None` hasta `load_sidebar_buttons()` |
| `recent_animes`, `favourite_animes`, `watching_animes`, `pending_animes`, `finished_animes` | Listas cacheadas. **Solo se llenan al arrancar**; quien cambie un estado tiene que releerlas antes de `refresh_sidebar_counts()` ([trampa 31](10-invariantes-y-trampas.md)) |
| `animes_persistence`, `user_persistence`, `anime_provider_mgr` | Los tres singletons |
| `last_search_instance` | La última búsqueda, para que volver a «Buscar» la encuentre igual |

**API pública que usan las vistas** (además de la que ya había):

| Método | Para qué |
|---|---|
| `navigate_to(etiqueta)` 🆕 | Abre otra vista **por su etiqueta de barra lateral** y deja la barra marcándola. Es lo que usan los botones de los estados vacíos. Devuelve `False` si la etiqueta no existe: **no lanza** |
| `retry_recent_animes()` 🆕 | Vuelve a pedir los estrenos. Lo llama el botón «Reintentar» de la portada |
| `refresh_sidebar_counts()` | Repinta los contadores desde las listas cacheadas |
| `set_active_sidebar_destination(destino)` | Marca el activo cuando la navegación no viene de un clic |
| `provider_for_saved_anime(provider_id)` | El orden de prioridad de [13 §8](13-selector-de-proveedor.md) |

### Arranque

0. `__init__` registra los tres proveedores y arranca `UserPersistence` **de forma síncrona** — el
   desplegable tiene que nacer con el valor guardado y el pin aplicado antes de la primera petición.
1. `show_loading_screen()` (`:412`) pinta el GIF y lanza un hilo daemon.
2. Ese hilo: `load_animes()` (BD, 0→40 %) → `get_recent_animes()` → `download_images_progress()`
   (90→100 %) → **destruye la pantalla de carga** → `RecentAnimeButton.show_frame()`.
3. Un segundo hilo (`__preload_recent_animes_info`) rellena sinopsis/géneros/episodios de cada
   estreno para que el clic sea instantáneo.

🔴 **La pantalla de carga se `destroy()`, no se `place_forget()`, y se retira también cuando no hay
estrenos.** Hasta la fase 9 solo se retiraba en la rama de éxito, así que **un arranque sin red
dejaba el GIF tapando la portada para siempre**; y como el widget seguía vivo, su animación se
reprogramaba cada 100 ms durante toda la sesión repintando un GIF de 400 × 400. Es la
[trampa 33](10-invariantes-y-trampas.md). ✅ Visto y arreglado el 2026-08-21.

🆕 **Y es la ventana entera, no una tarjeta.** El `loading_frame` va con `fg_color=Theme.BG` y
`place(relx=0, rely=0, relwidth=1, relheight=1)` (`:414-415`); dentro, un marco **transparente**
centrado con `place(relx=0.5, rely=0.5, anchor=CENTER)` (`:417-418`) sostiene el título, el GIF y la
barra. Título, porcentaje y barra salen de `Theme` (`TXT`, `TXT_2`, `LINE`, `ACCENT`, `T_VIEW`,
`T_UI`).

Hasta el 2026-08-31 ese marco **no llevaba `fg_color`** y se dibujaba del tamaño justo de su
contenido, de modo que el arranque enseñaba **tres fondos a la vez**: el gris por defecto de
CustomTkinter en el bloque (`#2B2B2B`), el de la raíz de Tk en la franja que reserva el `minsize` de
la columna de la barra lateral (`#242424`) y `Theme.BG` en el resto (`#14161A`). El GIF tiene el
fondo **transparente**, así que no tenía color propio: heredaba el del marco. Es la
[trampa 36](10-invariantes-y-trampas.md).

Dos cosas más de ese arreglo, por si se tocan:

- La raíz de Tk se pinta con `self.configure(fg_color=Theme.BG)` en `__config_main_window()`
  (`:104`). Solo asoma donde no llega ningún hijo, pero ahí se veía como una banda de otro color.
- El centrado ya **no** se calcula con `winfo_width() * 2.5`. Antes de que la ventana esté dibujada
  `winfo_width()` vale 1, así que aquel centrado acertaba por casualidad.

---

## 3. `Sidebar` — la barra lateral

Sustituye a los seis `CTkButton` que se pintaban solos. Contiene cabecera con el botón de plegado,
los seis destinos, el bloque de proveedor (desplegable + pin) y el de apariencia.

**Dos anchos**: 224 px desplegada, 84 px plegada (`Metrics.SIDEBAR_W` /
`SIDEBAR_COLLAPSED_W`). El estado se **persiste** en `DB_user.db` (`sidebar_collapsed`, ver
[13 §4](13-selector-de-proveedor.md)).

Cada destino es un `_NavItem`, que **no hereda de ningún widget**: agrupa cuatro piezas (barra de
acento de 2 px, icono, etiqueta y contador) que tienen que reaccionar juntas al hover y al clic,
porque en Tk `<Enter>` y `<Button-1>` **no burbujean** desde los hijos. Cada ítem construye sus dos
representaciones —desplegada y plegada— y enseña la que toque.

🔴 **Tres trampas de layout que costaron caro** y valen para cualquier componente nuevo:

1. **Un `CTkFrame` sin hijos conserva 200 × 200 como tamaño pedido** y estira su fila. La barrita de
   acento inflaba la fila a 200 y el icono caía en `y=86`, fuera de lo visible: la barra salía **con
   los seis destinos en blanco y sin ningún error**. Todo marco decorativo o todavía vacío necesita
   `height=` explícito ([trampa 29](10-invariantes-y-trampas.md)).
2. **El alto de fila se fija con `minsize` en la fila, no con `height=` + `grid_propagate(False)`**:
   esa combinación deja el marco al alto pedido por fuera, pero su rejilla interna sigue centrando
   los hijos como si midiera 200.
3. **El ancho fijo necesita `grid_propagate(False)` *y* `minsize` en la columna 0 del padre.** Solo
   con el primero, la rejilla de `MainWindow` le roba píxeles cuando el contenido pide más ancho del
   que cabe (medido: 219 en vez de 224).

**El orden de los destinos es el de la lista `destinations` de `load_sidebar_buttons()`**: Nuevos ·
Favoritos · Viendo · Pendientes · Finalizados · Buscar. **Las etiquetas viven en cada vista**, en su
`super().__init__`; renombrar una pestaña es tocar su vista, no la barra.

---

## 4. `SidebarButton` ya no es un widget

📖 `utils/buttons/utilsButtons.py:159`. Desde la fase 1 es una **clase llana** que solo describe un
destino:

```python
class SidebarButton:
    self.sidebar_text: str        # etiqueta que enseña la barra
    self.sidebar_command: Callable # qué se ejecuta al pulsarlo
    def sidebar_icon(size) -> CTkImage
    def show_frame()               # lo implementa cada vista
```

La firma del constructor **no cambió** (`parent_frame`, `text`, `row`, `column`, `command`,
`icon_path_light`, `icon_path_dark`), así que las seis vistas siguen heredando igual; `parent_frame`,
`row` y `column` se conservan por compatibilidad y **ya no se usan**.

⚠️ **Si necesitas el destino como widget, no existe.** Lo que hay es el `_NavItem` de la barra.

### Qué queda en `utilsButtons.py`

Tres piezas, y ninguna es un botón pese al nombre del fichero: `filter_animes_by_title()`,
`match_animes_from_search()` y `SavedAnimeSearch` (el buscador **local** de las cuatro vistas de
estado), más `SidebarButton`.

El paso 9.4 retiró **cinco clases huérfanas** —`BaseButton`, `EpisodeButton`, `SearchButton`,
`ApplyFiltersButton` y `AccordionFilterButton`—, todas `CTkButton` con colores y tamaños literales,
sustituidas por los componentes del rediseño. El módulo pasó de 361 a 205 líneas. Renombrarlo se
dejó fuera del plan: el rediseño es solo interfaz y esto vive en `utils/`.

---

## 5. Ciclo de vida de una vista

Sigue siendo el mismo patrón, con dos cambios:

```
sidebar → _NavItem.__handle_click → Sidebar.__on_item_click
   → set_active(destino) → destino.sidebar_command()
        → main_window.clear_frame()          # destruye los hijos de content_frame
        → construir ViewHeader + componentes en content_frame
```

1. 🔴 **`clear_frame()` no deshace la configuración de rejilla del `content_frame`.** Los pesos de
   filas y columnas **sobreviven**, y una columna con peso y sin widgets también recibe el espacio
   sobrante: la ficha repartía peso entre cuatro columnas y la vista siguiente pintaba en una columna
   0 estrecha. **Toda vista que reparta peso tiene que deshacerlo**; la ficha lo hace en su salida
   ([trampa 32](10-invariantes-y-trampas.md)).
2. **El `time.sleep(0.1)` tras `clear_frame()` desapareció.** Solo estaba para que `winfo_width()` no
   valiera 1 al calcular columnas; con rejillas de número fijo no se mide nada. **No lo reintroduzcas.**

---

## 6. Los componentes, uno a uno

### `ViewHeader`
Título (`T_VIEW`) + subtítulo (`T_SUB`, `TXT_3`) a la izquierda; `controls_frame` a la derecha, donde
cada vista mete lo suyo. Alto fijo 80 con `minsize`. `controls_frame` nace con `height=1` por la
trampa 29.
**No repite contadores**: viven en la barra lateral (`DISENO.md` §6).
**«Buscar» es la única vista sin `ViewHeader`**: su campo de 620 px *es* la cabecera.

### `PosterGrid` / `PosterItem`
Rejilla que **ajusta sus columnas al ancho disponible**. Una celda es un **`CTkFrame` propio que ocupa
UNA fila** de la rejilla, con el póster, el título (a dos líneas, vía `ellipsize`), un pie opcional y
un hueco libre opcional (`extra_builder`). Así añadir o quitar una línea no toca ningún índice.

🆕 **Cómo decide cuántas columnas** (2026-09-02): `columns_that_fit()` divide su `winfo_width()` entre
`póster + GRID_GAP_X`. El parámetro `columns` dejó de fijar el número y ahora es solo la **referencia
del diseño**: se usa mientras la rejilla todavía no se puede medir, y de ella sale el tamaño de página
inicial de la vista.

🔴 **La vista tiene que colocarla con `sticky="ew"`.** No es cosmético: con `sticky="w"` el widget se
queda con el ancho de su contenido, así que la cuenta de columnas se mediría a sí misma y nunca
cambiaría de valor ([trampa 41](10-invariantes-y-trampas.md)).

- **El sobrante se reparte, no se acumula**: `weight=1` y un mismo grupo `uniform` en las columnas en
  uso, y la celda con `sticky="n"` para que quede centrada en la suya. A 1440 eso deja el primer
  póster exactamente en los 28 px de margen del diseño. ⚠️ Al encoger hay que **quitar** el peso a las
  columnas que sobran ([trampa 32](10-invariantes-y-trampas.md)).
- **`on_columns_changed` es un contrato, no un aviso.** Quien lo pasa **se compromete a repintar** y
  la rejilla no vuelve a pintar por su cuenta; quien no lo pasa deja que se recoloque sola con los
  últimos ítems que recibió. Existe porque en las vistas paginadas el ancho no cambia solo cómo se
  coloca la página: cambia **qué animes entran en ella**, y pintar en los dos sitios sería pintar dos
  veces.
- ⚠️ **Repintar cuesta ~350 ms para 16 celdas, en el hilo de la interfaz** (cada una abre su JPG y lo
  reescala con PIL). Por eso `<Configure>` descarta todo lo que no cambie el número de columnas —el
  reparto del sobrante lo hace Tk gratis— y lo que queda pasa por `RELAYOUT_DELAY_MS`, que junta un
  arrastre del borde en un solo repintado. Entrar en una vista pinta de inmediato.
- El `<Configure>` va con **`add="+"`** ([trampa 40](10-invariantes-y-trampas.md)), y `clear()` es
  seguro porque `winfo_children()` de un `CTkFrame` **no** incluye su canvas interno —CustomTkinter lo
  filtra—, que es donde vive esa atadura.

- **Sello superpuesto** (`badge` + `badge_icon`), colocado con `place()` arriba a la izquierda. Es
  **siempre** el del diseño: `BADGE_BG` opaco y `BADGE_INK`, con el color del estado solo en el
  glifo. No se puede elegir otro par — va sobre la carátula, no sobre el fondo de la app, y los pares
  pastel de `StatusPill` no se leen sobre un póster claro.
- El widget que devuelve `extra_builder` **no hereda el clic de la celda** (los eventos de Tk no
  burbujean), que es justo lo que hace que pulsar una estrella no abra la ficha.
- Los pósters se cargan con `load_rounded_image()`: **CustomTkinter no redondea la `image` de un
  widget** por mucho `corner_radius` que tenga; el recorte hay que traerlo hecho desde PIL.

### `Pager`
Dos modos, sin subclase:

| Modo | Cuándo | Qué dice |
|---|---|---|
| `set_total(n, page)` | La lista está entera en memoria | «Mostrando 13-24 de 58». **Es dueño del corte** (`slice_bounds()`), para que el texto y lo que se ve no discrepen |
| `set_pages(última, actual)` | Quien trocea es el sitio web | «Página 2 de 50». El total **no se sabe**: el contrato devuelve la última página, no cuántos hay |

Se esconde solo si no hay nada que paginar.

🆕 **`set_page_size(n)`** (2026-09-02): el tamaño de página dejó de ser una constante porque depende
de cuántas columnas quepan. Conserva **el primer elemento que se estaba viendo**, no el número de
página — al pasar de 12 a 16 por página, la 2 se convierte legítimamente en la 1, y el anime que
abría la página sigue en pantalla. En el modo del proveedor guarda el valor y no toca la página: allí
`page_size` no corta nada.

### `AnimeRow` / `RowAction`
Fila en cascada: póster + título + géneros + (opcional) progreso + columna derecha. Parámetros:
`poster_size`, `show_progress`, `action`, `on_click`, `provider_name`, `meta_text`, `text_width`,
`show_separator`. «Pendientes» la usa **sin tocar el fichero**.

🔴 **Un `<Leave>` no significa que el ratón se haya ido**: Tk lo manda también al pasar del marco a
un hijo, así que apagar el hover ahí hace parpadear la fila y la píldora se escapa justo al ir a
pulsarla. `__pointer_inside()` compara `winfo_pointerxy()` con el rectángulo real antes de apagar
nada ([trampa 34](10-invariantes-y-trampas.md)).
**El hueco de la acción se reserva siempre**, con tamaño fijo y `grid_propagate(False)`: si la
píldora se creara al entrar el ratón, la fila cambiaría de ancho bajo el cursor.

⚠️ **`AnimeRow` no sufre la [trampa 37](10-invariantes-y-trampas.md) por cómo está montada, no por
suerte**: su separador va **fuera** del cuerpo que se resalta (`anime_row.py:143-144` lo mete en la
fila, no en `__body`) y el **hover** se ata a **todos los descendientes** de `__body`. No queda ningún
hijo sin atar dentro del rectángulo que se comprueba. Si algún día se mete un widget dentro de
`__body` sin atarlo, vuelve el fallo.

🔴 **El clic, en cambio, salta la píldora entera — con su canvas y su etiqueta dentro**
(`anime_row.py:278-312`, resuelto el 2026-09-01). Hasta entonces se saltaba **solo el botón**, y como
un `CTkButton` es un marco con hijos y `bind()` **sustituye** en vez de sumar, la fila estaba pisando
el `_clicked` que CustomTkinter monta en esos hijos: **la píldora nunca ejecutó su propio `command`**.
Pulsarla corría el `on_click` de la fila. Los dos abrían la ficha del mismo anime, así que no se notó
—salvo que **«Empezar» no movía nada a «Viendo»**— hasta que dejaron de hacer lo mismo
([trampa 40](10-invariantes-y-trampas.md)). Dos reglas de ahí en adelante:

- para excluir un widget de un recorrido recursivo, **exclúyele el subárbol**, no el widget;
- lo que se ate encima de un widget de CustomTkinter va con **`add="+"`** — por eso el hover sí llega
  a la píldora sin borrarle el suyo, que también estaba pisado y por eso nunca se coloreó.

### `SidePanel` y `ResumeBand`
Los 290 px de la derecha en «Viendo» y la banda «Retomar donde lo dejaste» de la portada.
Los 290 son **248 + 21 × 2**: 248 es el ancho al que se guarda el póster, así que se pinta a tamaño
natural, y **toda línea de la tarjeta se mide contra 248**.
`resume_progress(record)` es el **único** sitio donde se calcula por dónde ibas; ordena los episodios
antes de mirar nada, porque `AnimeRecord.episodes` **viene invertido** de la BD ([trampa 2](10-invariantes-y-trampas.md)).
La banda **no se pinta si no hay nada que retomar**: ni etiqueta ni hueco.

⚠️ **`resume_card.py` guarda dos cosas de naturaleza distinta**: los widgets de la banda, que usa una
sola vista, y las dos funciones puras `resume_progress()` / `resume_caption()`, que usan **cinco**
llamantes —incluidos `anime_row.py` y `side_panel.py`, que no pintan ninguna tarjeta—. `resume` es
*retomar*, no *resumen*. Inventario de llamantes en [02 §componentes](02-mapa-de-modulos.md).

🆕 **La banda se puede refrescar en caliente** (2026-09-01). `ResumeCard.update_record(record)` vuelca
una fila recién leída en el pie y en la barra —no recrea la tarjeta, que solo serviría para releer el
póster del disco y hacer parpadear la banda entera—, y `ResumeBand.update_record(record)` busca a
quién le toca **por `anime_id`**, no por posición, porque entre que se piden los datos y llegan la
banda pudo repintarse con otro reparto. Devuelve `False` si ese anime ya no está en la banda.
Quien lo usa es la portada: [03 §11](03-flujos-de-ejecucion.md).

### `RatingStars`
Cinco estrellas con medios puntos, **dibujadas con PIL** en tiempo de ejecución. Escala entera 0-10
(dos puntos por estrella); `NULL` **no es 0**. Volver a pulsar la misma calificación la quita.
🔴 **Calificar no reordena la rejilla**: si la lista se recolocara bajo el cursor, la segunda
estrella se pulsaría sobre otro anime.

### `StatusPill`
Texto, colores y **glifo** de los cuatro estados, en un solo sitio. Se usa como widget o sin él
(`text()`, `colors()`, `icon()`).
`other_status(record, besides=…)` responde «además de estar donde está, **¿qué más es** este anime?».
`icon(status, size, color, gap)`:
- **sin `color`**, se tiñe con la variante **oscura** del estado en los dos temas — es lo que necesita
  un sello, que va sobre `BADGE_BG`;
- **con `color`**, se dibuja dos veces, una por tema;
- **`gap=0`** lo deja cuadrado, para cuando va solo y centrado (los estados vacíos). Por defecto
  reserva 5 px transparentes a su derecha, porque Tk pega imagen y texto con `compound="left"` y
  `CTkLabel` no expone su padding interno.

### `GenreChips`
Fichas de género seleccionables; las activas van primeras, con `ACCENT_SOFT` + borde `ACCENT` + ✕.
Siete visibles y «Más géneros (33)» para el resto.
🔴 **Se colocan con `place()`, no con `grid()`**: las columnas de una rejilla son comunes a todas las
filas, así que envolver texto con `grid` hace que la tercera ficha de cada fila comparta el ancho de
la más larga y la fila se abra en huecos. Con `place()` el marco no pide alto, así que `show()` se lo
fija.
El texto sale de `refactor_genre_text(genre.name)`, **no de `.value`**: los `value` son slugs sin
tildes (`ciencia-ficcion`).

🔴 **Colocar con `place()` obliga a llevar la cuenta del ancho, y esa cuenta no es la del diseño.**
`__chip_width()` no puede sumar «texto medido + `CHIP_PAD_X`»: un `CTkButton` **no respeta el `width`
que se le pide** —su rejilla interna propaga tamaño y gana el ancho que ella necesita—, y `place()`
sin ancho explícito pinta el widget a su ancho *pedido*. Hay que sumarle además los 14 px por lado que
reserva el radio de la píldora, el borde de la etiqueta del texto y, con icono, el hueco interno más
el borde de la etiqueta de la imagen. Contar de menos **no encoge la ficha**: la deja pintándose
encima de la siguiente, que es como se destapó — **al seleccionar un género, la ficha de al lado le
tapaba la ✕**. La aritmética, con los números medidos, en la
[trampa 39](10-invariantes-y-trampas.md).

⚠️ **Regla general, no anécdota de este componente**: en CustomTkinter `width` y `height` son una
**petición**, no un contrato. Es la misma raíz de las trampas **29** (un `CTkFrame` no mide cero) y
**30** (un `CTkLabel` no se recorta a su `height`). Quien coloque con `place()` y calcule medidas a
mano tiene que comprobarlas leyendo `winfo_reqwidth()` del widget ya colocado
([09 §6d](09-verificacion-y-pruebas.md)), no fiarse de `cget("width")`.

### `EmptyState` 🆕
Icono, frase, pista opcional y un botón de acción. Sustituye al `CTkLabel` suelto de cada vista.

🔴 **Un estado vacío no puede mentir sobre su causa ni prometer una salida que no existe.** Dos
reglas que salieron de aquí:

- La portada vacía **no** es «no tienes nada»: el catálogo no es del usuario. Si sale vacía es que
  ningún proveedor respondió, así que el texto habla de la red y la acción es **reintentar**.
- En «Buscar» **no se puede ofrecer «prueba con otro proveedor»**: `call_with_fallback()` ya los ha
  probado todos cuando el elegido devuelve vacío. Se ofrece borrar la búsqueda o quitar los filtros,
  que es lo único que cambia el resultado.

Recibe el icono **ya construido**: las cuatro vistas de biblioteca pasan el glifo de su propio estado
(`StatusPill.icon(..., gap=0)`), y el módulo solo dibuja los dos que no existían —nube tachada y
lupa— con PIL. **Cero PNG nuevos**, así que la deuda **B11** no crece.

---

## 7. Las 6 vistas

Todas heredan de `SidebarButton`, se instancian en `load_sidebar_buttons()` y componen. Lo que las
distingue:

| Vista | Disposición | Paginador | Buscador | Estrena |
|---|---|---|---|---|
| **Nuevos lanzamientos** | `ResumeBand` + rejilla de **6 a 1440** (176 × 264) | sí, **columnas × 2** | — | la banda «Retomar», y su **refresco** al entrar |
| **Favoritos** | rejilla de **5 a 1440** (216 × 324) + estrellas | sí, **columnas × 2** | local | la calificación y su orden persistido |
| **Viendo** | cascada de `AnimeRow` (póster 70 × 100) + `SidePanel` | no | local | el panel de retomar |
| **Pendientes** | cascada de `AnimeRow` (póster 56 × 80) | no | local | orden por duración + «Empezar» |
| **Finalizados** | rejilla de **6 a 1440** | sí, **columnas × 2** | local | el sello «vistos / totales» |
| **Buscar** | campo de 620 px + `GenreChips` + rejilla de **6 a 1440** | sí, **del proveedor** | — | el sello «ya lo tienes» |

**Rejilla donde se mira, cascada donde se decide** (`DISENO.md` §6).

🆕 **Las columnas ya no son un número fijo: salen del ancho** (2026-09-02). Los 6 y 5 de la tabla son
lo que da la cuenta a 1440, que es el tamaño con el que se diseñó; maximizado a 1920 son **8 y 7**.
Y con ellas se mueve el tamaño de página, porque la regla del diseño —«dos filas llenas, nunca una
llena y otra coja»— solo se cumple si el número de página **acompaña** al de columnas: cada vista
declara `ROWS_PER_PAGE = 2` y el resto lo calcula `PosterGrid`. A 1440 salen los 12 y 10 de siempre.

⚠️ **«Buscar» queda fuera de esa regla**, y es correcto: allí trocea el proveedor, así que su última
fila puede quedar coja y no hay nada que repaginar. Por eso es la única que **no** pasa
`on_columns_changed` y deja que la rejilla se recoloque sola.

🆕 **«Nuevos lanzamientos» es la única vista que sale a la red por datos que ya tiene guardados.**
Al entrar, `__refresh_resume_episodes()` (`recentAnimes.py:137-186`) relee los episodios de las ≤3
filas de la banda y reescribe la columna `episodes` si el proveedor sirve más que la biblioteca; sin
eso, un anime en emisión decía «Lo has visto entero» hasta que abrías su ficha. Va con `strict=True`
—**sin fallback**— precisamente porque escribe sin que el usuario lo haya pedido
([03 §11](03-flujos-de-ejecucion.md), [trampa 38](10-invariantes-y-trampas.md)).

🆕 **«Viendo» y «Pendientes» ya no llevan al anime, llevan al episodio** (2026-09-01). Sus tres
acciones dicen un episodio concreto en su propio texto —«Episodio N →», «Seguir por el N» y
«Empezar»— y ahora lo cumplen: la ficha se abre con esa fila desplegada y sus servidores a la vista.
El número sale del mismo `resume_progress()` que escribió el texto. **«Empezar» además fuerza el
orden ascendente**, y «Viendo» **no**: con un anime largo servido de mayor a menor, forzarlo dejaría
el episodio fuera de los 25 que se pintan ([03 §12](03-flujos-de-ejecucion.md)).

⚠️ En el `SidePanel` son **dos gestos distintos**: el **botón** lleva al episodio, el **póster y el
título** siguen abriendo la ficha a secas. Es el mismo reparto que ya tenía `AnimeRow`, y el motivo de
que el panel fuera el único de los tres que funcionó a la primera: deja el botón fuera de sus
ataduras a mano, así que nunca le pisó el `command` ([trampa 40](10-invariantes-y-trampas.md)).

Tres cosas comunes a las **cuatro vistas de biblioteca**:

- Su clic delega en **`open_saved_anime()`**, que elige el proveedor, saca la petición del hilo de
  Tkinter y —🆕 desde el 2026-09-01— acepta `focus_episode=` y `force_ascending=`.
- Su buscador es **local** (`SavedAnimeSearch`): compara títulos guardados, funciona sin conexión, y
  la búsqueda web se **suma** encima sin quitar resultados nunca ([trampa 26](10-invariantes-y-trampas.md)).
- **Enseñan siempre el proveedor de la fila**, porque puede no ser el seleccionado.

⚠️ **El acordeón «Abrir filtro de animes» desapareció de las cuatro.** No está en el diseño y filtrar
por género seis animes que ya son tuyos no aporta. Si el filtrado vuelve, el sitio es `GenreChips`.

⚠️ **En «Buscar», texto y géneros son dos búsquedas distintas y no se combinan: manda el último
gesto.** `search_animes_by_query()` y `search_animes_by_genres_and_order()` son métodos distintos del
contrato y ninguno acepta lo del otro, así que buscar por texto **vacía las fichas** y tocar una
ficha **vacía el texto**. Las peticiones no se solapan porque cada una lleva su número de generación
y **solo pinta la última**.

---

## 8. `AnimeWindowViewer` — sigue sin ser una ventana

📖 `gui/anime_window.py` (1 924 líneas). Reemplaza el contenido de `content_frame`.

**Disposición**: bloque de proveedor + póster de 248 × 372 (redondeado) + título `T_SHEET` + sinopsis
+ fichas de género a la izquierda; los **4 botones de estado** en fila; y la lista de episodios.

**Los botones de estado se encienden y se apagan** (fase 8), en vez de cambiar de texto para decir
cuál de las dos acciones tocaba. Los cuatro comparten un único `command`, `__toggle_status()`, que
mira cómo está la fila; los cuatro booleanos sueltos son ahora un diccionario `__status_state`, así
que encender uno de los tres excluyentes y apagar los otros dos es una vuelta de bucle.

**`EpisodeRow`** sustituye al viejo botón de ancho completo que repetía «<título> - Episodio N»
veinticinco veces. Ahora dice solo «Episodio N» y reparte el resto entre una línea de estado y el
interruptor «Visto».
**Las filas van en las posiciones PARES de la rejilla y los servidores en la impar de debajo**:
desplegarlos no empuja nada, y la fila impar mide cero mientras está vacía.

🔴 **El hover se ata a TODOS los hijos de la fila; el clic, solo a la fila y a sus dos etiquetas**
(`anime_window.py:420-435`, dos bucles a propósito). El interruptor recibe `<Enter>` / `<Leave>` pero
no `<Button-1>` —tiene su propio comando y marcar un episodio no debe abrir sus servidores—, y el
**separador de 1 px** también va atado, porque `place(rely=1.0, relwidth=1.0)` lo pone en la última
fila de píxeles de cada episodio y **bajar de un episodio al siguiente obliga a cruzarlo**. Dejarlo
fuera era una salida de la que no llegaba ningún `<Leave>`, y el resaltado se quedaba encendido en
todos los episodios recorridos ([trampa 37](10-invariantes-y-trampas.md), resuelta el 2026-09-01).
Encima de eso, `EpisodeRow.__hovered` —atributo **de clase**— guarda la fila resaltada y la que se
enciende apaga a la anterior: **no puede haber dos a la vez** aunque se pierda un evento.

🆕 **La ficha se puede abrir por un episodio** (2026-09-01). `focus_episode=N` la deja con esa fila
desplegada, sus servidores a la vista y la ventana desplazada hasta ella; `force_ascending=True`
ordena la lista de menor a mayor pase lo que pase. Lo usan las tres acciones que prometen un episodio
en su texto — «Episodio N →», «Seguir por el N» y «Empezar» — y **solo ellas**: sin esos parámetros la
ficha se abre exactamente como antes. Recorrido completo y los dos finales silenciosos en
[03 §12](03-flujos-de-ejecucion.md).

Tres decisiones que no se ven leyendo la firma:

- **Se hace con `after(50 ms)` detrás del pintado**, no durante. Pedir servidores sigue yendo en el
  hilo de Tkinter (§10), así que sin ese respiro la ventana se congelaría con la ficha a medio
  dibujar.
- **Si el episodio cae fuera del corte de 25, se enseña él solo** con sus botones de anterior y
  siguiente, y el número se escribe en «Ir al episodio…»: es el mismo estado al que se llega
  buscándolo a mano. Con AnimeAV1 —que sirve ascendente— es lo que pasa con One Piece por el 1164.
- **El desplazamiento solo ocurre si hace falta.** Se mide la fila y el marco de servidores contra lo
  que se está viendo; si caben, no se toca nada. Desplazar siempre tiraba fuera el póster en el caso
  de «Empezar», donde el episodio 1 ya se veía. 🔴 `CTkScrollableFrame` no expone el desplazamiento en
  customtkinter 5.2.2: se usa su `_parent_canvas`.

**El corte de 25 episodios sigue en pie**, pero ahora **la lista lo dice** («Se muestran 25 de
1 174 episodios · usa "Ir al episodio…"»), que es lo que convierte el buscador de al lado en la
salida evidente. **La lista no se reordena al abrir** ([trampa 8](10-invariantes-y-trampas.md)), y el
botón de orden dice **el orden que llega del proveedor**: no es el mismo en todos.

### El bloque de proveedor
Hasta tres líneas: `Proveedor: X` (quién sirvió lo que ves), `En tu biblioteca: Y` (de quién es tu
fila) y el botón «Actualizar a Z». **El ⚠ ámbar compara las dos primeras**: iguales → gris
informativo; distintas → identidad partida. Detalle en [13 §8 y §14](13-selector-de-proveedor.md).

### Las dos identidades
🔴 Sigue siendo la [trampa 21](10-invariantes-y-trampas.md), intacta tras el rediseño:
`anime_info` / `provider_id` son del proveedor que sirvió la ficha;
`persistence_anime_id` / `persistence_poster_url` / `persistence_provider_id` salen de la **fila
guardada** y **no cambian mientras la ficha está en pantalla**. Toda operación de BD y de póster usa
las segundas, vía `__persistence_anime_info()`.

🔴 **Quien abra una ficha de algo que puede estar en la biblioteca tiene que pasar `anime_record=`.**
Omitirlo hace que un solo clic en un estado cree una fila duplicada.

### Ancho y envuelto
El `wraplength` de la sinopsis se resuelve **recalculando en `<Configure>`**, con umbral de 8 px: de
ahí salen el envuelto del título, el de la sinopsis y el reenvuelto de los géneros. Ya no hay ningún
número calculado a mano sobre el ancho del `content_frame` — eso cerró la
[trampa 22](10-invariantes-y-trampas.md).
🆕 **La sinopsis usa todo el ancho de la columna** (2026-09-02). Tenía tope de 74 caracteres
(`.syn`: `max-width:74ch`), que se quitó porque a pantalla completa dejaba media ficha vacía.

🔴 **Y recalcular el `wraplength` no basta**: si el texto trae un `
`, Tk lo respeta pase lo que
pase. La sinopsis de AnimeAV1 los trae —van escapados en su payload y `animeav1.py:206` los convierte
en saltos de verdad—, así que se quedaba con los renglones del proveedor por ancha que fuera la
ventana, **mientras el título de al lado sí se reajustaba**. Lo arregla `wrap_synopsis()` al construir
la etiqueta: los saltos sueltos pasan a espacio y **los dobles se conservan**, porque son párrafos que
escribió alguien ([trampa 42](10-invariantes-y-trampas.md)).

⚠️ **La petición de servidores sigue en el hilo de Tkinter.** Es lo que hacía la ficha vieja y el
rediseño solo recolocó; lo único que se añadió es el cursor de espera. **Es el último sitio de la GUI
que sale a la red desde el hilo de la interfaz** ([12](12-deuda-tecnica-y-roadmap.md)).

---

## 9. Temas claro/oscuro

`change_appearance_mode_event()` es **una línea**: `ctk.set_appearance_mode(...)`. Antes había que
recorrer los hijos de la barra reconfigurando fondo, hover, color de texto e icono uno a uno, porque
los botones se habían construido con literales.

Reglas que hay que respetar para que siga siendo una línea:

1. **Ningún color literal fuera de `theme.py`.** Si hace falta uno que no está, se añade el token.
2. **Texto sobre `ACCENT` va con `ACCENT_INK`** (blanco en claro, casi negro en oscuro); texto sobre
   `ACCENT_SOFT`, con `ACCENT`. ✅ Auditado el 2026-08-21: los **8** sitios con `fg_color=ACCENT` y
   los **4** con `ACCENT_SOFT` lo cumplen.
3. **Lo que se pinta sobre `BADGE_BG` se tiñe con la variante oscura del color en los dos temas.** El
   sello es una superficie oscura siempre —va sobre la carátula—, así que `FIN_TXT[0]`, que es un
   verde oscuro, desaparecería justo en tema claro.
4. Un `CTkImage` con `light_image` y `dark_image` distintos resuelve el tema solo. `load_dual_image()`
   lo construye.

⚠️ **Los iconos de la barra lateral y los dos GIF de carga son de origen desconocido** y
probablemente incompatibles con la GPL: es la deuda **B11** ([12 §4](12-deuda-tecnica-y-roadmap.md)).
Todo lo dibujado por el rediseño —el pin, las estrellas, los glifos de estado, los dos iconos de
estado vacío— **es nuestro**, hecho con PIL en tiempo de ejecución.

⚠️ **`viendo_light/dark.png` y `pendientes_light/dark.png` existen en `resources/images/utils/` y NO
se usan.** No son un par claro/oscuro: **los dos dibujos de cada par son de tinta negra**, así que en
tema oscuro el suyo sería invisible. El icono único funciona porque es bicolor. El paso 9.4 retiró el
código comentado que los invocaba; si se quieren pares de verdad, hay que **redibujarlos**.

---

## 10. Concurrencia — lo que no ha cambiado

⚠️ **Todo lo que abra una ficha va en hilo daemon y repinta con `after(0, …)`.** Hacerlo desde el
hilo secundario revienta con `invalid command name ...!ctkcanvas` al destruir una vista que tenía un
`<Configure>` encolado.

Antes de tocar un widget desde un callback diferido, comprobar `widget.winfo_exists()`.

🔴 **CustomTkinter no ata `bind()` al widget que crees**: `CTkFrame.bind()` va a su `_canvas`;
`CTkLabel.bind()`, al `_label` **y** al canvas; `CTkEntry.bind()`, al `_entry`. Con el ratón real da
igual, pero **`widget.event_generate()` sobre el objeto CTk no dispara nada**: cualquier prueba de
hover o de clic tiene que emitir sobre el hijo interno, o invocar el `command`
([trampa 35](10-invariantes-y-trampas.md)).

🔴 **Y con el ratón real tampoco da igual del todo.** Ese `_canvas` es **hermano** de los demás hijos
del marco, **no su ancestro**, y Tk manda los *leaves* virtuales solo a los ancestros: si el puntero
abandona el marco **desde un hijo sin `bind`**, el canvas no recibe ningún `<Leave>` y el hover se
queda encendido para siempre ([trampa 37](10-invariantes-y-trampas.md)). La regla que sale de ahí:
**el hover se ata a todos los hijos**, aunque el clic no.

Detalle completo en [07-concurrencia-e-hilos.md](07-concurrencia-e-hilos.md).

---

## 11. Añadir una vista nueva

1. Crear `gui/sidebarButtons/<vista>/<vista>.py` con la cabecera obligatoria.
2. Heredar de `utilsButtons.SidebarButton`, pasando la etiqueta y los dos iconos.
3. Implementar `show_frame()`: `main_window.clear_frame()` → `ViewHeader` → los componentes que
   necesite. **No dibujes nada que ya esté en `gui/components/`.**
4. Registrarla en `MainWindow.load_sidebar_buttons()`, en la lista `destinations` y —si lleva
   contador— en `counter_providers`.
5. **Declararla en `hiddenimports` del `.spec`**, o el `.exe` no arrancará.

Receta detallada en [11 §1](11-playbooks.md).
