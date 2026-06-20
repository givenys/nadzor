"""
Face Recognition System - WebSocket API Server
Сервер для потоковой обработки видео через веб-интерфейс.
"""
import sys
import os
import cv2
import base64
import numpy as np
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

# Добавляем корень проекта в путь для импортов
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.dynamic import DynamicConfig
from core.face_system import FaceRecognitionSystem
from utils.video import FPSCalculator
from utils.logging_config import setup_logging

logger = setup_logging(level="INFO")

# Глобальная переменная для системы распознавания
system = None
fps_calc = FPSCalculator()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Инициализация моделей при запуске сервера"""
    global system
    logger.info("Инициализация моделей ИИ при запуске сервера...")
    config = DynamicConfig()
    # enable_yolo=True включает детекцию объектов YOLOv8
    system = FaceRecognitionSystem(config, enable_yolo=True, yolo_conf_threshold=0.4)
    logger.info("Модели загружены и готовы к работе!")
    yield
    logger.info("Сервер остановлен, освобождение ресурсов...")

app = FastAPI(lifespan=lifespan)

@app.websocket("/ws/video-stream")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("📱 Клиент (браузер/телефон) подключился к видеопотоку")
    
    try:
        while True:
            # 1. Получаем кадр от React (в формате: "data:image/jpeg;base64,/9j/4...")
            data = await websocket.receive_text()
            
            # 2. Декодируем base64 в numpy array (формат OpenCV BGR)
            try:
                header, encoded = data.split(",", 1)
                nparr = np.frombuffer(base64.b64decode(encoded), np.uint8)
                frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            except Exception as e:
                logger.warning(f"Ошибка декодирования кадра: {e}")
                continue
            
            if frame is None:
                continue

            # 3. ТВОЯ ЛОГИКА ИЗ MAIN.PY (адаптированная под веб)
            # Примечание: параметры теперь берутся из DynamicConfig по умолчанию,
            # так как UI-ползунков в вебе пока нет.
            last_data = system.recognize_faces(frame)
            yolo_objects = system.detect_yolo_objects(frame)
            
            # Отрисовка результатов (лица + объекты YOLO)
            frame = system.draw_results(frame, last_data, yolo_objects)

            # 4. Кодируем обработанный кадр обратно в JPEG -> Base64
            # quality=70 - оптимальный баланс между скоростью передачи и качеством для ИИ
            _, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 70])
            jpg_as_text = base64.b64encode(buffer).decode('utf-8')
            
            # 5. Отправляем обработанный кадр обратно клиенту
            await websocket.send_text(f"data:image/jpeg;base64,{jpg_as_text}")
            
            # 6. Логирование производительности (каждые 30 кадров)
            fps = fps_calc.update()
            if fps_calc.curr_time % 2.0 < 0.1:  # Примерно раз в 2 секунды
                logger.debug(f"Server FPS: {fps:.1f}")
            
    except WebSocketDisconnect:
        logger.info("Клиент отключился")
    except Exception as e:
        logger.error(f"Критическая ошибка при обработке кадра: {e}")

if __name__ == "__main__":
    import uvicorn
    # Запуск сервера на всех интерфейсах (0.0.0.0), порт 8000
    logger.info("Запуск WebSocket сервера на порту 8000...")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")