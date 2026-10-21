# Fase 2 — Sacar la petición de servidores del hilo de Tkinter

| | |
|---|---|
| **Objetivo** | Que desplegar los servidores de un episodio deje de congelar la ventana. Cierra la **deuda técnica nº 1** del roadmap: el último sitio de la GUI que sale a la red desde el hilo de la interfaz |
| **Investigación** | §8 (fase 2) y §7 (apartado *Concurrencia*) |
| **Estrena** | Nada — es la fase más pequeña del plan |
| **Toca** | `src/gui/anime_window.py`, solo `__toggle_servers_frame()` (`:1661`) y su alrededor |
| **No toca** | `APIs/`, `animesPersistence.py`, `main_window.py`, las 6 vistas, `APIs/resolvers/` |
| **Riesgo** | Bajo |
| **Depende de** | Nada. Es independiente de las fases 0 y 1 |

---

## Por qué esta fase va antes que la 3

La fase 3 añade una **segunda** petición de red exactamente en este punto: primero se piden los
servidores, luego se resuelve el que se pulse. Hacerlo sobre el hilo de UI convertiría un congelado
de ~2 s en uno de ~4 s. Sacar la primera petición **antes** de añadir la segunda cuesta una fase
pequeña; hacerlo después es reescribir el mismo código dos veces.

Y ya estaba pedido: es la deuda nº 1 de
[`docs/12`](../../docs/12-deuda-tecnica-y-roadmap.md), heredada del cierre del rediseño.

---

## Antes de empezar

Lectura obligatoria, en este orden:

1. [`docs/10-invariantes-y-trampas.md`](../../docs/10-invariantes-y-trampas.md) — aquí muerden la
   **21** (las dos identidades), la **22** y las de CustomTkinter.
2. [`docs/07-concurrencia-e-hilos.md`](../../docs/07-concurrencia-e-hilos.md) — **entero**. Es la
   fase que va de esto.
3. [`docs/13 §8`](../../docs/13-selector-de-proveedor.md) — por qué la petición de servidores lleva
   `provider_id` explícito y `strict=True`.

Y leer `__toggle_servers_frame()` y sus vecinos en `src/gui/anime_window.py` (`:1661` a `:1733`).

**Trampas que van a morder en esta fase:**

- 🔴 **`strict=True` y el `provider_id` explícito no se tocan.** Sin eso se le pide a un sitio el
  slug de otro. Mover la llamada de hilo **no** es ocasión para «simplificar» sus argumentos.
- 🔴 **Antes de repintar hay que comprobar `winfo_exists()`.** El usuario puede cerrar la ficha
  mientras carga; repintar un widget destruido revienta con `invalid command name ...!ctkcanvas`.
  Es el fallo que ya persigue al proyecto (`__show_loading_frame` de `searchAnimes.py` es el
  precedente a copiar).
- ⚠️ **Un segundo clic mientras carga.** Hoy el congelado hace de candado; en cuanto no bloquea, el
  usuario puede desplegar dos episodios seguidos. Hace falta ignorar el segundo, o que la respuesta
  tardía **no pinte** sobre el episodio equivocado (un número de generación, como hace la vista de
  búsqueda desde la fase 7 del rediseño).
- ⚠️ **`cursor="watch"` deja de tener sentido** cuando el hilo de UI está libre: el puntero de espera
  sobre una ventana que responde miente. Sustituirlo por un estado visible en la propia fila.

---

## Pasos

### Paso 2.1 — La petición al hilo daemon

- Sacar `get_anime_episode_servers()` de `__toggle_servers_frame()` a un **hilo daemon**, y repintar
  con `self.after(0, …)` comprobando `winfo_exists()` antes de tocar nada.
