"""
Universal Single-URL Article & Media Extractor for 30 Football Plus (V2.5).
Given any football news URL (Sky Sports, BBC, Guardian, ESPN, Goal, club sites):
- Attribute-order-agnostic <meta> parser (og:title, og:image, twitter:image, description)
- JSON-LD schema articleBody + high-res image array extraction
- Clean <article>/<figure> hero & inline editorial image harvesting
- Automatic Guardian text-banner overlay parameter stripping (?overlay-base64=...)
"""

import re
import json
import urllib.request
import urllib.parse
import html as html_lib
from typing import Dict, Any, Optional, List

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

BAD_IMAGE_HINTS = (
    "favicon", "logo", "sprite", "avatar", "placeholder", "default.", "1x1",
    "pixel", "doubleclick", "googlesyndication", "guardian-logo", "bbc_sport_logo",
    "lookaside.instagram.com", "lookaside.fbsbx.com",
)


def _clean_editorial_image_url(url: str) -> str:
    """Strips publisher overlay watermarks (e.g. Guardian base64 bottom banners) and HTML entities."""
    if not url:
        return ""
    u = html_lib.unescape(url.strip())
    if u.startswith("//"):
        u = "https:" + u
    if "i.guim.co.uk" in u:
        parsed = urllib.parse.urlparse(u)
        qs = urllib.parse.parse_qs(parsed.query, keep_blank_values=True)
        for bad_k in ("overlay-base64", "overlay-width", "overlay-align"):
            qs.pop(bad_k, None)
        # Prefer uncropped master width when query manipulation doesn't break signed URL;
        # note Guardian signed URLs reject signature mismatch if `s=` present, so strip overlays only if unsigned
        if "s" not in qs:
            new_q = urllib.parse.urlencode(qs, doseq=True)
            u = urllib.parse.urlunparse(parsed._replace(query=new_q))
        elif "overlay-base64" in u:
            # Skip signed Guardian card URLs that hardcode a giant text banner overlay
            return ""
    return u


def _is_valid_article_image(url: str) -> bool:
    u_low = (url or "").lower()
    if not u_low.startswith("http"):
        return False
    if any(b in u_low for b in BAD_IMAGE_HINTS):
        return False
    if u_low.endswith((".svg", ".gif", ".ico")):
        return False
    return True


def _extract_meta_map(page_html: str) -> Dict[str, str]:
    """Attribute-order-agnostic <meta> extractor mapping property/name -> content."""
    meta: Dict[str, str] = {}
    for m in re.finditer(r"<meta\b([^>]+)>", page_html, re.IGNORECASE):
        attrs = m.group(1)
        prop_m = re.search(r'(?:property|name)\s*=\s*["\']([^"\']+)["\']', attrs, re.IGNORECASE)
        cont_m = re.search(r'content\s*=\s*["\']([^"\']+)["\']', attrs, re.IGNORECASE)
        if prop_m and cont_m:
            k = prop_m.group(1).strip().lower()
            if k not in meta:
                meta[k] = html_lib.unescape(cont_m.group(1).strip())
    return meta


