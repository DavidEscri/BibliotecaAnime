# Estado del plan de reproducción in-app

> Este fichero es la memoria del plan entre sesiones. Lo lee y lo escribe `/reproductor`.
> Si contradice al árbol de trabajo, **gana el árbol**: `git log --oneline` y `git status` mandan.

| | |
|---|---|
| **Fase actual** | **0 · Spike de libmpv** — ⬜ no empezada |
| **Situación** | ⬜ **Ninguna fase ejecutada todavía.** Plan creado el 2026-08-24; **diseño visual aprobado el 2026-09-23** ([DISENO-VISUAL.html](DISENO-VISUAL.html)) y fichas 0, 1, 3, 4 y 6 ajustadas a él |
| **Último paso completado** | Ninguno |
| **Siguiente paso** | Paso 0.1 — orientación, rama y foto del «antes» ([ficha](fases/0-spike-libmpv.md)) |
| **Rama** | ⬜ pendiente: `feature/reproductor-in-app`, sacada de `feature/ui-redisign`. **La crea la fase 0** |
| **Base** | `95abd56` en `feature/ui-redisign` (⚠️ esa rama **sigue sin fusionarse con `main`**) |
| **Commits** | automáticos (uno al cerrar cada fase) |
| **Actualizado** | 2026-09-23 |

---

## Tablero

| # | Fase | Situación | Commit | Verificada |
|---|---|---|---|---|
| 0 | Spike de libmpv | ⬜ no empezada | — | — |
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
| — | — | — |

---

## Puntos de decisión abiertos

Los hereda el plan de la §9 de la investigación. **Cada uno tiene una fase que lo cierra**; hasta
entonces nadie decide por su cuenta.

| # | Decisión | Quién la cierra | Estado |
|---|---|---|---|
| 1 | 🔴 **¿Marcar el episodio como visto al llegar al final?** Es un supuesto declarado, no una petición, y **escribe en la biblioteca real** | La **fase 4**, preguntando al usuario **antes** de escribir una línea | ⬜ abierta |
| 2 | **¿Se versiona `libmpv-2.dll` en el repo (`vendor/`) o se ignora y se documenta la descarga?** Son ~40 MB permanentes en el historial de git | La **fase 0**, al bajarla | ⬜ abierta |
| 3 | **¿Volumen en la barra de controles?** | El **usuario**, con el diseño | ✅ **cerrada el 2026-09-23: sí.** Icono plegado y deslizador vertical al pasar el ratón |
| 4 | **¿Ofrecer MP4Upload (H.264) como alternativa manual** si el AV1 1080p de AnimeAV1 consume demasiado? | La **fase 0** lo mide; si duele, lo implementa la **fase 3** | ⬜ abierta |
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
