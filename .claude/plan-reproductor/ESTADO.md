# Estado del plan de reproducción in-app

> Este fichero es la memoria del plan entre sesiones. Lo lee y lo escribe `/reproductor`.
> Si contradice al árbol de trabajo, **gana el árbol**: `git log --oneline` y `git status` mandan.

| | |
|---|---|
| **Fase actual** | **Plan cerrado** — las 7 fases hechas (ver *Cierre del plan*, al final) |
| **Situación** | ✅ **Fase 6 terminada** (2026-10-20): `CLAUDE.md` y 11 documentos de `.claude/docs/` al día con el reproductor, **12 trampas nuevas** (43-54) más la 18f, 0 enlaces rotos de 903, prueba de humo sobre copia con JKAnime/Desu visto en pantalla. ✅ **El audio lo ha oído el usuario** (2026-10-21: «los episodios se escuchan perfectamente»). La prueba de humo destapó la **trampa 54** (zilla lento → «Cargando» sin tope, deuda B15) |
| **Último paso completado** | Fase 6 cerrada (paso 6.4: cierre del plan) |
| **Siguiente paso** | Ninguno dentro del plan. Recomendación en *Cierre del plan* |
| **Rama** | **`feature/reproductor-embebido`** — la creó el usuario antes de la fase 0 (lleva el plan y un merge de `develop`). **No se crea `feature/reproductor-in-app`**: ver *Decisiones* |
| **Base** | `f7c88ca` en `feature/reproductor-embebido`; `95abd56` **es ancestro** (llega vía `develop`) |
| **Commits** | automáticos (uno al cerrar cada fase) |
| **Actualizado** | 2026-10-21 (audio confirmado por el usuario: fases 0 y 3 pasan a ✅) |

---

## Tablero

| # | Fase | Situación | Commit | Verificada |
|---|---|---|---|---|
| 0 | Spike de libmpv | ✅ terminada | commit «Reproductor fase 0 — Spike de libmpv» (`git log --grep "fase 0"`) | Sí, en pantalla. (b) contra zilla real ✅ **el 2026-10-20** (en la fase 4). Audio oído por el usuario ✅ **el 2026-10-21** |
| 1 | Capa de resolución | ✅ terminada | commit «Reproductor fase 1 — Capa de resolución» (`git log --grep "fase 1"`) | Sí, contra los sitios y en pantalla (B1). `ZillaResolver` ✅ **el 2026-10-20** (en la fase 4) |
| 2 | Servidores fuera del hilo de Tk | ✅ terminada | commit «Reproductor fase 2 — Servidores fuera del hilo de Tk» (`git log --grep "fase 2"`) | Sí, en la app (copia) con Tk y red reales: 16/16 comprobaciones y capturas |
| 3 | Panel de reproducción | ✅ terminada | commit «Reproductor fase 3 — Panel de reproducción» (`git log --grep "fase 3"`) | Sí, en pantalla sobre copia: AnimeAV1/MP4Upload y JKAnime/Desu y Magi, 47 comprobaciones y capturas. `HLS` ✅ **el 2026-10-20** (en la fase 4). Audio oído por el usuario ✅ **el 2026-10-21** |
| 4 | Navegación y fin de episodio | ✅ terminada | commit «Reproductor fase 4 — Navegación y fin de episodio» (`git log --grep "fase 4"`) | Sí, en pantalla sobre copia de las dos BD: 57 + 12 + 5 comprobaciones con clics y `Esc` reales, y capturas. BD real intacta |
| 5 | Empaquetado | ✅ terminada | commit «Reproductor fase 5 — Empaquetado» (`git log --grep "fase 5"`) | Sí, desde el `.exe` en una carpeta fuera del repo: AnimeAV1 `HLS` y JKAnime Desu se ven, UPNShare abre el navegador, capturas. Audio oído por el usuario el 2026-10-21 (⚠️ no consta si también desde el `.exe`) |
| 6 | Documentación | ✅ terminada | commit «Reproductor fase 6 — Documentación» (`git log --grep "fase 6"`) | Sí: barrido de enlaces (0 rotos de 903), 295 identificadores citados cotejados con `src/`, el script sin red de `docs/09 §6h` ejecutado y prueba de humo sobre copia (Desu visto, capturas). `HLS` no se vio en la prueba: zilla iba lento (trampa 54) |

**Situación**: ⬜ no empezada · 🟡 en curso · ✅ terminada · ⚠️ terminada sin verificar · ❌ revertida

### Qué quedó sin verificar

Lo que no se ha podido ejecutar en cada fase, para que nadie lo dé por probado. **Empieza vacío.**

> ⚠️ Lo que ya venía sin verificar **de la investigación** está en su §10 y no se repite aquí. Lo
> más gordo — que de mpv no se probó absolutamente nada — es lo que va a tapar la fase 0.

