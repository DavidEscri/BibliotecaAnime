# Fase 3 — Panel de reproducción y barra de controles

| | |
|---|---|
| **Objetivo** | Que pulsar un servidor reproduzca **dentro de la ventana**, con barra de controles fija debajo y pantalla completa. Es la fase que cambia lo que hace la app |
| **Investigación** | §5 (backend y su API), §6 **entero** (las tres restricciones de interfaz), §8 (fase 3) |
| **Estrena** | `VideoPlayer` — el **12.º** componente compartido — y `player_frame` en `MainWindow` |
| **Toca** | `src/gui/components/video_player.py` (nuevo), `src/gui/main_window.py`, `src/gui/anime_window.py` (`__play_video`), `src/gui/theme.py` (tokens que falten) |
| **No toca** | `APIs/` (la capa de resolución ya está hecha), `animesPersistence.py`, las 6 vistas |
| **Riesgo** | 🔴 **Alto** — una superficie nativa dentro de Tk se comporta distinto a cualquier widget del proyecto |
| **Depende de** | **Fase 0** (el backend validado) · **fase 1** (`registry.resolve`) · **fase 2** (el hilo ya libre) |

---

## 🔴 Las tres restricciones que fijan el diseño

Salen del §6 de la investigación y **no son negociables por criterio estético**:

1. **No se pueden superponer widgets Tk sobre el vídeo.** Una superficie incrustada por `winfo_id()`
   es una **ventana hija del sistema operativo**; Tk dibuja sus widgets sobre el único HWND del
   toplevel, así que el vídeo se pinta *encima*. Por eso los controles van en **barra fija debajo**
   y no flotando. (⚠️ Si la fase 0 lo verificó, su resultado manda sobre este párrafo.)
2. 🔴 **El reproductor NO puede vivir dentro de `content_frame`.** 📖 `main_window.py:115` lo declara
   `CTkScrollableFrame`: un canvas con una ventana incrustada. Una superficie nativa dentro de un
   canvas desplazable se recorta mal y se desincroniza al hacer scroll. **`player_frame` es
   hermano de `content_frame`**, no hijo suyo.
3. **Pantalla completa sin reparentar.** mpv fija su `wid` **al inicializarse**; mover la superficie
   a otro toplevel obliga a recrear el reproductor y perder la posición. La pantalla completa es
   `MainWindow.attributes('-fullscreen', True)` + ocultar la barra lateral + dejar que el panel
   ocupe todo. `Escape` revierte. Como el panel ya es hermano de `content_frame`, **es un cambio de
   geometría, no de padres**.

---

## Antes de empezar

Lectura obligatoria, en este orden:

1. [`docs/10-invariantes-y-trampas.md`](../../docs/10-invariantes-y-trampas.md) — las **35**; aquí
   muerden la **21**, la **29** (`CTkFrame` sin hijos mide 200 × 200), la **32** (la rejilla
   sobrevive a `clear_frame()`) y la **33**.
2. [`docs/06-gui-y-vistas.md`](../../docs/06-gui-y-vistas.md) — `MainWindow` como hub, el ciclo de
   vida de una vista y las 11 fichas de componente.
3. [`docs/07-concurrencia-e-hilos.md`](../../docs/07-concurrencia-e-hilos.md).
4. De la investigación: **§5** y **§6 entero**.
5. **La bitácora de la fase 0 en [`ESTADO.md`](../ESTADO.md)**: las versiones, el hilo de los
   eventos, el `reason` de `end-file` y lo que se midió del consumo. 🔴 Si la fase 0 no se ejecutó,
   **decirlo y parar**: esta fase da por buenas cosas que nadie ha comprobado.

**Trampas que van a morder en esta fase:**

- 🔴 **Los eventos de mpv llegan en su propio hilo.** Todo repintado va con `after(0, …)` y
  comprobando `winfo_exists()`. Aquí es más fácil de violar que en el resto de la GUI porque el
  evento **no lo origina el usuario**: llega solo, mientras el vídeo avanza.
