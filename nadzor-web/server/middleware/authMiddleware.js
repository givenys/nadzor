const jwt = require('jsonwebtoken');
const modelUser = require('../models/modelUser');
const JWT_SECRET = process.env.JWT_SECRET || 'change-me-in-prod-please';
const CAMERA_API_KEY = process.env.CAMERA_API_KEY || 'my-secret-camera-key-2026';
module.exports = async (req, res, next) => {
    const apiKey = req.headers['x-api-key'];
    if (apiKey === CAMERA_API_KEY) {
        req.isDevice = true; // Помечаем, что это устройство
        req.deviceId = req.headers['x-device-id']; // Сохраняем ID камеры
        return next(); // Пропускаем дальше!
    }

    const token = req.cookies?.token;
    if (!token) return res.status(401).json({ error: 'No token or API key' });
    
    try {
        const payload = jwt.verify(token, JWT_SECRET);
        const operator = await modelUser.findById(payload.id);
        if (!operator) return res.status(401).json({ error: 'User not found' });

        req.isDevice = false;
        req.user = { 
            id: operator.id, 
            login: operator.login, 
            full_name: operator.full_name,
            role: operator.operator_role,
            employee_role: operator.employee_role,
            face_embedding: operator.face_embedding
        };
        next();
    } catch (err) {
        console.error('Auth middleware error:', err);
        res.clearCookie('token');
        res.status(401).json({ error: 'Invalid token' });
    }
};