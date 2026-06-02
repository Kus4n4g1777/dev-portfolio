/**
 * Analytics GraphQL Type Definitions
 *
 * Extends the main schema with analytics types and queries.
 * Kept in a separate file to maintain clean separation — each domain
 * owns its own type definitions, merged at server startup.
 *
 * Design decisions:
 * - All analytics queries are optional-auth (requireAuth commented out)
 *   because the Angular dashboard shows these on a public metrics page.
 *   Add requireAuth/requireRole if this needs to be gated.
 * - `since` param is a String (ISO 8601) rather than a custom DateTime scalar
 *   to keep the schema simple — the Express Analytics service parses it.
 * - Latency values are Float (not Int) to preserve sub-millisecond precision
 *   for cache hits (~0.03ms).
 */

export const analyticsTypeDefs = `#graphql

  # ─── ANALYTICS DOMAIN (Express Analytics → MongoDB) ───────────────────────

  type CacheHitRate {
    total:     Int!
    cacheHits: Int!
    hitRate:   Float!   # percentage 0-100, e.g. 80.5
  }

  type RuntimeStat {
    runtime:      String!
    count:        Int!
    avgLatencyMs: Float!
  }

  type LatencyPercentile {
    runtime: String!
    count:   Int!
    p50:     Float!   # median latency
    p95:     Float!   # 95th percentile
    p99:     Float!   # 99th percentile — shows worst-case LLM call time
  }

  type DetectionStat {
    label:         String!
    count:         Int!
    avgConfidence: Float!
  }

  type InferenceLogLLM {
    runtime:      String!
    cacheHit:     Boolean!
    latencyMs:    Float!
    response:     String
    promptTokens: Int      # null for cache hits
    modelName:    String   # Ollama specific
  }

  type InferenceLogCache {
    hit:        Boolean!
    keyHash:    String
    missReason: String
  }

  type InferenceLogDetection {
    label:      String!
    confidence: Float!
    bbox:       [Float!]!  # [x1, y1, x2, y2] normalized 0-1
  }

  type InferenceLog {
    id:         ID!
    sessionId:  String!
    timestamp:  String!
    detections: [InferenceLogDetection!]!
    llm:        InferenceLogLLM!
    cache:      InferenceLogCache!
  }

  # ─── EXTEND MAIN QUERY ─────────────────────────────────────────────────────
  extend type Query {
    # Cache hit rate for the LLM Gateway Redis LRU layer
    # since: ISO 8601 date string, defaults to last 24h on the analytics service
    analyticsCacheHitRate(since: String): CacheHitRate!

    # Request count + avg latency per LLM runtime
    analyticsRuntimeDistribution(since: String): [RuntimeStat!]!

    # p50/p95/p99 latency per runtime — shows cache impact clearly
    analyticsLatencyPercentiles(since: String): [LatencyPercentile!]!

    # Most frequently detected YOLO labels
    analyticsTopDetections(since: String, limit: Int): [DetectionStat!]!

    # Last N raw inference logs for live monitoring
    analyticsRecentLogs(limit: Int): [InferenceLog!]!
  }
`;
