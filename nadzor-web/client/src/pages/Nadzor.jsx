import React, { useEffect, useState } from 'react';

export default function Camera() {
  const [frameUrl, setFrameUrl] = useState('');
  const [detections, setDetections] = useState([]);

  useEffect(() => {
    // Поллинг кадров
    const frameInterval = setInterval(() => {
      setFrameUrl(`/api/cam/frame?t=${Date.now()}`);
    }, 100);

    // Поллинг детектов
    const detectInterval = setInterval(async () => {
      try {
        const res = await fetch('/api/cam/detections', { credentials: 'include' });
        if (res.ok) setDetections(await res.json());
      } catch (e) { console.error(e); }
    }, 200);

    return () => {
      clearInterval(frameInterval);
      clearInterval(detectInterval);
    };
  }, []);

  return (
    <div className="p-4">
      <h1 className="text-xl mb-4">📷 Камера (admin)</h1>
      <div className="relative w-full max-w-xl mx-auto bg-black rounded overflow-hidden">
        {frameUrl && <img src={frameUrl} alt="ESP32 Stream" className="w-full" />}
        {detections.map((d, i) => (
          <div key={i} style={{
            position: 'absolute', left: d.bbox[0], top: d.bbox[1],
            width: d.bbox[2] - d.bbox[0], height: d.bbox[3] - d.bbox[1],
            border: '2px solid #0f0', borderRadius: 4
          }}>
            <span className="bg-black/70 text-white text-xs px-1">{d.class} {d.conf}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
