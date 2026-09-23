# Fase 3 — Panel de reproducción, barra de controles y pantalla completa

| | |
|---|---|
| **Objetivo** | Que pulsar un servidor reproduzca **dentro de la ventana, acoplado encima de la ficha**: columna de información a la izquierda, vídeo con su barra a la derecha y la lista de episodios debajo. En pantalla completa, solo el vídeo y una barra que se oculta sola. Es la fase que cambia lo que hace la app |
| **Diseño** | [`DISENO-VISUAL.html`](../DISENO-VISUAL.html) — secciones **Vista**, **Barra**, **Estados** (cargando y navegador) y **Pantalla completa**. 🔴 **Manda en lo visual** (regla 11 del plan) |
| **Investigación** | §5 (backend y su API), §6 **entero** (las tres restricciones de interfaz), §8 (fase 3) |
| **Estrena** | `VideoPlayer` — el **12.º** componente compartido —, `player_frame` en `MainWindow` y el token `VIDEO_BG` |
| **Toca** | `src/gui/components/video_player.py` (nuevo), `src/gui/main_window.py`, `src/gui/anime_window.py` (`__play_video`, la columna de información y el desplazamiento de la lista), `src/gui/theme.py` (`VIDEO_BG`) |
| **No toca** | `APIs/` (la capa de resolución ya está hecha), `animesPersistence.py`, las 6 vistas |
| **Riesgo** | 🔴 **Alto** — una superficie nativa dentro de Tk se comporta distinto a cualquier widget del proyecto, y la barra flotante es una ventana aparte |
| **Depende de** | **Fase 0** (el backend validado **y el paso 0.7**) · **fase 1** (`registry.resolve` y `registry.has_resolver`) · **fase 2** (el hilo ya libre) |

---

## Cómo se ve (resumen del diseño)

```
┌ sidebar ┬──────────────────────────────────────────────────────────────┐
│         │ ┌ info 330 px ─────┐ ┌ VideoPlayer 806 px ─────────────────┐ │  fila 0
│         │ │ ← Volver a la    │ │                                     │ │  player_frame
│         │ │   ficha          │ │        superficie 806 × 453         │ │  alto fijo
│         │ │ REPRODUCIENDO    │ │           (VIDEO_BG)                │ │
│         │ │ Título           │ │                                     │ │
│         │ │ Episodio 12 de 24│ ├─────────────────────────────────────┤ │
│         │ │ · servidor HLS   │ │ ⏮ ⟲10 ⏸ 10⟳ ⏭ ──●──── 14:32/23:40 🔊 ⛶ │ │
│         │ │ SERVIDOR  TU PROG│ └─────────────────────────────────────┘ │
│         │ │ [Siguiente ep. 13]                                         │
│         │ ├────────────────────────────────────────────────────────────┤
│         │ │ Episodios      [Mayor a menor ▾] [🔍 Ir al episodio…]      │  fila 1
│         │ │ Episodio 13   Siguiente para ti                 ○ Visto    │  content_frame
│         │ │ Episodio 12   ▮ Reproduciendo · HLS             ○ Visto    │  (la ficha,
│         │ │ Episodio 11                                     ● Visto    │   desplazada)
└─────────┴────────────────────────────────────────────────────────────────┘
```

A 1440 × 910 con la barra lateral desplegada: columna de información de **330 px**, hueco de 24,
superficie de **806 × 453** (16:9), barra de **56 px**. Lo que sobra en alto es de la ficha.

---

## 🔴 Las restricciones que fijan el diseño

Salen del §6 de la investigación y **no son negociables por criterio estético**:

1. **No se pueden superponer widgets Tk sobre el vídeo.** Una superficie incrustada por `winfo_id()`
   es una **ventana hija del sistema operativo**; Tk dibuja sus widgets sobre el único HWND del
   toplevel, así que el vídeo se pinta *encima*. Por eso, en la vista normal, la barra va **fija
   debajo** y los estados (cargando, navegador) **sustituyen** a la superficie en vez de taparla.
   ⚠️ **Lo que sí puede ir encima es otra ventana del sistema**: un `Toplevel` sin marco. Es lo que
   usan la barra flotante de pantalla completa y el deslizador de volumen. Que funcione lo decide el
   **paso 0.7** de la fase 0; si su resultado contradice este párrafo, manda el resultado.
