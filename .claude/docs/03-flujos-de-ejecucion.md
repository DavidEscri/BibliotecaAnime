# 03 — Flujos de ejecución

| | |
|---|---|
| **Fecha** | 2026-08-16 · **Commit** `a3d4331` (2026-08-17, rama `main`) · árbol **limpio** |
| **Última revisión** | 2026-08-16 (**columna `provider_id`**): §3 pasa de 2 caminos a **3, todos asíncronos**; **flujo 10 nuevo** (migrar una fila a otro proveedor); anclas de `anime_window.py` reubicadas tras crecer a 1 155 líneas |
| **Cubre** | `main_window.py`, `anime_window.py`, `recentAnimes.py`, `searchAnimes.py`, las 4 vistas de estado, `animeProviderMgr.py`, `animesPersistence.py`, `utils.py` |

Procedencia: ✅ verificado en ejecución · 📖 leído en código · ⚠️ sin verificar.
**Convención de hilos**: 🖥️ = hilo de Tkinter (UI) · 🧵 = hilo daemon · ⚙️ = worker del `ThreadPoolExecutor`.

---

## 1. Arranque y pantalla de carga

✅ Verificado: la app arranca, abre la ventana «Mi Biblioteca de Anime» y muestra los recientes sin
traceback.

```mermaid
sequenceDiagram
    participant U as Usuario
    participant APP as 🖥️ app.py
    participant MW as 🖥️ MainWindow
    participant T as 🧵 hilo daemon
    participant P as AnimesPersistence
    participant MGR as AnimeProviderManager
    participant NET as animeav1.com
    participant FS as resources/images/recent_animes

    U->>APP: python src/app.py
    APP->>MW: MainWindow()
    MW->>MW: __config_main_window() :100-111
    MW->>MW: __config_main_frames() :113-116
    MW->>MGR: register(AnimeAV1, default=True) :47
    MW->>MGR: register(JKAnime) :48
    MW->>MGR: register(AnimeFLV) :49
    MW->>MW: __registry_default_provider_id = get_default_provider_id() :65-66
    MW->>MW: __apply_saved_provider_preference() :68
    MW->>MW: load_sidebar_buttons() :154-238
    MW->>MW: show_loading_screen() :440
    MW->>MW: sidebar_frame.grid_forget() :441
    Note over MW: GIF + barra a 0 %#59; update_gif se reprograma con self.after(100,...) :474
    MW->>T: Thread(download_images_and_show_animes).start() :479
    APP->>MW: mainloop()

    T->>P: load_animes() :483 → start() :265
    P-->>T: favourite/finished/watching/pending
    Note over T: progreso 10→40 % (:530-543)<br/>⚠️ progress_bar.set() desde hilo daemon
    T->>MGR: get_recent_animes() :484
    MGR->>NET: GET https://animeav1.com
    NET-->>MGR: HTML
    MGR-->>T: List[AnimeInfo] (20 elementos ✅)

    alt lista vacía
        T->>U: messagebox.showwarning(...) :486-488
        T->>MW: __recent_animes_button.show_frame() :489
    else lista con datos
        T->>T: progress_bar.set(0.9) :491
        T->>FS: download_images_progress(...) :493
        T->>MW: loading_frame.place_forget() :494
        T->>MW: __recent_animes_button.show_frame() :495
        T->>T: Thread(__preload_recent_animes_info).start() :499-500
    end
```

**Notas ancladas**

- `show_frame()` de `RecentAnimeButton` (`recentAnimes.py:29-34`) **revela la sidebar** con
  `sidebar_frame.grid(...)` (`:31`) antes de pintar. Es el único sitio donde reaparece.
- 📖 Los `progress_bar.set()` / `configure()` de `load_animes` (`main_window.py:530-543`) y el
  `messagebox.showwarning` (`:486`) corren en **hilo daemon** ([07 §4](07-concurrencia-e-hilos.md)).
- 🆕 El paso `__registry_default_provider_id` (`:65-66`) va **antes** de aplicar la preferencia
  guardada, y no es cosmético: `__apply_saved_provider_preference()` llama a `set_default()`, que lo
  pisaría. Es la referencia contra la que se mide si el desplegable está desviado
  ([13 §8](13-selector-de-proveedor.md)).
- ✅ El arranque **no escribe** en la BD: el `LastWriteTime` de `DB_Animes.db` no cambió.

---

