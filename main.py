import sys
import os
import cv2
import logging
import time
import threading
import websocket
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.dynamic import DynamicConfig
from config.settings import NODE_JS_WS_URL, DEVICE_ID, API_KEY, SEND_EVERY_N_FRAME, JPEG_QUALITY
from core.face_system import FaceRecognitionSystem
from core.alert_sender import AlertSender
from utils.video import video_capture_context, FPSCalculator
from utils.logging_config import setup_logging

logger = logging.getLogger(__name__)


class WebSocketFrameSender:
    def __init__(self, ws_url, device_id, api_key, jpeg_quality=75):
        self.device_id = device_id
        self.api_key = api_key
        self.jpeg_quality = jpeg_quality
        
        self.ws_url = f"{ws_url}?device_id={device_id}&api_key={api_key}"
        self.ws = None
        self.running = True
        
        self.latest_frame = None
        self.condition = threading.Condition()
        
        self.dropped_frames = 0
        self.sent_frames = 0
        
        self.thread = threading.Thread(target=self._worker, daemon=True)
        self.thread.start()

    def _connect(self):
        try:
            self.ws = websocket.create_connection(
                self.ws_url,
                header=[f"X-Device-ID: {self.device_id}", f"X-API-Key: {self.api_key}"],
                timeout=5.0
            )
            self.ws.settimeout(1.0)
            logger.info("WebSocket connected to Node.js")
            return True
        except Exception as e:
            logger.warning(f"WebSocket connection failed: {e}")
            self.ws = None
            return False

    def _worker(self):
        while self.running:
            with self.condition:
                while self.latest_frame is None and self.running:
                    self.condition.wait(timeout=1.0)
                
                if not self.running:
                    break

                frame_to_send = self.latest_frame
                self.latest_frame = None

            if frame_to_send is None:
                continue

            if self.ws is None:
                if not self._connect():
                    time.sleep(1)
                    continue

            ret, buffer = cv2.imencode('.jpg', frame_to_send, [int(cv2.IMWRITE_JPEG_QUALITY), self.jpeg_quality])
            if not ret:
                continue

            try:
                self.ws.send_binary(buffer.tobytes())
                self.sent_frames += 1
            except Exception as e:
                logger.warning(f"Send error: {e}. Reconnecting...")
                try: self.ws.close()
                except: pass
                self.ws = None

    def send_frame(self, frame):
        with self.condition:
            if self.latest_frame is not None:
                self.dropped_frames += 1
            
            self.latest_frame = frame.copy()
            self.condition.notify()

    def stop(self):
        with self.condition:
            self.running = False
            self.condition.notify()
        self.thread.join()
        if self.ws:
            try: self.ws.close()
            except: pass
        logger.info(f"Sender stopped. Sent: {self.sent_frames} | Skipped (to keep low latency): {self.dropped_frames}")


def check_fire_detected(yolo_objects):
    if not yolo_objects:
        return None
    
    max_confidence = 0.0
    fire_detected = False
    
    for obj in yolo_objects:
        if obj.get('class_id') == 1:
            fire_detected = True
            conf = obj.get('confidence', 0.0)
            if conf > max_confidence:
                max_confidence = conf
    
    if fire_detected:
        return max_confidence
    return None


def main():
    setup_logging()
    config = DynamicConfig()
    system = FaceRecognitionSystem(config)
    sender = WebSocketFrameSender(NODE_JS_WS_URL, DEVICE_ID, API_KEY, JPEG_QUALITY)
    
    alert_sender = AlertSender(DEVICE_ID, API_KEY)

    frames_sent = 0
    frame_count = 0

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

                    fire_confidence = check_fire_detected(last_yolo_objects)
                    if fire_confidence is not None:
                        alert_sender.send_fire_alert(fire_confidence)

                frame = system.draw_results(frame, last_data, last_yolo_objects)

                if frame_count % SEND_EVERY_N_FRAME == 0:
                    sender.send_frame(frame)
                    frames_sent += 1

                frame_count += 1

                if frame_count % 150 == 0:
                    logger.info(f"Frames: {frame_count} | FPS: {fps:.1f} | Sent: {frames_sent} | Dropped: {sender.dropped_frames}")

    except KeyboardInterrupt:
        logger.info("Остановлено пользователем")
    finally:
        sender.stop()
        logger.info(f"Итоги: Отправлено ~{frames_sent}")


if __name__ == "__main__":
    main()