2. 🔴 **El reproductor NO puede vivir dentro de `content_frame`.** 📖 `main_window.py:115` lo declara
   `CTkScrollableFrame`: un canvas con una ventana incrustada. Una superficie nativa dentro de un
   canvas desplazable se recorta mal y se desincroniza al hacer scroll. **`player_frame` es
   hermano de `content_frame`** —en la fila de encima—, no hijo suyo.
3. **Pantalla completa sin reparentar.** mpv fija su `wid` **al inicializarse**; mover la superficie
   a otro toplevel obliga a recrear el reproductor y perder la posición. La pantalla completa es
   `MainWindow.attributes('-fullscreen', True)` + ocultar la barra lateral, la columna de información
   y `content_frame`, y dejar que la superficie ocupe todo. **Es un cambio de geometría, no de
   padres.**
4. **Tapar la superficie es ocultarla, no destruirla.** Las tarjetas de estado van en un frame
   **hermano** de la superficie, en la misma celda: `grid_remove()` de la superficie y `grid()` de la
   tarjeta. La superficie no se destruye nunca mientras el reproductor vive, porque mpv conserva su
   `wid`. ⚠️ Que vuelva a pintar tras reaparecer lo comprueba el paso 0.7.

---

## Antes de empezar

Lectura obligatoria, en este orden:

1. [`DISENO-VISUAL.html`](../DISENO-VISUAL.html) — ábrelo en el navegador. Es el contrato visual.
2. [`docs/10-invariantes-y-trampas.md`](../../docs/10-invariantes-y-trampas.md) — las **42**; aquí
   muerden la **21**, la **29** (`CTkFrame` sin hijos mide 200 × 200), la **32** (la rejilla
   sobrevive a `clear_frame()`), la **33** y la **40** (`bind()` sin `add="+"` y los hijos internos
   de CustomTkinter).
3. [`docs/06-gui-y-vistas.md`](../../docs/06-gui-y-vistas.md) — `MainWindow` como hub, el ciclo de
   vida de una vista y las 11 fichas de componente.
4. [`docs/07-concurrencia-e-hilos.md`](../../docs/07-concurrencia-e-hilos.md).
5. De la investigación: **§5** y **§6 entero**.
6. **La bitácora de la fase 0 en [`ESTADO.md`](../ESTADO.md)**: las versiones, el hilo de los
   eventos, el `reason` de `end-file`, lo que se midió del consumo y **el resultado del paso 0.7**
   (barra flotante, ratón, teclado, ocultar la superficie). 🔴 Si la fase 0 no se ejecutó, **decirlo
   y parar**: esta fase da por buenas cosas que nadie ha comprobado.

**Trampas que van a morder en esta fase:**

- 🔴 **Los eventos de mpv llegan en su propio hilo.** Todo repintado va con `after(0, …)` y
  comprobando `winfo_exists()`. Aquí es más fácil de violar que en el resto de la GUI porque el
  evento **no lo origina el usuario**: llega solo, mientras el vídeo avanza. Y en esta fase hay más:
  además de `time-pos`, **el movimiento del ratón** en pantalla completa.
- 🔴 **Sobre la superficie, Tk no recibe `<Motion>` ni teclas.** Los eventos se los queda la ventana
  de mpv. El ratón y `Esc` se piden **a mpv** (lo que encontrase el paso 0.7), no a Tk.
- 🔴 **Un `CTkFrame` sin hijos conserva 200 × 200 como tamaño pedido** y estira la fila que lo
  contenga. `player_frame` nace vacío: **necesita `height=` explícito** o desmonta la rejilla de
  `MainWindow` en cuanto exista.
