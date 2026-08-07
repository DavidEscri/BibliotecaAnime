# 07 — Concurrencia e hilos

| | |
|---|---|
| **Fecha** | 2026-08-07 · **Commit** `18311e3` · árbol **limpio** |
| **Última revisión** | 2026-08-07 (**auditoría**): inventario de hilos a **8** (eran 6) y de `after()` a **4** (eran 3); **C5 corregida** — la llamada de servidores usa `strict=True`, así que no hay fallback que sume timeouts |
| **Cubre** | `src/gui/main_window.py`, `src/gui/anime_window.py`, `src/gui/sidebarButtons/**`, `src/utils/utils.py` |

Procedencia: ✅ verificado en ejecución · 📖 leído en código · ⚠️ sin verificar.

> **Aviso de honestidad**: este documento describe **lo que hay**, no lo que debería haber. Varias de
> las prácticas listadas violan la regla «nada de Tk fuera del hilo de UI». Se documentan porque
> están en producción y funcionan en la práctica, no porque sean correctas. **No las repliques en
> código nuevo.**

---

## 1. Inventario de hilos

📖 Todos los `threading.Thread` del proyecto:

✅ Recontados el 2026-08-07: son **8**, no 6. Los dos nuevos (#1 y #2) llegaron con el selector de
proveedor el 2026-08-06.

| # | Dónde | Línea | Objetivo | Daemon |
|---|---|---|---|---|
| 1 | `main_window.__reload_recent_animes` | `:329-330` | `__reload_recent_animes_worker` — recarga al cambiar de proveedor | sí |
| 2 | `main_window.__on_recent_animes_reloaded` | `:365-366` | `__preload_recent_animes_info` tras la recarga | sí |
| 3 | `main_window.show_loading_screen` | `:419` | `download_images_and_show_animes` | sí |
| 4 | `main_window.download_images_and_show_animes` | `:439-440` | `__preload_recent_animes_info` | sí |
| 5 | `recentAnimes.__on_anime_click` | `:105` | `_load_and_show` (ficha) | sí |
| 6 | `searchAnimes.__show_loading_frame` | `:205-209` | `__search_anime_by_query` | sí |
| 7 | `searchAnimes.__show_loading_frame` | `:211-215` | `__search_anime_by_filter` | sí |
| 8 | `searchAnimes.__load_page` | `:329-333` | `__search_and_display_animes` | sí |

Más **dos `ThreadPoolExecutor(max_workers=8)`** para pósters:

| Dónde | Línea |
|---|---|
| `utils.download_animes_poster` | `:94` |
| `utils.download_images_progress` | `:149` |

Todos los hilos son **daemon**: al cerrar la ventana mueren sin limpieza. ✅ Verificado: la app se
cierra sin colgarse.

---

## 2. Qué corre en qué hilo

| Operación | Hilo | Anclaje |
|---|---|---|
| `mainloop()` y todos los callbacks de widget | 🖥️ UI | `app.py:14` |
| Animación del GIF (`after(100, …)`) | 🖥️ UI | `main_window.py:411-414`, `searchAnimes.py:197-201` |
| Carga inicial de la BD (`load_animes`) | 🧵 daemon | `main_window.py:423` → `470-483` |
| `get_recent_animes()` | 🧵 daemon | `main_window.py:424` |
| Descarga de pósters de recientes | ⚙️ pool (8) | `utils.py:149` |
| Precarga de fichas de recientes | 🧵 daemon | `main_window.py:442-468` |
| Clic en anime **desde recientes** | 🧵 daemon | `recentAnimes.py:105` |
| Clic en anime **desde las otras vistas** | 🖥️ **UI** ⚠️ | `favouriteAnimes.py:131` y homólogos |
| Búsquedas del buscador | 🧵 daemon | `searchAnimes.py:205-215` |
| Búsqueda dentro de las vistas de estado | 🖥️ **UI** ⚠️ | `favouriteAnimes.py:82` y homólogos |
| **Servidores de un episodio** | 🖥️ **UI** ⚠️ | `anime_window.py:608` |
| Recarga de recientes al cambiar de proveedor | 🧵 daemon → `after(0,…)` | `main_window.py:332-366` ✅ |
| Todas las escrituras en BD | 🖥️ UI (desde callbacks) | `anime_window.py:330-395` |
| Descarga/borrado de pósters por estado | 🖥️ UI ⚠️ | `anime_window.py:333, 348, 366…` |

---

## 3. Reglas para código nuevo

### ✅ SÍ

1. **Toda petición HTTP va en un hilo daemon.** Patrón de referencia: `recentAnimes.py:90-102`.
2. **Para volver al hilo de UI, usa `self.after(delay, callback)`.** Es lo que hacen las animaciones
   de GIF (`main_window.py:411-414`).
3. **Comprueba `widget.winfo_exists()` antes de tocar un widget desde un callback diferido.**
   El frame puede haberse destruido. Ejemplo bueno: `searchAnimes.py:197-201`.

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
| `main_window.py:470-483` | `progress_bar.set()` y `progress_label.configure()` |
| `main_window.py:426-428` | **`messagebox.showwarning`** |
| `main_window.py:431-434` | `progress_bar.set(0.9)`, `loading_frame.place_forget()` |
| `main_window.py:435` | `show_frame()` → construye **toda** la vista de recientes |
| `utils.py:127-128` | `progress_bar.set()` desde **8 workers** del pool |
| `recentAnimes.py:97-99` | `configure(cursor="")` + construye la ficha entera |
| `searchAnimes.py:219-224` | `__display_animes` → crea decenas de widgets |

Tkinter **no es thread-safe**. ✅ En la práctica el arranque completo funciona sin traceback, pero es
suerte estructural, no garantía. ⚠️ No se ha observado ningún cuelgue, pero tampoco se ha hecho
*stress test*.

**Mitigación en `utils.py:143-145`**: el contador de progreso sí está protegido con `threading.Lock`
— pero el `Lock` protege el **contador**, no la llamada a Tk que hace dentro.

### C2 — `AnimeWindowViewer` construido desde dos hilos 📖

`recentAnimes.py:98-99` construye la ficha desde un daemon; las otras vistas la construyen desde UI.
Si el usuario cambia de vista mientras el hilo #3 está en vuelo, el `content_frame` ya se ha vaciado y
la ficha se pinta **encima de la vista nueva**. ⚠️ No reproducido.

### C3 — Escritura concurrente en `recent_animes` 📖

`__preload_recent_animes_info` (`main_window.py:442-468`) y `_load_and_show` (`recentAnimes.py:93`)
pueden escribir el mismo índice a la vez. El propio código lo justifica (`:447-453`): la asignación de
un elemento de lista es atómica bajo el GIL. **Es correcto** para este caso concreto.

> ✅ **Mitigado desde el 2026-08-06** por el contador de generación `__recent_animes_generation`
> (`main_window.py:72`). Al cambiar de proveedor, `self.recent_animes` pasa a ser **otra lista** y los
> índices de la precarga en vuelo dejan de significar nada; la precarga comprueba su generación antes
> de escribir (`:457-459`, `:465`) y aborta si ha caducado. Lo que sigue sin cubrirse es la carrera
> original entre precarga y clic **dentro de la misma generación**, que es la benigna.

### C4 — El guard antidoble-búsqueda no funciona ✅

```python
# searchAnimes.py:205-209 y :211-215 y :329-333
self.__current_search_thread = threading.Thread(...).start()   # ← .start() devuelve None
```

`Thread.start()` devuelve `None`, así que `__current_search_thread` **siempre vale `None`** y el
guard `if self.__current_search_thread and self.__current_search_thread.is_alive()`
(`:159-160`, `:165-166`, `:327-328`) **nunca bloquea nada**. Consecuencia: pulsar «Buscar» dos veces
seguidas lanza dos hilos que pintan sobre el mismo `content_frame`.

**Arreglo** (no aplicado — este trabajo es solo de documentación):

```python
t = threading.Thread(target=..., args=(...), daemon=True)
self.__current_search_thread = t
t.start()
```

### C5 — HTTP en el hilo de UI al abrir servidores 📖

`anime_window.py:608` llama a `get_anime_episode_servers` en el callback del botón. ✅ Con AnimeAV1
tarda ~0,2 s.

> ⚠️ **Corrección (2026-08-07).** La versión anterior decía que «si AnimeAV1 falla y entra el fallback
> a AnimeFLV, se suman los timeouts de ambos proveedores». **Es falso desde el 2026-07-30**: esa
> llamada pasa `strict=True` y `provider_id` explícito (`anime_window.py:608-613`), justo para que
> **no** haya fallback — el slug es del proveedor que sirvió la ficha y no significa nada en otro
> sitio. Con `strict=True`, `call_with_fallback` recorta a `providers_to_try[:1]`.
>
> La congelación sigue siendo real, pero acotada al timeout de **un solo** proveedor.

### C6 — La purga de imágenes compite con los widgets que las muestran ✅

`load_image` (`utils.py:181`) hace `Image.open(path)` **sin cerrar**; PIL carga de forma perezosa, así
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

📖 Hay **4** usos de `.after(...)` (✅ recontados el 2026-08-07; eran 3 antes del pin de proveedor):

| Dónde | Para qué | Estado |
|---|---|---|
| **`main_window.py:347`** | **devolver el resultado de la recarga de recientes al hilo de UI** | ✅ **el patrón que recomienda §3** |
| `main_window.py:414` | animar el GIF de carga | ✅ correcto |
| `searchAnimes.py:201` | animar el GIF de búsqueda | ✅ correcto, con `winfo_exists()` |
| `utils.py:51` (`update_gif`) | — | ⚠️ **código muerto y roto** |

> ✅ **`main_window.py:347` es el único sitio del proyecto que aplica bien la regla 2 de §3**: el hilo
> daemon (`__reload_recent_animes_worker`) no toca ni un widget; hace la red y entrega el resultado con
> `after(0, …)` a `__on_recent_animes_reloaded`, que ya corre en el hilo de Tkinter. **Cópialo** en vez
> de copiar el arranque, que es justo el contraejemplo de C1. Llegó con el selector de proveedor
> (2026-08-06) y su docstring lo dice explícitamente.

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
