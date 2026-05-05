#!/bin/bash
echo "Installing dependencies..."
pip3 install -r requirements.txt
pip3 install pyinstaller

echo "Cleaning previous builds..."
rm -rf build dist *.spec

echo "Building executable for macOS..."
# Use ':' as separator for data on macOS/Linux
pyinstaller --noconfirm --windowed --name "Universal_Downloader" --icon "icona.icns" --add-data "static:static" --hidden-import webview app.py

echo "Applying macOS fixes..."
# Inserisce la versione minima di macOS (evita l'icona con il divieto)
plutil -insert LSMinimumSystemVersion -string 10.13.0 dist/Universal_Downloader.app/Contents/Info.plist || true
# Rimuove la quarantena di sicurezza e ri-firma l'app
xattr -cr dist/Universal_Downloader.app || true
codesign --force --deep -s - dist/Universal_Downloader.app || true
touch dist/Universal_Downloader.app

echo "Build complete! You can find 'Universal_Downloader.app' in the 'dist' folder."
