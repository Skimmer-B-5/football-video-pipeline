import sys
import re
import math
import html
import yaml
import hashlib
import sqlite3
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Dict, List, Any, Set, Tuple, Optional

# Let's test the enhanced collector and ranking logic
FEEDS = [
    {
        "name": "Google News Transfers",
        "url": "https://news.google.com/rss/search?q=%22football%22+AND+(transfer+OR+transfers+OR+signing+OR+bid+OR+contract)+when:2d&hl=en-GB&gl=GB&ceid=GB:en",
        "tier_weight": 1.0
    },
    {
        "name": "Transfermarkt",
        "url": "https://www.transfermarkt.com/rss/news",
        "tier_weight": 0.95
    },
    {
        "name": "Football Italia",
        "url": "https://football-italia.net/feed/",
        "tier_weight": 0.90
    },
    {
        "name": "BBC Sport",
        "url": "https://feeds.bbci.co.uk/sport/football/rss.xml",
        "tier_weight": 1.0
    },
    {
        "name": "Sky Sports News",
        "url": "https://www.skysports.com/rss/11095",
        "tier_weight": 0.95
    },
    {
        "name": "The Guardian",
        "url": "https://www.theguardian.com/football/rss",
        "tier_weight": 0.95
    },
    {
        "name": "CaughtOffside",
        "url": "https://www.caughtoffside.com/feed/",
        "tier_weight": 0.85
    }
]

NON_FOOTBALL_TERMS = {
    "baseball", "mlb", "nfl", "american football", "quarterback", "super bowl",
    "nba", "basketball", "padel", "darts", "pdc", "golf", "pga", "ryder cup",
    "cricket", "rugby", "tennis", "wimbledon", "f1", "formula 1", "grand prix",
    "ufc", "mma", "boxing", "snooker", "horse racing", "athletics", "pub chain"
}

TOP_CLUBS = {
    "real madrid", "barcelona", "arsenal", "chelsea", "liverpool", "manchester united",
    "man utd", "manchester city", "man city", "tottenham", "spurs", "bayern munich",
    "bayern", "borussia dortmund", "dortmund", "paris saint-germain", "psg",
    "juventus", "inter milan", "inter", "ac milan", "milan", "atletico madrid",
    "atletico", "sporting cp", "sporting", "napoli", "roma", "aston villa", "newcastle"
}

TRANSFER_TRIGGERS = {
    "transfer", "transfers", "bid", "bids", "bidding", "sign", "signs", "signing", "signed",
    "contract", "clause", "release clause", "buyback", "hijack", "deal", "talks", "agreed",
    "agree", "medical", "fee", "loan", "swap", "exit", "target", "targets", "pursuit",
    "eye", "eyes", "eyeing", "plot", "plots", "swoop", "replace", "replacement"
}

FLUFF_REJECT_PATTERNS = [
    r'\bfpl\b', r'fantasy\s+premier', r'gameweek', r'women[\'s]*\s+world\s+cup',
    r'match\s+report', r'highlights', r'player\s+ratings', r'predicted\s+lineup',
    r'how\s+to\s+watch', r'stream\s+live', r'press\s+conference', r'injury\s+update',
    r'verdict:\s+how\s+every', r'mascot', r'power\s+rankings'
]

def clean_html(raw_html: str) -> str:
    if not raw_html:
        return ""
    clean = re.sub(r'<script.*?</script>', '', raw_html, flags=re.DOTALL | re.IGNORECASE)
    clean = re.sub(r'<style.*?</style>', '', clean, flags=re.DOTALL | re.IGNORECASE)
    clean = re.sub(r'<[^<]+?>', ' ', clean)
    clean = re.sub(r'\s+', ' ', clean).strip()
    return html.unescape(clean)

def is_valid_transfer_story(title: str, text: str) -> Tuple[bool, str]:
    t_lower = title.lower()
    full_lower = f"{t_lower} {text[:300].lower()}"

    # 1. Hard check for non-football sports
    for term in NON_FOOTBALL_TERMS:
        if re.search(rf'\b{re.escape(term)}\b', t_lower):
            return False, f"Non-football sport: {term}"

    # 2. Reject fluff, match reports, fantasy, rankings
    for pat in FLUFF_REJECT_PATTERNS:
        if re.search(pat, t_lower):
            return False, f"Fluff pattern: {pat}"

    # 3. Must have a transfer trigger word
    has_transfer = any(re.search(rf'\b{re.escape(w)}\b', t_lower) for w in TRANSFER_TRIGGERS)
    if not has_transfer:
        return False, "No transfer trigger keyword in title"

    # 4. Must mention at least one recognized top club OR prominent football keyword
    has_club = any(c in full_lower for c in TOP_CLUBS)
    has_football_kw = any(w in full_lower for w in ["premier league", "champions league", "la liga", "serie a", "bundesliga", "striker", "winger", "midfielder", "centre-back", "defender", "manager"])
    if not (has_club or has_football_kw):
        return False, "No recognized club or league entity"

    return True, "Valid"

