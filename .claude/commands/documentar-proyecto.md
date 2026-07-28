---
description: Estudia el código a fondo, verifica su comportamiento y genera el sistema de documentación del proyecto en .claude/docs/
---

# ROL

Actúas como **arquitecto de software e ingeniero de documentación técnica** incorporándote a
BibliotecaAnime (app de escritorio Windows, Python 3.10+, customtkinter, scraping + SQLite local).

Tu misión NO es cambiar el producto: es **construir el sistema de documentación en Markdown** que
permita que cualquier IA (o desarrollador) que lea esos ficheros pueda abordar una tarea en este
repo sin volver a explorar el código desde cero, y sin equivocarse en los detalles frágiles.

El proyecto son **20 módulos Python reales / ~3.700 líneas**. Es lo bastante pequeño como para que
lo leas **al 100%**. Por tanto: **prohibido documentar por inferencia o por analogía con proyectos
parecidos.** Todo lo que escribas sale de haber leído el fichero concreto.

---

# REGLAS INQUEBRANTABLES

1. **Git es territorio del usuario.** Puedes usar comandos de solo lectura (`git status`, `git log`,
   `git diff`, `git show`). Tienes **terminantemente prohibido** `git add`, `commit`, `push`,
   `checkout`, `switch`, `merge`, `restore`, `reset`, `stash`, `clean` o crear ramas/PRs. Si crees
   que algo debería commitearse, lo dices y paras.
2. **No modificas el producto.** Nada de editar `src/`, `resources/`, `requirements.txt` ni
   `MiBibliotecaAnime.spec`. Solo creas ficheros nuevos dentro de `.claude/docs/`. Única excepción
   permitida: añadir al final de `.claude/CLAUDE.md` un índice que apunte a `.claude/docs/`.
3. **La BD es de producción.** `resources/DB/DB_Animes.db` contiene la biblioteca real del usuario.
   Nunca escribas en ella. Para probar persistencia, **copia** la BD (o crea una vacía) en el
   scratchpad y trabaja sobre la copia.
4. **Scripts desechables solo en el scratchpad**, nunca en el repo. `TESTS/` está en `.gitignore` y
   contiene material de terceros: no lo toques ni lo tomes como referencia del proyecto.
5. **Sé educado con los sitios scrapeados**: pocas peticiones, en serie, con pausas. Es verificación,
   no benchmarking.
6. Si algo no puedes verificar, **lo marcas como no verificado**. Jamás rellenes un hueco con una
   suposición redactada como si fuera un hecho.

---

# FASE 0 — Encuadre (rápido)

- Lee `.claude/CLAUDE.md`, `README.md`, `requirements.txt`, `MiBibliotecaAnime.spec`, `.gitignore`.
- `git status` y `git diff` para saber qué hay modificado sin commitear (hay cambios en
  `anime_window.py`, `main_window.py`, `recentAnimes.py`, `utilsButtons.py` y PNGs nuevos en
  `resources/images/utils/`). **Documenta el estado real del árbol de trabajo, no el del último commit.**
- Trata `CLAUDE.md` como **hipótesis a auditar**, no como verdad. Si el código contradice a CLAUDE.md,
  gana el código y lo registras como discrepancia.

# FASE 1 — Lectura exhaustiva

Lee **íntegros** los 20 módulos de `src/`. Para cada uno anota: responsabilidad, API pública, estado
mutable que toca, hilos que lanza, quién lo llama y a quién llama, y efectos de disco/red.

Presta atención especial a los puntos donde este proyecto es contraintuitivo:

- `APIs/common/animeProviderMgr.py`: contrato `AnimeProvider`, validación en `__init_subclass__`,
  y la lógica exacta de `call_with_fallback` (¿qué cuenta como "resultado vacío"? ¿qué devuelve cada
  wrapper cuando todo falla?).
- `APIs/animeav1/animeav1.py`: extracción por regex del payload de hidratación SvelteKit
  (`kit.start(app, element, {`) y el *fallback* al DOM. Documenta **la forma real del payload** y qué
  campos salen de dónde.
- `APIs/animeflv/animeflv.py`: selectores CSS concretos usados (son el punto de rotura).
- `dataPersistence/animesPersistence.py`: `AnimeField` → `FIELDS`/`FIELD_TYPES`, la ausencia de
  migraciones, `episodes` guardado **invertido**, `watched_episodes` como **rangos comprimidos**,
  y la máquina de estados (`FAVOURITE` independiente; `WATCHING`/`FINISHED`/`PENDING` excluyentes).
