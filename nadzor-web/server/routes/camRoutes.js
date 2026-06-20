const express = require('express');
const router = express.Router();
const camController = require('../controllers/camController');
const authMiddleware = require('../middleware/authMiddleware');
const requirePrivilege = require('../middleware/requirePrivilege');
const cookieParser = require('cookie-parser');

router.use(cookieParser());

router.get('/', authMiddleware, requirePrivilege('admin'), camController.getCameras);
router.get('/:id/stream', authMiddleware, requirePrivilege('admin'), camController.serveStream);

const API_KEY = process.env.CAM_API_KEY || 'my-secret-camera-key-2026';
const apiKeyAuth = (req, res, next) => {
    const key = req.headers['x-api-key'];
    if (key !== API_KEY) {
        return res.status(401).json({ error: 'Invalid API key' });
    }
    next();
};

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

module.exports = router;