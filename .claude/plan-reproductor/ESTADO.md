# Estado del plan de reproducción in-app

> Este fichero es la memoria del plan entre sesiones. Lo lee y lo escribe `/reproductor`.
> Si contradice al árbol de trabajo, **gana el árbol**: `git log --oneline` y `git status` mandan.

| | |
|---|---|
| **Fase actual** | **1 · Capa de resolución** — ⬜ no empezada |
| **Situación** | ⚠️ **Fase 0 terminada sin verificar del todo** (2026-09-23): **mpv sigue** como backend; solo falta repetir la prueba de cabeceras contra zilla real, que estaba caído (522). Ver *Qué quedó sin verificar* |
| **Último paso completado** | Fase 0 cerrada |
| **Siguiente paso** | Paso 1.1 — `base.py`: `MediaSource` y `Resolver` ([ficha](fases/1-resolutores.md)). ⚠️ Y en su verificación, **repetir (b) contra zilla real con mpv** (receta en *Qué quedó sin verificar*) |
| **Rama** | **`feature/reproductor-embebido`** — la creó el usuario antes de la fase 0 (lleva el plan y un merge de `develop`). **No se crea `feature/reproductor-in-app`**: ver *Decisiones* |
| **Base** | `f7c88ca` en `feature/reproductor-embebido`; `95abd56` **es ancestro** (llega vía `develop`) |
| **Commits** | automáticos (uno al cerrar cada fase) |
| **Actualizado** | 2026-09-23 (fase 0) |

---

## Tablero

| # | Fase | Situación | Commit | Verificada |
|---|---|---|---|---|
| 0 | Spike de libmpv | ⚠️ terminada sin verificar del todo | commit «Reproductor fase 0 — Spike de libmpv» (`git log --grep "fase 0"`) | Sí, en pantalla, salvo (b) contra zilla real y el audio oído |
| 1 | Capa de resolución | ⬜ no empezada | — | — |
| 2 | Servidores fuera del hilo de Tk | ⬜ no empezada | — | — |
| 3 | Panel de reproducción | ⬜ no empezada | — | — |
| 4 | Navegación y fin de episodio | ⬜ no empezada | — | — |
| 5 | Empaquetado | ⬜ no empezada | — | — |
| 6 | Documentación | ⬜ no empezada | — | — |

**Situación**: ⬜ no empezada · 🟡 en curso · ✅ terminada · ⚠️ terminada sin verificar · ❌ revertida

### Qué quedó sin verificar

Lo que no se ha podido ejecutar en cada fase, para que nadie lo dé por probado. **Empieza vacío.**

> ⚠️ Lo que ya venía sin verificar **de la investigación** está en su §10 y no se repite aquí. Lo
> más gordo — que de mpv no se probó absolutamente nada — es lo que va a tapar la fase 0.

| Fase | Sin verificar | Por qué |
|---|---|---|
| 0 | 🔴 **(b) contra zilla real**: que el servidor de verdad siga exigiendo `Sec-Fetch-Site` y que mpv reproduzca **su HLS fMP4** (otro demuxer que el MPEG-TS probado) | `player.zilla-networks.com` devolvió **522** (origen caído) a las ~23:30 y a las ~23:50 del 2026-09-23. **Receta para repetirlo** (la primera fase que salga a zilla, idealmente la 1 en su verificación): `mpv.MPV(vo="null", ao="null", cache="no")`, cargar `https://player.zilla-networks.com/m3u8/<hash>` **con** `http_header_fields=["Sec-Fetch-Site: same-origin"]` y ver que `time-pos` avanza; repetir **sin** ella y ver `[curl] HTTP error 403` en los segmentos y `end-file` con `reason=4`. Un episodio, dos pasadas separadas |
| 0 | **El audio, oído** | Se comprobó que se decodifica (`aac`) y que avanza con el vídeo, pero no puedo oír. Lo confirma el usuario en la fase 3 |
| 0 | La **deduplicación de hilos**: el callback de `Esc` desde mpv y su `after(0)` | Ya no hacen falta: el teclado llega a Tk. Si en otra máquina llegara a mpv, habría que volver a mirarlo |

