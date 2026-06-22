import sys
import os
import cv2
import logging
import time
import queue
import threading
import io
import websocket
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.dynamic import DynamicConfig
from core.face_system import FaceRecognitionSystem
from utils.video import video_capture_context, FPSCalculator
from utils.logging_config import setup_logging

NODE_JS_WS_URL = "ws://localhost:3001/api/cams/upload" 
DEVICE_ID = "81826630-e466-441d-9f92-351d6c3fe423"
API_KEY = "my-secret-camera-key-2026"
SEND_EVERY_N_FRAME = 3
JPEG_QUALITY = 75 

logger = logging.getLogger(__name__)

class WebSocketFrameSender:
    def __init__(self, ws_url, device_id, api_key, jpeg_quality=75, max_queue_size=2):
        self.device_id = device_id
        self.api_key = api_key
        self.jpeg_quality = jpeg_quality
        
        self.queue = queue.Queue(maxsize=max_queue_size)
        
        self.ws_url = f"{ws_url}?device_id={device_id}&api_key={api_key}"
        self.ws = None
        
        # Запускаем фоновый поток для отправки
        self.thread = threading.Thread(target=self._worker, daemon=True)
        self.thread.start()

    def _connect(self):
        try:
            self.ws = websocket.create_connection(
                self.ws_url,
                header=[
                    f"X-Device-ID: {self.device_id}",
                    f"X-API-Key: {self.api_key}"
                ],
                timeout=5
            )
            logger.info("WebSocket connected to Node.js")
        except Exception as e:
            logger.warning(f"WebSocket connection failed: {e}")
            self.ws = None

    def _worker(self):
        while True:
            frame = self.queue.get()
            if frame is None:
                break
            
            if self.ws is None:
                self._connect()
                if self.ws is None:
                    self.queue.task_done()
                    time.sleep(1)
                    continue

            try:
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(rgb_frame)
                buffer = io.BytesIO()
                img.save(buffer, format="JPEG", quality=self.jpeg_quality)
                jpeg_bytes = buffer.getvalue()
                
                self.ws.send_binary(jpeg_bytes)
                
            except websocket.WebSocketException as e:
                logger.warning(f"WebSocket send error: {e}. Reconnecting...")
                try: self.ws.close()
                except: pass
                self.ws = None
            except Exception as e:
                logger.error(f"Unexpected error in sender: {e}", exc_info=True)
                self.ws = None
            finally:
                self.queue.task_done()

    def send(self, frame):
        try:
            self.queue.put_nowait(frame)
            return True
        except queue.Full:
            return False
        
def main():
    setup_logging()
    config = DynamicConfig()
    system = FaceRecognitionSystem(config)

    sender = WebSocketFrameSender(NODE_JS_WS_URL, DEVICE_ID, API_KEY, JPEG_QUALITY, max_queue_size=2)

    frames_sent = 0
    frame_count = 0
    send_counter = 0

    try:
        with video_capture_context(0, 640, 480) as cam:
            logger.info("Камера открыта (ThreadedCamera)")
            fps_calc = FPSCalculator()
            last_data = []
            last_yolo_objects = []

            logger.info("Стриминг запущен. Ctrl+C для остановки.")

            while True:
                ret, frame = cam.read()
                if not ret:
                    time.sleep(0.01)
                    continue

                fps = fps_calc.update()

                if frame_count % config.frame_skip == 0:
                    last_data = system.recognize_faces(frame)
                    last_yolo_objects = system.detect_yolo_objects(frame) or []

                frame = system.draw_results(frame, last_data, last_yolo_objects)

                send_counter += 1
                if send_counter % SEND_EVERY_N_FRAME == 0:
                    if sender.send(frame):
                        frames_sent += 1

                frame_count += 1

                if frame_count % 150 == 0:
                    logger.info(f"Frames: {frame_count} | FPS: {fps:.1f} | Sent: {frames_sent}")

    except KeyboardInterrupt:
        logger.info("Остановлено пользователем")
    finally:
        logger.info(f"Итоги: Отправлено ~{frames_sent}")

if __name__ == "__main__":
    main()