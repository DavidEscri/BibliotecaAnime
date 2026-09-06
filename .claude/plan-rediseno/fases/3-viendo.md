# Fase 3 — Viendo

| | |
|---|---|
| **Objetivo** | La vista que más te importa: lista en cascada con póster, título, géneros, progreso y proveedor, y a la derecha el último que estabas viendo |
| **Diseño visual** | [DISENO-VISUAL.html#viendo](../DISENO-VISUAL.html#viendo), y `#claro` es esta misma vista en tema claro. Ábrelo en el navegador, **no** con `Read` |
| **Estrena** | `AnimeRow`, `SidePanel` |
| **Toca** | `src/gui/components/anime_row.py`, `side_panel.py` (nuevos), `src/gui/sidebarButtons/watchingAnimes/watchingAnimes.py` |
| **No toca** | Las otras vistas, `animesPersistence.py`, `APIs/` |
| **Riesgo** | Bajo |
| **Depende de** | Fase 1 · fase 2 (la preferencia `last_watched_anime_ids`) |

---

## Antes de empezar

- [`DISENO.md`](../DISENO.md) §3 (fila de viendo), §5, §6.
- `watchingAnimes.py` entero y el `SavedAnimeSearch` de `utilsButtons.py`.
- [`docs/06 §7`](../../docs/06-gui-y-vistas.md) y la
  [trampa 26](../../docs/10-invariantes-y-trampas.md) — por qué el buscador de estas vistas es local.

**Trampas que van a morder:**

- El buscador **local** (`SavedAnimeSearch`) ya está resuelto y funciona: compara títulos guardados,
  va sin conexión y no depende del proveedor. **Reutilizarlo tal cual.** La versión web se suma
  encima y nunca quita resultados.
- Las 4 vistas de estado abren la ficha con **`open_saved_anime()`**, que elige proveedor y saca la
  petición del hilo de Tkinter. No llamar a `AnimeWindowViewer` directamente: hay que pasarle
  `anime_record=` o se duplica la fila
  ([trampa 21](../../docs/10-invariantes-y-trampas.md)).
- La rejilla actual usa **3 filas de `grid`** por fila visual (póster / título / proveedor). Al pasar
  a lista, ese índice desaparece entero: no adaptarlo, sustituirlo.

---

## Pasos

### Paso 3.1 — `AnimeRow`

`AnimeRow(parent, anime_record, poster_size=(70,100), show_progress=True, action=None)`:

- Póster · título `T_ROW` · géneros en MAYÚSCULAS `T_META` separados por ` · ` · barra de progreso
  con «N de M episodios» · proveedor a la derecha en `TXT_3`.
- Separador `LINE_SOFT` abajo; fondo `CARD_HOVER` al pasar el ratón.
- `action` es un botón opcional que aparece a la derecha en hover. Aquí es **«Episodio N →»**; la
  fase 4 lo usará para «Empezar».
- Los géneros pasan por `refactor_genre_text()`, que ya existe en `utils.py`.
- El progreso sale de `len(watched_episodes)` sobre `len(episodes)` de la fila. **No recalcular
  nada por red**: la vista tiene que funcionar sin conexión.

### Paso 3.2 — `SidePanel`

Panel de 290 px a la derecha con la tarjeta grande: póster a ancho completo (ratio 2:3), título
`T_CARD`, «Lo dejaste en el episodio N · Proveedor», barra de progreso y botón `ACCENT`
**«Seguir por el N+1»**.

- Se alimenta del **primer** id de `last_watched_anime_ids` (fase 2). Si ese anime ya no está en
  «Viendo», se cae al primero de la lista.
- Si la lista está vacía, el panel no se pinta.

### Paso 3.3 — Montar la vista

- `ViewHeader`: «Viendo» + «N animes a medias · M episodios pendientes» + buscador local.
- Cuerpo en dos columnas: lista (flexible) + `SidePanel` (290 fijos).
- **Sin paginador**: son 6 y caben ([`DISENO.md`](../DISENO.md) §6).
- **Fuera** las columnas de estado y de último visto. Dentro de «Viendo» el estado se sabe y el
  capítulo lo dice el progreso.

---

## Terminado cuando

- [ ] La lista muestra los 6 animes con póster, título, géneros, progreso y proveedor.
- [ ] El botón «Episodio N →» aparece en hover y abre la ficha por ese episodio.
- [ ] El panel de la derecha muestra el último visto y su botón lleva al episodio siguiente.
- [ ] El buscador filtra sin conexión (probar con el wifi apagado o cortando la red).
- [ ] Un anime guardado desde AnimeFLV se abre bien con AnimeAV1 seleccionado (es el caso de
      `one-piece-tv`, [trampa 26](../../docs/10-invariantes-y-trampas.md)).

## Verificación

`python src/app.py` → Viendo. Buscar «one piece» y comprobar que sale aunque el proveedor
seleccionado sea otro. Abrir un anime desde la lista y desde el panel lateral. Comprobar que no
aparece ninguna fila duplicada en la biblioteca después.

## Qué anotar en ESTADO.md

Si `AnimeRow` quedó parametrizable de verdad (la fase 4 la reutiliza sin tocarla) · si el buscador
local sigue funcionando sin conexión · comportamiento del panel cuando no hay último visto.
