"""
beta/stages/ranker.py
Stage 2: High-Virality News Ranker & Clusterer.
Filters out non-football sports, fluff, match reports, and stale retrospectives.
Prioritizes genuine breaking transfer stories, top-tier sources, and megaclub moves.
Logs full ranking rationale to evidence/ranking_log.json.
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

STOPWORDS = {
    "a", "an", "the", "in", "on", "at", "for", "to", "of", "and", "or", "is",
    "are", "was", "were", "be", "been", "being", "have", "has", "had", "do",
    "does", "did", "but", "by", "from", "with", "as", "about", "into", "through",
    "after", "before", "between", "under", "above", "football", "news", "report",
    "reports", "live", "update", "updates", "breaking", "latest", "transfer", "transfers"
}

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
    "eye", "eyes", "eyeing", "plot", "plots", "swoop", "replace", "replacement", "renewal"
}

FLUFF_REJECT_PATTERNS = [
    r'\bfpl\b', r'fantasy\s+premier', r'gameweek', r'women[\'s]*\s+world\s+cup',
    r'match\s+report', r'highlights', r'player\s+ratings', r'predicted\s+lineup',
    r'how\s+to\s+watch', r'stream\s+live', r'press\s+conference', r'injury\s+update',
    r'verdict:\s+how\s+every', r'mascot', r'power\s+rankings', r'fears\s+mount',
    r'what\s+next\s+for', r'world\s+record\s+bid', r'five\s+kane\s+replacement'
]

TIER1_OUTLETS = {
    "The Times", "Sky Sports", "The Athletic", "BBC Sport", "The Guardian",
    "Telegraph", "Fabrizio Romano", "David Ornstein", "Cadena SER", "Gianluca Di Marzio",
    "L'Equipe", "Bild", "Florian Plettenberg", "Bavarian Football Works"
}

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

def calculate_recency_factor(published_dt: datetime, halflife_hours: float = 18.0) -> float:
    """Exponential decay based on hours since publication."""
    now = datetime.now(timezone.utc)
    age_hours = max(0.0, (now - published_dt).total_seconds() / 3600.0)
    decay_rate = math.log(2) / halflife_hours
    return math.exp(-decay_rate * age_hours)

def is_valid_transfer_story(title: str, text: str) -> bool:
    """Strictly verify the article is a high-relevance football transfer story."""
    t_lower = title.lower()
    full_lower = f"{t_lower} {text[:400].lower()}"

    # 1. Hard check for non-football sports
    for term in NON_FOOTBALL_TERMS:
        if re.search(rf'\b{re.escape(term)}\b', t_lower):
            return False

    # 2. Reject fluff, match reports, fantasy, rankings
    for pat in FLUFF_REJECT_PATTERNS:
        if re.search(pat, t_lower):
            return False

    # 3. Must have a transfer trigger word
    has_transfer = any(re.search(rf'\b{re.escape(w)}\b', t_lower) for w in TRANSFER_TRIGGERS)
    if not has_transfer:
        return False

    # 4. Must mention at least one recognized top club OR prominent football keyword
    has_club = any(c in full_lower for c in TOP_CLUBS)
    has_football_kw = any(w in full_lower for w in [
        "premier league", "champions league", "la liga", "serie a", "bundesliga",
        "striker", "winger", "midfielder", "centre-back", "defender", "manager"
    ])
    if not (has_club or has_football_kw):
        return False

    return True

def cluster_and_rank() -> List[Dict[str, Any]]:
    """Cluster stories, compute deterministic reliability tiers, and rank top stories."""
    with ResourceTracker("Ranker"):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        official_domains = config.get("official_domains", [])
        cluster_threshold = config.get("ranking", {}).get("cluster_similarity_threshold", 0.45)
        halflife = config.get("ranking", {}).get("recency_halflife_hours", 18.0)
        max_age_hours = config.get("ranking", {}).get("max_article_age_hours", 72.0)

        with get_db_connection() as conn:
            rows = conn.execute("""
                SELECT id, hash, title, source, url, published_at, raw_text, scraped_at
                FROM articles
                ORDER BY id DESC LIMIT 250
            """).fetchall()

        if not rows:
            print("[Ranker] No articles found in database.")
            return []

        now = datetime.now(timezone.utc)
        raw_articles = [dict(r) for r in rows]

        # 1. Filter out stale articles (> max_age_hours) & non-transfer stories
        articles = []
        for a in raw_articles:
            pub_dt = parse_article_time(a["published_at"])
            age_hours = (now - pub_dt).total_seconds() / 3600.0
            if age_hours > max_age_hours:
                continue
            if is_valid_transfer_story(a["title"], a["raw_text"]):
                a["pub_dt"] = pub_dt
                a["tokens"] = clean_tokens(a["title"])
                articles.append(a)

        print(f"[Ranker] Filtered {len(raw_articles)} recent items to {len(articles)} verified fresh transfer stories.")

        if not articles:
            return []

        # 2. Agglomerative clustering by entity tokens
        clusters: List[List[Dict[str, Any]]] = []
        for art in articles:
            matched_cluster = None
            for cl in clusters:
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
                sources = {item["source"] for item in cl}
                source_count = len(sources)

                # Check for official or Tier 1 outlet
                has_tier1 = any(item["source"] in TIER1_OUTLETS for item in cl)

                if has_tier1 or source_count >= 3:
                    tier = "confirmed"
                    tier_multiplier = 2.0
                elif source_count >= 2:
                    tier = "credible"
                    tier_multiplier = 1.5
                else:
                    tier = "rumour"
                    tier_multiplier = 1.0

                # Representative article (prefer Tier 1 outlet first, then longest text)
                representative = max(cl, key=lambda x: (100 if x["source"] in TIER1_OUTLETS else 0) + len(x["raw_text"]))

                # Recency factor of newest article in cluster
                newest_dt = max(item["pub_dt"] for item in cl)
                recency_factor = calculate_recency_factor(newest_dt, halflife)

                # Hotness score calculation
                cl_text = " ".join(f"{it['title']} {it['raw_text']}" for it in cl).lower()
                
                # A. Megaclub boost
                club_boost = 0.0
                for c in TOP_CLUBS:
                    if c in cl_text:
                        club_boost = 15.0
                        break

                # B. Breaking transfer verbs
                action_keywords = ["€", "£", "bid", "agreed", "agree", "medical", "hijack", "clause", "signs", "target", "talks", "renewal"]
                action_hits = sum(1 for kw in action_keywords if kw in cl_text)
                action_boost = min(action_hits * 4.0, 24.0)

                # C. Final virality formula
                raw_score = (recency_factor * 20.0 + club_boost + action_boost) * (1.0 + (source_count - 1) * 0.3) * tier_multiplier
                final_score = round(raw_score, 2)

                # Persist to database
                for item in cl:
                    conn.execute("""
                        UPDATE articles
                        SET cluster_id = ?, reliability_tier = ?, ranking_score = ?
                        WHERE id = ?
                    """, (cluster_idx, tier, final_score, item["id"]))

                cluster_info = {
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
                }
                ranked_clusters.append(cluster_info)

                ranking_ledger.append({
                    "cluster_id": cluster_idx,
                    "representative_id": representative["id"],
                    "headline": representative["title"],
                    "tier": tier,
                    "tier_rationale": "Tier 1 outlet or >=3 sources" if tier == "confirmed" else ("2 credible sources" if tier == "credible" else "Single source / unverified"),
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
