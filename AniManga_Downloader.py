#!/usr/bin/env python3
"""
AniManga_Downloader.py
Unione pulita di ADB_funzionante.py (anime) + MDB_Latest.py (manga).
Accetta link misti AnimeSaturn e MangaWorld, chiede intervalli e scarica tutto.
"""

import os
import re
import io
import sys
import base64
import logging
import tempfile
import shutil
import threading
from pathlib import Path
from urllib.parse import urlparse, urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
from PIL import Image

try:
    import yt_dlp
except ImportError:  # senza yt-dlp il download anime non è disponibile (il manga sì)
    yt_dlp = None


# ============================================================
# CONFIGURAZIONE
# ============================================================

ANIME_MAX_THREADS = 4
ANIME_FRAGMENTS = 4  # frammenti HLS scaricati in parallelo per ogni episodio
MANGA_MAX_THREADS = 8
HTTP_TIMEOUT = 20
HTTP_RETRIES = 3
USER_AGENT = "Mozilla/5.0"


def _find_binary(name: str) -> str | None:
    """Trova un binario esterno: prima quello incluso nel bundle (PyInstaller
    `sys._MEIPASS`), poi accanto all'eseguibile, infine nel PATH di sistema.
    Così funziona sia in sviluppo sia dentro l'app .dmg/.exe impacchettata."""
    candidates = [name, name + ".exe"]
    search_dirs = []
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        search_dirs.append(meipass)
    if getattr(sys, "frozen", False):
        search_dirs.append(os.path.dirname(sys.executable))
    for d in search_dirs:
        for c in candidates:
            p = os.path.join(d, c)
            if os.path.isfile(p):
                return p
    return shutil.which(name)


# ffmpeg serve a yt-dlp per assemblare (mux) gli stream HLS in un file mp4.
FFMPEG_PATH = _find_binary("ffmpeg")


def anime_check_dependencies() -> tuple[bool, list[str]]:
    """Verifica le dipendenze runtime del download anime.

    yt-dlp è una libreria Python (inclusa nel bundle), ffmpeg è un binario
    esterno necessario per gli stream HLS. Restituisce (ok, lista_mancanti)."""
    missing = []
    if yt_dlp is None:
        missing.append("yt-dlp")
    if not _find_binary("ffmpeg"):
        missing.append("ffmpeg")
    return (not missing, missing)


