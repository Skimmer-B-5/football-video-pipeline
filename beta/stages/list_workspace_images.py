import json
from pathlib import Path
import cv2

p = Path("beta/workspaces/endrick_milan/run_v7_1/assets")
for f in sorted(p.rglob("*.*")):
    if f.suffix.lower() in [".jpg", ".jpeg", ".png"]:
        img = cv2.imread(str(f))
        sh = img.shape if img is not None else "None"
        print(f"{f.relative_to(p)}: shape={sh}, size={f.stat().st_size}")