| Fase | Sin verificar | Por qué |
|---|---|---|
| 0 | 🔴 **(b) contra zilla real**: que el servidor de verdad siga exigiendo `Sec-Fetch-Site` y que mpv reproduzca **su HLS fMP4** (otro demuxer que el MPEG-TS probado) | `player.zilla-networks.com` devolvió **522** (origen caído) a las ~23:30 y a las ~23:50 del 2026-09-23. **Receta para repetirlo** (la primera fase que salga a zilla, idealmente la 1 en su verificación): `mpv.MPV(vo="null", ao="null", cache="no")`, cargar `https://player.zilla-networks.com/m3u8/<hash>` **con** `http_header_fields=["Sec-Fetch-Site: same-origin"]` y ver que `time-pos` avanza; repetir **sin** ella y ver `[curl] HTTP error 403` en los segmentos y `end-file` con `reason=4`. Un episodio, dos pasadas separadas |
| 0 · 3 · 4 · 5 | ✅ **El audio, oído — confirmado por el usuario el 2026-10-21** («los episodios se escuchan perfectamente»). Cierra las cuatro filas de audio de abajo. No consta si lo oyó también desde el `.exe` | — |
| 0 | **El audio, oído** | Se comprobó que se decodifica (`aac`) y que avanza con el vídeo, pero no puedo oír. Lo confirma el usuario en la fase 3 |
| 1 | 🔴 **`ZillaResolver` contra el zilla real**: que `m3u8/<hash>` siga siendo el playlist y que sus segmentos sigan dando 403 sin `Sec-Fetch-Site` | `player.zilla-networks.com`: el playlist agotó el tiempo (15 s) en **los 3 episodios** probados el 2026-09-24, y `play/` dio **403 de Cloudflare**. ✅ **Es caída del origen** (522 también desde otra IP). Repetir cuando vuelva (ver *Decisiones*, cobertura). La conversión `play/` → `m3u8/` y la cabecera **sí** se comprobaron sin red. **Es la misma pasada que la (b) de la fase 0**: resolver con `registry.resolve()`, bajar el playlist, un segmento con y sin la cabecera, y cargarlo en mpv |
| 1 | **B2 con un `Okru` real** | Ningún episodio probado ofrecía `Okru` el 2026-09-24 (One Piece ep. 1 ya no lo trae). Verificado con HTML sintético pasado por `get_anime_episode_servers()`: sale `https://jkanime.net/jkokru.php?u=…` |
| 1 | **La app lanzada desde la raíz con la BD real** | Se lanzó una **copia** de `src/` con copia de la BD (en el scratchpad): abrir una ficha y entrar en «Nuevos lanzamientos» **escriben** en la biblioteca (refresco de episodios, `provider_id`), y la regla 3 lo prohíbe fuera de la fase 4. El código es el mismo byte a byte |
| 2 | **El clic real con el ratón sobre la fila** y **el scroll a mano mientras carga** | El arnés llama a `__toggle_servers_frame` directamente (la atadura `<Button-1>` → `on_click` no se ha tocado) y demuestra que el bucle de eventos queda libre midiendo un latido de 10 ms (hueco máximo de 0,03 s durante la petición, 0,12 s con una de 3 s en vuelo), no arrastrando la barra. Lo confirma el usuario al usar la app |
| 2 | **La app lanzada desde la raíz con la BD real** | Igual que en la fase 1: se lanzó una **copia** byte a byte de `src/` (comprobado con `diff -r`) con copia de la BD, porque abrir fichas escribe en la biblioteca (regla 3) |
| 3 | 🔴 **AnimeAV1 por `HLS` (zilla) reproducido en la app** | `player.zilla-networks.com` sigue sin responder el 2026-09-24 a las ~00:40 (timeout de 15 s en el playlist, **tercer día**). En la app, `HLS` resuelve, mpv agota su espera y **cae al navegador a los ~20 s** ofreciendo MP4Upload: la degradación sí está verificada. El caso AV1 1080p dentro de la app se verificó con **MP4Upload**. Cuando zilla vuelva: abrir `dandadan` ep. 1, pulsar `HLS` y **ver** que arranca (misma pasada que las pendientes de la fase 0 y la 1) |
| 3 | **El audio, oído** | Decodifica `aac` en los tres medios y avanza con el vídeo; el volumen y el silencio cambian las propiedades de mpv. No puedo oír: **lo confirma el usuario** abriendo un episodio |
| 3 | **La app lanzada desde la raíz con la BD real** | Igual que en las fases 1 y 2: copia byte a byte de `src/` (`diff -r`) con copia de la BD. `app.py` de la copia arranca, sigue viva y se cierra por la ventana con código 0 |
| 3 | **Salir de pantalla completa con la barra lateral plegada** | Se probó con la barra desplegada (vuelve igual). El mecanismo es el mismo (se guarda y se restaura el `minsize` de la columna), pero plegada no se ejecutó |
| 3 | **Dos monitores en pantalla completa** | La app se probó en el principal. La receta es la de la fase 0 (que sí se probó en el secundario) |
| 0 · 1 · 3 | ✅ **Zilla, resuelto el 2026-10-20** (las tres filas 🔴 de arriba): el origen ha vuelto. `registry.resolve()` convierte `play/` en `m3u8/` con `Sec-Fetch-Site: same-origin`; el playlist es **HLS fMP4** (`EXT-X-MAP`, segmentos `segs/<hash>/NNN.html` que empiezan por `styp`); un segmento da **200 con la cabecera y 403 sin ella**; y en la app `dandadan` ep. 1 por `HLS` **se ve** a los 2,3 s (AV1 1920×1080 por software, `aac`, 0 fotogramas perdidos, `time-pos` avanza 5 s en 5 s). El 403 de `play/` a `requests` ya no importa: el resolutor no pide esa página | — |
| 4 | **El audio, oído** | Igual que en las fases 0 y 3: decodifica `aac`, pero no puedo oír. **Lo confirma el usuario** |
| 4 | **La app lanzada desde la raíz con la BD real** | Se lanzó `MainWindow` del `src/` real (no una copia) con `get_resource_path` desviado al sandbox para todo `resources/`, porque abrir fichas y terminar episodios **escriben**. Arranca, se recorre y se cierra con código 0 dejando solo `MainThread` |
| 4 | **La ✕ en pantalla completa** | Se pulsó en la vista acoplada. En pantalla completa la tarjeta es la misma (mismo frame) y la ✕ llama al mismo `hide_card()`, pero no se pulsó allí |
| 4 | **La tarjeta «Sin servidores» al navegar** y **el corte antes del final** (`END_TOLERANCE_S`) | Ningún episodio probado se quedó sin servidores ni cortó el stream. Son dos ramas cortas leídas en el código, sin ejecutar |
| 4 | **El primer episodio con «anterior» apagado al pulsar un servidor con la ventana a medio cargar**, la ordenación descendente de AnimeFLV | Anterior apagado en el ep. 1 **sí** se vio (`dandadan`, captura). AnimeFLV está en desuso; el cálculo de anterior/siguiente va por número, no por el orden de la lista |
| 5 | **El audio, oído, desde el `.exe`** | Igual que en las fases 0, 3 y 4. **Lo confirma el usuario** lanzando el `.exe` |
| 5 | **El `.exe` en una máquina sin el entorno de desarrollo** | Se probó en esta máquina, desde el scratchpad (fuera del repo) y sin la DLL en `%PATH%` (comprobado): el proceso la cargó de `_internal\vendor`. Otra máquina limpia no la hay |
| 5 | **El segundo `.exe` (recompilado con los avisos nuevos) no se volvió a lanzar** | Mismas entradas que el primero salvo los tres ficheros legales, que se copian tras `COLLECT` (comparados con `cmp`). El que se lanzó y reprodujo es el primero |
| 5 | **La receta de FFmpeg se leyó de `master`** (2026-10-20), no de la etiqueta `20260923` | La licencia (`--enable-gpl --enable-version3`, sin `nonfree`) lleva años igual en esa receta, pero no se comprobó en la etiqueta exacta. Hacerlo antes de distribuir |
| 0 | La **deduplicación de hilos**: el callback de `Esc` desde mpv y su `after(0)` | Ya no hacen falta: el teclado llega a Tk. Si en otra máquina llegara a mpv, habría que volver a mirarlo |
| 6 | **`HLS` (zilla) en la prueba de humo** | zilla respondía muy lento el 2026-10-20 por la tarde: el medio tardó ~70 s en abrirse (log de mpv en el scratchpad, `diag_hls_mpv.log`), y se dejó de esperar. Se verificó la reproducción con **JKAnime / Desu** (3,4 s, H.264 720p `d3d11va`, `aac`, 0 pérdidas, `time-pos` 4,96 s en 5,0 s, captura). `HLS` sí se había visto ese mismo día en las fases 4 y 5. Lo que destapó es la **trampa 54** |
| 6 | **La prueba de humo, con la BD real** | Se lanzó el `MainWindow` del `src/` real con `get_resource_path` desviado a una copia de las dos BD (abrir fichas y entrar en la portada escriben). sha256 de las dos BD reales idéntico antes y después |
| 6 | **Las anclas de los enlaces, en GitHub** | El barrido calcula las anclas con el algoritmo de GitHub (minúsculas, fuera la puntuación y los emojis, espacios a guiones), pero no se han abierto en GitHub. Los ficheros enlazados sí existen todos |
| 6 | **Las anclas `:línea` que esta fase no tocó** | `2f8a51d` (justo antes del plan) desplazó las de casi todos los módulos; esta fase reancló las de lo que documentó (y §1, §6 y §7 de `docs/07` enteras), y avisa del resto en las cabeceras |

---

## Puntos de decisión abiertos

Los hereda el plan de la §9 de la investigación. **Cada uno tiene una fase que lo cierra**; hasta
entonces nadie decide por su cuenta.

