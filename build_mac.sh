#!/bin/bash
echo "Checking dependencies..."
pip3 install -r requirements.txt 2>/dev/null || echo "⚠ pip install skipped (offline or already installed)"
pip3 install pyinstaller 2>/dev/null || echo "⚠ pyinstaller check skipped"

# ffmpeg è necessario per il download anime (mux degli stream HLS).
# Per un bundle PORTABILE serve un ffmpeg STATICO: scaricalo da
# https://evermeet.cx/ffmpeg ed esporta FFMPEG_BIN col suo percorso.
# Senza FFMPEG_BIN lo spec ripiega sul ffmpeg del PATH, che se è di Homebrew
# è collegato dinamicamente e NON funziona su un altro Mac.
if [ -z "$FFMPEG_BIN" ]; then
  echo "ℹ  FFMPEG_BIN non impostato: verrà usato il ffmpeg del PATH (potrebbe non essere portabile)."
  echo "   Per un .app distribuibile: export FFMPEG_BIN=/percorso/ffmpeg-statico"
fi

echo "Cleaning previous builds..."
rm -rf build dist

echo "Building executable for macOS (via AniManga_Downloader.spec)..."
pyinstaller --noconfirm AniManga_Downloader.spec

echo "Applying macOS fixes..."
# Inserisce la versione minima di macOS (evita l'icona con il divieto)
plutil -insert LSMinimumSystemVersion -string 10.13.0 dist/AniManga_Downloader.app/Contents/Info.plist || true
# Rimuove la quarantena di sicurezza e ri-firma l'app
xattr -cr dist/AniManga_Downloader.app || true
codesign --force --deep -s - dist/AniManga_Downloader.app || true
touch dist/AniManga_Downloader.app

echo "Build complete! You can find 'AniManga_Downloader.app' in the 'dist' folder."
