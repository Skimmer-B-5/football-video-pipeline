import json
from pathlib import Path

cand_dir = Path("beta/workspaces/endrick_milan/run_v7_1/assets/candidates")
for j in sorted(cand_dir.glob("*.json")):
    d = json.loads(j.read_text(encoding="utf-8"))
    print(f"{j.name}: scene={d.get('scene_id')} | subj={d.get('intended_subject')} | url={str(d.get('source_url'))[:70]}")
