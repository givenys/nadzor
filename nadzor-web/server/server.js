require('dotenv').config({ path: __dirname + '/.env' });
const database = require('./configs/database');
const camRoutes = require('./routes/camRoutes');
const camController = require('./controllers/camController');
const express = require('express');
const http = require('http');
const WebSocket = require('ws')
const path = require('path');
const cors = require('cors');
const fs = require('fs').promises;
const cookieParser = require('cookie-parser');

const app = express();
const PORT = process.env.PORT || 3001;
const API_KEY = process.env.CAM_API_KEY || 'my-secret-camera-key-2026';

const buildPath = path.join(__dirname, '/../client/dist');
const TMP_DIR = path.join(__dirname, 'tmp/cam'); 
fs.mkdir(TMP_DIR, { recursive: true }).catch(() => {});

app.use(cors({
    origin: ['http://localhost:3000', 'https://wellso.su', 'http://wellso.su'],
    credentials: true 
}));
app.use(express.json());
app.use(cookieParser());

// --- Эндпоинты для детектов ---
app.post('/api/cam/detections', express.json(), async (req, res) => {
    try {
        await fs.writeFile(path.join(TMP_DIR, 'detections.json'), JSON.stringify(req.body));
        res.sendStatus(200);
    } catch (err) {
        console.error('Ошибка сохранения детектов:', err);
        res.status(500).json({ error: 'Save failed' });
    }
});

app.get('/api/cam/detections', async (req, res) => {
    try {
        const data = await fs.readFile(path.join(TMP_DIR, 'detections.json'), 'utf8');
        res.json(JSON.parse(data));
    } catch {
        res.json([]); 
    }
});

app.use(express.static(buildPath));
app.get('/api', (req, res) => res.send({express: "express backend"}));
app.use('/api/users', require('./routes/routesUser.js'));
app.use('/api/cams', camRoutes);

app.get(/.*/, (req, res) => { 
    res.sendFile(path.resolve(buildPath, 'index.html'));
});

const server = http.createServer(app);
const wss = new WebSocket.Server({ server });
const cameraViewers = new Map();

wss.on('connection', (ws, req) => {
    const url = new URL(req.url, `http://${req.headers.host}`);
    const wsPath = url.pathname;
    const deviceId = url.searchParams.get('device_id');
    const apiKey = url.searchParams.get('api_key') || req.headers['x-api-key'];

    if (wsPath === '/api/cams/upload') {
        if (apiKey !== API_KEY || !deviceId) {
            console.log('Python WS отклонен');
            ws.close(4001, 'Unauthorized');
            return;
        }
        console.log(`Камера ${deviceId} подключена по WebSocket`);

        ws.on('message', (message, isBinary) => {
            if (isBinary) {
                camController.updateFrame(deviceId, message);
                
                const viewers = cameraViewers.get(deviceId);
                if (viewers) {
                    viewers.forEach(viewer => {
                        if (viewer.readyState === WebSocket.OPEN) {
                            viewer.send(message);
                        }
                    });
                }
            }
        });

        ws.on('close', (code, reason) => {
            console.log(`Камера ${deviceId} отключена. Код: ${code}`);
        });
        ws.on('error', (err) => {
            console.error(`Ошибка WS для камеры ${deviceId}:`, err.message);
        });
    }
    else if (wsPath === '/api/cams/viewer') {
        if (!deviceId) {
            ws.close();
            return;
        }
        console.log(`Зритель подключился к камере ${deviceId}`);
        
        if (!cameraViewers.has(deviceId)) {
            cameraViewers.set(deviceId, new Set());
        }
        cameraViewers.get(deviceId).add(ws);

        ws.on('close', () => {
            const viewers = cameraViewers.get(deviceId);
            if (viewers) {
                viewers.delete(ws);
                if (viewers.size === 0) cameraViewers.delete(deviceId);
            }
            console.log(`Зритель отключился от камеры ${deviceId}`);
        });
    }
    else {
        ws.close();
    }
});

server.listen(PORT, '0.0.0.0', () => {
    console.log(`Server launched on port ${PORT} (HTTP + WebSocket)`);
});