"""
Stage Component: Professional-Grade High-Resolution Image Scrapers.
Part of the @Footballin30sec automated production pipeline.

Provides high-resolution, watermark-free image scrapers:
1. BingImageScraper:
   - Specific filter flags:
     * &qft=+filterui:imagesize-large+filterui:photo-photo
     * &qft=+filterui:imagesize-large+filterui:aspect-tall (for vertical 9:16 portrait photos)
   - Direct high-resolution murl extraction
2. DuckDuckGoImageScraper:
   - DuckDuckGo API (token generation + direct image JSON at i.js) for uncompressed original image URLs
3. WikimediaCommonsScraper:
   - Original full-resolution media URLs (1080p to 4K) via action=query&prop=imageinfo&iiprop=url|size
4. RedditSportsScraper:
   - Direct high-res image extraction from r/soccer and sports photography post media metadata
5. Watermark Blacklist:
   - Complete exclusion of stock preview watermark domains (alamy, gettyimages, shutterstock, istockphoto, dreamstime, 123rf, vecteezy, stockphoto, etc.)
6. Verification:
   - Ultra-fast streaming header/chunk parser confirms width >= 1080 or height >= 1080 with exact resolution and file size metadata.
"""

import sys
import os
import re
import io
import json
import html
import socket
import urllib.request
import urllib.parse
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional, Tuple, Set
from PIL import Image, ImageFile

# Global socket timeout to avoid hanging sockets
socket.setdefaulttimeout(8)

# Blacklisted stock preview watermark domains
WATERMARK_BLACKLIST_DOMAINS: Set[str] = {
    "alamy.com",
    "gettyimages.com",
    "shutterstock.com",
    "istockphoto.com",
    "dreamstime.com",
    "123rf.com",
    "vecteezy.com",
    "stockphoto.com",
    "stock.adobe.com",
    "depositphotos.com",
    "bigstockphoto.com",
    "canstockphoto.com",
    "freepik.com",
}

# Standard browser headers
BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# Wikimedia compliant bot headers (required by Wikimedia SRE to prevent 429 blocks)
WIKIMEDIA_HEADERS = {
    "User-Agent": "FootballStudioBot/2.0 (https://footballin30sec.com; editorial@footballin30sec.com) Python/3.11"
}

# Reddit compliant user agent
REDDIT_HEADERS = {
    "User-Agent": "script:footballin30sec.scraper:v2.0 (by /u/footballin30sec)"
}


@dataclass
class ScrapedImage:
    url: str
    title: str = ""
    source: str = ""
    width: Optional[int] = None
    height: Optional[int] = None
    aspect: str = "any"  # "standard", "tall", or "any"
    file_size_bytes: Optional[int] = None
    format: Optional[str] = None
    page_url: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def is_stock_watermark_url(url: str) -> bool:
    """
    Check if a URL belongs to a known stock preview watermark domain or contains watermark keywords.
    """
    if not url:
        return True
    try:
        parsed = urllib.parse.urlparse(url)
        netloc = parsed.netloc.lower()
        if ":" in netloc:
            netloc = netloc.split(":")[0]

        for domain in WATERMARK_BLACKLIST_DOMAINS:
            if netloc == domain or netloc.endswith("." + domain):
                return True

        full_lower = url.lower()
        if any(marker in full_lower for marker in [
            "alamy.com", "gettyimages", "shutterstock", "istockphoto",
            "dreamstime", "123rf.com", "vecteezy", "stockphoto",
            "watermark", "preview_wm", "comp/2", "comp/3", "comp/g"
        ]):
            return True

        return False
    except Exception:
        return True


def get_request_headers(url: str) -> Dict[str, str]:
    """Return appropriate HTTP headers depending on the host."""
    u_lower = url.lower()
    if "wikimedia.org" in u_lower or "wikipedia.org" in u_lower:
        return WIKIMEDIA_HEADERS
    elif "reddit.com" in u_lower or "redd.it" in u_lower:
        return REDDIT_HEADERS
    else:
        return BROWSER_HEADERS


