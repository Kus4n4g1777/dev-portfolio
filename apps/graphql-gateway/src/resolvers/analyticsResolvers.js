/**
 * Analytics Resolvers
 *
 * Connects the analytics GraphQL queries to the AnalyticsDataSource.
 * Follows the same pattern as the existing resolvers in index.js —
 * pull the datasource from context, delegate, return.
 *
 * Why keep these in a separate file?
 * The resolvers/index.js already has ~80 lines. Splitting by domain
 * keeps each file focused and makes it easy to find what you're looking for.
 * The main index.js merges these in via spread.
 *
 * Auth strategy:
 * Analytics queries don't call requireAuth() — the dashboard metrics page
 * is intended to be publicly visible as a portfolio demo. If this were
 * production, you'd add requireRole(context, 'ADMIN') to each resolver.
 *
 * Error handling:
 * GraphQL catches thrown errors and formats them as proper GraphQL errors.
 * The AnalyticsDataSource throws on non-OK HTTP responses, so errors
 * propagate cleanly without needing try/catch in every resolver.
 */

export const analyticsResolvers = {
  Query: {
    /**
     * Cache hit rate for the LLM Gateway Redis LRU layer.
     * The headline metric — ~80% hit rate, ~0.03ms vs ~3000ms.
     */
    analyticsCacheHitRate: async (_, { since }, context) => {
      return context.analytics.getCacheHitRate(since);
    },

    /**
     * Request distribution across LLM runtimes (Gemini/Ollama/Dart/Go/cache).
     * Shows which runtime handles most traffic and their average latency.
     */
    analyticsRuntimeDistribution: async (_, { since }, context) => {
      return context.analytics.getRuntimeDistribution(since);
    },

    /**
     * Latency percentiles (p50/p95/p99) per runtime.
     * The most compelling visualization for the portfolio — shows the
     * dramatic difference between cache hits and full LLM calls.
     */
    analyticsLatencyPercentiles: async (_, { since }, context) => {
      return context.analytics.getLatencyPercentiles(since);
    },

    /**
     * Most frequently detected YOLO labels in the time window.
     * Answers "what does the model see most?" for the portfolio demo.
     */
    analyticsTopDetections: async (_, { since, limit }, context) => {
      return context.analytics.getTopDetections(since, limit);
    },

    /**
     * Last N inference logs — raw documents from MongoDB.
     * Used for live monitoring and debugging on the dashboard.
     */
    analyticsRecentLogs: async (_, { limit }, context) => {
      const logs = await context.analytics.getRecentLogs(limit);
      // Map MongoDB _id to GraphQL id convention
      return logs.map(log => ({
        ...log,
        id: log._id,
        sessionId:  log.session_id,
        llm: {
          ...log.llm,
          cacheHit:     log.llm?.cache_hit,
          latencyMs:    log.llm?.latency_ms,
          promptTokens: log.llm?.prompt_tokens,
          modelName:    log.llm?.model_name,
        },
        cache: {
          ...log.cache,
          keyHash:    log.cache?.key_hash,
          missReason: log.cache?.miss_reason,
        },
        detections: (log.detections || []).map(d => ({
          label:      d.label,
          confidence: d.confidence,
          bbox:       d.bbox,
        })),
      }));
    },
  },
};