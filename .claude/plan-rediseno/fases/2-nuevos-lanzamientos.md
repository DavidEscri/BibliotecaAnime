# Fase 2 — Nuevos lanzamientos

| | |
|---|---|
| **Objetivo** | La portada: rejilla de pósters grandes y, encima, los tres animes que dejaste a medias |
| **Diseño visual** | [DISENO-VISUAL.html#nuevos](../DISENO-VISUAL.html#nuevos). Ábrelo en el navegador, **no** con `Read` |
| **Estrena** | `PosterGrid`, `Pager`, `ResumeCard` + la preferencia `last_watched_anime_ids` |
| **Toca** | `src/gui/components/poster_grid.py`, `pager.py`, `resume_card.py` (nuevos), `src/gui/sidebarButtons/recentAnimes/recentAnimes.py`, `src/dataPersistence/userPersistence.py`, `src/gui/anime_window.py` (una línea: registrar el visto) |
| **No toca** | Las otras 5 vistas, `animesPersistence.py`, `APIs/` |
| **Riesgo** | Bajo |
| **Depende de** | Fase 1 (`theme.py`, `ViewHeader`, caché a 248 px) |

---

## Antes de empezar

- [`DISENO.md`](../DISENO.md) §3 (rejilla de 6), §5, §6 (regla de paginación) y §8.
- `src/gui/sidebarButtons/recentAnimes/recentAnimes.py` entero — es corto y es el patrón que copian
  las demás vistas.
- [`docs/03 §1 y §2`](../../docs/03-flujos-de-ejecucion.md) — arranque, pantalla de carga y la
  precarga en segundo plano de sinopsis/géneros/episodios.

**Trampas que van a morder:**

- `num_columns` hoy se calcula con `content_frame.winfo_width() // 150`. Pasa a ser **6 fijo**, pero
  ojo: `winfo_width()` vale 1 antes de mapear, y de ahí venían rejillas de una columna al arrancar.
- La rejilla usa **2 filas de `grid` por fila visual** (póster en `row*2`, título en `row*2+1`).
  La nueva usa lo mismo; si se añade una tercera fila hay que rehacer el índice entero.
- `__preload_recent_animes_info()` escribe en `main_window.recent_animes[index]` desde un hilo
  daemon y comprueba su `generation` antes de escribir. **No romper esa guarda**: sin ella, cambiar
  de proveedor a media precarga mete el anime equivocado en la posición equivocada.

---

## Pasos

### Paso 2.1 — `PosterGrid` y `Pager`

- `PosterGrid(parent, columns=6, poster_size=(176,264), on_click=…)`: celda con póster, título a
  2 líneas y hueco opcional para un sello (`place()`) y para una fila extra bajo el título. Las
  fases 5, 6 y 7 lo reutilizan con otros parámetros; **no bifurcarlo**.
- `Pager(parent, total, page_size, on_page=…)`: «Mostrando A–B de N» + botones. Se **oculta solo**
  si `total <= page_size` ([`DISENO.md`](../DISENO.md) §6).
- Tamaño de página aquí: **12**.

### Paso 2.2 — Registrar lo último visto

- En `userPersistence.py`: **miembro nuevo `LAST_WATCHED_ANIME_IDS` en `UserSettingKey`**
  (`userPersistence.py:40` — las claves son el enum, no cadenas) más
  `get_last_watched_ids()` / `push_last_watched_id(anime_id)`: hasta 3, el más reciente primero, sin
  repetidos. Sin migración: la tabla es clave/valor.
- En `anime_window.py`: llamar a `push_last_watched_id()` al marcar un episodio como visto. Usar
  **`self.persistence_anime_id`**, nunca `anime_info.id`
  ([trampa 21](../../docs/10-invariantes-y-trampas.md)).
- Es la única línea que esta fase toca en `anime_window.py`. El resto de la ficha es la fase 8.

### Paso 2.3 — `ResumeCard` y la banda «Retomar donde lo dejaste»

- Tres tarjetas en fila. Cada una: póster 84 × 118, título a 2 líneas, «Siguiente: episodio N de M»
  y barra de progreso.
- El episodio siguiente sale de `get_watched_episodes()` + la lista de episodios de la fila. Ojo:
  `episodes` se guarda **invertido** ([trampa 2](../../docs/10-invariantes-y-trampas.md)), así que
  hay que ordenar antes de calcular «el siguiente».
- Si no hay nada guardado todavía, la banda **no se pinta** (ni etiqueta ni hueco).

### Paso 2.4 — Montar la vista

- Reescribir `recentAnimes.py` con `ViewHeader` («Nuevos lanzamientos» + «N estrenos · Proveedor»),
  la banda de retomar, `PosterGrid` de 6 y `Pager`.
- Mantener el buscador de la cabecera si ya lo tenía; si no, dejarlo para la fase 9.
- ⚠️ Todo lo que abra una ficha va en **hilo daemon** y repinta con `after(0, …)`
  ([docs/07](../../docs/07-concurrencia-e-hilos.md)). Copiar el patrón, no improvisarlo.

---

## Terminado cuando

- [ ] La rejilla muestra 6 columnas con pósters de 176 × 264, nítidos.
- [ ] El paginador aparece y cambia de página.
- [ ] Tras ver un episodio de un anime, cerrar la app y reabrirla: ese anime está en «Retomar»,
      con el episodio siguiente correcto.
- [ ] Cambiar de proveedor en la barra lateral sigue recargando la portada sin colgarse.

## Verificación

`python src/app.py`. Abrir un anime desde la rejilla, marcar el episodio 3 como visto, volver,
cerrar, reabrir y comprobar que «Retomar» dice «Siguiente: episodio 4». Cambiar de proveedor dos
veces seguidas y comprobar que no se pisan las recargas.

## Qué anotar en ESTADO.md

Si «Retomar» sobrevive al reinicio · qué tamaño de página quedó · si el buscador de la cabecera se
implementó o se pospuso a la fase 9.
