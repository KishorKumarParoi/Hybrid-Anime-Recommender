const express = require('express');
const cors = require('cors');
const crypto = require('crypto');

const app = express();
const PORT = process.env.PORT || 8082;
const JWT_SECRET = process.env.JWT_SECRET_KEY || 'har-super-secret-jwt-key-2026-production-ready';

app.use(cors());
app.use(express.json());

// In-Memory Resilient Store (MongoDB/PostgreSQL buffer)
const interactions = [];
const animeStats = new Map();

// Helper: Seed initial interactions
interactions.push({
  id: 'act_demo_1',
  userId: 'admin',
  animeId: '5114',
  animeTitle: 'Fullmetal Alchemist: Brotherhood',
  rating: 10.0,
  type: 'completed',
  review: 'Masterpiece pacing, characters, and soundtrack.',
  timestamp: new Date().toISOString()
});
interactions.push({
  id: 'act_demo_2',
  userId: 'kenshiro',
  animeId: '9253',
  animeTitle: 'Steins;Gate',
  rating: 9.8,
  type: 'bookmark',
  review: 'Unmatched time travel dynamics.',
  timestamp: new Date().toISOString()
});

// Minimal zero-dependency JWT HS256 verifier
function verifyToken(token) {
  try {
    const parts = token.split('.');
    if (parts.length !== 3) return null;
    const [headerB64, payloadB64, sigB64] = parts;
    const expectedSig = crypto
      .createHmac('sha256', JWT_SECRET)
      .update(`${headerB64}.${payloadB64}`)
      .digest('base64url');
    if (sigB64 !== expectedSig) return null;
    const payload = JSON.parse(Buffer.from(payloadB64, 'base64url').toString('utf8'));
    if (payload.exp && payload.exp < Math.floor(Date.now() / 1000)) return null;
    return payload;
  } catch (e) {
    return null;
  }
}

// ─── Routes ──────────────────────────────────────────────────────────────────

// 1. Record User Interaction (Rating, Bookmark, Like, Review)
app.post(['/api/v1/interactions', '/api/v1/interactions/reviews', '/interactions'], (req, res) => {
  const { userId, animeId, animeTitle, rating, type = 'rating', review = '', user_id, anime_id, action } = req.body;
  const effectiveUserId = userId || user_id;
  const effectiveAnimeId = animeId || anime_id;
  const effectiveType = action || type;

  if (!effectiveUserId || !effectiveAnimeId) {
    return res.status(400).json({ error: 'userId and animeId are required' });
  }

  const record = {
    id: `act_${crypto.randomBytes(6).toString('hex')}`,
    userId: String(effectiveUserId),
    animeId: String(effectiveAnimeId),
    animeTitle: animeTitle || `Anime #${effectiveAnimeId}`,
    rating: Number(rating) || 0,
    type: effectiveType,
    review,
    timestamp: new Date().toISOString()
  };

  interactions.unshift(record);
  if (interactions.length > 500) interactions.pop();

  // Update aggregated community stats
  const current = animeStats.get(String(animeId)) || { totalRatings: 0, ratingSum: 0, likes: 0 };
  if (record.rating > 0) {
    current.totalRatings += 1;
    current.ratingSum += record.rating;
  }
  if (type === 'like' || type === 'bookmark') {
    current.likes += 1;
  }
  animeStats.set(String(animeId), current);

  return res.status(201).json({
    status: 'recorded',
    interaction: record,
    stats: {
      animeId,
      avgRating: current.totalRatings > 0 ? (current.ratingSum / current.totalRatings).toFixed(2) : 0,
      totalRatings: current.totalRatings,
      likes: current.likes
    }
  });
});

// 2. Get User Interaction History
app.get('/api/v1/interactions/user/:userId', (req, res) => {
  const { userId } = req.params;
  const userHistory = interactions.filter(i => i.userId === userId);
  return res.json({
    status: 'success',
    userId,
    count: userHistory.length,
    interactions: userHistory
  });
});

// 3. Get Anime Community Statistics
app.get('/api/v1/interactions/anime/:animeId/stats', (req, res) => {
  const { animeId } = req.params;
  const stats = animeStats.get(String(animeId)) || { totalRatings: 0, ratingSum: 0, likes: 0 };
  return res.json({
    status: 'success',
    animeId,
    stats: {
      averageRating: stats.totalRatings > 0 ? (stats.ratingSum / stats.totalRatings).toFixed(2) : 0,
      totalRatings: stats.totalRatings,
      likes: stats.likes
    }
  });
});

// 4. Live Platform Activity Feed
app.get('/api/v1/interactions/recent', (req, res) => {
  const limit = parseInt(req.query.limit || '10', 10);
  return res.json({
    status: 'success',
    count: Math.min(limit, interactions.length),
    recent: interactions.slice(0, limit)
  });
});

// 5. Health Check
app.get(['/health', '/api/v1/interactions/health', '/interactions/health'], (req, res) => {
  return res.json({
    status: 'healthy',
    service: 'express-interaction-service',
    totalInteractions: interactions.length,
    uptimeSec: Math.floor(process.uptime())
  });
});

// Export app for unit testing and local runner
if (require.main === module) {
  app.listen(PORT, () => {
    console.log(`[✓] Express Interaction Microservice listening on :${PORT}`);
  });
}

module.exports = app;
