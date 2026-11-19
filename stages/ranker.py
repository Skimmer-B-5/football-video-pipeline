"""
Stage 2: News Ranker & Clusterer.
Clusters near-duplicate transfer stories, computes recency-weighted scores,
and assigns deterministic, rule-based reliability tiers:
- 'confirmed': Official club/league source OR >= 3 independent credible outlets.
- 'credible': Exactly 2 independent credible outlets.
- 'rumour': Single source / unverified.
Never outputs hallucinated or invented percentages. Logs full ranking rationale to evidence/ranking_log.json.
"""

import sys
import os
import re
import json
import yaml
import math
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Dict, List, Any, Set, Tuple, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from pipeline.state_manager import get_db_connection
from pipeline.resource_monitor import ResourceTracker

CONFIG_PATH = PROJECT_ROOT / "config" / "config.yaml"
EVIDENCE_DIR = PROJECT_ROOT / "evidence"

# Words to ignore when matching story entities
STOPWORDS = {
    "a", "an", "the", "in", "on", "at", "for", "to", "of", "and", "or", "is",
    "are", "was", "were", "be", "been", "being", "have", "has", "had", "do",
    "does", "did", "but", "by", "from", "with", "as", "about", "into", "through",
    "after", "before", "between", "under", "above", "football", "news", "report",
    "reports", "live", "update", "updates", "breaking", "latest", "transfer", "transfers"
}

NON_FOOTBALL_SPORTS = {
    "darts", "golf", "pga", "dp world tour", "ryder cup", "cricket", "rugby",
    "tennis", "wimbledon", "f1", "formula 1", "grand prix", "ufc", "mma", "boxing",
    "nfl", "nba", "snooker", "moto gp", "motogp", "horse racing", "athletics"
}

GENERIC_HUB_PATTERNS = [
    r"latest news,\s*transfers,\s*rumours and updates",
    r"latest transfers,\s*rumours and updates",
    r"transfers,\s*rumours and gossip",
    r"premier league \d{4}/\d{2,4}:\s*latest",
    r"transfer centre live",
    r"football weekly video",
    r"gossip column",
    r"paper talk:",
    r"live text commentary",
    r"fixtures and results",
    r"league table",
]

FOOTBALL_INDICATORS = {
    "football", "soccer", "striker", "winger", "midfielder", "defender", "goalkeeper",
    "manager", "head coach", "premier league", "la liga", "serie a", "bundesliga",
    "ligue 1", "champions league", "europa league", "ballon d'or", "transfer", "fifa",
    "uefa", "arsenal", "chelsea", "liverpool", "manchester united", "man utd", "mufc",
    "manchester city", "man city", "mcfc", "tottenham", "spurs", "real madrid",
    "barcelona", "barca", "bayern", "psg", "juventus", "ac milan", "inter milan",
    "atletico", "newcastle", "aston villa", "sporting", "porto", "benfica", "ajax",
    "dortmund", "leverkusen", "napoli", "roma", "laliga", "mls", "al nassr", "al-nassr",
    "contract", "signing", "bid", "release clause", "loan", "medical", "free agent"
}

def is_football_story(title: str, text: str) -> bool:
    """Strictly verify the article is about football/soccer and not other sports or generic hubs."""
    t_lower = title.lower()
    full_lower = f"{t_lower} {text[:300].lower()}"

    # Hard rejection for generic news hub pages
    for pattern in GENERIC_HUB_PATTERNS:
        if re.search(pattern, t_lower):
            return False

    # Hard rejection for non-football sport headlines
    for sport in NON_FOOTBALL_SPORTS:
        # Match as whole word or phrase
        if re.search(rf'\b{re.escape(sport)}\b', t_lower):
            return False

    # Positive requirement: must have at least one football indicator
    return any(re.search(rf'\b{re.escape(term)}\b', full_lower) for term in FOOTBALL_INDICATORS)

def clean_tokens(text: str) -> Set[str]:
    """Extract normalized alphanumeric tokens, stripping stopwords."""
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    return {w for w in words if w not in STOPWORDS}

def token_similarity(set_a: Set[str], set_b: Set[str]) -> float:
    """Calculate Jaccard similarity of headline tokens to detect near-duplicate stories."""
    if not set_a or not set_b:
        return 0.0
    intersection = set_a.intersection(set_b)
    union = set_a.union(set_b)
    return len(intersection) / len(union) if union else 0.0

