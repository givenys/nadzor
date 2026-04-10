"""
Загрузка и кэширование эмбеддингов лиц.
Векторизация базы для ускорения сравнения.
"""
import os
import cv2
import numpy as np
from typing import List, Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)


def load_reference_faces(app: Any, reference_folder: str, supported_extensions: tuple) -> tuple:
    """
    Загрузка эталонных лиц из папки с векторизацией для ускорения.
    
    Args:
        app: InsightFace App для генерации эмбеддингов
        reference_folder: Путь к папке с эталонными изображениями
        supported_extensions: Кортеж поддерживаемых расширений файлов
        
    Returns:
        Tuple containing:
            - known_embeddings: Список словарей с именами и эмбеддингами
            - known_embeddings_matrix: Матрица эмбеддингов для векторизованного сравнения
            - known_norms: Предвычисленные нормы для ускорения
    """
    if not os.path.exists(reference_folder):
        os.makedirs(reference_folder)
        logger.warning(f"Папка '{reference_folder}' не найдена. Создана пустая.")
        return [], None, None

    known_embeddings: List[Dict] = []
    count = 0
    
    for filename in os.listdir(reference_folder):
        if filename.lower().endswith(supported_extensions):
            name = os.path.splitext(filename)[0]
            img_path = os.path.join(reference_folder, filename)
            
            try:
                img = cv2.imread(img_path)
                if img is None:
                    logger.warning(f"Не удалось прочитать изображение {filename}")
                    continue
                    
                faces = app.get(img)
                if faces and len(faces) > 0:
                    # Берем первое найденное лицо на фото
                    emb = faces[0].embedding
                    known_embeddings.append({'name': name, 'embedding': emb})
                    count += 1
                    logger.debug(f"Лицо {name} добавлено в базу")
                else:
                    logger.warning(f"Лица не найдены на изображении {filename}")
            except Exception as e:
                logger.warning(f"Ошибка загрузки {filename}: {e}")
    
    logger.info(f"Загружено лиц в базу: {count}")
    
    # Векторизация базы для ускорения сравнения (матричные операции вместо цикла)
    known_embeddings_matrix = None
    known_norms = None
    
    if known_embeddings:
        embeddings_list = [k['embedding'] for k in known_embeddings]
        known_embeddings_matrix = np.array(embeddings_list)
        # Предвычисляем нормы один раз при загрузке
        known_norms = np.linalg.norm(known_embeddings_matrix, axis=1, keepdims=True)
        logger.info("База векторизована для ускоренного сравнения")
    
    return known_embeddings, known_embeddings_matrix, known_norms


def warmup_model(app):
    """
    Прогрев модели для ускорения первой итерации.
    
    Args:
        app: InsightFace App для прогрева
    """
    try:
        dummy = np.zeros((100, 100, 3), dtype=np.uint8)
        app.get(dummy)
        logger.debug("Модель прогрета")
    except Exception as e:
        logger.warning(f"Прогрев модели не удался: {e}")
