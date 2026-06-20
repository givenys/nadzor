"""
Утилиты для работы с видео: захват камеры, расчёт FPS.
"""
import cv2
import time
from typing import Generator, Optional
import logging

logger = logging.getLogger(__name__)


class video_capture_context:
    """Контекстный менеджер для безопасной работы с камерой"""
    
    def __init__(self, cam_id: int, width: int, height: int):
        """
        Инициализация контекстного менеджера камеры.
        
        Args:
            cam_id: ID камеры (0 для встроенной)
            width: Желаемая ширина кадра
            height: Желаемая высота кадра
        """
        self.cam_id = cam_id
        self.width = width
        self.height = height
        self.cap: Optional[cv2.VideoCapture] = None
    
    def __enter__(self) -> cv2.VideoCapture:
        """Открытие камеры при входе в контекст"""
        #self.cap = cv2.VideoCapture(self.cam_id)
        #self.cap = cv2.VideoCapture("http://10.26.166.98:4747/video")
        self.cap = cv2.VideoCapture("http://192.168.1.101:4747/video")
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        
        if not self.cap.isOpened():
            logger.error(f"Камера {self.cam_id} не найдена")
            raise RuntimeError(f"Не удалось открыть камеру {self.cam_id}")
        
        return self.cap
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Закрытие камеры и окон при выходе из контекста"""
        if self.cap is not None:
            self.cap.release()
        cv2.destroyAllWindows()


class FPSCalculator:
    """Калькулятор FPS для мониторинга производительности"""
    
    def __init__(self):
        """Инициализация калькулятора FPS"""
        self.prev_time: float = 0.0
        self.curr_time: float = 0.0
        self.fps: float = 0.0
    
    def update(self) -> float:
        """
        Обновление значения FPS.
        
        Returns:
            Текущее значение FPS
        """
        self.curr_time = time.time()
        delta = self.curr_time - self.prev_time
        
        if delta > 0:
            self.fps = 1.0 / delta
        else:
            self.fps = 0.0
        
        self.prev_time = self.curr_time
        return self.fps
    
    def get_fps(self) -> float:
        """
        Получение текущего значения FPS.
        
        Returns:
            Текущее значение FPS
        """
        return self.fps
