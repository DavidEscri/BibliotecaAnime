# Fase 4 — Navegación entre episodios y fin de episodio

| | |
|---|---|
| **Objetivo** | Encadenar episodios sin volver a la ficha: botones anterior/siguiente en la barra, y un diálogo al terminar con dos salidas |
| **Investigación** | §2 (los requisitos y **el supuesto declarado**), §8 (fase 4), §9.1 (el punto de decisión) |
| **Estrena** | El diálogo de fin de episodio |
| **Toca** | `src/gui/components/video_player.py`, `src/gui/anime_window.py` |
| **No toca** | `APIs/`, `main_window.py` salvo el refresco de contadores, `animesPersistence.py` (se **usa**, no se cambia: no hay columna nueva) |
| **Riesgo** | 🔴 **Alto — única fase del plan que escribe en `DB_Animes.db`**, la biblioteca real |
| **Depende de** | **Fase 3** entera |

---

## 🔴 Antes de escribir una sola línea: cerrar el punto de decisión 1

La investigación (§2) declaró un **supuesto**, no un requisito:

> **Llegar al final de un episodio lo marca como visto**, reutilizando la semántica acumulativa que
> ya tiene 📖 `__toggle_episode_switch()`.

**El usuario no lo pidió.** Y escribe en la biblioteca real. Así que esta fase **empieza
preguntándoselo**, con las dos opciones sobre la mesa:

- **Sí** → al llegar al final, el episodio queda marcado (y con él los anteriores, que es cómo
  funciona el marcado hoy). Coherente con la banda «Retomar» de la portada.
- **No** → solo marca el interruptor manual. Es un `if` menos y la parte de persistencia de esta
  fase desaparece.

Anotar la respuesta en **Puntos de decisión** de [`ESTADO.md`](../ESTADO.md) antes de seguir. Si la
respuesta es «no», los pasos 4.3 y 4.4 se saltan y la fase se cierra sin tocar la BD.

---

## Antes de empezar

Lectura obligatoria, en este orden:

1. [`docs/10-invariantes-y-trampas.md`](../../docs/10-invariantes-y-trampas.md) — aquí muerden la
   **21** (las dos identidades) y la **31** (los contadores cacheados).
2. [`docs/04-modelo-de-datos.md`](../../docs/04-modelo-de-datos.md) — `watched_episodes` se persiste
   como **rangos comprimidos** y 🔴 **nunca se escribe a mano**.
3. [`docs/09 §3b`](../../docs/09-verificacion-y-pruebas.md) — cómo se prueba algo que escribe en la
   biblioteca **sin escribir en la biblioteca**.
4. De la investigación: **§2**, **§8 (fase 4)** y **§9.1**.
5. La bitácora de la **fase 0** en `ESTADO.md`: el **`reason`** de `end-file`. Es el dato del que
   depende el paso 4.2.

Y leer en `src/gui/anime_window.py`: `__previous_episode()` (`:1582`), `__next_episode()` (`:1592`)
y `__toggle_episode_switch()` (`:1602`).

**Trampas que van a morder en esta fase:**

- 🔴 **`end-file` también dispara al parar.** Si el diálogo sale cada vez que se cierra el
  reproductor, la función es insufrible. Hay que distinguir el motivo (`eof` frente a `stop`) — y
  el dato exacto lo trajo la fase 0.
- 🔴 **La identidad de persistencia es la de la fila guardada, no la del proveedor**
  ([trampa 21](../../docs/10-invariantes-y-trampas.md)). Marcar el visto pasa por
  `__persistence_anime_info()`, como todo lo demás que escribe en esta ficha. Escribir con
  `anime_info.id` cuando el desplegable está desviado **crea una fila duplicada**.
- 🔴 **Los contadores de la barra salen de listas cacheadas que solo se llenan al arrancar**
  ([trampa 31](../../docs/10-invariantes-y-trampas.md)). Quien cambie un estado tiene que
  **releerlas** antes de `refresh_sidebar_counts()`.
- ⚠️ **El marcado es acumulativo al marcar** y unitario al desmarcar, y conserva en BD los
  posteriores ya vistos. Esa lógica **no se toca**: se llama.
- ⚠️ **Cambiar de episodio es volver a resolver.** El servidor y su token son **por episodio**, y
  los de JKAnime caducan en ~3 h. Hilo daemon + `after(0, …)`, otra vez.
- ⚠️ **El corte `[:25]`** de la lista de episodios sigue vigente. «Siguiente» sobre el episodio 25
  de una lista de 1 100 tiene que hacer algo sensato, no un `IndexError`.

---

## Pasos

### Paso 4.1 — Anterior y siguiente en la barra

- Dos botones más en `VideoPlayer`. La lógica ya existe: 📖 `__previous_episode()` y
  `__next_episode()`.
- Cambiar de episodio: **cerrar el medio actual → hilo daemon → resolver el servidor del episodio
  nuevo → `after(0, …)` → cargar**. Con estado de carga mientras tanto.
- ⚠️ **Mismo servidor si existe**; si ese episodio no lo tiene, el siguiente de la lista que se
  resuelva. Si no se resuelve ninguno, **caer al navegador** (regla 2) y decirlo.