| # | Decisión | Quién la cierra | Estado |
|---|---|---|---|
| 1 | 🔴 **¿Marcar el episodio como visto al llegar al final?** Es un supuesto declarado, no una petición, y **escribe en la biblioteca real** | La **fase 4**, preguntando al usuario **antes** de escribir una línea | ✅ **cerrada el 2026-10-20 por el usuario: SÍ.** Llegar al final (`end-file` con `reason == 0`) marca el episodio con la semántica acumulativa de siempre, **solo si el anime ya está en la biblioteca** (nunca crea fila), con la identidad de la fila guardada. La tarjeta lleva la franja «✓ Marcado como visto · N de M» |
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
| 1 | **Capa `APIs/resolvers/`**: `base` (`MediaSource`, `Resolver`, `url_host`, `BROWSER_USER_AGENT`), `zilla`, `jkplayer`, `mp4upload`, `registry` (`resolve`, `has_resolver`). **Solo importa stdlib, `requests` y a sí misma** (ni `APIs.<sitio>` ni `gui/`): el UA de navegador está duplicado a propósito respecto a `jkanime.py`. `__subsystem__ = "APIs.resolvers"`. La red de seguridad de «nunca lanza» está en **dos capas**: cada resolutor captura `RequestException`, y `registry` captura cualquier otra excepción de `matches()` o `resolve()` y devuelve `None` |
| 1 | **Cobertura medida el 2026-09-24** (3 episodios × 2 proveedores): **MP4Upload 3/3** (206, `ftyp`, AV1 en `a3`/`a4.mp4upload.com:183`) · **Desu/Magi 7/7** (206, `#EXTM3U`, `nika.playmudos.com`) · **Desuka (`/jkplayer/jk`) 1/1** (206, `ftyp`, `jkplayers.com/stream/jkmedia/…`) · **zilla 0/3**: el playlist `m3u8/` no responde (timeout de 15 s) **en los 3 episodios**, y la página `play/` da **403 de Cloudflare en 0,1 s** (comprobado a petición del usuario, 3 peticiones sueltas). **No es de un episodio.** ✅ **Caída del origen, confirmada**: desde **otra IP** (WebFetch) el mismo playlist da **522** (`Retry-After: 120`), y el usuario tampoco lo reproduce en su navegador (en el iframe de AnimeAV1 sale «ha rechazado la conexión», que es como Chrome pinta una página de error de Cloudflare dentro de un iframe). ⚠️ Queda sin explicar el **403 de `play/`** a `requests`: puede ser un filtro de Cloudflare contra clientes que no son navegador. El resolutor no pide esa página, pero **cuando zilla vuelva, mirar si el `m3u8/` también lo da**, porque eso sí afectaría a mpv Sin resolutor, abren el navegador: UPNShare, Voe, Mega, YourUpload, DoodStream, Netu, VidHide, StreamTape |
| 1 | **JKAnime `um`/`umv`: funciona el anclaje en claro** (la regex del `.m3u8`, que casa con `hls.loadSource(...)`); el de `atob()` queda de respaldo y **también** trae la URL. El GET al reproductor va con `Referer: https://jkanime.net/` (no el del episodio, que el resolutor no conoce) y responde 200. `expires_at` = parámetro `e=` → **~3 h** desde la resolución |
| 1 | **Cabeceras sin cambios respecto a la investigación**: `jkplayers.com` **con** `Referer` → **410**; mp4upload con `Referer: https://animeav1.com/` → **403**, con el suyo → 206. ✅ La URL de `/jkplayer/jk` **lleva la IP pública del cliente** en el path: no se resuelve en una máquina y se reproduce en otra |
| 1 | `MediaSource.expires_at = None` significa «la URL no declara caducidad», no «no caduca»: mp4upload la da `None` y su token parece de sesión. No hay caché en ningún sitio, así que da igual hoy; **la fase 3 no debe guardar un `MediaSource` para reutilizarlo** |
| 1 | **B1: se numeran los repetidos** («Desu», «Desu 2»…), no se descartan: son URLs distintas (`t=`/`op=` diferentes). Lo hace `AnimeWindowViewer.__server_url_map()`; ✅ visto en pantalla con One Piece ep. 1 de JKAnime (5 botones) y cada botón abre su propia URL. **La fase 3 tiene que conservar esas etiquetas** en su selector de servidor |
| 1 | **B2 en el proveedor**: `urljoin(f"{BASE_URL}/", …)` en `JKAnime.get_anime_episode_servers()`. `Okru` sigue **sin resolutor** (`has_resolver` → `False`): abre el navegador, ahora con una URL absoluta |
| 2 | **Solapamiento: un número por despliegue, no candado.** `__servers_request_seq` numera cada despliegue y `__servers_requests[episode_id]` guarda el que está en vuelo; plegar, redesplegar o repintar la lista (`__display_episodes`) lo quita o lo cambia, y `__show_servers` descarta la respuesta cuyo número no coincide. Se pueden tener varios episodios desplegados a la vez, como antes. **La fase 3 debe hacer lo mismo con la resolución** (segunda petición en este mismo punto): comparar un número antes de pintar |
| 2 | **Dónde entra la fase 3**: el `CTkSegmentedButton` se construye en **`__show_servers()`** (ya en el hilo de Tk), no en `__toggle_servers_frame()`; su `command` sigue siendo `__play_video` → `webbrowser.open`. Las etiquetas numeradas de B1 salen de `__server_url_map()` como antes |
| 2 | **Qué se pinta ahora**: al desplegar, la fila dice «Buscando servidores…» (línea de apoyo, `TXT_3`) y el hueco de debajo también, a la altura de los botones que va a sustituir. Sin servidores —lista vacía **o** excepción, que el gestor no distingue— la fila dice «Sin servidores» y el hueco «<Proveedor> no ha devuelto servidores para este episodio · prueba con otro proveedor…». **Desaparecen** el `cursor="watch"` y el `messagebox` de «Sin servidores disponibles». La línea de apoyo sale de `__servers_states`, que sustituye a mirar `__servers_frames` |
| 2 | **Abrir la ficha por un episodio** (`__focus_on_episode`) llama a `__toggle_servers_frame(..., scroll_into_view=True)`: se desplaza al desplegar y **otra vez al llegar los servidores**, porque el hueco crece. `FOCUS_DELAY_MS` se queda (50 ms) con otro motivo: medir la fila con la ficha ya colocada |
| 2 | **Congelado antes y después**: antes, lo que tardase la petición (0,2-0,26 s típico en AnimeAV1 y JKAnime, «un par de segundos» en el peor caso) con la ventana parada. Después, **0,03 s** de hueco máximo en el bucle durante la petición real y **0,12 s** con una petición forzada de 3 s. ⚠️ Abrir la ficha **entera** sigue parando el bucle **0,45-0,68 s**, pero eso es construir los widgets de la ficha en el hilo de Tk, no red: no es de esta fase. **La deuda nº 1 del roadmap queda cerrada del todo** (la fase 6 la tacha en `docs/12`, `docs/07` C5 y `CLAUDE.md`) |
| 3 | 🔴 **Los callbacks de mpv no llaman a Tk, ni con `after()`**: dejan el dato en atributos (posición, duración, pausa) o en una `queue.Queue` (`start-file`, `playback-restart`, `end-file`) y el hilo de Tk los recoge con un **sondeo de 100 ms** (`VideoPlayer.__poll`). Motivo: `after()` desde otro hilo **espera** a que Tk lo atienda, y `terminate()` desde Tk espera a ese hilo; juntas se bloquean. **La fase 4 no debe cambiar esto**: el fin de episodio ya le llega a la ficha por `on_end`, en el hilo de Tk |
| 3 | **Qué es «empezar» y qué es «terminar»**: empieza con el primer `playback-restart` tras su `start-file` (hasta entonces sigue la tarjeta de «Cargando» encima). Un `end-file` antes del `start-file` del medio nuevo es del anterior y se ignora. `reason 0` → `on_end` (estado «Terminado», play pasa a repetir, +10 apagado); `reason 4` → `on_error` → navegador. **La tarjeta de fin la pone la fase 4 en `on_end`** |
| 3 | **`force-window=yes`**: la ventana de mpv se crea una vez y no se destruye al parar ni al cambiar de servidor (con `no`, cada `stop` la destruía y la volvía a crear desde otro hilo) |
| 3 | **`network-timeout=15`**: un servidor muerto (zilla) cae al navegador a los **~20 s** de pulsarlo, con la tarjeta de «Cargando» mientras tanto. Bajarlo más arriesga falsos fallos en hosters lentos |
| 3 | **La tarjeta de «Cargando» va encima de la superficie ya mapeada** (`lift()`), no en su lugar: mpv necesita la ventana puesta para crear su salida de vídeo. Las tarjetas finales (navegador) sí quitan la superficie con `grid_remove()`. Verificado: la tarjeta tapa el vídeo hasta que se retira |
| 3 | **«Seguir en el navegador» cierra el panel** (como «← Volver a la ficha»): con el episodio en otra pestaña, un recuadro negro no aporta nada. El diseño no decía qué hacía |
| 3 | **Clic en el icono de volumen = silenciar/activar**; el deslizador sale al pasar el ratón, como pide el diseño. El volumen y el silencio se recuerdan entre episodios **en la sesión** (atributos de clase de `VideoPlayer`), no en BD |
| 3 | **No se puede como está dibujado** (1): **esquinas rectas** en el vídeo y en la barra. La superficie es una ventana nativa y no se redondea; una barra con radio abajo y recta arriba no existe en CustomTkinter |
| 3 | **No se puede como está dibujado** (2): los botones de la barra miden **40 × 38**, no 38 × 38: un `CTkButton` de solo icono no baja de 40 de ancho, pruebe `width` o `border_spacing` que se pruebe (medido con `winfo_reqwidth()`) |
| 3 | **Alto del vídeo**: 16:9 del ancho disponible **sin pasar de la mitad del alto de la ventana**. A 1440 × 910 da los 806 × 453 del diseño; con la barra lateral plegada, 946 × 455; maximizado, el tope de media ventana deja sitio a la lista. El hub avisa también de los cambios solo en alto (`relayout_player()`) |
| 3 | **La ficha 3 decía `-fullscreen`, `cursor-autohide` y atar ratón y `Esc` en mpv; manda la fase 0**: pantalla completa manual (`overrideredirect` + rectángulo del monitor, en `MainWindow.enter_player_fullscreen()`), `<Motion>` atado **en Tk** sobre el escenario y la superficie, `Esc` con `bind_all` solo mientras dura, y el cursor lo oculta Tk (`cursor="none"`). La guarda de primer plano retira la barra en 150 ms si otra app pasa delante; al volver, la barra de tareas **no** se queda encima del vídeo (verificado) |
| 3 | **«Siguiente episodio» es un `CTkFrame` con dos etiquetas**, no un `CTkButton` (el número va a la derecha y un botón no lo permite). Hoy está apagado (fondo `LINE`). 🔴 **La fase 4 tiene que atar el clic al frame y a las dos etiquetas con `add="+"`** y cambiar los colores a `ACCENT`/`ACCENT_INK`. Anterior y siguiente de la barra (`PlayerControls.previous_button`/`next_button`) están `disabled` con icono en `LINE` |
| 3 | **Tokens**: solo `VIDEO_BG`, el que pedía el diseño. Lo demás son medidas en `Metrics` (`PLAYER_*`). El texto sobre el negro de «Cargando» usa `BADGE_INK` (blanco en los dos temas) |
| 3 | **Consumo y hosters (2026-09-24)**: AV1 1080p de MP4Upload por software, **0,18-0,32 núcleos**, 0 fotogramas perdidos. H.264 de JKAnime por `d3d11va`. ⚠️ **MP4Upload servía hoy a 110-260 KB/s** (`cache-speed` de mpv), por debajo del AV1 1080p: se ve **a tirones** (`paused-for-cache` cada pocos segundos). Es el hoster, no el reproductor |
| 3 | 🔴 **Lección para verificar con input sintético**: una pulsación **suelta de Alt** con la ventana ya en primer plano la mete en el **bucle modal de menú de Windows**, y el hilo de Tk queda parado dentro de `mainloop` (en C) hasta el siguiente clic o tecla. Parece un cuelgue de la app y **no lo es**. El truco de «Alt + `SetForegroundWindow`» solo se usa si el primer plano **no** es nuestro. Para diagnosticar cuelgues: `faulthandler.dump_traceback_later()`, que vuelca aunque Python esté parado |
| 4 | 🔴 **`keep-open=yes` y el fin se detecta por `eof-reached`, no por `end-file`** (spike del 2026-10-20 con `lavfi testsrc2` de 3 s, sin red). Sin `keep-open`, tras el EOF la superficie queda **negra** (brillo medio 0,0) y la ✕ no podría «devolver el último fotograma» como pide la ficha. Con `keep-open=yes`, el EOF **no manda `end-file`**: llega `eof-reached=True` con `pause=True` y el último fotograma se queda (brillo 127,5); quitar la superficie 1 s y volver a ponerla **lo repinta en pausa** (captura con `00:00:02.958`). `end-file` sigue llegando con `reason 2` al parar o cambiar de medio. **Repetir recarga el medio** (`play()`, que quita la pausa): `seek 0` no sirve en medios no buscables. El `end-file` con `reason 0` se sigue atendiendo como fin, por si llegara |
| 4 | **Un EOF lejos del final es un corte, no un fin**: si se sabe la duración y quedan más de `END_TOLERANCE_S` segundos, se trata como error (`on_error` → navegador) y **no se marca nada**. Sin esto, un stream que se cae a mitad marcaría el episodio como visto en la biblioteca |
| 4 | **«El último» con el corte `[:25]` es el último de `anime_info.episodes`** (todo lo que lista el proveedor), no el último de los 25 que se pintan. Anterior/siguiente van por **orden real de número** (el mayor menor / el menor mayor), como `__following_episode_id()` y el «N+1» de la tarjeta. Si el episodio nuevo no tiene fila en la lista (fuera del corte o con la lista filtrada por «Ir al episodio…»), se pinta **él solo con los botones de navegación**, igual que al buscarlo |
| 4 | **Cambiar de episodio pide sus servidores una sola vez**: la misma respuesta rellena el hueco de la fila (que se despliega, y se pliega la del episodio anterior) y elige el servidor: **el mismo nombre si existe**, si no, los demás que tengan resolutor en el orden del proveedor, **una petición por servidor, sin reintentos**. Si no se resuelve ninguno, navegador con la tarjeta de siempre. Sin servidores en absoluto: tarjeta «Sin servidores» con «Volver a la ficha» (no hay URL que abrir) |
| 4 | **Anterior y siguiente navegan en cualquier estado** (cargando, reproduciendo, en la tarjeta del navegador o al terminar): `PlaybackState.has_previous/has_next` no dependen de `enabled`. «Siguiente episodio» encendido = `ACCENT`/`ACCENT_INK` con `cursor=hand2`; apagado = `LINE`/`TXT_3` sin número |
| 4 | **Si el episodio terminado ya estaba visto, no se reescribe** (lo decide la fila, no la memoria), pero la franja «Marcado como visto · N de M» sale igual, porque es verdad. Sin fila en la biblioteca, ni se marca ni sale la franja |
| 4 | 🔴 **Lecciones del arnés** (para la fase 5 y quien verifique la GUI): (1) **con la portada vacía la app saca un `messagebox` modal** («conexión lenta»), que deshabilita la ventana; con `-topmost` el aviso queda tapado y **los clics no llegan a nada**, con `WindowFromPoint` devolviendo el marco `TkTopLevel`. Se suprime el aviso en el arnés. (2) Comprobar el destino del clic con **`winfo_containing(x, y)`** (que sea el widget o un descendiente), no solo con el proceso de `WindowFromPoint`. (3) `faulthandler.enable()` en Windows **vuelca también excepciones manejadas**: `terminate()` de mpv lanza y captura excepciones de LuaJIT (`0xe24c4a02`) y parecen cuelgues sin serlo; el proceso sigue y sale con 0 |
| 5 | **`binaries`: `('vendor/libmpv-2.dll', 'vendor')`, no `'.'`** como decía la ficha. `load_mpv()` ya buscaba en `get_resource_path("vendor")`, que en el `.exe` es `_internal/vendor`: con ese destino **no hizo falta tocar `src/`** ni `os.add_dll_directory(sys._MEIPASS)`. Verificado con `Get-Process -Module`: la DLL cargada es la de `_internal\vendor` del dist |
| 5 | **El `.spec` para si falta `vendor/libmpv-2.dll`** (`SystemExit` con el paso del README), en vez de compilar un `.exe` que lo abriría todo en el navegador. La descarga, con URL, nombre del `.7z` y sha256, está en el **paso 4 del `README.md`** |
| 5 | **`hiddenimports`: 37 nombres** (36 de `src/` + `mpv`). Auditado con AST en las dos direcciones: solo `app` queda fuera |
| 5 | **Licencias reales**: `python-mpv` es **GPLv2+ o LGPLv2.1+** (no MIT, como decía la ficha); **libmpv-2.dll es GPLv3+ en conjunto**: mpv sin `-Dgpl=false` (GPLv2+, leído de `mpv-configuration`) con FFmpeg `--enable-gpl --enable-version3` y sin `nonfree`. Todo compatible con la GPL-3.0-or-later del proyecto |
| 5 | **§6 de la GPL para la DLL**: `THIRD-PARTY-NOTICES.txt` da la versión exacta y los enlaces al fuente de mpv (`6fd80b2003`), FFmpeg (`7d14defcc`) y la receta (`mpv-winbuild-cmake` `20260923`), **más una oferta de facilitar el fuente** si los enlaces caen (pedirlo en las *Issues* del repo). `LEEME.txt` remite ahí. ⚠️ **La oferta compromete al autor**: si no la quiere, la alternativa es alojar una copia del fuente |
| 5 | **`THIRD-PARTY-NOTICES.txt`: 14 → 20 componentes.** Además de `python-mpv` y libmpv, faltaban **cuatro que ya viajaban** en el `.exe` (están en el `PYZ` del build anterior): brotli 1.1.0 (MIT), PySocks 1.7.1 (BSD-3), pyparsing 3.1.4 (MIT) y setuptools 63.2.0 por su `pkg_resources` (MIT). ⚠️ **No se reproducen íntegros** los avisos de las ~45 bibliotecas enlazadas dentro de libmpv ni los de los vendorizados de `pkg_resources`: se nombran y se remite a su fuente (**L10** para `docs/12 §7`). Generador: `notices_add.py` en el scratchpad (añade, no regenera desde cero) |
| 5 | **`docs/12 §7` se actualiza en la fase 6**, no aquí: los 6 componentes nuevos, la §6 de la DLL con su oferta, L9 (el generador sigue fuera del repo) y L10 nueva. Tamaño de `dist`: **38 → 153 MB** (157 693 874 bytes); `APP_VERSION` **no se subió** (sigue `0.2.1`): es decisión de release del usuario |
| 6 | **Trampas 43-54**, no «a continuación de la 35» como decía la ficha: ya había 42. La DLL va como **18f**, junto a la 18e, porque es de empaquetado y la misma mecánica. Tres candidatas de la ficha se escribieron **al revés** (49, 50), porque la fase 0 las desmintió |
| 6 | **Los «B1» y «B2» de este plan no son los B1 y B2 de `docs/12 §4`** (que ya existían: `get_anime_image` y la ordenación por géneros). En los documentos se citan como «B1/B2 del plan del reproductor» |
| 6 | **La convención de recuento de `docs/02` cambia**: líneas como las enseña un editor, no `wc -l` + 1, porque desde `2f8a51d` la mitad de los ficheros acaban en salto. **13 676** líneas en 37 módulos |
| 6 | **Deuda nueva B15** («Cargando» sin tope con un hoster lento) y **trampa 54**, encontradas en la prueba de humo. **No se arregla aquí**: la fase 6 no toca `src/` |
| 6 | Corregido de paso un fallo previo: un **salto de línea real** dentro de `` `\n` `` partía filas de tabla en `CLAUDE.md`, `docs/06` y `docs/README.md` (dos veces) |
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

