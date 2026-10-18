const test = require('node:test');
const assert = require('node:assert');
const http = require('node:http');
const app = require('../src/index');

test('Express Interaction Service Suite', async (t) => {
  const server = http.createServer(app);
  await new Promise(resolve => server.listen(0, resolve));
  const port = server.address().port;
  const baseUrl = `http://127.0.0.1:${port}`;

  t.after(() => server.close());

  await t.test('Health check returns 200 and healthy status', async () => {
    const res = await fetch(`${baseUrl}/health`);
    assert.strictEqual(res.status, 200);
    const data = await res.json();
    assert.strictEqual(data.status, 'healthy');
    assert.strictEqual(data.service, 'express-interaction-service');
  });

  await t.test('POST /api/v1/interactions records new user rating', async () => {
    const payload = {
      userId: 'test_user_42',
      animeId: '11061',
      animeTitle: 'Hunter x Hunter (2011)',
      rating: 9.9,
      type: 'completed',
      review: 'Chimera Ant arc is unmatched.'
    };
    const res = await fetch(`${baseUrl}/api/v1/interactions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    assert.strictEqual(res.status, 201);
    const data = await res.json();
    assert.strictEqual(data.status, 'recorded');
    assert.strictEqual(data.interaction.userId, 'test_user_42');
  });

  await t.test('GET /api/v1/interactions/user/:userId returns user history', async () => {
    const res = await fetch(`${baseUrl}/api/v1/interactions/user/test_user_42`);
    assert.strictEqual(res.status, 200);
    const data = await res.json();
    assert.strictEqual(data.status, 'success');
    assert.strictEqual(data.count, 1);
    assert.strictEqual(data.interactions[0].animeId, '11061');
  });
});
