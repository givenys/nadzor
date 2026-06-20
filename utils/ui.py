"""
Утилиты для работы с пользовательским интерфейсом: отрисовка, панель управления.
"""
import cv2
import numpy as np
from typing import List, Dict, Any, Optional

from core.face_system import FaceData


def draw_results(frame: np.ndarray, data: List[FaceData], model_name: str) -> np.ndarray:
    """
    Отрисовка результатов распознавания на кадре.
    
    Args:
        frame: Кадр для отрисовки
        data: Список распознанных лиц
        model_name: Название модели для отображения
        
    Returns:
        Кадр с нанесёнными результатами
    """
    for item in data:
        x1, y1, x2, y2 = item.bbox
        cv2.rectangle(frame, (x1, y1), (x2, y2), item.color, 2)
        
        # Преобразуем confidence в float
        if isinstance(item.confidence, np.ndarray):
            conf_value = float(item.confidence[0]) if item.confidence.size > 0 else 0.0
        else:
            conf_value = item.confidence
        
        label = f"{item.name} ({conf_value:.2f})" if conf_value > 0 else item.name
        
        cv2.putText(frame, label, (x1, y1 - 10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, item.color, 2)
    
    info_text = f"Faces: {len(data)} | Model: {model_name}"
    cv2.putText(frame, info_text, (10, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
    return frame


def create_controls_window(window_name: str, width: int, height: int, 
                          offset_x: int, offset_y: int = 10) -> None:
    """
    Создание окна панели управления с трекбарами.
    
    Args:
        window_name: Название окна
        width: Ширина окна
        height: Высота окна
        offset_x: Позиция X относительно главного окна
        offset_y: Позиция Y
    """
    cv2.namedWindow(window_name)
    cv2.resizeWindow(window_name, width, height)
    cv2.moveWindow(window_name, 640 + offset_x, offset_y)  # 640 = ширина основного окна
    
    # Трекбары основных параметров
    cv2.createTrackbar("Threshold x100", window_name, 50, 100, lambda x: None)
    cv2.createTrackbar("Frame Skip", window_name, 3, 15, lambda x: None)
    cv2.createTrackbar("Min Face Area", window_name, 2500, 10000, lambda x: None)
    
    # Трекбары для настройки улучшения освещения
    cv2.createTrackbar("CLAHE Clip", window_name, 20, 50, lambda x: None)
    cv2.createTrackbar("Gamma Dark x10", window_name, 18, 30, lambda x: None)
    cv2.createTrackbar("Brightness Thresh", window_name, 70, 150, lambda x: None)
    
    # Кнопка "Reload Base"
    cv2.createTrackbar("[RELOAD BASE]", window_name, 0, 1, lambda x: None)
    cv2.setTrackbarPos("[RELOAD BASE]", window_name, 0)


def read_control_params(window_name: str) -> Dict[str, Any]:
    """
    Чтение текущих значений параметров из панели управления.
    
    Args:
        window_name: Название окна с трекбарами
        
    Returns:
        Словарь с текущими значениями параметров
    """
    params = {
        'threshold': cv2.getTrackbarPos("Threshold x100", window_name) / 100.0,
        'frame_skip': max(1, cv2.getTrackbarPos("Frame Skip", window_name)),
        'min_face_area': cv2.getTrackbarPos("Min Face Area", window_name),
        'clahe_clip': cv2.getTrackbarPos("CLAHE Clip", window_name) / 10.0,
        'gamma_dark': cv2.getTrackbarPos("Gamma Dark x10", window_name) / 10.0,
        'brightness_thresh': cv2.getTrackbarPos("Brightness Thresh", window_name),
        'reload_base': cv2.getTrackbarPos("[RELOAD BASE]", window_name) == 1
    }
    return params


def update_enhancer_params(enhancer: Any, clahe_clip: float, gamma_dark: float,
                          brightness_thresh: float) -> None:
    """
    Обновление параметров улучшителя освещения.
    
    Args:
        enhancer: Экземпляр LowLightEnhancer
        clahe_clip: Значение CLAHE clip limit
        gamma_dark: Значение gamma для тёмных кадров
        brightness_thresh: Порог яркости
    """
    if (clahe_clip != enhancer.clahe_clip_limit or 
        brightness_thresh != enhancer.brightness_threshold):
        enhancer.update_clahe(clip_limit=clahe_clip, 
                             grid_size=enhancer.clahe_grid_size)
        enhancer.brightness_threshold = brightness_thresh
    enhancer.gamma_dark = gamma_dark