## 2. Precarga de la info de los recientes

```mermaid
sequenceDiagram
    participant T as 🧵 daemon (__preload_recent_animes_info)
    participant MGR as AnimeProviderManager
    participant NET as animeav1.com
    participant ST as MainWindow.recent_animes

    loop por cada anime de recent_animes  (:515-526)
        T->>ST: ¿synopsis/genres/episodes ya rellenos? :521
        alt ya precargado
            T->>T: continue :522
        else
            T->>MGR: get_anime_info(anime.id) :523
            MGR->>NET: GET /media/{slug}  (3 intentos, timeout 5)
            NET-->>MGR: HTML con payload SvelteKit
            MGR-->>T: AnimeInfo completo
            T->>ST: recent_animes[index] = anime_info :526
        end
    end
```

📖 `main_window.py:502-528`. El código justifica la ausencia de `Lock` (`:507-513`): asignar un
elemento de lista es atómico en CPython. ✅ Con AnimeAV1 cada `get_anime_info` tarda ~0,5 s → los 20
recientes ≈ 10 s de precarga en serie.

---

## 3. Clic en un anime → ficha de detalle

Hay **tres** caminos, según la vista. 🆕 Desde el 2026-08-16 los tres son **asíncronos** y los tres
vuelven al hilo de Tkinter con `after(0, …)`; lo que cambia es **cómo se decide el proveedor**.

| Vista | Proveedor | Por qué |
|---|---|---|
| **3a** Recientes | el que trajo la portada (`anime_clicked.provider_id`) | el slug es suyo |
| **3b** Las 4 de estado | `provider_for_saved_anime()` — puede re-resolver por título | el slug es del proveedor que **guardó la fila** |
| **3c** Buscador | el que sirvió el resultado | el slug es de **ese** sitio |

### 3a. Desde «Animes recientes»

```mermaid
sequenceDiagram
    participant U as Usuario
    participant V as 🖥️ RecentAnimeButton
    participant T as 🧵 daemon (_load_and_show)
    participant MGR as AnimeProviderManager
    participant AW as AnimeWindowViewer

    U->>V: clic en el póster  (bind :70)
    V->>V: localizar índice en recent_animes :83
    alt ya precargado (synopsis/genres/episodes != None)
        V->>AW: AnimeWindowViewer(mw, anime_clicked).display_anime_info() :117-118
        Note over V,AW: el provider_id sale del propio AnimeInfo (lo estampó el manager)
    else falta info
        V->>V: cursor="watch"#59; update_idletasks() :86-87
        V->>T: Thread(_load_and_show).start() :114
        T->>MGR: get_anime_info_with_provider(id, provider_id=anime_clicked.provider_id) :108-109
        MGR-->>T: (AnimeInfo | None, AnimeProviderId | None)
        T->>V: after(0, _show, anime_info, provider_id) :111
        V->>V: 🖥️ winfo_exists()#59; cursor="" :92-94
        alt None → todos los proveedores fallaron
            V->>U: show_anime_info_error(anime_id) y return
        else AnimeInfo
            V->>V: recent_animes[index] = anime_info
            V->>AW: display_anime_info() :102-103
        end
    end
```

> ✅ **Corregido en `1bfdf0f`** (2026-07-30) el caso `None`, que antes caía de vuelta al objeto obsoleto
> de `recent_animes` y petaba. 🆕 **Corregido el 2026-08-16** que el repintado ocurría en el hilo
> daemon: ahora vuelve con `after(0, …)` ([07 C2](07-concurrencia-e-hilos.md)).

### 3b. Desde favoritos / finalizados / viendo / pendientes 🆕

📖 `open_saved_anime()` (`anime_window.py:108-193`). Las cuatro vistas se limitan a llamarlo.

