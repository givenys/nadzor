"""
YOLOv8 Object Detection Module
Модуль для детекции объектов COCO с помощью YOLOv8.
"""
import cv2
import random
from pathlib import Path
from typing import List, Dict, Tuple, Any, Optional
import logging

logger = logging.getLogger(__name__)

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    logger.warning("ultralytics не установлен. YOLOv8 детекция будет недоступна.")


class YOLODetector:
    """
    Класс для детекции объектов с помощью YOLOv8.
    Поддерживает все COCO классы.
    """
    
    def __init__(self, model_path: Optional[str] = None, conf_threshold: float = 0.4):
        """
        Инициализация YOLO детектора.
        
        Args:
            model_path: Путь к файлу весов YOLOv8. Если None, используется yolov8n.pt
            conf_threshold: Порог уверенности для детекции
        """
        if not YOLO_AVAILABLE:
            raise RuntimeError("ultralytics не установлен. Установите: pip install ultralytics")
        
        self.conf_threshold = conf_threshold
        
        # Определяем путь к модели
        if model_path is None:
            # Используем встроенную модель yolov8n (nano - самая быстрая)
            self.model_path = "yolov8n.pt"
            logger.info(f"Использование стандартной модели YOLOv8: {self.model_path}")
        else:
            self.model_path = model_path
            model_file = Path(model_path)
            if not model_file.exists():
                raise FileNotFoundError(f"Файл весов YOLO не найден: {model_file}")
            logger.info(f"Использование кастомной модели YOLO: {self.model_path}")
        
        # Инициализация модели
        try:
            self.model = YOLO(str(self.model_path))
            self.class_names = self.model.names
            logger.info(f"YOLOv8 загружена. Классов: {len(self.class_names)}")
        except Exception as e:
            logger.error(f"Ошибка загрузки YOLO модели: {e}")
            raise e
        
        # Генерируем уникальный цвет для каждого класса (фиксируем seed для стабильности)
        random.seed(42)
        self.class_colors: Dict[int, Tuple[int, int, int]] = {
            cid: (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)) 
            for cid in self.class_names.keys()
        }
    
    def detect_objects(self, frame: cv2.Mat) -> List[Dict[str, Any]]:
        """
        Детекция объектов на кадре.
        
        Args:
            frame: Кадр в формате BGR
            
        Returns:
            Список обнаруженных объектов с их параметрами
        """
        results = self.model(frame, verbose=False, conf=self.conf_threshold)
        
        detected_objects: List[Dict[str, Any]] = []
        
        for r in results:
            if r.boxes is None:
                continue
                
            for box in r.boxes:
                conf = float(box.conf)
                if conf < self.conf_threshold:
                    continue
                
                cls_id = int(box.cls)
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                label = f"{self.class_names[cls_id]} {conf:.2f}"
                color = self.class_colors[cls_id]
                
                detected_objects.append({
                    'class_id': cls_id,
                    'class_name': self.class_names[cls_id],
                    'confidence': conf,
                    'bbox': (x1, y1, x2, y2),
                    'color': color,
                    'label': label
                })
        
        return detected_objects
    
    def draw_detections(self, frame: cv2.Mat, objects: List[Dict[str, Any]]) -> cv2.Mat:
        """
        Отрисовка检测结果 на кадре.
        
        Args:
            frame: Кадр для отрисовки
            objects: Список обнаруженных объектов
            
        Returns:
            Кадр с нанесёнными检测结果
        """
        for obj in objects:
            x1, y1, x2, y2 = obj['bbox']
            color = obj['color']
            label = obj['label']
            
            # Рамка
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            
            # Подпись с фоном для читаемости
            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(frame, (x1, y1 - 20), (x1 + tw, y1), color, -1)
            cv2.putText(frame, label, (x1, y1 - 5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        return frame
    
    def set_confidence_threshold(self, threshold: float):
        """
        Установка порога уверенности.
        
        Args:
            threshold: Новый порог (0.0 - 1.0)
        """
        self.conf_threshold = max(0.0, min(1.0, threshold))
        logger.info(f"Порог уверенности YOLO установлен: {self.conf_threshold}")
