# -*- mode: python ; coding: utf-8 -*-
import os
import sys
import shutil
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

is_mac = sys.platform == "darwin"
icon_file = "icona.ico" if sys.platform.startswith("win") else "icona.icns"

# --- Binari esterni inclusi nel bundle ------------------------------------
# ffmpeg serve a yt-dlp per assemblare (mux) gli stream HLS degli anime in mp4.
#
# ATTENZIONE: per un bundle DISTRIBUIBILE serve un ffmpeg STATICO, senza
# dipendenze da librerie di sistema. Un ffmpeg installato con Homebrew è
# collegato dinamicamente e NON parte su un altro Mac. Imposta la variabile
# d'ambiente FFMPEG_BIN al percorso di un binario statico prima del build:
#   macOS   -> https://evermeet.cx/ffmpeg  (ffmpeg statico)
#   Windows -> https://www.gyan.dev/ffmpeg/builds  (ffmpeg.exe statico)
#   Linux   -> https://johnvansickle.com/ffmpeg
ffmpeg = os.environ.get("FFMPEG_BIN") or shutil.which("ffmpeg")
binaries = []
if ffmpeg and os.path.isfile(ffmpeg):
    binaries.append((ffmpeg, "."))
    print(f"[spec] ffmpeg incluso nel bundle: {ffmpeg}")
else:
    print("[spec] ATTENZIONE: ffmpeg non trovato -> il download anime NON funzionerà nel bundle.")

# yt-dlp è una libreria Python: includiamo tutti i suoi sottomoduli (extractor),
# così non serve un binario yt-dlp separato.
hidden = ['webview'] + collect_submodules('yt_dlp')
datas = [('static', 'static')] + collect_data_files('yt_dlp')


a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='AniManga_Downloader',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=[icon_file],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='AniManga_Downloader',
)
if is_mac:
    app = BUNDLE(
        coll,
        name='AniManga_Downloader.app',
        icon='icona.icns',
        bundle_identifier=None,
    )
