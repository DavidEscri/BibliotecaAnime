# Fase 1 — Cimientos

| | |
|---|---|
| **Objetivo** | Entender el punto de partida y dejar montado lo que las 8 fases siguientes dan por hecho: los tokens, la barra lateral nueva y la cabecera de vista |
| **Diseño visual** | [DISENO-VISUAL.html#lateral](../DISENO-VISUAL.html#lateral) — la barra en sus dos estados, y `#claro` para la paleta clara. Ábrelo en el navegador, **no** con `Read` |
| **Estrena** | `theme.py`, `Sidebar`, `ViewHeader`, caché de pósters a 248 × 372 |
| **Toca** | `src/gui/theme.py` (nuevo), `src/gui/components/` (nuevo), `src/gui/main_window.py`, `src/utils/utils.py`, `src/dataPersistence/userPersistence.py` |
| **No toca** | `APIs/`, `animesPersistence.py`, `anime_window.py`, las 6 vistas de sidebar |
| **Riesgo** | Medio — cambia el esqueleto de `MainWindow` |
| **Depende de** | Nada |

---

## Antes de empezar

Lectura obligatoria, en este orden:

1. [`docs/10-invariantes-y-trampas.md`](../../docs/10-invariantes-y-trampas.md) — las 28 siguen vigentes.
2. [`docs/06-gui-y-vistas.md`](../../docs/06-gui-y-vistas.md) — `MainWindow` como hub, ciclo de vida de una vista.
3. [`docs/13 §4`](../../docs/13-selector-de-proveedor.md) — `USER_SETTINGS` y por qué `DB_user.db` va aparte.
4. [`DISENO.md`](../DISENO.md) §1, §2, §3, §4 y §8.

Y leer entero `src/gui/main_window.py` (535 líneas) y `src/utils/buttons/utilsButtons.py`.

**Trampas que van a morder en esta fase:**

- La barra lateral **hoy mide 220 px, no 340**: `SidebarButton` se construye con
  `width=parent_frame.winfo_width()`, que vale 1 antes de mapear, así que el frame encoge hasta su
  contenido. El 224 del diseño es casi lo que ya hay; no es un ensanche.
- `create_sidebar_frame()` da `weight=1` a la **fila 8**, que es el espaciador que empuja el
  proveedor y la apariencia al fondo. Si se reordenan filas, eso se rompe en silencio
  (`main_window.py:169-172` lo comenta).
- `change_appearance_mode_event()` recorre los hijos del sidebar y **reconfigura colores a mano**
  con literales. Al pasar a tokens hay que rehacerlo o quedará peleándose con `theme.py`.

---

## Pasos

### Paso 1.1 — Orientación y rama

- `git status`, `git log --oneline -5`, `git branch --show-current`.
- Confirmar que la base es `4f9e429` en `develop`. Si no lo es, anotarlo en `ESTADO.md` y seguir.
- Crear la rama: `git switch -c feature/rediseno-ui`.
- Arrancar `python src/app.py`, comprobar que la app sube, y cerrarla. Es la foto del «antes».
- Anotar en `ESTADO.md`: rama creada, base real, y si la app arrancó.

### Paso 1.2 — `src/gui/theme.py`

Módulo nuevo con la cabecera obligatoria. Expone los tokens de [`DISENO.md`](../DISENO.md) §1 y §2
como constantes de clase, en tuplas `(claro, oscuro)`, más un helper para las fuentes:

```python
class Theme:
    BG = ("#F4F5F7", "#14161A")
    ...
    @staticmethod
    def font(size: int, bold: bool = False, mono: bool = False) -> ctk.CTkFont: ...
```

No se toca ninguna vista todavía. Al terminar el paso, `theme.py` existe y no lo usa nadie.

### Paso 1.3 — Caché de pósters a 248 × 372

En `src/utils/utils.py`: subir el tamaño con el que se **guardan** los JPG de `(130, 185)` a
`(248, 372)`. Cada vista seguirá pidiendo su `size=` al construir el `CTkImage`.

- ⚠️ Conservar el `size=` explícito en la rama de descarga desde red de `get_anime_image()`
  ([trampa 17](../../docs/10-invariantes-y-trampas.md)): sin él pinta a 20 × 20.
- Borrar una vez las 6 carpetas de `resources/images/` (`favourite`, `watching`, `finished`,
  `pending`, `recent_animes`, `search`). Están en `.gitignore` y se regeneran al arrancar.
- Verificar arrancando: los pósters vuelven a bajarse y se ven nítidos.

### Paso 1.4 — `Sidebar`

`src/gui/components/sidebar.py`. Sustituye a los 6 `SidebarButton` sueltos y a los controles del pie.

- 6 destinos con icono + etiqueta + **contador**. Los contadores salen de las listas que
  `MainWindow` ya cachea (`favourite_animes`, `watching_animes`, `finished_animes`,
  `pending_animes`) y de `len(recent_animes)`. Buscar no lleva contador.
- Nombres nuevos: **Nuevos lanzamientos**, Favoritos, Viendo, Pendientes, Finalizados, Buscar.
  Cierra el `# TODO:` de `main_window.py:32`.
- Estado activo: fondo `CARD` + barra de 2 px `ACCENT` a la izquierda.
- Plegado a 84 px con el botón de la esquina: icono solo y contador en globo.
- Persistir el estado plegado/desplegado: **miembro nuevo `SIDEBAR_COLLAPSED` en `UserSettingKey`**
  (`userPersistence.py:40`) más un par `get_sidebar_collapsed()` / `set_sidebar_collapsed()` copiando
  el patrón de `get_default_provider_id()`. ⚠️ `get_setting()` recibe el **enum**, no una cadena
  ([`DISENO.md`](../DISENO.md) §8). Sin migración: la tabla es clave/valor.
- El proveedor y su pin, y el selector de apariencia, se conservan **con el mismo comportamiento**:
  el desplegable cambia solo la sesión, el pin escribe en `DB_user.db`
  ([docs/13](../../docs/13-selector-de-proveedor.md)). Solo cambia su aspecto.
- Un método público para refrescar los contadores, que las fases siguientes llamarán al guardar o
  quitar un anime.

### Paso 1.5 — `ViewHeader` y cableado de `MainWindow`

- `src/gui/components/view_header.py`: título + subtítulo + zona de controles a la derecha, alto 80.
- En `main_window.py`: sustituir `load_sidebar_buttons()` por la `Sidebar` nueva, aplicar `BG` al
  `content_frame`, y rehacer `change_appearance_mode_event()` para que no reconfigure colores a
  mano — con tuplas `(claro, oscuro)` CustomTkinter cambia el tema solo.
- **Las 6 vistas siguen siendo las de hoy.** Solo cambian de sitio y de contenedor.

---

## Terminado cuando

- [ ] `theme.py` y `components/` existen, con cabecera de módulo correcta.
- [ ] La barra lateral nueva se ve, navega a las 6 vistas y muestra contadores correctos.
- [ ] Se pliega y se despliega, y el estado sobrevive a cerrar y reabrir la app.
- [ ] El proveedor, el pin y la apariencia siguen funcionando igual que antes.
- [ ] Los pósters se ven nítidos a 176 px.
- [ ] `git grep -n "TODO" -- src/` — comprobar que el de `main_window.py:32` ya no está y anotar
      cuántos quedan.

## Verificación

`python src/app.py`. Recorrer las 6 vistas, plegar y desplegar, cambiar de proveedor, cambiar de
apariencia claro↔oscuro, cerrar y reabrir. Si la ventana Tk no se puede abrir, cerrar la fase como
⚠️ **terminada sin verificar** y decirlo.

## Qué anotar en ESTADO.md

Rama creada · si la app arrancó · contadores correctos sí/no · cuántos `TODO` quedan en `src/` ·
cualquier decisión que se haya tenido que tomar sobre la marcha (van a la tabla de *Decisiones*).