### Fase 6 · Paso 6.4 — Cierre del plan, verificación y commit          (2026-10-20)
- Ficheros: `ESTADO.md` (este cierre), `README.md` del plan (el enlace a la investigación, que no existe, pasa a texto)
- **Barrido de enlaces** de todo `.claude/` (salvo `plans/`): **903 enlaces internos, 0 rotos**, ficheros **y anclas** (`check_links.py`, scratchpad)
- **Nombres de API**: los 295 identificadores entre comillas invertidas que añadió esta fase, cotejados con `src/` y el `.spec` (`check_names.py`): 7 sin rastro, y los 7 son legítimos (nombres de fichero, paquetes, una API de Windows del arnés y un parámetro de CustomTkinter)
- **Prueba de humo** (`smoke_f6b.py`, `smoke_desu.py`): `src/` real sobre copia de las dos BD, dentro de `mainloop()`, sin teclas ni clics sintéticos. Portada real (AnimeAV1 no respondió; el *fallback* trajo 53 de JKAnime) · las 6 vistas · ficha de `dandadan` con servidores en hilo · UPNShare abre el navegador · `HLS` **no** arrancó en 45 ni en 70 s (**trampa 54**, diagnosticada con el log de mpv) · `kaijuu-8-gou` ep. 1 por **Desu se ve** (captura) · cerrar: sin hilos de mpv, sin hilos no-daemon · **0 `Traceback` y 0 `invalid command name`** en las dos salidas
- ⚠️ Un primer arnés movido con `update()` en vez de `mainloop()` dio dos `RuntimeError: main thread is not in main loop`: eran **del arnés**, no de la app
- De paso, en la portada con *fallback*: la precarga pide a AnimeAV1 los *slugs* de JKAnime y da 404 con 3 intentos por anime (12 en la prueba). Comportamiento anterior al plan; no se toca
- BD real: **46 filas** y sha256 `fc3f74bb…8dc5` antes y después (eran 36 al cerrar la fase 5: el usuario ha seguido usando la app); `DB_user.db` `ca4612be…aeae3`, igual
- `src/` sin tocar · colores literales solo en `theme.py` · TODOs: **4** (`anime_window.py:151,154`, `jkanime.py:156,217`)
- Estado: ✅

