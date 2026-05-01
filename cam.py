import cv2
import os
from datetime import datetime

# Cartella dove salvare l'immagine
save_dir = "./img/"
os.makedirs(save_dir, exist_ok=True)

# Nome file con timestamp
filename = datetime.now().strftime("foto_%Y%m%d_%H%M%S.jpg")
filepath = os.path.join(save_dir, filename)

# Apre la webcam (0 = prima webcam collegata)
cap = cv2.VideoCapture(1)

if not cap.isOpened():
    raise RuntimeError("Impossibile aprire la webcam")

# Legge un frame
ret, frame = cap.read()

if not ret:
    cap.release()
    raise RuntimeError("Impossibile catturare l'immagine")

# Salva l'immagine
cv2.imwrite(filepath, frame)

# Rilascia la webcam
cap.release()

print(f"Immagine salvata in: {filepath}")