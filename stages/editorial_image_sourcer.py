"""
beta/stages/editorial_image_sourcer.py
High-Fidelity Editorial Image Sourcer for the V7.1.6.7 Broadcast Pipeline.
Fetches ONLY genuine, high-resolution original media:
1. Wikipedia REST API & Wikimedia Commons (official verified player & manager archives).
2. Bing Images Full-Resolution Media Fetcher (downloads full-res 'murl', never low-res thumbnails).
3. Verified 1990s Broadcast Club Crest & Fixture Fallback (never substitutes unrelated players or empty grass).
"""

import io
import re
import json
import time
import html
import random
import urllib.request
import urllib.parse
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set
from PIL import Image, ImageOps, ImageDraw, ImageFont

DISQUALIFIED_DOMAINS = {
    'alamy.com', 'alamy', 'gettyimages.com', 'gettyimages', 'shutterstock.com', 'shutterstock',
    'istockphoto.com', 'stockphoto.com', 'depositphotos.com', 'depositphotos', '123rf.com',
    'adobestock', 'dreamstime.com', 'wallpaperaccess.com', 'wallpapercave.com', 'wallpapersafari.com',
    'pinterest.com', 'pinimg.com', 'i.pinimg.com', 'aliexpress.com', 'amazon.com', 'ebay.com', 'freepik.com', 'vectorstock.com',
    'clipart', 'iconfinder.com', 'flaticon.com', 'deviantart.com', 'lookfordiagnosis.com',
    'panoramastreetline.de', 'panoramastreetline', 'vecteezy.com', 'vecteezy', 'stockcake.com',
    'envato.com', 'graphicriver.net', 'stockfood.com', 'stockfood', 'imago-images', 'rexfeatures',
    'nurphoto', 'afp__', '_afp_', '_npls', '__mockup__', 'splashnews', 'zuma-press', 'sipa-usa',
    'lookaside.instagram.com', 'lookaside.fbsbx.com', 'fbsbx.com', 'dailymotion.com'
}

