import sys
import os
import cv2
import requests
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.dynamic import DynamicConfig
from core.face_system import FaceRecognitionSystem
from utils.video import video_capture_context, FPSCalculator
from utils.logging_config import setup_logging

# НАСТРОЙКИ
NODE_JS_URL = "http://localhost:3001/api/cams/upload"
DEVICE_ID = "81826630-e466-441d-9f92-351d6c3fe423"
API_KEY = "my-secret-camera-key-2026"
SEND_EVERY_N_FRAME = 3
JPEG_QUALITY = 75  # Уменьшили с 80 до 75 — быстрее кодирование

def send_frame(frame, url, device_id, api_key):
    """Отправка кадра в отдельном потоке"""
    try:
        _, buffer = cv2.imencode('.jpg', frame, 
                                  [int(cv2.IMWRITE_JPEG_QUALITY), JPEG_QUALITY])
        requests.post(
            url,
            data=buffer.tobytes(),
            headers={
                'Content-Type': 'image/jpeg',
                'X-Device-ID': device_id,
                'X-API-Key': api_key
            },
            timeout=2
        )
        return True
    except Exception as e:
        logger.debug(f"📡 Network error: {e}")
        return False


def main():
    setup_logging()
    logger = logging.getLogger(__name__)
    config = DynamicConfig()
    system = FaceRecognitionSystem(config)
    
    # Пул потоков для отправки (не блокирует основной цикл!)
    executor = ThreadPoolExecutor(max_workers=2)
    
    frames_sent = 0
    frames_failed = 0
    frame_count = 0
    send_counter = 0
    
    try:
        with video_capture_context(0, 640, 480) as cam:
            logger.info("✅ Камера открыта (ThreadedCamera)")
            fps_calc = FPSCalculator()
            last_data = []
            yolo_objects = []
            
            logger.info("🚀 Стриминг запущен. Ctrl+C для остановки.")
            
            last_data = []
            last_yolo_objects = []

            while True:
                # Читаем САМЫЙ СВЕЖИЙ кадр (без задержки!)
                ret, frame = cam.read()
                if not ret:
                    time.sleep(0.01)
                    continue
                
                fps = fps_calc.update()
                
                # # AI-обработка (только на нужных кадрах)
                # if frame_count % config.frame_skip == 0:
                #     last_data = system.recognize_faces(frame)
                #     yolo_objects = system.detect_yolo_objects(frame)
                if frame_count % config.frame_skip == 0:
                    last_data = system.recognize_faces(frame)
                    last_yolo_objects = system.detect_yolo_objects(frame) or []
                
                # Отрисовка
                #frame = system.draw_results(frame, last_data, yolo_objects)
                frame = system.draw_results(frame, last_data, last_yolo_objects)
                
                # 🔥 АСИНХРОННАЯ отправка на Node.js
                send_counter += 1
                if send_counter % SEND_EVERY_N_FRAME == 0:
                    # Отправляем в фоне — не блокируем цикл!
                    executor.submit(
                        send_frame, 
                        frame.copy(),  # копируем, пока поток не модифицировал
                        NODE_JS_URL, 
                        DEVICE_ID, 
                        API_KEY
                    )
                    frames_sent += 1
                
                frame_count += 1
                
                # Статистика раз в 5 секунд
                if frame_count % 150 == 0:
                    logger.info(f"📊 Frames: {frame_count} | FPS: {fps:.1f}")
    
    except KeyboardInterrupt:
        logger.info("⏹ Остановлено пользователем")
    finally:
        executor.shutdown(wait=False)
        logger.info(f"📊 Итоги: Отправлено ~{frames_sent}")


if __name__ == "__main__":
    main()