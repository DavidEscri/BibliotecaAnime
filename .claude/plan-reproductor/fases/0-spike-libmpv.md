# Fase 0 — Spike de libmpv

| | |
|---|---|
| **Objetivo** | Tapar el hueco más grande de la investigación: **de mpv no se verificó nada**. Probar las cuatro cosas de las que depende todo el plan antes de escribir una línea de producción |
| **Investigación** | §5 (decisión de reproductor), §6 (restricciones de interfaz), §4.1 (cabeceras de zilla), §9.6 y §10 (lo que no se pudo verificar) |
| **Estrena** | Nada. Es un spike: **ningún fichero de `src/`** |
| **Toca** | El entorno virtual `biblio_anime_env/`, el scratchpad, y —si se decide— `vendor/libmpv-2.dll` + `.gitignore` |
| **No toca** | `src/`, `MiBibliotecaAnime.spec`, `requirements.txt`, `resources/DB/` |
| **Riesgo** | 🔴 **Alto** — no de romper nada, sino de **tumbar la decisión de backend** y con ella las fases 3 y 5 |
| **Depende de** | Nada. Es la primera |

---

## Por qué esta fase existe

La investigación eligió **libmpv** sobre VLC y lo dejó dicho con todas las letras (§10):

> ⚠️ **mpv / libmpv / `python-mpv`: nada en absoluto.** No está instalado y no podía instalar. Toda
> la afirmación sobre mpv del §5 es documental.

Y no es un detalle de implementación: si mpv no incrusta en Tk, o si filtra las cabeceras `Sec-*`,
**la fase 3 no se puede escribir tal y como está planteada**. La contingencia —`python-vlc` + proxy
local— sí se verificó end-to-end el 2026-08-23, así que caerse ahí no rediseña nada: el resolutor,
la barra de controles y la navegación son idénticos, **solo cambia el backend**.

🔴 **Esta fase no escribe código de producción.** Todo va en el scratchpad. Si al terminar hay algo
en `src/`, la fase se ha hecho mal.

---

## Antes de empezar

Lectura obligatoria, en este orden:

1. [`docs/10-invariantes-y-trampas.md`](../../docs/10-invariantes-y-trampas.md) — las **35** siguen
   vigentes; en esta fase muerden las de CustomTkinter (29-35) y la **17**.
2. [`docs/07-concurrencia-e-hilos.md`](../../docs/07-concurrencia-e-hilos.md) — qué corre en qué
   hilo y por qué `after(0, …)` no es opcional.
3. De la investigación, **solo**: **§5** (la tabla de backends y lo que se verificó de VLC), **§6**
   (las tres restricciones de interfaz) y **§4.1** (la receta de zilla y su tabla de cabeceras).
4. [`README.md`](../README.md) de este plan — reglas 6 y 7 en particular.

**Trampas que van a morder en esta fase:**

- ⚠️ **`pip install python-mpv` no trae vídeo.** Son dos piezas: el *binding* por `ctypes` (~100 KB)
  y **la DLL aparte**. La DLL sale del artefacto **`mpv-dev-x86_64-*.7z`** de los builds oficiales
  de Windows — **no** del paquete normal, que solo trae `mpv.exe` y no sirve.
- 🔴 **Cloudflare bloquea por sondeo intensivo** (regla 6 del plan). Un episodio, unas pocas
  peticiones, y esperar entre intentos. El 403 de `/segs/` **no** es la IP marcada: ✅ persiste tras
  el enfriado porque es una regla de ruta.
- ⚠️ **`Sec-Fetch-Site: same-origin` solo hace falta en los segmentos**, no en el playlist, y **solo
  vale ese valor**: `cross-site`, `same-site` y `none` dan 403. `Referer`, `Origin` y `User-Agent`
  son irrelevantes en zilla.
- 🔴 **Los eventos de mpv llegan en su propio hilo.** Cualquier `print` desde el callback engaña:
  lo que hay que comprobar es **el nombre del hilo** (`threading.current_thread().name`), no que el
  evento llegue.

---

## Pasos

### Paso 0.1 — Orientación y rama