DISQUALIFIED_TITLE_TERMS = {
    'street view', 'streetview', 'streetline', 'sidewalk', 'brick wall', 'empty road',
    'empty bench', 'empty dugout', 'substitute bench empty', 'illustration', 'vector graphic',
    'clipart', 'cartoon', 'fan art', 'drawing', 'watermark', 'news18', 'match preview',
    'predicted xi', 'probable lineup', 'starting xi', 'dream11', 'fantasy tips',
    'conference hall', 'empty chairs', 'auditorium', 'head to head', 'score prediction',
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/*,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9"
}

class EditorialImageSourcer:
    GLOBAL_LEDGER_PATH = Path(__file__).resolve().parent.parent / "data" / "used_images_global.json"

    def __init__(self):
        self.used_hashes: Set[str] = set()
        self.used_urls: Set[str] = set()
        self.used_phashes: List[int] = []
        self.cross_story_hashes: Set[str] = set()
        self.cross_story_urls: Set[str] = set()
        self.cross_story_phashes: List[int] = []

    def reset(self):
        self.used_hashes.clear()
        self.used_urls.clear()
        self.used_phashes.clear()

    def hydrate_from_ledgers(self, current_ledger: Optional[Any] = None, current_story_id: str = ""):
        """Loads previously used URLs, SHA-256 hashes, and dHashes across scenes & other stories."""
        if current_ledger and getattr(current_ledger, "assets", None):
            for meta in current_ledger.assets.values():
                if meta.get("source_url"):
                    self.used_urls.add(meta["source_url"])
                if meta.get("sha256"):
                    self.used_hashes.add(meta["sha256"])

        if self.GLOBAL_LEDGER_PATH.exists():
            try:
                gdata = json.loads(self.GLOBAL_LEDGER_PATH.read_text(encoding="utf-8"))
                for entry in gdata.get("assets", []):
                    if current_story_id and entry.get("story_id") == current_story_id:
                        continue  # Allow re-generating the same story cleanly without locking itself out
                    if entry.get("url"):
                        self.cross_story_urls.add(entry["url"])
                    if entry.get("sha256"):
                        self.cross_story_hashes.add(entry["sha256"])
                    if entry.get("dhash") is not None:
                        self.cross_story_phashes.append(int(entry["dhash"]))
            except Exception:
                pass

    def record_used_image(self, url: str, sha256_hex: str, dhash_val: int, story_id: str = ""):
        if url:
            self.used_urls.add(url)
        if sha256_hex:
            self.used_hashes.add(sha256_hex)
        if dhash_val is not None:
            self.used_phashes.append(int(dhash_val))
        try:
            self.GLOBAL_LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
            gdata = {"assets": []}
            if self.GLOBAL_LEDGER_PATH.exists():
                gdata = json.loads(self.GLOBAL_LEDGER_PATH.read_text(encoding="utf-8"))
            assets = gdata.get("assets", [])
            assets.append({"story_id": story_id, "url": url, "sha256": sha256_hex, "dhash": int(dhash_val)})
            gdata["assets"] = assets[-400:]  # Bounded global window
            self.GLOBAL_LEDGER_PATH.write_text(json.dumps(gdata, indent=2), encoding="utf-8")
        except Exception:
            pass

    def is_url_or_hash_used(self, url: str = "", sha256_hex: str = "", dhash_val: Optional[int] = None) -> bool:
        if url and (url in self.used_urls or url in self.cross_story_urls):
            return True
        if sha256_hex and (sha256_hex in self.used_hashes or sha256_hex in self.cross_story_hashes):
            return True
        if dhash_val is not None:
            for existing in self.used_phashes + self.cross_story_phashes:
                if bin(int(dhash_val) ^ int(existing)).count("1") <= 6:
                    return True
        return False

    def fetch_wikipedia_player_photos(self, player_name: str, max_results: int = 6) -> List[Dict[str, Any]]:
        """Extracts genuine match & portrait photos from Wikipedia's official media archive, converting to full-res originals."""
        candidates = []
        if not player_name:
            return candidates
        def _fetch_media_list(wiki_title: str) -> List[Dict[str, Any]]:
            found = []
            c_title = urllib.parse.quote(wiki_title.strip().replace(" ", "_"))
            url = f"https://en.wikipedia.org/api/rest_v1/page/media-list/{c_title}"
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "FootballNewsDesk/2.0 (broadcast@footballin30sec.com)"}
            )
            with urllib.request.urlopen(req, timeout=8) as r:
                data = json.loads(r.read().decode('utf-8'))
            for it in data.get("items", []):
                title = it.get("title", "")
                if title.endswith((".svg", ".ogg", ".ogv", ".pdf", ".tif")):
                    continue
                srcset = it.get("srcset", [])
                src = srcset[-1].get("src", "") if srcset else it.get("src", "")
                if src:
                    if src.startswith("//"):
                        src = "https:" + src
                    full_res_url = src
                    if "thumb.wikimedia.org/wikipedia/commons/thumb/" in src:
                        m = re.match(r'https://thumb\.wikimedia\.org/wikipedia/commons/thumb/([0-9a-f]/[0-9a-f]{2}/[^/]+)/.*', src)
                        if m:
                            full_res_url = f"https://upload.wikimedia.org/wikipedia/commons/{m.group(1)}"
                    if full_res_url not in self.used_urls:
                        found.append({
                            "url": full_res_url,
                            "title": title,
                            "source": "Wikipedia Official Archive (Original)",
                            "priority": 2
                        })
                        if len(found) >= max_results:
                            break
            return found

        try:
            candidates = _fetch_media_list(player_name)
        except Exception:
            candidates = []

        # Canonical accent/disambiguation fallback via opensearch (e.g. 'Luis Suarez' -> 'Luis Suárez (footballer, born 1987)')
        if not candidates:
            for q_os in (f"{player_name} footballer", player_name):
                try:
                    os_url = f"https://en.wikipedia.org/w/api.php?action=opensearch&search={urllib.parse.quote(q_os)}&limit=4&format=json"
                    os_req = urllib.request.Request(os_url, headers={"User-Agent": "FootballNewsDesk/2.0 (broadcast@footballin30sec.com)"})
                    with urllib.request.urlopen(os_req, timeout=8) as r:
                        os_data = json.loads(r.read().decode('utf-8'))
                    titles = [str(w).strip() for w in (os_data[1] if len(os_data) > 1 else []) if w]
                    titles.sort(key=lambda t: (0 if "football" in t.lower() or "soccer" in t.lower() else 1))
                    for wt in titles[:3]:
                        try:
                            candidates = _fetch_media_list(wt)
                            if candidates:
                                break
                        except Exception:
                            continue
                    if candidates:
                        break
                except Exception:
                    continue
        return candidates

    def search_wikimedia_commons(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Queries Wikimedia Commons for public domain football media."""
        candidates = []
        try:
            wiki_url = f"https://commons.wikimedia.org/w/api.php?action=query&generator=search&gsrsearch={urllib.parse.quote(query)}&gsrnamespace=6&gsrlimit={max_results}&prop=imageinfo&iiprop=url|size&format=json"
            req = urllib.request.Request(
                wiki_url,
                headers={"User-Agent": "FootballNewsDesk/2.0 (broadcast@footballin30sec.com)"}
            )
            with urllib.request.urlopen(req, timeout=8) as r:
                w_data = json.loads(r.read().decode('utf-8'))
            pages = w_data.get('query', {}).get('pages', {})
            for _, pinfo in pages.items():
                img_info = pinfo.get('imageinfo', [{}])[0]
                u = img_info.get('url')
                w = img_info.get('width', 0)
                h = img_info.get('height', 0)
                if u and not u.endswith(('.svg', '.ogg', '.ogv')) and w >= 600 and h >= 600:
                    if u not in self.used_urls:
                        candidates.append({
                            "url": u,
                            "title": pinfo.get("title", ""),
                            "source": "Wikimedia Commons",
                            "priority": 2
                        })
        except Exception:
            pass
        return candidates

    def search_bing_full_res(self, query: str, avoid_terms: List[str] = None, max_results: int = 15) -> List[Dict[str, Any]]:
        """Searches Bing Images and extracts full-resolution media URLs (murl)."""
        candidates = []
        clean_q = query.replace('"', '').strip()
        url = f"https://www.bing.com/images/async?q={urllib.parse.quote(clean_q)}&first=0&count=35&mmasync=1"
        req = urllib.request.Request(url, headers=HEADERS)
        try:
            with urllib.request.urlopen(req, timeout=8) as resp:
                raw_html = resp.read().decode("utf-8", errors="ignore")
            matches = re.findall(r'm=[\'"](\{.*?\})[\'"]', raw_html)
            avoid = [a.lower() for a in (avoid_terms or [])]
            for m in matches:
                clean = html.unescape(m)
                try:
                    data = json.loads(clean)
                    murl = data.get("murl")
                    title = data.get("t", "")
                    purl = data.get("purl", "")
                    if not murl or murl in self.used_urls:
                        continue

                    # Domain check
                    murl_lower = murl.lower()
                    title_lower = title.lower()
                    if any(bad in murl_lower or bad in title_lower for bad in DISQUALIFIED_DOMAINS):
                        continue

                    # Disqualified title / subject check (no streetlines, empty benches, drawings)
                    if any(bad_term in title_lower for bad_term in DISQUALIFIED_TITLE_TERMS):
                        continue

                    # Avoid terms check
                    if any(av in title_lower for av in avoid):
                        continue

                    candidates.append({
                        "url": murl,
                        "title": title,
                        "page_url": purl,
                        "source": f"Bing Full-Res ({clean_q[:25]})",
                        "priority": 3
                    })
                    if len(candidates) >= max_results:
                        break
                except Exception:
                    continue
        except Exception as e:
            print(f"[ImageSourcer] Bing search note for '{clean_q}': {e}")
        return candidates

    def fetch_espn_photo_bank(self, entity_name: str, club_name: str = "", max_results: int = 8) -> List[Dict[str, Any]]:
        """Polls public ESPN soccer APIs across PL, UCL, La Liga, Serie A & Bundesliga for high-res photos."""
        candidates: List[Dict[str, Any]] = []
        if not hasattr(self, "_espn_cache"):
            self._espn_cache = []
            endpoints = [
                "https://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/news?limit=25",
                "https://site.api.espn.com/apis/site/v2/sports/soccer/uefa.champions/news?limit=20",
                "https://site.api.espn.com/apis/site/v2/sports/soccer/esp.1/news?limit=15",
                "https://site.api.espn.com/apis/site/v2/sports/soccer/ita.1/news?limit=15",
                "https://site.api.espn.com/apis/site/v2/sports/soccer/ger.1/news?limit=15",
            ]
            for ep in endpoints:
                try:
                    req = urllib.request.Request(ep, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
                    with urllib.request.urlopen(req, timeout=8) as r:
                        data = json.loads(r.read().decode("utf-8", errors="ignore"))
                    for art in data.get("articles", []):
                        hl = html.unescape((art.get("headline") or "").strip())
                        desc = html.unescape((art.get("description") or "").strip())
                        for im in (art.get("images") or []):
                            iu = (im.get("url") or "").strip()
                            if iu and iu.startswith("http") and "dm_" not in iu.lower():
                                self._espn_cache.append({"url": iu, "title": f"{hl} {im.get('caption', '')} {desc[:120]}".strip()})
                except Exception:
                    continue

        import unicodedata
        def _fold(s: str) -> str:
            return "".join(ch for ch in unicodedata.normalize("NFKD", s.lower()) if not unicodedata.combining(ch))

        ent_tokens = [_fold(t) for t in (entity_name or "").split() if len(t) > 2]
        club_tokens = [_fold(t) for t in (club_name or "").split() if len(t) > 3]
        for row in self._espn_cache:
            u = row["url"]
            if u in self.used_urls or any(b in u.lower() for b in DISQUALIFIED_DOMAINS):
                continue
            t_low = _fold(row["title"])
            ent_hit = ent_tokens and all(tok in t_low for tok in ent_tokens[:2])
            club_hit = club_tokens and any(ct in t_low for ct in club_tokens)
            if ent_hit or club_hit:
                candidates.append({
                    "url": u,
                    "title": row["title"],
                    "source": "ESPN Public Media Archive",
                    "priority": 1 if ent_hit else 3,
                })
                if len(candidates) >= max_results:
                    break
        return candidates

    def search_news_article_images(self, query: str, avoid_terms: List[str] = None, max_results: int = 8) -> List[Dict[str, Any]]:
        """Extracts genuine og:image / JSON-LD photos directly from current sports journalism articles."""
        candidates: List[Dict[str, Any]] = []
        avoid = [a.lower() for a in (avoid_terms or [])]
        try:
            import xml.etree.ElementTree as ET
            try:
                from stages.url_scraper import scrape_article_from_url
            except ModuleNotFoundError:
                from stages.url_scraper import scrape_article_from_url

            rss_url = f"https://www.bing.com/news/search?q={urllib.parse.quote(query + ' football')}&format=rss"
            req = urllib.request.Request(rss_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
            with urllib.request.urlopen(req, timeout=8) as r:
                root = ET.fromstring(r.read())
            for it in root.findall(".//item")[:6]:
                raw_link = (it.findtext("link") or "").strip()
                item_title = html.unescape((it.findtext("title") or "").strip())
                direct_url = raw_link
                try:
                    qs = urllib.parse.parse_qs(urllib.parse.urlparse(raw_link).query)
                    if "url" in qs:
                        direct_url = qs["url"][0]
                except Exception:
                    pass
                if not direct_url or any(av in item_title.lower() for av in avoid):
                    continue
                try:
                    art = scrape_article_from_url(direct_url, timeout=6)
                    for img_u in (art.get("candidate_images") or [])[:2]:
                        if img_u in self.used_urls or any(b in img_u.lower() for b in DISQUALIFIED_DOMAINS):
                            continue
                        candidates.append({
                            "url": img_u,
                            "title": art.get("title") or item_title,
                            "page_url": direct_url,
                            "source": f"Editorial Article ({art.get('source', 'Press')})",
                            "priority": 1,
                        })
                        if len(candidates) >= max_results:
                            return candidates
                except Exception:
                    continue
        except Exception as e:
            print(f"[ImageSourcer] Article hero search note for '{query}': {e}")
        return candidates

    def search_social_editorial_candidates(self, entity_name: str, club_name: str = "", avoid_terms: List[str] = None, max_results: int = 12) -> List[Dict[str, Any]]:
        """Sources public sports & social-syndicated imagery (ESPN, BBC, Sky, PL, Fabrizio/Reddit press coverage)."""
        results: List[Dict[str, Any]] = []
        queries = [
            f"{entity_name} {club_name} ESPN FC match".strip(),
            f"{entity_name} {club_name} Sky Sports BBC action".strip(),
            f"{entity_name} {club_name} premier league instagram photo".strip(),
            f"{entity_name} {club_name} reddit Fabrizio Romano".strip(),
        ]
        seen_u: Set[str] = set()
        for q in queries:
            for cand in self.search_bing_full_res(q, avoid_terms=avoid_terms, max_results=6):
                u = cand.get("url", "")
                if u and u not in seen_u:
                    seen_u.add(u)
                    cand["priority"] = 2
                    results.append(cand)
                    if len(results) >= max_results:
                        return results
        return results

    def download_image_bytes(self, url: str) -> Optional[bytes]:
        """Downloads full-resolution image bytes and validates MIME Content-Type & magic image header."""
        req = urllib.request.Request(url, headers=HEADERS)
        try:
            with urllib.request.urlopen(req, timeout=7) as resp:
                ctype = (resp.headers.get("Content-Type") or "").lower()
                if ctype and ("html" in ctype or "text/" in ctype or "json" in ctype):
                    return None
                data = resp.read()
            if len(data) < 30000:  # Reject tiny files < 30KB
                return None
            # Verify genuine raster image magic bytes (JPEG, PNG, WebP) so login walls never sneak through
            is_jpeg = data[:3] == b"\xff\xd8\xff"
            is_png = data[:8] == b"\x89PNG\r\n\x1a\n"
            is_webp = data[:4] == b"RIFF" and data[8:12] == b"WEBP"
            if not (is_jpeg or is_png or is_webp):
                return None
            return data
        except Exception:
            return None

    def _remove_crest_background(self, pil_img: Image.Image) -> Image.Image:
        """
        Ensures any club crest has a transparent cutout background:
        - Preserves native RGBA transparency if already present (<85% opaque corners).
        - Otherwise flood-fills uniform corner-connected outer background with smooth anti-aliased feathering.
        """
        import numpy as np
        import cv2
        from PIL import ImageFilter

        rgba = pil_img.convert("RGBA")
        arr = np.array(rgba)
        h, w = arr.shape[:2]
        if h < 16 or w < 16:
            return rgba

        # Check existing alpha transparency first (even if geometric logo touches corners!)
        corners_a = [arr[0, 0, 3], arr[0, w - 1, 3], arr[h - 1, 0, 3], arr[h - 1, w - 1, 3]]
        trans_frac = float(np.count_nonzero(arr[:, :, 3] < 40)) / float(max(1, h * w))
        if sum(1 for a in corners_a if a < 20) >= 2 or trans_frac >= 0.05:
            bb = rgba.getbbox()
            return rgba.crop(bb) if bb else rgba

        # Corner flood-fill against uniform box background (e.g. white or dark backdrop around club badge)
        rgb = arr[:, :, :3].copy()
        bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
        mask = np.zeros((h + 2, w + 2), np.uint8)
        corners = [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]
        for sx, sy in corners:
            diff = (20, 20, 20)
            cv2.floodFill(bgr.copy(), mask, (sx, sy), (0, 0, 0), diff, diff, flags=cv2.FLOODFILL_MASK_ONLY | (255 << 8))

        bg_mask = (mask[1:-1, 1:-1] == 255)
        bg_frac = float(np.count_nonzero(bg_mask)) / float(max(1, h * w))
        if 0.02 <= bg_frac <= 0.88:
            alpha = np.where(bg_mask, 0, 255).astype(np.uint8)
            alpha_img = Image.fromarray(alpha, mode="L").filter(ImageFilter.GaussianBlur(radius=0.8))
            arr[:, :, 3] = np.array(alpha_img)
            out = Image.fromarray(arr, mode="RGBA")
            bb = out.getbbox()
            return out.crop(bb) if bb else out

        # Fast lightweight u2netp fallback only if background is textured/photographic
        try:
            import rembg
            session = rembg.new_session("u2netp")
            cut = rembg.remove(rgba.convert("RGB"), session=session)
            bb = cut.getbbox()
            return cut.crop(bb) if bb else cut
        except Exception:
            return rgba

    def fetch_club_crest_cutout(self, club_name: str, out_path: Path) -> Optional[Path]:
        """
        Fetches a verified, background-removed RGBA transparent PNG crest/logo for `club_name`
        from Wikipedia / Wikimedia Commons (strictly checking club tokens to block wrong clubs).
        """
        if not club_name:
            return None
        club_clean = club_name.strip()
        tokens = [
            t.lower() for t in re.findall(r"[a-zA-ZÀ-ÿ]{3,}", club_clean)
            if t.lower() not in ("football", "club", "futbol", "calcio", "united") or len(club_clean.split()) == 1
        ]
        if not tokens:
            tokens = [t.lower() for t in re.findall(r"[a-zA-ZÀ-ÿ]{3,}", club_clean)]

        candidate_urls: List[str] = []
        headers = {"User-Agent": "FootballNewsDesk/2.0 (broadcast@footballin30sec.com)"}

        # 1. Resolve canonical Wikipedia club article first
        club_titles: List[str] = []
        for q in (f"{club_clean} F.C.", f"{club_clean} football club", club_clean):
            try:
                os_u = f"https://en.wikipedia.org/w/api.php?action=opensearch&search={urllib.parse.quote(q)}&limit=3&format=json"
                req = urllib.request.Request(os_u, headers=headers)
                with urllib.request.urlopen(req, timeout=6) as r:
                    res = json.loads(r.read().decode("utf-8"))
                for t in (res[1] if len(res) > 1 else []):
                    tl = t.lower()
                    if any(tok in tl for tok in tokens) and t not in club_titles:
                        club_titles.append(t)
            except Exception:
                continue

        # 2. Extract crest / logo / badge SVG-rendered PNG or PNG from club Wikipedia summary + media-list
        for wt in club_titles[:2]:
            slug = urllib.parse.quote(wt.replace(" ", "_"))
            try:
                ml_url = f"https://en.wikipedia.org/api/rest_v1/page/media-list/{slug}"
                req = urllib.request.Request(ml_url, headers=headers)
                with urllib.request.urlopen(req, timeout=7) as r:
                    data = json.loads(r.read().decode("utf-8"))
                for it in data.get("items", []):
                    title = (it.get("title") or "").lower()
                    if not any(k in title for k in ("logo", "crest", "badge", "shield", "pictogram", club_clean.split()[0].lower())):
                        continue
                    srcset = it.get("srcset", [])
                    src = srcset[-1].get("src", "") if srcset else it.get("src", "")
                    if not src:
                        continue
                    if src.startswith("//"):
                        src = "https:" + src
                    # Request crisp >= 640px PNG thumbnail for SVG logos (preserves crisp alpha channel!)
                    if ".svg" in src and "/thumb/" in src:
                        src = re.sub(r"/\d+px-([^/]+\.png)$", r"/640px-\1", src)
                    elif src.lower().endswith(".svg") and "/commons/" in src:
                        # Convert direct .svg URL to PNG thumb URL cleanly
                        m_svg = re.match(r"https://upload\.wikimedia\.org/wikipedia/(?:commons|en)/([0-9a-f]/[0-9a-f]{2}/([^/]+\.svg))$", src)
                        if m_svg:
                            base = "commons" if "/commons/" in src else "en"
                            src = f"https://upload.wikimedia.org/wikipedia/{base}/thumb/{m_svg.group(1)}/640px-{m_svg.group(2)}.png"
                    if not src.lower().endswith(".svg"):
                        candidate_urls.append(src)
            except Exception:
                continue

        # 3. Wikimedia Commons fallback specifically for "{club_name} logo"
        if not candidate_urls:
            try:
                cm_u = (
                    "https://commons.wikimedia.org/w/api.php?action=query&generator=search"
                    f"&gsrsearch={urllib.parse.quote(club_clean + ' football logo')}&gsrnamespace=6&gsrlimit=6"
                    "&prop=imageinfo&iiprop=url|mime&iiurlwidth=640&format=json"
                )
                req = urllib.request.Request(cm_u, headers=headers)
                with urllib.request.urlopen(req, timeout=7) as r:
                    cm = json.loads(r.read().decode("utf-8"))
                for _, p in cm.get("query", {}).get("pages", {}).items():
                    t_low = (p.get("title") or "").lower()
                    if not any(tok in t_low for tok in tokens):
                        continue
                    info = p.get("imageinfo", [{}])[0]
                    thumb = info.get("thumburl") or info.get("url")
                    if thumb and not thumb.lower().endswith(".svg"):
                        candidate_urls.append(thumb)
            except Exception:
                pass

        for cu in candidate_urls[:6]:
            try:
                req = urllib.request.Request(cu, headers=headers)
                with urllib.request.urlopen(req, timeout=8) as r:
                    raw_b = r.read()
                if len(raw_b) < 2000:
                    continue
                pil = Image.open(io.BytesIO(raw_b))
                cut_crest = self._remove_crest_background(pil)
                if min(cut_crest.size) < 80:
                    continue
                out_path.parent.mkdir(parents=True, exist_ok=True)
                cut_crest.save(str(out_path), "PNG")
                print(f"[ImageSourcer] Fetched background-cut club crest for '{club_clean}' ({cut_crest.width}x{cut_crest.height}) -> {out_path.name}")
                return out_path
            except Exception:
                continue
        return None

    def generate_broadcast_crest_fallback(self, club_name: str, out_path: Path) -> bool:
        """Generates a 1990s broadcast club crest card featuring the real transparent club logo when possible."""
        out_path.parent.mkdir(parents=True, exist_ok=True)
        w, h = 1080, 1920
        img = Image.new("RGBA", (w, h), (14, 22, 38, 255))
        draw = ImageDraw.Draw(img)

        for r in range(440, 0, -24):
            alpha = int(42 * (1 - r / 440))
            draw.ellipse(
                [(w//2 - r, h//2 - 220 - r), (w//2 + r, h//2 - 220 + r)],
                outline=(24 + alpha, 38 + alpha, 64 + alpha, 255),
                width=12
            )

        crest_tmp = out_path.with_name(out_path.stem + "_crest_alpha.png")
        real_crest = self.fetch_club_crest_cutout(club_name, crest_tmp)
        if real_crest and real_crest.exists():
            with Image.open(real_crest) as cr:
                cr = cr.convert("RGBA")
                scale = min(460.0 / float(cr.width), 460.0 / float(cr.height))
                nw, nh = max(1, int(cr.width * scale)), max(1, int(cr.height * scale))
                cr_res = cr.resize((nw, nh), Image.Resampling.LANCZOS)
                px, py = (w - nw) // 2, 540 + (460 - nh) // 2
                img.paste(cr_res, (px, py), cr_res)
            try:
                crest_tmp.unlink(missing_ok=True)
            except Exception:
                pass
            try:
                title_font = ImageFont.truetype("arialbd.ttf", 52)
            except Exception:
                title_font = ImageFont.load_default()
            draw.text((w // 2, 1085), club_name.upper(), font=title_font, fill=(255, 255, 255, 255), anchor="mm")
            img.convert("RGB").save(out_path, quality=95)
            print(f"[ImageSourcer] Created real-logo broadcast card for '{club_name}' -> {out_path.name}")
            return True

        # Broadcast studio diagonal stripe accent
        for offset in range(-h, w + h, 140):
            draw.line([(offset, 0), (offset - 450, h)], fill=(18, 28, 48), width=18)

        # Draw Club Emblem / Heraldic Shield placeholder
        shield_top = 560
        shield_w = 560
        shield_h = 520
        draw.rectangle(
            [(w//2 - shield_w//2, shield_top), (w//2 + shield_w//2, shield_top + shield_h)],
            outline=(220, 38, 38) if "united" in club_name.lower() else (255, 255, 255),
            width=8
        )
        draw.rectangle(
            [(w//2 - shield_w//2 + 14, shield_top + 14), (w//2 + shield_w//2 - 14, shield_top + shield_h - 14)],
            fill=(20, 30, 50),
            outline=(180, 180, 180),
            width=3
        )

        # Load bold TrueType fonts for readable 90s broadcast card
        try:
            title_font = ImageFont.truetype("arialbd.ttf", 62)
            sub_font = ImageFont.truetype("arialbd.ttf", 30)
        except Exception:
            title_font = ImageFont.load_default()
            sub_font = ImageFont.load_default()

        draw.text(
            (w//2, shield_top + shield_h//2 - 36),
            club_name.upper(),
            font=title_font,
            fill=(255, 255, 255),
            anchor="mm"
        )
        draw.text(
            (w//2, shield_top + shield_h//2 + 38),
            "OFFICIAL CLUB DOSSIER",
            font=sub_font,
            fill=(242, 200, 48),
            anchor="mm"
        )

        img.convert("RGB").save(out_path, quality=95)
        print(f"[ImageSourcer] Created authoritative broadcast crest card for '{club_name}' -> {out_path.name}")
        return True
