"""
Face Recognition System - Main Entry Point
Точка входа с минимальной логикой.
"""
import sys
import os

# Добавляем корень проекта в путь для импортов
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cv2
import logging
from datetime import datetime

from config.settings import (
    WINDOW_NAME, CONTROLS_WINDOW_NAME,
    WINDOW_WIDTH, WINDOW_HEIGHT,
    CONTROLS_WINDOW_WIDTH, CONTROLS_WINDOW_HEIGHT,
    CONTROLS_WINDOW_OFFSET_X
)
from config.dynamic import DynamicConfig
from core.face_system import FaceRecognitionSystem
from utils.video import video_capture_context, FPSCalculator
from utils.ui import create_controls_window, read_control_params, update_enhancer_params
from utils.logging_config import setup_logging


def main():
    """Основная функция запуска системы распознавания лиц"""
    
    # Настройка логирования
    logger = setup_logging(level="INFO")
    logger.info("Запуск системы распознавания лиц...")
    
    # Инициализация конфигурации и системы
    config = DynamicConfig()
    # enable_yolo=True включает детекцию объектов YOLOv8
    system = FaceRecognitionSystem(config, enable_yolo=True, 
                                    yolo_conf_threshold=config.threshold, 
                                    fire_conf_threshold=config.threshold)
    
    try:
        with video_capture_context(0, WINDOW_WIDTH, WINDOW_HEIGHT) as cap:
            # Создание панели управления
            create_controls_window(
                CONTROLS_WINDOW_NAME,
                CONTROLS_WINDOW_WIDTH,
                CONTROLS_WINDOW_HEIGHT,
                CONTROLS_WINDOW_OFFSET_X
            )
            
            logger.info("Нажмите 'q' для выхода. Меняйте параметры в панели 'Controls'")
            
            # Инициализация утилит
            fps_calc = FPSCalculator()
            frame_count = 0
            last_data = []
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    logger.error("Не удалось получить кадр от камеры")
                    break
                
                # Чтение параметров из панели управления
                params = read_control_params(CONTROLS_WINDOW_NAME)
                
                # Обновление конфигурации
                config.threshold = params['threshold']
                config.frame_skip = params['frame_skip']
                config.min_face_area = params['min_face_area']
                
                # Обновление параметров улучшителя освещения
                update_enhancer_params(
                    system.enhancer,
                    params['clahe_clip'],
                    params['gamma_dark'],
                    params['brightness_thresh']
                )
                
                # Перезагрузка базы по триггеру
                if params['reload_base']:
                    system.reload_base()
                    cv2.setTrackbarPos("[RELOAD BASE]", CONTROLS_WINDOW_NAME, 0)
                
                # Расчёт FPS
                fps = fps_calc.update()

                # Обработка с пропуском кадров
                yolo_objects = None
                if frame_count % config.frame_skip == 0:
                    last_data = system.recognize_faces(frame)
                    # Детекция объектов YOLO
                    yolo_objects = system.detect_yolo_objects(frame)

                # Отрисовка результатов (лица + объекты YOLO)
                frame = system.draw_results(frame, last_data, yolo_objects)
                
                # Отображение FPS и времени
                cv2.putText(frame, f"FPS: {fps:.1f}", 
                           (frame.shape[1] - 110, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                timestamp = datetime.now().strftime("%H:%M:%S")
                cv2.putText(frame, timestamp, 
                           (frame.shape[1] - 160, 60),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                # Показ кадра
                cv2.imshow(WINDOW_NAME, frame)
                
                # Выход по 'q'
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                
                frame_count += 1
    
    except RuntimeError as e:
        logging.error(f"Критическая ошибка: {e}")
    finally:
        logging.info("Завершено.")


if __name__ == "__main__":
    main()
