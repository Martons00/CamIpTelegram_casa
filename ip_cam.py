import cv2
import os
import time
from datetime import datetime
from pathlib import Path

RTSP_URL = Path("ip_cam_01.txt").read_text(encoding="utf-8").strip()
SAVE_DIR = "./img/cam1/"

os.makedirs(SAVE_DIR, exist_ok=True)

filename = datetime.now().strftime("snapshot_%Y%m%d_%H%M%S.jpg")
filepath = os.path.join(SAVE_DIR, filename)

cap = cv2.VideoCapture(RTSP_URL)

if not cap.isOpened():
    raise RuntimeError("Impossibile aprire lo stream RTSP")

frame = None
ret = False

for _ in range(10):
    ret, frame = cap.read()
    if ret and frame is not None:
        time.sleep(0.1)

cap.release()

if not ret or frame is None:
    raise RuntimeError("Impossibile leggere un frame valido dalla IP cam")

if not cv2.imwrite(filepath, frame):
    raise RuntimeError("Impossibile salvare lo snapshot")

print(f"Snapshot salvato in: {filepath}")