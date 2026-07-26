#!/usr/bin/env python3
# Universal_Downloader_Fixed_Unified.py
# File unico che integra gli SCRIPT ORIGINALI (invariati) per ANIME e MANGA
# + Orchestratore che accetta link misti, chiede intervalli per ciascuna opera e poi scarica in sequenza.

import os
import re
import types
import logging
from pathlib import Path
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed

# ======================================================
# === SCRIPT ORIGINALE ANIME — INCLUSO INTEGRALMENTE ===
# ======================================================
ANIME_SCRIPT_SOURCE = r'''import os
import re
import requests
from bs4 import BeautifulSoup
import subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse

# --- Estrazione episodi (identica alla logica originale) ---
def estrai_episodi(url_anime, base_url):
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url_anime, headers=headers)
    if r.status_code != 200:
        print("Errore nel caricamento della pagina.")
        return []

    soup = BeautifulSoup(r.text, "html.parser")
    episodi = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if re.search(r"/ep/.+-ep-\d+", href):
            if href.startswith("/ep/"):
                href = f"{base_url}{href}"
            episodi.append(href)

    episodi = list(set(episodi))
    episodi.sort(key=lambda x: int(re.search(r"ep-(\d+)", x).group(1)))
    return episodi

# --- Navigazione e download ---
def get_watch_link(ep_url, base_url):
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(ep_url, headers=headers)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    for a in soup.find_all("a", href=True):
        if a.get_text(strip=True).lower() == "guarda lo streaming":
            href = a["href"].strip()
            return href if href.startswith("http") else f"{base_url}{href}"
    print("[WARN] Nessun bottone trovato per", ep_url)
    return None

def get_final_watch_url(intermediate_url, base_url):
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(intermediate_url, headers=headers, allow_redirects=True)
    r.raise_for_status()
    if "/watch" in r.url:
        return r.url
    soup = BeautifulSoup(r.text, "html.parser")
    a = soup.find("a", href=re.compile("/watch"))
    if a:
        href = a["href"].strip()
        return href if href.startswith("http") else f"{base_url}{href}"
    return None

def download_video(index, ep_url, filename, base_url):
    if os.path.exists(filename):
        print(f"[SKIP] {filename} esiste già, salto download.")
        return
    inter = get_watch_link(ep_url, base_url)
    if not inter:
        return
    final = get_final_watch_url(inter, base_url)
    if not final:
        return
    print(f"[↓] ({index}) Scarico {filename}")
    subprocess.run(["yt-dlp", "--no-warnings", "--concurrent-fragments", "5", "-o", filename, final], check=False)

# --- MAIN ---
def main():
    url_anime = input("Inserisci il link della pagina AnimeSaturn con tutti gli episodi: ").strip()
    parsed = urlparse(url_anime)
    base_url = f"{parsed.scheme}://{parsed.netloc}"

    nome_cartella = re.sub(r'.*/anime/', '', url_anime).split('/')[0]

    download_dir = Path.home() / "Downloads" / nome_cartella
    download_dir.mkdir(parents=True, exist_ok=True)
    os.chdir(download_dir)

    episodi = estrai_episodi(url_anime, base_url)
    print(f"[INFO] Trovati {len(episodi)} episodi.")

    nome_base = re.search(r'/anime/([^/]+)', url_anime)
    nome_base = nome_base.group(1).split('-')[0].lower() if nome_base else ""
    episodi_filtrati = [e for e in episodi if nome_base in e.lower()]
    print(f"[INFO] Filtrati {len(episodi_filtrati)} episodi validi per {nome_base}.")

    scelta = input("\nInserisci l'intervallo di episodi da scaricare (es. 3-10, 5, tutti): ").strip().lower()

    if scelta == "tutti" or scelta == "*":
        start, end = 1, len(episodi_filtrati)
    elif re.match(r"^\d+-\d+$", scelta):
        start, end = map(int, scelta.split('-'))
    elif scelta.isdigit():
        start = end = int(scelta)
    else:
        print("Input non valido. Esempi validi: 3-10, 5, tutti")
        return

    start = max(1, start)
    end = min(len(episodi_filtrati), end)

    to_download = [(i, episodi_filtrati[i - 1], f"{i:02d}.mp4") for i in range(start, end + 1) if not os.path.exists(f"{i:02d}.mp4")]

    if not to_download:
        print("Tutti gli episodi richiesti sono già scaricati.")
        return

    max_threads = min(4, len(to_download))
    print(f"[INFO] Avvio download parallelo con {max_threads} thread...")

    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        futures = [executor.submit(download_video, i, ep_url, filename, base_url) for i, ep_url, filename in to_download]
        for future in as_completed(futures):
            future.result()

    print("\n[✓] Download completato.")

if __name__ == "__main__":
    main()
'''

