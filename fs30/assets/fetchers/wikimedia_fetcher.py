"""
Wikimedia Commons Licensed Photo Fetcher.
Queries Wikimedia Commons API, extracts metadata, validates license via LicenseGate,
and indexes approved photos into SQLite.
"""

import requests
import urllib.parse
import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from PIL import Image

from fs30.assets.license_gate import validate_license

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
WIKI_DIR = PROJECT_ROOT / "assets" / "wikimedia"
WIKI_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = PROJECT_ROOT / "assets" / "index.sqlite"

USER_AGENT = "FS30FootballBot/2.0 (https://github.com/antigravity; contact@30footballplus.internal) python-requests"

def search_wikimedia_commons(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """
    Queries Wikimedia Commons API for images matching query,
    parsing license, author, and image dimensions.
    """
    endpoint = "https://commons.wikimedia.org/w/api.php"
    params = {
        "action": "query",
        "format": "json",
        "generator": "search",
        "gsrsearch": f"{query} filetype:bitmap",
        "gsrnamespace": 6,
        "gsrlimit": max_results * 2,
        "prop": "imageinfo",
        "iiprop": "url|size|mime|extmetadata",
        "iiurlwidth": 1200
    }
    headers = {"User-Agent": USER_AGENT}

    try:
        resp = requests.get(endpoint, params=params, headers=headers, timeout=12)
        if resp.status_code != 200:
            return []
        data = resp.json()
    except Exception as e:
        print(f"[WikimediaFetcher] Search request failed: {e}")
        return []

    pages = data.get("query", {}).get("pages", {})
    results = []

    for page_id, p_info in pages.items():
        imageinfo = p_info.get("imageinfo", [])
        if not imageinfo:
            continue
        ii = imageinfo[0]
        meta = ii.get("extmetadata", {})

        lic_name = meta.get("LicenseShortName", {}).get("value", "")
        author = meta.get("Artist", {}).get("value", "Wikimedia Contributor")
        desc = meta.get("ImageDescription", {}).get("value", "")
        lic_url = meta.get("LicenseUrl", {}).get("value", "")
        file_url = ii.get("url")
        w = ii.get("width", 0)
        h = ii.get("height", 0)

        # Clean HTML from author string
        import re
        clean_author = re.sub(r'<[^>]+>', '', author).strip() or "Wikimedia Contributor"

        # Check License Gate
        is_allowed, canonical_lic, attr_req = validate_license(lic_name)
        if not is_allowed:
            continue

        results.append({
            "title": p_info.get("title", ""),
            "url": file_url,
            "width": w,
            "height": h,
            "author": clean_author,
            "license": canonical_lic,
            "license_url": lic_url,
            "attribution_required": 1 if attr_req else 0,
            "description": re.sub(r'<[^>]+>', '', desc).strip()[:120]
        })

        if len(results) >= max_results:
            break

    return results

def download_and_index_wikimedia(item: Dict[str, Any], prefix: str = "wiki") -> Optional[Dict[str, Any]]:
    """Downloads an approved Wikimedia asset, validates image, and indexes into SQLite."""
    file_url = item["url"]
    ext = Path(urllib.parse.urlparse(file_url).path).suffix or ".jpg"
    filename = f"{prefix}_{int(time.time()*1000)%1000000}_{len(item['title'])}".replace(" ", "_") + ext
    dest_path = WIKI_DIR / filename

    headers = {"User-Agent": USER_AGENT}
    try:
        r = requests.get(file_url, headers=headers, timeout=20)
        if r.status_code == 200:
            with open(dest_path, "wb") as f:
                f.write(r.content)
        else:
            return None
    except Exception as e:
        print(f"[WikimediaFetcher] Download failed for {file_url}: {e}")
        return None

    try:
        with Image.open(dest_path) as im:
            w, h = im.size
            sz = dest_path.stat().st_size
            has_alpha = 1 if im.mode in ("RGBA", "LA") else 0
            ar = round(w / float(h), 3) if h > 0 else 1.0
    except Exception:
        dest_path.unlink()
        return None

    # Save to SQLite
    import sqlite3
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    asset_id = f"photo_wiki_{dest_path.stem}"
    tags = ["wikimedia", "photo", "stadium" if "stadium" in item["title"].lower() else "player"]

    cursor.execute("""
        INSERT OR REPLACE INTO assets (
            id, path, pack, type, tags, dominant_colours, has_alpha,
            alpha_coverage, width, height, aspect_ratio, file_size_bytes,
            source_url, author, license, license_url, date_added, attribution_required
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        asset_id, str(dest_path.resolve()), "Wikimedia Commons", "photo",
        json.dumps(tags), "#808080", has_alpha, 0.0, w, h, ar, sz,
        item["url"], item["author"], item["license"], item["license_url"],
        time.strftime("%Y-%m-%dT%H:%M:%SZ"), item["attribution_required"]
    ))
    conn.commit()
    conn.close()

    item["id"] = asset_id
    item["path"] = str(dest_path.resolve())
    return item
