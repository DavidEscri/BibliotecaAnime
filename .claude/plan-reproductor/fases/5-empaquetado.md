# Fase 5 — Empaquetado

| | |
|---|---|
| **Objetivo** | Que el `.exe` reproduzca. Declarar los módulos nuevos, meter la DLL de libmpv en `binaries` (📖 hoy vacío) y dejar la distribución en regla con la GPL |
| **Investigación** | §8 (fase 5) y §5 (la nota de licencia de libmpv) |
| **Estrena** | La sección `binaries` del `.spec`, que nunca se ha usado |
| **Toca** | `MiBibliotecaAnime.spec`, `requirements.txt`, `THIRD-PARTY-NOTICES.txt`, `LEEME.txt` (si hace falta), `vendor/` |
| **No toca** | `src/` — salvo, como mucho, un `os.add_dll_directory()` en el arranque si la DLL no se encuentra |
| **Riesgo** | Medio — 🔴 **compila bien y revienta en ejecución**. El error clásico de este proyecto |
| **Depende de** | Fases 1, 3 y 4 (todo lo que hay que declarar) |

---

## Antes de empezar

Lectura obligatoria, en este orden:

1. [`docs/11 §6`](../../docs/11-playbooks.md) — el playbook de empaquetar, y **cómo se regenera
   `THIRD-PARTY-NOTICES.txt`**.
2. [`docs/12 §7`](../../docs/12-deuda-tecnica-y-roadmap.md) — el estado de licencia y cumplimiento
   de la distribución. La app es **GPL-3.0-or-later** desde el 2026-08-17.
3. [trampas 18d y 18e](../../docs/10-invariantes-y-trampas.md) — las dos de PyInstaller, ambas
   silenciosas.
4. La bitácora de la **fase 0**: dónde quedó la DLL (punto de decisión 2) y su versión exacta.

**Trampas que van a morder en esta fase:**

- 🔴 **Todo módulo nuevo bajo `src/` va en `hiddenimports`**, o el `.exe` compila y revienta al
  arrancar. 📖 Hoy son **30** nombres, auditados con AST en las dos direcciones el 2026-08-21.
  Esta fase añade `APIs.resolvers.*` (6), `gui.components.video_player` y **`mpv`**.
- 🔴 **El destino `'.'` de `binaries` cae DENTRO de `_internal/`**, igual que `datas` — no junto al
  `.exe`. `python-mpv` hace `ctypes.CDLL("libmpv-2.dll")` y depende del orden de búsqueda de
  Windows. Si no la encuentra: `os.add_dll_directory(sys._MEIPASS)` al arrancar.
- 🔴 **PyInstaller ignora las carpetas vacías** (trampa 18d). Por eso las carpetas de pósters
  *parecían* obligatorias en `datas`.
- 🔴 **NO volver a meter `resources/DB` ni las carpetas de pósters en `datas`.** Hasta el 2026-08-17
  el `.exe` distribuía la biblioteca **y las preferencias** del desarrollador. `datas` contiene hoy
  **solo `resources/images/utils`** y así se queda.
- ⚠️ **`THIRD-PARTY-NOTICES.txt` caduca al tocar `requirements.txt`**, y esta fase lo toca.
- ⚠️ **libmpv es GPLv2+** en los builds estándar de Windows (LGPL solo con `--enable-lgpl`); el
  binding `python-mpv` es MIT. Compatible con GPL-3-or-later, pero **distribuir la DLL activa la
  §6 de la GPL**.

---

## Pasos

### Paso 5.1 — `requirements.txt` y la DLL

- Añadir `python-mpv` con la **versión exacta** que validó la fase 0.
- Colocar `libmpv-2.dll` donde decidió el punto de decisión 2: `vendor/` versionado, o fuera del
  repo con la descarga documentada en el `README.md` del proyecto. **Lo que se decidió, no lo que
  parezca mejor ahora**; si se cambia de idea, va a *Decisiones* con su motivo.
- Anotar en `ESTADO.md` la versión de libmpv **que se empaqueta**. Es lo que hará diagnosticable un
  fallo dentro de seis meses.

### Paso 5.2 — `hiddenimports` y `binaries`

- `hiddenimports`: `APIs.resolvers.base`, `.zilla`, `.jkplayer`, `.mp4upload`, `.registry`,
  `gui.components.video_player` y **`mpv`** (el binding no lo detecta el análisis estático).