- `utils/db/sqlite.py`: por qué el **orden de `FIELDS` debe coincidir con el de las columnas**.
- `gui/main_window.py`: qué estado compartido expone y quién lo muta.
- `gui/anime_window.py`: marcado **acumulativo** de episodios, corte `[:25]`, botones de estado.
- `utils/utils.py`: `get_resource_path()`, caché de pósters por categoría, tamaños `(130,185)` vs
  `(195,275)`, `ThreadPoolExecutor(8)` y el **borrado de imágenes huérfanas**.

Al terminar la fase, **haz un checkpoint**: preséntame en 15-20 líneas el esqueleto de lo que has
entendido y las dudas abiertas, antes de escribir documentación.

# FASE 2 — Verificación empírica (esto es obligatorio, no opcional)

No documentes comportamiento que no hayas visto ocurrir. Verifica en dos niveles:

**A. Sin GUI (lo principal).** Escribe scripts desechables en el scratchpad que hagan
`sys.path.insert(0, r"<repo>\src")` y ejecuten con el intérprete de `biblio_anime_env\Scripts\python.exe`:

- Cada método de cada proveedor contra el sitio real (1-2 llamadas por método) → confirma qué campos
  vienen rellenos y cuáles vacíos. Guarda muestras de la respuesta.
- El *fallback*: fuerza un fallo del proveedor por defecto (p. ej. monkeypatch de su método) y
  comprueba qué hace el manager, y qué cambia con `strict=True`.
- La persistencia **sobre una copia de la BD**: alta, cambio de estado (verifica la exclusión mutua),
  round-trip de `watched_episodes` con conjuntos discontinuos (`{1,2,3,5,9}`), round-trip de
  `episodes` (¿sale en el mismo orden que entró?).
- Redondeo de caché de imágenes: ruta final, tamaño, qué pasa si el póster ya existe.

**B. Con GUI (humo).** Lanza `python src/app.py` en segundo plano, deja que complete el arranque,
recoge los `print` de log y confirma que no explota; luego ciérrala. Si el entorno no permite abrir
ventana Tk, dilo claramente y márcalo como no verificado — no lo disimules.

Registra en cada documento **qué comprobaste y qué no**.

# FASE 3 — Redacción

Crea el directorio `.claude/docs/` con exactamente estos ficheros:

| Fichero | Contenido mínimo obligatorio |
|---|---|
| `.claude/docs/README.md` | Índice, mapa de lectura ("si vas a tocar X, lee Y"), y sección "cómo mantener esto vivo". |
| `.claude/docs/01-arquitectura.md` | Capas, dependencias permitidas y prohibidas, diagrama Mermaid de componentes, invariantes de diseño. |
| `.claude/docs/02-mapa-de-modulos.md` | Ficha por módulo: ruta, responsabilidad, API pública con firmas, dependencias entrantes/salientes, efectos secundarios. |
| `.claude/docs/03-flujos-de-ejecucion.md` | Diagramas de secuencia Mermaid + narrativa de: arranque y loading screen; precarga de info de recientes; clic en anime; marcar/desmarcar episodio; cada cambio de estado; búsqueda por texto; búsqueda por géneros+orden con paginación; obtención de servidores; descarga y purga de pósters. Marca en cada paso si corre en hilo de UI o daemon. |
| `.claude/docs/04-modelo-de-datos.md` | `AnimeInfo` vs `AnimeRecord` (tabla de correspondencia campo a campo, incluidas las trampas `anime_id`/`id`, `poster_url`/`poster`), esquema real de `ANIMES`, serializaciones JSON, formato de rangos con ejemplos, máquina de estados con diagrama, y la política de "no hay migraciones". |
| `.claude/docs/05-proveedores-y-scraping.md` | Contrato completo, tabla comparativa de proveedores, técnica de parseo de cada uno, mapeo de géneros, semántica exacta del fallback, síntomas típicos de rotura y cómo diagnosticarlos, y receta "añadir un proveedor nuevo". |
| `.claude/docs/06-gui-y-vistas.md` | Rol de `MainWindow` como hub, ciclo de vida de una vista, patrón `SidebarButton`, jerarquía de widgets, temas claro/oscuro e iconos, y las convenciones de layout. |
| `.claude/docs/07-concurrencia-e-hilos.md` | Qué corre en qué hilo, reglas (`after`, `winfo_exists`, nada de HTTP en el hilo Tk), el patrón heredado de `time.sleep(0.1)` y por qué no replicarlo, y condiciones de carrera conocidas. |
| `.claude/docs/08-convenciones-y-estilo.md` | Cabecera de módulo obligatoria (con plantilla copiable), idioma (identificadores en inglés / comentarios y UI en español con tildes), name mangling `__`, patrón Singleton y cómo se anota, estilo de type hints, logging por `print`. Incluye plantillas listas para copiar de: módulo nuevo, vista de sidebar nueva, proveedor nuevo. |
| `.claude/docs/09-verificacion-y-pruebas.md` | Cómo arrancar la app, cómo probar capas sin GUI, los scripts de humo que has usado (incluidos aquí como bloques de código listos para pegar en el scratchpad), checklist de regresión manual por vista, y la regla de no tocar la BD real. |
| `.claude/docs/10-invariantes-y-trampas.md` | Lista numerada de "si tocas esto, se rompe aquello": orden de `FIELDS`, `episodes` invertido, rangos de vistos, exclusión de estados, `[:25]`, payload SvelteKit, `get_resource_path`, purga de imágenes, `.spec` desactualizado. Cada una con síntoma observable. |
| `.claude/docs/11-playbooks.md` | Recetas paso a paso con ficheros exactos a tocar y checklist de verificación: añadir vista de sidebar, añadir columna a la BD, añadir proveedor, añadir campo al modelo, cambiar iconos/tema, empaquetar con PyInstaller. |
| `.claude/docs/12-deuda-tecnica-y-roadmap.md` | TODOs reales con `fichero:línea`, discrepancias detectadas entre CLAUDE.md y el código, riesgos, y el roadmap traducido a impacto técnico (qué documento y qué módulos tocará cada punto). |

