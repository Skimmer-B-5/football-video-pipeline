"""
# PROVENANCE: Copied from stages/news_search.py for the isolated beta pipeline.
# Runtime Sandbox: beta/ - Safe experimental development environment.
"""

"""
Live Internet & Feed News Search Engine for Qwen Studio.
Searches live internet sports news (Google News RSS & Bing News RSS) and verified news archives.
Sorts results strictly by query relevance and latest recency, assigns reliability tiers,
and guarantees that /search returns stories matching the searched player/topic without /new pollution.
"""

import re
import html
import sqlite3
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "data" / "news.db"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/rss+xml,application/xml;q=0.9,*/*;q=0.8"
}

def determine_reliability_tier(source: str, url: str) -> str:
    s_low = (source or "").lower()
    u_low = (url or "").lower()
    
    tier_1 = ["bbc", "sky sports", "the athletic", "reuters", "associated press", "guardian", "official"]
    tier_2 = ["espn", "besoccer", "fabrizio", "romano", "marca", "as.com", "telefoot", "rmc", "lequipe", "di marzio", "telegraph", "times", "tnt sports"]
    
    if any(t in s_low or t in u_low for t in tier_1):
        return "confirmed"
    elif any(t in s_low or t in u_low for t in tier_2):
        return "credible"
    return "rumour"

def parse_date_to_timestamp(date_str: str) -> float:
    """Parse various RSS and database date formats to a float timestamp for sorting."""
    if not date_str:
        return 0.0
    try:
        from email.utils import parsedate_to_datetime
        dt = parsedate_to_datetime(date_str)
        return dt.timestamp()
    except Exception:
        pass
    
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(date_str.split(".")[0], fmt)
            return dt.replace(tzinfo=timezone.utc).timestamp()
        except Exception:
            continue
    return 0.0

def clean_text(raw_text: str) -> str:
    clean = re.sub(r'<[^<]+?>', ' ', raw_text or '')
    clean = re.sub(r'\s+', ' ', clean).strip()
    return html.unescape(clean)

def search_google_news(query: str, limit: int = 15) -> List[Dict[str, Any]]:
    """Search Google News RSS for live football coverage."""
    results = []
    try:
        url = f"https://news.google.com/rss/search?q={urllib.parse.quote(query + ' football')}&hl=en-GB&gl=GB&ceid=GB:en"
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=8) as resp:
            content = resp.read()
            root = ET.fromstring(content)
        
        for it in root.findall(".//item")[:limit * 2]:
            raw_title = it.findtext("title", "").strip()
            link = it.findtext("link", "").strip()
            pub_date = it.findtext("pubDate", "").strip()
            source = it.findtext("source", "Sports News").strip()
            desc = it.findtext("description", "").strip()
            
            if not raw_title or not link:
                continue
            
            # Google news title format: "Headline - Source"
            title = raw_title
            if " - " in raw_title:
                parts = raw_title.rsplit(" - ", 1)
                title = parts[0].strip()
                if not source or source == "Sports News":
                    source = parts[1].strip()
            
            results.append({
                "headline": html.unescape(title),
                "source": source,
                "url": link,
                "published_at": pub_date,
                "timestamp": parse_date_to_timestamp(pub_date),
                "reliability_tier": determine_reliability_tier(source, link),
                "article_text": clean_text(desc),
                "search_source": "GOOGLE_NEWS"
            })
    except Exception as e:
        print(f"[NewsSearch] Google News search note: {e}")
    return results

def search_live_internet(query: str, limit: int = 15) -> List[Dict[str, Any]]:
    """Search live web for real-time sports news via Bing News RSS."""
    results = []
    try:
        url = f"https://www.bing.com/news/search?q={urllib.parse.quote(query + ' football')}&format=rss"
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=8) as resp:
            content = resp.read()
            root = ET.fromstring(content)
        
        for it in root.findall(".//item")[:limit * 2]:
            title = it.findtext("title", "").strip()
            raw_link = it.findtext("link", "").strip()
            pub_date = it.findtext("pubDate", "").strip()
            desc = it.findtext("description", "").strip()
            
            if not title or not raw_link:
                continue
            
            # Extract direct URL from Bing apiclick wrapper
            direct_url = raw_link
            try:
                parsed = urllib.parse.urlparse(raw_link)
                qs = urllib.parse.parse_qs(parsed.query)
                if "url" in qs:
                    direct_url = qs["url"][0]
            except Exception:
                pass
            
            # Infer source from domain or title suffix
            source = "Online Media"
            if " - " in title:
                parts = title.rsplit(" - ", 1)
                if len(parts[1]) < 25:
                    source = parts[1].strip()
                    title = parts[0].strip()
            else:
                try:
                    p_url = urllib.parse.urlparse(direct_url)
                    source = p_url.netloc.replace("www.", "").split(".")[0].capitalize()
                except Exception:
                    pass
            
            results.append({
                "headline": html.unescape(title),
                "source": source,
                "url": direct_url,
                "published_at": pub_date,
                "timestamp": parse_date_to_timestamp(pub_date),
                "reliability_tier": determine_reliability_tier(source, direct_url),
                "article_text": clean_text(desc),
                "search_source": "BING_NEWS"
            })
    except Exception as e:
        print(f"[NewsSearch] Bing News search note: {e}")
    return results

def search_local_db(keywords: List[str], limit: int = 4) -> List[Dict[str, Any]]:
    """
    Search local verified news archive ONLY when title strictly contains the keywords.
    Never searches raw_text to prevent /new news from hijacking /search results!
    """
    if not DB_PATH.exists() or not keywords:
        return []
    
    results = []
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            conditions = []
            params = []
            for kw in keywords[:4]:
                if len(kw) > 2:
                    conditions.append("title LIKE ?")
                    params.append(f"%{kw}%")
            
            if not conditions:
                return []
            
            # Must match at least one keyword in the TITLE
            sql = f"""
                SELECT title, source, url, published_at, raw_text
                FROM articles
                WHERE {' OR '.join(conditions)}
                ORDER BY published_at DESC
                LIMIT ?
            """
            params.append(limit)
            rows = conn.execute(sql, params).fetchall()
            
            for r in rows:
                title = html.unescape(r["title"] or "")
                source = r["source"] or "Sports News"
                url = r["url"] or ""
                pub = r["published_at"] or ""
                text = r["raw_text"] or ""
                results.append({
                    "headline": title,
                    "source": source,
                    "url": url,
                    "published_at": pub,
                    "timestamp": parse_date_to_timestamp(pub),
                    "reliability_tier": determine_reliability_tier(source, url),
                    "article_text": text,
                    "search_source": "DB_ARCHIVE"
                })
    except Exception as e:
        print(f"[NewsSearch] Local DB search note: {e}")
    return results

def search_football_news(query: str, max_results: int = 12) -> List[Dict[str, Any]]:
    """
    Precision live internet sports search for /search:
    1. Queries Google News RSS and Bing News RSS for the exact query.
    2. Strictly filters candidates: every story MUST match the query terms in its headline.
    3. Scores candidates by headline relevance and recency.
    4. Guarantees 0 pollution from unrelated /new stories.
    """
    clean_q = query.strip()
    if not clean_q:
        return []
    
    stop_words = {"the", "a", "an", "is", "in", "on", "at", "for", "to", "and", "or", "of", "with", "about", "not", "football"}
    keywords = [w for w in re.findall(r'\b[a-zA-Z]{3,}\b', clean_q.lower()) if w not in stop_words]
    
    # 1. Search Google News & Bing News
    g_items = search_google_news(clean_q, limit=max_results)
    b_items = search_live_internet(clean_q, limit=max_results)
    
    # 2. Search local DB only for strict title matches
    db_items = search_local_db(keywords, limit=3)
    
    all_candidates = g_items + b_items + db_items
    clean_q_lower = clean_q.lower()
    
    scored_candidates = []
    seen_titles = set()
    
    for c in all_candidates:
        hl = c.get("headline", "").strip()
        if not hl:
            continue
            
        hl_lower = hl.lower()
        
        # Calculate strict query relevance score
        rel_score = 0
        if clean_q_lower in hl_lower:
            rel_score += 10 # Exact search query in headline
        
        match_count = sum(1 for kw in keywords if kw in hl_lower)
        rel_score += (match_count * 3)
        
        # STRICT RELEVANCE GATE: If headline does not contain ANY keyword, REJECT it!
        if rel_score == 0 and keywords:
            continue
        
        # Deduplication signature
        title_tokens = tuple(w for w in re.findall(r'\b[a-zA-Z]{3,}\b', hl_lower) if w not in stop_words)[:5]
        if not title_tokens or title_tokens in seen_titles:
            continue
        seen_titles.add(title_tokens)
        
        c["relevance_score"] = rel_score
        scored_candidates.append(c)
    
    # Sort strictly by (relevance_score, timestamp) descending
    scored_candidates.sort(key=lambda x: (x.get("relevance_score", 0), x.get("timestamp", 0.0)), reverse=True)
    return scored_candidates[:max_results]