# ======================================================
# === SCRIPT ORIGINALE MANGA — INCLUSO INTEGRALMENTE ===
# ======================================================
MANGA_SCRIPT_SOURCE = r'''#!/usr/bin/env python3
# Manga_Downloader_Bot.py

import argparse
import logging
from pathlib import Path
import tempfile
import io
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from fpdf import FPDF
from PIL import Image

PX_TO_MM = 0.264583

def configure_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] %(levelname)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

def extract_manga_name(url: str) -> str:
    path = urlparse(url).path
    segments = path.strip('/').split('/')
    slug = segments[-1] if segments else 'Manga'
    return slug.replace('-', ' ').title()

def parse_intervallo_input(total: int) -> list[int]:
    scelta = input("Inserisci l'intervallo di episodi da scaricare (es. 3-10, 5, tutti): ").strip().lower()
    if scelta == 'tutti':
        return list(range(1, total + 1))
    if re.match(r'^\d+-\d+$', scelta):
        start, end = map(int, scelta.split('-'))
        return list(range(max(1, start), min(total, end) + 1))
    if scelta.isdigit():
        num = int(scelta)
        return [num] if 1 <= num <= total else []
    print("Input non valido, verranno scaricati tutti i capitoli.")
    return list(range(1, total + 1))

class MangaDownloader:
    def __init__(self, base_url: str, output_folder: Path, max_workers: int):
        self.base_url = base_url.rstrip('/')
        self.output_folder = output_folder
        self.output_folder.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.max_workers = max_workers
        self.chapter_slugs: list[str] = []
        self.total_chapters: int = 0
        self.padding_length: int = 0

    def get_chapter_links(self) -> list[tuple[str, str]]:
        logging.info(f"Fetching chapter index: {self.base_url}")
        resp = self.session.get(self.base_url, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        anchors = soup.select('a[href*="/read/"]')

        data_anchors = soup.select('[data-href*="/read/"]')
        for a in data_anchors:
            if not a.get('href') and a.get('data-href'):
                a['href'] = a['data-href']
                anchors.append(a)

        seen = set()
        chapters: list[tuple[str, str]] = []
        for a in anchors:
            text = a.get_text(strip=True)
            if re.search(r"\bprimo capitolo\b", text, re.IGNORECASE) or \
               re.search(r"\bultimo capitolo\b", text, re.IGNORECASE):
                continue
            href = a.get('href')
            if not href:
                continue
            if not href.startswith('/read/') and '/read/' not in href:
                continue
            href = urljoin(self.base_url, href)
            if href in seen:
                continue
            seen.add(href)
            m = re.search(r"Capitolo\s*([\d\.]+)", text, re.IGNORECASE)
            slug = m.group(1) if m else href.rstrip('/').split('/')[-1]
            chapters.append((slug, href))

        numeric = all(re.match(r'^\d+(\.\d+)?$', slug) for slug, _ in chapters)
        if numeric:
            def parse_slug(s):
                try:
                    return float(s)
                except:
                    return float('inf')
            chapters.sort(key=lambda x: parse_slug(x[0]))
        else:
            logging.info("Non-numeric chapter IDs detected, keeping original order and reversing to ascending")
            chapters.reverse()

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
        resp = self.session.get(page1, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')

        pat_primary = re.compile(r'(?:https?:)?//cdn\.mangaworld\.[^/]+/chapters/', re.IGNORECASE)
        img = soup.find('img', src=pat_primary)

        if not img or not img.get('src'):
            pat_fallback1 = re.compile(r'(?:https?:)?//[^/]*mangaworld\.[^/]+/.*/chapters/', re.IGNORECASE)
            img = soup.find('img', src=pat_fallback1)

        if not img or not img.get('src'):
            pat_fallback2 = re.compile(r'/chapters/', re.IGNORECASE)
            img = soup.find('img', src=pat_fallback2)

        if not img or not img.get('src'):
            raise RuntimeError("Image not found on first page")

        src = img['src'].split('?')[0]
        if src.startswith('/'):
            parsed = urlparse(page1)
            src = f"{parsed.scheme}://{parsed.netloc}{src}"

        folder = src.rsplit('/', 1)[0]
        ext = Path(src).suffix
        return src, folder, ext, soup

    def get_total_pages(self, chapter_url: str, soup: BeautifulSoup, img_folder: str, ext: str) -> int:
        logging.info("Determining total pages via HTML and fallback methods")
        text = soup.get_text(separator=' ')
        slash = re.findall(r"\b\d+/(\d+)\b", text)
        if slash:
            total = max(int(n) for n in slash)
            logging.info(f"Total pages from slash nav: {total}")
            return total
        pattern = re.compile(re.escape(chapter_url) + r"/(\d+)$")
        nums = [int(m.group(1)) for a in soup.find_all('a', href=pattern) if (m := pattern.search(a['href']))]
        if nums:
            total = max(nums)
            logging.info(f"Total pages from HTML nav links: {total}")
            return total
        select = soup.find('select', id=re.compile('page', re.IGNORECASE))
        if select:
            count = len(select.find_all('option'))
            logging.info(f"Total pages from dropdown: {count}")
            return count
        ul = soup.find('ul', class_='page-numbers')
        if ul:
            nums = [int(t.get_text(strip=True)) for t in ul.find_all(['a','span'], class_='page-numbers') if t.get_text(strip=True).isdigit()]
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
            mid = (low + high)//2
            resp = self.session.head(f"{img_folder}/{mid}{ext}", timeout=10)
            if resp.status_code == 200:
                low = mid
            else:
                high = mid
        logging.info(f"Total pages from HEAD: {low}")
        return low

    def fallback_sequential_pages(self, img_folder: str, ext: str) -> int:
        logging.info("Sequential fallback via GET until failure")
        count = 1
        while True:
            resp = self.session.get(f"{img_folder}/{count+1}{ext}", timeout=20, stream=True)
            if resp.status_code == 200 and resp.headers.get('Content-Type','').startswith('image'):
                count += 1
            else:
                break
        logging.info(f"Sequential fallback total pages: {count}")
        return count

    def download_chapter(self, chap_slug: str, chapter_url: str, index: int):
        cleaned_slug = re.sub(r'\d{2}$', '', chap_slug)
        if re.match(r'^\d+(\.\d+)?$', cleaned_slug):
            pdf_filename = f"Capitolo_{cleaned_slug}.pdf"
        else:
            pdf_filename = f"Capitolo_{str(index).zfill(2)}.pdf"

        pdf_path = self.output_folder / pdf_filename
        if pdf_path.exists():
            logging.info(f"Skipping {pdf_filename}, PDF exists")
            return

        try:
            first_src, folder, ext, soup = self.get_first_image_info(chapter_url)
        except Exception as e:
            logging.error(f"Error in chapter {chap_slug} first image: {e}")
            return

        total = self.get_total_pages(chapter_url, soup, folder, ext)
        if total < 1:
            logging.warning(f"No pages for Capitolo {chap_slug}, skipping")
            return

        def fetch_page(i: int):
            candidates = ([first_src] if i == 1
                          else [f"{folder}/{i}{ext}", f"{folder}/{i}{('.png' if ext == '.jpg' else ext)}"])
            for url in candidates:
                try:
                    r = self.session.get(url, timeout=20)
                    r.raise_for_status()
                    im = Image.open(io.BytesIO(r.content)).convert('RGB')
                    tmp2 = Path(tempfile.mkdtemp())
                    p = tmp2 / f"{i:03d}.png"
                    im.save(p)
                    return i, p
                except:
                    continue
            raise RuntimeError(f"Page {i} missing in Capitolo {chap_slug}")

        imgs = {}
        errors = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(fetch_page, i): i for i in range(1, total + 1)}
            for fut in as_completed(futures):
                i = futures[fut]
                try:
                    idx, path = fut.result()
                    imgs[idx] = path
                    logging.info(f"Downloaded page {idx}/{total}")
                except Exception:
                    errors.append(i)

        if errors:
            logging.error(f"Error downloading pages {errors} in Capitolo {chap_slug}")
            return

        pil_images = [Image.open(imgs[i]).convert('RGB') for i in sorted(imgs)]
        pil_images[0].save(
            str(pdf_path),
            format='PDF',
            save_all=True,
            append_images=pil_images[1:]
        )
        logging.info(f"Created PDF {pdf_filename}")

    def close(self):
        self.session.close()

def rename_decimal_versions(folder: Path):
    for pdf in folder.glob('Capitolo_*_*.pdf'):
        match = re.match(r'Capitolo_(\d+)_\d+\.pdf', pdf.name)
        if not match:
            continue
        base_num = match.group(1)
        base_pdf = folder / f'Capitolo_{base_num}.pdf'
        target_pdf = folder / f'Capitolo_{base_num}_1.pdf'
        if base_pdf.exists():
            base_pdf.rename(target_pdf)
            logging.info(f"Rinomina {base_pdf.name} -> {target_pdf.name}")

def main():
    configure_logging()
    urls_input = input("Inserisci uno o più link delle pagine da cui estrarre i capitoli (separati da spazi o virgole): ").strip()
    urls = re.split(r"[\s,]+", urls_input) if urls_input else []
    workers = 8
    for url in urls:
        manga_name = extract_manga_name(url)
        output_folder = Path.home() / "Downloads" / f"{manga_name}_PDF"
        dl = MangaDownloader(url, output_folder, workers)
        try:
            chapters = dl.get_chapter_links()
            if not chapters:
                logging.error("Nessun capitolo trovato.")
                continue
            intervallo = parse_intervallo_input(len(chapters))
            for i in intervallo:
                if 1 <= i <= len(chapters):
                    slug, chapter_url = chapters[i - 1]
                    dl.download_chapter(slug, chapter_url, i)
        finally:
            dl.close()
            rename_decimal_versions(output_folder)

if __name__ == '__main__':
    main()
'''

