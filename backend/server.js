/**
 * KAIROS: Urban Flood Nowcasting System - API Gateway Server
 * Smart India Hackathon 2026 (Problem Statement #26085)
 * Ministry of Earth Sciences (MoES) & NCMRWF
 */

const express = require('express');
const cors = require('cors');
const path = require('path');
const http = require('http');
const WebSocket = require('ws');

const healthRoute = require('./routes/health');
const nowcastRoute = require('./routes/nowcast');
const hydraulicsRoute = require('./routes/hydraulics');
const routingRoute = require('./routes/routing');

const app = express();
const PORT = process.env.PORT || 5000;
const FRONTEND_DIR = path.resolve(__dirname, '../frontend');

// Middleware
app.use(cors());
app.use(express.json());

// API Routes
app.use('/api/health', healthRoute);
app.use('/api/nowcast', nowcastRoute);
app.use('/api/hydraulics', hydraulicsRoute);
app.use('/api/routing', routingRoute);
app.use('/api/route', routingRoute);

// Mount frontend static assets
app.use('/data', express.static(path.join(FRONTEND_DIR, 'data')));
app.use('/static', express.static(FRONTEND_DIR));
app.use(express.static(FRONTEND_DIR));

// Serve main dashboard
app.get('/', (req, res) => {
  res.sendFile(path.join(FRONTEND_DIR, 'index.html'));
});

// Create HTTP and WebSocket server
const server = http.createServer(app);
const wss = new WebSocket.Server({ server, path: '/ws' });

wss.on('connection', (ws) => {
  console.log('[WebSocket] Client connected to live flood telemetry stream');
  ws.send(JSON.stringify({
    type: 'CONNECTION_ESTABLISHED',
    radar_station: 'IMD Meenambakkam',
    active_nowcast_horizon: 'T+60m',
    timestamp: new Date().toISOString()
  }));

  const interval = setInterval(() => {
    if (ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({
        type: 'TELEMETRY_HEARTBEAT',
        radar_status: 'RECEIVING_SWEEPS',
        tide_stage_m: +(0.42 * Math.cos(Date.now() / 3600000) + 0.35).toFixed(2),
        timestamp: new Date().toISOString()
      }));
    }
  }, 10000);

  ws.on('close', () => clearInterval(interval));
});

if (require.main === module) {
  server.listen(PORT, () => {
    console.log('================================================================');
    console.log(`  KAIROS API Gateway running on http://127.0.0.1:${PORT}`);
    console.log(`  MoES / NCMRWF Pilot — Urban Flood Nowcasting System (PS #26085)`);
    console.log(`  Serving Web GIS Dashboard from: ${FRONTEND_DIR}`);
    console.log('================================================================');
  });
}

module.exports = { app, server };
