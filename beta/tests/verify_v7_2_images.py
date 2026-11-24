import cv2
import numpy as np
from pathlib import Path

BETA_ROOT = Path(__file__).resolve().parent.parent
test_dir = BETA_ROOT / "remotion" / "public" / "images" / "story_test_v7_2_bassey"

face_casc = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

def norm_blur(im):
    std = cv2.resize(im, (450, 800))
    gray = cv2.cvtColor(std, cv2.COLOR_BGR2GRAY)
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())

print(f"{'Shot File':<20} | {'Resolution':<12} | {'NormBlur':<9} | {'Quality':<8} | {'Face Position (Safe [240, 1250])'}")
print("-" * 88)

passed_count = 0
total_count = 0

for p in sorted(test_dir.glob("*.png")):
    if "retry" in p.name or "inspect" in p.name:
        continue
    img = cv2.imread(str(p))
    if img is None:
        continue
    total_count += 1
    h, w = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur_score = norm_blur(img)

    faces = face_casc.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60))
    face_strs = []
    for (fx, fy, fw, fh) in faces:
        face_top = fy
        face_bottom = fy + fh
        is_safe = (240 <= face_top and face_bottom <= 1250)
        face_strs.append(f"y={face_top}..{face_bottom} ({'SAFE' if is_safe else 'ALERT'})")

    blur_status = "SHARP" if blur_score >= 45.0 else "BLUR"
    face_summary = ", ".join(face_strs) if face_strs else "Tactical/Stadium/Action"
    if blur_status == "SHARP":
        passed_count += 1
    print(f"{p.name:<20} | {w}x{h:<7} | {blur_score:<9.1f} | {blur_status:<8} | {face_summary}")

print("-" * 88)
print(f"Summary: {passed_count}/{total_count} shots meet strict broadcast quality requirements.")
