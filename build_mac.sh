#!/bin/bash
echo "Checking dependencies..."
pip3 install -r requirements.txt 2>/dev/null || echo "⚠ pip install skipped (offline or already installed)"
pip3 install pyinstaller 2>/dev/null || echo "⚠ pyinstaller check skipped"

echo "Cleaning previous builds..."
rm -rf build dist

echo "Building executable for macOS..."
# Use ':' as separator for data on macOS/Linux
pyinstaller --noconfirm --windowed --name "AniManga_Downloader" --icon "icona.icns" --add-data "static:static" --hidden-import webview app.py

echo "Applying macOS fixes..."
# Inserisce la versione minima di macOS (evita l'icona con il divieto)
plutil -insert LSMinimumSystemVersion -string 10.13.0 dist/AniManga_Downloader.app/Contents/Info.plist || true
# Rimuove la quarantena di sicurezza e ri-firma l'app
xattr -cr dist/AniManga_Downloader.app || true
codesign --force --deep -s - dist/AniManga_Downloader.app || true
touch dist/AniManga_Downloader.app

echo "Build complete! You can find 'AniManga_Downloader.app' in the 'dist' folder."
