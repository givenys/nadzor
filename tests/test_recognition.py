"""
Тесты для системы распознавания лиц.
"""
import pytest
import numpy as np
import sys
import os

# Добавляем корневую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestLowLightEnhancer:
    """Тесты для класса LowLightEnhancer"""
    
    def test_enhancer_creation(self):
        """Проверка создания энхансера"""
        from core.enhancer import LowLightEnhancer
        
        enhancer = LowLightEnhancer()
        assert enhancer is not None
        assert enhancer.brightness_threshold == 70
        assert enhancer.gamma_dark == 1.8
    
    def test_brightness_measurement(self):
        """Проверка измерения яркости"""
        from core.enhancer import LowLightEnhancer
        
        enhancer = LowLightEnhancer()
        
        # Чёрный кадр (яркость ~0)
        black_frame = np.zeros((100, 100, 3), dtype=np.uint8)
        brightness_black = enhancer._measure_brightness(black_frame)
        assert brightness_black < 10
        
        # Белый кадр (яркость ~255)
        white_frame = np.full((100, 100, 3), 255, dtype=np.uint8)
        brightness_white = enhancer._measure_brightness(white_frame)
        assert brightness_white > 240
    
    def test_gamma_correction(self):
        """Проверка gamma-коррекции"""
        from core.enhancer import LowLightEnhancer
        
        enhancer = LowLightEnhancer()
        frame = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        
        # Gamma=1.0 не должна менять кадр
        corrected = enhancer._gamma_correct(frame, 1.0)
        assert np.array_equal(frame, corrected)
        
        # Gamma>1.0 должна осветлять
        corrected_bright = enhancer._gamma_correct(frame, 2.0)
        assert np.mean(corrected_bright) > np.mean(frame)


class TestFaceData:
    """Тесты для структуры FaceData"""
    
    def test_face_data_creation(self):
        """Проверка создания FaceData"""
        from core.face_system import FaceData
        
        face = FaceData(
            name="Test",
            bbox=(10, 20, 100, 150),
            color=(0, 255, 0),
            confidence=0.95
        )
        
        assert face.name == "Test"
        assert face.bbox == (10, 20, 100, 150)
        assert face.color == (0, 255, 0)
        assert face.confidence == 0.95


class TestVideoUtils:
    """Тесты для видео утилит"""
    
    def test_fps_calculator(self):
        """Проверка калькулятора FPS"""
        from utils.video import FPSCalculator
        import time
        
        calc = FPSCalculator()
        
        # Первый вызов должен вернуть 0
        fps1 = calc.update()
        assert fps1 == 0.0
        
        # Ждём немного и обновляем
        time.sleep(0.1)
        fps2 = calc.update()
        assert fps2 > 0.0
        assert fps2 < 20.0  # Разумный предел


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
