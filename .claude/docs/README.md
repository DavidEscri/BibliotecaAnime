# Documentación técnica de BibliotecaAnime

| | |
|---|---|
| **Fecha** | 2026-08-07 |
| **Commit** | `18311e3` |
| **Árbol de trabajo** | ✅ **limpio**. Sin trackear solo quedan 4 PNG sin usar, `.vscode/` y `.claude/settings.local.json` (ver [12 §1](12-deuda-tecnica-y-roadmap.md)) |
| **Última revisión** | 2026-08-07 — **auditoría completa** contra el código: ~55 anclas `fichero:línea` reubicadas, inventario de TODOs corregido (**3**, no 5), trampas **18a** y **19** cerradas, y las cabeceras de los 12 documentos puestas al día |
| **Último cambio** | ✅ 2026-08-06/07 — **JKAnime como tercer proveedor**, registrado entre AnimeAV1 y AnimeFLV. 50/50 comprobaciones sobre el sitio real. Cierra el punto 1 del roadmap y mitiga **R2** |
| **Siguiente tarea** | 🔴 **Columna `provider_id` en `ANIMES`** → **[13 §8](13-selector-de-proveedor.md)**. Su requisito previo (un segundo proveedor sano) ya se cumple |
| **Cubre** | los **37 ficheros `.py`** de `src/`: **19 módulos reales** + 18 `__init__.py`, ✅ **los 18 vacíos** desde `e6d1a73` |

`.claude/CLAUDE.md` es el **resumen de entrada** (qué es el proyecto, comandos, arquitectura en una
página). Esta carpeta es la **profundidad**: lo que hay que saber antes de tocar algo frágil.
No se duplica contenido; se enlaza.

---

## Marcas de procedencia

Toda afirmación de comportamiento va marcada:

| Marca | Significado |
|---|---|
| ✅ | **Verificado en ejecución** en esta máquina (scripts en [09-verificacion-y-pruebas.md](09-verificacion-y-pruebas.md)). Las tandas fueron el **2026-07-28** (base), **2026-07-30** (migraciones, encoding, pósters), **2026-08-06** (JKAnime, 50/50) y **2026-08-07** (auditoría). Cada afirmación lleva su fecha donde importa |
| 📖 | **Leído en el código**, con ancla `fichero.py:línea`, pero no ejecutado |
| ⚠️ | **Sin verificar / suposición** — trátalo como hipótesis |

---

## Índice

| Documento | Qué responde |
|---|---|
| [01-arquitectura.md](01-arquitectura.md) | Capas, quién puede importar a quién, invariantes de diseño |
| [02-mapa-de-modulos.md](02-mapa-de-modulos.md) | Ficha por módulo: API pública, dependencias, efectos secundarios |
| [03-flujos-de-ejecucion.md](03-flujos-de-ejecucion.md) | Diagramas de secuencia de los 10 flujos, con el hilo de cada paso |
| [04-modelo-de-datos.md](04-modelo-de-datos.md) | `AnimeInfo` vs `AnimeRecord`, esquema real de `ANIMES`, rangos, estados |
| [05-proveedores-y-scraping.md](05-proveedores-y-scraping.md) | Contrato, parseo de cada sitio, fallback, diagnóstico de roturas |
| [06-gui-y-vistas.md](06-gui-y-vistas.md) | `MainWindow` como hub, ciclo de vida de una vista, layout, temas |
| [07-concurrencia-e-hilos.md](07-concurrencia-e-hilos.md) | Qué corre en qué hilo, reglas y carreras conocidas |
| [08-convenciones-y-estilo.md](08-convenciones-y-estilo.md) | Cabecera obligatoria, idioma, singletons + **plantillas copiables** |
| [09-verificacion-y-pruebas.md](09-verificacion-y-pruebas.md) | Cómo arrancar y probar; scripts listos para pegar; checklist manual |
| [10-invariantes-y-trampas.md](10-invariantes-y-trampas.md) | **Lee esto siempre.** 25 trampas con síntoma observable |
| [11-playbooks.md](11-playbooks.md) | Recetas paso a paso con ficheros exactos y checklist |
| [12-deuda-tecnica-y-roadmap.md](12-deuda-tecnica-y-roadmap.md) | TODOs con `fichero:línea`, discrepancias, riesgos, roadmap técnico |
| [13-selector-de-proveedor.md](13-selector-de-proveedor.md) | Selector de proveedor y `DB_user.db`: decisiones de diseño, qué quedó fuera y **qué está verificado y qué no** |

