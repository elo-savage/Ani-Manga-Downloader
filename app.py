import os
import re
import json
import threading
from pathlib import Path

# Tentativo di import per pywebview
try:
    import webview
except ImportError:
    print("ERRORE: La libreria 'pywebview' non è installata in questo ambiente.")
    print("Esegui: pip3 install pywebview")
    # Facciamo finta di poter continuare in headless/mock se serve per la verifica statica,
    # ma in genere usciamo se non c'è webview.

from AniManga_Downloader import (
    _is_anime_link, _is_manga_link, extract_manga_name,
    anime_estrai_episodi, anime_download, MangaDownloader,
    MANGA_MAX_THREADS, _anime_folder_name, anime_check_dependencies
)

class Api:
    def __init__(self):
        self.window = None
        self.stop_events = {}   # index (str) -> threading.Event
        self._threads = {}      # index (str) -> Thread

    def set_window(self, window):
        self.window = window

    def _emit(self, index, data):
        """Invia un evento di progresso al JS, taggato con l'indice della card,
        così ogni download aggiorna la propria scheda anche in parallelo."""
        if self.window:
            payload = dict(data)
            payload["index"] = index
            safe_json = json.dumps(payload)
            self.window.evaluate_js(f"window.updateProgress({safe_json})")

    def fetch_info(self, text):
        """Riceve testo dalla UI, estrae link e restituisce info."""
        urls = [u for u in re.split(r"[\s,]+", text.strip()) if u]
        results = []
        for url in urls:
            if _is_anime_link(url):
                episodi = anime_estrai_episodi(url)
                if episodi:
                    results.append({
                        "kind": "anime",
                        "title": _anime_folder_name(url),
                        "url": url,
                        "count": len(episodi),  # già limitati allo slug dell'anime
                        "episodi": episodi  # teniamo traccia
                    })
            elif _is_manga_link(url):
                title = extract_manga_name(url)
                dl = MangaDownloader(url, Path.home() / "Downloads", 1) # dummy per estrarre info
                try:
                    chapters = dl.get_chapter_links()
                    if chapters:
                        results.append({
                            "kind": "manga",
                            "title": title,
                            "url": url,
                            "count": len(chapters),
                            "chapters": chapters
                        })
                finally:
                    dl.close()
        return results

    def start_download(self, item, start_idx, end_idx, index=0):
        """Avvia il download di una scheda in un thread dedicato.

        Ogni scheda (index) ha il proprio thread e stop_event, così più opere
        (es. un anime e un manga) possono scaricare in parallelo."""
        index = str(index)
        existing = self._threads.get(index)
        if existing and existing.is_alive():
            return {"status": "error", "message": "Download già in corso per questa scheda."}

        stop_event = threading.Event()
        self.stop_events[index] = stop_event
        thread = threading.Thread(
            target=self._download_worker,
            args=(item, start_idx, end_idx, stop_event, index),
            daemon=True
        )
        self._threads[index] = thread
        thread.start()
        return {"status": "started"}

    def stop_download(self, index=None):
        """Ferma una scheda specifica, oppure tutte se index è None (chiusura app)."""
        if index is None:
            for ev in self.stop_events.values():
                ev.set()
            return {"status": "stopped"}
        index = str(index)
        ev = self.stop_events.get(index)
        if ev:
            ev.set()
            return {"status": "stopped"}
        return {"status": "idle"}

    def _download_worker(self, item, start_idx, end_idx, stop_event, index):
        # Callback di progresso legata a questa scheda: ogni evento porta con sé
        # il proprio index, quindi i download paralleli non si sovrascrivono.
        cb = lambda data: self._emit(index, data)
        kind = item.get("kind")
        url = item.get("url")
        # 1-based indices to list
        selection = list(range(start_idx, end_idx + 1))

        try:
            if kind == "anime":
                anime_download(url, item.get("episodi", []), selection, progress_cb=cb, stop_event=stop_event)
            elif kind == "manga":
                name = extract_manga_name(url)
                out = Path.home() / "Downloads" / f"{name}_PDF"
                dl = MangaDownloader(url, out, MANGA_MAX_THREADS, progress_cb=cb, stop_event=stop_event)
                try:
                    chapters = item.get("chapters", [])
                    selected = [idx for idx in selection if 1 <= idx <= len(chapters)]
                    total_selected = len(selected)

                    for pos, idx in enumerate(selected, 1):
                        if stop_event.is_set(): break
                        slug, chapter_url = chapters[idx - 1]

                        # Notifica UI del progresso tra capitoli
                        cb({
                            "type": "manga_chapter_progress",
                            "chapter": slug,
                            "current_chapter": pos,
                            "total_chapters": total_selected,
                            "message": f"Capitolo {slug} ({pos}/{total_selected})"
                        })

                        try:
                            dl.download_chapter(slug, chapter_url, idx)
                        except Exception as ch_err:
                            # Errore su un singolo capitolo: logga ma continua con gli altri
                            cb({
                                "type": "manga_chapter_error",
                                "chapter": slug,
                                "current_chapter": pos,
                                "total_chapters": total_selected,
                                "message": f"Errore cap. {slug}: {ch_err}"
                            })
                            continue
                finally:
                    dl.close()
                    if not stop_event.is_set():
                        cb({"type": "manga_series_done", "name": name})

        except Exception as e:
            cb({"type": "error", "message": str(e)})


def main():
    api = Api()
    html_path = os.path.join(os.path.dirname(__file__), "static", "index.html")
    
    # Try to load pywebview
    try:
        import webview
        window = webview.create_window(
            "AniManga Downloader",
            html_path,
            js_api=api,
            width=1000,
            height=800,
            background_color='#f9f9f9'
        )
        
        def on_closed():
            # Forza l'arresto immediato di tutti i thread (inclusi quelli di download)
            api.stop_download()
            os._exit(0)

        window.events.closed += on_closed
        api.set_window(window)
        webview.start(debug=False)
    except ImportError:
        print("Scusa, pywebview non è installato in questa istanza Python.")
        print("Tuttavia l'app è pronta! Basta installarlo ed eseguire questo file.")

if __name__ == '__main__':
    main()
