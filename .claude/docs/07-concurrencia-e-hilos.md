# 07 — Concurrencia e hilos

| | |
|---|---|
| **Fecha** | 2026-09-01 · rama `feature/ui-redisign` · último commit **`a0e3f37`** (abrir la ficha por un episodio). ⚠️ **Solo se ha revisado C5**: el resto del documento sigue anclado en el 2026-09-01 con el refresco de la banda «Retomar» (`4ffc2ef`) |
| **Última revisión** | 2026-09-01 (**abrir la ficha por un episodio**): **C5 sube de gravedad** — la petición de servidores ya no la dispara solo el usuario, la dispara también abrir la ficha desde «Viendo» o «Pendientes»; el `after(50 ms)` que lo envuelve es una tirita, no el arreglo. Antes, 2026-09-01 (**refresco de la banda «Retomar»**): hilo nuevo en la portada, y **§1, §2 y §6 reancladas enteras contra el código real** — la mitad de las líneas que citaban se habían movido con el rediseño y tres hilos del inventario **ya no existían**. Antes, 2026-08-31 (**fondo de la pantalla de carga**): anclas de `main_window.py` reverificadas en §1, §2 y §4 (iban ~29 líneas desplazadas) y `place_forget()` corregido a `destroy()` en C1; las de #5 a #13 **siguen sin verificar**. Antes, 2026-08-16 (**columna `provider_id`**): hilos a **13** (eran 8) y `after()` a **10** (eran 4); **C2 resuelta** — los 4 puntos que abren una ficha pintan ya en el hilo de Tk. C5 sigue viva |
| **Cubre** | `src/gui/main_window.py`, `src/gui/anime_window.py`, `src/gui/sidebarButtons/**`, `src/utils/utils.py` |

Procedencia: ✅ verificado en ejecución · 📖 leído en código · ⚠️ sin verificar.

> **Aviso de honestidad**: este documento describe **lo que hay**, no lo que debería haber. Varias de
> las prácticas listadas violan la regla «nada de Tk fuera del hilo de UI». Se documentan porque
> están en producción y funcionan en la práctica, no porque sean correctas. **No las repliques en
> código nuevo.**

---

## 1. Inventario de hilos

📖 Todos los `threading.Thread` del proyecto:

✅ **Reanclados de cero el 2026-09-01**, con `git grep -n "threading.Thread"` sobre el árbol en
`4ffc2ef`. Siguen siendo **13**, pero **no son los mismos 13** que listaba este documento: el rediseño
se llevó por delante los **tres** hilos del frame de carga del buscador (#6, #7 y #8 de la tabla
vieja, que eran los últimos `❌ (C1)` fuera de `main_window`) y trajo uno que nunca se apuntó aquí, el
del póster de «Empezar». De la tabla vieja **solo las cuatro primeras líneas eran correctas**.

| # | Dónde | Línea | Objetivo | Vuelve con `after`? |
|---|---|---|---|---|
| 1 | `main_window.__reload_recent_animes` | `:355` | `__reload_recent_animes_worker` — recarga al cambiar de proveedor | ✅ |
| 2 | `main_window.__on_recent_animes_reloaded` | `:396` | `__preload_recent_animes_info` tras la recarga | — |
| 3 | `main_window.show_loading_screen` | `:463` | `download_images_and_show_animes` | ❌ (C1) |
| 4 | `main_window.download_images_and_show_animes` | `:494` | `__preload_recent_animes_info` | — |
| 5 | `recentAnimes.__on_anime_click` | `:232` | `_load_and_show` (ficha) | ✅ |
| **6** | `recentAnimes.__refresh_resume_episodes` | `:180` | 🆕 releer los episodios de la banda «Retomar» | ✅ |
| 7 | `searchAnimes.__launch_search` | `:352` | `_search` — busca **y baja las carátulas** en el mismo hilo | ✅ |
| 8 | `searchAnimes.__on_anime_click` | `:603` | abrir la ficha de un resultado | ✅ |
| 9 | `anime_window.open_saved_anime` | `:263` | abrir un anime **de la biblioteca** | ✅ |
| 10 | `anime_window.__repair_to_target_provider` | `:1042` | localizar el anime en el proveedor destino | ✅ |
| 11 | `anime_window.__confirm_and_migrate` | `:1125` | migrar la fila + mover/bajar pósters | ✅ |
| 12 | `utilsButtons.SavedAnimeSearch.search` | `:176` | búsqueda web que completa a la local | ✅ |
| 13 | `pendingAnimes.__cache_poster_async` | `:335` | copiar el póster a `watching/` al pulsar «Empezar» | — |

