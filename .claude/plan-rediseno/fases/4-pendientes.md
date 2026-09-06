# Fase 4 — Pendientes

| | |
|---|---|
| **Objetivo** | La cola: la misma fila que Viendo sin barra de progreso, ordenable por duración y con «Empezar» sin abrir la ficha |
| **Diseño visual** | [DISENO-VISUAL.html#pendientes](../DISENO-VISUAL.html#pendientes), comparándola con `#viendo`. Ábrelo en el navegador, **no** con `Read` |
| **Estrena** | Nada — es la prueba de que `AnimeRow` quedó bien parametrizada |
| **Toca** | `src/gui/sidebarButtons/pendingAnimes/pendingAnimes.py` y, como mucho, un parámetro nuevo en `anime_row.py` |
| **No toca** | Las otras vistas, `animesPersistence.py`, `APIs/` |
| **Riesgo** | Bajo — es la fase más corta del plan |
| **Depende de** | Fase 3 (`AnimeRow`) |

---

## Antes de empezar

- [`DISENO.md`](../DISENO.md) §3 (fila de pendientes: póster 56 × 80, alto 113) y §7.
- `pendingAnimes.py` y lo que dejó hecho la fase 3 en `anime_row.py`.

**Si esta fase necesita bifurcar `AnimeRow`, algo salió mal en la fase 3.** La forma correcta es
añadir parámetros (`show_progress=False`, `meta=…`), no copiar el componente. Si no hay más remedio,
anotarlo en *Decisiones* de `ESTADO.md`.

**Ojo con el dato que no existe:** `AnimeRecord` **no guarda fechas**. No hay «añadido el…» ni
«visto por última vez el…» en ningún sitio ([docs/04](../../docs/04-modelo-de-datos.md)). Los campos
disponibles son los de la fila y nada más; no inventar columnas de fecha para rellenar la maqueta.

---

## Pasos

### Paso 4.1 — `AnimeRow` sin progreso

Reutilizar el componente con `show_progress=False` y póster 56 × 80. El hueco que deja la barra lo
ocupa el texto de la derecha: **«N episodios · Proveedor»**, donde N es `len(anime_record.episodes)`.

### Paso 4.2 — Orden por duración

- Control de orden en la `ViewHeader`: **Más cortos primero** / Más largos primero / Título (A-Z).
- El orden se resuelve **en memoria** sobre la lista que `MainWindow` ya cachea
  (`pending_animes`). No hace falta tocar `animesPersistence.py` ni consultar la BD.
- Es el único dato que hace útil una cola: siete animes de 12 episodios no son lo mismo que uno de 55.

### Paso 4.3 — «Empezar»

Botón de acción en hover. Encadena lo que ya existe:

1. `update_anime_to_watching(anime_info)` — ojo, **inserta si no existía** y pone `FINISHED` y
   `PENDING` a 0, que es justo lo que se quiere ([docs/04](../../docs/04-modelo-de-datos.md)).
2. `download_anime_poster_by_status(AnimeStatus.WATCHING, …)` para que el póster caiga en la carpeta
   nueva.
3. Abrir la ficha por el episodio 1 con `open_saved_anime()`.
4. Refrescar los contadores de la barra lateral: el anime se ha movido de Pendientes a Viendo.

⚠️ Usar siempre el `AnimeInfo` de **persistencia**, no el de visualización
([trampa 21](../../docs/10-invariantes-y-trampas.md)).

### Paso 4.4 — Montar la vista

- `ViewHeader`: «Pendientes» + «N animes en cola · M episodios» + orden + buscador local.
- Sin paginador (son 7).
- Buscador local con `SavedAnimeSearch`, igual que en la fase 3.

---

## Terminado cuando

- [ ] La lista se ve con póster 56 × 80 y **sin** barra de progreso.
- [ ] El orden por duración funciona en los tres sentidos.
- [ ] «Empezar» mueve el anime a Viendo, actualiza los dos contadores de la barra lateral y abre la
      ficha.
- [ ] Después de «Empezar», el anime **ya no está** en Pendientes al volver.
- [ ] `AnimeRow` sigue siendo un solo componente.

## Verificación

`python src/app.py` → Pendientes. Ordenar por los tres criterios. Pulsar «Empezar» en un anime,
volver a Pendientes y comprobar que ha desaparecido y que aparece en Viendo con progreso 0.
**Deshacerlo después** desde la ficha si no querías moverlo de verdad: escribe en la biblioteca real.

## Qué anotar en ESTADO.md

Si hizo falta tocar `AnimeRow` y por qué · qué anime se movió durante la prueba y si se devolvió a
Pendientes.
