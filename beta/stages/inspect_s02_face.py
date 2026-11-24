import cv2
from pathlib import Path

p = Path("beta/workspaces/endrick_milan/run_v7_1/assets/candidates/cand_S02_e3c35c4a37.jpg")
img = cv2.imread(str(p))
print("cand_S02_e3c35c4a37.jpg shape:", img.shape) # (h, w, c)

face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
faces = face_cascade.detectMultiScale(gray, 1.1, 4)
print("Detected faces:", faces)
for (x, y, w, h) in faces:
    print(f"Face box: x={x}, y={y}, w={w}, h={h} | center_x={x + w//2}, center_y={y + h//2} in image {img.shape[1]}x{img.shape[0]}")