- `git status`, `git log --oneline -5`, `git branch --show-current`.
- Confirmar que la base es `95abd56` en `feature/ui-redisign`. Si no lo es, anotarlo en `ESTADO.md`
  y seguir.
- Crear la rama: `git switch -c feature/reproductor-in-app`.
- Arrancar `python src/app.py`, comprobar que la app sube, abrir una ficha y **desplegar los
  servidores de un episodio**. Es la foto del «antes»: anotar cuánto se congela la ventana (es lo
  que va a arreglar la fase 2) y qué servidores ofrece ese episodio.
- Anotar en `ESTADO.md`: rama creada, base real, si la app arrancó y el congelado medido.

### Paso 0.2 — Instalar las dos piezas

- `python-mpv` **en `biblio_anime_env/`**, no global. `requirements.txt` **no se toca** (regla 8).
- Bajar `libmpv-2.dll` del artefacto `mpv-dev-x86_64-*.7z`. Anotar **versión exacta** de libmpv y
  de `python-mpv` en `ESTADO.md`: sin eso, un fallo dentro de tres meses no es diagnosticable.
- 🔴 **Cerrar el punto de decisión 2** (`ESTADO.md`): ¿la DLL se versiona en `vendor/` o se ignora
  y se documenta la descarga? Son ~40 MB **permanentes** en el historial de git — no se pueden
  quitar después sin reescribirlo. Preguntar al usuario si no está claro; la fase 5 necesita la
  respuesta para el `.spec`.
- Comprobar que el binding **carga la DLL**: `import mpv` + construir un `mpv.MPV()` sin ventana.
  Si `ctypes.CDLL("libmpv-2.dll")` no la encuentra, probar `os.add_dll_directory(...)` — es la misma
  trampa que espera en el `.exe` (fase 5).

### Paso 0.3 — (a) Incrustar en un frame Tk

Ventana de prueba **en el scratchpad**: un `CTkFrame` y `mpv.MPV(wid=str(frame.winfo_id()), …)`.

- ⚠️ `winfo_id()` solo es válido **después de mapear** el widget: `update_idletasks()` antes, o
  crear el reproductor desde un `after()`.
- Comprobar los tres puntos del §6 mientras está reproduciendo:
  - que el vídeo **se pinta dentro del frame** y sigue su geometría al redimensionar la ventana;
  - ✅/❌ que un widget Tk colocado encima **no se ve** (§6.1: es una ventana hija del SO). Esto es
    ⚠️ *derivado*, no verificado; aquí se cierra de una vez y va a `Decisiones`;
  - qué pasa al meterlo dentro de un `CTkScrollableFrame` (§6.2). **No hace falta que funcione** —
    la decisión ya es no hacerlo—, pero confirmar el síntoma ahorra la duda en la fase 3.
- Comprobar el **cierre limpio**: `player.terminate()` antes de `destroy()` de la ventana. Un mpv
  vivo tras cerrar Tk deja el proceso colgado.

### Paso 0.4 — (b) Las cabeceras llegan a los segmentos

El paso que decide si mpv sirve o no.

- Coger un episodio de AnimeAV1 con servidor **`HLS`**, resolver a mano la receta de §4.1
  (`play/<hash>` → `m3u8/<hash>`) y reproducir con
  `--http-header-fields=Sec-Fetch-Site: same-origin`.
- 🔴 **La prueba de verdad es la negativa**: reproducir **sin** la cabecera y comprobar que
  **falla** (403 en los segmentos). Si funciona igual con y sin ella, la prueba no ha probado nada
  — significa que se está sirviendo de caché o que el playlist no llegó a pedir segmentos.
- Comprobar en el log de mpv (`log_handler` o `--msg-level`) que baja **init + segmentos
  consecutivos**, no solo el manifiesto.
- ⚠️ **Un episodio, peticiones espaciadas.** Regla 6: si sale un 403 masivo, parar y esperar.

### Paso 0.5 — (c) Eventos y marshalling

- `observe_property('time-pos')` y `observe_property('duration')`: comprobar que llegan y con qué
  frecuencia (la barra de progreso de la fase 3 se pinta con esto).
