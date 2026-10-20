# -*- mode: python ; coding: utf-8 -*-

APP_VERSION = "0.2.1"

block_cipher = None

import os

# libmpv no está en el repositorio (pesa ~120 MB): se descarga aparte, como
# explica el README. Sin ella el .exe compilaría y abriría todo en el
# navegador, así que se para aquí en vez de distribuir un reproductor mudo.
_LIBMPV_DLL = 'vendor/libmpv-2.dll'
if not os.path.isfile(os.path.join(SPECPATH, _LIBMPV_DLL)):
    raise SystemExit(f'Falta {_LIBMPV_DLL}: descárgala como indica el README (paso 4).')

a = Analysis(
    ['src/app.py'],
    pathex=['src'],
    # Destino 'vendor', no '.': load_mpv() la busca en get_resource_path("vendor"),
    # que en el .exe es _internal/vendor.
    binaries=[
        (_LIBMPV_DLL, 'vendor')
    ],
    datas=[
        ('resources/images/utils', 'resources/images/utils')
    ],
    hiddenimports=[
        'APIs.animeflv.animeflv',
        'APIs.animeav1.animeav1',
        'APIs.jkanime.jkanime',
        'APIs.common.animeProviderMgr',
        'APIs.common.models',
        'APIs.resolvers.base',
        'APIs.resolvers.jkplayer',
        'APIs.resolvers.mp4upload',
        'APIs.resolvers.registry',
        'APIs.resolvers.zilla',
        'dataPersistence.animesPersistence',
        'dataPersistence.userPersistence',
        'gui.sidebarButtons.favouriteAnimes.favouriteAnimes',
        'gui.sidebarButtons.finishedAnimes.finishedAnimes',
        'gui.sidebarButtons.pendingAnimes.pendingAnimes',
        'gui.sidebarButtons.recentAnimes.recentAnimes',
        'gui.sidebarButtons.searchAnimes.searchAnimes',
        'gui.sidebarButtons.watchingAnimes.watchingAnimes',
        # Componentes compartidos y tokens visuales del rediseño. Entraron con las
        # fases 1 a 9 y hay que declararlos uno a uno: PyInstaller sigue los
        # imports desde `src/app.py`, pero este proyecto usa imports absolutos con
        # raíz en `src` y el análisis estático no siempre los resuelve, que es por
        # lo que las seis vistas llevan aquí desde siempre.
        'gui.theme',
        'gui.components.anime_row',
        'gui.components.empty_state',
        'gui.components.genre_chips',
        'gui.components.pager',
        'gui.components.poster_grid',
        'gui.components.rating_stars',
        'gui.components.resume_card',
        'gui.components.side_panel',
        'gui.components.sidebar',
        'gui.components.status_pill',
        'gui.components.video_player',
        'gui.components.view_header',
        'gui.anime_window',
        'gui.main_window',
        'utils.buttons.utilsButtons',
        'utils.db.sqlite',
        'utils.utils',
        # El binding de libmpv: video_player lo importa dentro de load_mpv(),
        # después de poner la DLL en la ruta, y el análisis estático no lo ve.
        'mpv'
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=f'MiBibliotecaAnime_v{APP_VERSION}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    icon='resources/images/utils/app_icon.ico'
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name=f'MiBibliotecaAnime_v{APP_VERSION}'
)

# --- Ficheros legales, al lado del .exe ---------------------------------------
# Se copian aquí, tras COLLECT, para que queden en el primer nivel de la
# carpeta distribuida, junto al ejecutable.
#
# La GPL-3.0 obliga a conservar los avisos de licencia al
# distribuir binarios y a indicar cómo obtener el código fuente
# correspondiente, y las licencias MIT/BSD/Apache/MPL de las dependencias
# exigen reproducir sus avisos de copyright en cualquier redistribución.
import shutil

_dist_dir = os.path.join(DISTPATH, f'MiBibliotecaAnime_v{APP_VERSION}')
for _legal_file in ('LICENSE', 'LEEME.txt', 'THIRD-PARTY-NOTICES.txt'):
    shutil.copy(_legal_file, _dist_dir)
    print(f'Copiado junto al ejecutable: {_legal_file}')