def inspect_image_resolution(url: str, timeout: int = 6) -> Tuple[bool, int, int, int, str]:
    """
    High-speed streaming inspection of image resolution, file size, and format.
    Uses ImageFile.Parser() to decode dimensions from initial bytes in milliseconds,
    avoiding downloading huge multi-megabyte payloads when not needed.

    Returns:
        (is_highres, width, height, size_bytes, format)
        where is_highres is True if width >= 1080 or height >= 1080.
    """
    if not url or is_stock_watermark_url(url):
        return (False, 0, 0, 0, "")

    headers = get_request_headers(url)
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            content_length = resp.headers.get("Content-Length")
            file_size = int(content_length) if content_length and content_length.isdigit() else 0

            parser = ImageFile.Parser()
            total_read = 0
            chunks = []

            # Read first chunk (64KB is enough for 99% of image headers)
            chunk = resp.read(65536)
            total_read += len(chunk)
            chunks.append(chunk)
            parser.feed(chunk)

            # If not yet resolved, read up to 512KB
            while not parser.image and total_read < 524288:
                next_chunk = resp.read(65536)
                if not next_chunk:
                    break
                total_read += len(next_chunk)
                chunks.append(next_chunk)
                parser.feed(next_chunk)

            img = parser.image
            w, h, img_format = 0, 0, ""

            if img:
                w, h = img.size
                img_format = img.format or ""
            else:
                raw_bytes = b"".join(chunks)
                with Image.open(io.BytesIO(raw_bytes)) as fallback_img:
                    w, h = fallback_img.size
                    img_format = fallback_img.format or ""

            if file_size == 0:
                file_size = total_read

            is_highres = (w >= 1080 or h >= 1080)
            return (is_highres, w, h, file_size, img_format)

    except Exception:
        return (False, 0, 0, 0, "")


# ============================================================================
# 1. Bing High-Res Scraper
# ============================================================================

class BingImageScraper:
    """
    High-resolution Bing image scraper utilizing specific filter flags:
    - &qft=+filterui:imagesize-large+filterui:photo-photo
    - &qft=+filterui:imagesize-large+filterui:aspect-tall (for vertical 9:16 portrait photos)
    Directly extracts high-resolution original media URLs (murl) from iusc data attributes.
    """

    def __init__(self):
        self.headers = BROWSER_HEADERS.copy()
        self.headers["Referer"] = "https://www.bing.com/"

    def scrape(
        self,
        query: str,
        aspect: str = "any",
        max_results: int = 15
    ) -> List[ScrapedImage]:
        """
        Scrape Bing for high-res images.
        aspect: 'any', 'tall', or 'photo' (standard)
        """
        results: List[ScrapedImage] = []
        seen_urls: Set[str] = set()

        aspects_to_run = []
        if aspect == "tall":
            aspects_to_run = ["tall"]
        elif aspect == "photo" or aspect == "standard":
            aspects_to_run = ["photo"]
        else:
            aspects_to_run = ["photo", "tall"]

        for asp in aspects_to_run:
            if asp == "tall":
                qft = "+filterui:imagesize-large+filterui:aspect-tall"
                source_label = "Bing (large tall/portrait)"
            else:
                qft = "+filterui:imagesize-large+filterui:photo-photo"
                source_label = "Bing (large photo)"

            url = (
                f"https://www.bing.com/images/async?q={urllib.parse.quote(query)}"
                f"&qft={urllib.parse.quote(qft)}&first=1&count=40&relp=40"
                f"&scenario=ImageBasicHover&datsrc=N_I&layout=RowBased&mmasync=1"
            )

            try:
                req = urllib.request.Request(url, headers=self.headers)
                with urllib.request.urlopen(req, timeout=8) as resp:
                    raw_html = resp.read().decode("utf-8", errors="ignore")

                matches = re.findall(r'class=["\']iusc["\'][^>]*m=["\'](\{.*?\})["\']', raw_html)
                if not matches:
                    matches = re.findall(r'\bm=["\'](\{[^"\']+\})["\']', raw_html)

                for m in matches:
                    try:
                        clean_m = html.unescape(m).replace("&quot;", '"')
                        data = json.loads(clean_m)
                        murl = data.get("murl")
                        turl = data.get("turl")
                        title = data.get("t", "")
                        purl = data.get("purl", "")

                        if not murl or murl in seen_urls:
                            continue

                        if is_stock_watermark_url(murl) or is_stock_watermark_url(purl):
                            continue

                        seen_urls.add(murl)
                        results.append(ScrapedImage(
                            url=murl,
                            title=title,
                            source=source_label,
                            aspect=asp,
                            page_url=purl,
                            metadata={
                                "thumb_url": turl,
                                "bing_ow": data.get("ow"),
                                "bing_oh": data.get("oh"),
                            }
                        ))

                        if len(results) >= max_results:
                            break
                    except Exception:
                        continue
            except Exception:
                try:
                    fallback_url = (
                        f"https://www.bing.com/images/search?q={urllib.parse.quote(query)}"
                        f"&qft={urllib.parse.quote(qft)}&first=1"
                    )
                    req_fb = urllib.request.Request(fallback_url, headers=self.headers)
                    with urllib.request.urlopen(req_fb, timeout=8) as resp_fb:
                        raw_fb = resp_fb.read().decode("utf-8", errors="ignore")

                    matches_fb = re.findall(r'class=["\']iusc["\'][^>]*m=["\'](\{.*?\})["\']', raw_fb)
                    for m in matches_fb:
                        clean_m = html.unescape(m).replace("&quot;", '"')
                        data = json.loads(clean_m)
                        murl = data.get("murl")
                        if murl and murl not in seen_urls and not is_stock_watermark_url(murl):
                            seen_urls.add(murl)
                            results.append(ScrapedImage(
                                url=murl,
                                title=data.get("t", ""),
                                source=source_label,
                                aspect=asp,
                                page_url=data.get("purl", ""),
                            ))
                            if len(results) >= max_results:
                                break
                except Exception:
                    pass

            if len(results) >= max_results:
                break

        return results