### Fase 6 · Paso 6.1 y resto de 6.2 — `CLAUDE.md`, `docs/11`, `docs/12` y `docs/README.md`          (2026-10-20)
- `CLAUDE.md`: descripción, comandos (la DLL), **§1b capa de resolución** (y por qué no es un método de `AnimeProvider`), `VideoPlayer` como 12.º componente, `player_frame`, **bloque «El reproductor acoplado»**, concurrencia (sin HTTP en Tk, regla del hilo de mpv), `.spec` (37 `hiddenimports`, `binaries`), TODOs reinventariados, licencia de libmpv, roadmap (punto 4 hecho, deuda nº 1 tachada, deuda del reproductor), recuento de trampas
- `docs/11`: **§9 «Añadir un resolutor»** con MP4Upload como caso real; §6 con la DLL y anclas del `.spec` al día · `docs/12`: B4 cerrado, **B14**, **B15**, **C12**, §2, §6, §7 (L4b, L4c, L10, L11) · `docs/README.md`: cabecera, índice, mapa de lectura y mantenimiento
- Verificado: ver la entrada de arriba

### Fase 6 · Paso 6.2 (parcial) — `docs/01`, `02`, `05`, `06`, `07` y `09`          (2026-10-20)
- Ficheros: los seis de `.claude/docs/`
- 01: capa y reproductor en el diagrama, fila de `APIs/resolvers/` en dependencias, **I6 sin excepciones**, **I10** e **I11** nuevos, `python-mpv` y la DLL en §6 · 02: inventario **recontado de cero** (13 676 líneas, 37 módulos; la convención «`wc -l` + 1» ya no vale tras `2f8a51d`), ficha de `APIs/resolvers/`, `video_player.py` como 12.º componente, bloques del reproductor en `main_window` y `anime_window` · 05: **§9 hosters** · 06: **§12 reproductor**, `VIDEO_BG` (24 tokens; el «20» ya era falso antes del plan), `player_frame` · 07: **16 hilos** + §1b (mpv), **C5 resuelta**, `after()` 11 → **28**, `WM_DELETE_WINDOW` · 09: **§6h** (resolución sin GUI), **§6i** (arnés y lecciones), **§7.13** (checklist del reproductor)
- Verificado: anclas con `grep -n`; el script sin red de §6h **ejecutado** (11 casos, 0 peticiones)
- Pendiente que deja: 11, 12, README de docs y `CLAUDE.md`

### Fase 6 · Paso 6.3 — Trampas nuevas en `docs/10` (y flujo 13 en `docs/03`, adelantado)          (2026-10-20)
- Ficheros: `.claude/docs/10-invariantes-y-trampas.md`, `.claude/docs/03-flujos-de-ejecucion.md`
- **11 trampas nuevas, 43-53**, en el apartado «Reproductor in-app», más la **18f** (la DLL en `binaries`, junto a la 18e de la que es gemela). La ficha decía «a continuación de la 35»: ya había **42**
- Tres candidatas de la ficha **se escribieron al revés**, porque la fase 0 las desmintió: encima del vídeo **sí** se ve un widget hermano (49), el ratón y el teclado **sí** llegan a Tk (50) y `CTkScrollableFrame` no da el síntoma temido (49). La 46 (bloqueo `after()` + `terminate()`) va con ⚠️: es el motivo del diseño, no se reprodujo aposta; la 48 (corte antes del final) con 📖: rama sin ejecutar
- `docs/03`: §8 reescrito (servidores en 🧵 con número de despliegue), **§13 nuevo** (13, 13b, 13c) y el antiguo §13 pasa a **§14**; convención de hilos con 🎞️ (`MPVEventHandlerThread`)
- ⚠️ **Descubierto**: el commit `2f8a51d` (justo antes del plan) reescribió comentarios en 30 módulos (−400 líneas netas), así que **muchas anclas `:línea` de `docs/` ya venían desplazadas**. Se reanclan las que toca esta fase; el resto queda avisado en las cabeceras
- Verificado: anclas de las trampas y del flujo cotejadas con `grep -n` contra el código actual
- Pendiente que deja: 6.1 y el resto de 6.2