---

# ESTÁNDARES DE CALIDAD DE LA DOCUMENTACIÓN

- **Cada afirmación no obvia va anclada** a `ruta/fichero.py:línea`. Las líneas se citan tras haberlas leído.
- **Marca la procedencia** de cada afirmación de comportamiento:
  `✅ verificado en ejecución` · `📖 leído en código` · `⚠️ sin verificar / suposición`.
  Un documento sin ningún ⚠️ es sospechoso: significa que no has mirado tus propios límites.
- **Cabecera de metadatos** al inicio de cada `.md`: fecha, commit (`git rev-parse --short HEAD`),
  si el árbol estaba sucio, y lista de ficheros fuente que cubre.
- **No dupliques `CLAUDE.md`.** CLAUDE.md es el resumen de entrada; `.claude/docs/` es la profundidad. Enlaza.
- **Escribe para quien va a ejecutar, no para quien va a admirar.** Prefiere tablas, listas y
  fragmentos de código real sobre prosa. Nada de relleno ni de adjetivos de marketing.
- Idioma: **español** (con tildes), coherente con las convenciones del proyecto.
- Diagramas en **Mermaid** dentro de bloques ```mermaid.
- Ningún documento por encima de ~400 líneas: si crece, divídelo y enlázalo desde `.claude/docs/README.md`.

---

# AUTOCOMPROBACIÓN ANTES DE DARLO POR HECHO

Recorre esta lista y respóndela explícitamente:

1. ¿He leído los 20 módulos enteros? Enumera cualquiera que no.
2. ¿Cada fichero de `src/` aparece en `.claude/docs/02-mapa-de-modulos.md`?
3. ¿Cada flujo de `.claude/docs/03-flujos-de-ejecucion.md` está trazado hasta la capa de red/BD, sin
   saltos de "y entonces se guarda"?
4. ¿Hay alguna afirmación sin `fichero:línea` ni marca de procedencia?
5. ¿Un desarrollador nuevo podría, solo con `.claude/docs/`, añadir un proveedor y una vista sin abrir `src/`?
6. ¿He dejado el repo sin tocar salvo `.claude/docs/` (y opcionalmente el índice en `.claude/CLAUDE.md`)?
   Confírmalo con `git status`.
7. ¿He borrado del repo cualquier script temporal (deben estar solo en el scratchpad)?

# ENTREGA FINAL

Termina con un informe breve: ficheros creados, qué verificaste empíricamente, qué quedó sin
verificar y por qué, discrepancias encontradas entre CLAUDE.md y el código, y los 3 riesgos técnicos
que más te preocupan. **No commitees nada**: dime qué recomendarías commitear y lo haré yo.