---

## Puntos de decisión abiertos

Los hereda el plan de la §9 de la investigación. **Cada uno tiene una fase que lo cierra**; hasta
entonces nadie decide por su cuenta.

| # | Decisión | Quién la cierra | Estado |
|---|---|---|---|
| 1 | 🔴 **¿Marcar el episodio como visto al llegar al final?** Es un supuesto declarado, no una petición, y **escribe en la biblioteca real** | La **fase 4**, preguntando al usuario **antes** de escribir una línea | ⬜ abierta |
| 2 | **¿Se versiona `libmpv-2.dll` en el repo (`vendor/`) o se ignora y se documenta la descarga?** | La **fase 0**, al bajarla | ✅ **cerrada el 2026-09-23: NO se versiona.** La DLL pesa **120 MB** (no ~40): GitHub **rechaza** ficheros de más de 100 MB sin LFS. Vive en `vendor/libmpv-2.dll`, con `vendor/` en `.gitignore`; la descarga se documenta (ver *Decisiones*) |
| 3 | **¿Volumen en la barra de controles?** | El **usuario**, con el diseño | ✅ **cerrada el 2026-09-23: sí.** Icono plegado y deslizador vertical al pasar el ratón |
| 4 | **¿Ofrecer MP4Upload (H.264) como alternativa manual** si el AV1 1080p de AnimeAV1 consume demasiado? | La **fase 0** lo mide; si duele, lo implementa la **fase 3** | ✅ **cerrada el 2026-09-23: NO.** El AV1 1080p cuesta **0,2-0,33 núcleos** por software (dav1d), sin un fotograma perdido, en un i5-11400 con GTX 1070 (sin AV1 por hardware). Y MP4Upload **también es AV1 1080p**, no H.264, así que no sería alternativa |
| 5 | **Legalidad**: reproducir dentro de la app elimina los anuncios del hoster. Decisión del proyecto, no técnica | El usuario, cuando quiera | ⬜ abierta |
| 6 | **¿La barra de pantalla completa flota en un `Toplevel` o sale de la rejilla?** | El **usuario** | ✅ **cerrada el 2026-09-23: flotante**, para que el vídeo no cambie de tamaño. ⚠️ Falta que la fase 0 (paso 0.7) demuestre que se puede. **Si no se puede, se para y se pregunta**: sacar la barra de la rejilla no se aplica sin consultarlo |
| 7 | **La tarjeta de fin de episodio en pantalla completa** | El **usuario** | ✅ **cerrada el 2026-09-23.** Sale también en pantalla completa, centrada, y **la barra de controles se ve todo el rato** mientras está. Lleva una **✕** que cierra solo el aviso. **`Esc`** sale de pantalla completa y la tarjeta **vuelve al recuadro del vídeo acoplado**, no se queda en mitad de la pantalla |

---

## Decisiones tomadas sobre la marcha

