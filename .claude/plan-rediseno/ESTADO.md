# Estado del rediseño

> Este fichero es la memoria del plan entre sesiones. Lo lee y lo escribe `/fase`.
> Si contradice al árbol de trabajo, **gana el árbol**: `git log --oneline` y `git status` mandan.

| | |
|---|---|
| **Fase actual** | 2 — Nuevos lanzamientos |
| **Situación** | ⬜ no empezada |
| **Último paso completado** | Paso 1.5 — `ViewHeader` y cableado de `MainWindow` (**fase 1 cerrada**) |
| **Siguiente paso** | Paso 2.1 — leer la ficha de la fase 2 y `recentAnimes.py` |
| **Rama** | ✅ `feature/ui-redisign` (**no** `feature/rediseno-ui`: ya existía, ver Decisiones) |
| **Base** | `bd25742` en `feature/ui-redisign` (fase 1). El plan partió de `6377b92`, no de `4f9e429` |
| **Commits** | automáticos (uno al cerrar cada fase) |
| **Actualizado** | 2026-08-20 |

---

## Tablero

| # | Fase | Situación | Commit | Verificada |
|---|---|---|---|---|
| 1 | Cimientos | ✅ terminada | `bd25742` | ✅ app ejecutada y **mirada** (desplegada y plegada) + 73 comprobaciones |
| 2 | Nuevos lanzamientos | ⬜ no empezada | — | — |
| 3 | Viendo | ⬜ no empezada | — | — |
| 4 | Pendientes | ⬜ no empezada | — | — |
| 5 | Favoritos | ⬜ no empezada | — | — |
| 6 | Finalizados | ⬜ no empezada | — | — |
| 7 | Buscar | ⬜ no empezada | — | — |
| 8 | Ficha del anime | ⬜ no empezada | — | — |
| 9 | Cohesión | ⬜ no empezada | — | — |

**Situación**: ⬜ no empezada · 🟡 en curso · ✅ terminada · ⚠️ terminada sin verificar · ❌ revertida

---

## Decisiones tomadas sobre la marcha

Aquí va lo que se decide durante una fase y afecta a las siguientes. Una línea por decisión, con la
fase que la tomó. Empieza vacío a propósito: las decisiones de partida están en
[DISENO.md](DISENO.md).

| Fase | Decisión |
|---|---|
| 1 | **La rama es `feature/ui-redisign`, no `feature/rediseno-ui`.** Ya existía al empezar, creada por el usuario, y es donde vive el commit `6377b92` que trajo este plan. Renombrarla no está autorizado y el nombre es suyo. Todas las fases commitean ahí |
| 1 | **Las medidas de `DISENO.md` §3 también viven en `theme.py`**, en una clase `Metrics` junto a `Theme`. Mismo motivo que los colores: que un número del diseño no se copie a mano en cinco vistas y luego solo se corrija en tres |
| 1 | **`utils/utils.py` duplica el valor de `POSTER_CACHE_SIZE` a propósito.** `docs/01 §2` le prohíbe importar de `gui/**`, así que no puede leer `Metrics.POSTER_CACHE_SIZE`. El comentario de `utils.py:24-33` lo dice y nombra a su pareja: si cambia uno, cambia el otro |
| 1 | **Borrar las 6 carpetas de pósters NO era inocuo.** Las 4 vistas de estado pintan con `load_image()`, que **no sale a la red**: sin fichero se quedan con el placeholder gris hasta que el usuario vuelva a marcar el estado a mano. Se regeneraron los 39 pósters desde `poster_url` con un script del scratchpad (BD abierta en `?mode=ro`). `recent_animes/` y `search/` sí se rellenan solas. **Si una fase futura vuelve a vaciar la caché, tiene que repetir esa regeneración** |
| 1 | **`get_anime_image()` sigue con su `(195, 275)` por defecto.** Subirlo a los 248 × 372 de la ficha es cosa de la **fase 8**, que es la que rehace `anime_window.py` |
| 1 | 🔴 **`SidebarButton` ya no es un widget.** Pasó de `CTkButton` a clase llana: solo describe el destino (`sidebar_text`, `sidebar_command`, `sidebar_icon(size)`). Quien pinta es `Sidebar`. La firma del constructor **no cambió**, así que las 6 vistas heredan igual sin tocarlas. Si una fase futura necesita el botón como widget, no existe: lo que hay es el `_NavItem` de la barra |
| 1 | 🔴 **Un `CTkFrame` sin hijos conserva su tamaño por defecto (200 × 200)** como tamaño pedido, y estira la fila que lo contenga. Costó una tarde: la barrita de acento de 2 px inflaba la fila a 200 y el icono y la etiqueta caían en `y=86`, **fuera de la parte visible** — la barra salía con los seis destinos en blanco, sin ningún error. **Todo `CTkFrame` decorativo o todavía vacío necesita `height=` explícito** (`controls_frame` de `ViewHeader` nace con `height=1` por esto). Aplica a `PosterGrid`, `Pager`, `AnimeRow`, `SidePanel`… — es decir, a casi todo lo que construyen las fases 2-8 |
| 1 | **El ancho de la barra necesita `grid_propagate(False)` *y* `minsize` en la columna 0 del padre.** Solo con el primero, la rejilla de `MainWindow` le roba píxeles cuando el contenido pide más ancho del que cabe (medido: 219 en vez de 224). Lo pone `Sidebar.__apply_collapsed_layout()` en cada plegado |
| 1 | **Las etiquetas de los destinos viven en cada vista**, en su `super().__init__` (`"Favoritos"`, `"Viendo"`…), no en la barra. La barra las lee de `sidebar_text`. Renombrar una pestaña es tocar su vista, no `Sidebar` |
| 1 | **El orden de la barra cambió**: Nuevos · Favoritos · Viendo · Pendientes · Finalizados · Buscar. Antes finalizados iba delante de viendo y pendientes. Lo fija la lista `destinations` de `load_sidebar_buttons()` |

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