- Evento **`end-file`**: comprobar que llega **y con qué `reason`** al terminar el vídeo, al pararlo
  a mano y al cambiar de fichero. 🔴 Es lo que la fase 4 necesita para no sacar el diálogo de fin de
  episodio cuando el usuario simplemente cierra el reproductor.
- 🔴 **Anotar el nombre del hilo** en el que llega cada callback, y comprobar que
  `widget.after(0, …)` desde ahí repinta de verdad sin reventar. Es la regla que ya obliga al resto
  de la GUI y aquí es más fácil de violar porque el evento no lo origina el usuario.

### Paso 0.6 — (d) Controles y consumo

- `pause`, `seek ±10` (`player.seek(10, reference="relative")`), `player.volume`, y fijar la
  posición saltando a un punto concreto. Comprobar que responden **con el vídeo ya empezado** y que
  el `seek` en HLS no reinicia el stream.
- 🔴 **Medir el consumo de CPU** reproduciendo el `HLS` de AnimeAV1 (**AV1 1080p**, §9.6) durante
  un par de minutos: es la única forma de cerrar el punto de decisión 4. Anotar CPU, si hubo
  aceleración por hardware (`hwdec`) o dav1d por software, y si hay saltos de imagen.
- Comparar contra el **MP4 de MP4Upload** (H.264) del mismo episodio si el consumo asusta.
- Probar de paso un **HLS MPEG-TS de JKAnime** (§4.2, sin cabeceras): son dos demuxers distintos y
  la fase 3 va a usar los dos.

---

## Terminado cuando

- [ ] `python-mpv` y `libmpv-2.dll` instalados en el entorno del proyecto, con **versión anotada**.
- [ ] El punto de decisión 2 (versionar la DLL o no) está **cerrado y anotado** en `ESTADO.md`.
- [ ] (a) El vídeo se pinta **dentro de un frame Tk** y sigue su geometría al redimensionar.
- [ ] (b) `Sec-Fetch-Site: same-origin` llega a los segmentos: reproduce **con** la cabecera y
      **falla sin ella**.
- [ ] (c) `time-pos` y `end-file` llegan, se conoce el **`reason`** de cada salida y se sabe **en
      qué hilo** llegan.
- [ ] (d) `pause`, `seek ±10` y volumen responden sobre un stream ya empezado.
- [ ] Consumo de CPU del AV1 1080p **medido y anotado**.
- [ ] `src/` **no tiene ni un cambio** (`git status` limpio salvo `.claude/` y, si se decidió,
      `vendor/`).
- [ ] La decisión de backend está escrita en *Decisiones* de `ESTADO.md`: **mpv sigue** o **se cae a
      VLC + proxy**.

## Verificación

Un episodio de AnimeAV1 **reproduciéndose y viéndose** dentro de una ventana Tk de prueba, con pausa
y salto funcionando. **Verlo y oírlo**, no deducirlo del log: la investigación ya comprobó bytes y
*magic numbers*, y eso es exactamente lo que no bastó.

Si no se puede abrir ventana Tk, o si los sitios no responden ese día, cerrar la fase como ⚠️
**terminada sin verificar**, decir qué falta y **no seguir a la fase 1 dando mpv por bueno**.

## Si mpv no pasa

No se improvisa un tercer backend:

1. Anotar en *Decisiones* **qué** falló exactamente (incrustación, cabeceras, eventos o consumo).
2. Cambiar la decisión a **`python-vlc` + proxy local**, que ✅ se verificó end-to-end el
   2026-08-23 (VLC parseó el manifiesto fMP4 y pidió init + segmentos, todo 200).
3. ⚠️ Queda un hueco nuevo: **`python-vlc` incrustando en un frame Tk** tampoco se verificó. Habría
   que probarlo aquí mismo antes de dar la contingencia por buena.
4. **Avisar al usuario y parar.** Las fases 1 y 2 no cambian; las 3 y 5 sí, y bastante.

## Qué anotar en ESTADO.md

Versiones de `python-mpv` y de libmpv · si incrusta en Tk · si las cabeceras llegan a los segmentos
(y si falla sin ellas) · el hilo y el `reason` de `end-file` · CPU del AV1 1080p · dónde vive la DLL
· **la decisión de backend** · y el congelado medido en el paso 0.1, que es la línea base de la
fase 2.
