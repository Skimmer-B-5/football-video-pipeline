import cv2
import numpy as np
from pathlib import Path
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parent.parent
img_dir = PROJECT_ROOT / "beta" / "remotion" / "public" / "images" / "story_tg_1795519137"

face_casc = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

print(f"Inspecting images in: {img_dir}\n")
for img_p in sorted(img_dir.glob("*.png")):
    with Image.open(img_p) as pil_img:
        w, h = pil_img.size
        arr = np.array(pil_img.convert("RGB"))
        gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
        
        # Blur check
        lap_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        # Face check
        faces = face_casc.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(40, 40))
        
        face_info = []
        for (fx, fy, fw, fh) in faces:
            # Check safe zone in 1080x1920
            # Safe zone: y in [240, 1300]
            face_top = fy
            face_bottom = fy + fh
            face_info.append(f"y={face_top}..{face_bottom} (size {fw}x{fh})")
            
        print(f"[{img_p.name}] Res: {w}x{h} | BlurVar: {lap_var:.1f} | Faces ({len(faces)}): {', '.join(face_info) if face_info else 'None'}")
