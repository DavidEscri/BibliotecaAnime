# Fase 4 — Navegación entre episodios y fin de episodio

| | |
|---|---|
| **Objetivo** | Encadenar episodios sin volver a la ficha: anterior/siguiente en la barra, «Siguiente episodio» en la columna de información, y una tarjeta al terminar con dos salidas |
| **Diseño** | [`DISENO-VISUAL.html`](../DISENO-VISUAL.html) — sección **Estados → Fin de episodio**, y los botones 1 y 5 de la sección **Barra**. 🔴 **Manda en lo visual** |
| **Investigación** | §2 (los requisitos y **el supuesto declarado**), §8 (fase 4), §9.1 (el punto de decisión) |
| **Estrena** | La tarjeta de fin de episodio |
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
5. La bitácora de la **fase 0** en `ESTADO.md`: el **`reason`** de `end-file`, y **si la
   superficie vuelve a pintar tras `grid_remove()`** (paso 0.7). Son los dos datos de los que
   depende el paso 4.2.
6. La bitácora de la **fase 3**: cómo quedaron las tarjetas de estado y la columna de información,
   que es donde esta fase escribe.

Y leer en `src/gui/anime_window.py`: `__previous_episode()` (`:1582`), `__next_episode()` (`:1592`)
y `__toggle_episode_switch()` (`:1602`).

**Trampas que van a morder en esta fase:**

- 🔴 **`end-file` también dispara al parar.** Si la tarjeta sale cada vez que se cierra el
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

### Paso 4.1 — Anterior y siguiente

- Los botones **ya están dibujados** por la fase 3, deshabilitados: el **1** (anterior) y el **5**
  (siguiente) de la barra, y **«Siguiente episodio»** al fondo de la columna de información, con el
  número a la derecha. Esta fase los conecta; no añade botones.
- La lógica de qué episodio es el anterior o el siguiente ya existe: 📖 `__previous_episode()` y
  `__next_episode()`, que respetan el orden del proveedor.
- Cambiar de episodio: **cerrar el medio actual → tarjeta «Cargando el episodio N» → hilo daemon →
  resolver el servidor del episodio nuevo → `after(0, …)` → cargar**. Es el mismo camino que la
  fase 3 hizo para un clic en servidor.
- Al cambiar se actualiza **todo lo que nombra el episodio**: la línea «**Episodio N** de M ·
  servidor X», los servidores de la columna (los del episodio nuevo) y la fila «▮ Reproduciendo» de
  la lista de debajo, que se desplaza hasta él.
- ⚠️ **Mismo servidor si existe**; si ese episodio no lo tiene, el siguiente de la lista que se
  resuelva. Si no se resuelve ninguno, **caer al navegador** (regla 2) y decirlo.
- Deshabilitar «anterior» en el primero y «siguiente» en el último. ⚠️ Con el corte `[:25]`, «el
  último» es el último **de la lista cargada**, no el del anime: decidirlo y anotarlo.
- La ficha de debajo tiene que quedar coherente: al volver, el episodio desplegado debería ser el
  que se estaba viendo.

### Paso 4.2 — La tarjeta de fin de episodio

- Evento `end-file` con `reason` de fin real → `after(0, …)` → tarjeta en **el recuadro del vídeo**.
- 🔴 **Solo con `eof`.** Parar, volver a la ficha o cambiar de fichero **no** la sacan.
- **Dónde va, ya decidido por el diseño**: en el frame de tarjetas de la fase 3, que **sustituye** a
  la superficie en su celda (`grid_remove()` de la superficie, sin destruirla). Nada encima del
  vídeo: el medio ya ha terminado.
- **Qué dice**, de arriba abajo:
  - Una **✕** arriba a la derecha, como la de cualquier ventana: **cierra solo el aviso**. La
    superficie vuelve a su sitio con el último fotograma, la barra se queda en «repetir» y no se
    marca ni desmarca nada más. El aviso no vuelve a salir hasta el siguiente `eof`.
  - «**Has terminado el episodio N**» (20 px, negrita).
  - «<Título> · <proveedor> · <servidor>» en `TXT_3`.
  - Solo si el punto de decisión 1 dice que sí: una franja con ✓ en `FIN_TXT` y «Marcado como
    visto · N de M». Si dice que no, **la franja no existe**.
  - Dos botones: **«Volver a la ficha»** (el mismo efecto que «← Volver a la ficha») y **«Ver el
    episodio N+1»** (primario, con ▶). En el último episodio de la lista cargada, el primario no se
    ofrece.