- ⚠️ **`clear_frame()` no borra los pesos de la rejilla.** `player_frame` va en una fila con
  `weight=0` y `content_frame` en otra con `weight=1`; al cerrar el reproductor se retira la fila 0
  **y su configuración** ([trampa 32](../../docs/10-invariantes-y-trampas.md)).
- ⚠️ **`winfo_id()` solo vale después de mapear.** Crear el reproductor desde un `after()`, no en el
  constructor del frame.
- 🔴 **Cerrar sin `terminate()` deja mpv vivo.** Al volver a la ficha, al cambiar de vista y al
  cerrar la app. **La barra no tiene ✕**: el cierre normal es «← Volver a la ficha». (La ✕ de la
  tarjeta de fin de episodio, fase 4, cierra solo el aviso, no el reproductor.)
- ⚠️ **El deslizador de volumen es otra ventana.** Pasar el ratón del icono al deslizador dispara
  `<Leave>` en el icono: hace falta un margen de gracia (unos 300 ms) antes de cerrarlo, o se cierra
  al intentar usarlo.

---

## Pasos

### Paso 3.1 — `player_frame` en `MainWindow`, encima de la ficha

- Un frame **hermano** de `content_frame`, en la **fila 0** de la columna de contenido; `content_frame`
  pasa a la **fila 1**. Oculto por defecto. Con `height=` explícito.
- Dos métodos públicos en el hub: **mostrar** el panel (`grid()` de la fila 0, `content_frame` **se
  queda** y encoge) y **ocultarlo** (`grid_remove()` + deshacer el `rowconfigure`). Nada de destruir
  `content_frame`: las vistas cachean estado ahí.
- Al mostrarlo, la ficha de debajo **se desplaza hasta el episodio que suena** y lo marca como fila
  actual: fondo `CARD`, número y texto en `ACCENT`, «▮ Reproduciendo · <servidor>». Sin reconstruir
  la ficha.
- Al ocultarlo, la ficha queda **como estaba**, con el episodio y los servidores desplegados donde el
  usuario los dejó. Es gratis porque nunca se fue.
- ⚠️ La barra lateral sigue visible y en su estado. Solo desaparece en pantalla completa.

### Paso 3.2 — `VideoPlayer`, el componente

`src/gui/components/video_player.py`, cabecera obligatoria, **12.º componente compartido**. Sigue la
regla de oro de `gui/components/`: **una vista compone, no dibuja**, y las variantes son parámetros,
no bifurcaciones del fichero.

Es **la superficie y su barra**; nada más. La columna de información es de la ficha (paso 3.3).

- **Superficie** arriba: un frame con fondo `VIDEO_BG` al que se le pasa `winfo_id()` al backend. A
  su lado, en la misma celda y oculto, el frame de **tarjetas de estado** (restricción 4).
- **Barra** debajo, 56 px, fondo `CARD`, con borde `LINE`. **En este orden**, de izquierda a
  derecha:

  | # | Control | Detalle |
  |---|---|---|
  | 1 | Episodio anterior | Dibujado aquí, **deshabilitado** hasta la fase 4 |
  | 2 | −10 s | |
  | 3 | Play / pausa | **38 × 38, como los demás.** Fondo `ACCENT`, icono `ACCENT_INK`. Al terminar pasa a «repetir» |
  | 4 | +10 s | Deshabilitado al final del episodio |
  | 5 | Episodio siguiente | Dibujado aquí, **deshabilitado** hasta la fase 4 |
  | 6 | Barra de progreso | Ocupa lo que sobra. Se arrastra para buscar |
  | 7 | Tiempo | «14:32 / 23:40», fuente `T_NUM` (Cascadia Mono): los dígitos no bailan. El total en `TXT_3` |
  | 8 | Volumen | **Solo el icono.** Al pasar el ratón, deslizador **vertical** de 160 px con el porcentaje encima |
  | 9 | Pantalla completa | Alterna. Dentro, el icono pasa a «salir» y aparece la tecla `Esc` a su lado |

  🔴 **No hay botón de cerrar.** Es una decisión del diseño aprobado. Si hiciera falta, iría al final
  y habría que anotarlo en *Decisiones*.
