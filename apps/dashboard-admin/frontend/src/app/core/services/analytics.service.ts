/**
 * Analytics Service
 *
 * Wraps Apollo Client queries for the analytics domain.
 * Provides typed observables consumed by the AnalyticsComponent.
 *
 * Architecture:
 * AnalyticsComponent → AnalyticsService → Apollo Client
 *                                              ↓
 *                                    GraphQL Gateway (:4000)
 *                                              ↓
 *                                    Express Analytics (:3000)
 *                                              ↓
 *                                         MongoDB
 *
 * TypeScript note on result.data! (non-null assertion):
 * Apollo's watchQuery types data as T | undefined because it
 * can't guarantee presence on network errors. We use filter()
 * to skip emissions where data is absent, then use ! to tell
 * TypeScript "by the time map() runs, data is definitely here."
 * This is safe because filter() has already guarded the value —
 * it's more accurate than suppressing the error with 'any'.
 */

import { Injectable } from '@angular/core';
import { Apollo, gql } from 'apollo-angular';
import { map, filter } from 'rxjs/operators';

// ── Query Definitions ──────────────────────────────────────────────────────

const CACHE_HIT_RATE_QUERY = gql`
  query GetCacheHitRate {
    analyticsCacheHitRate {
      total
      cacheHits
      hitRate
    }
  }
`;

const RUNTIME_DISTRIBUTION_QUERY = gql`
  query GetRuntimeDistribution {
    analyticsRuntimeDistribution {
      runtime
      count
      avgLatencyMs
    }
  }
`;

const RECENT_LOGS_QUERY = gql`
  query GetRecentLogs($limit: Int) {
    analyticsRecentLogs(limit: $limit) {
      id
      sessionId
      timestamp
      llm {
        runtime
        cacheHit
        latencyMs
        response
      }
      detections {
        label
        confidence
      }
    }
  }
`;

// ── Types ──────────────────────────────────────────────────────────────────

export interface CacheHitRate {
  total: number;
  cacheHits: number;
  hitRate: number;
}

export interface RuntimeStat {
  runtime: string;
  count: number;
  avgLatencyMs: number;
}

export interface InferenceLog {
  id: string;
  sessionId: string;
  timestamp: string;
  llm: {
    runtime: string;
    cacheHit: boolean;
    latencyMs: number;
    response: string;
  };
  detections: { label: string; confidence: number }[];
}

// ── Service ────────────────────────────────────────────────────────────────

@Injectable({ providedIn: 'root' })
export class AnalyticsService {
  constructor(private apollo: Apollo) {}

  getCacheHitRate() {
    return this.apollo
      .watchQuery<{ analyticsCacheHitRate: CacheHitRate }>({
        query: CACHE_HIT_RATE_QUERY,
      })
      .valueChanges.pipe(
        filter((result) => !!result.data),
        map((result) => result.data!.analyticsCacheHitRate as CacheHitRate)
      );
  }

  getRuntimeDistribution() {
    return this.apollo
      .watchQuery<{ analyticsRuntimeDistribution: RuntimeStat[] }>({
        query: RUNTIME_DISTRIBUTION_QUERY,
      })
      .valueChanges.pipe(
        filter((result) => !!result.data),
        map((result) => result.data!.analyticsRuntimeDistribution as RuntimeStat[])
      );
  }

  getRecentLogs(limit = 10) {
    return this.apollo
      .watchQuery<{ analyticsRecentLogs: InferenceLog[] }>({
        query: RECENT_LOGS_QUERY,
        variables: { limit },
      })
      .valueChanges.pipe(
        filter((result) => !!result.data),
        map((result) => result.data!.analyticsRecentLogs as InferenceLog[])
      );
  }
}
