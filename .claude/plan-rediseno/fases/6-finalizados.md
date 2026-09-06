# Fase 6 — Finalizados

| | |
|---|---|
| **Objetivo** | El archivo: rejilla de 6 con el sello de completado sobre la carátula |
| **Diseño visual** | [DISENO-VISUAL.html#finalizados](../DISENO-VISUAL.html#finalizados). Ábrelo en el navegador, **no** con `Read` |
| **Estrena** | Sello superpuesto en `PosterGrid` |
| **Toca** | `src/gui/sidebarButtons/finishedAnimes/finishedAnimes.py`, `src/gui/components/poster_grid.py` |
| **No toca** | `animesPersistence.py`, `APIs/`, las otras vistas |
| **Riesgo** | Bajo |
| **Depende de** | Fase 1 · fase 2 (`PosterGrid`) |

---

## Antes de empezar

- [`DISENO.md`](../DISENO.md) §3 (rejilla de 6) y §6.
- Lo que dejaron las fases 2 y 5 en `poster_grid.py`.

**Por qué esta vista es rejilla y no lista**, para no discutirlo dos veces: es la única sección donde
no hay ninguna decisión que tomar. No hay progreso que consultar ni cola que ordenar, así que el
diseño puede dedicarse entero a enseñar carátulas.

**Trampa del sello:** en CustomTkinter una etiqueta superpuesta a otra va con **`place()`**, no con
`grid()`. Mezclar los dos gestores en el mismo contenedor es lo que produce widgets que no aparecen
o que se comen a sus hermanos. El sello se coloca con `place()` **sobre el `CTkLabel` del póster**,
no sobre la celda.

---

## Pasos

### Paso 6.1 — Sello en `PosterGrid`

Parámetro nuevo `badge=` que recibe texto, color e icono y lo pinta arriba a la izquierda del
póster: fondo translúcido oscuro, icono en `FIN` y texto **«N / N»**.

- El sello lo reutiliza la fase 7 con otros colores («Viendo», «Pendiente»), así que **no atarlo a
  finalizados**: recibe los valores desde fuera.
- El recuento sale de `len(watched_episodes)` y `len(episodes)` de la fila. Si no coinciden, el
  anime está marcado como finalizado pero no tiene todos los episodios vistos: pintar el sello con
  los números reales, **sin corregir el dato**. Es información, no un error que tapar.

### Paso 6.2 — Montar la vista

- `ViewHeader`: «Finalizados» + «N animes · M episodios vistos».
- `PosterGrid` de 6, póster 176 × 264, con `badge=`.
- Sin paginador mientras quepan en dos filas (12). A partir de ahí, `Pager` con página de 12, igual
  que en nuevos lanzamientos.
- Buscador local con `SavedAnimeSearch`.

---

## Terminado cuando

- [ ] La rejilla muestra 6 columnas con el sello sobre cada póster.
- [ ] El recuento del sello coincide con lo que dice la ficha de ese anime.
- [ ] Un anime finalizado al que le falten episodios por marcar enseña sus números reales.
- [ ] El buscador local filtra sin conexión.
- [ ] El sello quedó parametrizable (la fase 7 lo va a usar con otros colores).

## Verificación

`python src/app.py` → Finalizados. Comparar el sello de un anime con lo que dice su ficha. Buscar
por título. Cambiar a claro y comprobar que el sello sigue legible sobre pósters claros.

## Qué anotar en ESTADO.md

Si el sello quedó genérico · si apareció algún finalizado con episodios sin marcar (es un dato real
de la biblioteca, interesa saberlo).
