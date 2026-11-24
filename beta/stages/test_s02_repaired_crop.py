import cv2
from pathlib import Path

p = Path("beta/workspaces/endrick_milan/run_v7_1/assets/candidates/cand_S02_e3c35c4a37.jpg")
img = cv2.imread(str(p))

# Let's inspect where Endrick is in this image.
# Face 0 at (308, 84, 207, 207): center is x=411, y=187
# If we crop a 9:16 window centered at x=411:
h, w = img.shape[:2]
target_w = int(h * 9 / 16) # 427.5 -> 428
print(f"Image is {w}x{h}. Target crop width for 9:16 is {target_w}")

# If we center on x=411:
x1 = max(0, 411 - target_w // 2)
x2 = x1 + target_w
if x2 > w:
    x2 = w
    x1 = w - target_w

crop_centered = img[:, x1:x2]
print(f"Crop window: [{x1}:{x2}], shape={crop_centered.shape}")

# Resize to 1080x1920
crop_1080 = cv2.resize(crop_centered, (1080, 1920), interpolation=cv2.INTER_LANCZOS4)
out_p = Path("beta/workspaces/endrick_milan/run_v7_1/crops/test_s02_repaired_crop.png")
cv2.imwrite(str(out_p), crop_1080)
print(f"Saved {out_p}")

# Check face in this repaired crop:
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
gray = cv2.cvtColor(crop_1080, cv2.COLOR_BGR2GRAY)
faces = face_cascade.detectMultiScale(gray, 1.1, 4)
for (fx, fy, fw, fh) in faces:
    print(f"Face in repaired 1080x1920: x={fx}, y={fy}, w={fw}, h={fh}, right_edge={fx+fw}, left_margin={fx}, right_margin={1080-(fx+fw)}")
