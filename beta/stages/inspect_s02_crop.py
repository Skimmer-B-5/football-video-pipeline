import cv2
import numpy as np
from pathlib import Path

cand_p = Path("beta/workspaces/endrick_milan/run_v7_1/assets/candidates/cand_S02_e3c35c4a37.jpg")
cand = cv2.imread(str(cand_p))
h, w = cand.shape[:2]

# A 9:16 crop from height 760 needs width = 760 * 9 / 16 = 427.5 -> 428 pixels!
target_w = int(h * 9 / 16) # 427
print(f"To get 9:16 from height {h}, target width is {target_w} (out of {w})")

# If face center is at x=411:
# If crop is [x=411 - 214, x=411 + 214] = [197, 625]:
# What did the previous crop do?
prev_p = Path("beta/workspaces/endrick_milan/run_v7_1/assets/approved/S02_approved_9ae4d40a.png")
prev = cv2.imread(str(prev_p))
print(f"Previous approved S02 shape: {prev.shape}")

# Let's see where the face was in prev:
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
gray_prev = cv2.cvtColor(prev, cv2.COLOR_BGR2GRAY)
faces_prev = face_cascade.detectMultiScale(gray_prev, 1.1, 4)
print("Faces in previous approved S02:", faces_prev)
for (fx, fy, fw, fh) in faces_prev:
    print(f"  Face in 1080x1920: x={fx}, y={fy}, w={fw}, h={fh}, right_edge={fx+fw} (canvas width=1080)")
