import sys
from pathlib import Path

root = Path(r"C:\Users\sb000\.gemini\antigravity\scratch\football-video-pipeline\beta")
sys.path.insert(0, str(root))

from stages.visual_agent import VisualAgent
import urllib.request
import cv2
import numpy as np

agent = VisualAgent()
cands = agent.search_candidates_bing("Endrick Real Madrid portrait", max_results=20)
face_casc = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

for c in cands:
    u = c["url"]
    if any(b in u.lower() for b in ["alamy", "getty", "shutterstock", "stock", "depositphotos"]):
        continue
    try:
        req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=4) as resp:
            raw = resp.read()
        im = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR)
        if im is None:
            continue
        ih, iw = im.shape[:2]
        faces = face_casc.detectMultiScale(cv2.cvtColor(im, cv2.COLOR_BGR2GRAY), 1.1, 4)
        if len(faces) == 0:
            continue
        fx, fy, fw, fh = sorted(faces, key=lambda x: x[2] * x[3], reverse=True)[0]
        cx, cy = fx + fw / 2, fy + fh / 2

        # Face-Aware Safe-Zone Cropping Algorithm
        h_crop = max(int(fh * 4.2), int(ih * 0.55))
        h_crop = min(ih, h_crop)
        w_crop = int(h_crop * 9 / 16)
        if w_crop > iw:
            w_crop = iw
            h_crop = int(iw * 16 / 9)

        y0 = int(cy - 0.28 * h_crop)
        y0 = max(0, min(ih - h_crop, y0))
        x0 = int(cx - w_crop / 2)
        x0 = max(0, min(iw - w_crop, x0))

        face_final_y = int((fy - y0) / h_crop * 1920)
        face_final_h = int(fh / h_crop * 1920)
        face_final_x = int((fx - x0) / w_crop * 1080)

        is_safe = 260 <= face_final_y and (face_final_y + face_final_h <= 1150)
        print("SUCCESS!")
        print(f"Title: {c['title'][:45]}")
        print(f"Original Size: {iw}x{ih} | Face at y={fy}, fh={fh}")
        print(f"Crop window: x0={x0}, y0={y0}, w={w_crop}, h={h_crop}")
        print(f"Final 1080x1920 Face: y={face_final_y} to {face_final_y + face_final_h} | x={face_final_x}")
        print(f"Safe zone (y in [260, 1150]) verified: {is_safe}")
        break
    except Exception as e:
        pass
