# Plan de reproducción in-app — 7 fases

| | |
|---|---|
| **Creado** | 2026-08-24 |
| **Punto de partida** | commit `95abd56`, rama `feature/ui-redisign`, árbol con 4 PNG sin trackear |
| **Investigación** | [`../plans/investigacion-reproduccion-in-app-kind-flask.md`](../plans/investigacion-reproduccion-in-app-kind-flask.md) — **es la referencia y no se duplica aquí**. Cada ficha de fase cita la sección concreta que hay que leer |
| **Estado vivo** | [ESTADO.md](ESTADO.md) — lo actualiza cada sesión |

> ⚠️ **La investigación son ~700 líneas y no se lee entera.** Cada ficha dice en su *Antes de
> empezar* qué secciones necesita (§4.1 para zilla, §5 para el backend, §6 para las restricciones de
> interfaz…). Una sesión que se lea el documento completo se gasta el contexto en hosters que su
> fase no toca.

Sustituir `webbrowser.open(url)` por un reproductor **dentro de la propia ventana**: play/pausa,
±10 s, pantalla completa, episodio anterior/siguiente y diálogo al terminar. Añade una capa nueva
(`APIs/resolvers/`) y toca la GUI; **no cambia el contrato de proveedores, ni el fallback, ni la
identidad de persistencia**.

---

## Cómo se ejecuta

**Una fase = una sesión.** El bucle es siempre el mismo:

```
/clear          ← lo haces tú
/reproductor    ← arranca o retoma lo que toque, según ESTADO.md
```

`/reproductor` sin argumentos mira [ESTADO.md](ESTADO.md) y decide. `/reproductor 3` fuerza una
concreta. `/reproductor estado` solo informa y no toca nada.

**La sesión que ejecuta una fase no empieza la siguiente.** Al cerrar, avisa y para.

### Por qué comandos y no «yo te aviso de hacer el clear»

Un `/clear` borra el contexto entero. Cualquier mecanismo que dependa de que yo recuerde algo entre
sesiones está roto por construcción: después del clear no sé ni que existe este plan. Por eso el
estado vive en disco (`ESTADO.md` + el log de git) y el disparador es tuyo.

---

## Las 7 fases

El orden es de dependencia, y **la fase 0 puede tumbar el resto del diseño**: es un spike, no código
de producción. Va primera porque la decisión de backend (§5 de la investigación) es **documental, no
verificada** — ⚠️ nada de mpv se pudo probar el 2026-08-23.

| # | Fase | Estrena | Riesgo |
|---|---|---|---|
| 0 | [Spike de libmpv](fases/0-spike-libmpv.md) | Nada — valida o tumba el backend elegido | 🔴 **Alto — decide si el plan sigue como está** |
| 1 | [Capa de resolución](fases/1-resolutores.md) | `APIs/resolvers/`: `MediaSource`, `Resolver`, 3 resolutores y el registro | Medio — depende de sitios reales |
| 2 | [Servidores fuera del hilo de Tk](fases/2-servidores-fuera-del-hilo.md) | — (cierra la deuda nº 1 del roadmap) | Bajo |
| 3 | [Panel de reproducción](fases/3-panel-de-reproduccion.md) | `VideoPlayer` (12.º componente) y `player_frame` en `MainWindow` | 🔴 **Alto — superficie nativa dentro de Tk** |
| 4 | [Navegación y fin de episodio](fases/4-navegacion-y-fin-de-episodio.md) | Diálogo de fin de episodio, anterior/siguiente | 🔴 **Alto — única fase que escribe en `DB_Animes.db`** |
| 5 | [Empaquetado](fases/5-empaquetado.md) | `binaries` en el `.spec` (📖 hoy vacío) | Medio — compila bien y revienta en ejecución |
| 6 | [Documentación](fases/6-documentacion.md) | — | Bajo |

**Por qué la 2 va antes que la 3**: la fase 3 añade una **segunda** petición de red en el mismo
punto donde hoy ya hay una en el hilo de Tkinter. Hacerlo sin sacar la primera convierte un
congelado de 2 s en uno de 4 s.

---

## Lo que ya está decidido

Sale de la investigación y **no se rediscute** en las fases. Si una fase necesita desviarse, lo
anota en la tabla de *Decisiones* de [ESTADO.md](ESTADO.md) y lo dice al entregar.

| Decisión | Dónde |
|---|---|
| **Reproducción en la misma ventana.** Nada de pestañas ni de reproductor externo | §2 |
| **Controles en barra fija bajo el vídeo**, no overlay flotante — y no es solo estética: no se pueden superponer widgets Tk sobre una superficie nativa | §2, §6.1 |
| **Backend: libmpv incrustado con `python-mpv` vía `wid`, sin proxy.** Contingencia ya probada: `python-vlc` + proxy local | §5 |
| **Empaquetar libmpv con el `.exe`** (1 DLL, ~40 MB), no VLC (~150 MB) ni exigir instalación externa | §2 |
| **La resolución es una capa nueva (`APIs/resolvers/`), NO un sexto método de `AnimeProvider`** | §7 |
| **`ServerInfo` no cambia**, y se resuelve **al pulsar «play»**, no al listar servidores: los tokens de JKAnime caducan en ~3 h | §7 |
| **El fallback del manager no interviene.** Si la resolución falla, se cae a `webbrowser.open()` | §7 |
| **Cobertura objetivo**: `HLS` + MP4Upload en AnimeAV1, `Desu`/`Magi` en JKAnime — 7/7 episodios muestreados en cada proveedor. Mega, Voe, Byse y Okru abren el navegador | §3, §4.5 |

---

## Reglas del plan

