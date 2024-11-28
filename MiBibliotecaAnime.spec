# -*- mode: python ; coding: utf-8 -*-

APP_VERSION = "0.9.1"

block_cipher = None

a = Analysis(
    ['src/app.py'],
    pathex=['src'],
    binaries=[],
    datas=[
        ('resources/DB', 'resources/DB'),
        ('resources/images/favourite', 'resources/images/favourite'),
        ('resources/images/finished', 'resources/images/finished'),
        ('resources/images/pending', 'resources/images/pending'),
        ('resources/images/watching', 'resources/images/watching'),
        ('resources/images/search', 'resources/images/search'),
        ('resources/images/recent_animes', 'resources/images/recent_animes'),
        ('resources/images/utils', 'resources/images/utils')
    ],
    hiddenimports=[
        'APIs.animeflv.animeflv',
        'dataPersistence.animesPersistence',
        'gui.sidebarButtons.favouriteAnimes.favouriteAnimes',
        'gui.sidebarButtons.finishedAnimes.finishedAnimes',
        'gui.sidebarButtons.pendingAnimes.pendingAnimes',
        'gui.sidebarButtons.recentAnimes.recentAnimes',
        'gui.sidebarButtons.searchAnimes.searchAnimes',
        'gui.sidebarButtons.watchingAnimes.watchingAnimes',
        'gui.sidebarButtons.sidebarButton',
        'gui.anime_windows',
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
