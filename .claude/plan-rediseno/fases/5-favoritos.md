# Fase 5 — Favoritos

| | |
|---|---|
| **Objetivo** | Rejilla de 5 con pósters grandes y calificación personal, ordenable por ella |
| **Diseño visual** | [DISENO-VISUAL.html#favoritos](../DISENO-VISUAL.html#favoritos). Ábrelo en el navegador, **no** con `Read` |
| **Estrena** | Columna `rating` en `ANIMES`, `StatusPill` |
| **Toca** | `src/dataPersistence/animesPersistence.py`, `src/gui/sidebarButtons/favouriteAnimes/favouriteAnimes.py`, `src/gui/components/poster_grid.py`, `src/dataPersistence/userPersistence.py` |
| **No toca** | `APIs/`, `anime_window.py`, las otras vistas |
| **Riesgo** | 🔴 **Alto — la única fase que modifica `DB_Animes.db`, que tiene 28 filas irrecuperables** |
| **Depende de** | Fase 1 · fase 2 (`PosterGrid`) |

---

## 🔴 Antes de tocar una sola línea

Esta fase escribe en la biblioteca real del usuario. El orden no es negociable:

1. **Copia de seguridad manual** de `resources/DB/DB_Animes.db` al scratchpad de la sesión.
   `validate_db_integrity()` hace la suya en `resources/DB/backups/` antes de la primera
   modificación, pero no se confía el trabajo a un solo respaldo.
2. **Probar la migración sobre la copia primero**, con un script en el scratchpad que parchee
   `get_resource_path`. Receta lista para pegar en
   [`docs/09 §3b`](../../docs/09-verificacion-y-pruebas.md).
3. Contar las filas antes y después: `SELECT COUNT(*) FROM ANIMES` tiene que dar **lo mismo**, y las
   **14** columnas existentes tienen que seguir idénticas (`AnimeField` tiene hoy 14 miembros, de
   `ID` a `IS_PENDING`).
4. Solo entonces, sobre la real.

Lectura obligatoria: [`docs/04`](../../docs/04-modelo-de-datos.md),
[`docs/11 §2`](../../docs/11-playbooks.md) y las
[trampas 1 a 6](../../docs/10-invariantes-y-trampas.md).

---

## Pasos

### Paso 5.1 — La columna `rating`

- Miembro nuevo **al final** de `AnimeField`: `RATING = ("rating", "INTEGER")` — respetar la forma
  exacta que ya usan los demás miembros.
- **Al final importa**: `validate_db_integrity()` compara la BD con `SCHEMA` y, si solo faltan
  columnas *al final*, aplica `ALTER TABLE ADD COLUMN` sin mover datos. En cualquier otra posición
  reconstruye la tabla entera, que es el camino caro y arriesgado.
- ⚠️ **La migración es automática; `AnimeRecord` no.** Hay que actualizar a mano `to_db_dict()` y
  `from_db_dict()`, y añadir el campo a la dataclass con `rating: int | None = None`.
- ⚠️ El **orden de `FIELDS` debe seguir coincidiendo** con el de las columnas de la tabla:
  `query_sql` mapea por posición ([trampa 1](../../docs/10-invariantes-y-trampas.md)).
- Método nuevo `update_anime_rating(anime_id, rating)`, con el patrón de los `update_*` existentes.

**Escala**: entero de 0 a 10, que se pinta como 5 estrellas con medios puntos. Guardar medios como
enteros evita flotantes en SQLite y en la comparación de orden.

### Paso 5.2 — Verificar la migración

Sobre la copia: abrir, arrancar `AnimesPersistence.start()`, comprobar que la columna aparece, que
las 28 filas siguen, que `watched_episodes` sigue leyéndose como rangos y que `episodes` sigue
saliendo en el mismo orden. **Solo si esto pasa**, repetir sobre la real.

### Paso 5.3 — Estrellas y orden

- Fila de 5 estrellas bajo el título en la celda de `PosterGrid` (la fase 2 dejó el hueco previsto).
- Al pulsar, se guarda con `update_anime_rating()` y se refresca la celda.
- Control de orden en la `ViewHeader`: **Mi calificación** / Título (A-Z). La preferencia se guarda
  con un **miembro nuevo `FAVOURITES_ORDER` en `UserSettingKey`** — el enum, no una cadena
  ([`DISENO.md`](../DISENO.md) §8). Sin migración: `DB_user.db` es clave/valor y además es
  desechable.
- Las filas sin calificar (`NULL`) van **al final** en el orden por calificación, nunca las primeras.

### Paso 5.4 — Montar la vista

- `ViewHeader`: «Favoritos» + «N animes» + orden + buscador local.
- `PosterGrid` de **5** columnas, póster 216 × 324.
- `Pager` con tamaño de página **10**.

---

## Terminado cuando

- [ ] La copia de seguridad existe y está fuera del repo.
- [ ] `SELECT COUNT(*) FROM ANIMES` da lo mismo antes y después.
- [ ] Calificar un anime, cerrar la app y reabrirla: la calificación sigue ahí.
- [ ] El orden por calificación funciona y los `NULL` quedan al final.
- [ ] Los otros 4 estados, los episodios vistos y el proveedor de cada fila siguen intactos.
- [ ] `resources/DB/backups/` tiene la copia que hizo `validate_db_integrity()`.

## Verificación

Primero el script sobre la copia. Después `python src/app.py` → Favoritos: calificar dos animes,
ordenar, cerrar, reabrir, comprobar. Y entrar en Viendo y en la ficha de uno de ellos para confirmar
que no se ha roto nada de lo que ya funcionaba.

## Qué anotar en ESTADO.md

🔴 **Esta es la entrada de bitácora más importante del plan.** Filas antes y después · dónde quedó la
copia de seguridad · si la migración fue por `ALTER TABLE` o por reconstrucción · qué animes se
calificaron durante la prueba.

Y actualizar en la tabla de *Decisiones*: escala elegida y qué se hace con los `NULL`.
