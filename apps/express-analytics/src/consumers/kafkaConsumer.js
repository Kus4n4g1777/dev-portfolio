/**
 * Kafka Consumer — LLM Inference Events
 *
 * Subscribes to the `llm.inference.events` topic and persists
 * each event as an InferenceLog document in MongoDB.
 *
 * Architecture flow:
 * LLM Gateway (FastAPI) → Kafka topic → this consumer → MongoDB
 *
 * Why Kafka instead of direct HTTP to this service?
 * - Decoupling: LLM Gateway doesn't need to know analytics exists
 * - Resilience: if this service is down, events queue in Kafka
 *   and are consumed when it comes back — no data loss
 * - Replay: can reprocess historical events from any offset
 * - Scale: multiple consumer instances can read in parallel
 *
 * Consumer group: 'express-analytics-group'
 * Kafka tracks the committed offset per group — if the service
 * restarts, it resumes from where it left off. No events are lost.
 *
 * Error handling:
 * Parse errors are logged and skipped (don't crash the consumer).
 * DB errors are logged — the message is still committed to avoid
 * infinite retry loops on malformed data. For production, implement
 * a dead-letter topic for failed messages.
 */

import { Kafka } from 'kafkajs';
import InferenceLog from '../models/inferenceLog.js';

const kafka = new Kafka({
  clientId: 'express-analytics',
  brokers: (process.env.KAFKA_BROKERS || 'kafka:9092').split(','),
});

const consumer = kafka.consumer({ groupId: 'express-analytics-group' });

export const start = async () => {
  const topic = process.env.KAFKA_TOPIC || 'llm.inference.events';

  await consumer.connect();
  await consumer.subscribe({ topic, fromBeginning: false });

  console.log(`✅ Kafka consumer subscribed to topic: ${topic}`);

  await consumer.run({
    eachMessage: async ({ message }) => {
      const raw = message.value?.toString();
      if (!raw) return;

      let event;
      try {
        event = JSON.parse(raw);
      } catch (err) {
        console.error('❌ Failed to parse Kafka message:', raw);
        return; // skip malformed message — don't crash the consumer
      }

      try {
        const log = new InferenceLog({
          session_id: event.session_id || 'unknown',
          timestamp:  event.timestamp  ? new Date(event.timestamp) : new Date(),
          detections: event.detections || [],
          llm: {
            runtime:       event.llm?.runtime      || 'unknown',
            cache_hit:     event.llm?.cache_hit    ?? false,
            latency_ms:    event.llm?.latency_ms   ?? 0,
            response:      event.llm?.response,
            prompt_tokens: event.llm?.prompt_tokens,
            model_name:    event.llm?.model_name,
          },
          cache: {
            hit:         event.cache?.hit         ?? false,
            key_hash:    event.cache?.key_hash,
            miss_reason: event.cache?.miss_reason,
          },
        });

        await log.save();
        console.log(`📥 Saved inference log | runtime: ${log.llm.runtime} | cache_hit: ${log.llm.cache_hit} | latency: ${log.llm.latency_ms}ms`);
      } catch (err) {
        console.error('❌ Failed to save inference log to MongoDB:', err.message);
      }
    },
  });
};

export const stop = async () => {
  await consumer.disconnect();
  console.log('🛑 Kafka consumer disconnected');
};