```mermaid
sequenceDiagram
    participant U as Usuario
    participant V as 🖥️ vista de estado
    participant MW as MainWindow
    participant T as 🧵 daemon (_load_and_show)
    participant MGR as AnimeProviderManager
    participant AW as AnimeWindowViewer

    U->>V: clic en el póster
    V->>MW: open_saved_anime(main_window, anime_id) :142
    MW->>MW: anime_record = get_anime_by_anime_id(anime_id) :142
    MW->>MW: provider_id, hay_desviación = provider_for_saved_anime(record.provider_id) :143
    MW->>MW: cursor="watch"#59; update_idletasks() :145-149
    MW->>T: Thread(_load_and_show).start() :193
    alt hay desviación (el desplegable difiere de la referencia)
        T->>MGR: resolve_anime_in_provider(referencia, provider_id) :178
        Note over T,MGR: 2 peticiones: buscar por título + traer la ficha
        alt resuelto
            MGR-->>T: AnimeInfo del proveedor elegido (OTRO slug)
        else no lo tiene
            T->>T: print y sigue por la vía normal :185-186
        end
    end
    opt no se resolvió
        T->>MGR: get_anime_info_with_provider(anime_id, provider_id=…) :189
    end
    T->>MW: after(0, _show, anime_info, served_by) :191
    MW->>AW: AnimeWindowViewer(mw, anime_info, served_by, anime_record=anime_record) :164-165
```

🔴 **El `anime_record=` del último paso no es opcional.** Con el desplegable desviado, `anime_info.id`
es el slug de **otro** sitio; sin la fila, la ficha congelaría la identidad de persistencia sobre ese
slug ajeno, se mostraría como no guardada y el primer botón de estado insertaría una **fila
duplicada**. Es la [trampa 21](10-invariantes-y-trampas.md), y ocurrió de verdad durante la fase 4.

⚠️ Cuando el proveedor elegido **no tiene** el anime no se bloquea al usuario: se sigue por la vía
normal y la ficha muestra quién lo ha servido de verdad.

### 3c. Desde el buscador 🆕

📖 `searchAnimes.py:344-382`. Igual que 3a en estructura, pero **arrastrando el `provider_id` del
resultado** desde el `bind` del póster (`:254-259`):

```python
img_label.bind("<Button-1>",
               lambda e, anime_id=anime.id, provider_id=anime.provider_id:
               self.__on_anime_click(anime_id, provider_id))
```

Sin eso se le pediría al predeterminado un slug que puede no ser suyo, **y habría que esperar sus
reintentos** —AnimeAV1 hace 3 con `sleep(1)`— antes de que entrase el fallback.

> No usa `open_saved_anime()` a propósito: un resultado de búsqueda no tiene por qué estar en la
> biblioteca, y aquí el proveedor **no se decide**, ya se sabe.

### 3d. Qué hace la ficha al mostrarse

```mermaid
sequenceDiagram
    participant AW as 🖥️ AnimeWindowViewer
    participant P as AnimesPersistence
    participant DB as DB_Animes.db
    participant FS as resources/images/*
    participant NET as red

    AW->>AW: display_anime_info() :323
    AW->>AW: main_window.clear_frame() :324
    AW->>P: get_anime_by_anime_id(persistence_anime_id) :329-330
    P->>DB: SELECT * FROM ANIMES WHERE anime_id = ?
    DB-->>P: fila | ninguna
    alt existe en BD
        AW->>AW: __is_saved = True#59; __saved_provider_id = record.provider_id :333-340
        opt la fila no declara proveedor 🆕
            AW->>P: update_anime_provider_id(id, persistence_provider_id) :342
            P->>DB: UPDATE ANIMES SET provider_id = ?
        end
        AW->>P: si len(episodes) difiere → update_anime_episodes() :346-347
        AW->>P: get_watched_episodes(id) :354
        AW->>AW: watched_status[ep.id] = ep.id in watched :355-356
    end
    AW->>AW: __display_anime_info() :326 → clear_frame() + time.sleep(0.1) :359-360
    AW->>FS: get_anime_image(__persistence_anime_info()) :378
    alt póster en alguna de las 6 carpetas de estado/caché
        FS-->>AW: CTkImage (195,275)
    else no está en ninguna
        AW->>NET: requests.get(anime.poster, timeout=10) (utils.py:195-196)
        NET-->>AW: CTkImage (195,275) con size= explícito
    end
    AW->>AW: __show_provider_label() :428 → hasta 3 líneas 🆕
    AW->>AW: __show_anime_status() :429 → __display_anime_status() :716
    AW->>AW: __show_anime_episodes() :770 → __display_episodes() :913
```

🆕 **El autorrelleno del proveedor ocurre aquí**, y **solo si la columna estaba a `NULL`**: si la fila
ya declara proveedor, cambiarlo es una decisión explícita del usuario (el botón «Actualizar a …»), no
algo que deba pasar por el hecho de abrir la ficha. Ver [04 §8](04-modelo-de-datos.md).