def _make_session() -> requests.Session:
    """Crea una Session con retry automatico (3 tentativi, backoff esponenziale)."""
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    retry = Retry(total=HTTP_RETRIES, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


# ============================================================
# UTILITÀ CONDIVISE
# ============================================================

def parse_intervallo(total: int) -> list[int]:
    """Chiede all'utente un intervallo (es. 3-10, 5, tutti) e restituisce la lista di indici."""
    scelta = input("Inserisci l'intervallo da scaricare (es. 3-10, 5, tutti): ").strip().lower()
    if scelta in ("tutti", "*"):
        return list(range(1, total + 1))
    if re.match(r"^\d+-\d+$", scelta):
        start, end = map(int, scelta.split("-"))
        return list(range(max(1, start), min(total, end) + 1))
    if scelta.isdigit():
        num = int(scelta)
        return [num] if 1 <= num <= total else []
    print("Input non valido, verranno scaricati tutti.")
    return list(range(1, total + 1))


# ============================================================
# ANIME DOWNLOADER  (da ADB_funzionante.py, dominio reso dinamico)
# ============================================================

# Session condivisa per le richieste anime (con retry)
_anime_session = _make_session()


def _anime_folder_name(url: str) -> str:
    """Nome cartella/titolo leggibile dall'URL dell'anime, senza l'ID casuale
    finale di AnimeSaturn (es. "one-piece-PmTvj" -> "One Piece")."""
    m = re.search(r"/anime/([^/]+)", url)
    slug = m.group(1) if m else "Anime"
    parts = slug.split("-")
    # Rimuove un eventuale ID finale: segmento corto con maiuscole/cifre miste,
    # che non è una vera parola del titolo (es. "PmTvj", "CYk2T").
    if len(parts) > 1 and re.fullmatch(r"[A-Za-z0-9]{4,8}", parts[-1]) and re.search(r"[A-Z0-9]", parts[-1]):
        parts = parts[:-1]
    return " ".join(p.capitalize() for p in parts) if parts else slug


def anime_estrai_episodi(url_anime: str) -> list[str]:
    """Estrae tutti i link degli episodi dalla pagina principale di un anime."""
    parsed = urlparse(url_anime)
    base_url = f"{parsed.scheme}://{parsed.netloc}"

    r = _anime_session.get(url_anime, timeout=HTTP_TIMEOUT)
    if r.status_code != 200:
        print("Errore nel caricamento della pagina anime.")
        return []

    # Slug dell'anime (es. "akane-banashi-ita-CYk2T") per prendere SOLO i suoi
    # episodi ed escludere i link "consigliati" ad altri anime nella pagina.
    m_slug = re.search(r"/anime/([^/]+)", url_anime)
    slug = re.escape(m_slug.group(1)) if m_slug else r"[^/]+"

    # AnimeSaturn usa /episode/<slug>/ep-N (formato attuale) oppure il vecchio
    # /ep/<nome>-ep-N. Supportiamo entrambi.
    ep_pattern = re.compile(rf"/episode/{slug}/ep-\d+|/ep/.+-ep-\d+")

    soup = BeautifulSoup(r.text, "html.parser")
    episodi = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if ep_pattern.search(href):
            if href.startswith("/"):
                href = f"{base_url}{href}"
            episodi.append(href)

    episodi = list(set(episodi))
    episodi.sort(key=lambda x: int(re.search(r"ep-(\d+)", x).group(1)))
    return episodi


def _anime_get_watch_link(ep_url: str) -> str | None:
    """Trova il link 'Guarda lo streaming' dalla pagina dell'episodio."""
    parsed = urlparse(ep_url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"

    r = _anime_session.get(ep_url, timeout=HTTP_TIMEOUT)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    for a in soup.find_all("a", href=True):
        if a.get_text(strip=True).lower() == "guarda lo streaming":
            href = a["href"].strip()
            return href if href.startswith("http") else f"{base_url}{href}"
    print(f"[WARN] Nessun bottone trovato per {ep_url}")
    return None


def _anime_xor_decode(b64: str, key: str) -> str:
    """Decodifica una stringa base64 + XOR ciclico con `key`.

    È lo stesso schema usato dal player embed di saturncdn per offuscare
    l'URL dello stream nel JSON della playlist (la funzione `dec()` lato JS)."""
    if not b64:
        return ""
    data = base64.b64decode(b64)
    k = (key or "as").encode()
    return "".join(chr(data[i] ^ k[i % len(k)]) for i in range(len(data)))


def _anime_resolve_stream(watch_url: str) -> tuple[str, str] | None:
    """Dalla pagina di visione (quella con l'iframe `play.saturncdn.net/embed/...`)
    ricava l'URL reale dello stream HLS (.m3u8) e il referer da passare a yt-dlp.

    Flusso attuale di AnimeSaturn:
        pagina /anime/<slug>/ep-N -> <iframe src=".../embed/<id>?token=...&expires=...">
        embed page                -> window.__E = {i:<id>, k:"<token>", e:<expires>}
        GET /embed/<id>/playlist?token=...&expires=... -> JSON {d,p,t} offuscato
        dec(JSON.d, token)        -> https://.../playlist.m3u8

    Restituisce (stream_url, referer) oppure None se qualcosa non si risolve.
    """
    # 1. Pagina di visione -> iframe del player
    r = _anime_session.get(watch_url, timeout=HTTP_TIMEOUT)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    iframe = (soup.find("iframe", id="watch-iframe")
              or soup.find("iframe", src=re.compile(r"saturncdn|/embed/")))
    if not iframe or not iframe.get("src"):
        return None
    embed_url = iframe["src"].strip()
    if embed_url.startswith("//"):
        embed_url = "https:" + embed_url

    # 2. Pagina embed -> parametri (id, token, expires) in window.__E
    r2 = _anime_session.get(embed_url, headers={"Referer": watch_url}, timeout=HTTP_TIMEOUT)
    r2.raise_for_status()
    m = re.search(r"window\.__E\s*=\s*\{([^}]*)\}", r2.text)
    if not m:
        return None
    conf = m.group(1)
    m_id = re.search(r"i:\s*(\d+)", conf)
    m_key = re.search(r'k:\s*"([^"]+)"', conf)
    m_exp = re.search(r"e:\s*(\d+)", conf)
    if not (m_id and m_key):
        return None
    eid, token = m_id.group(1), m_key.group(1)
    expires = m_exp.group(1) if m_exp else ""

    # 3. Endpoint playlist -> JSON con la sorgente cifrata
    parsed = urlparse(embed_url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    playlist_url = f"{base}/embed/{eid}/playlist?token={token}&expires={expires}"
    r3 = _anime_session.get(playlist_url, headers={"Referer": embed_url}, timeout=HTTP_TIMEOUT)
    r3.raise_for_status()
    try:
        data = r3.json()
    except ValueError:
        return None

    # 4. Decodifica la sorgente (XOR con il token)
    stream = _anime_xor_decode(data.get("d", ""), token)
    if not stream:
        return None
    if stream.startswith("youtube/"):  # alcuni episodi puntano a YouTube
        stream = "https://www.youtube.com/watch?v=" + stream[len("youtube/"):]
    return stream, embed_url


class _AnimeStopped(Exception):
    """Sollevata dentro il progress hook di yt-dlp per interrompere il download."""


def _fmt_speed(bps) -> str:
    """Formatta una velocità in byte/s (es. 1572864 -> '1.50MiB/s')."""
    if not bps:
        return "?"
    for unit in ("B", "KiB", "MiB", "GiB"):
        if bps < 1024:
            return f"{bps:.2f}{unit}/s"
        bps /= 1024
    return f"{bps:.2f}TiB/s"


def _fmt_eta(seconds) -> str:
    """Formatta un ETA in secondi (es. 40 -> '00:40', 3700 -> '01:01:40')."""
    if seconds is None:
        return "?"
    seconds = int(seconds)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def _anime_download_video(ep_url: str, filepath: str, progress_cb=None, stop_event=None) -> None:
    """Scarica un singolo episodio usando l'API Python di yt-dlp (path assoluto)."""
    name = os.path.basename(filepath)
    if os.path.exists(filepath):
        if progress_cb: progress_cb({"type": "anime_skip", "file": name})
        else: print(f"[SKIP] {name} esiste già, salto download.")
        return

    if yt_dlp is None:
        if progress_cb: progress_cb({"type": "anime_error", "file": name, "message": f"yt-dlp non disponibile per {name}"})
        else: print(f"[ERRORE] yt-dlp non disponibile per {name}")
        return

    inter = _anime_get_watch_link(ep_url)
    if not inter:
        if progress_cb: progress_cb({"type": "anime_error", "file": name, "message": f"Link streaming non trovato per {name}"})
        else: print(f"[WARN] Link streaming non trovato per {ep_url}")
        return
    resolved = _anime_resolve_stream(inter)
    if not resolved:
        if progress_cb: progress_cb({"type": "anime_error", "file": name, "message": f"Player non risolto (stream non trovato) per {name}"})
        else: print(f"[WARN] Player non risolto per {ep_url}")
        return
    stream_url, referer = resolved

    if progress_cb: progress_cb({"type": "anime_start", "file": name})
    else: print(f"[↓] Scarico {name}")

    def hook(d):
        # Lo stop è cooperativo: sollevando qui interrompiamo subito yt-dlp.
        if stop_event and stop_event.is_set():
            raise _AnimeStopped()
        if d.get("status") == "downloading" and progress_cb:
            fi, fc = d.get("fragment_index"), d.get("fragment_count")
            total = d.get("total_bytes") or d.get("total_bytes_estimate")
            downloaded = d.get("downloaded_bytes", 0)
            if fc:  # gli HLS non conoscono la dimensione totale: usiamo i frammenti
                percent = (fi or 0) / fc * 100
            elif total:
                percent = downloaded / total * 100
            else:
                percent = 0.0
            progress_cb({
                "type": "anime_progress",
                "file": name,
                "percent": round(percent, 1),
                "speed": _fmt_speed(d.get("speed")),
                "eta": _fmt_eta(d.get("eta")),
            })

    opts = {
        "outtmpl": filepath,
        "http_headers": {"Referer": referer},
        "concurrent_fragment_downloads": ANIME_FRAGMENTS,
        "retries": 10,
        "fragment_retries": 10,
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
        "progress_hooks": [hook],
    }
    if FFMPEG_PATH:
        opts["ffmpeg_location"] = FFMPEG_PATH

    def _cleanup_partial():
        for p in (filepath, filepath + ".part"):
            try: os.remove(p)
            except OSError: pass

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            rc = ydl.download([stream_url])
        if rc != 0:
            raise RuntimeError(f"yt-dlp returncode {rc}")
        if progress_cb: progress_cb({"type": "anime_done", "file": name})
        else: print(f"[✓] {name} completato.")
    except _AnimeStopped:
        _cleanup_partial()
        if progress_cb: progress_cb({"type": "anime_stop", "file": name})
    except Exception as e:
        # yt-dlp può avvolgere l'eccezione di stop in DownloadError: distinguiamo.
        if stop_event and stop_event.is_set():
            _cleanup_partial()
            if progress_cb: progress_cb({"type": "anime_stop", "file": name})
        elif progress_cb:
            progress_cb({"type": "anime_error", "file": name, "message": f"Download fallito per {name}: {e}"})
        else:
            print(f"[ERRORE] Download fallito per {name}: {e}")


def anime_download(url: str, episodi: list[str], selezione: list[int], progress_cb=None, stop_event=None) -> None:
    """Scarica gli episodi selezionati di un anime."""
    ok, missing = anime_check_dependencies()
    if not ok:
        msg = f"Dipendenze mancanti per il download anime: {', '.join(missing)}."
        if progress_cb: progress_cb({"type": "error", "message": msg})
        else: print(f"[ERRORE] {msg}")
        return

    nome_cartella = _anime_folder_name(url)
    download_dir = Path.home() / "Downloads" / nome_cartella
    download_dir.mkdir(parents=True, exist_ok=True)

    # La lista `episodi` è già limitata allo slug esatto dell'anime da
    # anime_estrai_episodi, quindi la usiamo direttamente (nessun re-filtro).
    to_download = []
    for i in selezione:
        if 1 <= i <= len(episodi):
            filepath = str(download_dir / f"{i:02d}.mp4")
            if not os.path.exists(filepath):
                to_download.append((episodi[i - 1], filepath))

    # Comunica alla UI quanti episodi verranno scaricati davvero: così la barra
    # mostra un progresso AGGREGATO (X/N) invece di saltare tra i download paralleli.
    if progress_cb:
        progress_cb({"type": "anime_series_start", "total": len(to_download), "name": nome_cartella})

    if not to_download:
        print(f"[INFO] Tutti gli episodi di '{nome_cartella}' già scaricati.")
        if progress_cb:
            progress_cb({"type": "anime_series_done", "name": nome_cartella})
        return

    # Download parallelo (max 4 episodi contemporanei)
    max_threads = min(ANIME_MAX_THREADS, len(to_download))
    if not progress_cb: print(f"[INFO] Avvio download di {len(to_download)} episodi ({max_threads} paralleli)...")
    
    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        futures = [executor.submit(_anime_download_video, ep_url, fp, progress_cb, stop_event) for ep_url, fp in to_download]
        for future in as_completed(futures):
            future.result()

    if progress_cb: progress_cb({"type": "anime_series_done", "name": nome_cartella})
    else: print(f"[✓] Download anime '{nome_cartella}' completato.")


# ============================================================
# MANGA DOWNLOADER  (da MDB_Latest.py, fix temp files + bare except)
# ============================================================

class MangaDownloader:
    def __init__(self, base_url: str, output_folder: Path, max_workers: int, progress_cb=None, stop_event=None):
        self.base_url = base_url.rstrip("/")
        self.output_folder = output_folder
        self.output_folder.mkdir(parents=True, exist_ok=True)
        self.session = _make_session()
        self.max_workers = max_workers
        self.total_chapters: int = 0
        self.progress_cb = progress_cb
        self.stop_event = stop_event

    def get_chapter_links(self) -> list[tuple[str, str]]:
        logging.info(f"Fetching chapter index: {self.base_url}")
        resp = self.session.get(self.base_url, timeout=HTTP_TIMEOUT)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        anchors = soup.select('a[href*="/read/"]')

        # Supporto data-href
        data_anchors = soup.select('[data-href*="/read/"]')
        for a in data_anchors:
            if not a.get("href") and a.get("data-href"):
                a["href"] = a["data-href"]
                anchors.append(a)

        seen = set()
        chapters: list[tuple[str, str]] = []
        for a in anchors:
            text = a.get_text(strip=True)
            if re.search(r"\bprimo capitolo\b", text, re.IGNORECASE) or \
               re.search(r"\bultimo capitolo\b", text, re.IGNORECASE):
                continue
            href = a.get("href")
            if not href:
                continue
            if not href.startswith("/read/") and "/read/" not in href:
                continue
            href = urljoin(self.base_url, href)
            if href in seen:
                continue
            seen.add(href)
            m = re.search(r"Capitolo\s*([\d\.\-]+)", text, re.IGNORECASE)
            slug = m.group(1) if m else href.rstrip("/").split("/")[-1]
            chapters.append((slug, href))

        # Ordina i capitoli numericamente. I capitoli con decimali (es. 110.5) verranno messi nella giusta posizione.
        # Eventuali capitoli extra non numerici (one-shot, ecc.) finiranno alla fine della lista.
        chapters.reverse()
        def parse_slug(s):
            # Alcuni slug usano il trattino al posto del punto per i decimali (es. "1-5")
            s_clean = s.replace("-", ".")
            try: return float(s_clean)
            except: return float("inf")
        chapters.sort(key=lambda x: parse_slug(x[0]))

        logging.info(f"Found {len(chapters)} chapters (including decimals)")
        self.chapter_slugs = [slug for slug, _ in chapters]
        self.total_chapters = len(chapters)
        self.padding_length = len(str(self.total_chapters))
        if self.chapter_slugs:
            logging.info(f"First chapter detected: {self.chapter_slugs[0]}")
            logging.info(f"Last chapter detected: {self.chapter_slugs[-1]}")
        return chapters

    def get_first_image_info(self, chapter_url: str):
        page1 = f"{chapter_url}/1"
        logging.info(f"Fetching first page: {page1}")
        resp = self.session.get(page1, timeout=HTTP_TIMEOUT)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        pat_primary = re.compile(r"(?:https?:)?//cdn\.mangaworld\.[^/]+/chapters/", re.IGNORECASE)
        img = soup.find("img", src=pat_primary)

        if not img or not img.get("src"):
            pat_fallback1 = re.compile(r"(?:https?:)?//[^/]*mangaworld\.[^/]+/.*/chapters/", re.IGNORECASE)
            img = soup.find("img", src=pat_fallback1)

        if not img or not img.get("src"):
            pat_fallback2 = re.compile(r"/chapters/", re.IGNORECASE)
            img = soup.find("img", src=pat_fallback2)

        if not img or not img.get("src"):
            raise RuntimeError("Image not found on first page")

        src = img["src"].split("?")[0]
        if src.startswith("/"):
            parsed = urlparse(page1)
            src = f"{parsed.scheme}://{parsed.netloc}{src}"

        folder = src.rsplit("/", 1)[0]
        ext = Path(src).suffix
        return src, folder, ext, soup

    def get_total_pages(self, chapter_url: str, soup: BeautifulSoup, img_folder: str, ext: str) -> int:
        logging.info("Determining total pages via HTML and fallback methods")
        text = soup.get_text(separator=" ")
        slash = re.findall(r"\b\d+/(\d+)\b", text)
        if slash:
            total = max(int(n) for n in slash)
            logging.info(f"Total pages from slash nav: {total}")
            return total
        pattern = re.compile(re.escape(chapter_url) + r"/(\d+)$")
        nums = [int(m.group(1)) for a in soup.find_all("a", href=pattern) if (m := pattern.search(a["href"]))]
        if nums:
            total = max(nums)
            logging.info(f"Total pages from HTML nav links: {total}")
            return total
        select = soup.find("select", id=re.compile("page", re.IGNORECASE))
        if select:
            count = len(select.find_all("option"))
            logging.info(f"Total pages from dropdown: {count}")
            return count
        ul = soup.find("ul", class_="page-numbers")
        if ul:
            nums = [int(t.get_text(strip=True)) for t in ul.find_all(["a", "span"], class_="page-numbers") if t.get_text(strip=True).isdigit()]
            if nums:
                total = max(nums)
                logging.info(f"Total pages from page-numbers list: {total}")
                return total
        logging.info("Binary search fallback for total pages")
        low, high = 1, 2
        while True:
            resp = self.session.head(f"{img_folder}/{high}{ext}", timeout=10)
            if resp.status_code == 200:
                low = high
                high *= 2
            else:
                break
        while low + 1 < high:
            mid = (low + high) // 2
            resp = self.session.head(f"{img_folder}/{mid}{ext}", timeout=10)
            if resp.status_code == 200:
                low = mid
            else:
                high = mid
        logging.info(f"Total pages from HEAD: {low}")
        return low

    def download_chapter(self, chap_slug: str, chapter_url: str, index: int) -> None:
        if self.stop_event and self.stop_event.is_set():
            return

        cleaned_slug = chap_slug
        try:
            num = float(chap_slug)
            # MangaWorld moltiplica spesso i capitoli per 100 (es. 100 = cap 1, 150 = cap 1.5)
            # Se il numero è grande e intero, lo dividiamo per ottenere il vero capitolo.
            if num >= 100:
                real_num = num / 100
                if real_num.is_integer():
                    cleaned_slug = str(int(real_num))
                else:
                    cleaned_slug = str(real_num)
            elif num.is_integer():
                cleaned_slug = str(int(num))
        except ValueError:
            pass

        if re.match(r"^\d+(\.\d+)?$", cleaned_slug):
            pdf_filename = f"Capitolo_{cleaned_slug}.pdf"
        else:
            pdf_filename = f"Capitolo_{str(index).zfill(2)}.pdf"

        pdf_path = self.output_folder / pdf_filename
        if pdf_path.exists():
            if self.progress_cb: self.progress_cb({"type": "manga_skip", "chapter": chap_slug, "file": pdf_filename})
            else: logging.info(f"Skipping {pdf_filename}, PDF exists")
            return

        try:
            first_src, folder, ext, soup = self.get_first_image_info(chapter_url)
        except Exception as e:
            if self.progress_cb: self.progress_cb({"type": "manga_chapter_error", "chapter": chap_slug, "message": f"Errore capitolo {chap_slug}: {e}"})
            else: logging.error(f"Error in chapter {chap_slug} first image: {e}")
            return

        total = self.get_total_pages(chapter_url, soup, folder, ext)
        if total < 1:
            if not self.progress_cb: logging.warning(f"No pages for Capitolo {chap_slug}, skipping")
            return

        if self.progress_cb: self.progress_cb({"type": "manga_chapter_start", "chapter": chap_slug, "total_pages": total})

        tmp_dir = Path(tempfile.mkdtemp())

        def fetch_page(i: int):
            if self.stop_event and self.stop_event.is_set():
                raise InterruptedError("Stopped")

            candidates = (
                [first_src] if i == 1
                else [f"{folder}/{i}{ext}", f"{folder}/{i}{'.png' if ext == '.jpg' else ext}"]
            )
            for url in candidates:
                try:
                    r = self.session.get(url, timeout=20)
                    r.raise_for_status()
                    im = Image.open(io.BytesIO(r.content)).convert("RGB")
                    p = tmp_dir / f"{i:03d}.png"
                    im.save(p)
                    return i, p
                except Exception:
                    continue
            raise RuntimeError(f"Page {i} missing in Capitolo {chap_slug}")

        imgs = {}
        errors = []
        try:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {executor.submit(fetch_page, i): i for i in range(1, total + 1)}
                for fut in as_completed(futures):
                    i = futures[fut]
                    try:
                        idx, path = fut.result()
                        imgs[idx] = path
                        if self.progress_cb: self.progress_cb({"type": "manga_page_done", "chapter": chap_slug, "page": idx, "total_pages": total})
                        else: logging.info(f"Downloaded page {idx}/{total}")
                    except InterruptedError:
                        pass
                    except Exception:
                        errors.append(i)

            if errors:
                if self.progress_cb: self.progress_cb({"type": "manga_chapter_error", "chapter": chap_slug, "message": f"Pagine mancanti: {errors}"})
                else: logging.error(f"Error downloading pages {errors} in Capitolo {chap_slug}")
                return

            if self.stop_event and self.stop_event.is_set():
                return

            pil_images = [Image.open(imgs[i]).convert("RGB") for i in sorted(imgs)]
            if pil_images:
                pil_images[0].save(
                    str(pdf_path),
                    format="PDF",
                    save_all=True,
                    append_images=pil_images[1:],
                )
                if self.progress_cb: self.progress_cb({"type": "manga_chapter_done", "chapter": chap_slug})
                else: logging.info(f"Created PDF {pdf_filename}")
        except InterruptedError:
            pass
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    def close(self):
        self.session.close()







def extract_manga_name(url: str) -> str:
    path = urlparse(url).path
    segments = path.strip("/").split("/")
    slug = segments[-1] if segments else "Manga"
    return slug.replace("-", " ").title()


# ============================================================
# ORCHESTRATORE
# ============================================================

def _is_anime_link(url: str) -> bool:
    try:
        return "animesaturn" in urlparse(url).netloc.lower()
    except Exception:
        return False


def _is_manga_link(url: str) -> bool:
    try:
        return "mangaworld" in urlparse(url).netloc.lower()
    except Exception:
        return False


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    raw = input("Inserisci uno o più link di anime e/o manga (separati da spazi o virgole): ").strip()
    urls = [u for u in re.split(r"[\s,]+", raw) if u]
    if not urls:
        print("Nessun link fornito.")
        return

    # Classifica e filtra
    works: list[tuple[str, str]] = []  # (tipo, url)
    for u in urls:
        if _is_anime_link(u):
            works.append(("anime", u))
        elif _is_manga_link(u):
            works.append(("manga", u))
        else:
            print(f"[WARN] Link non riconosciuto, ignorato: {u}")

    if not works:
        print("Nessun link valido (AnimeSaturn o MangaWorld).")
        return

    # --- Fase 1: raccogli tutte le info e intervalli PRIMA di scaricare ---
    download_queue: list[dict] = []

    for kind, url in works:
        if kind == "anime":
            episodi = anime_estrai_episodi(url)
            if not episodi:
                print(f"[WARN] Nessun episodio trovato per {url}")
                continue
            print(f"\n[ANIME] {len(episodi)} episodi trovati per: {url}")
            sel = parse_intervallo(len(episodi))
            download_queue.append({
                "kind": "anime",
                "url": url,
                "episodi": episodi,  # cache: non riscaricare la lista
                "selezione": sel,
            })

        elif kind == "manga":
            name = extract_manga_name(url)
            out = Path.home() / "Downloads" / f"{name}_PDF"
            dl = MangaDownloader(url, out, MANGA_MAX_THREADS)
            try:
                chapters = dl.get_chapter_links()
                if not chapters:
                    print(f"[WARN] Nessun capitolo trovato per {url}")
                    continue
                print(f"\n[MANGA] {len(chapters)} capitoli trovati per: {url}")
                sel = parse_intervallo(len(chapters))
                download_queue.append({
                    "kind": "manga",
                    "url": url,
                    "name": name,
                    "output": out,
                    "chapters": chapters,  # cache: non riscaricare la lista
                    "selezione": sel,
                })
            finally:
                dl.close()

    if not download_queue:
        print("Nessuna opera da scaricare.")
        return

    # --- Fase 2: download sequenziale per opera ---
    print(f"\nTutti gli intervalli raccolti. Avvio download di {len(download_queue)} opere...\n")

    for i, item in enumerate(download_queue, 1):
        kind = item["kind"]
        url = item["url"]
        sel = item["selezione"]
        print(f"[{i}/{len(download_queue)}] {kind.upper()}: {url}")

        if not sel:
            print(f"  [SKIP] Nessun intervallo selezionato.")
            continue

        try:
            if kind == "anime":
                anime_download(url, item["episodi"], sel)
            elif kind == "manga":
                dl = MangaDownloader(item["url"], item["output"], MANGA_MAX_THREADS)
                try:
                    chapters = item["chapters"]
                    selected = [idx for idx in sel if 1 <= idx <= len(chapters)]
                    for pos, idx in enumerate(selected, 1):
                        slug, chapter_url = chapters[idx - 1]
                        print(f"  [{pos}/{len(selected)}] Capitolo {slug}...")
                        dl.download_chapter(slug, chapter_url, idx)
                finally:
                    dl.close()
                    print(f"[✓] Download manga '{item['name']}' completato.")
        except Exception as e:
            print(f"[ERROR] Errore su {url}: {e}")

    print("\n[✓] Tutto completato.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[!] Interrotto dall'utente. Download parziali salvati.")
