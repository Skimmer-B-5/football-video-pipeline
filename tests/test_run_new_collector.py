import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) in sys.path:
    sys.path.remove(str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT))

print("[Test] Running collector with new Google News + Transfermarkt + Tier-1 feeds...")
from stages.collector import run_collector
new_count = run_collector()
print(f"[Test] Collector completed: {new_count} new articles inserted.")

print("[Test] Running ranker with strict football filter & virality formula...")
from stages.ranker import cluster_and_rank
top = cluster_and_rank()
print(f"[Test] Ranker finished: {len(top)} high-virality transfer clusters generated.")
print("\n--- TOP 10 STORIES AVAILABLE ON TELEGRAM /new ---")
for i, s in enumerate(top[:10], 1):
    print(f"  {i}. [{s['reliability_tier'].upper()}] ({s['source']}) Score: {s['ranking_score']}")
    print(f"     \"{s['headline']}\"")