# ============================================================================
# 2. DuckDuckGo Images Scraper
# ============================================================================

class DuckDuckGoImageScraper:
    """
    DuckDuckGo Images Scraper:
    - Hits DuckDuckGo API (token generation + direct image JSON at i.js) to get uncompressed original image URLs.
    - Extracts resolution (width/height), direct source image URL, and title metadata.
    """

    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Referer": "https://duckduckgo.com/",
            "Accept-Language": "en-US,en;q=0.9",
        }

    def _get_vqd_token(self, query: str) -> Optional[str]:
        """Fetch vqd token from DuckDuckGo."""
        try:
            init_url = f"https://duckduckgo.com/?q={urllib.parse.quote(query)}"
            init_headers = BROWSER_HEADERS.copy()
            req = urllib.request.Request(init_url, headers=init_headers)
            with urllib.request.urlopen(req, timeout=6) as resp:
                content = resp.read().decode("utf-8", errors="ignore")

            m = re.search(r'vqd=([0-9\-]+)', content) or re.search(r'vqd=[\'"]([0-9\-]+)[\'"]', content)
            if m:
                return m.group(1)
        except Exception:
            pass
        return None

    def scrape(self, query: str, max_results: int = 15) -> List[ScrapedImage]:
        """
        Hit DuckDuckGo token generation + i.js image API.
        """
        results: List[ScrapedImage] = []
        vqd = self._get_vqd_token(query)
        if not vqd:
            return results

        api_url = (
            f"https://duckduckgo.com/i.js?l=us-en&o=json&q={urllib.parse.quote(query)}"
            f"&vqd={vqd}&f=,,,&p=1"
        )
        try:
            req = urllib.request.Request(api_url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=6) as resp:
                data = json.loads(resp.read().decode("utf-8", errors="ignore"))

            raw_results = data.get("results", [])
            for it in raw_results:
                img_url = it.get("image")
                if not img_url or is_stock_watermark_url(img_url):
                    continue

                w = it.get("width")
                h = it.get("height")
                title = it.get("title", "")
                source_domain = it.get("source", "")
                purl = it.get("url", "")

                results.append(ScrapedImage(
                    url=img_url,
                    title=title,
                    source=f"DuckDuckGo ({source_domain})" if source_domain else "DuckDuckGo",
                    width=int(w) if w else None,
                    height=int(h) if h else None,
                    page_url=purl,
                    metadata={"thumbnail": it.get("thumbnail")}
                ))

                if len(results) >= max_results:
                    break
        except Exception:
            pass

        return results


