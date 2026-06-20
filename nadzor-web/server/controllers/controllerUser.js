const jwt = require('jsonwebtoken');
const modelUser = require('../models/modelUser');
const JWT_SECRET = process.env.JWT_SECRET || 'change-me-in-prod-please';

const COOKIE_OPTIONS = {
  httpOnly: true,          
  secure: false,            
  sameSite: 'lax',         
  maxAge: 7 * 24 * 60 * 60 * 1000, 
  path: '/'                
};

// Регистрация
exports.register = async (req, res) => {
  try {
    const { user, password, nickname, role } = req.body; // nickname теперь = full_name
    
    if (!user || !password) {
      return res.status(400).json({ error: 'Login and password required' });
    }

    const existing = await modelUser.findByLogin(user);
    if (existing) {
      return res.status(409).json({ error: 'User already exists' });
    }

    const newOperator = await modelUser.create(user, nickname || user, password, role || 'operator');

    const token = jwt.sign({ id: newOperator.id, login: newOperator.login }, JWT_SECRET, { expiresIn: '7d' });
    res.cookie('token', token, COOKIE_OPTIONS);

    res.status(201).json({ 
      user: { 
        id: newOperator.id, 
        login: newOperator.login, 
        full_name: newOperator.full_name, 
        role: newOperator.role 
      } 
    });
  } catch (err) {
    console.error('Register error:', err);
    res.status(500).json({ error: 'Registration failed' });
  }
};

// Логин
exports.login = async (req, res) => {
  try {
    const { user, password } = req.body; // user = login
    
    if (!user || !password) {
      return res.status(400).json({ error: 'Login and password required' });
    }

    const foundUser = await modelUser.findByLogin(user);
    if (!foundUser) {
      return res.status(401).json({ error: 'Invalid credentials' });
    }

    const valid = await modelUser.verifyPassword(foundUser, password);
    if (!valid) {
      return res.status(401).json({ error: 'Invalid credentials' });
    }

    const token = jwt.sign({ id: foundUser.id, login: foundUser.login }, JWT_SECRET, { expiresIn: '7d' });
    res.cookie('token', token, COOKIE_OPTIONS);

    res.json({ 
      user: { 
        id: foundUser.id, 
        login: foundUser.login, 
        full_name: foundUser.full_name, 
        role: foundUser.operator_role // отдаем роль оператора
      } 
    });
  } catch (err) {
    console.error('Login error:', err);
    res.status(500).json({ error: 'Login failed' });
  }
};

// Выход
exports.logout = (req, res) => {
  res.clearCookie('token', COOKIE_OPTIONS);
  res.json({ message: 'Logged out' });
};

// Проверка сессии (для авто-логина)
exports.me = async (req, res) => {
  if (!req.user) return res.status(401).json({ error: 'Not authenticated' });
  res.json({ user: req.user });
};