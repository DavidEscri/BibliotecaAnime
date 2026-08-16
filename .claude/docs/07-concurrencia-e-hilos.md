# 07 — Concurrencia e hilos

| | |
|---|---|
| **Fecha** | 2026-08-16 · **Commit** `54fb3d6` · árbol **sucio** (columna `provider_id`, 16 ficheros) |
| **Última revisión** | 2026-08-16 (**columna `provider_id`**): hilos a **13** (eran 8) y `after()` a **10** (eran 4); **C2 resuelta** — los 4 puntos que abren una ficha pintan ya en el hilo de Tk. C5 sigue viva |
| **Cubre** | `src/gui/main_window.py`, `src/gui/anime_window.py`, `src/gui/sidebarButtons/**`, `src/utils/utils.py` |

Procedencia: ✅ verificado en ejecución · 📖 leído en código · ⚠️ sin verificar.

> **Aviso de honestidad**: este documento describe **lo que hay**, no lo que debería haber. Varias de
> las prácticas listadas violan la regla «nada de Tk fuera del hilo de UI». Se documentan porque
> están en producción y funcionan en la práctica, no porque sean correctas. **No las repliques en
> código nuevo.**

---

## 1. Inventario de hilos

📖 Todos los `threading.Thread` del proyecto:

✅ Recontados el 2026-08-16: son **13**, no 8. Los **cinco nuevos** (#9 a #13) llegaron con la columna
`provider_id`, y todos siguen la regla buena: petición en el hilo, repintado con `after(0, …)`.

| # | Dónde | Línea | Objetivo | Vuelve con `after`? |
|---|---|---|---|---|
| 1 | `main_window.__reload_recent_animes` | `:386-390` | `__reload_recent_animes_worker` — recarga al cambiar de proveedor | ✅ |
| 2 | `main_window.__on_recent_animes_reloaded` | `:425-426` | `__preload_recent_animes_info` tras la recarga | — |
| 3 | `main_window.show_loading_screen` | `:479` | `download_images_and_show_animes` | ❌ (C1) |
| 4 | `main_window.download_images_and_show_animes` | `:499-500` | `__preload_recent_animes_info` | — |
| 5 | `recentAnimes.__on_anime_click` | `:114` | `_load_and_show` (ficha) | ✅ 🆕 |
| 6 | `searchAnimes.__show_loading_frame` | `:206-210` | `__search_anime_by_query` | ❌ (C1) |
| 7 | `searchAnimes.__show_loading_frame` | `:212-216` | `__search_anime_by_filter` | ❌ (C1) |
| 8 | `searchAnimes.__load_page` | `:335-339` | `__search_and_display_animes` | ❌ (C1) |
| **9** | `searchAnimes.__on_anime_click` | `:382` | 🆕 abrir la ficha de un resultado | ✅ |
| **10** | `anime_window.open_saved_anime` | `:193` | 🆕 abrir un anime **de la biblioteca** | ✅ |
| **11** | `anime_window.__repair_to_target_provider` | `:600` | 🆕 localizar el anime en el proveedor destino | ✅ |
| **12** | `anime_window.__confirm_and_migrate` | `:683` | 🆕 migrar la fila + mover/bajar pósters | ✅ |
| **13** | `utilsButtons.SavedAnimeSearch.search` | `:165` | 🆕 búsqueda web que completa a la local | ✅ |

Más **dos `ThreadPoolExecutor(max_workers=8)`** para pósters:

| Dónde | Línea |
|---|---|
| `utils.download_animes_poster` | `:113` |
| `utils.download_images_progress` | `:168` |

> 🆕 **Los hilos #5 y #9 son antiguos que se arreglaron**, no nuevos: `recentAnimes` ya tenía hilo pero
> pintaba desde él, y `searchAnimes.__on_anime_click` **no tenía hilo** —hacía la petición en el hilo
> de Tkinter y la ventana se congelaba—. Los dos pasan ahora por `after(0, …)`.

Todos los hilos son **daemon**: al cerrar la ventana mueren sin limpieza. ✅ Verificado: la app se
cierra sin colgarse.

---

## 2. Qué corre en qué hilo

| Operación | Hilo | Anclaje |
|---|---|---|
| `mainloop()` y todos los callbacks de widget | 🖥️ UI | `app.py:14` |
| Animación del GIF (`after(100, …)`) | 🖥️ UI | `main_window.py:471-474`, `searchAnimes.py:198-202` |
| Carga inicial de la BD (`load_animes`) | 🧵 daemon | `main_window.py:483` → `530-543` |
| `get_recent_animes()` | 🧵 daemon | `main_window.py:484` |
| Descarga de pósters de recientes | ⚙️ pool (8) | `utils.py:168` |
| Precarga de fichas de recientes | 🧵 daemon | `main_window.py:502-528` |
| Clic en anime **desde recientes** | 🧵 daemon → `after(0,…)` ✅ | `recentAnimes.py:105-114` |
| Clic en anime **desde las 4 vistas de estado** | 🧵 daemon → `after(0,…)` ✅ 🆕 | `open_saved_anime` (`anime_window.py:145-193`) |
| Clic en anime **desde el buscador** | 🧵 daemon → `after(0,…)` ✅ 🆕 | `searchAnimes.py:363-382` |
| Búsquedas del buscador | 🧵 daemon | `searchAnimes.py:206-216` |
| Búsqueda dentro de las vistas de estado | 🖥️ UI (local) + 🧵 daemon (web) → `after(0,…)` ✅ 🆕 | `utilsButtons.py:137-165` |
| **Servidores de un episodio** | 🖥️ **UI** ⚠️ | `anime_window.py:1116-1121` |
| Recarga de recientes al cambiar de proveedor | 🧵 daemon → `after(0,…)` | `main_window.py:392-426` ✅ |
| **Migrar una fila a otro proveedor** | 🧵 daemon → `after(0,…)` ✅ 🆕 | `anime_window.py:675-683` |
| Todas las escrituras de estado en BD | 🖥️ UI (desde callbacks) | `anime_window.py:830-903` |
| Descarga/borrado de pósters por estado | 🖥️ UI ⚠️ | `anime_window.py:835, 852, 872…` |
| **Mover/rebajar pósters al migrar** | 🧵 daemon ✅ 🆕 | `anime_window.py:685-709` |

> 🆕 **Tres de las cuatro filas ⚠️ del 2026-08-07 se han cerrado** con la columna `provider_id`: los
> clics de las vistas de estado y del buscador, y la búsqueda dentro de las vistas. La que **queda
> viva es la de los servidores de vídeo** (C5): sigue haciendo HTTP en el hilo de Tkinter.

---

## 3. Reglas para código nuevo

### ✅ SÍ

1. **Toda petición HTTP va en un hilo daemon.** Patrón de referencia: `recentAnimes.py:105-114`.
2. **Para volver al hilo de UI, usa `self.after(delay, callback)`.** Es lo que hacen las animaciones
   de GIF (`main_window.py:471-474`).
3. **Comprueba `widget.winfo_exists()` antes de tocar un widget desde un callback diferido.**
   El frame puede haberse destruido. Ejemplo bueno: `searchAnimes.py:198-202`.

   ```python
   def update_gif(frame=0):
       if self.__loading_frame and self.__loading_frame.winfo_exists() \
               and loading_image_label.winfo_exists():
           loading_image_label.configure(image=gif_frames[frame])
           self.after(100, update_gif, (frame + 1) % len(gif_frames))
   ```

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
| `main_window.py:530-543` | `progress_bar.set()` y `progress_label.configure()` |
| `main_window.py:486-488` | **`messagebox.showwarning`** |
| `main_window.py:491-494` | `progress_bar.set(0.9)`, `loading_frame.place_forget()` |
| `main_window.py:495` | `show_frame()` → construye **toda** la vista de recientes |
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
| `recentAnimes.__on_anime_click` | `:104-111` |
| `searchAnimes.__on_anime_click` | `:369-380` |
| `open_saved_anime` (las 4 vistas de estado) | `anime_window.py:151-165` |
| `__confirm_and_migrate._done` (reconstruye tras migrar) | `anime_window.py:657-673` |

> 🔴 **No fue una mejora cosmética: era un crash reproducible.** Construir la ficha desde el hilo
> secundario revienta con `invalid command name ...!searchbutton.!ctkcanvas` en cuanto la vista que se
> está destruyendo tenía un evento `<Configure>` encolado —lo tienen las cuatro vistas de estado, por
> su barra de búsqueda—, porque ese evento se atiende cuando el canvas ya no existe. El síntoma es un
> traceback en consola y la ficha a medio pintar.
>
> Reproducido y verificado en `test_crash_tk.py` (scratchpad de la sesión).

### C3 — Escritura concurrente en `recent_animes` 📖

`__preload_recent_animes_info` (`main_window.py:502-528`) y `_load_and_show` (`recentAnimes.py:105-111`)
pueden escribir el mismo índice a la vez. El propio código lo justifica (`:507-513`): la asignación de
un elemento de lista es atómica bajo el GIL. **Es correcto** para este caso concreto.

> ✅ **Mitigado desde el 2026-08-06** por el contador de generación `__recent_animes_generation`
> (`main_window.py:78`). Al cambiar de proveedor, `self.recent_animes` pasa a ser **otra lista** y los
> índices de la precarga en vuelo dejan de significar nada; la precarga comprueba su generación antes
> de escribir (`:517-519`, `:525`) y aborta si ha caducado. Lo que sigue sin cubrirse es la carrera
> original entre precarga y clic **dentro de la misma generación**, que es la benigna.

### C4 — El guard antidoble-búsqueda no funciona ✅

```python
# searchAnimes.py:206-210 y :212-216 y :335-339
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

`anime_window.py:1116-1121` llama a `get_anime_episode_servers` en el callback del botón. ✅ Con AnimeAV1
tarda ~0,2 s.

> ⚠️ **Corrección (2026-08-07).** La versión anterior decía que «si AnimeAV1 falla y entra el fallback
> a AnimeFLV, se suman los timeouts de ambos proveedores». **Es falso desde el 2026-07-30**: esa
> llamada pasa `strict=True` y `provider_id` explícito (`anime_window.py:1116-1121`), justo para que
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

📖 Aparece **6 veces**, siempre justo después de `clear_frame()` y **siempre en el hilo de UI**:

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

📖 Hay **10** usos de `.after(...)` (✅ recontados el 2026-08-16; eran 4). Los **seis nuevos** son todos
del patrón bueno — hilo daemon → `after(0, …)` — y ya son la **mayoría**:

| Dónde | Para qué | Estado |
|---|---|---|
| `main_window.py:407` | devolver el resultado de la recarga de recientes al hilo de UI | ✅ **el patrón de referencia** |
| `main_window.py:474` | animar el GIF de carga | ✅ correcto |
| `searchAnimes.py:202` | animar el GIF de búsqueda | ✅ correcto, con `winfo_exists()` |
| 🆕 `recentAnimes.py:111` | pintar la ficha tras la petición | ✅ |
| 🆕 `searchAnimes.py:380` | pintar la ficha de un resultado de búsqueda | ✅ |
| 🆕 `anime_window.py:191` | pintar la ficha de un anime guardado | ✅ |
| 🆕 `anime_window.py:598` | abrir el diálogo tras localizar el anime en otro proveedor | ✅ |
| 🆕 `anime_window.py:680` | repintar la ficha tras migrar la fila | ✅ |
| 🆕 `utilsButtons.py:163` | añadir a la rejilla lo que aporte la búsqueda web | ✅ |
| `utils.py:51` (`update_gif`) | — | ⚠️ **código muerto y roto** |

> ✅ **El patrón ha dejado de ser la excepción.** En 2026-08-07 había **un** sitio que devolvía trabajo
> al hilo de UI correctamente; hoy hay **siete**. La regla operativa que los siete comparten:
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

La función suelta `update_gif` de `utils.py:48-51` haría
`root.after(100, update_gif, frame)`, pasando `frame` como primer argumento (`label`). **No tiene
llamantes en `src/`.** Cada pantalla define su propia `update_gif` local, correcta.

---

## 7. Ciclo de vida al cerrar

📖 No hay `protocol("WM_DELETE_WINDOW", …)` ni `join()` de ningún hilo. Al cerrar la ventana:

- Los hilos daemon mueren de golpe. Una descarga de póster a medias puede dejar un JPEG truncado
  en disco. ⚠️ No verificado.
- No hay `commit` pendiente que perder: `SqlUtils` hace `commit()` y `close()` en cada operación
  (`sqlite.py:16-46`).
- ✅ Verificado: arrancar la app y cerrarla **no modifica** `DB_Animes.db`.
