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
    """
    
    def __init__(self, config: DynamicConfig):
        """
        Инициализация системы распознавания.
        
        Args:
            config: Динамическая конфигурация с параметрами
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

        # 🔦 Улучшаем кадр для детекции, если нужно
        processed_frame = self.enhancer.enhance(frame)
        
        # InsightFace работает с улучшенным кадром
        faces = self.app.get(processed_frame)
        
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
                    FaceData(name="Unknown", bbox=(x1, y1, x2, y2), 
                            color=(0, 0, 255), confidence=0.0)
                )
        
        return recognized_data
    
    def draw_results(self, frame: np.ndarray, data: List[FaceData]) -> np.ndarray:
        """
        Отрисовка результатов распознавания.
        
        Args:
            frame: Кадр для отрисовки
            data: Список распознанных лиц
            
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
        
        info_text = f"Faces: {len(data)} | Model: {self.config.model_name}"
        cv2.putText(frame, info_text, (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        return frame