Más **dos `ThreadPoolExecutor(max_workers=8)`** para pósters:

| Dónde | Línea |
|---|---|
| `utils.download_animes_poster` | `:124` |
| `utils.download_images_progress` | `:179` |

> 🆕 **El hilo #6 es el primero que sale a la red por datos que ya están guardados.** Los otros doce
> traen algo que el usuario acaba de pedir; éste corrige una fila de la biblioteca por su cuenta al
> entrar en la portada ([03 §11](03-flujos-de-ejecucion.md)). De ahí sus dos precauciones propias:
> `strict=True` —sin *fallback*— y no escribir nunca si el proveedor devuelve una lista vacía.
>
> **Los #5 y #8 son antiguos que se arreglaron**, no nuevos: `recentAnimes` ya tenía hilo pero pintaba
> desde él, y `searchAnimes.__on_anime_click` **no tenía hilo** —hacía la petición en el hilo de
> Tkinter y la ventana se congelaba—. Los dos pasan ahora por `after(0, …)`.
>
> ⚠️ **El #13 no vuelve con `after`, y no le hace falta**: no toca ningún widget. Baja un JPEG y ya;
> mientras tanto `find_cached_poster_path()` sigue encontrando la imagen en `pending/`.

Todos los hilos son **daemon**: al cerrar la ventana mueren sin limpieza. ✅ Verificado: la app se
cierra sin colgarse.

---

## 2. Qué corre en qué hilo

✅ Anclajes reverificados el 2026-09-01 contra `4ffc2ef`.

| Operación | Hilo | Anclaje |
|---|---|---|
| `mainloop()` y todos los callbacks de widget | 🖥️ UI | `app.py:14` |
| Animación del GIF (`after(100, …)`) | 🖥️ UI | `main_window.py:453-458` |
| Carga inicial de la BD (`load_animes`) | 🧵 daemon | `main_window.py:467` → `528-541` |
| `get_recent_animes()` | 🧵 daemon | `main_window.py:468` |
| Descarga de pósters de recientes | ⚙️ pool (8) | `utils.py:179` |
| Precarga de fichas de recientes | 🧵 daemon | `main_window.py:500-526` |
| Clic en anime **desde recientes** | 🧵 daemon → `after(0,…)` ✅ | `recentAnimes.py:205-232` |
| **Refresco de la banda «Retomar»** | 🧵 daemon → `after(0,…)` ✅ 🆕 | `recentAnimes.py:131-180` |
| Clic en anime **desde las 4 vistas de estado** | 🧵 daemon → `after(0,…)` ✅ | `open_saved_anime` (`anime_window.py:196-263`) |
| Clic en anime **desde el buscador** | 🧵 daemon → `after(0,…)` ✅ | `searchAnimes.py:598-606` |
| Búsquedas del buscador (**y sus carátulas**) | 🧵 daemon → `after(0,…)` ✅ | `searchAnimes.py:341-352` |
| Búsqueda dentro de las vistas de estado | 🖥️ UI (local) + 🧵 daemon (web) → `after(0,…)` ✅ | `utilsButtons.py:172-176` |
| **Servidores de un episodio** | 🖥️ **UI** ⚠️ | `anime_window.py:1694` |
| Recarga de recientes al cambiar de proveedor | 🧵 daemon → `after(0,…)` ✅ | `main_window.py:355-400` |
| **Migrar una fila a otro proveedor** | 🧵 daemon → `after(0,…)` ✅ | `anime_window.py:1110-1125` |
| Todas las escrituras de estado en BD | 🖥️ UI (desde callbacks) | `anime_window.py:1307-1368` |
| Descarga/borrado de pósters por estado | 🖥️ UI ⚠️ | `anime_window.py:1308, 1315, 1325…` |
| **Mover/rebajar pósters al migrar** | 🧵 daemon ✅ | `anime_window.py:1127-1148` |
| **Escritura de `episodes` desde el refresco de la banda** | 🖥️ UI (dentro del `after`) ✅ 🆕 | `recentAnimes.py:147-166` |

