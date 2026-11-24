import cv2
from pathlib import Path

p = Path("beta/workspaces/endrick_milan/run_v7_1/assets/candidates/cand_S04_11fe2a9773.jpg")
img = cv2.imread(str(p))
print("cand_S04 shape:", img.shape)

face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
faces = face_cascade.detectMultiScale(gray, 1.1, 4)
print("Detected faces in S04 candidate:", faces)
for (x, y, w, h) in faces:
    print(f"Face: x={x}, y={y}, w={w}, h={h} | center=({x+w//2}, {y+h//2}) in image {img.shape[1]}x{img.shape[0]}")
