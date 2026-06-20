const express = require('express');
const router = express.Router();
const controllerUser = require('../controllers/controllerUser');
const authMiddleware = require('../middleware/authMiddleware');
const cookieParser = require('cookie-parser');

// Парсер куки — обязательно!
router.use(cookieParser());

// Публичные маршруты
router.post('/register', controllerUser.register);
router.post('/login', controllerUser.login);
router.post('/logout', controllerUser.logout);

// Защищённые маршруты
router.get('/me', authMiddleware, controllerUser.me);

// Пример: защитить камеру только для авторизованных
router.use('/cam', authMiddleware); // раскомментируй, если нужно

module.exports = router;
