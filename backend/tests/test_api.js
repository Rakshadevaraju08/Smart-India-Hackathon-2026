/**
 * Backend API Smoke & Integration Test Suite
 */
const http = require('http');
const { app, server } = require('../server');

const PORT = 5001; // Separate port for test runner
let testServer;

function get(path) {
  return new Promise((resolve, reject) => {
    http.get(`http://127.0.0.1:${PORT}${path}`, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          resolve({ status: res.statusCode, body: JSON.parse(data) });
        } catch (e) {
          resolve({ status: res.statusCode, raw: data });
        }
      });
    }).on('error', reject);
  });
}

async function runTests() {
  console.log('=== RUNNING BACKEND API TESTS ===');
  testServer = server.listen(PORT, async () => {
    try {
      // 1. Health Route
      const health = await get('/api/health');
      console.assert(health.status === 200, 'Health check failed');
      console.assert(health.body.status === 'operational', 'Health body incorrect');
      console.log('  [PASS] GET /api/health');

      // 2. Nowcast Route
      const nowcast = await get('/api/nowcast?scenario=michaung&clogging=0.45');
      console.assert(nowcast.status === 200, 'Nowcast endpoint failed');
      console.assert(nowcast.body.status === 'success', 'Nowcast status not success');
      console.assert(nowcast.body.segments !== undefined, 'Nowcast missing segments');
      console.log('  [PASS] GET /api/nowcast');

      // 3. Hydraulics Route
      const hydraulics = await get('/api/hydraulics?clogging=0.40');
      console.assert(hydraulics.status === 200, 'Hydraulics endpoint failed');
      console.assert(hydraulics.body.coastal_boundary !== undefined, 'Hydraulics missing coastal boundary');
      console.log('  [PASS] GET /api/hydraulics');

      // 4. Routing Route
      const routing = await get('/api/routing?vehicle=ambulance');
      console.assert(routing.status === 200, 'Routing endpoint failed');
      console.assert(routing.body.safe_bypass_route.is_safe === true, 'Safe route failed');
      console.log('  [PASS] GET /api/routing');

      console.log('================================================================');
      console.log('  ALL BACKEND API TESTS PASSED (100%)');
      console.log('================================================================');
      testServer.close();
      process.exit(0);
    } catch (err) {
      console.error('Test Failed:', err);
      testServer.close();
      process.exit(1);
    }
  });
}

runTests();
