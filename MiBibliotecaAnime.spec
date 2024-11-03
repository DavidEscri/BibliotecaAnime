# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['src/app.py'],
    pathex=['src'],
    binaries=[],
    datas=[
        ('resources/DB', 'resources/DB'),
        ('resources/images/favorites', 'resources/images/favorites'),
        ('resources/images/recent_animes', 'resources/images/recent_animes'),
        ('resources/images/utils', 'resources/images/utils')
    ],
    hiddenimports=[
        'APIs.animeflv.animeflv',
        'gui.sidebarButtons.favoriteAnimes.favoriteAnimes',
        'gui.sidebarButtons.finishedAnimes.finishedAnimes',
        'gui.sidebarButtons.pendingAnimes.pendingAnimes',
        'gui.sidebarButtons.recentAnimes.recentAnimes',
        'gui.sidebarButtons.searchAnimes.searchAnimes',
        'gui.sidebarButtons.watchingAnimes.watchingAnimes',
        'gui.sidebarButtons.sidebarButton',
        'gui.anime_windows',
        'gui.main_window',
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
    name='MiBibliotecaAnime',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Cambia a True si deseas que el programa abra una ventana de consola
    icon='resources/images/utils/app_icon.ico'
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='MiBibliotecaAnime'
)
