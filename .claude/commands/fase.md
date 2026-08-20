---
description: Ejecuta o retoma una fase del plan de rediseño de la interfaz (.claude/plan-rediseno/). Sin argumentos, continúa por donde iba.
---

# ROL

Estás ejecutando **una fase** del plan de rediseño de la interfaz de BibliotecaAnime.

Vienes de una sesión limpia: **no recuerdas nada**. Todo lo que necesitas está en disco. No supongas
nada sobre lo que se hizo antes: léelo.

Argumento recibido: `$ARGUMENTS`

| Argumento | Qué hacer |
|---|---|
| *(vacío)* | Leer `ESTADO.md` y continuar la fase actual, o empezar la siguiente si la actual está ✅ |
| Un número `1`-`9` | Ejecutar esa fase, aunque no sea la que tocaba |
| `estado` | **Solo informar.** Leer, resumir y parar. No tocar ni un fichero |
| `cerrar` | Cerrar la fase en curso: verificar, commitear y marcarla ✅. Sin ejecutar pasos nuevos |
| Otra cosa | Decir que no se entiende y enseñar esta tabla |

---

# REGLAS INQUEBRANTABLES

1. **Una sesión, una fase.** Al terminar, **no empieces la siguiente**: avisa al usuario de que haga
   `/clear` y vuelva a lanzar `/fase`.
2. **`resources/DB/DB_Animes.db` es la biblioteca real del usuario** — 28 filas irrecuperables. Solo
   la fase 5 la modifica, con copia previa y prueba sobre copia. Cualquier otra fase que se vea
   escribiendo ahí está haciendo algo mal: para y pregunta.
3. **Actualiza `ESTADO.md` según avanzas**, no solo al final. Si esta sesión se corta a mitad, lo que
   quede escrito es lo único que tendrá la siguiente.
4. **Git**: puedes crear la rama `feature/rediseno-ui` y commitear al cerrar una fase — eso está
   autorizado por el plan. **Nada más**: ni `push`, ni `merge`, ni `rebase`, ni `reset`, ni tocar
   `main` ni `develop`. Si `ESTADO.md` dice `Commits: manuales`, tampoco commitees: prepara el
   cambio y pídeselo al usuario.
5. **La app tiene que arrancar al terminar la fase.** Si no arranca, no cierres la fase: deja el
   estado en 🟡, escribe en la bitácora qué está roto y dilo.
6. **Sin tests.** La verificación es lanzar `python src/app.py` desde la raíz y mirar. Si no puedes
   abrir ventana Tk, cierra la fase como ⚠️ **terminada sin verificar** y dilo claramente. No lo
   disimules.
7. **Scripts desechables solo en el scratchpad**, nunca en el repo.
8. **Cabecera obligatoria** en todo `.py` nuevo: `__author__` (Jose David Escribano Orts),
   `__subsystem__`, `__module__`, `__version__`, `__info__`. Comentarios y textos de UI en
   **español con tildes**; identificadores en inglés.

---

# PASO 0 — Orientación (obligatorio, antes de tocar nada)

En este orden:

1. `.claude/plan-rediseno/ESTADO.md` — dónde estábamos.
2. `.claude/plan-rediseno/README.md` — las reglas del plan.
3. `git status` · `git log --oneline -8` · `git branch --show-current`.
4. La ficha de la fase que toca: `.claude/plan-rediseno/fases/<N>-*.md`.
5. `.claude/plan-rediseno/DISENO.md` — tokens y medidas. **Es la especificación; manda sobre tu
   criterio estético.**
6. Lo que esa ficha mande leer en su apartado *Antes de empezar*.

⚠️ **No abras `DISENO-VISUAL.html` con `Read`.** Es el diseño maquetado, ~1 350 líneas, y no contiene
nada que no esté en `DISENO.md`. Está ahí para que **el usuario** lo abra en el navegador. Si te
falta un detalle visual que la especificación no cierra, **pregúntaselo** en vez de leerte el
fichero: cada fase indica en su cabecera qué sección mirar (`DISENO-VISUAL.html#viendo`, etc.).

**Si `ESTADO.md` contradice al árbol de trabajo, gana el árbol.** El log de git y `git status` son la
verdad; `ESTADO.md` es prosa y puede haberse quedado a medias. Corrígelo y dilo.

Después, **antes de editar nada**, resume al usuario en 10 líneas o menos:

- Qué fase toca y por qué.
- Qué se hizo la última vez (del último commit y de la bitácora).
- Si hay una fase a medias, **qué paso quedó abierto**.
- Qué vas a hacer ahora.
- Cualquier cosa que no cuadre.

Con `estado`, **para aquí**.

---

# PASO 1 — Ejecutar la fase

Sigue los pasos de la ficha en orden. Después de cada paso completado:

1. Escribe una entrada en la **bitácora** de `ESTADO.md` (la más reciente arriba), con el formato
   que indica el propio fichero.
2. Actualiza la cabecera: *Último paso completado* y *Siguiente paso*.

Si durante la fase tomas una decisión que afecta a fases posteriores, **añádela a la tabla de
Decisiones** de `ESTADO.md`. Es lo que evita que la fase 6 se contradiga con la 3.

Si te encuentras con algo que la ficha no previó y que cambia el alcance, **para y pregunta**. No
amplíes la fase por tu cuenta.

---

# PASO 2 — Verificar

Lo que diga el apartado *Verificación* de la ficha. Como mínimo: lanzar la app, recorrer la vista
tocada, y comprobar que las demás siguen abriéndose.

Si la fase toca la BD (solo la 5), comprobar el recuento de filas **antes y después**.

---

# PASO 3 — Cerrar

1. Recorre el checklist *Terminado cuando* de la ficha y respóndelo **punto por punto**, con un sí o
   un no. Nada de «todo correcto» genérico.
2. `git add` de lo que toca esta fase y commit:
   `Rediseño fase N — <nombre>`, con el pie `Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>`.
3. En `ESTADO.md`: marca la fase ✅ (o ⚠️ si no se pudo verificar), pon su commit en el tablero,
   avanza *Fase actual* a la siguiente y escribe su primer paso en *Siguiente paso*.
4. Entrega al usuario:
   - Qué has hecho, en 5-8 líneas.
   - Qué has verificado y qué no.
   - Lo que te preocupe de cara a la fase siguiente.
   - Y esto, literal:

   > **Fase N cerrada.** Haz `/clear` y luego `/fase` para seguir con la fase N+1.

**No empieces la fase siguiente.** Aunque quede sesión de sobra.