- 🔴 **Un `CTkFrame` sin hijos conserva 200 × 200 como tamaño pedido** y estira la fila que lo
  contenga (decisión de la fase 1 del rediseño). `player_frame` nace vacío: **necesita `height=`
  explícito** o desmonta la rejilla de `MainWindow` en cuanto exista.
- ⚠️ **`clear_frame()` no borra los pesos de la rejilla.** Si el panel reparte peso al mostrarse,
  tiene que deshacerlo al ocultarse ([trampa 32](../../docs/10-invariantes-y-trampas.md)).
- ⚠️ **`winfo_id()` solo vale después de mapear.** Crear el reproductor desde un `after()`, no en el
  constructor del frame.
- 🔴 **Cerrar sin `terminate()` deja mpv vivo.** Al ocultar el panel, al cerrar la ficha y al cerrar
  la app.

---

## Pasos

### Paso 3.1 — `player_frame` en `MainWindow`

- Un frame **hermano** de `content_frame`, oculto por defecto (§6.2). Con `height=` explícito.
- Dos métodos públicos en el hub: mostrar el panel (oculta `content_frame`) y ocultarlo (lo
  devuelve). Nada de destruir `content_frame`: las vistas cachean estado ahí.
- Al ocultar el panel, **la ficha tiene que volver como estaba**, con el episodio y los servidores
  desplegados donde el usuario los dejó.
- ⚠️ La barra lateral sigue visible durante la reproducción normal; solo desaparece en pantalla
  completa.

### Paso 3.2 — `VideoPlayer`, el componente

`src/gui/components/video_player.py`, cabecera obligatoria, **12.º componente compartido**. Sigue la
regla de oro de `gui/components/`: **una vista compone, no dibuja**, y las variantes son parámetros,
no bifurcaciones del fichero.

- **Superficie de vídeo** arriba: un frame al que se le pasa `winfo_id()` al backend.
- **Barra fija inferior** con los tokens de `theme.py` (🔴 regla 10 del plan: si falta un color, se
  añade el token primero). De izquierda a derecha:
  play/pausa · −10 s · +10 s · **barra de progreso con búsqueda** · tiempo transcurrido/total ·
  volumen · pantalla completa · cerrar.
- La barra **sigue visible en pantalla completa**. Es la decisión de §2 y es lo que la hace
  utilizable sin overlay.
- El reproductor recibe un `MediaSource` (url + cabeceras + `kind`), no una URL suelta: las
  cabeceras van a `--http-header-fields`.
- **Progreso**: `observe_property('time-pos')` y `duration` → `after(0, …)` → etiqueta y barra.
  ⚠️ Que arrastrar la barra no pelee con las actualizaciones que llegan del reproductor mientras se
  arrastra.
- **Volumen**: punto de decisión 3 de [`ESTADO.md`](../ESTADO.md) — asumido que sí. Si el usuario
  dice que no, es un control menos y se anota.
- 🔴 **Un `stop()` limpio** que llame a `terminate()` del backend. Lo llaman: el botón de cerrar, el
  ocultar del panel, salir de la ficha y cerrar la app.

### Paso 3.3 — Pantalla completa

- `MainWindow.attributes('-fullscreen', True)`, ocultar la barra lateral, panel a pantalla completa.
  `Escape` y el propio botón revierten. **Sin reparentar** (§6.3).
- Comprobar que al volver, la barra lateral vuelve **con su estado plegado/desplegado de antes**
  (vive en `DB_user.db`, no se toca).
- ⚠️ Que `Escape` no se coma otros atajos de la app ni cierre la ficha.

### Paso 3.4 — `__play_video()` deja de abrir el navegador

📖 `anime_window.py:1732` es hoy literalmente `webbrowser.open(url)`. Pasa a:

```
clic en servidor → hilo daemon → registry.resolve(url) → after(0, …) → montar el reproductor
```

- 🔴 **Si `resolve()` devuelve `None`, `webbrowser.open(url)`.** Degradación limpia: nunca peor que
  hoy (regla 2 del plan). Vale para Mega, Voe, Byse, Okru y para cualquier hoster que cambie.