### Fase 5 · Verificación y cierre          (2026-10-20)
- Recompilado con los avisos nuevos: 0 errores; `LICENSE`, `LEEME.txt` y `THIRD-PARTY-NOTICES.txt` junto al `.exe` e idénticos a los del repo (`cmp`), ninguno dentro de `_internal/`; `_internal/resources/` = solo `images/utils`; 0 `.db` y 0 `.jpg`; 153 MB
- BD real: sha256 `0c8d5216…fa96` (36 filas) y `DB_user.db` `8e7e9798…3354`, sin cambios: el `.exe` crea las suyas en su propio `_internal/resources/DB` · `src/` sin tocar · colores literales solo en `theme.py` · TODOs: 4
- Estado: ✅

### Fase 5 · Paso 5.4 — Licencia y avisos          (2026-10-20)
- Ficheros: `THIRD-PARTY-NOTICES.txt` (índice y 6 secciones nuevas antes de PyInstaller, leídas de los `LICENSE` del venv; UTF-8 con BOM y CRLF como estaba), `LEEME.txt` (python-mpv en la lista y párrafo de libmpv que remite a los avisos)
- Contrastado contra el `PYZ-00.toc` del build nuevo **y** del anterior (`build/` del repo, 2026-10-15): el mismo conjunto de paquetes; los 4 que faltaban ya faltaban antes
- Verificado: sí · leído el bloque generado; ver *Decisiones* para lo que **no** se reproduce íntegro
- Pendiente que deja: la actualización de `docs/12 §7` (fase 6)

### Fase 5 · Paso 5.3 — Compilar y reproducir desde el `.exe`          (2026-10-20)
- `pyinstaller MiBibliotecaAnime.spec --distpath/--workpath` al **scratchpad** (no pisa el `dist/MiBibliotecaAnime_v0.2.1` de 38 MB del repo): exit 0, sin `ERROR` ni `Traceback`
- `libmpv-2.dll` **no** está en `%PATH%` (comprobado). `.exe` lanzado desde el scratchpad, manejado con clics reales (destino comprobado con `WindowFromPoint`) y capturas `PrintWindow`:
  - portada de AnimeAV1 a los 15 s, **vivo a los 43 s** y después
  - `Dark Machine` ep. 1 → `HLS` (zilla) **se ve**: `00:04` → `00:16` en 12 s de reloj, AV1. `Get-Process -Module`: `…\dist\MiBibliotecaAnime_v0.2.1\_internal\vendor\libmpv-2.dll`
  - UPNShare ↗ en la columna → **abre el navegador** (Brave, proceso nuevo) y tarjeta «UPNShare se abre en tu navegador» con «Ver aquí con HLS»
  - proveedor de la sesión a JKAnime (desplegable) → portada de 53 → `Psyren` ep. 1 → **Desu se ve** (HLS MPEG-TS, subtítulos incrustados, `00:04 / 23:40`)
  - cerrado por la ventana: sale en < 15 s, sin procesos colgados
- No hizo falta `os.add_dll_directory(sys._MEIPASS)`: ver *Decisiones*
- Peticiones reales: ~8 en total (2 portadas, 2 fichas, 2 listas de servidores, 2 resoluciones) más los medios; ningún 403
- Pendiente que deja: 5.4

### Fase 5 · Paso 5.2 — `hiddenimports` y `binaries`          (2026-10-20)
- Ficheros: `MiBibliotecaAnime.spec`
- `hiddenimports`: +5 `APIs.resolvers.*` (`base`, `jkplayer`, `mp4upload`, `registry`, `zilla`; la ficha decía 6, pero son 5 más el `__init__`), `gui.components.video_player` y `mpv` → **37 nombres** (36 de `src/` + `mpv`)
- `binaries`: `('vendor/libmpv-2.dll', 'vendor')` — **destino `vendor`, no `'.'`** (ver *Decisiones*). El `.spec` para con un mensaje claro si falta la DLL
- `python-mpv` no arrastra datos propios: `mpv.py` solo importa la stdlib
- Verificado: sí · auditoría con AST en las dos direcciones (`audit.py`, scratchpad): los 36 nombres de `src/` resuelven a ficheros reales y el único módulo de `src/` sin declarar es `app` (script de entrada)
- Pendiente que deja: 5.3

### Fase 5 · Paso 5.1 — `requirements.txt` y la DLL          (2026-10-20)
- Ficheros: `requirements.txt` (`python-mpv==1.0.8`, la de la fase 0), `README.md` (paso 4 «Descargar libmpv» con URL, nombre del `.7z` y sha256; aviso en «Compilar»; mpv en tecnologías)
- La DLL **sigue fuera del repo** (decisión 2): `vendor/libmpv-2.dll`, sha256 `751131f8…25ff0`, la misma de la fase 0. Es la que se empaqueta: `mpv v0.41.0-1055-g6fd80b200`, FFmpeg `N-126773-g7d14defcc` (leído de la propia DLL con `mpv-version` / `ffmpeg-version`)
- Licencia real comprobada (ver *Decisiones*): libmpv sin `-Dgpl=false` + FFmpeg con `--enable-gpl --enable-version3`, sin `nonfree` → **GPLv3+** en conjunto. `python-mpv` es **GPLv2+ o LGPLv2.1+**, no MIT
- Verificado: sí · `pip check` sin quejas de `python-mpv`; sha256 de la DLL recalculado
- Pendiente que deja: 5.2

### Fase 4 · Verificación y cierre          (2026-10-20)
- Arneses `verify_f4.py`, `verify_f4b.py` y `verify_f4c.py` (scratchpad): `MainWindow` del `src/` real con todo `resources/` desviado a un sandbox con **copia de las dos BD**, portada vacía (sin bajar estrenos), `webbrowser.open` interceptado, clics reales solo si `winfo_containing` da el widget y `Esc` solo con el primer plano nuestro (0 descartados)
- Copia preparada: `kaijuu-8-gou` (JKAnime) con vistos {1, 2, 5}; fila de `kaoru-hana-wa-rin-to-saku` **borrada en la copia** para probarlo como no guardado. Animes tocados en la copia: esos dos y `dandadan` (sin escrituras de vistos)
- **57/57** (el único rojo fue una expectativa mal escrita del arnés: «4 de 12» donde lo correcto era 5, y la captura dice 5): ep. 3 por Desu (clic real) → fin real (`seek` a 6 s del final) → tarjeta con título, «Kaijuu 8-gou · JKAnime · Desu», «Marcado como visto · 4 de 12» y los dos botones · BD copia `[[1,3],[5,5]]` (acumulativo, **conserva el 5**) · interruptor y «Terminado» en la fila · TERMINADO en la columna · +10 apagado, play en repetir · `on_end` una vez · **✕ (clic real)**: retira la tarjeta, **vuelve el último fotograma** (captura), la barra sigue en repetir, no marca nada más, el aviso no vuelve · **«Siguiente episodio» de la columna (clic real)** → ep. 4 por el **mismo servidor**, «Episodio 4 de 12 · servidor Desu», el 4 desplegado y el 3 plegado · **pantalla completa (clic real)**: fin, la barra flotante **sigue a los 7 s quieto**, tarjeta centrada (960 = 960) con «5 de 12» · **`Esc` real**: sale y la tarjeta **queda sola en el recuadro acoplado** (806×453), sin moverla a mano · «Ver el episodio 5» (clic real) encadena · **«anterior» de la barra (clic real)** → 4 · fin de un episodio ya visto: franja sí, sin reescribir · «Volver a la ficha» de la tarjeta cierra el panel y la ficha sigue con el 4 desplegado · ep. 6 a mitad + «← Volver a la ficha» → **ni tarjeta ni `on_end`**, el 6 sin marcar · **no guardado**, último episodio (13): siguiente apagado y anterior encendido, «Siguiente episodio» apagado, tarjeta sin franja y sin «Ver el episodio…», **ninguna fila nueva** (35 = 35)
- **Degradación (12/12)**: `dandadan` (AnimeAV1) · UPNShare ↗ → navegador con su URL y la tarjeta de siempre · siguiente con `registry.resolve` forzado a None → intenta **solo** HLS y MP4Upload, **una vez cada uno**, y abre el navegador con el preferido; la tarjeta no ofrece lo ya intentado · «Seguir en el navegador» cierra · 0 escrituras
- **Zilla ha vuelto** (una petición de sondeo: 200). `zilla_check.py`: resolución, playlist fMP4 y segmento **200 con / 403 sin** `Sec-Fetch-Site`. En la app (`verify_f4c.py`, 5/5): `HLS` se ve a los 2,3 s, AV1 1080p, 0 fotogramas perdidos
- Peticiones reales: ~25 en total, espaciadas, ningún 403 salvo el segmento sin cabecera, que era la prueba
- **BD real**: sha256 `0c8d5216…fa96` antes y después de todas las pasadas · **36 filas** (sin cambios) · `DB_user.db` real también intacta · colores literales solo en `theme.py` · TODOs: 4 (los de `anime_window.py` en las líneas 151 y 154) · sin errores de Tk en los `stderr`
- Estado: ✅

