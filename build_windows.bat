@echo off
echo Installing dependencies...
pip install -r requirements.txt
pip install pyinstaller

echo Cleaning previous builds...
rmdir /s /q build
rmdir /s /q dist
del /q *.spec

echo Building executable for Windows...
REM Use ';' as separator for data on Windows
pyinstaller --noconfirm --windowed --name "Universal_Downloader" --icon "icona.ico" --add-data "static;static" --hidden-import webview app.py

echo Build complete! You can find the executable in the 'dist\Universal_Downloader' folder.
pause