def _extract_json_ld_details(page_html: str) -> Dict[str, Any]:
    """Extracts headline, articleBody, and high-res image URLs from schema.org JSON-LD blocks."""
    out: Dict[str, Any] = {"images": [], "body": "", "headline": ""}
    for m in re.finditer(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', page_html, re.DOTALL | re.IGNORECASE):
        raw = m.group(1).strip()
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except Exception:
            continue
        items = data if isinstance(data, list) else ([data] + data.get("@graph", []) if isinstance(data, dict) else [])
        for obj in items:
            if not isinstance(obj, dict):
                continue
            if not out["headline"] and isinstance(obj.get("headline"), str):
                out["headline"] = html_lib.unescape(obj["headline"].strip())
            if not out["body"] and isinstance(obj.get("articleBody"), str):
                out["body"] = html_lib.unescape(re.sub(r"\s+", " ", obj["articleBody"]).strip())
            imgs = obj.get("image")
            if isinstance(imgs, str):
                imgs = [imgs]
            elif isinstance(imgs, dict):
                imgs = [imgs.get("url") or imgs.get("contentUrl") or ""]
            elif isinstance(imgs, list):
                flat = []
                for x in imgs:
                    if isinstance(x, str):
                        flat.append(x)
                    elif isinstance(x, dict):
                        flat.append(x.get("url") or x.get("contentUrl") or "")
                imgs = flat
            else:
                imgs = []
            for iu in imgs:
                cleaned = _clean_editorial_image_url(str(iu))
                if _is_valid_article_image(cleaned) and cleaned not in out["images"]:
                    out["images"].append(cleaned)
    return out


def _try_espn_core_api(url: str, timeout: int = 8) -> Optional[Dict[str, Any]]:
    """Fast-path structured JSON extractor for espn.com/espnfc story URLs."""
    if "espn" not in (url or "").lower():
        return None
    m_id = re.search(r"/(?:id|story/_/id)/(\d+)", url)
    if not m_id:
        return None
    story_id = m_id.group(1)
    api_url = f"https://now.core.api.espn.com/v1/sports/news/{story_id}"
    try:
        req = urllib.request.Request(api_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="ignore"))
        headlines = data.get("headlines") or []
        if not headlines:
            return None
        h0 = headlines[0]
        title = html_lib.unescape((h0.get("headline") or h0.get("title") or "").strip())
        raw_story_html = h0.get("story") or h0.get("description") or ""
        story_clean = html_lib.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", raw_story_html)).strip())
        cands: List[str] = []
        # Prefer genuine editorial photography (a.espncdn.com/photo/...) over sidebar video stills (dm_*)
        imgs = sorted(
            h0.get("images") or [],
            key=lambda im: (0 if "a.espncdn.com/photo/" in (im.get("url") or "") else 1, -int(im.get("width") or 0)),
        )
        for im in imgs:
            iu = _clean_editorial_image_url(im.get("url") or "")
            if _is_valid_article_image(iu) and "dm_" not in iu.lower() and iu not in cands:
                cands.append(iu)
        return {
            "title": title,
            "source": "ESPN FC",
            "url": url,
            "raw_text": story_clean or title,
            "image_url": cands[0] if cands else None,
            "candidate_images": cands[:6],
            "reliability_tier": "confirmed",
        }
    except Exception:
        return None