# ============================================================================
# 3. Wikimedia Commons High-Res API
# ============================================================================

class WikimediaCommonsScraper:
    """
    Wikimedia Commons High-Res API:
    - Extracts original full-resolution media URLs (1080p to 4K) using:
      action=query&generator=search&gsrsearch=...&prop=imageinfo&iiprop=url|size
    - Filters out non-image files (.svg, .ogg, .ogv, .webm, .pdf).
    - Uses compliant Wikimedia headers to prevent rate limits.
    - Employs smart entity / sub-query fallback expansion when long compound phrases yield 0 hits.
    """

    def __init__(self):
        self.headers = WIKIMEDIA_HEADERS.copy()

    def scrape(
        self,
        query: str,
        max_results: int = 15,
        min_dimension: int = 1080
    ) -> List[ScrapedImage]:
        """
        Query Wikimedia Commons API for original full-resolution media files.
        """
        results: List[ScrapedImage] = []
        seen_urls: Set[str] = set()

        search_queries = [query]
        words = [w for w in query.split() if w.lower() not in ("playing", "press", "conference", "signing", "celebration", "vs", "the", "and")]
        if len(words) >= 2 and " ".join(words) != query:
            search_queries.append(" ".join(words))
        if len(words) >= 3:
            search_queries.append(" ".join(words[:2]))

        for sq in search_queries:
            url = (
                f"https://commons.wikimedia.org/w/api.php?action=query&generator=search"
                f"&gsrsearch={urllib.parse.quote(sq)}&gsrnamespace=6&format=json"
                f"&prop=imageinfo&iiprop=url|size&gsrlimit={max_results * 2}"
            )
            try:
                req = urllib.request.Request(url, headers=self.headers)
                with urllib.request.urlopen(req, timeout=6) as resp:
                    data = json.loads(resp.read().decode("utf-8", errors="ignore"))

                pages = data.get("query", {}).get("pages", {})
                for pid, pdata in pages.items():
                    info_list = pdata.get("imageinfo", [])
                    if not info_list:
                        continue
                    info = info_list[0]
                    img_url = info.get("url", "")
                    w = info.get("width", 0)
                    h = info.get("height", 0)
                    title = pdata.get("title", "")

                    if not img_url or img_url in seen_urls:
                        continue

                    lower_url = img_url.lower()
                    if any(lower_url.endswith(ext) for ext in [".svg", ".ogg", ".ogv", ".webm", ".pdf", ".mp4", ".tiff"]):
                        continue

                    # Filter out images smaller than 1080 if dimensions are reported in API response
                    if w and h and (w < min_dimension and h < min_dimension):
                        continue

                    seen_urls.add(img_url)
                    results.append(ScrapedImage(
                        url=img_url,
                        title=title.replace("File:", "").replace(".jpg", "").replace(".png", ""),
                        source="Wikimedia Commons",
                        width=w,
                        height=h,
                        metadata={
                            "pageid": pid,
                            "descriptionshorturl": info.get("descriptionshorturl")
                        }
                    ))

                    if len(results) >= max_results:
                        break

            except Exception:
                pass

            if len(results) >= max_results:
                break

        return results


# ============================================================================
# 4. Reddit r/soccer & Sports Photography Scraper
# ============================================================================

