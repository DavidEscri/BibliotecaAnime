# Plan de rediseño de la interfaz — 9 fases

| | |
|---|---|
| **Creado** | 2026-08-20 |
| **Punto de partida** | commit `4f9e429`, rama `develop`, árbol con 4 PNG sin trackear |
| **Diseño visual** | [`DISENO-VISUAL.html`](DISENO-VISUAL.html) — **ábrelo en el navegador**. Las 7 vistas, la barra lateral en sus dos estados y la comprobación en claro |
| **Especificación ejecutable** | [DISENO.md](DISENO.md) — tokens y medidas exactas. Es de donde se implementa |
| **Estado vivo** | [ESTADO.md](ESTADO.md) — lo actualiza cada sesión |
| **Copia en la nube** | https://claude.ai/code/artifact/69458b98-88bd-479c-960c-2b441d56344a — el mismo documento, por si quieres compartirlo |

> ⚠️ **`DISENO-VISUAL.html` es para mirarlo, no para leerlo.** Son ~1 350 líneas de maquetación que
> no contienen nada que no esté en `DISENO.md`. Una sesión que lo abra con `Read` se gasta el
> contexto para nada: implementa desde el `.md` y usa el `.html` solo si necesitas resolver una duda
> visual que la especificación no cierra.

Rediseño completo de las 7 vistas más la barra lateral. Es **solo interfaz**: no cambia el scraping,
ni el contrato de proveedores, ni el fallback, ni la identidad de persistencia.

---

## Cómo se ejecuta

**Una fase = una sesión.** El bucle es siempre el mismo:

```
/clear          ← lo haces tú
/fase           ← arranca o retoma lo que toque, según ESTADO.md
```

`/fase` sin argumentos mira [ESTADO.md](ESTADO.md) y decide. `/fase 5` fuerza una concreta.
`/fase estado` solo informa y no toca nada.

**La sesión que ejecuta una fase no empieza la siguiente.** Al cerrar, avisa y para.

### Por qué comandos y no «yo te aviso de hacer el clear»

Un `/clear` borra el contexto entero. Cualquier mecanismo que dependa de que yo recuerde algo entre
sesiones está roto por construcción: después del clear no sé ni que existe este plan. Por eso el
estado vive en disco (`ESTADO.md` + el log de git) y el disparador es tuyo.

---

## Las 9 fases

El orden **no** es el del documento de diseño. Es orden de dependencia: cada fase estrena un
componente que las siguientes reutilizan, así que hacerlas en otro orden obliga a construir dos
veces lo mismo.

| # | Fase | Estrena | Riesgo |
|---|---|---|---|
| 1 | [Cimientos](fases/1-cimientos.md) | `theme.py`, barra lateral plegable, cabecera de vista, caché de pósters a mayor tamaño | Medio — toca el esqueleto de `MainWindow` |
| 2 | [Nuevos lanzamientos](fases/2-nuevos-lanzamientos.md) | Rejilla de pósters, paginación, tarjetas «Retomar» | Bajo |
| 3 | [Viendo](fases/3-viendo.md) | Fila en cascada, panel lateral de retomar | Bajo |
| 4 | [Pendientes](fases/4-pendientes.md) | — (reutiliza la fila) | Bajo |
| 5 | [Favoritos](fases/5-favoritos.md) | Calificación personal | 🔴 **Alto — única fase que toca `DB_Animes.db`** |
| 6 | [Finalizados](fases/6-finalizados.md) | Sello sobre el póster | Bajo |
| 7 | [Buscar](fases/7-buscar.md) | Fichas de género, paginación del proveedor, sello «ya lo tienes» | Medio |
| 8 | [Ficha del anime](fases/8-ficha.md) | Botones encendido/apagado, lista de episodios | Medio — `anime_window.py` son 1 155 líneas |
| 9 | [Cohesión](fases/9-cohesion.md) | Estados vacíos, repaso claro/oscuro, documentación | Bajo |

---

## Reglas del plan

1. **La app tiene que arrancar y ser usable al final de cada fase.** Las vistas que aún no han
   llegado a su fase siguen funcionando con su aspecto viejo. Nunca se deja el árbol a medias entre
   sesiones.
2. **`resources/DB/DB_Animes.db` es la biblioteca real** (28 filas irrecuperables). Solo la fase 5
   la modifica, y con copia de seguridad previa y prueba sobre copia. Ver
   [docs/09 §3b](../docs/09-verificacion-y-pruebas.md).
3. **Rama propia**: `feature/rediseno-ui`, sacada de `develop`. La crea la fase 1.
4. **Un commit al cerrar cada fase**, con el mensaje `Rediseño fase N — <nombre>`. Es lo que hace
   que «¿qué se hizo la última vez?» tenga una respuesta fiable y no dependa de la prosa de
   `ESTADO.md`. Si prefieres commitear tú, cambia la línea *Commits* de [ESTADO.md](ESTADO.md) a
   `manuales` y las fases pararán a pedírtelo.
5. **Ningún cambio de comportamiento sin declararlo.** El rediseño toca aspecto y disposición; donde
   además cambia lo que hace la app (botones de estado, orden de pendientes, sello de duplicado) la
   fase lo dice en su apartado *Cambios de comportamiento*.
6. **Sin tests**: la verificación es lanzar `python src/app.py` y mirar. Si una fase no se ha podido
   ejecutar, se cierra marcada como **no verificada** en `ESTADO.md`. No se disimula.
7. **Cabecera obligatoria** en todo `.py` nuevo (`__author__`, `__subsystem__`, `__module__`,
   `__version__`, `__info__`) — plantilla en [docs/08](../docs/08-convenciones-y-estilo.md).
8. **Antes de tocar nada**, la fase lee [docs/10-invariantes-y-trampas.md](../docs/10-invariantes-y-trampas.md).
   Las 28 trampas siguen vigentes; el rediseño no anula ninguna.

---

## Qué NO entra en este plan

Para que no se cuele por el camino:

- Convivencia anime + manga (roadmap, posterior).
- Bloque «Si te ha gustado X, te puede interesar…».
- Proveedores nuevos (MonosChinos2, TioAnime).
- Redibujar los iconos de origen dudoso (deuda **B11**,
  [docs/12 §4](../docs/12-deuda-tecnica-y-roadmap.md)). El rediseño los sigue usando tal cual; la
  fase 9 deja anotado cuáles quedan.

---

## Si algo se tuerce

| Síntoma | Qué hacer |
|---|---|
| Una sesión murió a mitad de fase | `/fase` — lee `ESTADO.md`, ve el paso a medias y `git status`, y retoma desde ahí |
| `ESTADO.md` no cuadra con el árbol | Gana el árbol. `git log --oneline` y `git status` son la verdad; `ESTADO.md` se corrige |
| Una fase salió mal entera | `git revert` de su commit, poner la fase a ⬜ en `ESTADO.md` y volver a lanzarla |
| Quieres saltarte una vista | `/fase N` de la siguiente. Deja la saltada a ⬜; la fase 9 avisará de que falta |
