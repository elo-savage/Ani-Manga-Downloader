#!/usr/bin/env python3
"""Debug: stampa i capitoli trovati dal scraper per capire cosa viene estratto."""
import sys, re, requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

url = sys.argv[1] if len(sys.argv) > 1 else "https://www.mangaworld.mx/manga/1708/one-piece"

print(f"Fetching: {url}")
resp = requests.get(url, timeout=15)
print(f"Status: {resp.status_code}")
soup = BeautifulSoup(resp.text, "html.parser")

# 1. Check all /read/ links
anchors = soup.select('a[href*="/read/"]')
print(f"\n=== <a href*=/read/> links: {len(anchors)} ===")
for i, a in enumerate(anchors[:20]):
    print(f"  [{i}] text={a.get_text(strip=True)[:60]!r}  href={a.get('href','')[:100]}")

# 2. Check data-href
data_anchors = soup.select('[data-href*="/read/"]')
print(f"\n=== [data-href*=/read/] elements: {len(data_anchors)} ===")
for i, a in enumerate(data_anchors[:20]):
    print(f"  [{i}] tag={a.name} text={a.get_text(strip=True)[:60]!r}  data-href={a.get('data-href','')[:100]}")

# 3. Check chapter class elements
chapter_els = soup.select('.chapter, .chapter-link, [class*="chapter"], [class*="Chapter"]')
print(f"\n=== Elements with 'chapter' in class: {len(chapter_els)} ===")
for i, el in enumerate(chapter_els[:20]):
    cls = el.get('class', [])
    href = el.get('href', el.get('data-href', ''))
    print(f"  [{i}] tag={el.name} class={cls} text={el.get_text(strip=True)[:60]!r}  href={str(href)[:100]}")

# 4. Look for any other link patterns
all_links = soup.find_all('a', href=True)
read_links = [a for a in all_links if '/read/' in a['href'] or '/chapter/' in a['href']]
print(f"\n=== All links with /read/ or /chapter/: {len(read_links)} ===")
for i, a in enumerate(read_links[:10]):
    print(f"  [{i}] text={a.get_text(strip=True)[:60]!r}  href={a['href'][:120]}")

# 5. Run the actual extraction logic
seen = set()
chapters = []
for a in anchors:
    text = a.get_text(strip=True)
    if re.search(r"\bprimo capitolo\b", text, re.IGNORECASE) or \
       re.search(r"\bultimo capitolo\b", text, re.IGNORECASE):
        continue
    href = a.get("href", "")
    if not href or (not href.startswith("/read/") and "/read/" not in href):
        continue
    href = urljoin(url, href)
    if href in seen:
        continue
    seen.add(href)
    m = re.search(r"Capitolo\s*([\d\.]+)", text, re.IGNORECASE)
    slug = m.group(1) if m else href.rstrip("/").split("/")[-1]
    chapters.append((slug, href))

print(f"\n=== Extracted chapters: {len(chapters)} ===")
for i, (slug, href) in enumerate(chapters[:15]):
    print(f"  [{i+1}] slug={slug!r}  url={href[:120]}")
print("  ...")
for i, (slug, href) in enumerate(chapters[-5:], len(chapters)-4):
    print(f"  [{i}] slug={slug!r}  url={href[:120]}")
