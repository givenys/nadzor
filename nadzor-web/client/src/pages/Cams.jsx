import React, { useState, useEffect } from 'react';
import '../styles/Cams.css';
import { useCameraStream } from '../hooks/useCameraStream';
import { useIncidents } from '../hooks/useIncidents';

// ===== Компонент одного инцидента =====
const IncidentItem = ({ incident, onConfirm, onReject }) => (
  <div className="incident-item">
    <div className="incident-item-info">
      <span className="incident-item-icon">🔥</span>
      <div className="incident-item-text">
        <div className="incident-item-title">{incident.title}</div>
        <div className="incident-item-time">
          {new Date(incident.opened_at).toLocaleTimeString()}
        </div>
      </div>
    </div>
    <div className="incident-buttons">
      <button 
        className="incident-btn confirm"
        onClick={(e) => { e.stopPropagation(); onConfirm(incident.id); }}
      >
        ✓
      </button>
      <button 
        className="incident-btn reject"
        onClick={(e) => { e.stopPropagation(); onReject(incident.id); }}
      >
        ✗
      </button>
    </div>
  </div>
);

// ===== Компонент карточки камеры =====
const CameraCard = ({ camera, isMain = false, expandedId, toggleFocus, incidents, onConfirm, onReject }) => {
  const { status, frameUrl } = useCameraStream(camera.is_online ? camera.id : null);
  const [isIncidentListExpanded, setIsIncidentListExpanded] = useState(false);

  const isOffline = !camera.is_online || (status !== 'connected' && !frameUrl);
  const incidentCount = incidents.length;

  return (
    <div
      onClick={() => !isMain && toggleFocus(camera.id)}
      className={`camera-card ${isOffline ? 'camera-card-offline' : ''} ${
        expandedId && !isMain ? 'camera-card-small' : ''
      }`}
    >
      {isOffline ? (
        <div className="offline-placeholder">
          {/*<div className="offline-icon">📡</div>*/}
          <div className="offline-text">
            {!camera.is_online ? 'Камера отключена' : 
             status === 'connecting' ? 'Подключение...' : 
             'Нет связи'}
          </div>
        </div>
      ) : (
        <>
          {frameUrl ? (
            <img
              src={frameUrl}
              alt={`Camera ${camera.id}`}
              className={`video-stream ${isMain ? '' : 'video-preview'}`}
            />
          ) : (
            <div className="offline-placeholder">
              <div className="offline-icon">⏳</div>
              <div className="offline-text">Ожидание кадра</div>
            </div>
          )}
        </>
      )}

      {/* ===== Отображение алертов ===== */}
      {incidentCount === 1 && (
        <div className="incident-alert">
          <IncidentItem 
            incident={incidents[0]} 
            onConfirm={onConfirm} 
            onReject={onReject} 
          />
        </div>
      )}

      {incidentCount > 1 && (
        <div className="incident-alert incident-alert-multi">
          {!isIncidentListExpanded ? (
            // Свёрнутый вид
            <div 
              className="incident-summary"
              onClick={(e) => { e.stopPropagation(); setIsIncidentListExpanded(true); }}
            >
              <div className="incident-summary-icon">🔥</div>
              <div className="incident-summary-text">
                <div className="incident-summary-title">Найдено угроз: {incidentCount}</div>
                <div className="incident-summary-hint">Нажмите, чтобы развернуть</div>
              </div>
              <div className="incident-summary-arrow">▼</div>
            </div>
          ) : (
            // Развёрнутый вид со списком
            <div className="incident-list">
              <div 
                className="incident-list-header"
                onClick={(e) => { e.stopPropagation(); setIsIncidentListExpanded(false); }}
              >
                <span>🔥 Угроз: {incidentCount}</span>
                <span className="incident-collapse-arrow">▲</span>
              </div>
              <div className="incident-list-items">
                {incidents.map(inc => (
                  <IncidentItem 
                    key={inc.id} 
                    incident={inc} 
                    onConfirm={onConfirm} 
                    onReject={onReject} 
                  />
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      <div className="camera-info">
        <span className={`status-dot ${isOffline ? 'status-dot-alert' : 'status-dot-normal'}`}></span>
        <span className="camera-name">
          {camera.name}: {camera.employee_name}
        </span>
      </div>

      {!isOffline && !isMain && (
        <div className="expand-overlay">
          <span className="expand-icon">🔍</span>
        </div>
      )}
    </div>
  );
};

// ===== Главный компонент дашборда =====
export default function VideoDashboard() {
  const [cameras, setCameras] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expandedId, setExpandedId] = useState(null);
  const [currentTime, setCurrentTime] = useState(new Date());
  const { incidents, respondToIncident } = useIncidents();

  // ===== Часы с секундами =====
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  // ===== Загрузка камер =====
  useEffect(() => {
    let interval;
    const fetchCams = () => {
      fetch('/api/cams', { credentials: 'include' })
        .then(res => {
          if (res.status === 401) {
            clearInterval(interval);
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

  const handleConfirm = async (incidentId) => {
    console.log(`Подтверждаем инцидент ${incidentId}`);
    const success = await respondToIncident(incidentId, 'confirm');
    if (success) {
      console.log('Инцидент подтверждён');
    } else {
      console.error('Не удалось подтвердить инцидент');
    }
  };

  const handleReject = async (incidentId) => {
    console.log(`Отклоняем инцидент ${incidentId}`);
    const success = await respondToIncident(incidentId, 'reject');
    if (success) {
      console.log('Инцидент отклонён');
    } else {
      console.error('Не удалось отклонить инцидент');
    }
  };

  // ===== Теперь возвращает массив всех инцидентов для камеры =====
  const getIncidentsForCamera = (cameraId) => {
    return incidents.filter(inc => {
      try {
        const desc = JSON.parse(inc.description);
        return desc.device_id === cameraId;
      } catch {
        return false;
      }
    });
  };

  const mainCamera = expandedId ? cameras.find(c => c.id === expandedId) : null;
  const sideCameras = expandedId ? cameras.filter(c => c.id !== expandedId) : cameras;

  // Форматирование времени
  const timeString = currentTime.toLocaleTimeString('ru-RU', { 
    hour: '2-digit', 
    minute: '2-digit', 
    second: '2-digit' 
  });
  const dateString = currentTime.toLocaleDateString('ru-RU', {
    weekday: 'short',
    day: '2-digit',
    month: 'short'
  });

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
        
        {/* ===== Часы ===== */}
        <div className="header-clock">
          <div className="clock-time">{timeString}</div>
          <div className="clock-date">{dateString}</div>
        </div>

        <div className="status-legend">
          <div className="legend-item">
            <span className="status-indicator status-normal"></span>
            Норма
          </div>
          <div className="legend-item">
            <span className="status-indicator status-offline"></span>
            Нет связи
          </div>
          {incidents.length > 0 && (
            <div className="legend-item">
              <span className="status-indicator status-alert"></span>
              Тревога: {incidents.length}
            </div>
          )}
        </div>
      </header>

      <div className={`camera-grid ${expandedId ? 'camera-grid-expanded' : ''}`}>
        {mainCamera && (
          <div className="main-video-container">
            <CameraCard 
              camera={mainCamera} 
              isMain={true} 
              expandedId={expandedId}
              toggleFocus={toggleFocus}
              incidents={getIncidentsForCamera(mainCamera.id)}
              onConfirm={handleConfirm}
              onReject={handleReject}
            />
            <div className="video-controls">
              <button onClick={() => setExpandedId(null)} className="control-btn">
                Свернуть
              </button>
            </div>
          </div>
        )}

        {sideCameras.map((camera) => (
          <CameraCard 
            key={camera.id} 
            camera={camera} 
            expandedId={expandedId}
            toggleFocus={toggleFocus}
            incidents={getIncidentsForCamera(camera.id)}
            onConfirm={handleConfirm}
            onReject={handleReject}
          />
        ))}
      </div>
    </div>
  );
}