1. **La app tiene que arrancar y ser usable al final de cada fase.** Mientras el reproductor no
   exista (fases 0-2), pulsar un servidor sigue abriendo el navegador. Nunca se deja el árbol a
   medias entre sesiones.
2. 🔴 **La degradación es sagrada.** Si un hoster no se resuelve, si mpv no arranca o si el medio
   devuelve 403, la app **abre el navegador**, como hoy. Ninguna fase puede dejar el proyecto peor
   que `webbrowser.open()`.
3. **`resources/DB/DB_Animes.db` es la biblioteca real** (28 filas irrecuperables). Solo la fase 4
   la modifica, y **solo después de confirmar con el usuario** el supuesto de §2 de la investigación
   («llegar al final marca el episodio como visto»). La verificación va sobre **copia**, comprobando
   el hash de la real al terminar. Receta en [docs/09 §3b](../docs/09-verificacion-y-pruebas.md).
4. **Rama propia**: `feature/reproductor-in-app`, sacada de `feature/ui-redisign` — que es donde
   vive el código de hoy y ⚠️ **sigue sin fusionarse con `main`**. La crea la fase 0. Si prefieres
   otra base, dilo antes de lanzarla.
5. **Un commit al cerrar cada fase**, con el mensaje `Reproductor fase N — <nombre>`. Es lo que hace
   que «¿qué se hizo la última vez?» tenga una respuesta fiable y no dependa de la prosa de
   `ESTADO.md`. Si prefieres commitear tú, cambia la línea *Commits* de [ESTADO.md](ESTADO.md) a
   `manuales` y las fases pararán a pedírtelo.
6. 🔴 **Sin reintentos en bucle contra los sitios reales.** El sondeo del 2026-08-23 dejó la IP
   bloqueada por Cloudflare (✅ también para un navegador de verdad). Las fases 0, 1, 3 y 4 salen a
   la red: peticiones espaciadas, y al primer 403 se cae a otro servidor — **no se reintenta**.
7. **Sin tests**: la verificación es lanzar `python src/app.py` y **ver y oír** un episodio. Si una
   fase no se ha podido ejecutar, se cierra marcada como **no verificada** en `ESTADO.md`. No se
   disimula. ⚠️ «Bytes descargados» **no** es «vídeo reproducido»: la investigación ya llegó hasta
   ahí y ese es justo el hueco que quedó abierto.
8. **Dependencias nuevas solo en `biblio_anime_env/`**. `requirements.txt` no se toca hasta la
   fase 5, que es la que además ⚠️ **regenera `THIRD-PARTY-NOTICES.txt`** — caduca al tocarlo
   ([docs/11 §6](../docs/11-playbooks.md)).
9. **Cabecera obligatoria** en todo `.py` nuevo (`__author__`, `__subsystem__`, `__module__`,
   `__version__`, `__info__`) — plantilla en [docs/08](../docs/08-convenciones-y-estilo.md).
10. 🔴 **Ningún color literal fuera de `gui/theme.py`.** La barra de controles usa tokens; si falta
    uno, se añade allí primero. Comprobable con
    `git grep -nE "#[0-9A-Fa-f]{6}" -- src/`, que solo debe devolver `theme.py`.
11. **Antes de tocar nada**, la fase lee
    [docs/10-invariantes-y-trampas.md](../docs/10-invariantes-y-trampas.md). Las **35** siguen
    vigentes; este plan no anula ninguna y añade varias.

---

## Qué NO entra en este plan

Para que no se cuele por el camino:

- **Descargar episodios.** Es streaming; nada toca el disco salvo la caché de mpv.
- **Los hosters aplazados**: Voe, Byse, YourUpload, StreamTape y VidHide (§4.5). Y **Mega**, que
  está bloqueado de verdad (cifrado extremo a extremo). Todos siguen abriendo el navegador.
- **Recordar el minuto donde lo dejaste.** Es una columna más en `DB_Animes.db` y no se ha pedido
  (§9.3). Si se quiere, es un plan aparte.
- **Selección de calidad o de pista de subtítulos.** ⚠️ Ninguno de los dos playlists declara
  calidades alternativas ni `TYPE=SUBTITLES`: los subtítulos van incrustados en el vídeo.
- **Proveedores nuevos** (MonosChinos2, TioAnime) — aunque la capa de resolutores se diseña
  pensando en que comparten hosters con AnimeAV1.
- **Redibujar los iconos de origen dudoso** (deuda **B11**,
  [docs/12 §4](../docs/12-deuda-tecnica-y-roadmap.md)).

---

## Si algo se tuerce

| Síntoma | Qué hacer |
|---|---|
| Una sesión murió a mitad de fase | `/reproductor` — lee `ESTADO.md`, ve el paso a medias y `git status`, y retoma desde ahí |
| `ESTADO.md` no cuadra con el árbol | Gana el árbol. `git log --oneline` y `git status` son la verdad; `ESTADO.md` se corrige |
| Una fase salió mal entera | `git revert` de su commit, poner la fase a ⬜ en `ESTADO.md` y volver a lanzarla |
| **La fase 0 tumba mpv** | No se improvisa: se anota en *Decisiones*, se avisa al usuario y **se para**. La contingencia (VLC + proxy) cambia las fases 3 y 5, no la 1 ni la 2 |
| **Un hoster deja de resolver** | Es lo esperable: estos sitios cambian sin aviso. La app cae al navegador sola. Se arregla su resolutor, no el resto de la capa |
| **403 de Cloudflare en zilla** | Parar y esperar. **No reintentar en bucle** — la regla 6 existe por esto. MP4Upload cubre los mismos 7/7 episodios |
| Quieres saltarte una fase | `/reproductor N` de la siguiente. Deja la saltada a ⬜; la fase 6 avisará de que falta |
