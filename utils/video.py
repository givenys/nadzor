import cv2
import threading
import time
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class ThreadedCamera:
    """
    Поточный захват видео. 
    Фоновый поток постоянно читает кадры и хранит только САМЫЙ СВЕЖИЙ.
    """
    
    def __init__(self, src: str, width: int = 640, height: int = 480):
        self.src = src
        self.width = width
        self.height = height
        self.running = True
        self.lock = threading.Lock()
        
        self.cap = self._open_capture()
        self.grabbed = False
        self.frame = None
        
        self.thread = threading.Thread(target=self._update, daemon=True)
        self.thread.start()
    
    def _open_capture(self):
        """Открытие capture с минимальным буфером"""
        cap = cv2.VideoCapture(self.src, cv2.CAP_FFMPEG)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 5000)
        cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 2000)
        
        if not cap.isOpened():
            raise RuntimeError(f"Не удалось открыть стрим: {self.src}")
        
        logger.info(f"📹 Стрим открыт: {self.src} ({self.width}x{self.height})")
        return cap
    
    def _update(self):
        """Фоновый поток: grab() + retrieve() для минимальной задержки"""
        while self.running:
            # grab() быстро переходит к следующему кадру БЕЗ декодирования
            if self.cap.grab():
                # retrieve() декодирует последний захваченный кадр
                ret, frame = self.cap.retrieve()
                if ret:
                    with self.lock:
                        self.frame = frame
                        self.grabbed = True
            else:
                # Стрим оборвался — переподключение
                logger.warning("⚠️ Стрим потерянен, переподключение...")
                self.cap.release()
                time.sleep(2)
                try:
                    self.cap = self._open_capture()
                except RuntimeError:
                    time.sleep(3)
    
    def read(self):
        """Возвращает САМЫЙ СВЕЖИЙ кадр (без задержки!)"""
        with self.lock:
            if self.grabbed:
                return True, self.frame.copy()
            return False, None
    
    def release(self):
        """Освобождение ресурсов"""
        self.running = False
        if self.thread.is_alive():
            self.thread.join(timeout=3)
        self.cap.release()
        logger.info("📹 Камера освобождена")


class video_capture_context:
    """Контекстный менеджер — обратная совместимость"""
    
    def __init__(self, cam_id, width: int = 640, height: int = 480):
        self.cam_id = cam_id
        self.width = width
        self.height = height
        self.camera: Optional[ThreadedCamera] = None
    
    def __enter__(self):
        self.camera = ThreadedCamera(
            "http://192.168.1.101:4747/video",
            self.width, 
            self.height
        )
        return self.camera
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.camera:
            self.camera.release()


class FPSCalculator:
    """Калькулятор FPS"""
    def __init__(self, avg_count=30):
        self.times = []
        self.avg_count = avg_count
    
    def update(self):
        now = time.time()
        self.times.append(now)
        if len(self.times) > self.avg_count:
            self.times.pop(0)
        if len(self.times) < 2:
            return 0.0
        return (len(self.times) - 1) / (self.times[-1] - self.times[0])

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