# ======================================================
# Carica gli script originali come moduli in-memory
# ======================================================

def _load_module_from_source(mod_name: str, source: str) -> types.ModuleType:
    mod = types.ModuleType(mod_name)
    code = compile(source, filename=f'<embedded:{mod_name}>', mode='exec')
    exec(code, mod.__dict__)
    return mod

anime_mod = _load_module_from_source('anime_original', ANIME_SCRIPT_SOURCE)
manga_mod = _load_module_from_source('manga_original', MANGA_SCRIPT_SOURCE)

# ======================================================
# ORCHESTRATORE UNIFICATO
# ======================================================

def _is_anime_link(url: str) -> bool:
    try:
        p = urlparse(url)
        host = p.netloc.lower()
        path = p.path.lower()
        return ('animesaturn' in host)
    except:
        return False


def _is_manga_link(url: str) -> bool:
    try:
        p = urlparse(url)
        host = p.netloc.lower()
        return 'mangaworld' in host
    except:
        return False


def _normalize_links_input(prompt: str) -> list[str]:
    raw = input(prompt).strip()
    return [u for u in re.split(r"[\s,]+", raw) if u]

# Patch solo visualizzazione log Manga per i capitoli rilevati
# Non modifica la logica interna di MangaDownloader

def _apply_manga_log_trim():
    _orig_info = logging.info
    def _info_wrapper(msg, *args, **kwargs):
        try:
            if isinstance(msg, str) and (msg.startswith("First chapter detected:") or msg.startswith("Last chapter detected:")):
                value = msg.split(":", 1)[1].strip()
                if value.isdigit() and len(value) >= 3:
                    msg = msg.replace(value, value[:-2], 1)
        except Exception:
            pass
        return _orig_info(msg, *args, **kwargs)
    logging.info = _info_wrapper

