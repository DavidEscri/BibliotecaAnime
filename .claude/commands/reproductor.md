---
description: Ejecuta o retoma una fase del plan de reproducción in-app (.claude/plan-reproductor/). Sin argumentos, continúa por donde iba.
---

# ROL

Estás ejecutando **una fase** del plan de reproducción in-app de episodios de BibliotecaAnime.

Vienes de una sesión limpia: **no recuerdas nada**. Todo lo que necesitas está en disco. No supongas
nada sobre lo que se hizo antes: léelo.

Argumento recibido: `$ARGUMENTS`

| Argumento | Qué hacer |
|---|---|
| *(vacío)* | Leer `ESTADO.md` y continuar la fase actual, o empezar la siguiente si la actual está ✅ |
| Un número `0`-`6` | Ejecutar esa fase, aunque no sea la que tocaba |
| `estado` | **Solo informar.** Leer, resumir y parar. No tocar ni un fichero |
| `cerrar` | Cerrar la fase en curso: verificar, commitear y marcarla ✅. Sin ejecutar pasos nuevos |
| Otra cosa | Decir que no se entiende y enseñar esta tabla |

---

# REGLAS INQUEBRANTABLES

1. **Una sesión, una fase.** Al terminar, **no empieces la siguiente**: avisa al usuario de que haga
   `/clear` y vuelva a lanzar `/reproductor`.
2. 🔴 **La degradación es sagrada.** Si un hoster no resuelve, si el reproductor no arranca o si el
   medio devuelve 403, la app **abre el navegador**, que es lo que hace hoy. Ninguna fase puede
   dejar el proyecto peor que `webbrowser.open()`. Si una fase te obliga a elegir entre «funciona a
   medias» y «cae limpio al navegador», **cae al navegador**.
3. **`resources/DB/DB_Animes.db` es la biblioteca real del usuario** — 28 filas irrecuperables.
   Solo la **fase 4** la modifica, y **solo después de que el usuario confirme** el supuesto de
   «llegar al final marca el episodio como visto» (punto de decisión 1 de `ESTADO.md`). La
   verificación va sobre **copia**, comprobando el `sha256` de la real al terminar. Cualquier otra
   fase que se vea escribiendo ahí está haciendo algo mal: para y pregunta.
4. 🔴 **Sin reintentos en bucle contra los sitios reales.** El sondeo del 2026-08-23 dejó la IP
   bloqueada por Cloudflare, también para un navegador de verdad. Peticiones espaciadas, y al primer
   403 se cae a otro servidor. Si empiezan a llover 403, **para y espera**: no es un bug que se
   arregle insistiendo.
5. **Actualiza `ESTADO.md` según avanzas**, no solo al final. Si esta sesión se corta a mitad, lo que
   quede escrito es lo único que tendrá la siguiente. Y si tomas una decisión que afecta a fases
   posteriores, va a la tabla de **Decisiones**.
6. **Git**: puedes crear la rama `feature/reproductor-in-app` (desde `feature/ui-redisign`) y
   commitear al cerrar una fase — eso está autorizado por el plan. **Nada más**: ni `push`, ni
   `merge`, ni `rebase`, ni `reset`, ni tocar `main`, `develop` ni `feature/ui-redisign`. Si
   `ESTADO.md` dice `Commits: manuales`, tampoco commitees: prepara el cambio y pídeselo al usuario.
7. **La app tiene que arrancar al terminar la fase.** Si no arranca, no cierres la fase: deja el
   estado en 🟡, escribe en la bitácora qué está roto y dilo.
8. **Sin tests.** La verificación es lanzar `python src/app.py` desde la raíz y **ver y oír** el
   resultado. Si no puedes abrir ventana Tk, o si los sitios no responden ese día, cierra la fase
   como ⚠️ **terminada sin verificar** y dilo claramente. No lo disimules.
   🔴 **«Bytes descargados» no es «vídeo reproducido».** La investigación ya comprobó *magic
   numbers* y logs de demuxer; ese es justo el hueco que este plan viene a tapar. Si no lo has
   visto en pantalla, no está verificado.
9. **Dependencias nuevas solo en `biblio_anime_env/`.** `requirements.txt` no se toca hasta la
   fase 5, que es la que además regenera `THIRD-PARTY-NOTICES.txt` (caduca al tocarlo).
