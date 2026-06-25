export type AuditLog = {
  id: string;
  event_type: string;
  payload: string;
  timestamp: string;
};

export type RuntimeStat = {
  runtime: string;
  count: number;
  avgLatencyMs: number;
};

export type CacheStats = {
  total: number;
  cacheHits: number;
  hitRate: number;
};
