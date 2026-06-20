import React, { useRef, useEffect, useState } from 'react';

const VideoStream = () => {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const [processedImage, setProcessedImage] = useState('');
  const wsRef = useRef(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [status, setStatus] = useState('Ожидание...');

  // Подключение к WebSocket при монтировании компонента
  useEffect(() => {
    // ЗАМЕНИ 'yourdomain.com' на реальный IP или домен твоего Ubuntu-сервера
    // Если тестируешь локально, используй 'ws://localhost:8000/ws/video-stream'
    const wsUrl = 'ws://yourdomain.com/ws/video-stream'; 
    wsRef.current = new WebSocket(wsUrl);

    wsRef.current.onopen = () => {
      setStatus('Подключено к серверу. Нажмите "Запустить ИИ"');
    };

    wsRef.current.onmessage = (event) => {
      // Получили обработанный кадр от Python
      setProcessedImage(event.data);
    };

    wsRef.current.onerror = (error) => {
      setStatus('Ошибка подключения к серверу. Проверьте адрес и HTTPS.');
      console.error('WebSocket error:', error);
    };

    wsRef.current.onclose = () => {
      setStatus('Соединение разорвано');
    };

    return () => {
      if (wsRef.current) wsRef.current.close();
    };
  }, []);

  // Захват камеры и отправка кадров
  useEffect(() => {
    if (!isStreaming) return;

    let animationFrameId;
    let lastSentTime = 0;
    const FPS_LIMIT = 15; // Ограничиваем до 15 FPS, чтобы не перегружать сервер и сеть
    const frameInterval = 1000 / FPS_LIMIT;

    const captureAndSend = (timestamp) => {
      if (timestamp - lastSentTime > frameInterval) {
        const video = videoRef.current;
        const canvas = canvasRef.current;
        if (!video || !canvas) return;

        const ctx = canvas.getContext('2d');
        // Рисуем текущий кадр видео на canvas (можно уменьшить разрешение для скорости, например 640x480)
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        
        // Конвертируем в base64 с сжатием 0.6 (60% качества) для экономии трафика
        const base64Frame = canvas.toDataURL('image/jpeg', 0.6);

        // Отправляем на сервер, если соединение открыто
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
          wsRef.current.send(base64Frame);
        }
        lastSentTime = timestamp;
      }
      animationFrameId = requestAnimationFrame(captureAndSend);
    };

    // Запрос доступа к камере
    navigator.mediaDevices.getUserMedia({ 
      video: { width: 640, height: 480, facingMode: "environment" } // "environment" = задняя камера телефона
    })
      .then((stream) => {
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          setStatus('Камера активна, отправка кадров...');
          animationFrameId = requestAnimationFrame(captureAndSend);
        }
      })
      .catch((err) => {
        setStatus(`Ошибка доступа к камере: ${err.message}. Убедитесь, что сайт использует HTTPS.`);
        setIsStreaming(false);
      });

    return () => {
      cancelAnimationFrame(animationFrameId);
      // Останавливаем камеру
      if (videoRef.current && videoRef.current.srcObject) {
        videoRef.current.srcObject.getTracks().forEach(track => track.stop());
      }
    };
  }, [isStreaming]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '20px', padding: '20px' }}>
      <h2>Система распознавания (Real-time)</h2>
      <p style={{ color: isStreaming ? 'green' : 'red' }}>{status}</p>
      
      {/* Скрытые элементы для захвата */}
      <video ref={videoRef} autoPlay playsInline muted style={{ display: 'none' }} />
      <canvas ref={canvasRef} width="640" height="480" style={{ display: 'none' }} />
      
      <button 
        onClick={() => setIsStreaming(!isStreaming)}
        style={{ padding: '15px 30px', fontSize: '18px', backgroundColor: isStreaming ? '#ff4444' : '#44ff44', border: 'none', borderRadius: '8px', cursor: 'pointer', color: '#000', fontWeight: 'bold' }}
      >
        {isStreaming ? '⏹ Остановить' : '▶ Запустить ИИ'}
      </button>
      
      <div style={{ border: '2px solid #333', borderRadius: '8px', overflow: 'hidden' }}>
        {processedImage ? (
          <img src={processedImage} alt="AI Processed" style={{ display: 'block', maxWidth: '100%', height: 'auto' }} />
        ) : (
          <div style={{ width: '640px', height: '480px', background: '#222', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            {isStreaming ? 'Обработка первого кадра...' : 'Поток остановлен'}
          </div>
        )}
      </div>
    </div>
  );
};

export default VideoStream;
