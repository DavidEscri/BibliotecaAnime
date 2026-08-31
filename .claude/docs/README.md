# Documentación técnica de BibliotecaAnime

| | |
|---|---|
| **Fecha** | 2026-09-01 |
| **Commit** | rama `feature/ui-redisign`, en `4ffc2ef` (**el refresco de la banda «Retomar»**). El rediseño está **entero commiteado** (fases 1-9, de `bd25742` a `7606def`), y también los tres arreglos posteriores: el **fondo de la pantalla de carga** en `e7d8f2f`, el **hover de la lista de episodios** en `df47130` y el **refresco de la banda «Retomar»** en `4ffc2ef`, con su documentación intermedia en `f847c83` y `497128d`. ⚠️ La rama **no** se ha fusionado con `main` |
| **Árbol de trabajo** | 🟡 **Sin código pendiente**: lo único modificado es esta tanda de documentación ([02](02-mapa-de-modulos.md), [03](03-flujos-de-ejecucion.md), [06](06-gui-y-vistas.md), [07](07-concurrencia-e-hilos.md), [09](09-verificacion-y-pruebas.md), [10](10-invariantes-y-trampas.md), [12](12-deuda-tecnica-y-roadmap.md), una línea de [13](13-selector-de-proveedor.md), `CLAUDE.md` y este índice). Sin trackear siguen los 4 PNG sin usar, `.vscode/`, `.claude/settings.local.json` y `.claude/plans/` (ver [12 §1](12-deuda-tecnica-y-roadmap.md)) |
| **Última revisión** | 2026-09-01 — **refresco de la banda «Retomar»**: [03](03-flujos-de-ejecucion.md) estrena el **flujo 11** (la portada relee los episodios de lo que estás viendo al entrar) y renumera el antiguo §11 a **§12**; [10](10-invariantes-y-trampas.md) gana la trampa **38** —una fila guardada no refresca sus episodios sola—, resuelta **solo** para las ≤3 tarjetas de la portada; [09](09-verificacion-y-pruebas.md) estrena **§6c**, cómo verificar en tres tramos algo que sale a la red, escribe en la biblioteca y repinta un widget; [07](07-concurrencia-e-hilos.md) **reancla §1, §2 y §6 enteras** —de los 13 hilos que listaba, **tres ya no existían** y solo cuatro líneas eran correctas—; [12](12-deuda-tecnica-y-roadmap.md) abre **B12** y cierra **B3** y **B8**. Antes, 2026-09-01 — **hover de la lista de episodios**: [10](10-invariantes-y-trampas.md) gana la trampa **37** —un hijo sin `bind` es una salida de la que no llega ningún `<Leave>`, la complementaria de la **34**—; [09](09-verificacion-y-pruebas.md) estrena **§6b**, cómo recorrer el hover con el puntero de píxel en píxel; [02](02-mapa-de-modulos.md) estrena la **ficha de `EpisodeRow`**, que no tenía; y [06](06-gui-y-vistas.md) explica por qué `AnimeRow` no sufre lo mismo. Antes, 2026-08-31 — **fondo de la pantalla de carga**: [10](10-invariantes-y-trampas.md) gana la trampa **36** (un widget sin `fg_color` sale del gris por defecto de CustomTkinter, no de `Theme`); el arranque se reancla en [03 §1](03-flujos-de-ejecucion.md), [06](06-gui-y-vistas.md), [07 §1-§4](07-concurrencia-e-hilos.md) y [02](02-mapa-de-modulos.md) —sus anclas de `main_window.py` iban ~29 líneas desplazadas—, y [09 §7.1](09-verificacion-y-pruebas.md) gana la comprobación del fondo. Antes, 2026-08-21 — **rediseño de interfaz (fases 1-9)**: [06](06-gui-y-vistas.md) **reescrito entero**, [09 §7](09-verificacion-y-pruebas.md) también; **7 trampas nuevas** (29-35) en [10](10-invariantes-y-trampas.md); fichas de `theme.py` y de los 11 componentes en [02](02-mapa-de-modulos.md); la columna `rating` en [04 §3b](04-modelo-de-datos.md); las tres preferencias nuevas en [13 §4](13-selector-de-proveedor.md); [11](11-playbooks.md) gana §1b y **corrige §5**, que mandaba activar unos iconos que no funcionan. Antes, 2026-08-18 — **sincronización de estado**: las cabeceras de los 14 documentos dejan de decir «árbol sucio» (la tanda de licencia entró en `e337d20`; la columna `provider_id`, en `a3d4331`) y se corrige el **árbol de directorios del `README.md`**, que cerraba **C10** |
| **Último cambio** | ✅ 2026-09-01 — **la banda «Retomar» ya no miente con los animes en emisión**. La columna `episodes` de una fila solo se reescribía al abrir su ficha, así que un anime que estrena los domingos decía «Lo has visto entero» con el capítulo nuevo ya publicado. Ahora, **al entrar en «Nuevos lanzamientos»** —no al arrancar—, un hilo daemon relee los episodios de las ≤3 filas de la banda y, si el proveedor sirve más, reescribe **solo** esa columna y repinta la tarjeta. Va con `strict=True`, sin *fallback*, porque escribe sin que el usuario lo pida. ✅ Verificado en tres tramos: la red real contra los 3 animes de la banda, la escritura sobre **copia** de la BD (9 → 10 episodios: «Lo has visto entero» → «Siguiente: episodio 10 de 10», con `watched_episodes` y estados intactos) y el repintado leyendo el widget con la raíz de Tk oculta. Nace la **trampa 38** y la deuda **B12**. Antes, 2026-09-01 — **el resaltado de la lista de episodios ya no se queda pegado**. `EpisodeRow` ataba el hover a la fila y a sus dos etiquetas, pero no al interruptor ni al separador de 1 px que hay entre episodios; como `CTkFrame.bind()` ata al canvas interno —**hermano** de esos hijos, no ancestro—, salir de la fila por uno de ellos no mandaba ningún `<Leave>` y el episodio se quedaba encendido. Recorrer la lista despacio dejaba **las cinco filas resaltadas a la vez**. Ahora el hover va a los cinco hijos, el clic sigue solo en tres, y un atributo de clase garantiza que **nunca haya dos**. ✅ Medido con `SetCursorPos` de píxel en píxel: antes 5 de 5, después 1 siempre y 0 al salir. Nace la **trampa 37**. Antes, 2026-08-31 — **el arranque tiene un solo fondo**. La pantalla de carga era un `CTkFrame` sin `fg_color`, así que salía del gris por defecto de CustomTkinter: el arranque enseñaba **tres grises a la vez** y el GIF, que es transparente, heredaba el del marco. Ahora cubre la ventana entera con `Theme.BG`, se centra con `place` relativo (antes multiplicaba `winfo_width()` por 2.5, que vale 1 antes de dibujar) y el texto y la barra salen de `Theme`. ✅ Medido con captura y muestreo de píxeles en los dos temas. Nace la **trampa 36**. Antes, 2026-08-21 — **la interfaz está rediseñada de arriba abajo**: `gui/theme.py` y **11 componentes compartidos** nuevos, barra lateral plegable y persistida, las 6 vistas y la ficha rehechas, calificación personal en favoritos (columna `rating`) y estados vacíos en las 7 vistas. **+5 064 líneas**. Verificado con la app real en los dos temas y el `.exe` compilado y arrancado. Cierra el TODO de `main_window.py:32` y **5 puntos del roadmap**. Antes, 2026-08-17 — **el proyecto es formalmente GPL-3.0-or-later**: `LICENSE`, aviso de copyright, `LEEME.txt` y `THIRD-PARTY-NOTICES.txt` junto al `.exe`. El `.spec` deja de empaquetar la BD y los pósters del desarrollador y queda **verificado compilando y arrancando el `.exe`** por primera vez. Cierra **A3**, **C11** y **C10**. Publicado como **`v0.2.1`** |
| **Siguiente tarea** | **Sacar la petición de servidores del hilo de Tkinter** (`anime_window.py`): es el último sitio de la GUI que sale a la red desde el hilo de la interfaz, y el rediseño lo dejó así a propósito para no ampliar su alcance. Después, **B2** (`str` vs enum, barato y desbloquea dos puntos) → [12 §6](12-deuda-tecnica-y-roadmap.md) |
| **Cubre** | los **50 ficheros `.py`** de `src/`: **31 módulos reales** (**11 403** líneas) + 19 `__init__.py`, ✅ **todos vacíos** |

