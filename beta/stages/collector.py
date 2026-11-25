"""
# PROVENANCE: Copied from stages/collector.py for the isolated beta pipeline.
# Runtime Sandbox: beta/ | Safe experimental development environment.
"""

"""
Stage 1: News Collector.
Polls RSS feeds from sports outlets (Sky Sports, BBC Sport, Guardian, ESPN, etc.)
Extracts title, source, URL, publish date, and story text into SQLite (data/news.db).
Respects robots.txt on fallback HTML scraping.
"""

import sys
import os
import re
import json
import html
import yaml
import hashlib
import sqlite3
import urllib.request
import urllib.parse
import urllib.robotparser
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from pipeline.state_manager import init_database, get_db_connection
from pipeline.resource_monitor import ResourceTracker

CONFIG_PATH = PROJECT_ROOT / "config" / "config.yaml"

def clean_html(raw_html: str) -> str:
    """Strip HTML tags and convert entities."""
    if not raw_html:
        return ""
    # Remove script and style tags
    clean = re.sub(r'<script.*?</script>', '', raw_html, flags=re.DOTALL | re.IGNORECASE)
    clean = re.sub(r'<style.*?</style>', '', clean, flags=re.DOTALL | re.IGNORECASE)
    # Remove HTML tags
    clean = re.sub(r'<[^<]+?>', ' ', clean)
    # Replace whitespace sequences
    clean = re.sub(r'\s+', ' ', clean).strip()
    return html.unescape(clean)

def can_fetch_url(url: str, user_agent: str = "FootballVideoBot/1.0") -> bool:
    """Verify robots.txt permissions before attempting HTML scrape."""
    try:
        parsed = urllib.parse.urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        rp = urllib.robotparser.RobotFileParser()
        rp.set_url(robots_url)
        rp.read()
        return rp.can_fetch(user_agent, url)
    except Exception as e:
        print(f"[robots.txt] Warning checking {url}: {e}. Proceeding cautiously.")
        return True

