# Fase 6 — Documentación

| | |
|---|---|
| **Objetivo** | Que `.claude/docs/` y `CLAUDE.md` no contradigan al código: capa nueva, flujo nuevo, trampas nuevas y la deuda nº 1 tachada. Y cerrar el plan |
| **Investigación** | §8 (fase 6) y §10 (lo que quedó sin verificar — parte de ello sigue vigente) |
| **Estrena** | El playbook «añadir un resolutor» |
| **Toca** | `.claude/CLAUDE.md`, `.claude/docs/` (01, 02, 03, 05, 07, 09, 10, 11, 12, README), `.claude/plan-reproductor/ESTADO.md` |
| **No toca** | `src/`. Si esta fase necesita cambiar código, es que una fase anterior se cerró mal |
| **Riesgo** | Bajo |
| **Depende de** | Las 6 anteriores |

---

## Antes de empezar

Leer [`ESTADO.md`](../ESTADO.md) **entero**, incluida la bitácora y las dos tablas de decisiones.
Esta fase es la que paga lo que las 6 anteriores fueron anotando.

Si alguna fase quedó en ⬜ o en ⚠️ sin verificar, **decirlo al principio** y decidir con el usuario
si se cierra igual o si se vuelve a esa fase primero.

⚠️ **La documentación se escribe contra el código, no contra este plan.** Las fichas de fase dicen
lo que se pensaba hacer; lo que hay que documentar es lo que se hizo. Cotejar cada afirmación con el
fichero real — los nombres de API, uno a uno, no de memoria. Es lo que se hizo el 2026-08-21 y es
lo que evita que `docs/` envejezca mintiendo.

---

## Pasos

### Paso 6.1 — `CLAUDE.md`

- **Sección de arquitectura**: la capa de resolución como pieza nueva, entre proveedores y GUI. Qué
  es un `Resolver`, qué es un `MediaSource`, y 🔴 **por qué no es un método de `AnimeProvider`**.
- **GUI**: `VideoPlayer` como 12.º componente, `player_frame` **encima** de `content_frame` (que se
  queda debajo), la barra flotante de pantalla completa, el token `VIDEO_BG` y qué hace hoy
  `__play_video()`. Enlazar [`DISENO-VISUAL.html`](../DISENO-VISUAL.html) como referencia visual.
- **Roadmap**: tachar la **deuda nº 1** («la petición de servidores sigue en el hilo de Tkinter»),
  que cerró la fase 2. Y decir qué deja este plan sin hacer.
- **Notas de mantenimiento**: `hiddenimports` con el recuento nuevo, `binaries` con la DLL, y la
  nota de licencia de libmpv.
- ⚠️ **Reinventariar los `TODO`**: `git grep -n "TODO" -- src/` **y mirar lo que devuelve**. Este
  apartado se ha equivocado **tres veces** ([docs/12 §2](../../docs/12-deuda-tecnica-y-roadmap.md));
  hoy dice 4 y este plan puede haber cerrado o abierto alguno.

### Paso 6.2 — Los documentos de `.claude/docs/`

| Documento | Qué añadir |
|---|---|
| [`01-arquitectura.md`](../../docs/01-arquitectura.md) | La capa `APIs/resolvers/` en el mapa de capas y sus **dependencias permitidas**: no importa de `gui/`, no la usa el manager, la llama la ficha |
| [`02-mapa-de-modulos.md`](../../docs/02-mapa-de-modulos.md) | Ficha por módulo nuevo: los 6 de `resolvers/` y `video_player.py` |
| [`03-flujos-de-ejecucion.md`](../../docs/03-flujos-de-ejecucion.md) | **Flujo nuevo**, antes de «Flujos documentados en otro sitio» (hoy §13, que se renumera): clic en servidor → tarjeta «Cargando» → hilo daemon → `registry.resolve` → `after(0)` → reproductor → `end-file` → tarjeta de fin. Con el hilo de cada paso, que es el formato del documento |
| [`06-gui-y-vistas.md`](../../docs/06-gui-y-vistas.md) | La disposición acoplada (fila 0 / fila 1 de la columna de contenido), la ficha de `VideoPlayer` con el parámetro `floating`, la columna de información y la pantalla completa. Y `VIDEO_BG` en la lista de tokens |
| [`05-proveedores-y-scraping.md`](../../docs/05-proveedores-y-scraping.md) | Un apartado de **hosters**: qué entrega cada uno, con qué cabecera y con qué caducidad. Y cómo se diagnostica uno que dejó de resolver |
| [`07-concurrencia-e-hilos.md`](../../docs/07-concurrencia-e-hilos.md) | Los eventos de mpv, que llegan en **su propio hilo**; y la petición de servidores, que ya no está en el de Tk |
| [`09-verificacion-y-pruebas.md`](../../docs/09-verificacion-y-pruebas.md) | Cómo probar la capa de resolución **sin GUI** (el script de la fase 1) y el checklist manual del reproductor |
| [`10-invariantes-y-trampas.md`](../../docs/10-invariantes-y-trampas.md) | Las trampas nuevas — ver abajo |
| [`11-playbooks.md`](../../docs/11-playbooks.md) | **§ nueva: «añadir un resolutor»**, con el caso real de uno de los tres |
| [`12-deuda-tecnica-y-roadmap.md`](../../docs/12-deuda-tecnica-y-roadmap.md) | Deuda nº 1 **cerrada**; los hosters sin resolver como deuda nueva; y **§7** con lo que hizo la fase 5 sobre la GPL |
| [`README.md`](../../docs/README.md) | Cabecera de metadatos, «último cambio», «siguiente tarea» y el mapa «si tocas X, lee Y» |