### Fase 4 · Pasos 4.1-4.4 — Anterior/siguiente, tarjeta de fin, marcado y listas del hub          (2026-10-20)
- Spike previo (scratchpad, `spike_keepopen.py`, sin red): `keep-open` necesario para la ✕ (ver *Decisiones*)
- Ficheros: `src/gui/components/video_player.py` (`keep_open`, `eof-reached` → `__reach_end()` con `END_TOLERANCE_S`; `on_previous`/`on_next`, `set_navigation()`, `PlaybackState.has_previous/has_next`; `show_message(check_note=, closable=)`; glifos `close` y `check`; la barra flotante sale al aparecer una tarjeta), `src/gui/anime_window.py` (`__play_episode`, `__play_adjacent`, `__adjacent_episode`, `__on_episode_resolved`, `__on_player_ended`, `__mark_finished_episode`, «Siguiente episodio» conectado, estado `unavailable`; extraídos sin cambiar comportamiento `__set_episode_watched`, `__refresh_hub_lists`, `__open_servers_frame`, `__fetch_servers`, `__ensure_episode_row`)
- 4.4: los contadores de la barra cuentan **animes por estado**, así que marcar un episodio **no los mueve** (y la ficha 4.4 prohíbe mover estados). Aun así se releen las listas del hub tras marcar, para que nada quede cacheado con los vistos viejos
- Verificado: compila; colores literales solo en `theme.py`; TODOs: 4. **En pantalla: todavía no** (siguiente: arnés sobre copia)
- Pendiente que deja: la verificación

### Fase 4 · Inicio — Punto de decisión 1 cerrado          (2026-10-20)
- Ficheros: ESTADO.md
- El usuario responde **sí**: llegar al final marca como visto (solo si el anime está guardado; nunca crea fila)
- Verificado: no aplica
- Pendiente que deja: pasos 4.1-4.4

### Fase 3 · Verificación y cierre          (2026-09-24)
- Arnés `verify_f3.py` (scratchpad) sobre **copia** de `src/` (idéntica, `diff -r`) y de la BD: Tk, mpv y red reales, `webbrowser.open` interceptado, capturas de pantalla con la ventana encima, clics y teclas **solo** si el destino es nuestro (0 descartados)
- **Batería completa limpia** (47 comprobaciones, 0 errores de Tk): AnimeAV1 `dandadan` ep. 1 por MP4Upload se ve (AV1 1920×1080, `aac`) · columna y fila «▮ Reproduciendo · MP4Upload» · pausa congela `time-pos` · +10/−10 · buscar al 50 % · volumen y silencio · clic real en play/pausa · 9 controles en orden, anterior/siguiente apagados · deslizador de volumen: abre, aguanta el paso al deslizador, se arrastra, se cierra · pantalla completa en 1920×1080, barra flotante 64 px, se oculta a los ~5 s con el cursor y vuelve al mover, clic en la barra flotante, tema claro en ella, guarda de primer plano, `Esc` real → misma geometría y barra lateral · Mega → navegador + tarjeta «Ver aquí con HLS» · HLS (zilla caído) → navegador a los 20 s + «Ver aquí con MP4Upload» · JKAnime Desu y Magi se ven (`d3d11va`) · cambiar de servidor desde la columna · plegar la barra lateral (806→946 px) · «Ir al episodio…» con el vídeo en marcha · «Volver a la ficha» (ficha como estaba, sin hilos de mpv) · cambiar de vista (panel cerrado) · cerrar la app sonando (solo queda `MainThread`)
- Clics reales: Desu en la lista, Magi en la columna, salir con el botón de la barra flotante, «Volver a la ficha»
- Un cuelgue que resultó ser el Alt suelto del arnés (ver *Decisiones*); 4/4 limpias tras corregirlo
- `app.py` de la copia arranca y cierra por la ventana con código 0 · colores literales solo en `theme.py` · TODOs: 4 (los de `anime_window.py` pasan a las líneas 150 y 153)
- BD real: sha256 `0c8d5216…fa96` antes y después (36 filas)
- Estado: ⚠️ por `HLS`/zilla y el audio oído

### Fase 3 · Pasos 3.1-3.5 — Panel, `VideoPlayer`, columna, pantalla completa y `__play_video`          (2026-09-24)
- Ficheros: `src/gui/components/video_player.py` (nuevo: `VideoPlayer`, `PlayerControls`, glifos PIL, `load_mpv()`), `src/gui/main_window.py` (`player_frame`, `show/hide/close_player`, pantalla completa manual, `WM_DELETE_WINDOW`, `clear_frame()` cierra el reproductor), `src/gui/anime_window.py` (columna de información, `__play_video` con resolución en hilo y número de petición, caída al navegador, ↗ en los servidores, fila actual en `EpisodeRow`), `src/gui/theme.py` (`VIDEO_BG`, `Metrics.PLAYER_*`)
- Zilla, una sola petición antes de empezar: el playlist sigue sin responder (timeout de 15 s)
- Verificado: sí (ver la entrada de arriba)
- Pendiente que deja: `HLS` con zilla vivo, el audio oído, y lo que es de la fase 4

### Fase 2 · Verificación y cierre          (2026-09-24)
- Arnés `verify_f2.py` (scratchpad) sobre **copia** de `src/` y de la BD: Tk real, red real, `webbrowser.open` interceptado, latido de 10 ms para medir el bucle, capturas con `PrintWindow`
- **16/16**: One Piece (AnimeAV1) abierto por el 1164 → 7 servidores, petición en `Thread-5 (_fetch)` con `strict=True` y `animeav1` · fila «Buscando servidores…» · plegar mientras carga 0,007 s · respuesta tardía (3 s, centinela) del 3 **no** pinta bajo el 5 · redesplegar el mismo episodio no pinta la vieja · plegar ya cargado 0,016 s sin petición · vacío y excepción dicen «Sin servidores» · pulsar «HLS» abre el navegador con su URL · JKAnime (`kaijuu-8-gou` ep. 1) → Desu, Magi · cerrar la ficha con una petición en vuelo: 0 errores de Tk, sin `invalid command name` en el log
- Peticiones reales: ~8 a AnimeAV1 y 2 a JKAnime por pasada, dos pasadas, sin un 403
- BD real: sha256 `0c8d5216…fa96` antes y después (36 filas) · colores literales solo en `theme.py`
- Estado: ✅