def parse_article_time(date_str: Optional[str]) -> datetime:
    """Parse various RSS date formats to UTC datetime."""
    if not date_str:
        return datetime.now(timezone.utc)
    try:
        dt = parsedate_to_datetime(date_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        pass
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return datetime.now(timezone.utc)

def calculate_recency_factor(published_dt: datetime, halflife_hours: float = 12.0) -> float:
    """Exponential decay based on hours since publication."""
    now = datetime.now(timezone.utc)
    age_hours = max(0.0, (now - published_dt).total_seconds() / 3600.0)
    decay_rate = math.log(2) / halflife_hours
    return math.exp(-decay_rate * age_hours)

def is_official_source(url: str, official_domains: List[str]) -> bool:
    """Check if the source URL belongs to an official club or league domain."""
    url_lower = url.lower()
    return any(domain.lower() in url_lower for domain in official_domains)

def cluster_and_rank():
    """Cluster stories, compute deterministic reliability tiers, and rank top stories."""
    with ResourceTracker("Ranker"):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        official_domains = config.get("official_domains", [])
        cluster_threshold = config.get("ranking", {}).get("cluster_similarity_threshold", 0.40)
        halflife = config.get("ranking", {}).get("recency_halflife_hours", 12.0)

        with get_db_connection() as conn:
            rows = conn.execute("""
                SELECT id, hash, title, source, url, published_at, raw_text, scraped_at
                FROM articles
                ORDER BY id DESC LIMIT 100
            """).fetchall()

        if not rows:
            print("[Ranker] No articles found in database.")
            return []

        raw_articles = [dict(r) for r in rows]
        articles = [a for a in raw_articles if is_football_story(a['title'], a['raw_text'])]
        print(f"[Ranker] Filtered {len(raw_articles)} recent items to {len(articles)} verified football stories.")

        for a in articles:
            a["tokens"] = clean_tokens(a["title"])
            a["pub_dt"] = parse_article_time(a["published_at"])

        # Agglomerative clustering
        clusters: List[List[Dict[str, Any]]] = []
        for art in articles:
            matched_cluster = None
            for cl in clusters:
                # Check similarity against cluster centroid/members
                for member in cl:
                    sim = token_similarity(art["tokens"], member["tokens"])
                    if sim >= cluster_threshold:
                        matched_cluster = cl
                        break
                if matched_cluster:
                    break

            if matched_cluster:
                matched_cluster.append(art)
            else:
                clusters.append([art])

        print(f"[Ranker] Clustered {len(articles)} articles into {len(clusters)} unique story clusters.")

        ranked_clusters = []
        ranking_ledger = []

        with get_db_connection() as conn:
            for cluster_idx, cl in enumerate(clusters, start=1):
                # Count independent sources
                sources = {item["source"] for item in cl}
                source_count = len(sources)

                # Check for official domain
                has_official = any(is_official_source(item["url"], official_domains) for item in cl)

                # Deterministic reliability tier assignment
                if has_official or source_count >= config.get("ranking", {}).get("confirmed_sources_count", 3):
                    tier = "confirmed"
                    tier_multiplier = 2.0
                elif source_count >= config.get("ranking", {}).get("credible_sources_count", 2):
                    tier = "credible"
                    tier_multiplier = 1.5
                else:
                    tier = "rumour"
                    tier_multiplier = 1.0

                # Representative article (prefer longest descriptive text)
                representative = max(cl, key=lambda x: len(x["raw_text"]))

                # Recency factor of newest article in cluster
                newest_dt = max(item["pub_dt"] for item in cl)
                recency_factor = calculate_recency_factor(newest_dt, halflife)

                # Viral hotness boost based on transfer keywords
                hot_keywords = [
                    "shock", "hijack", "bid", "agree", "blockbuster", "record", "done deal",
                    "medical", "agreed", "race", "swap", "sacked", "exit", "bombing", "signs",
                    "target", "official", "talks", "clause", "overhaul", "deal", "barcelona",
                    "real madrid", "manchester united", "chelsea", "liverpool", "arsenal"
                ]
                cl_text = " ".join(f"{it['title']} {it['raw_text']}" for it in cl).lower()
                hot_hits = sum(1 for kw in hot_keywords if kw in cl_text)
                hotness_boost = min(hot_hits * 3.5, 30.0)

                # Final ranking score (0 to 100 scale)
                raw_score = (recency_factor * 15.0 + hotness_boost) * (1.0 + (source_count - 1) * 0.4) * tier_multiplier
                final_score = round(raw_score, 2)

                # Persist to database
                for item in cl:
                    conn.execute("""
                        UPDATE articles
                        SET cluster_id = ?, reliability_tier = ?, ranking_score = ?
                        WHERE id = ?
                    """, (cluster_idx, tier, final_score, item["id"]))

                ranked_clusters.append({
                    "cluster_id": cluster_idx,
                    "representative_id": representative["id"],
                    "headline": representative["title"],
                    "source": representative["source"],
                    "url": representative["url"],
                    "published_at": representative["published_at"],
                    "reliability_tier": tier,
                    "source_count": source_count,
                    "sources": list(sources),
                    "ranking_score": final_score,
                    "recency_factor": round(recency_factor, 3),
                    "sample_text": representative["raw_text"][:250]
                })

                ranking_ledger.append({
                    "cluster_id": cluster_idx,
                    "representative_id": representative["id"],
                    "headline": representative["title"],
                    "tier": tier,
                    "tier_rationale": "Official source or >=3 outlets" if tier == "confirmed" else ("2 credible outlets" if tier == "credible" else "Single source / unverified"),
                    "source_count": source_count,
                    "sources": list(sources),
                    "url": representative["url"],
                    "recency_factor": round(recency_factor, 3),
                    "score": final_score,
                    "raw_text": representative["raw_text"]
                })

            conn.commit()

        # Sort clusters by score descending
        ranked_clusters.sort(key=lambda x: x["ranking_score"], reverse=True)
        ranking_ledger.sort(key=lambda x: x["score"], reverse=True)

        EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
        with open(EVIDENCE_DIR / "ranking_log.json", "w", encoding="utf-8") as f:
            json.dump(ranking_ledger, f, indent=2)

        print(f"[Ranker] Ranking log saved to evidence/ranking_log.json.")
        print(f"[Ranker] Top 3 stories:")
        for idx, item in enumerate(ranked_clusters[:3], 1):
            print(f"  {idx}. [{item['reliability_tier'].upper()}] (Score: {item['ranking_score']}) {item['headline']} ({item['source']})")

        return ranked_clusters

if __name__ == "__main__":
    top = cluster_and_rank()
