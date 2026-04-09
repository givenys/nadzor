import cv2
import os
import numpy as np
import time
from datetime import datetime
from deepface import DeepFace

# --- КОНФИГУРАЦИЯ ПО УМОЛЧАНИЮ ---
REFERENCE_FOLDER = "reference_faces"
WEBCAM_ID = 0
MODEL_NAME = "SFace"
DETECTOR_BACKEND = "opencv"

class DynamicConfig:
    """Контейнер для параметров, которые можно менять на лету"""
    def __init__(self):
        self.threshold = 0.40       # Порог сходства (0.0 - 1.0)
        self.frame_skip = 5         # Пропуск кадров
        self.analysis_scale = 0.6   # Масштаб анализа (0.2 - 1.0)
        self.min_face_area = 2500   # Мин. площадь лица в пикселях

class FaceRecognitionSystem:
    def __init__(self, config: DynamicConfig):
        self.config = config
        self.known_embeddings = []
        print(f"[INFO] Инициализация системы (Модель: {MODEL_NAME})...")
        
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        
        self._warmup_model()
        self._load_reference_faces()
        print("[OK] Система готова к работе")

    def _warmup_model(self):
        try:
            dummy = np.zeros((100, 100, 3), dtype=np.uint8)
            DeepFace.represent(
                dummy, model_name=MODEL_NAME, detector_backend='skip', enforce_detection=False
            )
        except Exception:
            pass

    def _load_reference_faces(self):
        if not os.path.exists(REFERENCE_FOLDER):
            os.makedirs(REFERENCE_FOLDER)
            print(f"[WARN] Папка '{REFERENCE_FOLDER}' не найдена. Создана пустая.")
            return

        self.known_embeddings.clear()
        count = 0
        for filename in os.listdir(REFERENCE_FOLDER):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                name = os.path.splitext(filename)[0]
                img_path = os.path.join(REFERENCE_FOLDER, filename)
                try:
                    result = DeepFace.represent(
                        img_path, model_name=MODEL_NAME, 
                        detector_backend=DETECTOR_BACKEND, enforce_detection=False
                    )
                    if result and len(result) > 0:
                        emb = np.array(result[0]['embedding'])
                        self.known_embeddings.append({'name': name, 'embedding': emb})
                        count += 1
                except Exception as e:
                    print(f"[WARN] Ошибка загрузки {filename}: {e}")
        print(f"[INFO] Загружено лиц в базу: {count}")

    def reload_base(self):
        """Мягкая перезагрузка базы без полного рестарта"""
        print("[INFO] Перезагрузка базы...")
        self._load_reference_faces()
        print("[OK] База обновлена")

    def recognize_faces(self, frame):
        if not self.known_embeddings:
            return []

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
        
        if len(faces) == 0:
            return []

        # Читаем актуальные параметры из конфига
        scale = max(0.2, min(1.0, self.config.analysis_scale))
        min_area = max(1000, min(10000, self.config.min_face_area))
        
        small_frame = cv2.resize(frame, (0, 0), fx=scale, fy=scale)
        recognized_data = []
        
        for (x, y, w, h) in faces:
            x_s, y_s = int(x * scale), int(y * scale)
            w_s, h_s = int(w * scale), int(h * scale)
            
            if w_s * h_s < min_area:
                continue
                
            face_crop = small_frame[y_s:y_s+h_s, x_s:x_s+w_s]
            if face_crop.size == 0:
                continue

            try:
                current_emb = DeepFace.represent(
                    face_crop, model_name=MODEL_NAME, 
                    detector_backend='skip', enforce_detection=False
                )
                if not current_emb or len(current_emb) == 0:
                    continue
                    
                current_vec = np.array(current_emb[0]['embedding'])
                best_name, min_dist = "Unknown", float('inf')
                
                for known in self.known_embeddings:
                    dist = np.linalg.norm(current_vec - known['embedding'])
                    if dist < min_dist:
                        min_dist = dist
                        best_name = known['name']
                        
                threshold = max(0.1, min(1.0, self.config.threshold))
                if min_dist <= threshold:
                    recognized_data.append({"name": best_name, "bbox": (x, y, x+w, y+h), "color": (0, 255, 0)})
                else:
                    recognized_data.append({"name": f"Unknown ({min_dist:.2f})", "bbox": (x, y, x+w, y+h), "color": (0, 0, 255)})
            except Exception:
                continue
        return recognized_data

    def draw_results(self, frame, data):
        for item in data:
            x1, y1, x2, y2 = item["bbox"]
            cv2.rectangle(frame, (x1, y1), (x2, y2), item["color"], 2)
            cv2.putText(frame, item["name"], (x1, y1 - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, item["color"], 2)
        cv2.putText(frame, f"Faces: {len(data)} | Model: {MODEL_NAME}", (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        return frame

def main():
    config = DynamicConfig()
    system = FaceRecognitionSystem(config)

    cap = cv2.VideoCapture(WEBCAM_ID)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    if not cap.isOpened():
        print("[ERROR] Камера не найдена")
        return

    # --- ПАНЕЛЬ УПРАВЛЕНИЯ ---
    cv2.namedWindow("Controls")
    cv2.resizeWindow("Controls", 320, 220)
    cv2.moveWindow("Controls", 660, 10) # Справа от видео (640+20 отступ)

    # Инициализация трекбаров (значения x100 для float)
    cv2.createTrackbar("Threshold x100", "Controls", int(config.threshold * 100), 100, lambda x: None)
    cv2.createTrackbar("Frame Skip", "Controls", config.frame_skip, 15, lambda x: None)
    cv2.createTrackbar("Scale x100", "Controls", int(config.analysis_scale * 100), 80, lambda x: None)
    cv2.createTrackbar("Min Face Area", "Controls", config.min_face_area, 10000, lambda x: None)
    
    # Кнопка "Reload Base" (0 -> 1 триггерит перезагрузку)
    cv2.createTrackbar("[RELOAD BASE]", "Controls", 0, 1, lambda x: None)
    cv2.setTrackbarPos("[RELOAD BASE]", "Controls", 0)

    print("[INFO] Нажмите 'q' для выхода. Меняйте параметры в панели 'Controls'")

    frame_count = 0
    last_data = []
    prev_time = time.time()
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Читаем актуальные значения с панели
        config.threshold = cv2.getTrackbarPos("Threshold x100", "Controls") / 100.0
        config.frame_skip = max(1, cv2.getTrackbarPos("Frame Skip", "Controls"))
        config.analysis_scale = cv2.getTrackbarPos("Scale x100", "Controls") / 100.0
        config.min_face_area = cv2.getTrackbarPos("Min Face Area", "Controls")
        
        # Мягкая перезагрузка базы
        if cv2.getTrackbarPos("[RELOAD BASE]", "Controls") == 1:
            system.reload_base()
            cv2.setTrackbarPos("[RELOAD BASE]", "Controls", 0)

        # Корректный FPS
        curr_time = time.time()
        fps = 1.0 / (curr_time - prev_time) if (curr_time - prev_time) > 0 else 0
        prev_time = curr_time

        # Обработка с пропуском кадров
        if frame_count % config.frame_skip == 0:
            last_data = system.recognize_faces(frame)
            
        frame = system.draw_results(frame, last_data)
        
        cv2.putText(frame, f"FPS: {fps:.1f}", (frame.shape[1] - 110, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        timestamp = datetime.now().strftime("%H:%M:%S")
        cv2.putText(frame, timestamp, (frame.shape[1] - 160, 60), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        cv2.imshow('Video Feed', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        frame_count += 1

    cap.release()
    cv2.destroyAllWindows()
    print("[INFO] Завершено.")

if __name__ == "__main__":
    main()