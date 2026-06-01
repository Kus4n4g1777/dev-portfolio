/**
 * InferenceLog Model
 *
 * Represents a single LLM inference event consumed from Kafka.
 * Stored in the `inference_logs` collection in MongoDB.
 *
 * Why MongoDB for this instead of PostgreSQL?
 * Each runtime (Gemini, Ollama, Dart, Go, cache) returns slightly
 * different metadata. A cache hit has no prompt_tokens. Ollama has
 * model_name. Gemini has safety_ratings. MongoDB's flexible document
 * model handles this schema variance without null columns or migrations.
 * This is the canonical use case for a document store over a relational DB.
 *
 * Schema design:
 * - Top level: session context and timestamp
 * - detections[]: array of YOLO results that triggered this inference
 * - llm{}: inference metadata — runtime, latency, response text
 * - cache{}: Redis LRU cache hit/miss info
 *
 * Indexes:
 * - timestamp: for time-range queries in analytics endpoints
 * - llm.runtime: for runtime distribution aggregations
 * - llm.cache_hit: for cache hit rate calculations
 * - session_id: for per-session history queries
 */

import mongoose from 'mongoose';

const detectionSchema = new mongoose.Schema({
  label:      { type: String, required: true },
  confidence: { type: Number, required: true },
  bbox:       { type: [Number], required: true }, // [x1, y1, x2, y2] normalized 0-1
}, { _id: false });

const llmSchema = new mongoose.Schema({
  runtime:       { type: String,  required: true }, // gemini-2.5-flash | dart | go | cache | ollama
  cache_hit:     { type: Boolean, required: true },
  latency_ms:    { type: Number,  required: true },
  response:      { type: String },
  // Optional — only present for full LLM calls, not cache hits
  prompt_tokens: { type: Number },
  model_name:    { type: String }, // Ollama specific
}, { _id: false });

const cacheSchema = new mongoose.Schema({
  hit:          { type: Boolean, required: true },
  key_hash:     { type: String },
  miss_reason:  { type: String }, // e.g. 'new_detection_pattern'
}, { _id: false });

const inferenceLogSchema = new mongoose.Schema({
  session_id: { type: String, required: true },
  timestamp:  { type: Date,   required: true, default: Date.now },
  detections: { type: [detectionSchema], default: [] },
  llm:        { type: llmSchema,   required: true },
  cache:      { type: cacheSchema, required: true },
}, {
  collection: 'inference_logs',
  timestamps: false, // using our own timestamp field
});

// Indexes for analytics query performance
inferenceLogSchema.index({ timestamp: -1 });
inferenceLogSchema.index({ 'llm.runtime': 1 });
inferenceLogSchema.index({ 'llm.cache_hit': 1 });
inferenceLogSchema.index({ session_id: 1 });

export default mongoose.model('InferenceLog', inferenceLogSchema);