- Los iconos (anterior/siguiente, ±10 con el «10» dentro, volumen, pantalla completa) se dibujan
  **con PIL** en tiempo de ejecución, como el resto de glifos del proyecto
  ([`docs/11 §5`](../../docs/11-playbooks.md)): supermuestreo 8x + LANCZOS, variante clara y oscura.
  No se añaden PNG a `resources/` (deuda B11).
- El reproductor recibe un `MediaSource` (url + cabeceras + `kind`), no una URL suelta: las
  cabeceras van a `--http-header-fields`.
- **Progreso**: `observe_property('time-pos')` y `duration` → `after(0, …)` → etiqueta y barra.
  ⚠️ **Mientras se arrastra, no se hace caso a `time-pos`**: si no, el tirador salta hacia atrás.
- **Volumen**: el deslizador sube **por encima de la barra**, sobre el vídeo, así que es un
  `Toplevel` sin marco colocado encima del icono (restricción 1). Margen de gracia al salir del icono.
- **Un parámetro `floating`**: la misma barra, construida dentro de un `Toplevel` para la pantalla
  completa (paso 3.4). Un widget de Tk no cambia de padre, así que son **dos instancias conectadas
  al mismo estado** del reproductor, no un fichero aparte.
- 🔴 **Un `stop()` limpio** que llame a `terminate()` del backend. Lo llaman «← Volver a la ficha»,
  el ocultar del panel, cambiar de vista y cerrar la app.

### Paso 3.3 — La columna de información (la compone la ficha)

330 px a la izquierda del vídeo, dentro de `player_frame`, **sin póster**. De arriba abajo:

- **«← Volver a la ficha»**: botón con borde. Llama a `stop()` y oculta el panel.
- Etiqueta en mayúsculas (`T_LABEL`, `TXT_3`) con el estado: «Reproduciendo», «Cargando»,
  «Terminado», «En el navegador».
- **Título** del anime (22 px, negrita).
- «**Episodio 12** de 24 · servidor HLS» — número en `TXT` y negrita, resto en `TXT_2`.
- «AnimeAV1 · en tu biblioteca» en `TXT_3`. Proveedor y fila **con la identidad de la ficha**
  ([trampa 21](../../docs/10-invariantes-y-trampas.md)).
- **Servidor**: los servidores del episodio que suena, como fichas seleccionables. El activo en
  `ACCENT_SOFT` + borde `ACCENT`. 🔴 **Los que no tienen resolutor llevan ↗** y van en `TXT_3`: se
  sabe **sin red** con `registry.has_resolver(url)` (fase 1). Pulsar otro servidor para el medio,
  resuelve y carga el nuevo.
- **Tu progreso**: la misma barra de «N de M vistos» que `__refresh_seen_bar()` pinta en la ficha.
- Al fondo, **«Siguiente episodio»** con el número a la derecha: botón primario de 44 px. En esta
  fase, **deshabilitado**; lo conecta la fase 4.

### Paso 3.4 — Pantalla completa

- `MainWindow.attributes('-fullscreen', True)`, y ocultar la **barra lateral**, la **columna de
  información** y **`content_frame`**. La superficie ocupa toda la pantalla; lo que no es 16:9 queda
  en `VIDEO_BG`, y lo pinta mpv.
- **La barra flota**: la instancia `floating=True` en un `Toplevel` sin marco (`overrideredirect`) y
  siempre encima (`-topmost`), pegada al borde inferior, **a todo el ancho y 64 px de alto**.
- **Se oculta sola**: aparece al mover el ratón sobre el vídeo y se va **a los 5 s** del último
  movimiento. El movimiento **lo informa mpv**, no Tk (paso 0.7), y llega en su hilo:
  `after(0, …)`. Mientras el ratón está **sobre la barra** no se oculta.
