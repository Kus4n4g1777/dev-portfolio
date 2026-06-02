/**
 * Analytics DataSource — Express Analytics REST Client
 *
 * Wraps the Express Analytics service HTTP API for use in GraphQL resolvers.
 * Follows the same DataSource pattern as FastAPIDataSource and SpringBootDataSource
 * — thin HTTP client, no business logic, resolver-friendly error handling.
 *
 * Architecture role:
 * GraphQL gateway is the single API layer for the Angular dashboard.
 * Rather than the frontend calling Express Analytics directly, all traffic
 * goes through GraphQL — consistent auth, consistent error format, one endpoint.
 *
 * Base URL: http://express_analytics:3000 (docker internal network)
 * Injected via ANALYTICS_URL env var — set in docker-compose.
 *
 * All methods accept an optional `since` param (ISO date string) to filter
 * results to a time window. Defaults handled by Express Analytics (last 24h).
 */

export class AnalyticsDataSource {
  constructor() {
    // Internal Docker network URL — never exposed to the outside world
    this.baseUrl = process.env.ANALYTICS_URL || 'http://express_analytics:3000';
  }

  /**
   * Generic fetch helper — centralizes error handling for all analytics calls.
   *
   * Why not use a library here?
   * Node 20 has native fetch. Keeping dependencies minimal in the gateway
   * reduces attack surface and build time. The pattern matches what's already
   * used in the resolvers/index.js for servicesHealth checks.
   */
  async #get(path) {
    const res = await fetch(`${this.baseUrl}${path}`);
    if (!res.ok) {
      throw new Error(`Analytics service error: ${res.status} ${res.statusText}`);
    }
    return res.json();
  }

  /**
   * Overall Redis LRU cache hit rate for the time window.
   * The key metric that demonstrates the LLM Gateway caching layer —
   * ~80% hit rate dropping average latency from ~3000ms to ~300ms.
   *
   * @param {string} [since] ISO date string — defaults to last 24h
   * @returns {{ total: number, cacheHits: number, hitRate: number }}
   */
  async getCacheHitRate(since) {
    const qs = since ? `?since=${since}` : '';
    return this.#get(`/analytics/cache-hit-rate${qs}`);
  }

  /**
   * Request count and average latency broken down by LLM runtime.
   * Shows which runtimes (Gemini/Ollama/Dart/Go/cache) handle most traffic.
   *
   * @param {string} [since] ISO date string — defaults to last 24h
   * @returns {Array<{ runtime: string, count: number, avgLatencyMs: number }>}
   */
  async getRuntimeDistribution(since) {
    const qs = since ? `?since=${since}` : '';
    return this.#get(`/analytics/runtime-distribution${qs}`);
  }

  /**
   * p50/p95/p99 latency percentiles per runtime.
   * The definitive proof of cache impact: cache hits at ~0.03ms vs ~3000ms.
   *
   * @param {string} [since] ISO date string — defaults to last 24h
   * @returns {Array<{ runtime: string, count: number, p50: number, p95: number, p99: number }>}
   */
  async getLatencyPercentiles(since) {
    const qs = since ? `?since=${since}` : '';
    return this.#get(`/analytics/latency-percentiles${qs}`);
  }

  /**
   * Most frequently detected YOLO labels in the time window.
   *
   * @param {string} [since] ISO date string — defaults to last 24h
   * @param {number} [limit] max results — defaults to 10
   * @returns {Array<{ label: string, count: number, avgConfidence: number }>}
   */
  async getTopDetections(since, limit) {
    const params = new URLSearchParams();
    if (since) params.set('since', since);
    if (limit) params.set('limit', limit);
    const qs = params.toString() ? `?${params}` : '';
    return this.#get(`/analytics/top-detections${qs}`);
  }

  /**
   * Last N inference logs for live monitoring and debugging.
   *
   * @param {number} [limit] max results — defaults to 20
   * @returns {Array<InferenceLog>}
   */
  async getRecentLogs(limit) {
    const qs = limit ? `?limit=${limit}` : '';
    return this.#get(`/analytics/recent${qs}`);
  }
}
