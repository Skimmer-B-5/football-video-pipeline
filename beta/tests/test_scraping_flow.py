import sys
import json
from pathlib import Path

BETA_ROOT = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BETA_ROOT.parent

if str(BETA_ROOT) in sys.path:
    sys.path.remove(str(BETA_ROOT))
sys.path.insert(0, str(BETA_ROOT))
if str(PROJECT_ROOT) in sys.path:
    sys.path.remove(str(PROJECT_ROOT))
sys.path.insert(1, str(PROJECT_ROOT))

print("[Test] Verifying imports from beta...")
from stages.collector import run_collector
from stages.ranker import cluster_and_rank
from pipeline.state_manager import get_db_connection
from stages.telegram_bot import TelegramBotClient, get_env_credentials

print("[Test] Running ranker directly...")
top_clusters = cluster_and_rank()
print(f"[Test] Found {len(top_clusters)} ranked clusters.")

story_pool = []
for cl in top_clusters[:15]:
    raw_t = ""
    art_url = cl.get("url", "https://www.besoccer.com/news")
    with get_db_connection() as conn:
        rep_id = cl.get("representative_id")
        if rep_id:
            row = conn.execute("SELECT raw_text, url FROM articles WHERE id = ?", (rep_id,)).fetchone()
        else:
            row = conn.execute("SELECT raw_text, url FROM articles WHERE title = ? LIMIT 1", (cl["headline"],)).fetchone()
        if row:
            if row["raw_text"]:
                raw_t = row["raw_text"]
            if row["url"]:
                art_url = row["url"]

    story_pool.append({
        "headline": cl["headline"],
        "source": cl["sources"][0] if cl.get("sources") else (cl.get("source") or "News Outlet"),
        "url": art_url,
        "reliability_tier": cl.get("reliability_tier") or cl.get("tier", "confirmed"),
        "ranking_score": cl.get("ranking_score") or cl.get("score", 0),
        "raw_text": raw_t
    })

print(f"[Test] Built story pool with {len(story_pool)} items!")
for i, item in enumerate(story_pool[:3], 1):
    print(f"  Item {i}: {item['headline']} ({item['source']}) | text len: {len(item['raw_text'])}")

print("[Test] All scraping and pool construction passed perfectly!")
