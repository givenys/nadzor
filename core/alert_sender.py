"""
Alert Sender Module
Модуль для отправки алертов на сервер.
"""
import time
import requests
import json
import logging
from typing import Optional
from config.settings import NODE_JS_API_URL, DEVICE_ID, API_KEY, FIRE_EVENT_TYPE_ID, ALERT_COOLDOWN

logger = logging.getLogger(__name__)


class AlertSender:
    """
    Класс для отправки алертов о обнаруженных угрозах на сервер.
    Поддерживает кулдаун между отправками одного типа алерта.
    """
    
    def __init__(self, device_id: str = DEVICE_ID, api_key: str = API_KEY):
        """
        Инициализация отправщика алертов.
        
        Args:
            device_id: ID устройства (камеры)
            api_key: API ключ для авторизации
        """
        self.device_id = device_id
        self.api_key = api_key
        self.api_url = NODE_JS_API_URL
        
        # Отслеживание времени последней отправки алертов
        self.last_alert_times = {}
        
        logger.info(f"AlertSender инициализирован для устройства {device_id}")
    
    def can_send_alert(self, alert_type: str, cooldown: int = ALERT_COOLDOWN) -> bool:
        """
        Проверяет, можно ли отправить алерт данного типа (с учётом кулдауна).
        
        Args:
            alert_type: Тип алерта (например, "fire")
            cooldown: Время кулдауна в секундах
            
        Returns:
            True если можно отправить, False если ещё рано
        """
        current_time = time.time()
        last_time = self.last_alert_times.get(alert_type, 0)
        
        return (current_time - last_time) >= cooldown
    
    def update_last_alert_time(self, alert_type: str):
        """
        Обновляет время последней отправки алерта.
        
        Args:
            alert_type: Тип алерта
        """
        self.last_alert_times[alert_type] = time.time()
    
    def send_fire_alert(self, confidence: float) -> bool:
        """
        Отправляет алерт о пожаре на сервер.
        
        Args:
            confidence: Уверенность детекции огня (0.0 - 1.0)
            
        Returns:
            True если алерт успешно отправлен, False в противном случае
        """
        alert_type = "fire"
        
        # Проверяем кулдаун
        if not self.can_send_alert(alert_type):
            logger.debug(f"Fire alert skipped (cooldown)")
            return False
        
        try:
            payload = {
                "device_id": self.device_id,
                "event_type_id": FIRE_EVENT_TYPE_ID,
                "status": "open",
                "title": "Fire detected",
                "description": json.dumps({
                    "device_id": self.device_id,
                    "confidence": confidence
                })
            }
            
            response = requests.post(
                f"{self.api_url}/api/cams/incidents",
                json=payload,
                headers={
                    "X-API-Key": self.api_key,
                    "Content-Type": "application/json"
                },
                timeout=5
            )
            
            if response.status_code == 201:
                self.update_last_alert_time(alert_type)
                logger.info(f"Fire alert sent successfully (confidence: {confidence:.2f})")
                return True
            else:
                logger.warning(f"Failed to send fire alert: {response.status_code} - {response.text}")
                return False
                
        except requests.exceptions.Timeout:
            logger.error("Timeout while sending fire alert")
            return False
        except requests.exceptions.RequestException as e:
            logger.error(f"Error sending fire alert: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending fire alert: {e}")
            return False
    
    def send_custom_alert(self, event_type_id: str, title: str, description: dict, 
                         cooldown: int = ALERT_COOLDOWN) -> bool:
        """
        Отправляет произвольный алерт на сервер.
        
        Args:
            event_type_id: ID типа события из БД
            title: Заголовок алерта
            description: Описание в формате dict (будет конвертировано в JSON)
            cooldown: Время кулдауна в секундах
            
        Returns:
            True если алерт успешно отправлен
        """
        alert_type = event_type_id
        
        if not self.can_send_alert(alert_type, cooldown):
            logger.debug(f"Alert {alert_type} skipped (cooldown)")
            return False
        
        try:
            payload = {
                "device_id": self.device_id,
                "event_type_id": event_type_id,
                "status": "open",
                "title": title,
                "description": json.dumps(description)
            }
            
            response = requests.post(
                f"{self.api_url}/api/cams/incidents",
                json=payload,
                headers={
                    "X-API-Key": self.api_key,
                    "Content-Type": "application/json"
                },
                timeout=5
            )
            
            if response.status_code == 201:
                self.update_last_alert_time(alert_type)
                logger.info(f"Alert sent: {title}")
                return True
            else:
                logger.warning(f"Failed to send alert: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending alert: {e}")
            return False