class RedditSportsScraper:
    """
    Reddit r/soccer & sports photography high-res direct image links scraper:
    - Extracts direct full-resolution image URLs by searching post media metadata:
      * post["preview"]["images"][0]["source"]["url"] (original high-res)
      * post["media_metadata"] (galleries original "s" URLs)
      * direct i.redd.it / i.imgur.com post URLs
    - Queries targeted sports subreddits: r/soccer, r/sportsphotography, r/football.
    - Includes dual discovery: direct Reddit API + Bing Reddit index to guarantee retrieval
      regardless of transient unauthenticated Reddit API rate-limits.
    """

    def __init__(self):
        self.headers = REDDIT_HEADERS.copy()

    def _scrape_reddit_api(self, query: str, subreddit: str = "soccer", max_results: int = 10) -> List[ScrapedImage]:
        """Direct Reddit JSON search."""
        images: List[ScrapedImage] = []
        url = f"https://www.reddit.com/r/{subreddit}/search.json?q={urllib.parse.quote(query)}&restrict_sr=1&sort=relevance&limit={max_results * 2}"
        try:
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=6) as resp:
                data = json.loads(resp.read().decode("utf-8", errors="ignore"))

            posts = data.get("data", {}).get("children", [])
            for p in posts:
                pdata = p.get("data", {})
                title = pdata.get("title", "")
                post_url = pdata.get("url", "")
                permalink = f"https://reddit.com{pdata.get('permalink', '')}"

                # 1. Preview source
                preview_imgs = pdata.get("preview", {}).get("images", [])
                if preview_imgs:
                    source = preview_imgs[0].get("source", {})
                    src_url = source.get("url", "").replace("&amp;", "&")
                    if src_url and not is_stock_watermark_url(src_url):
                        images.append(ScrapedImage(
                            url=src_url,
                            title=title,
                            source=f"Reddit r/{subreddit} (preview source)",
                            width=source.get("width"),
                            height=source.get("height"),
                            page_url=permalink
                        ))
                        continue

                # 2. Media metadata (galleries)
                media_meta = pdata.get("media_metadata", {})
                if media_meta:
                    for item_id, item_val in media_meta.items():
                        s = item_val.get("s", {})
                        gallery_url = s.get("u", "").replace("&amp;", "&")
                        if gallery_url and not is_stock_watermark_url(gallery_url):
                            images.append(ScrapedImage(
                                url=gallery_url,
                                title=title,
                                source=f"Reddit r/{subreddit} (gallery)",
                                width=s.get("x"),
                                height=s.get("y"),
                                page_url=permalink
                            ))

                # 3. Direct image link (i.redd.it or direct image url)
                if post_url and ("i.redd.it" in post_url or post_url.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))):
                    if not is_stock_watermark_url(post_url):
                        images.append(ScrapedImage(
                            url=post_url,
                            title=title,
                            source=f"Reddit r/{subreddit} (direct link)",
                            page_url=permalink
                        ))

                if len(images) >= max_results:
                    break
        except Exception:
            pass

        return images

    def _scrape_reddit_bing_index(self, query: str, max_results: int = 10) -> List[ScrapedImage]:
        """
        Search Reddit sports photography and r/soccer media indexed with high-res filters.
        Provides robust resilience when unauthenticated Reddit API requests are blocked.
        """
        images: List[ScrapedImage] = []
        search_query = f"site:reddit.com/r/soccer {query}"
        qft = "+filterui:imagesize-large+filterui:photo-photo"
        url = (
            f"https://www.bing.com/images/async?q={urllib.parse.quote(search_query)}"
            f"&qft={urllib.parse.quote(qft)}&first=1&count=30&relp=30"
            f"&scenario=ImageBasicHover&datsrc=N_I&layout=RowBased&mmasync=1"
        )
        try:
            req = urllib.request.Request(url, headers=BROWSER_HEADERS)
            with urllib.request.urlopen(req, timeout=6) as resp:
                content = resp.read().decode("utf-8", errors="ignore")

            matches = re.findall(r'class=["\']iusc["\'][^>]*m=["\'](\{.*?\})["\']', content)
            for m in matches:
                clean_m = html.unescape(m).replace("&quot;", '"')
                data = json.loads(clean_m)
                murl = data.get("murl")
                if not murl or is_stock_watermark_url(murl):
                    continue

                images.append(ScrapedImage(
                    url=murl,
                    title=data.get("t", ""),
                    source="Reddit r/soccer (indexed high-res)",
                    page_url=data.get("purl", ""),
                    metadata={"thumb": data.get("turl")}
                ))
                if len(images) >= max_results:
                    break
        except Exception:
            pass

        return images

    def scrape(self, query: str, subreddits: Optional[List[str]] = None, max_results: int = 15) -> List[ScrapedImage]:
        """
        Scrape sports images across Reddit.
        """
        if subreddits is None:
            subreddits = ["soccer", "sportsphotography", "football"]

        all_results: List[ScrapedImage] = []
        seen_urls: Set[str] = set()

        for sub in subreddits:
            api_results = self._scrape_reddit_api(query, subreddit=sub, max_results=max_results)
            for img in api_results:
                if img.url not in seen_urls:
                    seen_urls.add(img.url)
                    all_results.append(img)
            if len(all_results) >= max_results:
                break

        if len(all_results) < max_results:
            indexed = self._scrape_reddit_bing_index(query, max_results=max_results - len(all_results))
            for img in indexed:
                if img.url not in seen_urls:
                    seen_urls.add(img.url)
                    all_results.append(img)

        return all_results


