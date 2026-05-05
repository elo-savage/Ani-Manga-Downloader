#!/bin/bash
echo "Installing dependencies..."
pip3 install -r requirements.txt
pip3 install pyinstaller

echo "Cleaning previous builds..."
rm -rf build dist *.spec

echo "Building executable for macOS..."
# Use ':' as separator for data on macOS/Linux
pyinstaller --noconfirm --windowed --name "Universal_Downloader" --add-data "static:static" app.py

echo "Build complete! You can find 'Universal_Downloader.app' in the 'dist' folder."