- **El cursor** también se oculta a los 5 s: `cursor-autohide=5000` en mpv, el mismo plazo.
- `Esc` y el botón de salir revierten. `Esc` **se ata en mpv** además de en Tk, porque con el foco en
  la superficie la tecla no le llega a Tk. ⚠️ Que `Esc` no se coma otros atajos ni cierre la ficha.
- Al salir: se destruye el `Toplevel` flotante, vuelven la columna de información, `content_frame` y
  la barra lateral **con su estado plegado o desplegado de antes** (vive en `DB_user.db`, no se toca).
- **Mientras haya una tarjeta de estado a la vista, la barra no se oculta.** Lo pide el usuario para
  la de fin de episodio (fase 4, punto de decisión 7); se aplica igual a «cargando» y a «navegador»,
  que también esperan una acción.
- 🔴 **La barra flota por decisión del usuario** (punto de decisión 6): así el vídeo no cambia de
  tamaño. Si el paso 0.7 dijo que no se puede, esta fase **no empieza**: se pregunta antes. Sacar la
  barra de la rejilla y hacer crecer la superficie no es una salida que se tome por cuenta propia.
- 🔴 **Las tarjetas no son ventanas aparte.** Viven en el frame de tarjetas, hermano de la
  superficie (restricción 4). Por eso, al salir de pantalla completa, **vuelven solas al recuadro
  del vídeo acoplado**: es un cambio de geometría, como todo lo demás. Una tarjeta en un `Toplevel`
  se quedaría en mitad de la pantalla.

### Paso 3.5 — `__play_video()` deja de abrir el navegador

📖 `anime_window.py:1732` es hoy literalmente `webbrowser.open(url)`. Pasa a:

```
clic en servidor → mostrar panel en «Cargando» → hilo daemon → registry.resolve(url)
                 → after(0, …) → montar el reproductor
```

- **Cargando**: tarjeta en el recuadro del vídeo con un aro que gira y «Cargando el episodio N» +
  «<servidor> · <proveedor>». La barra, deshabilitada, con «--:-- / --:--». La columna dice
  «Cargando».
- 🔴 **Si `resolve()` devuelve `None`, `webbrowser.open(url)`** y tarjeta en el recuadro del vídeo:
  icono ↗, «**<Servidor> se abre en tu navegador**», una línea que diga que se ha abierto en una
  pestaña nueva y **qué servidores del mismo episodio sí se ven aquí**, y dos botones: **«Ver aquí
  con <servidor>»** (primario, el primero con resolutor) y «Seguir en el navegador». La fila de
  debajo dice «↗ Abierto en el navegador». Degradación limpia: nunca peor que hoy (regla 2).
- Lo mismo si el reproductor falla al arrancar o el medio devuelve 403: **tarjeta, no un panel negro
  mudo**.
- ⚠️ **Al primer 403 de zilla no se reintenta** (regla 6): se ofrece otro servidor o se cae al
  navegador. MP4Upload cubre los mismos 7/7 episodios.
- **Saltar a un episodio** no necesita nada nuevo: «Ir al episodio…» de la lista de debajo es el
  buscador de la ficha (📖 `__search_episodes()`). Escribes el número, Enter, se queda ese episodio
  con sus servidores y con «← Episodio anterior / Episodio siguiente →». Pulsar uno de sus
  servidores **para el medio actual y entra por este mismo camino**.

---

## Cambios de comportamiento

Esta fase cambia lo que hace la app, así que se declara (regla del proyecto):

| Antes | Ahora |
|---|---|
| Pulsar un servidor abre el navegador **siempre** | Reproduce **encima de la ficha** si el hoster se resuelve; si no, abre el navegador **y lo dice** |
| Los servidores no avisan de adónde llevan | Los que abren el navegador llevan ↗ antes de pulsarlos |
| No hay pantalla completa | Botón y `Esc`; la barra se oculta sola a los 5 s |
| El vídeo se ve con los anuncios del hoster | Se ve sin ellos (⚠️ punto de decisión 5 de `ESTADO.md`) |

---

## Terminado cuando

