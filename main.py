import cv2
import os
import numpy as np
import time
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import logging
from contextlib import contextmanager
from insightface.app import FaceAnalysis

# --- КОНФИГУРАЦИЯ ---
REFERENCE_FOLDER = "reference_faces"
WEBCAM_ID = 0
# InsightFace использует модели по умолчанию (ArcFace), название для отображения
DEFAULT_MODEL_NAME = "ArcFace (InsightFace)"
WINDOW_WIDTH = 640
WINDOW_HEIGHT = 480
CONTROLS_WINDOW_WIDTH = 320
CONTROLS_WINDOW_HEIGHT = 220
CONTROLS_WINDOW_OFFSET_X = 20

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


@contextmanager
def video_capture_context(cam_id: int, width: int, height: int):
    """Контекстный менеджер для безопасной работы с камерой"""
    cap = cv2.VideoCapture(cam_id)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    if not cap.isOpened():
        logger.error("Камера не найдена")
        raise RuntimeError(f"Не удалось открыть камеру {cam_id}")
    try:
        yield cap
    finally:
        cap.release()
        cv2.destroyAllWindows()


class DynamicConfig:
    """Контейнер для параметров, которые можно менять на лету"""
    def __init__(self):
        # Порог для косинусного расстояния (обычно 0.3 - 0.6 для ArcFace)
        self.threshold: float = 0.50       
        self.frame_skip: int = 3           # Пропуск кадров (InsightFace быстрее, можно меньше пропускать)
        self.min_face_area: int = 2500     # Мин. площадь лица в пикселях
        self.model_name: str = DEFAULT_MODEL_NAME


class FaceData:
    """Структура данных о распознанном лице"""
    def __init__(self, name: str, bbox: Tuple[int, int, int, int], 
                 color: Tuple[int, int, int], confidence: float = 0.0):
        self.name = name
        self.bbox = bbox
        self.color = color
        self.confidence = confidence