`.claude/CLAUDE.md` es el **resumen de entrada** (qué es el proyecto, comandos, arquitectura en una
página). Esta carpeta es la **profundidad**: lo que hay que saber antes de tocar algo frágil.
No se duplica contenido; se enlaza.

---

## Marcas de procedencia

Toda afirmación de comportamiento va marcada:

| Marca | Significado |
|---|---|
| ✅ | **Verificado en ejecución** en esta máquina (scripts en [09-verificacion-y-pruebas.md](09-verificacion-y-pruebas.md)). Las tandas fueron el **2026-07-28** (base), **2026-07-30** (migraciones, encoding, pósters), **2026-08-06** (JKAnime, 50/50), **2026-08-07** (auditoría) y **2026-08-16** (`provider_id`, 351/351). Cada afirmación lleva su fecha donde importa |
| 📖 | **Leído en el código**, con ancla `fichero.py:línea`, pero no ejecutado |
| ⚠️ | **Sin verificar / suposición** — trátalo como hipótesis |

---

## Índice

| Documento | Qué responde |
|---|---|
| [01-arquitectura.md](01-arquitectura.md) | Capas, quién puede importar a quién, invariantes de diseño |
| [02-mapa-de-modulos.md](02-mapa-de-modulos.md) | Ficha por módulo: API pública, dependencias, efectos secundarios |
| [03-flujos-de-ejecucion.md](03-flujos-de-ejecucion.md) | Diagramas de secuencia de los **12** flujos, con el hilo de cada paso |
| [04-modelo-de-datos.md](04-modelo-de-datos.md) | `AnimeInfo` vs `AnimeRecord`, esquema real de `ANIMES`, rangos, estados |
| [05-proveedores-y-scraping.md](05-proveedores-y-scraping.md) | Contrato, parseo de cada sitio, fallback, diagnóstico de roturas |
| [06-gui-y-vistas.md](06-gui-y-vistas.md) | `MainWindow` como hub, ciclo de vida de una vista, layout, temas |
| [07-concurrencia-e-hilos.md](07-concurrencia-e-hilos.md) | Qué corre en qué hilo, reglas y carreras conocidas |
| [08-convenciones-y-estilo.md](08-convenciones-y-estilo.md) | Cabecera obligatoria, idioma, singletons + **plantillas copiables** |
| [09-verificacion-y-pruebas.md](09-verificacion-y-pruebas.md) | Cómo arrancar y probar; scripts listos para pegar; checklist manual |
| [10-invariantes-y-trampas.md](10-invariantes-y-trampas.md) | **Lee esto siempre.** **38** trampas con síntoma observable |
| [11-playbooks.md](11-playbooks.md) | Recetas paso a paso con ficheros exactos y checklist |
| [12-deuda-tecnica-y-roadmap.md](12-deuda-tecnica-y-roadmap.md) | TODOs con `fichero:línea`, discrepancias, riesgos, roadmap técnico **y §7: licencia GPL-3.0 y cumplimiento de la distribución** |
| [13-selector-de-proveedor.md](13-selector-de-proveedor.md) | Selector de proveedor, `DB_user.db` **y la columna `provider_id`** (§14): decisiones de diseño, qué quedó fuera y **qué está verificado y qué no** |

