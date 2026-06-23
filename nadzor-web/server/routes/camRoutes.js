const express = require('express');
const router = express.Router();
const camController = require('../controllers/camController');
const incidentController = require('../controllers/incidentController');
const authMiddleware = require('../middleware/authMiddleware');
const requirePrivilege = require('../middleware/requirePrivilege');
const cookieParser = require('cookie-parser');

router.use(cookieParser());

// Маршруты для камер (только для админов)
router.get('/', authMiddleware, requirePrivilege('admin'), camController.getCameras);
router.get('/:id/stream', authMiddleware, requirePrivilege('admin'), camController.serveStream);

// API Key middleware для Python
const API_KEY = process.env.CAM_API_KEY || 'my-secret-camera-key-2026';
const apiKeyAuth = (req, res, next) => {
  const key = req.headers['x-api-key'];
  if (key !== API_KEY) {
    return res.status(401).json({ error: 'Invalid API key' });
  }
  next();
};

// Маршруты для кадров и детектов (от Python)
router.post('/upload',
  apiKeyAuth,
  express.raw({ type: 'image/jpeg', limit: '5mb' }),
  camController.receiveFrame
);

router.post('/detections',
  apiKeyAuth,
  express.json(),
  camController.receiveDetections
);

router.post('/incidents',
  apiKeyAuth,
  express.json(),
  incidentController.createIncident
);

router.get('/incidents',
  authMiddleware,  // Только авторизованные пользователи
  incidentController.getActiveIncidents
);

router.post('/incidents/:id/respond',
  authMiddleware,  // Только авторизованные операторы
  express.json(),
  incidentController.respondToIncident
);

module.exports = router;