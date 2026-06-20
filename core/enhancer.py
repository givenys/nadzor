"""
Адаптивное улучшение кадров для детекции в условиях низкой освещённости.
Использует CLAHE и gamma-коррекцию для улучшения видимости лиц в темноте.
"""
import cv2
import numpy as np
import logging

logger = logging.getLogger(__name__)


class LowLightEnhancer:
    """Адаптивное улучшение кадров для детекции в условиях низкой освещённости"""
    
    def __init__(self, 
                 clahe_clip_limit: float = 2.0,
                 clahe_grid_size: int = 8,
                 gamma_default: float = 1.0,
                 gamma_dark: float = 1.8,
                 brightness_threshold: int = 70):
        """
        Инициализация улучшителя освещения.
        
        Args:
            clahe_clip_limit: Лимит контраста для CLAHE (1.5-3.0)
            clahe_grid_size: Размер сетки для CLAHE
            gamma_default: Gamma для ярких кадров (обычно 1.0)
            gamma_dark: Gamma для тёмных кадров (1.5-2.2)
            brightness_threshold: Порог яркости для активации улучшения (0-255)
        """
        self.clahe_clip_limit = clahe_clip_limit
        self.clahe_grid_size = clahe_grid_size
        self.clahe = cv2.createCLAHE(clipLimit=clahe_clip_limit, 
                                     tileGridSize=(clahe_grid_size, clahe_grid_size))
        self.gamma_default = gamma_default
        self.gamma_dark = gamma_dark
        self.brightness_threshold = brightness_threshold
    
    def _measure_brightness(self, frame: np.ndarray) -> float:
        """
        Оценивает среднюю яркость кадра по яркостному каналу HSV.
        
        Args:
            frame: Кадр в формате BGR
            
        Returns:
            Средняя яркость (0-255)
        """
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        return np.mean(hsv[:, :, 2])
    
    def _gamma_correct(self, frame: np.ndarray, gamma: float) -> np.ndarray:
        """
        Применяет gamma-коррекцию к кадру.
        
        Args:
            frame: Входной кадр
            gamma: Коэффициент gamma (>1 осветляет, <1 затемняет)
            
        Returns:
            Кадр с применённой gamma-коррекцией
        """
        if gamma == 1.0:
            return frame
        
        inv_gamma = 1.0 / gamma
        table = np.array([(i / 255.0) ** inv_gamma * 255 
                         for i in np.arange(0, 256)]).astype("uint8")
        return cv2.LUT(frame, table)
    
    def enhance(self, frame: np.ndarray, force: bool = False) -> np.ndarray:
        """
        Улучшает кадр для детекции лиц.
        
        Args:
            frame: Входной кадр BGR
            force: Если True, применяет улучшение независимо от яркости
            
        Returns:
            Улучшенный кадр
        """
        brightness = self._measure_brightness(frame)
        
        # Если кадр достаточно яркий — возвращаем как есть (экономим время)
        if brightness >= self.brightness_threshold and not force:
            return frame
        
        # 1. Применяем CLAHE к яркостному каналу (не к цвету!)
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        hsv[:, :, 2] = self.clahe.apply(hsv[:, :, 2])
        enhanced = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
        
        # 2. Gamma-коррекция для тёмных кадров
        gamma = self.gamma_dark if brightness < self.brightness_threshold else self.gamma_default
        enhanced = self._gamma_correct(enhanced, gamma)
        
        logger.debug(f"🔦 Темный кадр (яркость={brightness:.1f}), применяем улучшение")
        
        return enhanced
    
    def update_clahe(self, clip_limit: float, grid_size: int = 8):
        """
        Пересоздаёт CLAHE с новыми параметрами.
        
        Args:
            clip_limit: Новый лимит контраста
            grid_size: Новый размер сетки
        """
        self.clahe_clip_limit = clip_limit
        self.clahe_grid_size = grid_size
        self.clahe = cv2.createCLAHE(clipLimit=clip_limit, 
                                     tileGridSize=(grid_size, grid_size))