---

## Mapa de lectura — «si vas a tocar X, lee Y»

| Vas a tocar… | Lee, en este orden |
|---|---|
| **Cualquier cosa** | [10-invariantes-y-trampas.md](10-invariantes-y-trampas.md) — 10 minutos que te ahorran un día |
| **Cualquier cosa de la interfaz** | [06](06-gui-y-vistas.md) → trampas **29-37** (todas de CustomTkinter y de layout) → [11 §1 y §1b](11-playbooks.md) |
| **Un componente compartido, o crear uno** | [06 §6](06-gui-y-vistas.md) → [11 §1b](11-playbooks.md) → [02](02-mapa-de-modulos.md) |
| **Colores, medidas o tipografía** | [06 §1](06-gui-y-vistas.md) → [`plan-rediseno/DISENO.md`](../plan-rediseno/DISENO.md), que es la especificación |
| **Abrir un anime guardado, o el proveedor de una fila** | [13 §8 y §14](13-selector-de-proveedor.md) → [04 §8](04-modelo-de-datos.md) → trampas **21, 26, 27 y 28** |
| Elegir a qué sitio pedir datos | [05 §2](05-proveedores-y-scraping.md) (tabla comparativa de los 3) → [05 §5](05-proveedores-y-scraping.md) |
| Un proveedor de anime (`APIs/`) | [05](05-proveedores-y-scraping.md) → [01](01-arquitectura.md) → trampas 11-14, 20 |
| **JKAnime en concreto** | [05 §3b](05-proveedores-y-scraping.md) → trampas **23, 24 y 25** → [02](02-mapa-de-modulos.md) |
| Añadir un proveedor nuevo | [11 §3](11-playbooks.md) → [05 §3b](05-proveedores-y-scraping.md) (el ejemplo trabajado) → [08](08-convenciones-y-estilo.md) → [09 §3d](09-verificacion-y-pruebas.md) |
| **Elegir/cambiar de proveedor, preferencias de usuario** | [13](13-selector-de-proveedor.md) → [05](05-proveedores-y-scraping.md) → [04 §3](04-modelo-de-datos.md) |
| La base de datos / un campo nuevo | [04](04-modelo-de-datos.md) → [11 §2 y §4](11-playbooks.md) → trampas 1-6 |
| Episodios vistos / estados | [04](04-modelo-de-datos.md) → [03 §4 y §5](03-flujos-de-ejecucion.md) → trampas 3-7 y **38** |
| Una vista de la sidebar | [06](06-gui-y-vistas.md) → [11 §1](11-playbooks.md) → [07](07-concurrencia-e-hilos.md) |
| La ficha de detalle (`anime_window.py`) | [06 §4 y §6](06-gui-y-vistas.md) → [03 §3](03-flujos-de-ejecucion.md) → trampas **21 y 22**, luego 7-10 |
| El buscador **de la biblioteca** (las 4 vistas de estado) | [06 §7](06-gui-y-vistas.md) → **trampa 26** |
| Hilos, `after`, congelaciones | [07](07-concurrencia-e-hilos.md) → [03](03-flujos-de-ejecucion.md) |
| **Refrescar datos guardados contra el proveedor** | **trampa 38** → [03 §11](03-flujos-de-ejecucion.md) → **B12** ([12 §4](12-deuda-tecnica-y-roadmap.md)) → trampa **27** |
| Pósters / imágenes / caché | [02 §utils.py](02-mapa-de-modulos.md) → [03 §9](03-flujos-de-ejecucion.md) → trampas 15-17 |
| **Empaquetar con PyInstaller o distribuir el `.exe`** | [11 §6](11-playbooks.md) → trampa 18 (**a, b, c, d, e**) → [12 §7](12-deuda-tecnica-y-roadmap.md) |
| **Licencia, avisos legales, dependencias nuevas** | [12 §7](12-deuda-tecnica-y-roadmap.md) → [11 §6](11-playbooks.md) |
| Iconos, tema claro/oscuro | [06 §5](06-gui-y-vistas.md) → [11 §5](11-playbooks.md) → **B11** ([12 §4](12-deuda-tecnica-y-roadmap.md)) |

