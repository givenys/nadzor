require('dotenv').config({ path: __dirname + '/.env' });

const database = require('./configs/database');
const camRoutes = require('./routes/camRoutes');

const express = require('express');
const path = require('path');
const cors = require('cors');
const fs = require('fs').promises;
const cookieParser = require('cookie-parser');
const app = express();

const PORT = process.env.PORT || 3001;
const buildPath = path.join(__dirname, '/../client/dist');
const TMP_DIR = path.join(__dirname, 'tmp/cam'); // for cam frames

fs.mkdir(TMP_DIR, { recursive: true }).catch(() => {});

app.use(cors({
  origin: ['http://localhost:3000', 'https://wellso.su', 'http://wellso.su'],
  credentials: true // Разрешает браузеру отправлять/принимать куки
}));
app.use(express.json());
app.use(cookieParser());


// ВАЖНО: express.raw() только для этого роута, чтобы не ломать express.json() для остальных
app.post('/api/cam/upload', express.raw({ type: 'image/jpeg', limit: '2mb' }), async (req, res) => {
  try {
    await fs.writeFile(path.join(TMP_DIR, 'latest.jpg'), req.body);
    res.sendStatus(200);
  } catch (err) {
    console.error('Ошибка сохранения кадра:', err);
    res.status(500).json({ error: 'Save failed' });
  }
});

// Эндпоинт для детектов от Python
app.post('/api/cam/detections', express.json(), async (req, res) => {
  try {
    await fs.writeFile(path.join(TMP_DIR, 'detections.json'), JSON.stringify(req.body));
    res.sendStatus(200);
  } catch (err) {
    console.error('Ошибка сохранения детектов:', err);
    res.status(500).json({ error: 'Save failed' });
  }
});

// React забирает последний кадр (с cache-busting)
app.get('/api/cam/frame', (req, res) => {
  const framePath = path.join(TMP_DIR, 'latest.jpg');
  if (fs.access) {
    fs.access(framePath).then(() => {
      res.sendFile(framePath);
    }).catch(() => {
      res.status(404).send('No frame yet');
    });
  }
});

// React забирает последние детекты
app.get('/api/cam/detections', async (req, res) => {
  try {
    const data = await fs.readFile(path.join(TMP_DIR, 'detections.json'), 'utf8');
    res.json(JSON.parse(data));
  } catch {
    res.json([]); // Пусто, если ещё нет детектов
  }
});


app.use(express.static(buildPath));
app.get('/api', (req, res) => res.send({express: "express backend"}));
app.use('/api/users', require('./routes/routesUser.js'));
app.use('/api/cams', camRoutes);

app.get(/.*/, (req, res) => { // /.*/ without '' means all other routs
    res.sendFile(path.resolve(buildPath, 'index.html'));
});

app.listen(PORT, '0.0.0.0', () => {
    console.log(`Server launched on port ${PORT}`);
    console.log("Index.html exists:", require('fs').existsSync(path.join(buildPath, 'index.html')));

});
