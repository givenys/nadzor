"""
Глобальные константы и настройки системы распознавания лиц.
Эти параметры редко меняются и задают базовое поведение системы.
"""
import os

# --- ПУТИ И ДИРЕКТОРИИ ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REFERENCE_FOLDER = os.path.join(BASE_DIR, "data", "reference_faces")
OUTPUT_FOLDER = os.path.join(BASE_DIR, "data", "output")

# --- СЕТЕВЫЕ КОНСТАНТЫ ---
NODE_JS_WS_URL = os.getenv("NODE_JS_WS_URL", "ws://localhost:3001/api/cams/upload")
NODE_JS_API_URL = os.getenv("NODE_JS_API_URL", "http://localhost:3001")
DEVICE_ID = os.getenv("DEVICE_ID", "81826630-e466-441d-9f92-351d6c3fe423")
API_KEY = os.getenv("API_KEY", "my-secret-camera-key-2026")

# --- ПАРАМЕТРЫ ОТПРАВКИ КАДРОВ --- 
SEND_EVERY_N_FRAME = 3
JPEG_QUALITY = 75

# --- ПАРАМЕТРЫ АЛЕРТОВ ---
FIRE_EVENT_TYPE_ID = "e5a5b71d-9356-4662-a77c-87faf69cde0d"
ALERT_COOLDOWN = 5 

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
DEFAULT_MODEL_NAME = ""#"ArcFace (InsightFace)"
INSIGHTFACE_DET_SIZE = (320, 320)

# --- ЛОГИРОВАНИЕ ---
LOG_LEVEL = "INFO"
LOG_FORMAT = "[%(levelname)s] %(name)s: %(message)s"

# --- ПРОЧЕЕ ---
SUPPORTED_IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.bmp')
