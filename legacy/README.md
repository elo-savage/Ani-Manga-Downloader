# 🗄️ Legacy / Archivio

Questi file **non fanno parte dell'app** e non vengono importati né eseguiti da essa.
Sono versioni precedenti e materiale di sviluppo, tenuti solo come riferimento storico.

L'app viva è composta da 3 file nella root del progetto:
`app.py` (finestra + bridge pywebview) · `AniManga_Downloader.py` (motore anime + manga) · `static/index.html` (UI).

| File | Cos'è |
|------|-------|
| `Universal_Downloader.py` | Vecchio entry point/motore, sostituito da `AniManga_Downloader.py`. |
| `AM_DB_Funzionante.py` | Esperimento "script originali unificati" (pre-merge). |
| `AM_DB_Test.py` | Variante di test dello stesso esperimento. |
| `MDB_Latest.py` | Vecchio downloader manga standalone (usava `fpdf`), superato dalla classe `MangaDownloader`. |
| `debug_chapters.py` | Script di debug per capire cosa estrae lo scraper dei capitoli di MangaWorld. Utile solo in fase di sviluppo: `python3 legacy/debug_chapters.py <url_manga>`. |
| `Stitch Manga Ink Downloader/` | Mockup di design originale (DESIGN.md con i token, code.html, screen.png) da cui è nata la UI neo-brutalista. |

> ⚠️ Non modificare questi file pensando che influenzino l'app: non lo fanno.
