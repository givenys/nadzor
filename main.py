import sys
import os
import cv2
import requests
import logging
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.dynamic import DynamicConfig
from core.face_system import FaceRecognitionSystem
from utils.video import video_capture_context, FPSCalculator
from utils.logging_config import setup_logging

# НАСТРОЙКИ
NODE_JS_URL = "http://localhost:3001/api/cams/upload"
DEVICE_ID = "81826630-e466-441d-9f92-351d6c3fe423"
API_KEY = "my-secret-camera-key-2026"
SHOW_LOCAL_WINDOW = False

stop_event = threading.Event()

latest_frame = None
latest_frame_lock = threading.Lock()

def camera_worker():
    """Поток 1"""
    global latest_frame
    logger = logging.getLogger(__name__)
    logger.info("Camera worker started")
    
    with video_capture_context(0, 640, 480) as cap:
        logger.info("Камера открыта")
        fps_calc = FPSCalculator()
        frame_count = 0
        
        while not stop_event.is_set():
            ret, frame = cap.read()
            if not ret:
                logger.error("Не удалось получить кадр")
                time.sleep(0.1)
                continue
            
            fps = fps_calc.update()
            frame_count += 1
            
            # Сохраняем САМЫЙ СВЕЖИЙ кадр (перезаписываем предыдущий)
            with latest_frame_lock:
                latest_frame = frame.copy()
            
            # Логируем статистику
            if frame_count % 150 == 0:
                logger.info(f"FPS: {fps:.1f}")
    
    logger.info("Camera worker stopped")

def ai_and_sender_worker():
    """Поток 2: AI обработка + отправка на сервер"""
    global latest_frame
    logger = logging.getLogger(__name__)
    logger.info("AI + Sender worker started")
    
    config = DynamicConfig()
    config.frame_skip = 1
    system = FaceRecognitionSystem(config, enable_yolo=True, enable_fire=True,
                                   yolo_conf_threshold=0.4, 
                                   fire_conf_threshold=0.5)
    
    processed_count = 0
    
    while not stop_event.is_set():
        # Берём САМЫЙ СВЕЖИЙ кадр
        with latest_frame_lock:
            if latest_frame is None:
                time.sleep(0.01)
                continue
            frame = latest_frame.copy()
        
        # AI обработка
        start_time = time.time()
        last_data = system.recognize_faces(frame)
        yolo_objects = system.detect_yolo_objects(frame)
        
        # Отрисовка результатов
        frame_with_ai = system.draw_results(frame, last_data, yolo_objects)
        processing_time = time.time() - start_time
        
        processed_count += 1
        
        # Кодируем в JPEG
        _, buffer = cv2.imencode('.jpg', frame_with_ai, 
                                [int(cv2.IMWRITE_JPEG_QUALITY), 60])
        
        # Отправляем на сервер
        try:
            response = requests.post(
                NODE_JS_URL,
                data=buffer.tobytes(),
                headers={
                    'Content-Type': 'image/jpeg',
                    'X-Device-ID': DEVICE_ID,
                    'X-API-Key': API_KEY,
                    'X-Source': 'AI'
                },
                timeout=1
            )
            
            if response.status_code == 200:
                if processed_count % 10 == 0:
                    logger.debug(f"AI processed {processed_count} frames, time: {processing_time:.3f}s")
            else:
                logger.warning(f"Server status: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            logger.debug(f"Network error")
    
    logger.info(f"AI + Sender worker stopped. Processed: {processed_count}")

def main():
    logger = setup_logging(level="INFO")
    logger.info("Запуск стриминга (2 потока)...")
    logger.info(f"URL: {NODE_JS_URL}")

    # Создаем потоки
    threads = []
    
    # Поток 1: Камера (читает кадры и сохраняет самый свежий)
    camera_thread = threading.Thread(target=camera_worker, name="CameraWorker", daemon=True)
    threads.append(camera_thread)
    
    # Поток 2: AI обработка + отправка на сервер
    ai_thread = threading.Thread(target=ai_and_sender_worker, name="AIWorker", daemon=True)
    threads.append(ai_thread)

    # Запускаем все потоки
    for thread in threads:
        thread.start()
        logger.info(f"Started: {thread.name}")

    logger.info("Стриминг запущен. Ctrl+C для остановки.")

    try:
        # Основной поток ждет
        while not stop_event.is_set():
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Остановлено пользователем")
    
    finally:
        # Останавливаем все потоки
        stop_event.set()
        for thread in threads:
            thread.join(timeout=3)
        
        logger.info("Все потоки остановлены")

if __name__ == "__main__":
    main()