> 🆕 **La última fila es deliberada.** La petición va en el hilo, pero el `UPDATE` se hace **ya en el
> hilo de Tkinter**, dentro del `after(0, …)`: así la relectura de la fila, la escritura y el
> repintado de la tarjeta pasan en el mismo turno y no puede colarse nada entre medias
> ([03 §11](03-flujos-de-ejecucion.md)). Son tres consultas a SQLite local, no red.
>
> 🆕 **El buscador ya no tiene hilos «malos»**: sus tres hilos con ❌ (C1) —los del frame de carga con
> GIF— desaparecieron con el rediseño. Hoy sus dos hilos vuelven los dos por `after(0, …)`, y el de la
> búsqueda **baja también las carátulas** antes de volver, para no dejar esa descarga en el hilo de UI.

> 🆕 **Tres de las cuatro filas ⚠️ del 2026-08-07 se han cerrado** con la columna `provider_id`: los
> clics de las vistas de estado y del buscador, y la búsqueda dentro de las vistas. La que **queda
> viva es la de los servidores de vídeo** (C5): sigue haciendo HTTP en el hilo de Tkinter.

---

## 3. Reglas para código nuevo

### ✅ SÍ

1. **Toda petición HTTP va en un hilo daemon.** Patrón de referencia: `recentAnimes.py:205-232`.
2. **Para volver al hilo de UI, usa `self.after(delay, callback)`.** Es lo que hacen las animaciones
   de GIF (`main_window.py:453-458`).
3. **Comprueba `widget.winfo_exists()` antes de tocar un widget desde un callback diferido.**
   El frame puede haberse destruido. Ejemplo bueno: `recentAnimes.py:147-166`, que comprueba **dos**
   widgets distintos y reacciona distinto a cada uno.

   ```python
   def _apply(fresh_episodes):          # ya en el hilo de Tkinter
       if not self.main_window.winfo_exists():
           return                        # la ventana se cerró: no hay nada que hacer
       for anime_id, episodes in fresh_episodes:
           ...                           # la escritura en BD SÍ se hace igualmente
           if not resume_band.winfo_exists():
               continue                  # la banda se fue: solo se salta el repintado
   ```

   ⚠️ El GIF de carga (`main_window.py:453-458`) es el otro ejemplo, pero **el del buscador ya no
   existe**: el rediseño se llevó su frame de carga.

4. **Guarda el `Thread`, no el resultado de `.start()`** (ver §4, carrera C4).

### ❌ NO

1. **No hagas HTTP en el hilo de Tkinter.** Congela la ventana entera.
2. **No añadas `time.sleep()` en el hilo de UI.** Ver §5.
3. **No crees ni configures widgets desde un hilo daemon** en código nuevo, aunque el código
   existente lo haga.
4. **No asumas que `winfo_width()` es correcto** justo después de crear un widget: devuelve `1`
   hasta el primer dibujado.

---

## 4. Condiciones de carrera conocidas

### C1 — Widgets Tk manipulados desde hilos daemon 📖

El caso más extendido. Ejemplos reales:

| Dónde | Qué hace desde un hilo daemon |
|---|---|
| `main_window.py:531-541` | `progress_bar.set()` y `progress_label.configure()` |
| `main_window.py:475-478` | **`messagebox.showwarning`** |
| `main_window.py:482-487` | `progress_bar.set(0.9)`, `loading_frame.destroy()` |
| `main_window.py:490` | `show_frame()` → construye **toda** la vista de recientes |
| `utils.py:146-147` | `progress_bar.set()` desde **8 workers** del pool |
| ~~`recentAnimes.py:97-99`~~ | ✅ **resuelto**: ahora vuelve con `after(0,…)` (C2) |
| `searchAnimes.py:220-225` | `__display_animes` → crea decenas de widgets |