- **Alrededor**: la etiqueta de la columna pasa a «Terminado» y su barra de progreso se actualiza;
  en la barra de controles, play/pausa pasa a **repetir**, el progreso queda lleno y **+10 s**,
  deshabilitado.
- **En pantalla completa** (punto de decisión 7, cerrado por el usuario): la tarjeta sale **igual,
  centrada**, y la barra flotante **se ve todo el rato** mientras la tarjeta está a la vista; no
  hay auto-ocultación.
- 🔴 **`Esc` con la tarjeta a la vista** sale de pantalla completa y la tarjeta **vuelve al recuadro
  del vídeo acoplado**, como en la vista normal del diseño. **No se queda en mitad de la pantalla.**
  Sale gratis si la tarjeta vive en el frame de tarjetas y no en un `Toplevel` (fase 3,
  restricción 4); comprobarlo, porque es justo lo que el usuario pidió.

### Paso 4.3 — Marcar el episodio como visto *(solo si el punto de decisión 1 dice que sí)*

- Al llegar al final, marcar el episodio reutilizando **la misma persistencia** que
  📖 `__toggle_episode_switch()`. **No** se escribe `watched_episodes` a mano: se persiste como
  rangos comprimidos y hay funciones para eso.
- Pasa por `__persistence_anime_info()` (trampa 21). Sin excepciones.
- ⚠️ **Un anime que no está en la biblioteca no se guarda solo.** Terminar un episodio de algo que
  no es tuyo no puede crear una fila: sería la app decidiendo por el usuario. Si no hay fila, no se
  marca nada.
- Reflejarlo **en el momento** en la lista de debajo, que está a la vista: el interruptor del
  episodio encendido y su línea «Terminado». Y en «N de M vistos» de la columna. Sin reconstruir la
  ficha entera: 📖 `__refresh_episode_states()` y `__refresh_seen_bar()` ya lo hacen.

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
| Un episodio termina y no pasa nada | Sale una tarjeta en el recuadro del vídeo: seguir o volver a la ficha |
| Solo el interruptor marca un episodio | **Además**, llegar al final lo marca *(si el punto de decisión 1 dice que sí)* |
| Para ver el siguiente hay que volver a la ficha | Botones en la barra y «Siguiente episodio» en la columna |

---

## Terminado cuando

- [ ] El punto de decisión 1 está **cerrado y anotado**, con la respuesta del usuario.
- [ ] «Siguiente» y «anterior» cambian de episodio **resolviendo de nuevo**, sin congelar la ventana.
- [ ] Están deshabilitados en los extremos, y el comportamiento con el corte `[:25]` está decidido y
      anotado.
- [ ] La tarjeta sale **al terminar**, en el recuadro del vídeo, y **no** al volver a la ficha a mano.
- [ ] «Siguiente episodio» de la columna hace lo mismo que el botón 5 de la barra.
- [ ] La **✕** cierra solo el aviso: vuelve el último fotograma y la barra sigue en «repetir».
- [ ] En pantalla completa, la tarjeta sale centrada y **la barra no se oculta** mientras está.
- [ ] `Esc` con la tarjeta a la vista sale de pantalla completa y la deja **en el recuadro acoplado**.
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
   comprobar la tarjeta, **también en pantalla completa**: dejar el ratón quieto más de 5 s (la
   barra no se va), pulsar `Esc` (la tarjeta vuelve al recuadro acoplado) y pulsar la **✕**.
2. Las **dos salidas**: encadenar dos episodios seguidos, y volver a la ficha.
3. Volver a la ficha a mitad → **la tarjeta no sale**.
4. Comprobar el marcado: el episodio y los anteriores, y que **los posteriores ya vistos siguen**.
5. Recuento de filas antes y después.
6. Los contadores de la barra, mirados en pantalla.

Si no se puede llegar al final de un episodio ese día, decirlo: la tarjeta **es** la fase, y darlo
por bueno sin verlo salir es exactamente lo que la regla 7 del plan prohíbe.

## Qué anotar en ESTADO.md

La respuesta al punto de decisión 1 · el `reason` real con el que se distingue el fin · recuento de
filas y `sha256` de la BD real antes y después · qué animes se tocaron en la copia · qué se decidió
sobre «el último episodio» con el corte `[:25]` · si la superficie volvió a pintar tras enseñar la
tarjeta · y si la tarjeta volvió sola al recuadro acoplado al pulsar `Esc` o hizo falta moverla a mano.
