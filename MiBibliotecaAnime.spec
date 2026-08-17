# -*- mode: python ; coding: utf-8 -*-

APP_VERSION = "0.2.1"

block_cipher = None

a = Analysis(
    ['src/app.py'],
    pathex=['src'],
    binaries=[],
    datas=[
        ('resources/images/utils', 'resources/images/utils')
    ],
    hiddenimports=[
        'APIs.animeflv.animeflv',
        'APIs.animeav1.animeav1',
        'APIs.jkanime.jkanime',
        'APIs.common.animeProviderMgr',
        'APIs.common.models',
        'dataPersistence.animesPersistence',
        'dataPersistence.userPersistence',
        'gui.sidebarButtons.favouriteAnimes.favouriteAnimes',
        'gui.sidebarButtons.finishedAnimes.finishedAnimes',
        'gui.sidebarButtons.pendingAnimes.pendingAnimes',
        'gui.sidebarButtons.recentAnimes.recentAnimes',
        'gui.sidebarButtons.searchAnimes.searchAnimes',
        'gui.sidebarButtons.watchingAnimes.watchingAnimes',
        'gui.anime_window',
        'gui.main_window',
        'utils.buttons.utilsButtons',
        'utils.db.sqlite',
        'utils.utils'
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
import os
import shutil

_dist_dir = os.path.join(DISTPATH, f'MiBibliotecaAnime_v{APP_VERSION}')
for _legal_file in ('LICENSE', 'LEEME.txt', 'THIRD-PARTY-NOTICES.txt'):
    shutil.copy(_legal_file, _dist_dir)
    print(f'Copiado junto al ejecutable: {_legal_file}')
