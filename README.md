# Universal Downloader

A cross-platform desktop application built with Python (Flask & pywebview) and a modern neo-brutalist user interface to download manga, anime, and other media.

## Prerequisites

- Python 3.8+
- [Git](https://git-scm.com/)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/elo-savage/Ani-Manga-Downloader.git
   cd Universal_Downloader
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the app locally

Run the following command to start the application:

```bash
python3 app.py
```

## Building Executables

You can create standalone executables that don't require Python to be installed on the target machine. We use `PyInstaller` for this.

### For macOS
Run the provided shell script from your Mac terminal:
```bash
chmod +x build_mac.sh
./build_mac.sh
```
The `.app` file will be generated in the `dist` folder.

### For Windows
You must run the build process **on a Windows machine** (or a Windows Virtual Machine). Double click the `build_windows.bat` file, or run it from the command prompt:
```cmd
build_windows.bat
```
The `.exe` file will be generated in the `dist` folder.

## Technologies Used
- **Backend:** Python, Flask
- **Desktop Window:** pywebview
- **Frontend:** HTML, CSS (Tailwind CSS / Custom Neo-Brutalist design), JavaScript