print("Testing enhanced validator against samples:")
samples = [
    ("Mauricio Pochettino targets new striker in January transfer window - The Times", "Chelsea and Tottenham former manager..."),
    ("Man Utd transfer news: Fulham defender Calvin Bassey is in talks over new contract amid Man Utd links", "Sky Sports report..."),
    ("Pub chain drops bid to serve children after backlash - BBC", "A pub chain..."),
    ("Padel players complete 50-hour world record bid - BBC", "Padel sport..."),
    ("Transfer window verdict: how every Premier League club fared - The Guardian", "Summer review..."),
    ("FPL Gameweek 12 Transfer Tips 2026/27: Who to Target", "Fantasy tips..."),
    ("Milan prepare €60m bid for Endrick - BeSoccer", "Real Madrid Brazilian starlet..."),
    ("Barcelona make official Ronald Araujo to Liverpool transfer announcement", "LiveScore report..."),
    ("Are Man Utd genuinely in a relegation battle?", "Matchday review...")
]

for title, txt in samples:
    ok, reason = is_valid_transfer_story(title, txt)
    status = "✅ PASS" if ok else "❌ REJECT"
    print(f"  {status} [{reason}]: {title}")


print("\n--- POLLING LIVE FEEDS & RANKING STORIES ---")
articles = []
for feed in FEEDS:
    url = feed["url"]
    name = feed["name"]
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 Football30Sec/2.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = resp.read()
            root = ET.fromstring(data)
            items = root.findall(".//item")
            print(f"[{name}] Found {len(items)} items")
            for it in items:
                title = it.findtext("title", "").strip()
                link = it.findtext("link", "").strip()
                pub_date = it.findtext("pubDate", "").strip()
                desc = clean_html(it.findtext("description", "") or "")
                source_elem = it.find("source")
                item_source = source_elem.text.strip() if source_elem is not None and source_elem.text else name

                # If Google News title has " - Source" at the end, clean it
                clean_title = re.sub(r'\s+-\s+[A-Za-z0-9\s\.\']+$', '', title).strip()

                is_valid, reason = is_valid_transfer_story(clean_title, desc)
                if is_valid:
                    articles.append({
                        "title": clean_title,
                        "source": item_source,
                        "url": link,
                        "published_at": pub_date,
                        "desc": desc,
                        "feed_weight": feed["tier_weight"]
                    })
    except Exception as e:
        print(f"[{name}] Error: {e}")

print(f"\nTotal Validated Transfer Stories: {len(articles)}")

# Deduplicate by title similarity
unique_stories = []
for art in articles:
    words_a = set(re.findall(r'\b[a-zA-Z]{4,}\b', art["title"].lower()))
    is_dup = False
    for u in unique_stories:
        words_u = set(re.findall(r'\b[a-zA-Z]{4,}\b', u["title"].lower()))
        jaccard = len(words_a & words_u) / max(1, len(words_a | words_u))
        if jaccard > 0.5:
            is_dup = True
            break
    if not is_dup:
        unique_stories.append(art)

print(f"Unique Deduplicated Stories: {len(unique_stories)}")

# Rank by Virality Score:
# 1. Breaking urgency verbs (bid, agree, talks, medical, clause, hijack)
# 2. Megaclub stature (Real Madrid, Man Utd, Barca, Arsenal, Liverpool, Bayern, Chelsea, City)
# 3. Source weight
def score_story(s: Dict[str, Any]) -> float:
    t = s["title"].lower()
    score = 10.0 * s.get("feed_weight", 1.0)
    
    # Big club boost
    for c in TOP_CLUBS:
        if c in t:
            score += 15.0
            break
            
    # High-impact transfer keywords
    high_impact = ["€", "£", "bid", "agreed", "agree", "medical", "hijack", "clause", "signs", "target", "talks"]
    for kw in high_impact:
        if kw in t:
            score += 8.0
            
    return round(score, 2)

unique_stories.sort(key=score_story, reverse=True)

print("\n--- TOP 10 HIGH-VIRALITY TRANSFER STORIES ---")
for i, s in enumerate(unique_stories[:10], 1):
    sc = score_story(s)
    print(f"{i}. [{s['source']}] (Score: {sc}) {s['title']}")