---

## Mapa de lectura — «si vas a tocar X, lee Y»

| Vas a tocar… | Lee, en este orden |
|---|---|
| **Cualquier cosa** | [10-invariantes-y-trampas.md](10-invariantes-y-trampas.md) — 10 minutos que te ahorran un día |
| Elegir a qué sitio pedir datos | [05 §2](05-proveedores-y-scraping.md) (tabla comparativa de los 3) → [05 §5](05-proveedores-y-scraping.md) |
| Un proveedor de anime (`APIs/`) | [05](05-proveedores-y-scraping.md) → [01](01-arquitectura.md) → trampas 11-14, 20 |
| **JKAnime en concreto** | [05 §3b](05-proveedores-y-scraping.md) → trampas **23, 24 y 25** → [02](02-mapa-de-modulos.md) |
| Añadir un proveedor nuevo | [11 §3](11-playbooks.md) → [05 §3b](05-proveedores-y-scraping.md) (el ejemplo trabajado) → [08](08-convenciones-y-estilo.md) → [09 §3d](09-verificacion-y-pruebas.md) |
| **Elegir/cambiar de proveedor, preferencias de usuario** | [13](13-selector-de-proveedor.md) → [05](05-proveedores-y-scraping.md) → [04 §3](04-modelo-de-datos.md) |
| La base de datos / un campo nuevo | [04](04-modelo-de-datos.md) → [11 §2 y §4](11-playbooks.md) → trampas 1-6 |
| Episodios vistos / estados | [04](04-modelo-de-datos.md) → [03 §4 y §5](03-flujos-de-ejecucion.md) → trampas 3-7 |
| Una vista de la sidebar | [06](06-gui-y-vistas.md) → [11 §1](11-playbooks.md) → [07](07-concurrencia-e-hilos.md) |
| La ficha de detalle (`anime_window.py`) | [06](06-gui-y-vistas.md) → [03 §3-§5](03-flujos-de-ejecucion.md) → trampas 7-10 |
| Hilos, `after`, congelaciones | [07](07-concurrencia-e-hilos.md) → [03](03-flujos-de-ejecucion.md) |
| Pósters / imágenes / caché | [02 §utils.py](02-mapa-de-modulos.md) → [03 §9](03-flujos-de-ejecucion.md) → trampas 15-17 |
| Empaquetar con PyInstaller | [11 §6](11-playbooks.md) → trampa 18 (a, b, c, d) |
| Iconos, tema claro/oscuro | [06 §5](06-gui-y-vistas.md) → [11 §5](11-playbooks.md) |

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
| Añades un proveedor | Tabla comparativa en [05](05-proveedores-y-scraping.md) + registro en [01](01-arquitectura.md) |
| Un sitio cambia su HTML | Selectores en [05](05-proveedores-y-scraping.md) + sección de diagnóstico |
| Cambias hilos o `after` | [07](07-concurrencia-e-hilos.md) + el flujo afectado en [03](03-flujos-de-ejecucion.md) |
| Cierras un TODO | Quítalo de [12](12-deuda-tecnica-y-roadmap.md) (tiene `fichero:línea`, se desincroniza rápido) |
| **Arreglas un bug listado en [12 §4](12-deuda-tecnica-y-roadmap.md)** | Muévelo a «✅ Resuelto» **sin reutilizar su identificador**, marca su trampa en [10](10-invariantes-y-trampas.md) como resuelta **conservando el número** y el invariante que quede vivo, y actualiza el checklist de [09](09-verificacion-y-pruebas.md) para que compruebe la **no regresión** |
| **Insertas o borras líneas en un módulo muy citado** | `animeav1.py` y `anime_window.py` acumulan ~50 citas entre todos los documentos. Reubícalas comparando el **contenido** de cada línea entre la versión vieja y la nueva, no sumando un desplazamiento a ojo: no es uniforme, y las citas cortas (`:205`) se escapan de cualquier búsqueda por nombre de fichero |

**Al revisar**: relee las cabeceras de metadatos. Si el commit que citan es muy anterior al `HEAD`
actual, asume que las líneas citadas se han desplazado y reverifica antes de fiarte de un número
de línea concreto.

**Regla de oro de esta carpeta**: si no lo has leído o ejecutado, va con ⚠️. Un documento sin
ningún ⚠️ es sospechoso — significa que quien lo escribió no miró sus propios límites.
