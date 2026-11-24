import cv2
from pathlib import Path

cand_p = Path("beta/workspaces/endrick_milan/run_v7_1/assets/candidates/cand_S02_e3c35c4a37.jpg")
img = cv2.imread(str(cand_p))
h, w = img.shape[:2]

face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
faces = face_cascade.detectMultiScale(gray, 1.1, 4)

out_dir = Path("beta/workspaces/endrick_milan/run_v7_1/assets/candidates")
for idx, (x, y, fw, fh) in enumerate(faces):
    face_crop = img[max(0, y-30):min(h, y+fh+30), max(0, x-30):min(w, x+fw+30)]
    cv2.imwrite(str(out_dir / f"temp_face_{idx}.jpg"), face_crop)
    print(f"Saved temp_face_{idx}.jpg: {fw}x{fh} at ({x}, {y})")