### Fase 1 · Paso 1.5 — `ViewHeader` y cableado de `MainWindow`          (2026-08-20)
- Ficheros: `src/gui/components/view_header.py` (nuevo), `src/gui/main_window.py`
- `ViewHeader`: título `T_VIEW` + subtítulo `T_SUB` a la izquierda y `controls_frame` vacío a la
  derecha, alto 80. **Todavía no lo usa ninguna vista**: lo estrena la fase 2.
- `MainWindow`: fuera `create_sidebar_frame()`; `sidebar_frame` pasa a ser la `Sidebar` y se
  construye en `load_sidebar_buttons()` (necesita el gestor de proveedores y las preferencias, que
  no existen en `__config_main_frames()`). `content_frame` estrena `fg_color=Theme.BG`.
- `change_appearance_mode_event()` pasa de 10 líneas recorriendo widgets a **una**: con tuplas
  `(claro, oscuro)` el tema lo cambia CustomTkinter solo.
- Métodos nuevos del hub para las fases siguientes: **`refresh_sidebar_counts()`** (llámalo tras
  guardar o quitar un anime) y **`set_active_sidebar_destination()`** (para la navegación que no
  viene de un clic — el arranque y la recarga de proveedor).
- ✅ El `# TODO:` de `main_window.py:32` **está cerrado**: la ventana se titula «Mi Biblioteca» y
  ninguna pestaña lleva ya la palabra «Anime». Quedan **4** `TODO` en `src/` (2 en `jkanime.py`,
  2 en `anime_window.py`).
- Verificado: sí · app real + las tres baterías del scratchpad. Las **11** comprobaciones de
  `smoke_provider.py` cubren el punto del checklist que faltaba: pin fijar/desfijar (icono **y** fila
  en BD), cambio de proveedor que **no** escribe en BD y pone el pin en gris, y el fondo `CARD` del
  ítem activo aguantando el salto claro↔oscuro sin reconfigurar nada.
- Pendiente que deja: nada.

### Fase 1 · Paso 1.4 — `Sidebar`          (2026-08-20)
- Ficheros: `src/gui/components/__init__.py` y `sidebar.py` (nuevos),
  `src/utils/buttons/utilsButtons.py`, `src/utils/utils.py`,
  `src/dataPersistence/userPersistence.py`, y **una línea** en cada una de las 6 vistas (solo la
  etiqueta).
- `Sidebar` (`CTkFrame`) sustituye a los 6 `SidebarButton` sueltos y al pie. 6 destinos con icono +
  etiqueta + contador, activo con fondo `CARD` y barra de 2 px `ACCENT`, plegado a 84 px con globo
  de contador. Proveedor con pin y apariencia **con el mismo comportamiento de antes**, solo
  cambia el aspecto.
- `SidebarButton` deja de ser `CTkButton` (ver Decisiones). `update_icon()` desaparece: el icono es
  un único `CTkImage` con `light_image`/`dark_image` y lo cambia CustomTkinter.