---

## Reglas de oro para trabajar en este repo

1. **`resources/DB/DB_Animes.db` es la biblioteca real del usuario.** Nunca escribas en ella desde un
   script. Copia al scratchpad y parchea `get_resource_path`. Receta en
   [09-verificacion-y-pruebas.md](09-verificacion-y-pruebas.md). `DB_user.db` (preferencias) sí es
   desechable: se puede borrar y se regenera ([13 §4](13-selector-de-proveedor.md)).
2. **No hay tests, ni linter, ni formateador.** `TESTS/` está en `.gitignore` y contiene material de
   terceros: no es del proyecto. No inventes comandos de test.
3. **Se lanza como script**, no como módulo: `python src/app.py` desde la raíz. `python -m src.app`
   **no** funciona (los imports son absolutos con raíz en `src`).
4. **Sé educado con los sitios scrapeados**: pocas peticiones, en serie, con pausas.
5. Los `print` **son** el sistema de logging. No introduzcas `logging` sin acordarlo.

---

## Cómo mantener esto vivo

Esta documentación caduca. Puntos de mantenimiento concretos:

| Cuándo | Qué actualizar |
|---|---|
| Añades/quitas un módulo en `src/` | Ficha en [02](02-mapa-de-modulos.md) + diagrama en [01](01-arquitectura.md) + `hiddenimports` del `.spec` |
| Añades un miembro a `AnimeField` | Tabla de esquema en [04](04-modelo-de-datos.md) + trampa 1 + playbook [11 §2](11-playbooks.md). La migración la aplica `validate_db_integrity()`; verifícala sobre copia ([09 §3b](09-verificacion-y-pruebas.md)) |
| Añades una tabla a `AnimesPersistence.SCHEMA` | Playbook [11 §2b](11-playbooks.md) + [04 §3](04-modelo-de-datos.md) + ficha de `animesPersistence.py` en [02](02-mapa-de-modulos.md) |
| Añades una preferencia de usuario | Tabla de claves de [13 §4](13-selector-de-proveedor.md) — es una fila nueva en `USER_SETTINGS`, **no** una migración de esquema |
| Añades un proveedor | **Miembro nuevo en `AnimeProviderId`** ([04 §1b](04-modelo-de-datos.md)) + tabla comparativa en [05](05-proveedores-y-scraping.md) + registro en [01](01-arquitectura.md). El `value` es **permanente**: se persiste en la biblioteca |
| Un sitio cambia su HTML | Selectores en [05](05-proveedores-y-scraping.md) + sección de diagnóstico |
| Cambias hilos o `after` | [07](07-concurrencia-e-hilos.md) + el flujo afectado en [03](03-flujos-de-ejecucion.md) |
| Cierras un TODO | Quítalo de [12](12-deuda-tecnica-y-roadmap.md) (tiene `fichero:línea`, se desincroniza rápido) |
| **Arreglas un bug listado en [12 §4](12-deuda-tecnica-y-roadmap.md)** | Muévelo a «✅ Resuelto» **sin reutilizar su identificador**, marca su trampa en [10](10-invariantes-y-trampas.md) como resuelta **conservando el número** y el invariante que quede vivo, y actualiza el checklist de [09](09-verificacion-y-pruebas.md) para que compruebe la **no regresión** |
| **Insertas o borras líneas en un módulo muy citado** | `anime_window.py` (**1 155** líneas) y `animesPersistence.py` (**705**) acumulan ~80 citas entre todos los documentos. Reubícalas comparando el **contenido** de cada línea entre la versión vieja y la nueva, no sumando un desplazamiento a ojo: no es uniforme, y las citas cortas (`:205`) se escapan de cualquier búsqueda por nombre de fichero |

**Al revisar**: relee las cabeceras de metadatos. Si el commit que citan es muy anterior al `HEAD`
actual, asume que las líneas citadas se han desplazado y reverifica antes de fiarte de un número
de línea concreto.

**Regla de oro de esta carpeta**: si no lo has leído o ejecutado, va con ⚠️. Un documento sin
ningún ⚠️ es sospechoso — significa que quien lo escribió no miró sus propios límites.
