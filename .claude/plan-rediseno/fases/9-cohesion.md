# Fase 9 — Cohesión

| | |
|---|---|
| **Objetivo** | Que las 7 vistas parezcan la misma aplicación: estados vacíos, repaso claro/oscuro, barra plegada en todas, limpieza y documentación |
| **Diseño visual** | [DISENO-VISUAL.html](../DISENO-VISUAL.html) **entero** — esta fase compara las 7 vistas entre sí, y `#claro` es la referencia del tema claro. Ábrelo en el navegador, **no** con `Read` |
| **Estrena** | `EmptyState` |
| **Toca** | `src/gui/components/empty_state.py` (nuevo), las 7 vistas (retoques), `MiBibliotecaAnime.spec`, `.claude/docs/`, `.claude/CLAUDE.md` |
| **No toca** | Nada estructural. Si esta fase necesita rehacer una vista, es que su fase se cerró mal |
| **Riesgo** | Bajo |
| **Depende de** | Las 8 anteriores |

---

## Antes de empezar

Leer `ESTADO.md` **entero**, incluida la bitácora y la tabla de *Decisiones*. Esta fase es la que
paga las deudas que las 8 anteriores fueron dejando anotadas.

Si alguna fase quedó en ⬜ o en ⚠️ sin verificar, **decirlo al principio** y decidir con el usuario si
se cierra igual o si se vuelve a esa fase primero.

---

## Pasos

### Paso 9.1 — Estados vacíos

`EmptyState`: icono, una frase y una acción. Sustituye al `CTkLabel` suelto de hoy. Uno por vista,
con texto propio:

| Vista | Frase | Acción |
|---|---|---|
| Nuevos lanzamientos | «No se han podido cargar los estrenos» | Reintentar / cambiar de proveedor |
| Favoritos | «Todavía no has marcado ningún favorito» | Ir a Nuevos lanzamientos |
| Viendo | «No tienes nada a medias» | Ir a Pendientes |
| Pendientes | «No tienes nada en la cola» | Buscar un anime |
| Finalizados | «Aún no has terminado ninguno» | Ir a Viendo |
| Buscar | «Sin resultados para “X” en *Proveedor*» | Probar con otro proveedor |

El de Nuevos lanzamientos es distinto de los demás: ahí el vacío casi siempre significa **fallo de
red o de proveedor**, no biblioteca vacía. No decir «no tienes nada» cuando lo que pasa es que el
sitio no respondió.

### Paso 9.2 — Repaso claro/oscuro

Recorrer las 7 vistas en los dos temas y con `System`. Buscar en concreto:

- Colores literales que se colaran fuera de `theme.py` — `git grep -nE "#[0-9A-Fa-f]{6}" -- src/`
  no debería devolver nada fuera de `theme.py` (y del `WARN` que ya estaba en `anime_window.py`).
- Sellos sobre pósters claros: que sigan legibles.
- Texto sobre `ACCENT`: tiene que usar `ACCENT_INK`, que es blanco en claro y casi negro en oscuro.

### Paso 9.3 — La barra plegada en las 7

La fase 1 la dejó funcionando, pero solo se probó a fondo en la ficha. Comprobar que las 6 vistas
respiran con 1 356 px de ancho: la rejilla de 6 y la de 5 se ensanchan, las listas también, y nada
se sale ni se recorta.

### Paso 9.4 — Limpieza

- ¿Quedó `AccordionFilterButton` huérfana tras la fase 7? Si nadie la usa, retirarla.
- ¿Quedan `SidebarButton` o vistas viejas sin usar?
- Los iconos `viendo_light/dark.png` y `pendientes_light/dark.png` existen en
  `resources/images/utils/` pero su uso está comentado. Decidir: usarlos o borrar el código muerto.
- ⚠️ **`hiddenimports` del `.spec`**: el plan ha añadido `gui/theme.py` y varios `gui/components/*`.
  Hay que declararlos o el `.exe` no arranca. Recorrer uno a uno como se hizo el 2026-08-07 y
  **compilar de verdad** para comprobarlo ([`docs/11 §6`](../../docs/11-playbooks.md)).
- ⚠️ **No volver a meter `resources/DB` ni las carpetas de pósters en `datas`**: eso distribuiría la
  biblioteca del desarrollador ([trampa 18d y 18e](../../docs/10-invariantes-y-trampas.md)).
- `git grep -n "TODO" -- src/` e inventariar los que quedan. El de `main_window.py:32` lo cerró la
  fase 1.

### Paso 9.5 — Documentación

- `.claude/docs/06-gui-y-vistas.md`: reescribir. Es el documento que más ha caducado.
- `.claude/docs/02-mapa-de-modulos.md`: fichas de `theme.py` y de cada componente nuevo.
- `.claude/docs/04-modelo-de-datos.md`: la columna `rating`.
- `.claude/docs/13`: la clave `sidebar_collapsed`, `last_watched_anime_ids` y `favourites_order`.
- `.claude/docs/10-invariantes-y-trampas.md`: trampas nuevas que hayan aparecido (candidata segura:
  el sello con `place()` sobre `grid()`).
- `.claude/docs/09-verificacion-y-pruebas.md`: checklist manual de las 7 vistas nuevas.
- `.claude/CLAUDE.md`: la sección de arquitectura GUI y el roadmap (los puntos que este plan cierra).
- `.claude/docs/README.md`: cabecera de metadatos, «último cambio» y «siguiente tarea».

---

## Terminado cuando

- [ ] Las 7 vistas tienen estado vacío y ninguno miente sobre la causa.
- [ ] `git grep -nE "#[0-9A-Fa-f]{6}" -- src/` solo devuelve `theme.py`.
- [ ] Las 7 vistas se ven bien en claro, en oscuro, con la barra desplegada y plegada.
- [ ] El `.exe` compila y arranca.
- [ ] La documentación no contradice al código.
- [ ] `ESTADO.md` cierra con las 9 fases en ✅ (o con las excepciones anotadas).

## Verificación

Recorrido completo: las 7 vistas × 2 temas × 2 estados de barra. Después
`pyinstaller MiBibliotecaAnime.spec` y arrancar el `.exe` resultante.

## Qué anotar en ESTADO.md

El cierre del plan: qué quedó fuera, qué fases se cerraron sin verificar, y qué recomendarías como
siguiente tarea del roadmap.