- Deshabilitar «anterior» en el primero y «siguiente» en el último. ⚠️ Con el corte `[:25]`, «el
  último» es el último **de la lista cargada**, no el del anime: decidirlo y anotarlo.
- La ficha de debajo tiene que quedar coherente: al volver, el episodio desplegado debería ser el
  que se estaba viendo.

### Paso 4.2 — El diálogo de fin de episodio

- Evento `end-file` con `reason` de fin real → `after(0, …)` → diálogo con **dos salidas**:
  **«Ver el siguiente episodio»** y **«Volver a la ficha»**.
- 🔴 **Solo con `eof`.** Parar, cerrar o cambiar de fichero **no** sacan el diálogo.
- Deshabilitar la primera opción si es el último episodio.
- ⚠️ El diálogo es un widget Tk: **no puede ir encima del vídeo** (§6.1). Sale al parar la
  reproducción, o sobre el panel con el vídeo ya cerrado. Decidirlo aquí y anotarlo.

### Paso 4.3 — Marcar el episodio como visto *(solo si el punto de decisión 1 dice que sí)*

- Al llegar al final, marcar el episodio reutilizando **la misma persistencia** que
  📖 `__toggle_episode_switch()`. **No** se escribe `watched_episodes` a mano: se persiste como
  rangos comprimidos y hay funciones para eso.
- Pasa por `__persistence_anime_info()` (trampa 21). Sin excepciones.
- ⚠️ **Un anime que no está en la biblioteca no se guarda solo.** Terminar un episodio de algo que
  no es tuyo no puede crear una fila: sería la app decidiendo por el usuario. Si no hay fila, no se
  marca nada.
- Reflejarlo en la lista de episodios de la ficha al volver (el interruptor encendido), sin
  reconstruir la ficha entera si se puede evitar.

### Paso 4.4 — Contadores *(solo si el 4.3 se hace)*

- 🔴 **Releer las listas cacheadas** del hub (`watching_animes`, `pending_animes`, …) **antes** de
  `refresh_sidebar_counts()`. Sin eso el número no se mueve hasta el siguiente arranque
  ([trampa 31](../../docs/10-invariantes-y-trampas.md)).
- ⚠️ Marcar el último episodio **no** mueve el anime a «Finalizados» por su cuenta: los estados
  excluyentes los decide el usuario con los cuatro botones. **No ampliar la fase por aquí** — si
  parece buena idea, va a *Decisiones* como propuesta, no al código.

---

## Cambios de comportamiento

| Antes | Ahora |
|---|---|
| Un episodio termina y no pasa nada | Sale un diálogo: seguir o volver a la ficha |
| Solo el interruptor marca un episodio | **Además**, llegar al final lo marca *(si el punto de decisión 1 dice que sí)* |
| Para ver el siguiente hay que volver a la ficha | Botón en la barra |

---

## Terminado cuando

- [ ] El punto de decisión 1 está **cerrado y anotado**, con la respuesta del usuario.
- [ ] «Siguiente» y «anterior» cambian de episodio **resolviendo de nuevo**, sin congelar la ventana.
- [ ] Están deshabilitados en los extremos, y el comportamiento con el corte `[:25]` está decidido y
      anotado.
- [ ] El diálogo sale **al terminar** y **no** al cerrar el reproductor a mano.
- [ ] «Ver el siguiente» encadena; «Volver a la ficha» devuelve la ficha como estaba.
- [ ] *(Si aplica)* El episodio queda marcado, **con la identidad de la fila guardada**, y los
      anteriores también — la semántica acumulativa de siempre.
- [ ] *(Si aplica)* Los contadores de la barra lateral se mueven **sin reiniciar la app**.
- [ ] 🔴 **`SELECT COUNT(*) FROM ANIMES` da lo mismo antes y después.** Ni una fila nueva.
- [ ] Los episodios vistos que ya había **siguen ahí**.

## Verificación

🔴 **Sobre una copia de `DB_Animes.db`, no sobre la real.** Es la receta que dejó la fase 4 del
rediseño y que la 8 volvió a aplicar: se apunta la persistencia a una copia
(`persistence.path_db` + `SqlUtils`) y al terminar se comprueba que el **hash de la real no ha
cambiado**. Anotar el `sha256` antes y después.

Con la copia montada:

1. Ver **el final de un episodio corto** de verdad (o saltar cerca del final con la barra) y
   comprobar el diálogo.
2. Las **dos salidas**: encadenar dos episodios seguidos, y volver a la ficha.
3. Cerrar el reproductor a mitad → **el diálogo no sale**.
4. Comprobar el marcado: el episodio y los anteriores, y que **los posteriores ya vistos siguen**.
5. Recuento de filas antes y después.
6. Los contadores de la barra, mirados en pantalla.

Si no se puede llegar al final de un episodio ese día, decirlo: el diálogo **es** la fase, y darlo
por bueno sin verlo salir es exactamente lo que la regla 7 del plan prohíbe.

## Qué anotar en ESTADO.md

La respuesta al punto de decisión 1 · el `reason` real con el que se distingue el fin · recuento de
filas y `sha256` de la BD real antes y después · qué animes se tocaron en la copia · qué se decidió
sobre «el último episodio» con el corte `[:25]` · y dónde acabó saliendo el diálogo, dado que no
puede ir sobre el vídeo.
