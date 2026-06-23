const express = require('express');
const router = express.Router();
const controllerUser = require('../controllers/controllerUser');
const authMiddleware = require('../middleware/authMiddleware');
const cookieParser = require('cookie-parser');

router.use(cookieParser());

router.post('/register', controllerUser.register);
router.post('/login', controllerUser.login);
router.post('/logout', controllerUser.logout);

router.get('/me', authMiddleware, controllerUser.me);

router.get('/token', (req, res) => {
  const token = req.cookies.token;
  if (!token) {
    return res.status(401).json({ error: 'No token' });
  }
  res.json({ token });
});

module.exports = router;