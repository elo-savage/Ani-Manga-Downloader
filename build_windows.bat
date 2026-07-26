@echo off
echo Installing dependencies...
pip install -r requirements.txt
pip install pyinstaller

echo Cleaning previous builds...
rmdir /s /q build
rmdir /s /q dist

REM ffmpeg e' necessario per il download anime (mux degli stream HLS).
REM Per un bundle PORTABILE serve un ffmpeg.exe STATICO: scaricalo da
REM https://www.gyan.dev/ffmpeg/builds ed imposta FFMPEG_BIN col suo percorso.
if "%FFMPEG_BIN%"=="" echo ATTENZIONE: FFMPEG_BIN non impostato. Imposta FFMPEG_BIN a un ffmpeg.exe statico per un bundle distribuibile.

echo Building executable for Windows (via AniManga_Downloader.spec)...
pyinstaller --noconfirm AniManga_Downloader.spec

echo Build complete! You can find the executable in the 'dist\AniManga_Downloader' folder.
pause
