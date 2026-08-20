# Fase 8 — Ficha del anime

| | |
|---|---|
| **Objetivo** | Recolocar la ficha: botones de estado que se encienden y se apagan, episodios que no repiten el título, barra de vistos, y el bloque de proveedor conservado |
| **Diseño visual** | [DISENO-VISUAL.html#ficha](../DISENO-VISUAL.html#ficha) — es la única vista dibujada con la barra plegada. Ábrelo en el navegador, **no** con `Read` |
| **Estrena** | Nada nuevo — es recolocación sobre lógica que ya existe y funciona |
| **Toca** | `src/gui/anime_window.py` |
| **No toca** | `animesPersistence.py`, `APIs/`, las 6 vistas |
| **Riesgo** | Medio-alto — son 1 155 líneas y concentra las trampas más caras del proyecto |
| **Depende de** | Fase 1 (`theme.py`) · fase 2 (la línea de `push_last_watched_id`) |

---

## 🔴 Lo que NO se toca en esta fase

`anime_window.py` es el fichero donde un error cuesta filas duplicadas en la biblioteca real. Lo
siguiente ya está resuelto, está bien, y esta fase **solo lo recoloca**:

- **La identidad de persistencia.** `persistence_anime_id`, `persistence_poster_url` y
  `persistence_provider_id` se congelan en el constructor y **no cambian mientras la ficha está en
  pantalla**. Toda operación de BD y de póster pasa por `__persistence_anime_info()`. Es la
  [trampa 21](../../docs/10-invariantes-y-trampas.md) y es la más cara del repo.
- **El aviso de identidad partida** y el botón «Actualizar a X» (`migrate_anime_identity`).
- **`__confirm_save()`**, que compara títulos normalizados al 0,9 antes de crear una fila.
- **El marcado acumulativo** de episodios y la conservación de los posteriores ya vistos.
- **`strict=True` y el `provider_id` explícito** al pedir servidores: sin eso se le pide a un sitio
  el slug de otro.

Lectura obligatoria antes de empezar: [`docs/13 §8 y §14`](../../docs/13-selector-de-proveedor.md) y
las [trampas 21 y 22](../../docs/10-invariantes-y-trampas.md).

---

## Pasos

### Paso 8.1 — Cabecera de la ficha

- Póster 248 × 372 a la izquierda, radio 11.
- Derecha: bloque de proveedor arriba, título `T_SHEET`, sinopsis `T_BODY` en `TXT_2`, géneros como
  fichas, y una **barra de «N de M vistos»** — el único añadido real de la fase, y sale de
  `get_watched_episodes()` sin tocar nada.
- El bloque de proveedor conserva sus **tres líneas**: `Proveedor: X`, `En tu biblioteca: Y` y el
  botón «Actualizar a Z». El ⚠ en `WARN` compara las dos primeras, exactamente como ahora.
- ⚠️ La sinopsis usa hoy un `wraplength` calculado a mano sobre `content_frame.winfo_width()`. Con
  la barra lateral plegable el ancho cambia en caliente: recalcularlo al plegar, o pasar a un
  contenedor que se ajuste solo.

### Paso 8.2 — Botones de estado encendido/apagado

**Cambio de comportamiento.** Hoy los 4 botones cambian de texto («Añadir a favoritos» /
«Eliminar de favoritos»). Pasan a decir siempre **Favorito · Viendo · Pendiente · Finalizado** y a
estar encendidos (fondo `FAV_BG`/`SEE_BG`/`PEN_BG`/`FIN_BG` + texto de su color) o apagados
(borde `LINE`, texto `TXT_2`).

- Los `command` no cambian: siguen alternando entre `add_to_*` y `remove_from_*`.
- Recordar que `FAVOURITE` es independiente y que `WATCHING`/`FINISHED`/`PENDING` son excluyentes:
  encender uno de los tres **apaga los otros dos en pantalla**, igual que en BD.
- Al cambiar un estado, refrescar los contadores de la barra lateral.

### Paso 8.3 — Lista de episodios

- Cada fila: **«Episodio N»** a la izquierda (sin repetir el título del anime), una línea de estado
  en `TXT_3` y el interruptor «Visto» a la derecha. Alto 52.
- Se conserva el corte `[:25]`, el botón de orden y el buscador de episodio.
- Los servidores se despliegan bajo la fila del episodio como hoy, con `CTkSegmentedButton`.
- ⚠️ El interruptor sigue siendo **acumulativo al marcar** y unitario al desmarcar, y sigue
  conservando en BD los episodios posteriores ya vistos. Esa lógica no se toca: se le cambia el
  envoltorio.

---

## Terminado cuando

- [ ] Los 4 botones muestran el estado real al abrir la ficha y al cambiarlo.
- [ ] Marcar el episodio 5 marca del 1 al 5; desmarcar el 3 solo desmarca el 3; los posteriores ya
      vistos siguen ahí al reabrir.
- [ ] El bloque de proveedor enseña las tres líneas y el ⚠ ámbar cuando hay identidad partida.
- [ ] «Actualizar a X» sigue migrando y conservando los episodios vistos.
- [ ] Los servidores se abren para un episodio y el vídeo se lanza en el navegador.
- [ ] **No aparece ninguna fila nueva en la biblioteca** después de todas las pruebas.
- [ ] Plegar la barra lateral con la ficha abierta no recorta la sinopsis.

## Verificación

`python src/app.py`. Abrir *Ore dake Level Up na Ken* desde Viendo (que está guardado desde AnimeFLV
con AnimeAV1 seleccionado: es el caso con ⚠ real). Comprobar el aviso. Marcar y desmarcar episodios.
Abrir servidores. Cambiar los 4 estados y devolverlos a como estaban.

Antes y después: `SELECT COUNT(*) FROM ANIMES`. Tiene que dar lo mismo.

## Qué anotar en ESTADO.md

Recuento de filas antes y después · si el `wraplength` de la sinopsis se resolvió recalculando o
cambiando de contenedor · qué animes se tocaron durante la prueba y si se dejaron como estaban.