Tkinter **no es thread-safe**. ✅ En la práctica el arranque completo funciona sin traceback, pero es
suerte estructural, no garantía. ⚠️ No se ha observado ningún cuelgue, pero tampoco se ha hecho
*stress test*.

**Mitigación en `utils.py:162-164`**: el contador de progreso sí está protegido con `threading.Lock`
— pero el `Lock` protege el **contador**, no la llamada a Tk que hace dentro.

### C2 — `AnimeWindowViewer` construido desde dos hilos ✅ *(resuelta 2026-08-16)*

**Antes**: `recentAnimes.py` construía la ficha desde un daemon; las otras vistas, desde UI. Si el
usuario cambiaba de vista con el hilo en vuelo, el `content_frame` ya se había vaciado y la ficha se
pintaba **encima de la vista nueva**.

**Ahora**: los **cuatro** puntos que abren una ficha construyen el viewer en el hilo de Tkinter, vía
`after(0, …)`, y **todos** comprueban `main_window.winfo_exists()` antes de tocar nada:

| Punto de entrada | Línea |
|---|---|
| `recentAnimes.__on_anime_click` | `:213-229` |
| `searchAnimes.__on_anime_click` | `:588-601` |
| `open_saved_anime` (las 4 vistas de estado) | `anime_window.py:225-261` |
| `__confirm_and_migrate._done` (reconstruye tras migrar) | `anime_window.py:1100-1115` |

✅ Líneas reancladas el 2026-09-01 contra `4ffc2ef`.

> 🔴 **No fue una mejora cosmética: era un crash reproducible.** Construir la ficha desde el hilo
> secundario revienta con `invalid command name ...!searchbutton.!ctkcanvas` en cuanto la vista que se
> está destruyendo tenía un evento `<Configure>` encolado —lo tienen las cuatro vistas de estado, por
> su barra de búsqueda—, porque ese evento se atiende cuando el canvas ya no existe. El síntoma es un
> traceback en consola y la ficha a medio pintar.
>
> Reproducido y verificado en `test_crash_tk.py` (scratchpad de la sesión).

### C3 — Escritura concurrente en `recent_animes` 📖

`__preload_recent_animes_info` (`main_window.py:500-526`) y `_load_and_show` (`recentAnimes.py:226-229`)
pueden escribir el mismo índice a la vez. El propio código lo justifica (`:504-511`): la asignación de
un elemento de lista es atómica bajo el GIL. **Es correcto** para este caso concreto.

> ✅ **Mitigado desde el 2026-08-06** por el contador de generación `__recent_animes_generation`
> (`main_window.py:74`). Al cambiar de proveedor, `self.recent_animes` pasa a ser **otra lista** y los
> índices de la precarga en vuelo dejan de significar nada; la precarga comprueba su generación antes
> de escribir (`:515`, `:523`) y aborta si ha caducado. Lo que sigue sin cubrirse es la carrera
> original entre precarga y clic **dentro de la misma generación**, que es la benigna.

### ~~C4 — El guard antidoble-búsqueda no funciona~~ ✅ **Desaparecida con el rediseño (2026-08-21)**

⚠️ **Ya no hay tal guard, ni los tres hilos que protegía.** El rediseño dejó el buscador con **dos**
hilos (`__launch_search` y `__on_anime_click`) y sustituyó el guard roto por un **contador de
generación** (`searchAnimes.py:107`, `:329-330`, `:361`): las peticiones ya no se estorban porque
pueden solaparse sin problema — **solo pinta la última**. Se conserva la entrada porque el error de
código que la causaba es fácil de reintroducir:

```python
# el patrón roto, hoy inexistente en src/
self.__current_search_thread = threading.Thread(...).start()   # ← .start() devuelve None
```

`Thread.start()` devuelve `None`, así que `__current_search_thread` **siempre vale `None`** y el
guard `if self.__current_search_thread and self.__current_search_thread.is_alive()`
(`:160-161`, `:166-167`, `:333-334`) **nunca bloquea nada**. Consecuencia: pulsar «Buscar» dos veces
seguidas lanza dos hilos que pintan sobre el mismo `content_frame`.

**Arreglo** (no aplicado — este trabajo es solo de documentación):

