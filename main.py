"""
Face Recognition System - Streaming to Node.js Backend
Только стриминг в браузер, без локальных окон OpenCV.
"""
import sys
import os
import cv2
import requests
import logging
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
SHOW_LOCAL_WINDOW = False  # False, чтобы не открывать окно

def main():
    logger = setup_logging(level="INFO")
    logger.info(" Запуск стриминга на Node.js (без локального UI)...")
    logger.info(f"📡 URL: {NODE_JS_URL}")
    logger.info(f"📷 Device ID: {DEVICE_ID}")
    
    config = DynamicConfig()
    system = FaceRecognitionSystem(config, enable_yolo=True, yolo_conf_threshold=0.4, fire_conf_threshold=0.5)
    
    frame_count = 0
    send_counter = 0
    frames_sent = 0
    frames_failed = 0
    
    try:
        with video_capture_context(0, 640, 480) as cap:
            logger.info("✅ Камера открыта")
            fps_calc = FPSCalculator()
            last_data = []
            
            logger.info(" Стриминг запущен. Ctrl+C для остановки.")
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    logger.error("❌ Не удалось получить кадр")
                    break
                
                fps = fps_calc.update()
                
                # AI-обработка
                if frame_count % config.frame_skip == 0:
                    last_data = system.recognize_faces(frame)
                    yolo_objects = system.detect_yolo_objects(frame)
                
                # Отрисовка рамок
                frame = system.draw_results(frame, last_data, yolo_objects)
                
                # Отправка на Node.js
                send_counter += 1
                if send_counter % SEND_EVERY_N_FRAME == 0:
                    try:
                        _, buffer = cv2.imencode('.jpg', frame, 
                            [int(cv2.IMWRITE_JPEG_QUALITY), 80])
                        
                        response = requests.post(
                            NODE_JS_URL,
                            data=buffer.tobytes(),
                            headers={
                                'Content-Type': 'image/jpeg',
                                'X-Device-ID': DEVICE_ID,
                                'X-API-Key': API_KEY
                            },
                            timeout=2
                        )
                        
                        if response.status_code == 200:
                            frames_sent += 1
                        else:
                            frames_failed += 1
                            logger.warning(f"️ Server status: {response.status_code}")
                    
                    except requests.exceptions.RequestException as e:
                        frames_failed += 1
                        if frames_failed % 10 == 0:
                            logger.debug(f"📡 Network error: {e}")
                    
                    send_counter = 0
                
                # Логируем статистику раз в 5 секунд
                if frame_count % 150 == 0:
                    logger.info(f" Sent: {frames_sent} | Failed: {frames_failed} | FPS: {fps:.1f}")
                
                frame_count += 1
                
                # Если включено локальное окно (для отладки)
                if SHOW_LOCAL_WINDOW:
                    cv2.imshow("Stream", frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
    
    except KeyboardInterrupt:
        logger.info("⏹ Остановлено пользователем")
    except RuntimeError as e:
        logger.error(f"❌ Критическая ошибка: {e}")
    finally:
        logger.info(f"📊 Итоги: Отправлено: {frames_sent}, Ошибок: {frames_failed}")
        if SHOW_LOCAL_WINDOW:
            cv2.destroyAllWindows()

if __name__ == "__main__":
    main()