⚠️ El póster se pide con `__persistence_anime_info()`, no con `anime_info`: así sigue encontrando el
`{anime_id}.jpg` ya cacheado aunque se esté mostrando la ficha de otro proveedor.

---

## 4. Marcar / desmarcar un episodio

📖 `anime_window.py:1052-1105`. Es el flujo más delicado del proyecto.

```mermaid
flowchart TD
    A["Usuario mueve el switch<br/>__toggle_episode_switch(ep_id) :1052"] --> B{"¿ep_id en anime_info.episodes?<br/>:546-550"}
    B -->|no| B2["print error + return"]
    B -->|sí| C{"marking_as_watched<br/>= not watched_status[ep_id] :552-553"}

    C -->|marcar| D{"sort_descending? :557"}
    D -->|sí| D1["select() switches [index … fin]<br/>:558-562"]
    D -->|no| D2["select() switches [0 … index]<br/>:568-572"]

    C -->|desmarcar| E["deselect() SOLO este switch<br/>:564-566 / :573-576"]

    D1 --> F["bd_watched = get_watched_episodes(id) :579"]
    D2 --> F
    E --> F

    F --> G{"marking_as_watched?"}
    G -->|sí| H["episodes_up_to = todos los eps ≤ ep_id<br/>en orden ASCENDENTE real :586-589<br/>episodes_after = vistos en BD > ep_id :591<br/><b>merged = union</b> :592"]
    G -->|no| I["<b>merged = bd_watched - {ep_id}</b> :595"]

    H --> J["update_watched_episodes(id, merged) :597"]
    I --> J
    J --> K["_episodes_to_ranges(merged)<br/>animesPersistence.py:361"]
    K --> L["UPDATE ANIMES SET watched_episodes=?,<br/>last_watched_episode=max(merged) :363-371"]
```

**Reglas que hay que respetar** (✅ round-trip verificado):

1. **Marcar es acumulativo**: marca todos los episodios **anteriores en orden real ascendente**, no
   los anteriores en pantalla (`:586-589`). Es correcto tanto si la lista está ascendente como
   descendente.
2. **Los episodios posteriores ya vistos se conservan** (`:591`).
3. **Desmarcar es unitario**: solo se quita ese episodio (`:595`).
4. `update_watched_episodes` **devuelve `False` y no escribe nada si el anime no está en BD**
   (`animesPersistence.py:358`). ✅ Verificado. Es decir: **marcar episodios de un anime sin
   estado asignado no persiste nada**.

> ⚠️ Los pasos 1 y 2 usan `self.episode_switches`, que solo contiene los **widgets visibles** (25 como
> mucho, o los filtrados por búsqueda). Con la lista filtrada a un único episodio, `index` viene de
> `anime_info.episodes` (`:547`) pero se indexa `self.episode_switches[index]` (`:559-562`, `:566`) →
> posible `IndexError`. Camino leído en código, no reproducido.

---

## 5. Cambios de estado (los 4 botones)

📖 `anime_window.py:830-903` + `animesPersistence.py:594-684`. ✅ Máquina de estados verificada
completa sobre una copia de la BD.

```mermaid
sequenceDiagram
    participant U as Usuario
    participant AW as 🖥️ AnimeWindowViewer
    participant P as AnimesPersistence
    participant DB as DB_Animes.db
    participant FS as resources/images/{estado}/

    U->>AW: clic en «Añadir a viendo» (:747)
    AW->>AW: __confirm_save(WATCHING) :868  🆕
    AW->>P: update_anime_to_watching(__persistence_anime_info()) :871
    P->>P: _set_status(info, WATCHING, True) :542-544
    P->>DB: SELECT * WHERE anime_id = ? :626
    alt no existe → INSERT (:629-636)
        Note over DB: episodes se guarda INVERTIDO (to_db_dict :90)
    else ya existe → UPDATE (:638-682)
        Note over P,DB: 🆕 si provider_id estaba a NULL, se anota de paso (:643-644)
        Note over DB: is_watching=?, is_finished=0, is_pending=0
    end
    AW->>FS: download_anime_poster_by_status(WATCHING, info) :872
    Note over FS: GET anime.poster → resize (130,185)<br/>→ resources/images/watching/{id}.jpg
    AW->>AW: flags locales + __display_anime_status() :874-877
```

**Tabla de transiciones** ✅ verificada (líneas de `animesPersistence.py`):