- [ ] Un episodio de **AnimeAV1** por el servidor `HLS` (fMP4, AV1 1080p) se ve y se oye **encima de
      la ficha**, con la columna de información a la izquierda y la lista debajo, desplazada hasta él.
- [ ] Un episodio de **JKAnime** por `Desu` o `Magi` (HLS MPEG-TS) también.
- [ ] La barra tiene **los nueve controles en el orden del diseño**, sin ✕. Funcionan −10 s,
      play/pausa, +10 s, la búsqueda en la barra, el tiempo, el volumen y la pantalla completa.
      Anterior y siguiente están, deshabilitados (los conecta la fase 4).
- [ ] El volumen es un icono y **el deslizador vertical sale al pasar el ratón**, y se puede usar
      sin que se cierre al pasar del icono a él.
- [ ] Cambiar de servidor desde la columna izquierda para el medio y carga el nuevo. Los servidores
      sin resolutor llevan ↗.
- [ ] Pantalla completa entra y sale; **la barra aparece al mover el ratón y se va a los 5 s**, y el
      cursor con ella; `Esc` sale; la barra lateral vuelve con su estado de antes.
- [ ] Un servidor **Mega** (o Voe/Byse/Okru) **abre el navegador**, enseña la tarjeta con la
      alternativa y no rompe nada.
- [ ] «← Volver a la ficha» devuelve la ficha **como estaba**, con su episodio desplegado.
- [ ] Cerrar la app con el vídeo en marcha **no deja procesos vivos** ni suelta un `Traceback`.
- [ ] `git grep -nE "#[0-9A-Fa-f]{6}" -- src/` sigue devolviendo **solo `theme.py`**.
- [ ] La biblioteca real no se ha tocado: `SELECT COUNT(*) FROM ANIMES` igual antes y después.
      🔴 Esta fase **no escribe en BD**; marcar el visto es de la fase 4.

## Verificación

`python src/app.py`, y **ver y oír** tres episodios:

1. **AnimeAV1 / `HLS`** — el caso principal: HLS fMP4 con la cabecera `Sec-Fetch-Site`. Ejercitar
   los controles, el volumen y la pantalla completa **dejando el ratón quieto 5 s** para ver irse
   la barra.
2. **JKAnime / `Desu`** — HLS MPEG-TS, sin cabeceras. Otro demuxer.
3. **Un hoster no resuelto** (Mega es el fácil: está en 7/7 de AnimeAV1) — tiene que abrir el
   navegador y ofrecer HLS.

Y las pruebas feas, que son donde vive el fallo:

- «← Volver a la ficha» **a mitad** y volver a abrir otro episodio.
- Saltar con «Ir al episodio…» a otro episodio **con el vídeo en marcha**.
- Cambiar de vista desde la barra lateral con el vídeo en marcha.
- Cerrar la **app** con el vídeo en marcha (mirar el gestor de tareas: sin procesos huérfanos).
- Plegar y desplegar la barra lateral con el vídeo en marcha.
- Cambiar de tema claro↔oscuro con el panel abierto **y en pantalla completa** (la barra flotante
  también tiene que cambiar).
- Alt+Tab en pantalla completa: **la barra flotante no puede quedarse encima de otra aplicación**.

Si no se puede abrir ventana Tk o los sitios no responden ese día, cerrar como ⚠️ **terminada sin
verificar** y decirlo. **«El log dice que baja segmentos» no cuenta**: la investigación ya llegó ahí.

## Qué anotar en ESTADO.md

Qué hosters se reprodujeron de verdad y cuáles cayeron al navegador · consumo de CPU observado con
el AV1 · si la barra de progreso pelea con `time-pos` al arrastrar · **cómo quedó la barra flotante**
(si hubo que parar y preguntar, cuándo y qué se decidió) · cómo se detecta el ratón y cómo llega `Esc` · el margen de gracia que
necesitó el deslizador de volumen · si hizo falta algún token más que `VIDEO_BG` · y **cualquier
cosa que no se pudiera hacer como está dibujada**, que va derecha a *Decisiones* y a las trampas de
la fase 6.
