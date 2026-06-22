"""
Face Recognition System - Core Logic
Основной класс системы распознавания лиц.
"""
import cv2
import numpy as np
from typing import List, Dict, Optional, Tuple, Any
import logging

from insightface.app import FaceAnalysis

from config.settings import (
    REFERENCE_FOLDER, INSIGHTFACE_DET_SIZE, 
    SUPPORTED_IMAGE_EXTENSIONS, DEFAULT_MODEL_NAME
)
from config.dynamic import DynamicConfig
from core.enhancer import LowLightEnhancer
from core.models import load_reference_faces, warmup_model
from core.yolo import YOLODetector

logger = logging.getLogger(__name__)


class FaceData:
    """Структура данных о распознанном лице"""
    
    def __init__(self, name: str, bbox: Tuple[int, int, int, int], 
                 color: Tuple[int, int, int], confidence: float = 0.0):
        self.name = name
        self.bbox = bbox
        self.color = color
        self.confidence = confidence


class FaceRecognitionSystem:
    """
    Основная система распознавания лиц.
    Использует InsightFace для детекции и генерации эмбеддингов.
    Также поддерживает YOLOv8 для детекции объектов COCO.
    """
    
    def __init__(self, config: DynamicConfig, enable_yolo: bool = True, enable_fire: bool = True, yolo_conf_threshold: float = 0.4, fire_conf_threshold: float = 0.5):
        """
        Инициализация системы распознавания.
        
        Args:
            config: Динамическая конфигурация с параметрами
            enable_yolo: Включить ли детекцию объектов YOLO
            yolo_conf_threshold: Порог уверенности для YOLO детекции
        """
        self.config = config
        self.known_embeddings: List[Dict] = []
        self.known_embeddings_matrix: Optional[np.ndarray] = None
        self.known_norms: Optional[np.ndarray] = None
        
        logger.info(f"Инициализация InsightFace (Модель: {config.model_name})...")
        
        # Инициализация InsightFace App
        try:
            self.app: Any = FaceAnalysis(providers=['CPUExecutionProvider'])
            self.app.prepare(ctx_id=0, det_size=INSIGHTFACE_DET_SIZE)
            logger.info(f"InsightFace успешно инициализирован (det_size={INSIGHTFACE_DET_SIZE[0]}x{INSIGHTFACE_DET_SIZE[1]})")
        except Exception as e:
            logger.error(f"Ошибка инициализации InsightFace: {e}")
            raise e
        
        warmup_model(self.app)
        self._load_reference_faces()
        
        # Инициализация улучшителя освещения
        self.enhancer = LowLightEnhancer(
            clahe_clip_limit=2.0,
            gamma_dark=1.8,
            brightness_threshold=70
        )
        
        # Инициализация YOLO детектора
        self.yolo_detector: Optional[YOLODetector] = None
        if enable_yolo:
            try:
                self.yolo_detector = YOLODetector(conf_threshold=yolo_conf_threshold)
                
                logger.info("YOLOv8 детектор успешно инициализирован")
            except Exception as e:
                logger.warning(f"Не удалось инициализировать YOLO: {e}. Детекция объектов будет отключена.")
                self.yolo_detector = None

        self.fire_detector: Optional[YOLODetector] = None
        if enable_fire:
            try:
                self.fire_detector = YOLODetector(
                    model_path="yolov8_fire.pt", 
                    conf_threshold=fire_conf_threshold
                )
                
                logger.info("YOLOv8 детектор успешно инициализирован")
            except Exception as e:
                logger.warning(f"Не удалось инициализировать YOLO: {e}. Детекция объектов будет отключена.")
                self.fire_detector = None
        
        logger.info("Система готова к работе")
    
    def _load_reference_faces(self):
        """Загрузка эталонных лиц из папки с векторизацией для ускорения"""
        self.known_embeddings, self.known_embeddings_matrix, self.known_norms = \
            load_reference_faces(self.app, REFERENCE_FOLDER, SUPPORTED_IMAGE_EXTENSIONS)
    
    def reload_base(self):
        """Мягкая перезагрузка базы без полного рестарта"""
        logger.info("Перезагрузка базы...")
        self._load_reference_faces()
        logger.info("База обновлена")
    
    def recognize_faces(self, frame: np.ndarray) -> List[FaceData]:
        """
        Распознавание лиц на кадре с улучшением при низкой освещённости.
        
        Args:
            frame: Кадр в формате BGR
            
        Returns:
            Список распознанных лиц
        """
        if not self.known_embeddings or self.known_embeddings_matrix is None:
            return []

        processed_frame = self.enhancer.enhance(frame)
        
        faces = self.app.get(processed_frame)
        
        if not faces:
            return []

        recognized_data: List[FaceData] = []
        threshold = np.clip(self.config.threshold, 0.1, 1.0)
        min_area = np.clip(self.config.min_face_area, 1000, 10000)
        
        for face in faces:

            bbox = face.bbox.astype(int)
            x1, y1, x2, y2 = bbox
            w, h = x2 - x1, y2 - y1
            
            if w * h < min_area:
                continue
            
            current_vec = face.embedding.reshape(1, -1)  # (1, dim)
            
            dot_products = np.dot(current_vec, self.known_embeddings_matrix.T)  # (1, N)

            norm_current = np.linalg.norm(current_vec)
            if norm_current == 0:
                continue

            cosine_similarities = dot_products / (norm_current * self.known_norms.flatten())  # (N,)
            
            best_idx = np.argmax(cosine_similarities)
            max_sim = cosine_similarities[best_idx]
            best_name = self.known_embeddings[best_idx]['name']
            
            distance = 1.0 - max_sim
            
            confidence = max(0.0, max_sim) 
            
            if distance <= threshold:
                recognized_data.append(
                    FaceData(name=best_name, bbox=(x1, y1, x2, y2), 
                            color=(0, 255, 0), confidence=confidence)
                )
            else:
                recognized_data.append(
                    FaceData(name="Unknown", bbox=(x1, y1, x2, y2), 
                            color=(0, 0, 255), confidence=0.0)
                )
        
        return recognized_data
    
    def draw_results(self, frame: np.ndarray, data: List[FaceData], 
                     yolo_objects: Optional[List[Dict[str, Any]]] = None) -> np.ndarray:
        """
        Отрисовка результатов распознавания лиц и объектов YOLO.
        
        Args:
            frame: Кадр для отрисовки
            data: Список распознанных лиц
            yolo_objects: Список обнаруженных объектов YOLO (опционально)
            
        Returns:
            Кадр с нанесёнными результатами
        """
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
        
        # Отрисовка объектов YOLO
        if yolo_objects:
            detector = self.yolo_detector or self.fire_detector
            if detector:
                frame = detector.draw_detections(frame, yolo_objects)
        
        info_parts = [f"Faces: {len(data)}"]
        if yolo_objects:
            info_parts.append(f"Objects: {len(yolo_objects)}")
        info_parts.append(f"Model: {self.config.model_name}")
        
        info_text = " | ".join(info_parts)
        cv2.putText(frame, info_text, (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        return frame
    
    def detect_yolo_objects(self, frame: np.ndarray) -> Optional[List[Dict[str, Any]]]:
        """
        Детекция объектов с помощью YOLO.
        
        Args:
            frame: Кадр в формате BGR
            
        Returns:
            Список обнаруженных объектов или None, если YOLO отключен
        """        
        objects = []
    
        if self.yolo_detector is not None:
            objects.extend(self.yolo_detector.detect_objects(frame))
        
        if self.fire_detector is not None:
            objects.extend(self.fire_detector.detect_objects(frame))
        
        return objects if objects else None