| Acción | `fav` | `watch` | `fin` | `pend` | Línea |
|---|---|---|---|---|---|
| `update_anime_to_favourite` | **1** | = | = | = | `:531-533` |
| `update_anime_to_not_favourite` | **0** | = | = | = | `:535-540` |
| `update_anime_to_watching` | = | **1** | **0** | **0** | `:542-544` |
| `update_anime_to_not_watching` | = | **0** | = | `is_pending` previo | `:546-560` |
| `update_anime_to_finished` | = | **0** | **1** | **0** | `:562-564` |
| `update_anime_to_not_finished` | = | `is_watching` previo | **0** | **1** | `:566-581` |
| `update_anime_to_pending` | = | **0** | **0** | **1** | `:583-585` |
| `update_anime_to_not_pending` | = | = | = | **0** | `:587-592` |

⚠️ **`remove_from_*` no crea el anime**: usan `_update_flag` (`:605-612`), un `UPDATE` puro; si el
anime no está en BD, ✅ `update_sql` devuelve `True` sin haber tocado nada. `add_to_*` sí lo insertan
(`_set_status:628-636`).

⚠️ **El póster no se mueve de categoría.** Al hacer `remove_from_finished` el anime pasa a
*pendiente* en BD (`:566-581`) pero su póster se borra de `finished/` y **no** se crea en `pending/`
(`anime_window.py:859-865`) → la vista «pendientes» lo muestra en gris. Deuda B7 en
[12 §4](12-deuda-tecnica-y-roadmap.md).

---

## 6. Búsqueda por texto

```mermaid
sequenceDiagram
    participant U as Usuario
    participant SB as 🖥️ SearchButton (searchAnimes)
    participant T as 🧵 daemon
    participant MGR as AnimeProviderManager
    participant NET as animeav1.com
    participant FS as resources/images/search

    U->>SB: clic en «Buscar» :92-96
    SB->>SB: __search_anime(entry) :158
    Note over SB: guard :159-160 ⚠️ INEFECTIVO (__current_search_thread siempre None)
    SB->>SB: __show_loading_frame(text_entry=texto) :162
    SB->>SB: oculta loading/episodes/pagination :171-176
    SB->>SB: pinta GIF#59; update_gif con self.after(100,…) :196-202
    SB->>T: Thread(__search_anime_by_query, (texto, 1)).start() :205-209
    T->>MGR: search_animes_by_query(texto, 1) :218
    MGR->>NET: GET /catalogo?search=…&page=1
    NET-->>MGR: HTML
    MGR-->>T: (List[AnimeInfo], last_page)
    T->>T: __display_animes(...) :219
    T->>SB: save_anime_search(...) → main_window.last_search_instance :226
    T->>FS: download_animes_poster(search_images_path, animes) :229
    Note over FS: ⚙️ 8 workers#59; descarga las que faltan y PURGA las que ya no están en la lista
    T->>SB: pinta tarjetas + paginación :236-265  ⚠️ Tk desde hilo daemon
```

📖 `searchAnimes.py`. La condición `if text_entry == "" or text_entry is not None` (`:204`) equivale a
`text_entry is not None`: con texto (aunque sea vacío) va a búsqueda por query; con `None`, al filtro
por géneros.

---

## 7. Búsqueda por géneros + orden, con paginación

```mermaid
sequenceDiagram
    participant U as Usuario
    participant SB as 🖥️ SearchButton
    participant T as 🧵 daemon
    participant MGR as AnimeProviderManager
    participant AV1 as AnimeAV1

    U->>SB: marca géneros + orden, «Aplicar Filtros» :142-146
    SB->>SB: __apply_filters() :164
    SB->>SB: selected_genres = [g marcados] :167
    SB->>SB: __show_loading_frame() (text_entry=None) :168
    SB->>T: Thread(__search_anime_by_filter, (1,)).start() :211-215
    T->>MGR: search_animes_by_genres_and_order(genres, order, 1) :222
    MGR->>AV1: GET /catalogo?genre=accion&genre=…&page=1
    AV1->>AV1: __parse_anime_cards :242-276
    AV1->>AV1: __get_last_page (max de todos los ?page=N) :278-290
    AV1->>AV1: __apply_client_side_order :326-336
    AV1-->>T: ([AnimeInfo], last_page)
    T->>SB: __display_animes(...) → __display_pagination_buttons :265

    U->>SB: clic en «Siguiente »» :318-324
    SB->>SB: __load_page(page+1, text_query) :326
    SB->>T: Thread(__search_and_display_animes, (page, text_query)) :329-333
    T->>SB: __show_loading_frame(text_entry=text_query, page=page) :336
    Note over T,SB: vuelve a entrar en el flujo 6 o 7 según text_query
```

