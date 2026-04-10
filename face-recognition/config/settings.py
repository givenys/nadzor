"""
Глобальные константы и настройки системы распознавания лиц.
Эти параметры редко меняются и задают базовое поведение системы.
"""
import os

# --- ПУТИ И ДИРЕКТОРИИ ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REFERENCE_FOLDER = os.path.join(BASE_DIR, "data", "reference_faces")
OUTPUT_FOLDER = os.path.join(BASE_DIR, "data", "output")

# --- КАМЕРА ---
WEBCAM_ID = 0
DEFAULT_CAM_WIDTH = 640
DEFAULT_CAM_HEIGHT = 480

# --- ОКНА ---
WINDOW_NAME = "Video Feed"
CONTROLS_WINDOW_NAME = "Controls"
WINDOW_WIDTH = 640
WINDOW_HEIGHT = 480
CONTROLS_WINDOW_WIDTH = 320
CONTROLS_WINDOW_HEIGHT = 220
CONTROLS_WINDOW_OFFSET_X = 20

# --- МОДЕЛИ ---
DEFAULT_MODEL_NAME = "ArcFace (InsightFace)"
INSIGHTFACE_DET_SIZE = (320, 320)  # Баланс скорость/точность

# --- ЛОГИРОВАНИЕ ---
LOG_LEVEL = "INFO"
LOG_FORMAT = "[%(levelname)s] %(name)s: %(message)s"

# --- ПРОЧЕЕ ---
SUPPORTED_IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.bmp')
