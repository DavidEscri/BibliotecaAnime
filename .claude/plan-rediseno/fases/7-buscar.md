# Fase 7 — Buscar

| | |
|---|---|
| **Objetivo** | El acordeón de 40 géneros pasa a fichas, la paginación se vuelve real y cada resultado avisa si ya lo tienes guardado |
| **Diseño visual** | [DISENO-VISUAL.html#buscar](../DISENO-VISUAL.html#buscar). Ábrelo en el navegador, **no** con `Read` |
| **Estrena** | `GenreChips`, sello «ya lo tienes» |
| **Toca** | `src/gui/sidebarButtons/searchAnimes/searchAnimes.py`, `src/gui/components/genre_chips.py` (nuevo), `poster_grid.py` |
| **No toca** | `APIs/` (el contrato ya devuelve lo que hace falta), `animesPersistence.py` |
| **Riesgo** | Medio — es la vista con más lógica propia de las seis |
| **Depende de** | Fase 1 · fase 2 (`PosterGrid`, `Pager`) · fase 6 (el sello) |

---

## Antes de empezar

- `searchAnimes.py` entero, y `AccordionFilterButton` en `utilsButtons.py`.
- [`docs/05 §2`](../../docs/05-proveedores-y-scraping.md) — qué devuelve cada método del contrato.
- [`docs/03 §7`](../../docs/03-flujos-de-ejecucion.md) — el flujo de búsqueda con paginación.

**Lo que juega a favor:** `search_animes_by_query()` y `search_animes_by_genres_and_order()` ya
devuelven `Tuple[List[AnimeInfo], int]` — resultados **y última página**. La paginación de esta vista
es la única gratis del plan: el `Pager` solo tiene que pedir la página siguiente.

**Trampas que van a morder:**

- Los géneros se pasan **siempre como `AnimeGenreFilter`**, nunca como texto del sitio. Cada
  proveedor traduce internamente si sus slugs son otros
  ([docs/05](../../docs/05-proveedores-y-scraping.md)).
- La búsqueda de esta vista va **a la red**, y `call_with_fallback` prueba otros proveedores si el
  elegido falla **o devuelve vacío**. Un «0 resultados» puede venir de otro sitio distinto al del
  desplegable: la cabecera tiene que decir de quién son los resultados que se están viendo.
- `__show_loading_frame` comprueba `widget.winfo_exists()` antes de tocar nada, porque el frame puede
  haberse destruido mientras llegaba la respuesta. **Conservar esa comprobación.**

---

## Pasos

### Paso 7.1 — `GenreChips`

- Fila de fichas seleccionables construida desde `list(AnimeGenreFilter)`, con
  `refactor_genre_text()` para el texto.
- Se ven las ~7 primeras más una ficha **«Más géneros»** que despliega el resto. Las seleccionadas
  se quedan siempre a la vista, delante, con `ACCENT_SOFT` y borde `ACCENT`, y una ✕ para quitarlas.
- Sustituye a `AccordionFilterButton` en esta vista. **No borrar la clase todavía**: la fase 9
  comprueba si queda huérfana y la retira entonces.

### Paso 7.2 — Sello «ya lo tienes»

Sobre cada resultado que ya esté en la biblioteca, con el `badge=` de la fase 6 y los colores de
`SEE` / `PEN` / `FAV` / `FIN`.

- Se resuelve **en local**, sin una sola petición extra: `get_all_animes()` más la normalización de
  títulos de `AnimeProviderManager.normalize_title()`, que es la misma que usa
  `find_saved_duplicate()`.
- Emparejar **primero por slug y luego por título normalizado**. Hacen falta las dos vías: el slug
  solo coincide si la fila la guardó el mismo proveedor que acaba de responder.
- Es la pieza que más trabajo ahorra: hoy el duplicado solo se detecta al pulsar guardar.

### Paso 7.3 — Paginación real

`Pager` conectado a la última página que devuelve el proveedor. Tamaño de página: el que devuelva el
sitio (no re-trocear en cliente). La cabecera dice «N resultados en *Proveedor*».

### Paso 7.4 — Montar la vista

- Campo de búsqueda grande arriba (620 px), fichas de género debajo, control de orden a la derecha.
- `PosterGrid` de 6 con sellos, `Pager` al pie.
- ⚠️ La petición va en hilo daemon y el repintado vuelve con `after(0, …)`.

---

## Terminado cuando

- [ ] Buscar por texto devuelve resultados y el paginador cambia de página de verdad.
- [ ] Filtrar por 2 géneros + orden devuelve lo mismo que devolvía el acordeón.
- [ ] Un anime que ya tienes guardado sale con su sello y el sello dice la sección correcta.
- [ ] Un anime guardado desde **otro** proveedor también sale sellado (empareja por título).
- [ ] La cabecera dice de qué proveedor son los resultados, aunque haya entrado el fallback.
- [ ] Cambiar de vista a media búsqueda no lanza `invalid command name ...!ctkcanvas`.

## Verificación

`python src/app.py` → Buscar. Buscar «level up» y comprobar que *Ore dake Level Up na Ken* sale
sellado. Buscar «one piece» con AnimeAV1 seleccionado y comprobar que el que tienes guardado como
`one-piece-tv` (AnimeFLV) también sale sellado. Filtrar por Acción + Fantasía. Cambiar de vista
mientras una búsqueda está en vuelo.

Sé educado con el sitio: pocas búsquedas, en serie.

## Qué anotar en ESTADO.md

Si el sello acierta con animes guardados desde otro proveedor · si `AccordionFilterButton` quedó
huérfana (lo retira la fase 9) · tamaño de página que devuelve cada proveedor.