- Conservar **tal cual**: el `provider_id` explícito, `strict=True`, y el `AnimeInfo` con el que se
  pide (⚠️ [trampa 21](../../docs/10-invariantes-y-trampas.md): la ficha maneja **dos identidades**
  del mismo anime — la del proveedor que la sirvió y la de la fila guardada. La petición de
  servidores usa la del proveedor que sirvió la ficha; **no cambiarla de sitio por error**).
- Que el **plegado** (segundo clic sobre un episodio ya desplegado) siga siendo instantáneo y no
  dispare petición alguna.

### Paso 2.2 — Estado de carga en la fila

- Fuera el `cursor="watch"`. En su lugar, la fila del episodio muestra que está cargando (texto o
  indicador en `TXT_3`, con los tokens de `theme.py` — 🔴 regla 10 del plan: ningún color literal).
- Si la petición devuelve **lista vacía** —que es lo que hace AnimeFLV siempre, y lo que hace
  cualquier proveedor cuando el episodio no tiene servidores—, decirlo en la fila. Hoy simplemente
  no aparece nada, que es indistinguible de «sigue cargando».
- Si lanza o devuelve `None`, lo mismo: un mensaje, no un hueco.

### Paso 2.3 — Clics solapados

- Un número de generación por despliegue: la respuesta que llegue con generación vieja **se
  descarta**. Es el mismo patrón que ya usa la vista de búsqueda.
- Comprobar el caso feo: desplegar el episodio 3, plegarlo, desplegar el 5, y que la respuesta del 3
  al llegar tarde **no pinte servidores bajo el 5**.

---

## Terminado cuando

- [ ] Desplegar los servidores de un episodio **no congela la ventana**: se puede seguir haciendo
      scroll en la lista mientras carga.
- [ ] Los servidores aparecen bajo la fila del episodio, como antes, y en las posiciones de la
      rejilla que ya usaba la ficha (filas pares para episodios, impar de debajo para servidores).
- [ ] Cerrar la ficha mientras carga **no** produce `invalid command name ...!ctkcanvas`.
- [ ] Desplegar dos episodios seguidos rápido no pinta los servidores del primero bajo el segundo.
- [ ] Un episodio sin servidores lo **dice**, en vez de dejar el hueco vacío.
- [ ] Pulsar un servidor sigue abriendo el navegador — esta fase **no** cambia eso.
- [ ] `strict=True` y el `provider_id` explícito siguen exactamente donde estaban.
- [ ] La biblioteca real no se ha tocado: `SELECT COUNT(*) FROM ANIMES` igual antes y después.

## Verificación

`python src/app.py`. Abrir una ficha desde «Viendo» y:

1. Desplegar servidores de un episodio y **mover la ventana o hacer scroll mientras carga**. Es la
   prueba: antes no se podía.
2. Comparar con el congelado que anotó el **paso 0.1** en `ESTADO.md`, si la fase 0 se ejecutó.
3. Desplegar, plegar y volver a desplegar el mismo episodio.
4. Desplegar el episodio 3 y **cerrar la ficha inmediatamente** (volver a la vista anterior).
   Comprobar la salida de la consola: sin `Traceback`, sin `invalid command name`.
5. Repetirlo con los dos proveedores: AnimeAV1 (que responde) y AnimeFLV si hay alguna fila suya
   (📖 devuelve `[]` siempre — es el caso «sin servidores» gratis).
6. Pulsar un servidor y comprobar que **sigue abriendo el navegador**.

Lanzar la app con `python -u src/app.py` y guardar la salida: lo que se busca es la **ausencia** de
`invalid command name`, y eso solo se ve en el log.

## Qué anotar en ESTADO.md

Congelado antes y después (en segundos, aunque sea a ojo) · cómo se resolvió el solapamiento
(generación o candado) · qué se pinta ahora cuando no hay servidores · y si la deuda nº 1 del
roadmap queda cerrada del todo o quedó algo suelto (la **fase 6** tiene que tacharla en
[`docs/12`](../../docs/12-deuda-tecnica-y-roadmap.md) y en `CLAUDE.md`).
