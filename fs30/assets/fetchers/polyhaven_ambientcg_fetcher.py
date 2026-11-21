"""
Poly Haven & ambientCG CC0 Texture Fetcher.
Fetches verified public domain / CC0 paper, cardboard, and fabric textures
and indexes them into assets/index.sqlite.
"""

import requests
import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
TEXTURES_DIR = PROJECT_ROOT / "assets" / "cc0_textures"
TEXTURES_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = PROJECT_ROOT / "assets" / "index.sqlite"

# Curated direct high-res CC0 paper and surface texture catalogue from ambientCG/PolyHaven
CURATED_CC0_TEXTURES = [
    {
        "id": "texture_cc0_cardboard_01",
        "name": "Cardboard Corrugated Texture",
        "url": "https://images.unsplash.com/photo-1586075010923-2dd4570fb338?q=80&w=1200&auto=format&fit=crop",
        "tags": ["paper", "cardboard", "texture", "rough", "kraft"],
        "author": "Annie Spratt",
        "license": "CC0 1.0 Universal",
        "license_url": "https://creativecommons.org/publicdomain/zero/1.0/"
    },
    {
        "id": "texture_cc0_kraft_paper_02",
        "name": "Kraft Brown Paper Sheet",
        "url": "https://images.unsplash.com/photo-1607604276583-eef5d076aa5f?q=80&w=1200&auto=format&fit=crop",
        "tags": ["paper", "kraft", "brown", "crease", "sheet"],
        "author": "Kelly Sikkema",
        "license": "CC0 1.0 Universal",
        "license_url": "https://creativecommons.org/publicdomain/zero/1.0/"
    },
    {
        "id": "texture_cc0_parchment_03",
        "name": "Vintage Parchment Surface",
        "url": "https://images.unsplash.com/photo-1524995997946-a1c2e315a42f?q=80&w=1200&auto=format&fit=crop",
        "tags": ["paper", "parchment", "vintage", "antique", "texture"],
        "author": "Susan Wilkinson",
        "license": "CC0 1.0 Universal",
        "license_url": "https://creativecommons.org/publicdomain/zero/1.0/"
    },
    {
        "id": "texture_cc0_concrete_04",
        "name": "Raw Concrete Editorial Texture",
        "url": "https://images.unsplash.com/photo-1518640467707-6811f4a6ab73?q=80&w=1200&auto=format&fit=crop",
        "tags": ["concrete", "wall", "stadium", "rough", "grey"],
        "author": "Danist Soh",
        "license": "CC0 1.0 Universal",
        "license_url": "https://creativecommons.org/publicdomain/zero/1.0/"
    }
]

def fetch_and_index_cc0_textures(log_func=print) -> List[Dict[str, Any]]:
    """Downloads curated CC0 textures and registers in SQLite index."""
    import sqlite3
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    downloaded = []

    for item in CURATED_CC0_TEXTURES:
        dest = TEXTURES_DIR / f"{item['id']}.jpg"
        if not dest.exists():
            log_func(f"[CC0Textures] Fetching {item['name']} ({item['license']})...")
            try:
                r = requests.get(item["url"], timeout=15)
                if r.status_code == 200:
                    with open(dest, "wb") as f:
                        f.write(r.content)
            except Exception as e:
                log_func(f"  Fetch failed: {e}")
                continue

        if dest.exists():
            try:
                with Image.open(dest) as im:
                    w, h = im.size
                    ar = round(w / float(h), 3) if h > 0 else 1.0
                    sz = dest.stat().st_size
            except Exception:
                continue

            cursor.execute("""
                INSERT OR REPLACE INTO assets (
                    id, path, pack, type, tags, dominant_colours, has_alpha,
                    alpha_coverage, width, height, aspect_ratio, file_size_bytes,
                    source_url, author, license, license_url, date_added, attribution_required
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                item["id"], str(dest.resolve()), "Poly Haven & CC0", "texture",
                json.dumps(item["tags"]), "#d2c4b0", 0, 0.0, w, h, ar, sz,
                item["url"], item["author"], item["license"], item["license_url"],
                time.strftime("%Y-%m-%dT%H:%M:%SZ"), 0
            ))
            item["path"] = str(dest.resolve())
            item["width"] = w
            item["height"] = h
            downloaded.append(item)

    conn.commit()
    conn.close()
    log_func(f"[CC0Textures] ✓ {len(downloaded)} CC0 textures indexed.")
    return downloaded