- `load_dual_image()` nuevo en `utils/utils.py`.
- `UserSettingKey.SIDEBAR_COLLAPSED` + `get_sidebar_collapsed()` / `set_sidebar_collapsed()`.
  Sin migración: la tabla es clave/valor. Persistido como `"1"`/`"0"`.
- 🔴 **Dos fallos encontrados y corregidos por el camino**, los dos silenciosos: el ancho robado por
  la rejilla (219 en vez de 224) y —el gordo— los seis destinos **en blanco** porque un `CTkFrame`
  sin hijos conserva su alto por defecto de 200. Los dos están en Decisiones porque van a repetirse.
- Verificado: sí · **38 comprobaciones** de la barra (medidas, contadores, activo, plegado ida y
  vuelta, persistencia, proveedor, apariencia, ocultar/mostrar) y **24** de las vistas, todas en
  verde; más **captura de la ventana real** desplegada y plegada.
- Pendiente que deja: nada.

### Fase 1 · Paso 1.3 — Caché de pósters a 248 × 372          (2026-08-20)
- Ficheros: `src/utils/utils.py`
- Qué cambia: constante nueva `POSTER_CACHE_SIZE = (248, 372)` y los **tres** `.resize((130, 185))`
  pasan a usarla (`download_anime_poster_by_status`, `download_animes_poster._download_single`,
  `download_images_progress._download_single`). `load_image()` conserva su `(130, 185)` por defecto
  —es el tamaño **pintado**, y las 6 vistas siguen siendo las de hoy— y `get_anime_image()` su
  `(195, 275)`, con su `size=` explícito intacto (trampa 17/16).
- Caché: las 6 carpetas de `resources/images/` se movieron al scratchpad y **se regeneraron los 39
  pósters de las 4 carpetas de estado** a 248 × 372 desde `poster_url`. **39 OK, 0 fallidos.**
- ⚠️ `watching/` tenía **7** ficheros y ahora tiene **1**: la BD solo declara un anime con
  `is_watching = 1`. Los otros 6 eran huérfanos de estados anteriores. La caché queda **más**
  alineada con la BD que antes, no menos.
- ✅ De paso desaparece el huérfano `Chi.` (0 bytes) que provocaba el aviso de cada arranque
  (trampa 17).
- **`DB_Animes.db` NO se tocó**: abierta con `file:...?mode=ro`; mtime sigue en 2026-08-17 21:04.
- ⚠️ La BD tiene **29 filas**, no las 28 que dicen `CLAUDE.md` y el README del plan. Solo lectura,
  nada que corregir aquí, pero **la fase 5 debe contar 29 antes y después**.
- Verificado: sí · script del scratchpad; muestra comprobada con PIL → `(248, 372)`.
- Pendiente que deja: nada.

### Fase 1 · Paso 1.2 — `src/gui/theme.py`          (2026-08-20)
- Ficheros: `src/gui/theme.py` (nuevo)
- Qué trae: clase `Theme` con los 13 tokens de color de `DISENO.md` §1 en tuplas `(claro, oscuro)`,
  los 4 pares de píldora de estado, los 10 roles tipográficos de §2 como tuplas
  `(tamaño, negrita, mono)` y `Theme.font(size, bold, mono)` con caché. Clase `Metrics` con las
  medidas de §3.
- `WARN` es el `("#B45309", "#FBBF24")` que ya usaba `anime_window.py:441`, no uno nuevo.
- Las fuentes se construyen dentro de `font()`, nunca a nivel de módulo: un `CTkFont` necesita que
  ya exista la raíz de Tk.
- Verificado: sí · import + construcción de fuentes con una raíz CTk real (familia, tamaño, peso,
  caché y la monoespaciada).
- Pendiente que deja: nadie lo usa todavía. Lo estrena el paso 1.5.

### Fase 1 · Paso 1.1 — Orientación y rama          (2026-08-20)
- Ficheros: ninguno.
- Rama: **ya existía** `feature/ui-redisign` con el plan commiteado en `6377b92`. No se crea
  `feature/rediseno-ui` (ver Decisiones). `src/` estaba intacto respecto a `4f9e429`.
- Foto del «antes»: ✅ **la app arranca entera** — valida las dos BD, aplica el proveedor fijado
  (`animeav1`), baja los pósters y pinta la portada.
- Verificado: sí · `python -u src/app.py`, log en el scratchpad.
- Pendiente que deja: nada.
