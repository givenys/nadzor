import cv2
from ultralytics import YOLO
import numpy as np

# Список всех твоих моделей
models_to_test = [
    'yolov8n.pt',
    'yolov8_fire.pt',
]

def test_model(model_path):
    print(f"\n{'='*60}")
    print(f"Тестируем модель: {model_path}")
    print('='*60)
    
    try:
        # Загружаем модель
        model = YOLO(model_path)
        
        # Показываем все классы
        print(f"\n📋 Классы модели ({len(model.names)}):")
        for class_id, class_name in model.names.items():
            print(f"  {class_id}: {class_name}")
        
        # Проверяем, есть ли огонь
        fire_classes = []
        for class_id, class_name in model.names.items():
            if 'fire' in class_name.lower() or 'flame' in class_name.lower() or 'огонь' in class_name.lower():
                fire_classes.append((class_id, class_name))
        
        if fire_classes:
            print(f"\n✅ НАЙДЕНЫ КЛАССЫ ОГНЯ:")
            for class_id, class_name in fire_classes:
                print(f"   - {class_id}: {class_name}")
        else:
            print(f"\nВ этой модели нет классов огня!")
        
        # Тест на изображении (если есть)
        test_image = 'test_fire.jpg'
        
        try:
            # Создаём тестовое изображение (чёрный фон с оранжевым "огнём")
            test_img = np.zeros((480, 640, 3), dtype=np.uint8)
            # Рисуем оранжевый круг (имитация огня)
            cv2.circle(test_img, (320, 240), 100, (0, 100, 255), -1)
            cv2.circle(test_img, (320, 240), 80, (0, 150, 255), -1)
            cv2.circle(test_img, (320, 240), 60, (0, 200, 255), -1)
            
            # Запускаем детекцию
            results = model(test_img, verbose=False)
            
            print(f"\n🔍 Результат детекции на тестовом изображении:")
            if len(results[0].boxes) > 0:
                print(f"   ✅ Найдено объектов: {len(results[0].boxes)}")
                for box in results[0].boxes:
                    class_id = int(box.cls[0])
                    confidence = float(box.conf[0])
                    class_name = model.names[class_id]
                    print(f"   - {class_name}: {confidence:.2%}")
            else:
                print(f"   ❌ Ничего не найдено")
                
        except Exception as e:
            print(f"   ⚠️ Ошибка при тестировании: {e}")
        
        return len(fire_classes) > 0
        
    except Exception as e:
        print(f"\n❌ Ошибка загрузки модели: {e}")
        return False

if __name__ == "__main__":
    print("🔥 ТЕСТ МОДЕЛЕЙ DETECTION ОГНЯ")
    print("="*60)
    
    fire_models = []
    
    for model_path in models_to_test:
        has_fire = test_model(model_path)
        if has_fire:
            fire_models.append(model_path)
    
    print(f"\n{'='*60}")
    print(f"📊 ИТОГИ:")
    print('='*60)
    
    if fire_models:
        print(f"✅ Модели с детекцией огня:")
        for m in fire_models:
            print(f"   - {m}")
        print(f"\nИспользуй эти модели в твоём проекте!")
    else:
        print(f"НИ ОДНА модель не содержит классов огня!")