### Paso 6.3 — Las trampas nuevas

Candidatas seguras, todas con **síntoma observable**, que es el formato del documento:

- 🔴 **`Sec-Fetch-Site: same-origin` en los segmentos de zilla** — el playlist responde 200 y los
  segmentos 403. Síntoma: el reproductor carga y no pinta nada.
- 🔴 **`Referer` ROMPE jkplayers** (410 Gone). Es lo contrario de MP4Upload, que lo exige y además
  **el suyo propio**, no el del sitio que lo embebe. La política de cabeceras es **por hoster**.
- 🔴 **Las URLs de jkplayers están atadas a la IP** (la incrustan en el path) y las de playmudos
  **caducan en ~3 h**. Síntoma: funciona en el momento y falla al día siguiente, o tras una VPN.
- 🔴 **Los eventos de mpv llegan fuera del hilo de Tkinter.** Síntoma: `invalid command name
  ...!ctkcanvas` sin que el usuario haya tocado nada.
- 🔴 **`end-file` dispara también al parar** — hay que mirar el `reason`. Síntoma: la tarjeta de
  fin sale al volver a la ficha.
- 🔴 **Sobre la superficie de mpv, Tk no recibe `<Motion>` ni teclas.** Síntoma: la barra de
  pantalla completa no vuelve al mover el ratón, o `Esc` no sale. El ratón y el teclado se piden
  a mpv (lo que encontrase el paso 0.7).
- ⚠️ **La barra flotante y el deslizador de volumen son ventanas aparte.** Síntomas posibles: la
  barra se queda encima de otra aplicación tras Alt+Tab, o el deslizador se cierra al pasar del
  icono a él (`<Leave>` sin margen de gracia). Confirmar con lo que pasó en las fases 0 y 3.
- 🔴 **Una superficie nativa no admite widgets Tk encima ni vive dentro de un
  `CTkScrollableFrame`.** Síntoma: controles invisibles, o vídeo que se recorta al hacer scroll.
- 🔴 **La DLL de `binaries` cae dentro de `_internal/`** y `ctypes` puede no encontrarla. Síntoma:
  el `.exe` arranca perfecto y falla **solo al reproducir**.
- ⚠️ **Servidores con nombre repetido** se perdían en un dict (B1). Si vuelve a aparecer un
  `{s.server: s.url}` por ahí, es el mismo bug.

Numerarlas a continuación de la **35** y respetar el formato del documento.

### Paso 6.4 — Cerrar el plan

En [`ESTADO.md`](../ESTADO.md), sección *Cierre del plan*:

- **Qué quedó fuera** — hosters sin resolver, lo que dice el `README.md` en *Qué NO entra*, y lo que
  se haya decidido no hacer por el camino.
- **Qué fases se cerraron sin verificar** y por qué.
- **Qué sigue vigente del §10 de la investigación**: lo que aquel día no se pudo comprobar y este
  plan tampoco ha comprobado.
- **Qué recomendaría como siguiente tarea**, mirando el roadmap de `CLAUDE.md`.
- Poner las 7 fases en ✅ (o con sus excepciones anotadas).

---

## Terminado cuando

- [ ] `CLAUDE.md` describe la capa de resolución y el reproductor, y **no** dice que la petición de
      servidores esté en el hilo de Tkinter.
- [ ] Los **10 documentos** de la tabla están actualizados y la fecha de cabecera sincronizada.
- [ ] `docs/03` tiene el flujo nuevo, con el hilo de cada paso.
- [ ] `docs/10` tiene las trampas nuevas, numeradas y con síntoma.
- [ ] `docs/11` tiene el playbook «añadir un resolutor».
- [ ] `docs/12` tiene la deuda nº 1 **tachada** y los hosters pendientes anotados.
- [ ] Los enlaces internos de `.claude/` no están rotos (barrido completo, como el 2026-08-21).
- [ ] Los nombres de API citados están **cotejados contra el código**, no escritos de memoria.
- [ ] `git grep -n "TODO" -- src/` inventariado, **mirando la salida**.
- [ ] `ESTADO.md` cierra con las 7 fases en ✅ o con sus excepciones.

## Verificación

- Barrido de enlaces internos de `.claude/`: **0 rotos**.
- Prueba de humo final: `python -u src/app.py` desde la raíz, recorrer las vistas, **reproducir un
  episodio** y comprobar que no hay ni un `Traceback` ni un `invalid command name` en la salida.
- `sha256` de `DB_Animes.db` idéntico antes y después.

## Qué anotar en ESTADO.md

El cierre del plan (paso 6.4), qué documentos se tocaron, cuántas trampas nuevas quedaron y con qué
números, y el recuento final de `TODO` en `src/`.