```python
t = threading.Thread(target=..., args=(...), daemon=True)
self.__current_search_thread = t
t.start()
```

### C5 — HTTP en el hilo de UI al abrir servidores 📖

`anime_window.py:1802-1871` llama a `get_anime_episode_servers` en el callback de la fila. ✅ Con
AnimeAV1 tarda ~0,2 s.

🆕 **Desde el 2026-09-01 esta llamada ya no la dispara solo el usuario.** Abrir la ficha por un
episodio ([03 §12](03-flujos-de-ejecucion.md)) entra por aquí sola, así que la congelación pasó de
«cuando pulso una fila» a «cada vez que entro desde “Viendo” o “Pendientes”». Se mitiga con un
`after(FOCUS_DELAY_MS = 50)` **detrás del pintado**: la ficha se ve entera y el cursor `watch` sale
después. Es una tirita —la petición sigue en 🖥️— y sube la prioridad de C5, que es el **último** sitio
de la GUI que sale a la red desde el hilo de la interfaz.

> ⚠️ **Corrección (2026-08-07).** La versión anterior decía que «si AnimeAV1 falla y entra el fallback
> a AnimeFLV, se suman los timeouts de ambos proveedores». **Es falso desde el 2026-07-30**: esa
> llamada pasa `strict=True` y `provider_id` explícito (`anime_window.py:1694-1696`), justo para que
> **no** haya fallback — el slug es del proveedor que sirvió la ficha y no significa nada en otro
> sitio. Con `strict=True`, `call_with_fallback` recorta a `providers_to_try[:1]`.
>
> La congelación sigue siendo real, pero acotada al timeout de **un solo** proveedor.

### C6 — La purga de imágenes compite con los widgets que las muestran ✅

`load_image` (`utils.py:198-202`) hace `Image.open(path)` **sin cerrar**; PIL carga de forma perezosa, así
que el descriptor queda abierto mientras viva el `CTkImage`. Verificado: `os.remove` sobre esa ruta
lanza `PermissionError` en Windows, y solo se libera tras `del` + `gc.collect()`.

La purga (`utils.py:99-105`) captura la excepción e imprime, así que **no rompe** — pero deja
huérfanos que reaparecen en el siguiente arranque.

---

## 5. El patrón heredado `time.sleep(0.1)`

✅ **Ya no está en `src/`** (2026-08-21, rediseño). `git grep -n "time.sleep" -- src/` solo devuelve las
dos esperas **entre reintentos de scraping**, que van en hilo daemon y son correctas
(`animeav1.py:241`, `animeflv.py:233`). En su lugar, las seis vistas dejaron un comentario donde
estaba la llamada, explicando por qué ya no hace falta (`recentAnimes.py:59-61` y equivalentes): las
rejillas son de un número **fijo** de columnas, así que no se mide ningún `winfo_width()`.

**La sección se conserva porque la regla sigue viva**: no metas `sleep` en el hilo de UI. Lo que
sigue es el estado **anterior** al rediseño, con sus líneas de entonces:

📖 Aparecía **6 veces**, siempre justo después de `clear_frame()` y **siempre en el hilo de UI**:

| Fichero | Línea |
|---|---|
| `anime_window.py` | `:65` |
| `recentAnimes.py` | `:38` |
| `favouriteAnimes.py` | `:37` |
| `finishedAnimes.py` | `:37` |
| `watchingAnimes.py` | `:39` |
| `pendingAnimes.py` | `:39` |
| `searchAnimes.py` | `:70` |

### Qué pretende

⚠️ *Reconstrucción, no confirmada por el autor*: dar tiempo a Tk a procesar los `destroy()` de
`clear_frame()` antes de leer `content_frame.winfo_width()` para calcular `num_columns`
(`recentAnimes.py:39`). Si `winfo_width()` devuelve `1`, la rejilla colapsa a una columna.

### Por qué NO replicarlo

1. **No hace lo que parece.** `time.sleep` en el hilo de UI **bloquea** el bucle de eventos: Tk no
   procesa nada durante esos 100 ms. No «deja que Tk respire» — le impide respirar.
