"""
Universal Single-URL Article Scraper.
Given any football news article URL from Telegram, extracts:
- Title / Headline
- Source / Domain Name
- Article Body Text
- Image URL (if available via og:image)
"""

import re
import urllib.request
import urllib.parse
import html as html_lib
from typing import Dict, Any, Optional

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9"
}

def scrape_article_from_url(url: str) -> Dict[str, Any]:
    """Scrapes headline and article body from an arbitrary news URL."""
    print(f"[UrlScraper] Scraping: {url}")
    parsed = urllib.parse.urlparse(url)
    domain = parsed.netloc.replace("www.", "").split(".")[0].capitalize()
    
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as resp:
        page_html = resp.read().decode("utf-8", errors="ignore")

    # Title extraction
    title = ""
    og_title = re.search(r'<meta\s+property=["\']og:title["\']\s+content=["\']([^"\']+)["\']', page_html, re.I)
    if og_title:
        title = og_title.group(1).strip()
    else:
        h1 = re.search(r'<h1[^>]*>(.*?)</h1>', page_html, re.DOTALL | re.I)
        if h1:
            title = re.sub(r'<[^>]+>', '', h1.group(1)).strip()
        else:
            t_tag = re.search(r'<title>(.*?)</title>', page_html, re.I)
            if t_tag:
                title = t_tag.group(1).split(" - ")[0].split(" | ")[0].strip()

    title = html_lib.unescape(title)

    # Source name extraction
    source_name = domain
    og_site = re.search(r'<meta\s+property=["\']og:site_name["\']\s+content=["\']([^"\']+)["\']', page_html, re.I)
    if og_site:
        source_name = html_lib.unescape(og_site.group(1).strip())

    # Image extraction
    image_url = None
    og_img = re.search(r'<meta\s+property=["\']og:image["\']\s+content=["\']([^"\']+)["\']', page_html, re.I)
    if og_img:
        image_url = og_img.group(1).strip()

    # Body extraction
    clean_paragraphs = []
    for p_match in re.finditer(r'<p[^>]*>(.*?)</p>', page_html, re.DOTALL):
        p_raw = re.sub(r'<[^>]+>', ' ', p_match.group(1)).strip()
        p_norm = re.sub(r'\s+', ' ', p_raw).strip()
        words = [w for w in p_norm.split() if len(w) > 1]
        
        # Filter junk/scripts/cookies/ads/scripts
        low = p_norm.lower()
        if (len(words) >= 7 and
            "{" not in p_norm and "}" not in p_norm and
            "var " not in low and "document." not in low and "function(" not in low and
            "cookie" not in low and "loadscript" not in low and "dugout" not in low and
            "confirm if you are" not in low and "watch an ad" not in low and "broadcast" not in low):
            clean_paragraphs.append(html_lib.unescape(p_norm))

    body_text = " ".join(clean_paragraphs)
    if not body_text or len(body_text) < 80:
        meta_desc = re.search(r'<meta\s+name=["\']description["\']\s+content=["\']([^"\']+)["\']', page_html, re.I)
        if meta_desc:
            body_text = html_lib.unescape(meta_desc.group(1).strip())
        else:
            body_text = title

    return {
        "title": title,
        "source": source_name,
        "url": url,
        "raw_text": body_text,
        "image_url": image_url,
        "reliability_tier": "rumour"  # single external link defaults to rumour unless official
    }

if __name__ == "__main__":
    test_urls = [
        "https://www.transfermarketweb.com/transfers/bayern-munich-attention-olise-contract-kane-renewal-ceo-dreesen-confirms-talks-planned-228562",
        "https://www.besoccer.com/new/real-madrid-and-barcelona-join-race-for-jj-gabriel-1438873"
    ]
    for u in test_urls:
        res = scrape_article_from_url(u)
        print("Scraped:", res["title"])
        print("Source:", res["source"])
        print("Body preview:", res["raw_text"][:150], "...\n")
