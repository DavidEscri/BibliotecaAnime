# Cómo pedirme tareas en BibliotecaAnime

Guía práctica para que una petición salga bien a la primera. **No es prompt engineering genérico**:
está calibrada sobre lo que este repo tiene de particular (sin tests, BD de producción en el árbol,
scraping que se rompe solo, GUI sin router).

> **No es obligatorio seguirla.** `.claude/CLAUDE.md` lleva un protocolo que normaliza cualquier
> petición contra esta guía automáticamente — ver [§13](#13--qué-hago-yo-con-tu-petición-no-tienes-que-escribir-bien).
> Esto sirve para **acotar** cuando quieras control fino, no para rellenar formularios.

Índice: [Contrato por defecto](#1--el-contrato-por-defecto) · [Refactorizar](#3--refactorizar) ·
[Nueva funcionalidad](#4--nueva-funcionalidad) · [Bugs](#5--buscarreparar-bugs) ·
[Investigar](#6--investigarentender) · [Documentar](#7--documentar) ·
[Release](#8--empaquetarrelease) · [Palancas de control](#9--palancas-de-control) ·
[Errores frecuentes](#11--errores-frecuentes-al-pedir) ·
[Qué hago automáticamente](#13--qué-hago-yo-con-tu-petición-no-tienes-que-escribir-bien)

---

## 1 · El contrato por defecto

Esto lo asumo **siempre**, sin que lo digas. Solo tienes que escribir algo si quieres **cambiarlo**.

| Asumo | Cómo desactivarlo |
|---|---|
| **Git es tuyo.** Leo (`status`, `log`, `diff`, `show`) pero no hago `commit`, `push`, `checkout`, `merge`, `reset`… Al terminar te digo qué commitear. | «commitea tú», «haz el commit y el push» |
| **`resources/DB/DB_Animes.db` es tu biblioteca real.** Nunca escribo en ella; si necesito probar persistencia, copio al scratchpad y parcheo `get_resource_path`. | «puedes usar la BD real, tengo copia» |
| **Los scripts desechables van al scratchpad**, nunca al repo. | — |
| **Soy educado con los sitios scrapeados**: pocas peticiones, en serie, con pausas. | «tira lo que haga falta, es mi propio servidor» |
| **Leo antes de escribir.** Si toco un módulo, lo leo entero primero. | — |
| **Marco lo que no he verificado.** Si no lo he ejecutado, lo digo. | — |
| **Consulto `.claude/docs/`** antes de tocar zonas frágiles. | — |

**Lo que NO hago si no lo pides**: lanzar subagentes, arreglar bugs colaterales que encuentre de
paso (te los reporto), reformatear código que no toco, o añadir tests (no hay suite).

---

## 2 · La plantilla mínima

Para tareas de código, cuatro líneas bastan:

```
QUÉ:        <el cambio concreto>
DÓNDE:      <fichero/módulo, si lo sabes; si no, dilo y lo busco>
ALCANCE:    <hasta dónde puedo tocar / qué NO tocar>
VERIFICAR:  <ejecutar la GUI / script sin GUI / solo leer / nada>
```

Ejemplo real y suficiente:

> **QUÉ**: que el póster de la ficha se vea a 195×275 también cuando hay que descargarlo.
> **DÓNDE**: `utils.py:176-177`, es la trampa 16.
> **ALCANCE**: solo esa función, no toques la caché.
> **VERIFICAR**: con script sin GUI; la GUI la abro yo.

---

## 3 · Refactorizar

### Qué incluir

| Campo | Por qué importa **aquí** |
|---|---|
| **Objetivo** | «que se lea mejor» ≠ «que deje de congelar la UI» ≠ «que no se repita». Cambian el resultado por completo |
| **Radio de acción** | «solo este método», «este fichero», «las 4 vistas de estado». Las vistas son casi idénticas: si no lo dices, no sé si quieres tocar una o las cuatro |
| **Compatibilidad de datos** | Si el refactor roza `AnimeField`, `AnimeRecord` o la serialización, dime si puede cambiar el formato en BD o tiene que seguir leyendo lo ya guardado |
| **Verificación** | Sin tests, la única red de seguridad es ejecutar. Dime si quieres que verifique o si prefieres hacerlo tú |

### Plantilla

```
Refactoriza <X> para <objetivo>.
Radio: solo <ficheros>. No toques <lo demás>.
El formato en BD [puede cambiar / NO puede cambiar].
Verifica con [script sin GUI / GUI / no hace falta].
```

### Ejemplos

✅ **Bien**
> Extrae la paginación de `searchAnimes.py:267-324` a `utilsButtons.py` como widget reutilizable,
> porque la quiero usar también en favoritos. Radio: esos dos ficheros. No cambies el comportamiento
> visible. Verifícalo abriendo el buscador.

❌ **Flojo**
> Limpia el código del buscador.
>
> *(¿limpiar qué? ¿el guard roto de hilos, la duplicación con las vistas de estado, los nombres,
> el layout? Acabaré preguntando o eligiendo por ti.)*

### Trampas que te conviene mencionar

- Si refactorizas **las 4 vistas de estado**, son casi idénticas línea por línea: di si quieres
  factorizar una base común o mantenerlas separadas. Es una decisión de diseño, no técnica.
- Si tocas los `time.sleep(0.1)` (hay 7): **no los quites todos de golpe**. Están ahí por el cálculo
  de columnas. Pídeme uno, verifícalo, y seguimos.
- `.claude/docs/` se desincroniza al refactorizar. Dime si quieres que actualice los documentos
  afectados en el mismo trabajo (te diré cuáles son).

---

## 4 · Nueva funcionalidad

### Qué incluir

| Campo | Por qué |
|---|---|
| **Comportamiento observable** | Qué ve o hace el usuario. Es lo que menos ambigüedad deja |
| **¿Persiste?** | Si hay que guardar algo, **es el dato más importante de la petición**: implica columna nueva y tocar `AnimeRecord`. La migración de la BD ya es automática ([11 §2](docs/11-playbooks.md)), pero se prueba sobre una copia de tu BD |
| **Dónde vive en la UI** | Vista nueva de sidebar, ficha de detalle, o dentro de una vista existente |
| **Alcance del roadmap** | Si es un paso hacia la convivencia anime/manga, dímelo: cambia si generalizo los modelos o no |
| **Hasta dónde llego** | ¿Diseño y espero tu OK, o implemento del tirón? |

### Plantilla

```
Quiero <comportamiento observable>.
Vive en <vista / ficha / sidebar nueva>.
[Persiste en BD: sí — <qué campo> / no]
[Es un paso hacia <punto del roadmap> / es independiente]
[Diséñalo primero y espera mi OK / impleméntalo entero]
```

### Ejemplos

✅ **Bien**
> En «viendo», que cada anime muestre debajo del título «Cap. 340 de 1171». El dato ya está en BD
> (`last_watched_episode` y `episodes`), así que **no hace falta migrar nada**. Solo
> `watchingAnimes.py`. Impleméntalo entero y luego lo pruebo yo.

✅ **Bien (grande, con freno)**
> Quiero calificación personal de 1 a 5 en favoritos, guardada y con ordenación por ella. Sé que
> implica columna nueva en `AnimeField` y que la migración se aplica sola al arrancar.
> **Diseña primero** el plan y espera mi OK antes de tocar `src/`.

❌ **Flojo**
> Añade puntuaciones a los animes.
>
> *(¿del sitio o del usuario? ¿se guardan? ¿dónde se ven? ¿se puede ordenar? Cuatro preguntas.)*

### Regla de oro

**Si la funcionalidad guarda algo, dilo en la primera frase.** Es la diferencia entre 20 minutos y
una sesión con cambios de esquema y pruebas sobre copia de tu BD.

---

## 5 · Buscar/reparar bugs

Aquí lo valioso es **el síntoma**, no tu diagnóstico. Si me das el diagnóstico, tiendo a confirmarlo
en vez de cuestionarlo.

### Qué incluir

| Campo | Ejemplo |
|---|---|
| **Qué viste** | «el póster sale como un cuadradito diminuto» |
| **Qué esperabas** | «debería verse grande, como en los demás animes» |
| **Cuándo pasa** | «solo en los animes que tengo en “viendo”» ← **esto es lo que resuelve el caso** |
| **Reproducible** | siempre / a veces / una sola vez |
| **Consola** | pega los `print`, aunque parezcan ruido. Son el único log que hay |
| **Tu hipótesis** | opcional, y márcala como hipótesis |

### Plantilla

```
BUG: <qué viste>
Esperaba: <qué debería pasar>
Pasa cuando: <condición>
Reproducible: <sí/no/a veces>
Consola: <pega la salida>
[Sospecho de <X>, pero no estoy seguro]
```

### Ejemplo

✅ **Bien**
> Marco los episodios 1-10 de un anime que acabo de encontrar, salgo, vuelvo, y están todos
> apagados. Con los de mi lista de favoritos no pasa. Consola limpia, sin errores.
>
> *(Esto es la trampa 7 y lo identifico en un minuto: el anime no está en BD, así que
> `update_watched_episodes` devuelve `False` en silencio.)*

❌ **Flojo**
> Los episodios vistos no se guardan bien, arréglalo.

### Dos modos, dilo cuál quieres

| Petición | Qué hago |
|---|---|
| «**diagnostica**, no arregles» | Investigo, te explico la causa con `fichero:línea`, y paro |
| «diagnostica **y arregla**» | Además aplico el cambio mínimo y te digo cómo verificarlo |

Por defecto hago lo segundo. Si el arreglo resulta ser grande o arriesgado, paro y te lo cuento
antes de tocar nada.

### Bugs ya conocidos

Antes de reportar, un vistazo a [`docs/10-invariantes-y-trampas.md`](docs/10-invariantes-y-trampas.md)
te ahorra tiempo: hay 25 trampas documentadas con su síntoma observable. Si tu síntoma está ahí,
basta con **«arregla la trampa N»**.

---

## 6 · Investigar/entender

Cuando no quieres cambios, solo respuestas. **Dilo explícitamente** o asumiré que quieres el arreglo.

```
Solo explícame: <pregunta>. No cambies nada.
```

Ejemplos que funcionan bien:

> Explícame por qué el orden de los episodios sale al revés entre AnimeAV1 y AnimeFLV, y qué
> consecuencias tiene. No toques código.

> ¿Qué pasa exactamente si añado una columna en medio de `AnimeField`, en mi BD que ya tiene
> 24 animes? Solo dime.

> Enséñame todo lo que corre fuera del hilo de Tkinter y cuál me puede dar problemas.

---

## 7 · Documentar

Existe el comando **`/documentar-proyecto`**, que hace el trabajo completo (leer todo, verificar
empíricamente, regenerar `.claude/docs/`). Es caro. Para retoques, pide directo:

```
Actualiza docs/<fichero> porque <qué cambió>.
```

> Acabo de cambiar `get_anime_image`. Actualiza la trampa 15 y 16 de `docs/10` y la ficha de
> `utils.py` en `docs/02`.

Si haces un cambio de código y quieres que la documentación acompañe, **dilo en la misma petición**:
«… y actualiza los documentos que queden desfasados».

---

## 8 · Empaquetar/release

🚧 El `hiddenimports` del `.spec` se corrigió el 2026-08-06, pero **leyendo los `import`, sin
compilar nunca**. Al pedir un empaquetado, dime:

- **Qué hacer con `('resources/DB', 'resources/DB')`**: tal cual, tu biblioteca personal viaja
  dentro del `.exe`. Es el problema serio que queda.
- La `APP_VERSION` nueva.
- Si quieres que además quite `gui.sidebarButtons.sidebarButton`, que sigue declarado y no existe.

Asumiré que el primer empaquetado hay que **verificarlo arrancando el `.exe`**, no solo compilarlo.

Receta completa con checklist: [`docs/11 §6`](docs/11-playbooks.md).

---

## 9 · Palancas de control

Frases cortas que cambian mi comportamiento de forma fiable:

| Frase | Efecto |
|---|---|
| «**no toques `X`**» | Lo respeto literalmente, aunque crea que el arreglo está ahí. Te lo diré, pero no lo tocaré |
| «**ignora `X`**» | Dejo de investigar por ahí. *(Funcionó perfectamente cuando me dijiste que AnimeFLV está caído)* |
| «**solo dime, no cambies**» | Investigo y reporto, cero ediciones |
| «**diseña primero y espera mi OK**» | Te presento el plan antes de tocar `src/` |
| «**verifica ejecutándolo**» | Escribo scripts en el scratchpad y los corro contra el código real |
| «**no hace falta verificar**» | Entrego el cambio leído, marcándolo como no verificado |
| «**mínimo cambio**» | Nada de mejoras de paso, ni renombrados, ni reordenar imports |
| «**hazlo entero**» | No paro a preguntar detalles menores; asumo y te digo qué asumí |
| «**esto es de producción**» | Máxima cautela: copias, verificación previa, y paro ante lo irreversible |

---

## 10 · Comandos útiles en este repo

| Comando | Para qué |
|---|---|
| `/documentar-proyecto` | Regenera `.claude/docs/` entero, con verificación empírica |
| `/code-review` | Revisa tu diff actual (lo lanzas tú, no yo) |
| `/security-review` | Revisión de seguridad de los cambios pendientes |
| `/simplify` | Limpieza de calidad sobre lo ya cambiado — no busca bugs |
| `! <comando>` | Ejecuta algo en tu shell y la salida entra en la conversación. Útil para pegarme un traceback: `! biblio_anime_env\Scripts\python.exe src/app.py` |

---

## 11 · Errores frecuentes al pedir

| Lo que escribes | Qué falla | Mejor |
|---|---|---|
| «arregla el buscador» | Hay 4 problemas distintos ahí; elegiré uno | «arregla el guard de hilos de `searchAnimes.py`, que `.start()` devuelve `None`» |
| Pegarme 200 líneas de código | Ya lo leo yo, y me quitas contexto útil | Dame la ruta: `searchAnimes.py:205` |
| «haz que funcione como antes» | No sé cómo era antes | Descríbeme el comportamiento, o dime el commit |
| «añade un campo X» sin decir si persiste | Es la diferencia entre 5 minutos y un cambio de esquema | Dilo en la primera frase |
| «mejora el rendimiento» | Nada está medido; optimizaría a ciegas | «el arranque tarda ~15 s por la precarga de recientes, ¿se puede paralelizar?» |
| «revisa todo el proyecto» | Sin foco, el resultado es una lista genérica | «revisa la capa de persistencia buscando pérdidas de datos» |
| Pedir tests | No hay suite y `TESTS/` es material de terceros | «verifícalo con un script en el scratchpad» |

---

## 12 · Cómo corregirme a mitad

- **Interrúmpeme en cuanto veas que voy mal.** Cuanto antes, menos trabajo tirado.
- Una frase basta: «no, eso no; céntrate en `X`». No necesitas justificarlo.
- Si te doy un resultado que no cuadra con lo que ves en tu máquina, **dímelo con lo que ves**. Tu
  observación gana sobre mi lectura del código.
- Si repito un error, dímelo y lo guardo en memoria para las próximas sesiones.

---

## 13 · Qué hago yo con tu petición (no tienes que escribir bien)

Esta guía es para **afinar**, no un requisito. `.claude/CLAUDE.md` incluye un **protocolo de
recepción** que se aplica a toda petición automáticamente: cojo lo que escribas, por suelto que sea,
y lo normalizo internamente contra esta guía y contra `.claude/docs/` antes de actuar.

En concreto resuelvo siempre: tipo de tarea · **¿persiste algo?** (el que más cambia el trabajo) ·
ficheros y frontera de alcance · ¿es una [trampa conocida](docs/10-invariantes-y-trampas.md)? ·
nivel de verificación · diagnosticar vs. arreglar · si la documentación queda desfasada.

**Cuánto verás de eso:**

| Tu petición | Qué hago |
|---|---|
| Clara y de bajo riesgo | La normalizo **en silencio** y la ejecuto. No te muestro el análisis |
| Ambigua, amplia o de riesgo medio | Abro con un **«Entiendo que»** de ≤6 líneas y **sigo sin esperarte**. Si me equivoqué, me paras |
| Escribe en tu BD, borra datos, toca git, o el alcance cambia del todo según tu respuesta | Te presento el encuadre y **espero tu OK** |

Ante una duda menor **asumo y declaro el supuesto**; no te interrogo. Solo te bloqueo si avanzar a
ciegas fuese inseguro o dejase el trabajo inservible.

> Consecuencia práctica: **«el póster de la ficha se ve diminuto, arréglalo»** es una petición
> perfectamente válida. Las plantillas de arriba sirven para cuando quieras **acotar** (radio de
> acción, nivel de verificación, diseñar antes de tocar), no para que tengas que rellenarlas.

---

## 14 · Tres peticiones modelo

**Bug**
> El buscador a veces muestra resultados duplicados o mezclados si pulso «Buscar» dos veces rápido.
> Consola limpia. Diagnostica y arregla si es pequeño; si es grande, cuéntamelo antes.

**Funcionalidad pequeña**
> En la ficha de detalle, muestra «Episodio 340 de 1171» junto al título de la lista de episodios.
> El dato está en BD, no persiste nada nuevo. Solo `anime_window.py`. Hazlo entero.

**Cambio arriesgado**
> Quiero añadir `user_rating` a la BD. Mi BD tiene 24 animes reales, así que verifica la migración
> sobre una copia antes de nada. Diseña el plan completo y espera mi OK antes de tocar `src/`.