def fetch_feed_items(feed_conf: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Fetch and parse an RSS or Atom feed with robust source and text extraction."""
    url = feed_conf["url"]
    feed_name = feed_conf["name"]
    items = []
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            content = resp.read()
            root = ET.fromstring(content)

        # Handle standard RSS 2.0 items
        for item in root.findall(".//item"):
            title = item.findtext("title", "").strip()
            link = item.findtext("link", "").strip()
            pub_date = item.findtext("pubDate", "").strip()
            description = item.findtext("description", "").strip()
            content_encoded = ""
            for elem in item:
                if elem.tag.endswith("encoded") and elem.text:
                    content_encoded = elem.text.strip()
                    break

            if not title or not link:
                continue

            # Extract specific publisher source if provided (e.g. Google News <source>)
            source_name = feed_name
            source_elem = item.find("source")
            if source_elem is not None and source_elem.text:
                source_name = source_elem.text.strip()
                # Clean redundant "- Publisher" suffix from title
                title = re.sub(r'\s+-\s+[A-Za-z0-9\s\.\']+$', '', title).strip()

            best_text = content_encoded if len(content_encoded) > len(description) else description
            cleaned_desc = clean_html(best_text)
            item_hash = hashlib.sha256(f"{source_name}:{title}:{link}".encode("utf-8")).hexdigest()

            items.append({
                "hash": item_hash,
                "title": title,
                "source": source_name,
                "url": link,
                "published_at": pub_date,
                "raw_text": cleaned_desc
            })

        # Handle Atom feed entries
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        for entry in root.findall(".//atom:entry", ns) or root.findall(".//entry"):
            title = entry.findtext("atom:title", namespaces=ns) or entry.findtext("title", "") or ""
            title = title.strip()
            link_elem = entry.find("atom:link", namespaces=ns) or entry.find("link")
            link = link_elem.get("href", "").strip() if link_elem is not None else ""
            pub_date = entry.findtext("atom:published", namespaces=ns) or entry.findtext("atom:updated", namespaces=ns) or entry.findtext("published", "") or ""
            summary = entry.findtext("atom:summary", namespaces=ns) or entry.findtext("atom:content", namespaces=ns) or entry.findtext("summary", "") or ""
            
            if not title or not link:
                continue

            cleaned_desc = clean_html(summary)
            item_hash = hashlib.sha256(f"{feed_name}:{title}:{link}".encode("utf-8")).hexdigest()

            items.append({
                "hash": item_hash,
                "title": title,
                "source": feed_name,
                "url": link,
                "published_at": pub_date,
                "raw_text": cleaned_desc
            })

    except Exception as e:
        print(f"[Collector] Error fetching feed '{feed_name}' ({url}): {e}")

    return items

def scrape_besoccer(limit: int = 15) -> List[Dict[str, Any]]:
    """Scrape latest football news from BeSoccer HTML with full article body extraction."""
    import html as html_lib
    url = "https://www.besoccer.com/news"
    print(f"[Collector] Scraping HTML news from BeSoccer ({url})...")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9"
    }

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=12) as resp:
            page_html = resp.read().decode("utf-8", errors="ignore")
    except Exception as e:
        print(f"[Collector] Error fetching BeSoccer index: {e}")
        return []

    matches = re.findall(r'href=["\'](?:https://www\.besoccer\.com)?(/new/[a-zA-Z0-9_\-]+-\d+)["\']', page_html)
    unique_urls = [u for u in dict.fromkeys(matches) if "latest-news-transfers-rumours-and-updates" not in u.lower()]
    print(f"[Collector] Found {len(unique_urls)} BeSoccer articles.")

    items = []
    for rel_url in unique_urls[:limit]:
        full_url = f"https://www.besoccer.com{rel_url}"
        try:
            art_req = urllib.request.Request(full_url, headers=headers)
            with urllib.request.urlopen(art_req, timeout=10) as aresp:
                a_html = aresp.read().decode("utf-8", errors="ignore")

            title_m = re.search(r'<meta\s+property=["\']og:title["\']\s+content=["\']([^"\']+)["\']', a_html)
            title = title_m.group(1).strip() if title_m else ""
            if not title:
                h1_m = re.search(r'<h1[^>]*>(.*?)</h1>', a_html, re.DOTALL)
                title = re.sub(r'<[^>]+>', '', h1_m.group(1)).strip() if h1_m else ""
            title = html_lib.unescape(title)

            # Skip generic hub titles
            if any(k in title.lower() for k in ["latest news, transfers, rumours", "latest transfers, rumours", "premier league 2026/27: latest"]):
                continue

            body_paragraphs = []
            for p_match in re.finditer(r'<p[^>]*>(.*?)</p>', a_html, re.DOTALL):
                p_raw = re.sub(r'<[^>]+>', ' ', p_match.group(1)).strip()
                p_norm = re.sub(r'\s+', ' ', p_raw).strip()
                words = [w for w in p_norm.split() if len(w) > 1]
                low = p_norm.lower()

                # Filter out scripts, ads, cookies, and boilerplate
                if not (len(words) >= 6 and "{" not in p_norm and "}" not in p_norm and
                        "var " not in low and "document." not in low and "function(" not in low and
                        "cookie" not in low and "loadscript" not in low and "dugout" not in low and
                        "confirm if you are" not in low and "watch an ad" not in low):
                    continue

                # Filter out tactical position strings like "F ST RW GK LB" or "4-3-3"
                if re.search(r'\b(F|ST|RW|LW|CF|CAM|CM|CDM|LB|CB|RB|GK)\s+(F|ST|RW|LW|CF|CAM|CM|CDM|LB|CB|RB|GK)\b', p_norm):
                    continue
                if re.match(r'^[A-Z]{1,3}(\s+[A-Z]{1,3}){1,}$', p_norm):
                    continue
                alpha_words = [w for w in words if w.isalpha()]
                if not alpha_words or (sum(len(w) for w in alpha_words) / len(alpha_words) < 3.0):
                    continue

                body_paragraphs.append(html.unescape(p_norm))

            body_text = " ".join(body_paragraphs)
            if not body_text:
                desc_m = re.search(r'<meta\s+name=["\']description["\']\s+content=["\']([^"\']+)["\']', a_html)
                body_text = html.unescape(desc_m.group(1).strip()) if desc_m else title

            art_hash = hashlib.sha256(f"BeSoccer:{title}:{full_url}".encode("utf-8")).hexdigest()
            items.append({
                "hash": art_hash,
                "title": title,
                "source": "BeSoccer",
                "url": full_url,
                "published_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                "raw_text": body_text
            })
        except Exception as e:
            print(f"[Collector] Error fetching BeSoccer article '{full_url}': {e}")

    return items

def scrape_reddit_soccer(url: str = "https://www.reddit.com/r/soccer/hot.json?limit=25", limit: int = 20) -> List[Dict[str, Any]]:
    """Fetch breaking football posts from Reddit r/soccer (direct JSON with Google News site:reddit RSS fallback)."""
    items: List[Dict[str, Any]] = []
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            payload = json.loads(resp.read().decode("utf-8", errors="ignore"))
        children = payload.get("data", {}).get("children", [])
        for child in children:
            if len(items) >= limit:
                break
            post = child.get("data", {})
            if not post or post.get("stickied"):
                continue
            title = html.unescape((post.get("title") or "").strip())
            if len(title) < 18:
                continue
            score = int(post.get("score") or 0)
            num_comments = int(post.get("num_comments") or 0)
            if score < 30 and not any(k in title.lower() for k in ("romano", "ornstein", "official", "breaking", "sacked", "agreed", "signing", "transfer")):
                continue
            permalink = post.get("permalink") or ""
            post_url = post.get("url") or f"https://www.reddit.com{permalink}"
            created_utc = float(post.get("created_utc") or datetime.now(timezone.utc).timestamp())
            pub_str = datetime.fromtimestamp(created_utc, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            selftext = clean_html(post.get("selftext") or "")
            body = f"Reddit engagement: {score} upvotes, {num_comments} comments. {selftext[:500]}".strip()
            art_hash = hashlib.sha256(f"Reddit:{title}:{permalink}".encode("utf-8")).hexdigest()
            items.append({
                "hash": art_hash,
                "title": title,
                "source": "Reddit r/soccer",
                "url": post_url,
                "published_at": pub_str,
                "raw_text": body or title,
            })
        if items:
            return items
    except Exception as e:
        print(f"[Collector] Direct Reddit JSON note ({e}); using Google News r/soccer RSS fallback...")

    fallback_rss = {
        "name": "Reddit r/soccer",
        "url": "https://news.google.com/rss/search?q=reddit+r%2Fsoccer+football&hl=en-GB&gl=GB&ceid=GB:en",
    }
    for it in fetch_feed_items(fallback_rss)[:limit]:
        it["source"] = "Reddit r/soccer"
        it["title"] = re.sub(r'\s*[:\-]\s*r/soccer\s*$', '', it["title"], flags=re.IGNORECASE).strip()
        items.append(it)
    return items


def scrape_espn_json(url: str = "https://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/news", limit: int = 20) -> List[Dict[str, Any]]:
    """Fetch structured breaking football articles from ESPN public news JSON API."""
    items: List[Dict[str, Any]] = []
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            payload = json.loads(resp.read().decode("utf-8", errors="ignore"))
        for art in payload.get("articles", [])[:limit]:
            title = html.unescape((art.get("headline") or "").strip())
            desc = clean_html(art.get("description") or "")
            link = (art.get("links", {}).get("web", {}).get("href") or "").strip()
            pub_str = (art.get("published") or datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")).strip()
            if not title or not link:
                continue
            art_hash = hashlib.sha256(f"ESPN FC:{title}:{link}".encode("utf-8")).hexdigest()
            items.append({
                "hash": art_hash,
                "title": title,
                "source": "ESPN FC",
                "url": link,
                "published_at": pub_str,
                "raw_text": desc or title,
            })
    except Exception as e:
        print(f"[Collector] Error polling ESPN JSON API: {e}")
    return items


def store_articles(articles: List[Dict[str, Any]]) -> int:
    """Store articles into SQLite, skipping duplicates."""
    init_database()
    inserted_count = 0
    now = datetime.now(timezone.utc).isoformat()

    with get_db_connection() as conn:
        for art in articles:
            try:
                conn.execute("""
                    INSERT INTO articles (hash, title, source, url, published_at, raw_text, scraped_at, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 'NEW')
                """, (art["hash"], art["title"], art["source"], art["url"], art["published_at"], art["raw_text"], now))
                inserted_count += 1
            except sqlite3.IntegrityError:
                # Article already exists
                pass
        conn.commit()

    return inserted_count

def run_collector() -> int:
    """Main collector entrypoint."""
    with ResourceTracker("Collector"):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        all_items = []
        for feed in config.get("feeds", []):
            ftype = feed.get("type")
            if ftype == "html" or feed.get("name") == "BeSoccer":
                items = scrape_besoccer(limit=15)
            elif ftype == "reddit":
                print(f"[Collector] Polling Reddit feed: {feed['name']}...")
                items = scrape_reddit_soccer(url=feed.get("url", "https://www.reddit.com/r/soccer/hot.json?limit=25"), limit=20)
            elif ftype == "espn_json":
                print(f"[Collector] Polling ESPN API: {feed['name']}...")
                items = scrape_espn_json(url=feed.get("url", "https://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/news"), limit=20)
            else:
                print(f"[Collector] Polling feed: {feed['name']}...")
                items = fetch_feed_items(feed)
            print(f"[Collector] Found {len(items)} items from {feed['name']}.")
            all_items.extend(items)

        new_count = store_articles(all_items)
        print(f"[Collector] Complete. Inserted {new_count} new articles into database.")
        return new_count

if __name__ == "__main__":
    count = run_collector()
    print(f"Collector finished with {count} new stories.")
