import React, { useState, useEffect } from 'react';
import '../styles/Cams.css';

export default function VideoDashboard() {
  const [cameras, setCameras] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expandedId, setExpandedId] = useState(null);

  useEffect(() => {
    let interval; // Выносим переменную, чтобы иметь к ней доступ

    const fetchCams = () => {
        fetch('/api/cams', { credentials: 'include' })
        .then(res => {
            if (res.status === 401) {
                clearInterval(interval);
                console.warn('Ошибка 401: Нет доступа. Опрос камер остановлен.');
                // window.location.href = '/login';
                throw new Error('Unauthorized');
            }
            
            if (!res.ok) throw new Error('Failed to load cameras');
            return res.json();
        })
        .then(data => {
            const cams = data.map(c => ({
                id: c.id,
                name: c.device_name || `Камера ${c.id}`,
                employee_name: c.employee_name || 'Не назначен',
                is_online: c.is_online,
                streamUrl: `/api/cams/${c.id}/stream`
            }));
            setCameras(cams);
            setLoading(false);
        })
        .catch(err => {
            if (err.message !== 'Unauthorized') {
                console.error('Failed to load cams:', err);
            }
            setLoading(false);
        });
    };

    fetchCams();
    interval = setInterval(fetchCams, 3000);
    
    return () => clearInterval(interval);
}, []);

  const toggleFocus = (id) => setExpandedId(expandedId === id ? null : id);

  const mainCamera = expandedId ? cameras.find(c => c.id === expandedId) : null;
  const sideCameras = expandedId ? cameras.filter(c => c.id !== expandedId) : cameras;

  // Компонент одной камеры
  const CameraCard = ({ camera, isMain = false }) => {
    const isOffline = !camera.is_online;
    const streamUrl = `${camera.streamUrl}?t=${Date.now()}`;

    return (
      <div
        onClick={() => !isMain && toggleFocus(camera.id)}
        className={`camera-card ${isOffline ? 'camera-card-offline' : ''} ${
          expandedId && !isMain ? 'camera-card-small' : ''
        }`}
      >
        {isOffline ? (
          <div className="offline-placeholder">
            <div className="offline-icon">📡</div>
            <div className="offline-text">Нет связи</div>
          </div>
        ) : (
          <img
            src={streamUrl}
            alt={`Camera ${camera.id}`}
            className={`video-stream ${isMain ? '' : 'video-preview'}`}
          />
        )}

        {!isOffline && (
          <div className="camera-info">
            <span className="status-dot status-dot-normal"></span>
            <span className="camera-name">
              {camera.name}: {camera.employee_name}
            </span>
          </div>
        )}

        {!isOffline && !isMain && (
          <div className="expand-overlay">
            <span className="expand-icon">🔍</span>
          </div>
        )}
      </div>
    );
  };

  if (loading) {
    return (
      <div className="dashboard">
        <div className="loading">Загрузка камер...</div>
      </div>
    );
  }

  if (cameras.length === 0) {
    return (
      <div className="dashboard">
        <div className="loading">Нет доступных камер</div>
      </div>
    );
  }

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1 className="title">Панель оператора</h1>
        <div className="status-legend">
          <div className="legend-item">
            <span className="status-indicator status-normal"></span>
            Норма
          </div>
          <div className="legend-item">
            <span className="status-indicator status-offline"></span>
            Нет связи
          </div>
        </div>
      </header>

      <div className={`camera-grid ${expandedId ? 'camera-grid-expanded' : ''}`}>
        {mainCamera && (
          <div className="main-video-container">
            <CameraCard camera={mainCamera} isMain={true} />
            <div className="video-controls">
              <button onClick={() => setExpandedId(null)} className="control-btn">
                Свернуть
              </button>
            </div>
          </div>
        )}

        {sideCameras.map((camera) => (
          <CameraCard key={camera.id} camera={camera} />
        ))}
      </div>
    </div>
  );
}