- Lo mismo si el reproductor falla al arrancar o el medio devuelve 403: **caer al navegador y
  decírselo al usuario**, no dejar un panel negro.
- ⚠️ **Al primer 403 de zilla no se reintenta** (regla 6): se ofrece otro servidor o se cae al
  navegador. MP4Upload cubre los mismos 7/7 episodios.
- Mientras resuelve, un estado de carga: la resolución son una o dos peticiones HTTP.

---

## Cambios de comportamiento

Esta fase cambia lo que hace la app, así que se declara (regla del proyecto):

| Antes | Ahora |
|---|---|
| Pulsar un servidor abre el navegador **siempre** | Reproduce dentro de la ventana **si el hoster se resuelve**; si no, abre el navegador |
| No hay pantalla completa | `F11`/botón, y `Escape` para salir |
| El vídeo se ve con los anuncios del hoster | Se ve sin ellos (⚠️ punto de decisión 5 de `ESTADO.md`) |

---

## Terminado cuando

- [ ] Un episodio de **AnimeAV1** por el servidor `HLS` (fMP4, AV1 1080p) se ve y se oye **dentro de
      la ventana**.
- [ ] Un episodio de **JKAnime** por `Desu` o `Magi` (HLS MPEG-TS) también.
- [ ] Los **siete controles** funcionan: play/pausa, −10 s, +10 s, búsqueda en la barra, tiempo,
      volumen, pantalla completa. Y el de cerrar.
- [ ] Pantalla completa entra y sale, **la barra de controles se sigue viendo**, y la barra lateral
      vuelve con su estado de antes.
- [ ] Un servidor **Mega** (o Voe/Byse/Okru) **abre el navegador** y no rompe nada.
- [ ] Cerrar el reproductor devuelve la ficha **como estaba**, con su episodio desplegado.
- [ ] Cerrar la app con el vídeo en marcha **no deja procesos vivos** ni suelta un `Traceback`.
- [ ] `git grep -nE "#[0-9A-Fa-f]{6}" -- src/` sigue devolviendo **solo `theme.py`**.
- [ ] La biblioteca real no se ha tocado: `SELECT COUNT(*) FROM ANIMES` igual antes y después.
      🔴 Esta fase **no escribe en BD**; marcar el visto es de la fase 4.

## Verificación

`python src/app.py`, y **ver y oír** tres episodios:

1. **AnimeAV1 / `HLS`** — el caso principal: HLS fMP4 con la cabecera `Sec-Fetch-Site`. Ejercitar
   los siete controles y la pantalla completa.
2. **JKAnime / `Desu`** — HLS MPEG-TS, sin cabeceras. Otro demuxer.
3. **Un hoster no resuelto** (Mega es el fácil: está en 7/7 de AnimeAV1) — tiene que abrir el
   navegador.

Y las pruebas feas, que son donde vive el fallo:

- Cerrar el reproductor **a mitad** y volver a abrir otro episodio.
- Cerrar la ficha entera con el vídeo en marcha.
- Cerrar la **app** con el vídeo en marcha (mirar el gestor de tareas: sin procesos huérfanos).
- Plegar y desplegar la barra lateral con el vídeo en marcha.
- Cambiar de tema claro↔oscuro con el panel abierto.

Si no se puede abrir ventana Tk o los sitios no responden ese día, cerrar como ⚠️ **terminada sin
verificar** y decirlo. **«El log dice que baja segmentos» no cuenta**: la investigación ya llegó ahí.

## Qué anotar en ESTADO.md

Qué hosters se reprodujeron de verdad y cuáles cayeron al navegador · consumo de CPU observado con
el AV1 · si la barra de progreso pelea con `time-pos` al arrastrar · cómo se resolvió el `Escape` ·
si hizo falta algún token nuevo en `theme.py` · y **cualquier restricción del §6 que resultara ser
distinta en la práctica**, que va derecha a *Decisiones* y a las trampas de la fase 6.
