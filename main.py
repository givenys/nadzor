import sys
import os
import cv2
import requests
import logging
import threading
from queue import Queue, Empty  # ✅ Исправлен импорт
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
SEND_ORIGINAL_EVERY_N = 3
SEND_AI_EVERY_N = 1
SHOW_LOCAL_WINDOW = False

# Очереди для связи между потоками
camera_queue = Queue(maxsize=5)
ai_queue = Queue(maxsize=10)
original_queue = Queue(maxsize=10)
stop_event = threading.Event()

def camera_worker():
    """Поток 1: Читает кадры с камеры и раскладывает по очередям"""
    logger = logging.getLogger(__name__)
    logger.info("📷 Camera worker started")
    
    with video_capture_context(0, 640, 480) as cap:
        logger.info("✅ Камера открыта")
        fps_calc = FPSCalculator()
        frame_count = 0
        
        while not stop_event.is_set():
            ret, frame = cap.read()
            if not ret:
                logger.error("❌ Не удалось получить кадр")
                time.sleep(0.1)  # ✅ Добавлена пауза перед повтором
                continue  # ✅ Продолжаем цикл вместо break
            
            fps = fps_calc.update()
            frame_count += 1
            
            # Отправляем в AI обработку (копия кадра)
            try:
                camera_queue.put_nowait(frame.copy())
            except:
                pass
            
            # Отправляем оригинал на сервер (каждые N кадров)
            if frame_count % SEND_ORIGINAL_EVERY_N == 0:
                try:
                    original_queue.put_nowait(frame.copy())
                except:
                    pass
            
            # Логируем статистику
            if frame_count % 150 == 0:
                logger.info(f"📊 FPS: {fps:.1f} | Camera queue: {camera_queue.qsize()}")
    
    logger.info("📷 Camera worker stopped")

def ai_worker():
    """Поток 2: Делает AI обработку кадров"""
    logger = logging.getLogger(__name__)
    logger.info("🧠 AI worker started")
    
    config = DynamicConfig()
    config.frame_skip = 1
    system = FaceRecognitionSystem(config, enable_yolo=True, 
                                   yolo_conf_threshold=0.4, 
                                   fire_conf_threshold=0.5)
    
    processed_count = 0
    
    while not stop_event.is_set():
        try:
            frame = camera_queue.get(timeout=1)
            
            # AI обработка
            start_time = time.time()
            last_data = system.recognize_faces(frame)
            yolo_objects = system.detect_yolo_objects(frame)
            
            # Отрисовка результатов
            frame_with_ai = system.draw_results(frame, last_data, yolo_objects)
            processing_time = time.time() - start_time
            
            processed_count += 1
            
            # Отправляем обработанный кадр в очередь для отправки
            try:
                _, buffer = cv2.imencode('.jpg', frame_with_ai, 
                                        [int(cv2.IMWRITE_JPEG_QUALITY), 60])
                ai_queue.put_nowait(buffer.tobytes())
            except:
                pass
            
            if processed_count % 10 == 0:
                logger.debug(f"🧠 AI processed {processed_count} frames, time: {processing_time:.3f}s")
            
            camera_queue.task_done()
            
        except Empty:  # ✅ Исправлено: Empty вместо queue.Empty
            continue
        except Exception as e:
            logger.error(f"❌ AI worker error: {e}")
    
    logger.info(f"🧠 AI worker stopped. Processed: {processed_count}")

def sender_worker(frame_queue, queue_name):
    """Поток 3 и 4: Отправляют кадры на сервер"""
    logger = logging.getLogger(__name__)
    logger.info(f"📡 {queue_name} sender started")
    
    sent_count = 0
    failed_count = 0
    
    while not stop_event.is_set():
        try:
            frame_data = frame_queue.get(timeout=1)  # ✅ Переименован параметр
            
            try:
                response = requests.post(
                    NODE_JS_URL,
                    data=frame_data,
                    headers={
                        'Content-Type': 'image/jpeg',
                        'X-Device-ID': DEVICE_ID,
                        'X-API-Key': API_KEY,
                        'X-Source': queue_name
                    },
                    timeout=1
                )
                
                if response.status_code == 200:
                    sent_count += 1
                else:
                    failed_count += 1
                    if failed_count % 10 == 0:
                        logger.warning(f"⚠️ {queue_name} server status: {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                failed_count += 1
                if failed_count % 10 == 0:
                    logger.debug(f"📡 {queue_name} network error")
            
            frame_queue.task_done()
            
        except Empty:  # ✅ Исправлено: Empty вместо queue.Empty
            continue
    
    logger.info(f"📊 {queue_name} stats - Sent: {sent_count}, Failed: {failed_count}")

def main():
    logger = setup_logging(level="INFO")
    logger.info("🚀 Запуск многопоточного стриминга (4 потока)...")
    logger.info(f"📡 URL: {NODE_JS_URL}")
    logger.info(f"📷 Device ID: {DEVICE_ID}")

    # Создаем потоки
    threads = []
    
    # Поток 1: Камера
    camera_thread = threading.Thread(target=camera_worker, name="CameraWorker", daemon=True)
    threads.append(camera_thread)
    
    # Поток 2: AI обработка
    ai_thread = threading.Thread(target=ai_worker, name="AIWorker", daemon=True)
    threads.append(ai_thread)
    
    # Поток 3: Отправка оригиналов
    original_sender = threading.Thread(
        target=sender_worker, 
        args=(original_queue, "Original"), 
        name="OriginalSender", 
        daemon=True
    )
    threads.append(original_sender)
    
    # Поток 4: Отправка AI-обработанных кадров
    ai_sender = threading.Thread(
        target=sender_worker, 
        args=(ai_queue, "AI"), 
        name="AISender", 
        daemon=True
    )
    threads.append(ai_sender)

    # Запускаем все потоки
    for thread in threads:
        thread.start()
        logger.info(f"✅ Started: {thread.name}")

    logger.info("🎥 Стриминг запущен. Ctrl+C для остановки.")

    try:
        # Основной поток ждет
        while not stop_event.is_set():
            time.sleep(1)
            
            # Периодически логируем состояние очередей
            logger.info(f"📊 Queues - Camera: {camera_queue.qsize()}, "
                       f"AI: {ai_queue.qsize()}, "
                       f"Original: {original_queue.qsize()}")
            
    except KeyboardInterrupt:
        logger.info("⏹ Остановлено пользователем")
    
    finally:
        # Останавливаем все потоки
        stop_event.set()
        for thread in threads:
            thread.join(timeout=3)
        
        logger.info("✅ Все потоки остановлены")

if __name__ == "__main__":
    main()