### Fase 2 · Pasos 2.1-2.3 — Servidores en hilo daemon, estado en la fila y generación          (2026-09-24)
- Ficheros: `src/gui/anime_window.py` (`__toggle_servers_frame` partido en petición + `__show_servers` + `__show_servers_message`; `__servers_requests`/`__servers_states`/`__servers_request_seq`; comentario de `FOCUS_DELAY_MS`)
- `strict=True` y `provider_id=self.provider_id` intactos (identidad de visualización, trampa 21). Plegar no sale a la red. Fuera el `cursor="watch"` y el `messagebox` de «sin servidores»
- Verificado: no todavía (siguiente: arnés sobre copia en el scratchpad)
- Pendiente que deja: la verificación

### Fase 1 · Verificación y cierre          (2026-09-24)
- Sin red (`requests` bloqueado): `has_resolver()` acierta los 12 casos (los 8 de la ficha + `mp4upload.com` sin `www`, URL vacía, basura) con **0 peticiones**; `resolve()` da `None` sin lanzar en Mega, Voe, Byse, Okru, vacía y basura; y sin red, `um`/`jk`/mp4upload dan `None` sin lanzar
- Con red (espaciada 2-3 s, sin reintentos): cobertura en *Decisiones*. Negativas: `jkplayers` con `Referer` → 410 ✅; zilla sin cabecera → **no probada** (caído)
- GUI: copia de `src/` + copia de la BD en el scratchpad, con `webbrowser.open` interceptado. Arranca y pinta «Nuevos lanzamientos»; «Viendo» → One Piece (reapuntado a JKAnime **solo en la copia**) → «Seguir por el 1» → **5 servidores en pantalla** · pulsar «Desu 2» y «Desuka» manda al navegador sus dos URLs distintas
- BD real: sha256 `0c8d5216…fa96` al empezar y al terminar · colores literales solo en `theme.py` · `git grep resolvers -- src/gui/` vacío
- Estado: ⚠️ por zilla (ver *Qué quedó sin verificar*)

### Fase 1 · Pasos 1.1-1.6 — Capa `APIs/resolvers/` escrita, B1 y B2          (2026-09-24)
- Ficheros: `src/APIs/resolvers/{__init__,base,zilla,jkplayer,mp4upload,registry}.py` (nuevos), `src/APIs/jkanime/jkanime.py` (B2: `urljoin`), `src/gui/anime_window.py` (B1: `__server_url_map`, numera repetidos)
- Antes de escribir, **una** petición a cada página (2026-09-24): `jkplayer/um` 200, 16 992 B, URL en claro **y** en `atob()` · embed de mp4upload 200, `player.src({… src: "https://a3.mp4upload.com:183/d/<token>/video.mp4"})` · **zilla: timeout de lectura** (15 s) en el playlist, sigue caído
- Verificado: no todavía (siguiente: script de verificación)
- Pendiente que deja: la verificación completa

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

Escrito el 2026-10-20 por la fase 6.

### Las 7 fases

| # | Fase | Cierre | Excepción |
|---|---|---|---|
| 0 | Spike de libmpv | ✅ | — (audio oído por el usuario el 2026-10-21; (b) contra zilla real, el 2026-10-20) |
| 1 | Capa de resolución | ✅ | — (`Okru` real y la app con la BD real, sin ejecutar; ver arriba) |
| 2 | Servidores fuera del hilo de Tk | ✅ | — |
| 3 | Panel de reproducción | ✅ | Dos monitores en pantalla completa y salir de ella con la barra lateral plegada (audio oído el 2026-10-21) |
| 4 | Navegación y fin de episodio | ✅ | — (la ✕ a pantalla completa y el corte antes del final, leídos y no ejecutados) |
| 5 | Empaquetado | ✅ | El audio desde el `.exe`, una máquina limpia y la receta de FFmpeg en su etiqueta |
| 6 | Documentación | ✅ | `HLS` no se vio en la prueba de humo (zilla lento, trampa 54); sí se vio Desu |

~~Lo único que falta para que las 7 queden en ✅ es que el usuario oiga un episodio.~~ ✅ **Hecho el
2026-10-21**: el usuario confirma que los episodios se oyen perfectamente. **Las 7 fases están en
✅.**

### Qué quedó fuera

- **Hosters sin resolver** (deuda **B14**): siguen abriendo el navegador con ↗ UPNShare, Voe, Byse,
  YourUpload, DoodStream, Netu, VidHide y StreamTape (AnimeAV1), y Okru (JKAnime). **Mega** está
  bloqueado de verdad (cifrado de extremo a extremo). Los resueltos —zilla, MP4Upload, Desu, Magi y
  Desuka— cubrían 7/7 episodios muestreados por proveedor.
- Lo que el [README](README.md#qué-no-entra-en-este-plan) dejaba fuera desde el principio: descargar
  episodios, **recordar el minuto donde lo dejaste**, elegir calidad o subtítulos (los playlists no
  ofrecen alternativas), proveedores nuevos, los descartes del diseño (teatro, carril, pie, póster) y
  redibujar los iconos de **B11**.
- Lo que se decidió no hacer por el camino: **MP4Upload como alternativa H.264** (es AV1 también,
  decisión 4); la **contingencia VLC + proxy** (mpv pasó la fase 0); la rama
  **`feature/reproductor-in-app`** (se trabajó en `feature/reproductor-embebido`, que ya existía);
  **versionar la DLL** (120 MB, decisión 2); subir **`APP_VERSION`** (decisión de release del usuario).
- Lo que apareció al final y **no** se arregló, porque la fase 6 no toca `src/`: **B15**, «Cargando»
  sin tope con un hoster lento ([trampa 54](../docs/10-invariantes-y-trampas.md)).
- **La legalidad** (decisión 5): reproducir dentro elimina los anuncios del hoster. **Sigue abierta**, y
  es del usuario.

### Qué sigue vigente de lo que la investigación no pudo comprobar

La investigación (`.claude/plans/investigacion-reproduccion-in-app-kind-flask.md`) **no está en
disco** desde antes de la fase 0, así que su §10 no se puede releer. De lo que el plan copió de ella:

- ✅ **Cerrado**: «de mpv no se probó nada» (fase 0); que mpv mande la cabecera en cada segmento de
  zilla (fase 0 en local, 2026-10-20 contra zilla real); el consumo del AV1 1080p (0,2-0,33 núcleos);
  la cobertura de los tres hosters (fase 1).
- ⚠️ **Sigue sin comprobar** (el audio oído salió de esta lista el 2026-10-21): el consumo en una máquina **sin** otra GPU que la de
  pruebas; la URL de `jkplayers` **tras cambiar de IP** (se sabe que la incrusta, no se ha visto
  fallar); un `Okru` real; por qué `play/` de zilla da **403 de Cloudflare a `requests`** (no afecta: el
  resolutor no pide esa página); y el `.exe` en una **máquina limpia**.

### Qué recomendaría como siguiente tarea

1. ~~**Oír un episodio**~~ — ✅ hecho por el usuario el 2026-10-21.
2. ✅ **Hecho el 2026-10-21 con 30 s** (`LOAD_TIMEOUT_S`, trampa 54 resuelta). ~~**B15 — un tope propio para «Cargando»**~~: un plazo desde `play()` hasta el primer
   `playback-restart` que, al vencer, haga lo mismo que `on_error`. Es pequeño, toca dos ficheros y es
   lo que más se nota: con zilla lento, hoy el usuario no sabe si esperar.
3. ~~**B2**~~ (`str` vs enum en la ordenación por géneros) — ✅ cerrado el 2026-10-21 en
   `animesPersistence.py` ([`docs/12 §4`](../docs/12-deuda-tecnica-y-roadmap.md)).
4. ✅ **Hecho el 2026-10-21**: **L10** y **L11** cerrados con `tools/actualizar_libmpv.py`, y la
   **oferta de facilitar el fuente** se mantiene (decisión del usuario). La DLL sigue dentro del
   `.exe`, para que el reproductor sea transparente (`docs/12 §7`, L12-L13).
5. Fusionar `feature/reproductor-embebido` en `develop`, cuando el usuario lo decida: ninguna fase
   tocó otra rama.
