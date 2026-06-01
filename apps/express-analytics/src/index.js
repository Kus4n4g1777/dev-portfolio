/**
 * Express Analytics Service — Entry Point
 *
 * Orchestrates startup of three subsystems:
 * 1. MongoDB connection (Mongoose)
 * 2. Kafka consumer (KafkaJS) — persists inference events to MongoDB
 * 3. Express HTTP server — exposes analytics endpoints
 *
 * Architecture role in the portfolio stack:
 * This service is the bridge between the real-time LLM Gateway and
 * the analytics layer. The Gateway publishes inference events to Kafka
 * without waiting for a response. This service consumes those events
 * asynchronously and persists them to MongoDB, where the GraphQL gateway
 * can query them for the Angular dashboard.
 *
 * Startup order:
 * MongoDB must be connected before Kafka consumer starts,
 * because incoming messages are immediately written to the DB.
 * Express starts last — no point accepting traffic before both are ready.
 *
 * Graceful shutdown:
 * SIGTERM/SIGINT handlers disconnect the Kafka consumer cleanly,
 * ensuring in-flight messages are committed before the process exits.
 * Critical in Docker environments where compose sends SIGTERM on `down`.
 *
 * ES Modules:
 * This service uses native ES Modules (import/export) — the current
 * Node.js standard. "type": "module" in package.json enables this globally.
 */

import express from 'express';
import morgan  from 'morgan';

import { connect }     from './db/connection.js';
import * as consumer   from './consumers/kafkaConsumer.js';
import analyticsRouter from './routes/analytics.js';

const app  = express();
const PORT = process.env.PORT || 3000;

// ── Middleware ──────────────────────────────────────────────────────────────
app.use(express.json());
app.use(morgan('dev')); // HTTP request logging

// ── Routes ──────────────────────────────────────────────────────────────────
// Health check — used by Docker compose healthcheck and GraphQL gateway
app.get('/health', (req, res) => {
  res.json({ status: 'ok', service: 'express-analytics', timestamp: new Date() });
});

// Analytics endpoints — consumed by GraphQL gateway → Angular dashboard
app.use('/analytics', analyticsRouter);

// ── Startup ─────────────────────────────────────────────────────────────────
const start = async () => {
  try {
    // 1. Connect to MongoDB first — consumer will write on first message
    await connect();

    // 2. Start Kafka consumer — begins polling for inference events
    await consumer.start();

    // 3. Start HTTP server — ready to serve analytics queries
    app.listen(PORT, () => {
      console.log(`✅ Express Analytics running on :${PORT}`);
      console.log(`   → GET /health`);
      console.log(`   → GET /analytics/cache-hit-rate`);
      console.log(`   → GET /analytics/runtime-distribution`);
      console.log(`   → GET /analytics/latency-percentiles`);
      console.log(`   → GET /analytics/top-detections`);
      console.log(`   → GET /analytics/recent`);
    });
  } catch (err) {
    console.error('❌ Startup failed:', err.message);
    process.exit(1);
  }
};

// ── Graceful shutdown ────────────────────────────────────────────────────────
// Docker sends SIGTERM on `docker compose down` — we catch it to flush
// the Kafka consumer and avoid losing in-flight messages.
const shutdown = async (signal) => {
  console.log(`\n🛑 ${signal} received — shutting down gracefully...`);
  await consumer.stop();
  process.exit(0);
};

process.on('SIGTERM', () => shutdown('SIGTERM'));
process.on('SIGINT',  () => shutdown('SIGINT'));

start();