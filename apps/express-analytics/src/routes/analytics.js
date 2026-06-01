/**
 * Analytics Routes
 *
 * Exposes aggregated metrics from the inference_logs collection.
 * All endpoints support an optional `?since=` query param (ISO date string)
 * to filter results to a time window. Defaults to the last 24 hours.
 *
 * These endpoints are consumed by the GraphQL gateway, which exposes
 * them to the Angular dashboard frontend.
 *
 * Aggregation strategy:
 * MongoDB's aggregation pipeline is used throughout — filter → group → project.
 * This keeps computation in the database layer where it belongs,
 * and keeps the Node.js layer thin and stateless.
 *
 * Endpoints:
 * GET /analytics/cache-hit-rate        — % of requests served from Redis cache
 * GET /analytics/runtime-distribution  — request count broken down by LLM runtime
 * GET /analytics/latency-percentiles   — p50/p95/p99 latency by runtime
 * GET /analytics/top-detections        — most frequently detected labels
 * GET /analytics/recent                — last N inference logs (default 20)
 */

import { Router }    from 'express';
import InferenceLog  from '../models/inferenceLog.js';

const router = Router();

// Helper: parse ?since= param or default to last 24 hours
const getSince = (query) => {
  if (query.since) return new Date(query.since);
  const d = new Date();
  d.setHours(d.getHours() - 24);
  return d;
};

// ── GET /analytics/cache-hit-rate ──────────────────────────────────────────
// Returns overall cache hit rate for the time window.
// Demonstrates the Redis LRU cache performance of the LLM Gateway.
router.get('/cache-hit-rate', async (req, res) => {
  try {
    const since = getSince(req.query);

    const result = await InferenceLog.aggregate([
      { $match: { timestamp: { $gte: since } } },
      {
        $group: {
          _id: null,
          total:     { $sum: 1 },
          cacheHits: { $sum: { $cond: ['$llm.cache_hit', 1, 0] } },
        },
      },
      {
        $project: {
          _id: 0,
          total: 1,
          cacheHits: 1,
          hitRate: {
            $round: [
              { $multiply: [{ $divide: ['$cacheHits', '$total'] }, 100] },
              2,
            ],
          },
        },
      },
    ]);

    res.json(result[0] || { total: 0, cacheHits: 0, hitRate: 0 });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// ── GET /analytics/runtime-distribution ────────────────────────────────────
// Returns request count per LLM runtime.
// Shows which runtimes (Gemini/Ollama/Dart/Go/cache) handle most traffic.
router.get('/runtime-distribution', async (req, res) => {
  try {
    const since = getSince(req.query);

    const result = await InferenceLog.aggregate([
      { $match: { timestamp: { $gte: since } } },
      {
        $group: {
          _id:          '$llm.runtime',
          count:        { $sum: 1 },
          avgLatencyMs: { $avg: '$llm.latency_ms' },
        },
      },
      {
        $project: {
          _id: 0,
          runtime:      '$_id',
          count:        1,
          avgLatencyMs: { $round: ['$avgLatencyMs', 2] },
        },
      },
      { $sort: { count: -1 } },
    ]);

    res.json(result);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// ── GET /analytics/latency-percentiles ─────────────────────────────────────
// Returns p50/p95/p99 latency per runtime.
// The key metric that shows the cache impact: cache hits at ~0.03ms,
// full LLM calls at ~3000ms.
router.get('/latency-percentiles', async (req, res) => {
  try {
    const since = getSince(req.query);

    const result = await InferenceLog.aggregate([
      { $match: { timestamp: { $gte: since } } },
      { $sort:  { 'llm.latency_ms': 1 } },
      {
        $group: {
          _id:       '$llm.runtime',
          latencies: { $push: '$llm.latency_ms' },
          count:     { $sum: 1 },
        },
      },
      {
        $project: {
          _id:     0,
          runtime: '$_id',
          count:   1,
          p50: {
            $arrayElemAt: [
              '$latencies',
              { $floor: { $multiply: [0.50, { $subtract: ['$count', 1] }] } },
            ],
          },
          p95: {
            $arrayElemAt: [
              '$latencies',
              { $floor: { $multiply: [0.95, { $subtract: ['$count', 1] }] } },
            ],
          },
          p99: {
            $arrayElemAt: [
              '$latencies',
              { $floor: { $multiply: [0.99, { $subtract: ['$count', 1] }] } },
            ],
          },
        },
      },
      { $sort: { runtime: 1 } },
    ]);

    res.json(result);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// ── GET /analytics/top-detections ──────────────────────────────────────────
// Returns the most frequently detected labels in the time window.
// Useful for understanding what objects the YOLO model sees most.
router.get('/top-detections', async (req, res) => {
  try {
    const since = getSince(req.query);
    const limit = parseInt(req.query.limit) || 10;

    const result = await InferenceLog.aggregate([
      { $match:  { timestamp: { $gte: since } } },
      { $unwind: '$detections' },
      {
        $group: {
          _id:           '$detections.label',
          count:         { $sum: 1 },
          avgConfidence: { $avg: '$detections.confidence' },
        },
      },
      {
        $project: {
          _id:           0,
          label:         '$_id',
          count:         1,
          avgConfidence: { $round: ['$avgConfidence', 4] },
        },
      },
      { $sort:  { count: -1 } },
      { $limit: limit },
    ]);

    res.json(result);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// ── GET /analytics/recent ──────────────────────────────────────────────────
// Returns the last N inference logs for debugging and live monitoring.
router.get('/recent', async (req, res) => {
  try {
    const limit = parseInt(req.query.limit) || 20;

    const logs = await InferenceLog
      .find({})
      .sort({ timestamp: -1 })
      .limit(limit)
      .select('-__v');

    res.json(logs);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

export default router;