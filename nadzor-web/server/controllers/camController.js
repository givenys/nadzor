const db = require('../configs/database');

// Хранилище последних кадров в памяти
const latestFrames = {};
const OFFLINE_TIMEOUT = 3000; // 3 секунды без кадра = оффлайн

//  Прием кадра от Python
exports.receiveFrame = (req, res) => {
  const deviceId = req.headers['x-device-id'];
  
  if (!deviceId) {
    return res.status(400).json({ error: 'X-Device-Id header is required' });
  }

  latestFrames[deviceId] = {
    buffer: req.body,
    timestamp: Date.now()
  };
  
  res.status(200).send('OK');
};

// 📡 Отдача MJPEG-потока для React
exports.serveStream = (req, res) => {
  const deviceId = req.params.id;

  res.writeHead(200, {
    'Connection': 'close',
    'Content-Type': 'multipart/x-mixed-replace; boundary=--frameboundary',
    'Cache-Control': 'no-cache, no-store, must-revalidate',
    'Pragma': 'no-cache',
  });

  const sendFrame = () => {
    const frameData = latestFrames[deviceId];
    if (frameData && (Date.now() - frameData.timestamp < OFFLINE_TIMEOUT)) {
      const jpg = frameData.buffer;
      res.write(`--frameboundary\r\n`);
      res.write(`Content-Type: image/jpeg\r\n`);
      res.write(`Content-Length: ${jpg.length}\r\n\r\n`);
      res.write(jpg);
      res.write(`\r\n`);
    }
  };

  const interval = setInterval(sendFrame, 100);

  req.on('close', () => {
    clearInterval(interval);
  });
};

// 📋 Получение списка камер
exports.getCameras = async (req, res) => {
  try {
    const result = await db.query(`
      SELECT 
        d.id, 
        d.name AS device_name, 
        e.full_name AS employee_name
      FROM devices d
      LEFT JOIN employees e ON d.assigned_to = e.id
      ORDER BY d.name
    `);

    const cameras = result.rows.map(cam => {
      const frameData = latestFrames[cam.id];
      const isOnline = frameData && (Date.now() - frameData.timestamp < OFFLINE_TIMEOUT);
      
      return {
        id: cam.id,
        name: cam.device_name,
        employee_name: cam.employee_name,
        is_online: isOnline
      };
    });

    res.json(cameras);
  } catch (err) {
    console.error('Get cameras error:', err);
    res.status(500).json({ error: 'Failed to load cameras' });
  }
};

//  Прием детекций (заглушка)
exports.receiveDetections = async (req, res) => {
  res.status(200).json({ message: 'Detections received' });
};