10. **Scripts desechables solo en el scratchpad**, nunca en el repo.
11. 🔴 **Ningún color literal fuera de `src/gui/theme.py`.** Si la barra de controles necesita un
    color que no está, se añade el token primero. Comprobable:
    `git grep -nE "#[0-9A-Fa-f]{6}" -- src/` solo debe devolver `theme.py`.
12. **Cabecera obligatoria** en todo `.py` nuevo: `__author__` (Jose David Escribano Orts),
    `__subsystem__`, `__module__`, `__version__`, `__info__`. Comentarios y textos de UI en
    **español con tildes**; identificadores en inglés.

---

# PASO 0 — Orientación (obligatorio, antes de tocar nada)

En este orden:

1. `.claude/plan-reproductor/ESTADO.md` — dónde estábamos, qué se decidió y qué decisiones siguen
   **abiertas**.
2. `.claude/plan-reproductor/README.md` — las reglas del plan y lo que ya está decidido.
3. `git status` · `git log --oneline -8` · `git branch --show-current`.
4. La ficha de la fase que toca: `.claude/plan-reproductor/fases/<N>-*.md`.
5. Lo que esa ficha mande leer en su apartado *Antes de empezar* — incluidas **las secciones
   concretas** de la investigación.

⚠️ **No leas entero `.claude/plans/investigacion-reproduccion-in-app-kind-flask.md`.** Son ~700
líneas y cada ficha te dice qué secciones necesita (§4.1 para zilla, §5 para el backend, §6 para las
restricciones de interfaz…). Leerlo completo te gasta el contexto en hosters que tu fase no toca.

**Si `ESTADO.md` contradice al árbol de trabajo, gana el árbol.** El log de git y `git status` son la
verdad; `ESTADO.md` es prosa y puede haberse quedado a medias. Corrígelo y dilo.

🔴 **Si vas a ejecutar la fase 3, 4 o 5 y la fase 0 está en ⬜**: dilo y para. Esas tres dan por
buenas cosas de mpv que **nadie ha comprobado** — la investigación lo dejó por escrito en su §10.

Después, **antes de editar nada**, resume al usuario en 10 líneas o menos:

- Qué fase toca y por qué.
- Qué se hizo la última vez (del último commit y de la bitácora).
- Si hay una fase a medias, **qué paso quedó abierto**.
- Qué decisiones siguen abiertas y si alguna bloquea esta fase.
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
Decisiones** de `ESTADO.md`. Es lo que evita que la fase 5 se contradiga con la 0.

Si te encuentras con algo que la ficha no previó y que cambia el alcance, **para y pregunta**. No
amplíes la fase por tu cuenta. Y si lo que se tuerce es un **sitio real** que ha cambiado, eso no es
ampliar el alcance: es el trabajo. Anótalo con la fecha, arregla su resolutor y sigue.

---

# PASO 2 — Verificar

Lo que diga el apartado *Verificación* de la ficha. Como mínimo: lanzar la app, recorrer lo que la
fase toca, y comprobar que **pulsar un servidor no resuelto sigue abriendo el navegador**.

Si la fase toca la BD (solo la 4), comprobar el recuento de filas **y el `sha256`** antes y después.

---

# PASO 3 — Cerrar

1. Recorre el checklist *Terminado cuando* de la ficha y respóndelo **punto por punto**, con un sí o
   un no. Nada de «todo correcto» genérico.
2. `git add` de lo que toca esta fase y commit:
   `Reproductor fase N — <nombre>`, con el pie `Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>`.
3. En `ESTADO.md`: marca la fase ✅ (o ⚠️ si no se pudo verificar), pon su commit en el tablero,
   avanza *Fase actual* a la siguiente, escribe su primer paso en *Siguiente paso*, y anota en *Qué
   quedó sin verificar* todo lo que no hayas podido ejecutar.
4. Entrega al usuario:
   - Qué has hecho, en 5-8 líneas.
   - Qué has verificado y qué no.
   - Qué decisiones has cerrado y cuáles siguen abiertas.
   - Lo que te preocupe de cara a la fase siguiente.
   - Y esto, literal:

   > **Fase N cerrada.** Haz `/clear` y luego `/reproductor` para seguir con la fase N+1.

**No empieces la fase siguiente.** Aunque quede sesión de sobra.