class FaceRecognitionSystem:
    def __init__(self, config: DynamicConfig):
        self.config = config
        self.known_embeddings: List[Dict] = []
        self.known_embeddings_matrix: Optional[np.ndarray] = None  # Матрица для векторизации
        self.known_norms: Optional[np.ndarray] = None  # Предвычисленные нормы
        logger.info(f"Инициализация InsightFace (Модель: {config.model_name})...")
        
        # Инициализация InsightFace App
        # det_size влияет на скорость: (320, 320) быстрее, (640, 640) точнее для мелких лиц
        try:
            self.app = FaceAnalysis(providers=['CPUExecutionProvider'])
            # Уменьшаем det_size для повышения FPS. Если лица мелкие, можно вернуть (640, 640)
            self.app.prepare(ctx_id=0, det_size=(320, 320))
            logger.info("InsightFace успешно инициализирован (det_size=320x320)")
        except Exception as e:
            logger.error(f"Ошибка инициализации InsightFace: {e}")
            raise e
        
        self._warmup_model()
        self._load_reference_faces()
        logger.info("Система готова к работе")

    def _warmup_model(self):
        """Прогрев модели для ускорения первой итерации"""
        try:
            dummy = np.zeros((100, 100, 3), dtype=np.uint8)
            self.app.get(dummy)
            logger.debug("Модель прогрета")
        except Exception as e:
            logger.warning(f"Прогрев модели не удался: {e}")

    def _load_reference_faces(self):
        """Загрузка эталонных лиц из папки с векторизацией для ускорения"""
        if not os.path.exists(REFERENCE_FOLDER):
            os.makedirs(REFERENCE_FOLDER)
            logger.warning(f"Папка '{REFERENCE_FOLDER}' не найдена. Создана пустая.")
            return

        self.known_embeddings.clear()
        self.known_embeddings_matrix = None
        self.known_norms = None
        count = 0
        
        for filename in os.listdir(REFERENCE_FOLDER):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                name = os.path.splitext(filename)[0]
                img_path = os.path.join(REFERENCE_FOLDER, filename)
                try:
                    img = cv2.imread(img_path)
                    if img is None:
                        logger.warning(f"Не удалось прочитать изображение {filename}")
                        continue
                        
                    faces = self.app.get(img)
                    if faces and len(faces) > 0:
                        # Берем первое найденное лицо на фото
                        emb = faces[0].embedding
                        self.known_embeddings.append({'name': name, 'embedding': emb})
                        count += 1
                        logger.debug(f"Лицо {name} добавлено в базу")
                    else:
                        logger.warning(f"Лица не найдены на изображении {filename}")
                except Exception as e:
                    logger.warning(f"Ошибка загрузки {filename}: {e}")
        
        logger.info(f"Загружено лиц в базу: {count}")
        
        # Векторизация базы для ускорения сравнения (матричные операции вместо цикла)
        if self.known_embeddings:
            embeddings_list = [k['embedding'] for k in self.known_embeddings]
            self.known_embeddings_matrix = np.array(embeddings_list)
            # Предвычисляем нормы один раз при загрузке
            self.known_norms = np.linalg.norm(self.known_embeddings_matrix, axis=1, keepdims=True)
            logger.info("База векторизована для ускоренного сравнения")

    def reload_base(self):
        """Мягкая перезагрузка базы без полного рестарта"""
        logger.info("Перезагрузка базы...")
        self._load_reference_faces()
        logger.info("База обновлена")

    def recognize_faces(self, frame: np.ndarray) -> List[FaceData]:
        """Распознавание лиц на кадре с помощью InsightFace (векторизованное сравнение)"""
        if not self.known_embeddings or self.known_embeddings_matrix is None:
            return []

        # InsightFace сам выполняет детекцию и выравнивание
        faces = self.app.get(frame)
        
        if not faces:
            return []

        recognized_data: List[FaceData] = []
        threshold = np.clip(self.config.threshold, 0.1, 1.0)
        min_area = np.clip(self.config.min_face_area, 1000, 10000)
        
        for face in faces:
            # Получаем bounding box (x1, y1, x2, y2)
            bbox = face.bbox.astype(int)
            x1, y1, x2, y2 = bbox
            w, h = x2 - x1, y2 - y1
            
            # Фильтрация по площади
            if w * h < min_area:
                continue
            
            current_vec = face.embedding.reshape(1, -1)  # (1, dim)
            
            # ВЕКТОРИЗОВАННОЕ СРАВНЕНИЕ: вместо цикла по всем известным лицам
            # используем матричное умножение для вычисления всех сходств сразу
            dot_products = np.dot(current_vec, self.known_embeddings_matrix.T)  # (1, N)
            
            # Нормы уже предвычислены, берем норму текущего вектора
            norm_current = np.linalg.norm(current_vec)
            if norm_current == 0:
                continue
                
            # Косинусное сходство для всех лиц сразу
            cosine_similarities = dot_products / (norm_current * self.known_norms.flatten())  # (N,)
            
            # Находим лучшее совпадение
            best_idx = np.argmax(cosine_similarities)
            max_sim = cosine_similarities[best_idx]
            best_name = self.known_embeddings[best_idx]['name']
            
            # Конвертируем сходство в "расстояние" для порога
            distance = 1.0 - max_sim
            
            # Уверенность
            confidence = max(0.0, max_sim) 
            
            if distance <= threshold:
                recognized_data.append(
                    FaceData(name=best_name, bbox=(x1, y1, x2, y2), 
                            color=(0, 255, 0), confidence=confidence)
                )
            else:
                recognized_data.append(
                    FaceData(name=f"Unknown", bbox=(x1, y1, x2, y2), 
                            color=(0, 0, 255), confidence=0.0)
                )
        
        return recognized_data

    def draw_results(self, frame: np.ndarray, data: List[FaceData]) -> np.ndarray:
        """Отрисовка результатов распознавания"""
        for item in data:
            x1, y1, x2, y2 = item.bbox
            cv2.rectangle(frame, (x1, y1), (x2, y2), item.color, 2)
            
            # Преобразуем confidence в float, т.к. InsightFace возвращает ndarray
            if isinstance(item.confidence, np.ndarray):
                conf_value = float(item.confidence[0]) if item.confidence.size > 0 else 0.0
            else:
                conf_value = item.confidence
            
            label = f"{item.name} ({conf_value:.2f})" if conf_value > 0 else item.name
            
            cv2.putText(frame, label, (x1, y1 - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, item.color, 2)
        
        info_text = f"Faces: {len(data)} | Model: {self.config.model_name}"
        cv2.putText(frame, info_text, (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        return frame

def main():
    config = DynamicConfig()
    system = FaceRecognitionSystem(config)

    try:
        with video_capture_context(WEBCAM_ID, WINDOW_WIDTH, WINDOW_HEIGHT) as cap:
            # --- ПАНЕЛЬ УПРАВЛЕНИЯ ---
            cv2.namedWindow("Controls")
            cv2.resizeWindow("Controls", CONTROLS_WINDOW_WIDTH, CONTROLS_WINDOW_HEIGHT)
            cv2.moveWindow("Controls", WINDOW_WIDTH + CONTROLS_WINDOW_OFFSET_X, 10)

            # Инициализация трекбаров
            # Threshold: для косинусного расстояния (0.3-0.6 типично)
            cv2.createTrackbar("Threshold x100", "Controls", int(config.threshold * 100), 100, lambda x: None)
            cv2.createTrackbar("Frame Skip", "Controls", config.frame_skip, 15, lambda x: None)
            # Убран трекбар Scale x100, т.к. InsightFace сам масштабирует
            cv2.createTrackbar("Min Face Area", "Controls", config.min_face_area, 10000, lambda x: None)
            
            # Кнопка "Reload Base" (0 -> 1 триггерит перезагрузку)
            cv2.createTrackbar("[RELOAD BASE]", "Controls", 0, 1, lambda x: None)
            cv2.setTrackbarPos("[RELOAD BASE]", "Controls", 0)

            logger.info("Нажмите 'q' для выхода. Меняйте параметры в панели 'Controls'")

            frame_count = 0
            last_data: List[FaceData] = []
            prev_time = time.time()
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                # Читаем актуальные значения с панели
                config.threshold = cv2.getTrackbarPos("Threshold x100", "Controls") / 100.0
                config.frame_skip = max(1, cv2.getTrackbarPos("Frame Skip", "Controls"))
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

    except RuntimeError as e:
        logger.error(f"Критическая ошибка: {e}")
    finally:
        logger.info("Завершено.")


if __name__ == "__main__":
    main()