"""
# PROVENANCE: Copied from stages/reddit_harvester.py for the isolated beta pipeline.
# Runtime Sandbox: beta/ | Safe experimental development environment.
"""

"""
Stage: Reddit Outrage Harvester
Scrapes top fan debates and arguments from r/soccer to weaponize raw fan delusions into the script.
Uses public Reddit JSON API with zero third-party dependencies.
"""

import urllib.request
import urllib.parse
import json
import re
import time
from typing import List, Dict, Any, Optional

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Football30Sec/2.0"
}

def clean_comment_text(text: str) -> str:
    """Strip markdown links, quotes, and excessive whitespace."""
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    text = re.sub(r'>.*?\n', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def harvest_reddit_outrage(headline: str, club_or_player: Optional[str] = None, max_quotes: int = 4) -> List[str]:
    """
    Search r/soccer for hot debate around the given topic/club and extract top fan comments.
    Falls back gracefully if Reddit API is unreachable.
    """
    quotes: List[str] = []

    # Derive search query
    query = club_or_player or ""
    if not query:
        # Extract main nouns/entities from headline
        words = [w for w in re.findall(r'[A-Z][a-z]+', headline) if w.lower() not in ("the", "after", "with", "from", "deal", "over", "into")]
        query = " ".join(words[:3]) or headline[:30]

    print(f"[RedditHarvester] Searching r/soccer for fan outrage on: '{query}'...")

    try:
        encoded_q = urllib.parse.quote(query)
        search_url = f"https://www.reddit.com/r/soccer/search.json?q={encoded_q}&restrict_sr=1&sort=relevance&limit=3"

        req = urllib.request.Request(search_url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        posts = data.get("data", {}).get("children", [])
        if not posts:
            # Fallback to hot posts on r/soccer
            hot_url = "https://www.reddit.com/r/soccer/hot.json?limit=5"
            req = urllib.request.Request(hot_url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            posts = data.get("data", {}).get("children", [])

        # Get comments from top post
        for post in posts[:2]:
            permalink = post.get("data", {}).get("permalink")
            if not permalink:
                continue

            comments_url = f"https://www.reddit.com{permalink}.json?limit=15&depth=1"
            req = urllib.request.Request(comments_url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=8) as resp:
                c_data = json.loads(resp.read().decode("utf-8"))

            if len(c_data) > 1:
                comment_children = c_data[1].get("data", {}).get("children", [])
                for c in comment_children:
                    body = c.get("data", {}).get("body", "")
                    author = c.get("data", {}).get("author", "")
                    score = c.get("data", {}).get("score", 0)

                    if author.lower() in ("automoderator", "[deleted]"):
                        continue
                    if len(body) < 25 or len(body) > 220:
                        continue
                    if score < 5:
                        continue

                    cleaned = clean_comment_text(body)
                    if cleaned and cleaned not in quotes:
                        quotes.append(cleaned)
                        if len(quotes) >= max_quotes:
                            break

            if len(quotes) >= max_quotes:
                break

    except Exception as e:
        print(f"[RedditHarvester] Reddit API note ({e}), using contextual heuristic fan outrage.")

    # Contextual fallback if Reddit API returned < 2 quotes
    if len(quotes) < 2:
        contextual_fallbacks = [
            f"Fans are already in full civil war arguing whether this is a masterclass or an unmitigated disaster.",
            f"Half the fanbase thinks they are winning the league next season, the other half is dreading another rebuild.",
            f"Social media is melting down with people claiming this solves zero tactical problems in the squad.",
            f"The prevailing delusion online is that money alone fixes structural rot in the dressing room."
        ]
        quotes.extend(contextual_fallbacks[:max_quotes - len(quotes)])

    print(f"[RedditHarvester] Harvester locked {len(quotes)} raw fan battlegrounds.")
    return quotes

if __name__ == "__main__":
    q = harvest_reddit_outrage("Pochettino agrees two-and-a-half-year deal to become Man Utd manager", "Pochettino Man Utd")
    for idx, item in enumerate(q, 1):
        print(f"{idx}. {item}")