📖 Paginación: `:267-324`. `start_page = max(2, current_page)` (`:295`),
`end_page = min(start_page+3, last_page-1)` (`:296`); botones fijos «1» (`:286`) y `last_page`
(`:309`). ✅ `last_page` real observado: 50 (AnimeAV1) / 79 (AnimeFLV) para acción+aventura.

⚠️ Cuando todos los proveedores fallan, el wrapper devuelve `([], 1)` (`animeProviderMgr.py:262`).
El `1` es **una constante, no la última página real**: la paginación se colapsa a una sola página.

---

## 8. Obtención de servidores de un episodio

```mermaid
sequenceDiagram
    participant U as Usuario
    participant AW as 🖥️ AnimeWindowViewer
    participant MGR as AnimeProviderManager
    participant AV1 as AnimeAV1
    participant FLV as AnimeFLV
    participant BR as Navegador

    U->>AW: clic en el botón del episodio (EpisodeButton :304-311)
    AW->>AW: __toggle_servers_frame(ep, frames, row) :454
    alt el frame ya estaba abierto
        AW->>AW: destroy() + del :456-457
    else
        AW->>MGR: get_anime_episode_servers(ep.anime, ep.id) :459
        Note over AW: ⚠️ HTTP EN EL HILO DE UI → la ventana se congela
        MGR->>AV1: GET /media/{slug}/{n}
        AV1->>AV1: __extract_svelte_payload :228-240
        AV1->>AV1: regex embeds:…SUB:(\[…\]) :126
        AV1-->>MGR: [ServerInfo(server, url)] ✅ 5 servidores
        alt AnimeAV1 devuelve []
            MGR->>FLV: get_anime_episode_servers(...)
            Note over FLV: ✅ hoy devuelve [] — «var videos = {» ya no está
        end
        MGR-->>AW: List[ServerInfo] (o [] si todos fallan)
        AW->>AW: CTkSegmentedButton con los nombres :471-477
    end
    U->>AW: elige servidor → __play_video(url) :481
    AW->>BR: webbrowser.open(url)
```

⚠️ `server_button.set(None)` (`:476`) se ejecuta **antes** de asignar el `command` (`:477`), así que no
dispara la reproducción al construirse. Si `servers_info` viene vacío, el `CTkSegmentedButton` se crea
sin valores y **no hay ningún aviso al usuario**.

---

## 9. Descarga y purga de pósters

✅ Verificado end-to-end.

```mermaid
flowchart TD
    A["download_animes_poster(path, animes)<br/>utils.py:71"] --> B["os.makedirs si falta :72-73"]
    B --> C["current = set(os.listdir(path)) :75"]
    C --> D["to_download = animes cuyo {id}.jpg NO está :78-81"]
    D --> E{"¿hay algo que bajar?"}
    E -->|sí| F["⚙️ ThreadPoolExecutor(max_workers=8) :94<br/>GET anime.poster (timeout 10)<br/>PIL.resize((130,185)) → {id}.jpg :86-88"]
    E -->|no| G
    F --> G["anime_ids = {id}.jpg de la lista ACTUAL :98"]
    G --> H["por cada fichero de current que NO esté en anime_ids:<br/>os.remove :99-105"]
    H --> I["errores → print 'No se pudo borrar…' + continue :103-105"]
```

**Hechos verificados**

| Hecho | Resultado |
|---|---|
| Tamaño en disco | exactamente **130×185 JPEG** |
| Segunda llamada con los mismos animes | **0,00 s**, `mtime` intacto — no se re-descarga |
| Llamada con la lista reducida | los pósters sobrantes **se borran** |
| `download_images_progress` | idéntico + progreso `0.9 + 0.1·completados/total` (`:126`) |

⚠️ **La purga es agresiva**: `download_animes_poster` se usa también para `resources/images/search`
(`searchAnimes.py:229`), así que **cada búsqueda borra los pósters de la búsqueda anterior**.