2. **Congela la ventana** 100 ms en cada cambio de vista.
3. **No garantiza nada**: si el layout tarda más, el problema reaparece.

### Qué hacer en su lugar

```python
# En vez de:  self.main_window.clear_frame(); time.sleep(0.1); construir()
self.main_window.clear_frame()
self.main_window.content_frame.update_idletasks()   # procesa geometría pendiente, sin bloquear
construir()

# O, si de verdad hace falta ceder el turno al bucle de eventos:
self.main_window.after(100, construir)
```

⚠️ Ninguna de las dos alternativas se ha probado en este proyecto. **No refactorices las 6
ocurrencias a la vez**: cambia una, verifica que la rejilla mantiene sus columnas, y sigue.

---

## 6. `after()` — dónde se usa y dónde no

📖 Hay **11** usos de `.after(...)`. ✅ Recontados y **reanclados de cero el 2026-09-01** contra
`4ffc2ef`: el conteo de agosto decía 10, pero incluía el GIF del buscador —que el rediseño se llevó—
y **ninguna de sus diez líneas seguía siendo correcta**.

| Dónde | Para qué | Estado |
|---|---|---|
| `main_window.py:376` | devolver el resultado de la recarga de recientes al hilo de UI | ✅ **el patrón de referencia** |
| `main_window.py:458` | animar el GIF de carga | ✅ correcto |
| 🆕 `recentAnimes.py:178` | persistir los episodios nuevos y repintar la banda «Retomar» | ✅ |
| `recentAnimes.py:229` | pintar la ficha tras la petición | ✅ |
| `searchAnimes.py:350` | pintar una página de resultados (y sus carátulas ya bajadas) | ✅ |
| `searchAnimes.py:601` | pintar la ficha de un resultado de búsqueda | ✅ |
| `anime_window.py:261` | pintar la ficha de un anime guardado | ✅ |
| `anime_window.py:1040` | abrir el diálogo tras localizar el anime en otro proveedor | ✅ |
| `anime_window.py:1122` | repintar la ficha tras migrar la fila | ✅ |
| `utilsButtons.py:174` | añadir a la rejilla lo que aporte la búsqueda web | ✅ |
| `utils.py:62` (`update_gif`) | — | ⚠️ **código muerto y roto** |

> ✅ **El patrón ha dejado de ser la excepción.** En 2026-08-07 había **un** sitio que devolvía trabajo
> al hilo de UI correctamente; hoy hay **nueve**. La regla operativa que los nueve comparten:
>
> ```python
> def _volver(resultado):          # ya en el hilo de Tkinter
>     if not main_window.winfo_exists():
>         return                    # la ventana pudo cerrarse mientras tanto
>     main_window.configure(cursor="")   # restaurar ANTES de cualquier salida
>     ...                           # aquí, y solo aquí, se tocan widgets
>
> def _trabajo():                   # hilo daemon: red y BD, cero widgets
>     main_window.after(0, _volver, peticion())
>
> threading.Thread(target=_trabajo, daemon=True).start()
> ```
>
> Dos detalles que se olvidan y hacen daño: **restaurar el cursor en todas las salidas**, incluida la
> de error, y usar **`update_idletasks()`** en vez de `update()` antes de lanzar el hilo — `update()`
> atiende eventos de usuario, así que un segundo clic puede reentrar y lanzar un segundo hilo.

La función suelta `update_gif` de `utils.py:59-62` haría
`root.after(100, update_gif, frame)`, pasando `frame` como primer argumento (`label`). **No tiene
llamantes en `src/`.** La pantalla de carga define su propia `update_gif` local, correcta.

---

## 7. Ciclo de vida al cerrar

📖 No hay `protocol("WM_DELETE_WINDOW", …)` ni `join()` de ningún hilo. Al cerrar la ventana:

- Los hilos daemon mueren de golpe. Una descarga de póster a medias puede dejar un JPEG truncado
  en disco. ⚠️ No verificado.
- No hay `commit` pendiente que perder: `SqlUtils` hace `commit()` y `close()` en cada operación
  (`sqlite.py:16-46`).
- ✅ Verificado: arrancar la app y cerrarla **no modifica** `DB_Animes.db`.