# ------------------------------------------------------
# Raccoglie intervalli per ogni opera prima del download
# ------------------------------------------------------

def _gather_intervals(works):
    intervals = {}
    for kind, url in works:
        if kind == 'anime':
            parsed = urlparse(url)
            base = f"{parsed.scheme}://{parsed.netloc}"
            eps = anime_mod.estrai_episodi(url, base)
            if not eps:
                print(f"[WARN] Nessun episodio trovato per {url}")
                continue
            print(f"[INFO] {len(eps)} episodi trovati per {url}")
            sel = manga_mod.parse_intervallo_input(len(eps))
            intervals[url] = sel
        elif kind == 'manga':
            manga_mod.configure_logging()
            _apply_manga_log_trim()
            dl = manga_mod.MangaDownloader(url, Path('/tmp'), 1)
            try:
                ch = dl.get_chapter_links()
                if not ch:
                    print(f"[WARN] Nessun capitolo trovato per {url}")
                    continue
                print(f"[INFO] {len(ch)} capitoli trovati per {url}")
                sel = manga_mod.parse_intervallo_input(len(ch))
                intervals[url] = sel
            finally:
                dl.close()
    return intervals

# ------------------------------------------------------
# Download funzioni separate
# ------------------------------------------------------

def _anime_process_single(url, sel):
    parsed = urlparse(url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"
    name = re.sub(r'.*/anime/', '', url).split('/')[0]
    folder = Path.home() / "Downloads" / name
    folder.mkdir(parents=True, exist_ok=True)
    eps = anime_mod.estrai_episodi(url, base_url)
    os.chdir(folder)
    to_download = [(i, eps[i-1], f"{i:02d}.mp4") for i in sel if 1 <= i <= len(eps)]
    if not to_download:
        print(f"[INFO] Tutti gli episodi di {name} già scaricati.")
        return
    with ThreadPoolExecutor(max_workers=4) as ex:
        for f in as_completed([ex.submit(anime_mod.download_video, i, u, fn, base_url) for i,u,fn in to_download]):
            f.result()
    print(f"[✓] Download anime '{name}' completato.")


def _manga_process_single(url, sel):
    manga_mod.configure_logging()
    _apply_manga_log_trim()
    name = manga_mod.extract_manga_name(url)
    out = Path.home() / "Downloads" / f"{name}_PDF"
    dl = manga_mod.MangaDownloader(url, out, 8)
    try:
        chapters = dl.get_chapter_links()
        for i in sel:
            if 1 <= i <= len(chapters):
                s, cu = chapters[i-1]
                dl.download_chapter(s, cu, i)
    finally:
        dl.close()
        manga_mod.rename_decimal_versions(out)
        print(f"[✓] Download manga '{name}' completato.")

# ------------------------------------------------------
# MAIN
# ------------------------------------------------------

def main_unified():
    urls = _normalize_links_input("Inserisci uno o più link di anime e/o manga (separati da spazi o virgole): ")
    if not urls:
        print("Nessun link fornito.")
        return
    works = [("anime", u) if _is_anime_link(u) else ("manga", u) for u in urls if _is_anime_link(u) or _is_manga_link(u)]
    if not works:
        print("Nessuna opera valida trovata.")
        return
    intervals = _gather_intervals(works)
    print("\nTutti gli intervalli raccolti. Avvio download...\n")
    total = len(works)
    for i, (kind, url) in enumerate(works, 1):
        print(f"[INFO] [{i}/{total}] Avvio: {url} [{kind}]")
        sel = intervals.get(url, [])
        if not sel:
            print(f"[SKIP] Nessun intervallo selezionato per {url}.")
            continue
        try:
            if kind == 'anime':
                _anime_process_single(url, sel)
            else:
                _manga_process_single(url, sel)
        except Exception as e:
            print(f"[ERROR] Errore su {url}: {e}")
        else:
            print(f"[INFO] [{i}/{total}] Completato: {url}")

if __name__ == '__main__':
    main_unified()