Aquí va lo que se decide durante una fase y afecta a las siguientes. Una línea por decisión, con la
fase que la tomó. Empieza vacío a propósito: las decisiones de partida están en el
[README](README.md#lo-que-ya-está-decidido) y en la investigación.

| Fase | Decisión |
|---|---|
| 0 | **Rama de trabajo: `feature/reproductor-embebido`**, no `feature/reproductor-in-app`. La creó el usuario con el plan dentro y ya contiene `feature/ui-redisign` (vía `develop`); sacar otra de `ui-redisign` habría dejado el plan fuera. Las fases siguientes commitean aquí |
| 0 | ⚠️ **La investigación (`.claude/plans/investigacion-reproduccion-in-app-kind-flask.md`) no existe en disco** (buscada el 2026-09-23 en el repo, en git y en `~/.claude`). Lo que las fases necesitan de ella está copiado en las fichas (recetas de zilla, jkplayer y mp4upload en la ficha 1) y en `docs/05`. Quien cite «§N de la investigación» cita un documento que ya no está |
| 0 | **libmpv**: `mpv-dev-x86_64-20260923-git-6fd80b2003.7z` de <https://github.com/shinchiro/mpv-winbuild-cmake/releases/tag/20260923> (build x86_64 **básico**, no el `-v3`, que exige AVX2). `libmpv-2.dll` = **120 779 776 bytes**, sha256 `751131f81b5ce485d046ff08d1a44a93c5455be5135d53c0ab19c56780925ff0`. Reporta `mpv v0.41.0-1055-g6fd80b200`, FFmpeg `N-126773-g7d14defcc`. **Binding: `python-mpv` 1.0.8** en `biblio_anime_env/`. Para la fase 5: el `.exe` crecerá ~120 MB, no ~40 |
| 0 | ⚠️ **`python-mpv` busca la DLL en `%PATH%`** (con `ctypes.util.find_library`), no junto al script: sin ella en la ruta, `import mpv` lanza `OSError: Cannot find mpv-1.dll, mpv-2.dll or libmpv-2.dll`. **Hay que añadir la carpeta de la DLL a `os.environ["PATH"]` antes de `import mpv`** (también `os.add_dll_directory` para sus dependencias). Es la misma trampa que espera en el `.exe` (fase 5) |
| 0 | **En libmpv vienen apagados** `input-default-bindings`, `input-vo-keyboard` y `osc`: mpv **no trae atajos propios** (ni su `Esc`, ni la `q` que cierra, ni su barra en pantalla). `input-cursor` sí viene a `True`. Existen las propiedades `mouse-pos` y `hwdec-current` |
| 0 | ✅ **mpv incrusta en Tk**: `mpv.MPV(wid=str(frame.winfo_id()))` sobre un `CTkFrame(fg_color=negro, corner_radius=0)`, creado desde `after()` tras `update_idletasks()`. `vo=gpu-next`, `hwdec=auto-safe` → `d3d11va` con H.264. Sigue la geometría al encoger y al agrandar la ventana, con bandas negras (letterbox) propias |
| 0 | 🔴 **La §6.1 era más estricta de lo real**: un widget **hijo** del frame del `wid` **no se ve** (0 % de sus píxeles), pero un widget **hermano** —hijo de la raíz, colocado encima con `place(in_=video)` y `lift()`— **sí se ve** (92 %, opaco). Encima del vídeo **sí** se puede poner un widget Tk, siempre que **no** sea descendiente del frame del vídeo y que sea opaco (Tk no tiene transparencia por widget). No cambia el diseño aprobado, pero **abre una alternativa a la barra flotante en `Toplevel`** para la fase 3 (ver paso 0.7) |
| 0 | **Eventos**: `time-pos` llega a **24/s** (a la cadencia de fotogramas); `duration`, `end-file` y los observadores llegan en el hilo **`MPVEventHandlerThread`**. `root.after(0, …)` desde ahí se ejecuta en **`MainThread`** y repinta (24 repintados/s sin errores). Regla para la fase 3: **nunca tocar widgets desde el callback, siempre `after(0, …)`** |
| 0 | 🔴 **`end-file.reason`**: **0 (EOF)** al llegar al final · **2** al `stop()` · **2** al `loadfile(..., "replace")` · **3** al `terminate()`. Parar a mano y cambiar de episodio **dan el mismo código**: la fase 4 tiene que sacar la tarjeta de fin **solo con `reason == 0`**. Con `idle=True` el núcleo sigue vivo tras el EOF (`idle-active=True`) y se puede cargar otro fichero sin recrear el reproductor |
| 0 | **Controles sobre un stream ya empezado** (HLS MPEG-TS de JKAnime): `pause` congela `time-pos` y la imagen · `seek(±10, "relative")` en **0,05-0,06 s** · `seek(300, "absolute")` en **0,35-0,48 s** · **sin `start-file` nuevo** (no reinicia el stream) · `volume` se lee y se escribe. `terminate()` tarda 0,01 s y no deja hilos de mpv vivos |
| 0 | ✅ **La barra flotante en `Toplevel` funciona** (decisión 6 viable): `Toplevel` con `overrideredirect(True)` + `-topmost` **se ve encima del vídeo** a pantalla completa (99 % de sus píxeles) y el vídeo sigue moviéndose alrededor · sus botones **reciben el clic** y el primer plano **sigue siendo de la app** (el foco de Tk pasa a la barra; `bind_all` sigue recibiendo `Esc`) · `withdraw()` 1-6 ms, `deiconify()` 2-3 ms, visible en 0,15 s, sin parpadeo apreciable. ⚠️ Crear la barra con **`update()`**, no `update_idletasks()`: sin mapear del todo, el primer clic se pierde |
| 0 | 🔴 **Con `Alt+Tab`, la barra `-topmost` se queda flotando encima de la otra aplicación** (verificado: encima de la terminal). **Mitigación verificada**: un `after(150)` que mira `GetForegroundWindow()` y, si no es de este proceso, hace `withdraw()` de la barra (y del deslizador de volumen). La fase 3 la necesita |
| 0 | 🔴 **El ratón y el teclado sobre el vídeo llegan a Tk, no a mpv** — con `input-vo-keyboard` **encendido o apagado**: 39-40 de 40 `<Motion>` en el frame del `wid`, `Esc` y `q` los recibe Tk (`bind_all`) y los bindings de mpv (`ESC`, `q`, `MOUSE_MOVE`) y `mouse-pos` **no reciben nada**. La ventana hija de mpv no se queda la entrada. **Consecuencia para la fase 3**: el «mover el ratón muestra la barra» y el `Esc` se atan **en Tk**, como cualquier otro widget; no hace falta marshalling desde mpv. `cursor-autohide` **no sirve** (mpv no ve el ratón): el cursor lo tiene que ocultar Tk |
| 0 | ✅ **La superficie vuelve a pintar tras `grid_remove()` → `grid()`** con el vídeo en marcha, sin recrear el reproductor ni hacer `seek` (3 s oculta). Vale para las tarjetas de estado de la fase 3 |
| 0 | ✅ Entrar y salir de pantalla completa **3 veces** con el vídeo en marcha: la superficie crece y encoge, pinta en ambos casos y no se reinicia |
| 0 | 🔴 **`attributes("-fullscreen", True)` lleva la ventana al monitor PRINCIPAL**, aunque esté en el secundario (de `(2028, 91)` a `(0, 0, 1920, 1080)`), y al salir **vuelve** a su sitio. Con dos monitores, «pantalla completa» sale en el que no estás mirando. La fase 3 tiene que corregirlo (ver entrada siguiente) |
| 0 | ✅ **Pantalla completa en el monitor correcto — receta para la fase 3**: **no usar `-fullscreen`**. Leer el rectángulo del monitor con `MonitorFromWindow(wm_frame, MONITOR_DEFAULTTONEAREST)` + `GetMonitorInfoW`, y hacer `root.overrideredirect(True)` + `root.geometry(f"{w}x{h}+{x}+{y}")`; al salir, `overrideredirect(False)` + la geometría guardada. Verificado: el vídeo llena el monitor secundario, sigue en movimiento y la ventana vuelve a su sitio exacto. Descartados: `-fullscreen` seguido de `geometry` y `geometry` seguido de `-fullscreen` (los dos acaban en el principal) y quitar el marco con `SetWindowLong` (coloca bien, pero al salir descoloca la ventana). ⚠️ **Sin probar juntos**: esta pantalla completa **con** la barra flotante encima (cada pieza por separado sí) |
| 0 | ✅ **El cursor se oculta desde Tk**: `video.configure(cursor="none")` cambia el cursor a uno en blanco sobre la superficie y `cursor=""` lo restaura (verificado por el `hCursor` de `GetCursorInfo`; ⚠️ `CURSOR_SHOWING` no cambia, así que no sirve para comprobarlo). Es lo que sustituye a `cursor-autohide` para ocultarlo a los 5 s |
| 0 | ✅ **Las cabeceras llegan a los segmentos** (prueba (b), **sin zilla**, que estaba caído): servidor HLS local con la **regla de zilla** (playlist 200 siempre; segmentos 403 salvo `Sec-Fetch-Site: same-origin`) y 3 segmentos reales de JKAnime. **Con** `http_header_fields=["Sec-Fetch-Site: same-origin"]`: los 3 segmentos llegan con la cabecera, 200, reproduce 12 s. **Sin ella**: 3 × 403 y no arranca. Los segmentos los pide el cliente **`curl` propio de mpv** (este build ya no usa el HTTP de FFmpeg), que aplica `http-header-fields` a cada petición. ⚠️ **Contra zilla real no se ha podido probar** (ver *Qué quedó sin verificar*) |
| 0 | 🔴 **Un HLS cuyos segmentos dan 403 acaba en `end-file` con `reason=4` (ERROR)**: es la señal para que la fase 3 **caiga al navegador** (degradación). Con `hwdec=auto-safe`, un AV1 sin decodificador hardware **escribe errores en el log** (`Your platform doesn't support hardware accelerated AV1 decoding`, `Failed setup for format cuda`) y cae solo a software: la fase 3 **no** debe tratar los errores de log como fallo de reproducción; el fallo es el `reason=4` |
| 0 | **Consumo** (i5-11400, 12 hilos; GTX 1070 + UHD 730): AV1 1080p MP4Upload `auto-safe` → `hwdec-current=no`, 0,33 núcleos (2,8 %) · AV1 software explícito 0,19 núcleos (1,5 %) · H.264 720p JKAnime `d3d11va` 0,09 núcleos (0,7 %). **0 fotogramas perdidos** en los tres, avance vídeo/reloj 1,00 |
| 0 | **Controles sobre MP4** (AV1 de MP4Upload, puerto 183): igual que en HLS, pero los `seek` tardan **0,5-0,7 s**. ⚠️ **`seek(±10, "relative")` cae en el fotograma clave**: +10 salta +12 a +14,7 s. Para que «+10 s» sea exacto, la fase 3 usa **`reference="relative+exact"`**. `time-pos` llega a ~13/s con AV1 (24/s con H.264): de sobra para la barra |
| 0 | `CTkScrollableFrame`: **el síntoma temido de la §6.2 no aparece** — la superficie se recorta al área visible del canvas y se desplaza con él, sin pintarse sobre lo de fuera. La decisión de no meter el vídeo ahí **no cambia** (el diseño lo pone en su propia fila), pero ya no se apoya en un fallo |
| 0 | 🟢 **DECISIÓN DE BACKEND: mpv SIGUE** (`python-mpv` + `libmpv-2.dll` incrustado vía `wid`, sin proxy). Pasan (a), (c), (d), el consumo y las cinco pruebas de (e); (b) pasa contra la regla de zilla simulada. **No se cae a VLC** |
| 0 | ✅ **Punto 6 viable tal como se decidió**: barra flotante en `Toplevel`, con tres condiciones para la fase 3 — pantalla completa **manual** (no `-fullscreen`), **guarda de primer plano** que oculta la barra al perder el foco la app, y crear la barra con `update()` |
| Diseño (2026-09-23) | **Diseño visual aprobado**, segunda ronda: [DISENO-VISUAL.html](DISENO-VISUAL.html). Reproductor **acoplado encima de la ficha** (`player_frame` fila 0, `content_frame` fila 1, que se queda); columna izquierda sin póster con volver, título, episodio, servidor, progreso y «Siguiente episodio»; barra en el orden anterior · −10 · play/pausa · +10 · siguiente · progreso · tiempo · volumen · pantalla completa, **sin ✕**; pantalla completa con barra flotante que se oculta a los 5 s; «Ir al episodio…» es el buscador de la ficha. Descartados: modo teatro, carril de episodios, pie de información. **Cambia la fase 3 entera, el paso 4.1 y 4.2, y añade el paso 0.7 y `registry.has_resolver()` (fase 1)** |

---

## Bitácora

Una entrada por paso completado, **la más reciente arriba**. Formato:

```
### Fase N · Paso N.M — <qué se hizo>          (AAAA-MM-DD)
- Ficheros: ruta/uno.py, ruta/dos.py
- Verificado: sí/no · cómo
- Pendiente que deja: …
```

<!-- nuevas entradas aquí arriba -->

### Fase 0 · Cierre          (2026-09-23)
- Ficheros commiteados: `.gitignore` (+`vendor/`), `ESTADO.md`. `src/` **sin un cambio**; `DB_Animes.db` intacta (sha256 `0c8d5216…fa96`, igual que al empezar)
- Verificado: `python src/app.py` arranca y pinta «Nuevos lanzamientos» tras la fase. Pulsar un servidor **no se probó a mano** (abriría el navegador del usuario), pero el código no se ha tocado: `__play_video` sigue siendo `webbrowser.open(url)`
- Colores literales: `git grep -nE "#[0-9A-Fa-f]{6}" -- src/` solo devuelve `theme.py`
- Estado: ⚠️ por (b) contra zilla real; **la decisión de backend es firme** (mpv), porque lo que (b) tenía que demostrar de mpv —que manda la cabecera en cada segmento— quedó demostrado en local

### Fase 0 · Pasos 0.3 (scroll), 0.4, 0.6 (CPU) — Scroll, cabeceras y consumo          (2026-09-23)
- Ficheros: solo scratchpad (`p03_scroll.py`, `p04_local.py`, `p06_cpu.py`, `p07d_combo.py`)
- Verificado: **sí, en pantalla** — episodio de **AnimeAV1** (`dandadan` ep. 1 por MP4Upload, AV1 1080p) incrustado en la ventana de prueba con la columna izquierda y la barra, con pausa y saltos; pantalla completa manual + barra flotante juntas en el monitor secundario
- Zilla: **reintento único a las ~23:50, sigue en 522**. No se insistió más (regla 4). (b) se verificó contra un servidor local con su regla
- Resultados en *Decisiones*; lo que queda, en *Qué quedó sin verificar*
- Pendiente que deja: repetir (b) contra zilla real cuando vuelva

### Fase 0 · Paso 0.7 — Pantalla completa, barra flotante, ratón y teclado          (2026-09-23)
- Ficheros: solo scratchpad (`p07b_fs.py`, protecciones en `spike_common.py`)
- 🔴 **Incidente**: la primera pasada mandó `Esc`, `q` y clics sintéticos **a la terminal del usuario**, que estaba maximizada en el mismo monitor encima de la ventana de prueba; el `Esc` interrumpió la sesión. **Corregido**: antes de cada clic se comprueba con `WindowFromPoint` que la ventana es de este proceso, y antes de cada tecla que el primer plano lo es; si no, no se envía y se anota. La lección vale para cualquier fase que verifique la GUI con input sintético
- Verificado: **sí, en pantalla** (capturas del monitor), con `input-vo-keyboard` apagado y encendido. Resultados en *Decisiones*
- Salto de monitor **resuelto** (receta en *Decisiones*) y cursor oculto desde Tk **verificado** (`p07c_monitor.py`)
- Pendiente que deja: nada del 0.7, salvo probar juntas la pantalla completa manual y la barra flotante

### Fase 0 · Pasos 0.3, 0.5 y controles del 0.6 — Incrustación, eventos y controles          (2026-09-23)
- Ficheros: solo scratchpad (`spike_common.py`, `p03_embed.py`); ventana de prueba en el **monitor secundario**
- Medio: JKAnime `kaijuu-8-gou` ep. 1 por `Desu` (`/jkplayer/um` → HLS MPEG-TS de `nika.playmudos.com`, H.264 1280×720, sin cabeceras)
- Verificado: **sí, visto en pantalla** (capturas del frame: imagen en movimiento, subtítulos incrustados, letterbox al redimensionar). Audio: `aac` decodificando y `ao` activo, pero **no oído** — no puedo oír; lo tiene que confirmar el usuario
- Resultados en *Decisiones* (incrustación, §6.1, hilos, `end-file`, controles)
- ⚠️ **Zilla (AnimeAV1 `HLS`) está caído hoy**: `522` de Cloudflare (origen sin responder) a las ~23:30. No es un bloqueo a la IP. El paso 0.4 queda pendiente
- ⚠️ **MP4Upload de AnimeAV1 también es AV1 1920×1080**, no H.264 (`dandadan` ep. 1): el supuesto del punto de decisión 4 no se cumple en este episodio
- Pendiente que deja: `CTkScrollableFrame` (0.3), pantalla completa (0.7), CPU (0.6) y la prueba de cabeceras (0.4)

### Fase 0 · Paso 0.2 — `python-mpv` y `libmpv-2.dll`          (2026-09-23)
- Ficheros: `.gitignore` (+`vendor/`), `vendor/libmpv-2.dll` (ignorada), `biblio_anime_env/` (+`python-mpv` 1.0.8)
- Verificado: sí · `mpv.MPV(vo="null", ao="null")` se construye y se cierra con `terminate()`; versiones leídas de la propia DLL
- Decisión 2 **cerrada**: no se versiona (120 MB > límite de GitHub)
- Pendiente que deja: nada

### Fase 0 · Paso 0.1 — Orientación, rama y foto del «antes»          (2026-09-23)
- Ficheros: ESTADO.md
- Rama: se queda en `feature/reproductor-embebido` (ver *Decisiones*). `95abd56` es ancestro de `HEAD`
- Verificado: sí · `python src/app.py` arranca y pinta «Nuevos lanzamientos» (captura con `PrintWindow`)
- **Línea base de la fase 2**: la petición de servidores que la ficha hace en el hilo de Tk tarda **0,2 s** en AnimeAV1 (`dandadan` ep. 1) y **0,2 s** en JKAnime (`kaijuu-8-gou` ep. 1), medida fuera de la GUI con la misma llamada. En caliente y sin Cloudflare de por medio: el «par de segundos» de CLAUDE.md es el peor caso, no el típico
- Servidores de ese episodio: AnimeAV1 → HLS, UPNShare, Voe, Mega, YourUpload, MP4Upload, DoodStream, Netu, VidHide, StreamTape · JKAnime → Desu, Magi
- De paso: la biblioteca tiene **36 filas**, no 28 (sha256 `0c8d5216…fa96` al empezar la fase)
- Pendiente que deja: nada

### Fuera de fases — Puntos de decisión 6 y 7 cerrados por el usuario          (2026-09-23)
- Ficheros: DISENO-VISUAL.html (✕ en la tarjeta de fin y su versión en pantalla completa), README.md, ESTADO.md, fases/0, 3 y 4
- Verificado: no aplica (solo documentación)
- Pendiente que deja: nada nuevo. La fase 0 sigue siendo la siguiente

### Fuera de fases — Diseño visual aprobado y fichas ajustadas          (2026-09-23)
- Ficheros: DISENO-VISUAL.html (nuevo), README.md, ESTADO.md, fases/0, 1, 3, 4 y 6, `.claude/commands/reproductor.md`
- Verificado: no aplica (solo documentación; `src/` sin tocar)
- Pendiente que deja: los puntos de decisión 6 y 7. **La fase 0 sigue siendo la siguiente**, ahora con el paso 0.7

---

## Cierre del plan

*(lo escribe la fase 6: qué quedó fuera, qué fases se cerraron sin verificar, qué hosters siguen
abriendo el navegador y qué recomendaría como siguiente tarea)*