def scrape_article_from_url(url: str, timeout: int = 12) -> Dict[str, Any]:
    """Scrapes headline, clean full article body, primary image_url, and candidate_images from any news URL."""
    print(f"[UrlScraper] Scraping: {url}")
    espn_fast = _try_espn_core_api(url, timeout=min(timeout, 8))
    if espn_fast and len(espn_fast.get("raw_text", "")) > 120:
        return espn_fast

    parsed = urllib.parse.urlparse(url)
    domain = parsed.netloc.replace("www.", "").split(".")[0].capitalize()

    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        final_url = resp.geturl() or url
        page_html = resp.read().decode("utf-8", errors="ignore")

    meta = _extract_meta_map(page_html)
    jsonld = _extract_json_ld_details(page_html)

    # 1. Title extraction
    title = meta.get("og:title") or jsonld.get("headline") or ""
    if not title:
        h1 = re.search(r"<h1[^>]*>(.*?)</h1>", page_html, re.DOTALL | re.I)
        if h1:
            title = html_lib.unescape(re.sub(r"<[^>]+>", "", h1.group(1)).strip())
        else:
            t_tag = re.search(r"<title>(.*?)</title>", page_html, re.I | re.DOTALL)
            if t_tag:
                title = html_lib.unescape(t_tag.group(1).split(" - ")[0].split(" | ")[0].strip())

    # 2. Source name extraction
    source_name = meta.get("og:site_name") or domain

    # 3. Candidate Images Collection (JSON-LD -> og:image -> twitter:image -> <figure>/<img> hero tags)
    candidate_images: List[str] = []
    for raw_img in (
        list(jsonld.get("images", []))
        + [meta.get("og:image", ""), meta.get("og:image:secure_url", ""), meta.get("twitter:image", ""), meta.get("twitter:image:src", "")]
    ):
        cleaned = _clean_editorial_image_url(raw_img)
        if _is_valid_article_image(cleaned) and cleaned not in candidate_images:
            candidate_images.append(cleaned)

    # Also harvest <figure>/<article> high-res <img> tags (helps BBC Sport articles where og:image differs or is absent)
    for img_m in re.finditer(r'<img\b([^>]+)>', page_html, re.IGNORECASE):
        attrs = img_m.group(1)
        srcset_m = re.search(r'srcset\s*=\s*["\']([^"\']+)["\']', attrs, re.IGNORECASE)
        src_m = re.search(r'\bsrc\s*=\s*["\']([^"\']+)["\']', attrs, re.IGNORECASE)
        chosen = ""
        if srcset_m:
            entries = [e.strip().split()[0] for e in srcset_m.group(1).split(",") if e.strip()]
            if entries:
                chosen = entries[-1]
        elif src_m:
            chosen = src_m.group(1)
        if chosen:
            cleaned = _clean_editorial_image_url(chosen)
            # Filter editorial sports CDNs or jpg/jpeg/webp photos
            if _is_valid_article_image(cleaned) and (
                any(cdn in cleaned.lower() for cdn in ("ichef.bbci.co.uk", "365dm.com", "espncdn.com", "guim.co.uk", "pulselive.com", "akamaized.net"))
                or any(ext in cleaned.lower() for ext in (".jpg", ".jpeg", ".webp"))
            ):
                # Upgrade BBC small thumbnail width to high-res /1024/
                if "ichef.bbci.co.uk" in cleaned:
                    cleaned = re.sub(r'/standard/\d+/', '/standard/1024/', cleaned)
                if cleaned not in candidate_images:
                    candidate_images.append(cleaned)
                    if len(candidate_images) >= 8:
                        break

    image_url = candidate_images[0] if candidate_images else None

    # 4. Full Body Extraction (HTML paragraphs -> JSON-LD articleBody -> meta description)
    clean_paragraphs = []
    for p_match in re.finditer(r"<p[^>]*>(.*?)</p>", page_html, re.DOTALL):
        p_raw = re.sub(r"<[^>]+>", " ", p_match.group(1)).strip()
        p_norm = re.sub(r"\s+", " ", p_raw).strip()
        words = [w for w in p_norm.split() if len(w) > 1]
        low = p_norm.lower()
        if (
            len(words) >= 7
            and "{" not in p_norm
            and "}" not in p_norm
            and "var " not in low
            and "document." not in low
            and "function(" not in low
            and "cookie" not in low
            and "loadscript" not in low
            and "confirm if you are" not in low
            and "watch an ad" not in low
            and "all rights reserved" not in low
            and "sign up to our newsletter" not in low
        ):
            clean_paragraphs.append(html_lib.unescape(p_norm))

    body_text = " ".join(clean_paragraphs)
    if len(jsonld.get("body", "")) > len(body_text):
        body_text = jsonld["body"]
    if not body_text or len(body_text) < 80:
        body_text = meta.get("description") or meta.get("og:description") or title

    return {
        "title": title,
        "source": source_name,
        "url": final_url,
        "raw_text": body_text,
        "image_url": image_url,
        "candidate_images": candidate_images,
        "reliability_tier": "rumour",
    }


if __name__ == "__main__":
    test_urls = [
        "https://www.skysports.com/football/news/11095/13616234/arsenal-and-manchester-citys-problems-analysed-as-both-set-to-meet-in-bumper-premier-league-clash-this-weekend",
    ]
    for u in test_urls:
        try:
            res = scrape_article_from_url(u)
            print("TITLE:", res["title"], "| IMG:", res["image_url"], "| CANDIDATES:", len(res["candidate_images"]), "| LEN:", len(res["raw_text"]))
        except Exception as e:
            print("ERR:", e)
