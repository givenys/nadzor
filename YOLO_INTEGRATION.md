# Интеграция YOLOv8 в систему распознавания лиц

## Обзор

В проект была интегрирована поддержка детекции объектов COCO с помощью модели YOLOv8. Теперь система одновременно:
- **Распознаёт лица** с помощью InsightFace (ArcFace)
- **Детектирует объекты** (80 классов COCO) с помощью YOLOv8

## Структура модуля YOLO

```
face-recognition/
├── core/
│   ├── yolo/
│   │   ├── __init__.py          # Экспорт YOLODetector
│   │   └── yolo_detector.py     # Основной класс детектора
│   └── face_system.py           # Обновлён для поддержки YOLO
├── main.py                       # Точка входа с включённым YOLO
└── requirements.txt              # Добавлена зависимость ultralytics
```

## Установка зависимостей

```bash
pip install -r requirements.txt
```

Или вручную:
```bash
pip install ultralytics>=8.0.0
```

## Использование

### Базовое использование

```python
from core.face_system import FaceRecognitionSystem
from config.dynamic import DynamicConfig

config = DynamicConfig()

# Включение YOLO при инициализации
system = FaceRecognitionSystem(
    config, 
    enable_yolo=True,           # Включить детекцию объектов
    yolo_conf_threshold=0.4     # Порог уверенности для YOLO
)
```

### Детекция объектов

```python
# Получить список обнаруженных объектов
yolo_objects = system.detect_yolo_objects(frame)

# Каждый объект содержит:
# {
#     'class_id': 0,                    # ID класса COCO
#     'class_name': 'person',           # Название класса
#     'confidence': 0.95,               # Уверенность детекции
#     'bbox': (x1, y1, x2, y2),         # Bounding box
#     'color': (255, 128, 0),           # Цвет для отрисовки
#     'label': 'person 0.95'            # Текст метки
# }
```

### Отрисовка результатов

```python
# Отрисовка лиц + объектов YOLO на кадре
frame = system.draw_results(frame, face_data, yolo_objects)
```

## Настройка порога уверенности

```python
# Изменение порога во время работы
if system.yolo_detector:
    system.yolo_detector.set_confidence_threshold(0.6)
```

## Классы COCO (80 категорий)

YOLOv8 поддерживает следующие классы:
- person, bicycle, car, motorcycle, airplane, bus, train, truck, boat
- traffic light, fire hydrant, stop sign, parking meter, bench, bird, cat, dog
- horse, sheep, cow, elephant, bear, zebra, giraffe, backpack, umbrella
- handbag, tie, suitcase, frisbee, skis, snowboard, sports ball, kite
- baseball bat, baseball glove, skateboard, surfboard, tennis racket, bottle
- wine glass, cup, fork, knife, spoon, bowl, banana, apple, sandwich, orange
- broccoli, carrot, hot dog, pizza, donut, cake, chair, couch, potted plant
- bed, dining table, toilet, tv, laptop, mouse, remote, keyboard, cell phone
- microwave, oven, toaster, sink, refrigerator, book, clock, vase, scissors
- teddy bear, hair drier, toothbrush

## Производительность

- **Модель**: YOLOv8n (nano) - самая быстрая из семейства YOLOv8
- **Режим**: CPU (может быть медленным без GPU)
- **Оптимизация**: Детекция выполняется только каждый N-й кадр (параметр `frame_skip`)

## Отключение YOLO

Если нужна только детекция лиц:

```python
system = FaceRecognitionSystem(config, enable_yolo=False)
```

## Возможные ошибки

### "ultralytics не установлен"
```bash
pip install ultralytics
```

### "No space left on device"
Очистите кэш pip:
```bash
pip cache purge
```

### Медленная работа на CPU
- Увеличьте `frame_skip` в настройках
- Используйте модель меньшего размера (yolov8n уже самая маленькая)
- Рассмотрите возможность использования GPU версии

## Пример работы

При запуске `main.py`:
1. Открывается веб-камера
2. Распознаются лица (зелёная рамка - знакомое, красная - неизвестное)
3. Детектируются объекты COCO (разноцветные рамки)
4. В левом верхнем углу отображается статистика:
   ```
   Faces: 2 | Objects: 5 | Model: ArcFace (InsightFace)
   ```

## Архитектурные изменения

### `core/yolo/yolo_detector.py`
Класс `YOLODetector` предоставляет:
- Инициализацию модели YOLOv8
- Детекцию объектов на кадре
- Отрисовку bounding box с подписями
- Управление порогом уверенности

### `core/face_system.py`
Добавлено:
- Параметр `enable_yolo` в конструкторе
- Атрибут `self.yolo_detector`
- Метод `detect_yolo_objects()`
- Поддержка `yolo_objects` в методе `draw_results()`

### `main.py`
Изменения:
- Инициализация системы с `enable_yolo=True`
- Вызов `system.detect_yolo_objects(frame)` в цикле обработки
- Передача объектов YOLO в `draw_results()`

### `requirements.txt`
Добавлена зависимость:
```
ultralytics>=8.0.0
```

## Будущие улучшения

- [ ] Добавить настройку порога YOLO через UI
- [ ] Поддержка кастомных моделей YOLO
- [ ] Фильтрация классов (детектировать только нужные)
- [ ] Трекинг объектов между кадрами
- [ ] Оптимизация для GPU (CUDA)