# ============================================================================
# 5. Unified High-Res Image Sourcing Pipeline
# ============================================================================

class HighResImagePipeline:
    """
    Unified high-resolution image sourcing engine:
    Orchestrates Bing, DuckDuckGo, Wikimedia Commons, and Reddit scrapers.
    Guarantees:
    - 0 stock preview watermark domains
    - Confirmed resolution >= 1080 (width or height)
    - Full metadata: width, height, file size, format, source
    """

    def __init__(self):
        self.bing_scraper = BingImageScraper()
        self.ddg_scraper = DuckDuckGoImageScraper()
        self.wiki_scraper = WikimediaCommonsScraper()
        self.reddit_scraper = RedditSportsScraper()

    def scrape_all(
        self,
        query: str,
        aspect: str = "any",
        min_dimension: int = 1080,
        verify_online: bool = True,
        max_verified: int = 6
    ) -> List[ScrapedImage]:
        """
        Query all scrapers, filter watermarks, and optionally verify dimensions online.
        """
        candidates: List[ScrapedImage] = []
        seen_urls: Set[str] = set()

        def add_candidates(items: List[ScrapedImage]):
            for it in items:
                if it.url and it.url not in seen_urls and not is_stock_watermark_url(it.url):
                    seen_urls.add(it.url)
                    candidates.append(it)

        # 1. Bing Scraper (standard large & aspect tall)
        add_candidates(self.bing_scraper.scrape(query, aspect=aspect, max_results=15))

        # 2. Wikimedia Commons Scraper (1080p to 4K original media)
        add_candidates(self.wiki_scraper.scrape(query, max_results=10, min_dimension=min_dimension))

        # 3. Reddit Sports Scraper (r/soccer, sports photography)
        add_candidates(self.reddit_scraper.scrape(query, max_results=10))

        # 4. DuckDuckGo Scraper
        add_candidates(self.ddg_scraper.scrape(query, max_results=10))

        if not verify_online:
            return candidates[:max_verified]

        verified_results: List[ScrapedImage] = []
        for cand in candidates:
            is_highres, w, h, size_bytes, img_format = inspect_image_resolution(cand.url)
            if is_highres:
                cand.width = w
                cand.height = h
                cand.file_size_bytes = size_bytes
                cand.format = img_format
                verified_results.append(cand)
                if len(verified_results) >= max_verified:
                    break

        return verified_results


# Module-level convenience functions
def scrape_bing_images(query: str, aspect: str = "any", max_results: int = 15) -> List[ScrapedImage]:
    return BingImageScraper().scrape(query, aspect=aspect, max_results=max_results)

def scrape_duckduckgo_images(query: str, max_results: int = 15) -> List[ScrapedImage]:
    return DuckDuckGoImageScraper().scrape(query, max_results=max_results)

def scrape_wikimedia_images(query: str, max_results: int = 15, min_dimension: int = 1080) -> List[ScrapedImage]:
    return WikimediaCommonsScraper().scrape(query, max_results=max_results, min_dimension=min_dimension)

def scrape_reddit_images(query: str, subreddits: Optional[List[str]] = None, max_results: int = 15) -> List[ScrapedImage]:
    return RedditSportsScraper().scrape(query, subreddits=subreddits, max_results=max_results)