⚠️ **La purga puede fallar en Windows.** ✅ `load_image` (`utils.py:181`) hace `Image.open(path)` sin
cerrar y PIL es perezoso: el fichero queda **abierto** mientras viva el `CTkImage` → `os.remove`
lanza `PermissionError`. Está capturado (`:103-105`), así que solo imprime. Además ✅ en la caché real
del usuario hay un huérfano `Chi.` (0 bytes) que `os.listdir` lista pero `os.remove` no puede borrar
(`WinError 2`) → **aviso en cada arranque**:

```
No se pudo borrar la imagen Chi.: [WinError 2] El sistema no puede encontrar el archivo
especificado: '…\resources\images\recent_animes\Chi.'
```

⚠️ El origen de ese fichero (un `anime.id` terminado en punto, que Windows no puede resolver) **no
está verificado**.

---

## 10. Migrar un anime guardado a otro proveedor 🆕 *(2026-08-16)*

📖 `anime_window.py:556-709`. Es el **único flujo que reescribe la identidad de una fila** de la
biblioteca, y por eso es el que más comprobaciones lleva.

```mermaid
sequenceDiagram
    participant U as Usuario
    participant AW as 🖥️ AnimeWindowViewer
    participant T as 🧵 daemon
    participant MGR as AnimeProviderManager
    participant P as AnimesPersistence
    participant FS as resources/images/*

    U->>AW: clic en «Actualizar a X» :509
    AW->>AW: target = __repair_target_provider_id() :565
    alt X ya sirve esta ficha
        AW->>AW: __confirm_and_migrate(self.anime_info, target) :571
        Note over AW: 0 peticiones: los datos ya están en pantalla
    else X es el seleccionado en la sidebar
        AW->>AW: cursor="watch" :574-575
        AW->>T: Thread(_resolve).start() :600
        T->>MGR: resolve_anime_in_provider(referencia, target) :596-597
        MGR-->>T: AnimeInfo | None
        T->>AW: after(0, _resolved, …) :598
        alt None
            AW->>U: showinfo «X no tiene este anime» :584-589
            Note over AW: el anime sigue guardado como estaba
        else resuelto
            AW->>AW: __confirm_and_migrate(resuelto, target) :591
        end
    end

    AW->>P: get_anime_by_anime_id(persistence_anime_id) :614
    alt la fila ya no existe
        AW->>U: showinfo «ya no está guardado» :617-620 y return
    end
    alt el anime_id destino ya lo ocupa otra fila
        AW->>U: showwarning «no se puede actualizar» :630-634 y return
        Note over AW,P: sin UNIQUE, el UPDATE dejaría DOS filas del mismo anime<br/>(trampa 28)
    end
    AW->>U: askyesno con los cambios + «se conservan N episodios vistos» :644-650
    U-->>AW: sí
    AW->>T: Thread(_migrate).start() :683
    T->>P: migrate_anime_identity(old_id, anime_info, target) :676-677
    P->>P: comprueba OTRA VEZ el destino ocupado
    P-->>T: True | False
    opt migrada
        T->>FS: __move_posters(...) :679 → renombrar, o descargar si no había :705-706
    end
    T->>AW: after(0, _done, migrated) :680
    AW->>AW: AnimeWindowViewer(mw, anime_info, target).display_anime_info() :673
```

**Tres decisiones que se ven en el diagrama y conviene no revertir**:

1. **La comprobación del destino ocupado está en las dos capas.** En la GUI para poder **explicarla**;
   en persistencia porque `migrate_anime_identity` es pública y no puede fiarse de quien la llame.
2. **Al terminar se construye una ficha nueva**, no se retocan atributos. La identidad de persistencia
   se congela en el constructor y el resto de la clase la da por inmutable; mutarla a mano sería
   pedir la [trampa 21](10-invariantes-y-trampas.md) otra vez.
3. **Un fallo moviendo pósters no revierte la migración.** El peor caso es un recuadro gris hasta la
   próxima descarga; revertir una escritura de BD correcta por una imagen sería peor.

---

## 11. Flujos documentados en otro sitio

- **Cambio de tema claro/oscuro** (`main_window.py:428-438`) → [06 §5](06-gui-y-vistas.md).
- **Semántica interna del fallback entre proveedores** → [05 §5](05-proveedores-y-scraping.md).
- **Serialización de `episodes` y `watched_episodes`** → [04 §4](04-modelo-de-datos.md).
- 🆕 **Buscar dentro de la biblioteca** (`SavedAnimeSearch`) → [06 §7](06-gui-y-vistas.md).