- `binaries`: `('vendor/libmpv-2.dll', '.')`.
- **Auditar en las dos direcciones**, como el 2026-08-21: que cada nombre declarado resuelva a un
  fichero real de `src/`, y que ningún módulo de `src/` quede sin declarar (salvo `app.py`, que es
  el script de entrada). Anotar el recuento final — hoy son 30.
- ⚠️ Si `python-mpv` arrastra dependencias de datos propias, declararlas también.

### Paso 5.3 — Compilar y **reproducir desde el `.exe`**

- `pyinstaller MiBibliotecaAnime.spec`.
- 🔴 **Arrancar el `.exe` NO es la verificación.** La trampa de la DLL compila limpio y falla al
  reproducir. Hay que **abrir una ficha, pulsar un servidor y ver el vídeo**.
- Si `ctypes` no encuentra la DLL: `os.add_dll_directory(sys._MEIPASS)` en el arranque, con el
  `getattr(sys, '_MEIPASS', …)` que hace falta para que **siga funcionando ejecutado como script**.
- Comprobar de paso que el `.exe` sigue **sin llevar la biblioteca del desarrollador**: mirar el
  contenido de `_internal/resources/` — solo `images/utils`.
- ⚠️ Anotar el tamaño de `dist/` antes y después. Son ~40 MB más y el usuario debería saberlo.

### Paso 5.4 — Licencia y avisos

- ⚠️ **Regenerar `THIRD-PARTY-NOTICES.txt`** ([docs/11 §6](../../docs/11-playbooks.md)): ha cambiado
  `requirements.txt`, así que el fichero de hoy es incorrecto. Añadir `python-mpv` (MIT) y
  **libmpv** con su licencia real.
- 🔴 **§6 de la GPL**: distribuir la DLL de libmpv (GPLv2+) obliga a ofrecer el fuente
  correspondiente o una **oferta escrita**. Sumarlo a lo que ya cubren `LEEME.txt` y
  `THIRD-PARTY-NOTICES.txt`, que se copian junto al `.exe` en el bloque **posterior a `COLLECT`**
  (por la trampa 18e: los destinos de `datas` caen dentro de `_internal/`).
- Actualizar [`docs/12 §7`](../../docs/12-deuda-tecnica-y-roadmap.md) con el estado nuevo — o
  dejarlo anotado para la fase 6, que es la que documenta. **Decidirlo, no dejarlo a medias.**

---

## Terminado cuando

- [ ] `pyinstaller MiBibliotecaAnime.spec` termina **sin errores**.
- [ ] El `.exe` abre su ventana y **sigue vivo a los 40 s** (la prueba que ya se usó el 2026-08-21).
- [ ] 🔴 **Un episodio se reproduce desde el `.exe`**, no solo desde `python src/app.py`.
- [ ] `hiddenimports` auditado en las dos direcciones, con el recuento nuevo anotado.
- [ ] `_internal/resources/` contiene **solo** `images/utils` — ni BD ni pósters.
- [ ] `THIRD-PARTY-NOTICES.txt` regenerado e incluye libmpv con su licencia real.
- [ ] La §6 de la GPL está cubierta (oferta de fuentes o equivalente), y dicho dónde.
- [ ] `LEEME.txt` y `THIRD-PARTY-NOTICES.txt` siguen apareciendo **junto al `.exe`**, no dentro de
      `_internal/`.

## Verificación

`pyinstaller MiBibliotecaAnime.spec`, y sobre `dist/MiBibliotecaAnime_v<APP_VERSION>/`:

1. Arrancar el `.exe` y esperar a la portada.
2. Abrir una ficha, desplegar un episodio y **reproducir**. Ver y oír.
3. Probar **los dos formatos**: un HLS de AnimeAV1 y uno de JKAnime. Son dos rutas de decodificación
   distintas y la DLL empaquetada podría traer una y no la otra.
4. Probar un hoster no resuelto: tiene que **abrir el navegador** desde el `.exe` igual que desde el
   script.
5. Mirar el árbol de `dist/`: los ficheros legales fuera de `_internal/`, y `resources/` sin datos
   de usuario.

⚠️ **Probarlo en una carpeta distinta de la del repo**, o el `.exe` puede estar encontrando la DLL
por el `PATH` del desarrollador y no por la que empaquetó.

## Qué anotar en ESTADO.md

Versión de libmpv empaquetada · dónde vive la DLL · si hizo falta `add_dll_directory` · recuento
nuevo de `hiddenimports` · tamaño de `dist/` antes y después · qué se hizo con la §6 de la GPL · y
si el `.exe` **reprodujo de verdad** o solo arrancó.
