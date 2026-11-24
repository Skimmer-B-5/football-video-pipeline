import sys
from pathlib import Path

BETA_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BETA_ROOT))
PROJECT_ROOT = BETA_ROOT.parent
sys.path.insert(1, str(PROJECT_ROOT))

print(f"Testing collector from BETA_ROOT: {BETA_ROOT}")
from stages.collector import run_collector
from stages.ranker import cluster_and_rank

print("Running collector...")
new_count = run_collector()
print(f"Scrape completed. Inserted {new_count} articles.")

print("Running ranker...")
ranked = cluster_and_rank()
print(f"Ranking completed. Got {len(ranked)} ranked stories.")
for i, s in enumerate(ranked[:5], 1):
    print(f"  {i}. [{s['reliability_tier']}] (Score: {s['ranking_score']}) {s['headline']}")
