/**
 * Analytics Dashboard Component
 *
 * Displays real-time LLM Gateway metrics sourced from MongoDB
 * via the Express Analytics service and GraphQL gateway.
 *
 * Data flow:
 * This component → AnalyticsService → Apollo → GraphQL Gateway
 *                                                    ↓
 *                               Express Analytics → MongoDB
 *
 * Three panels:
 * 1. Cache Hit Rate — Redis LRU cache performance (headline metric)
 * 2. Runtime Distribution — which LLM handled each request
 * 3. Recent Logs — last 10 inference events for live monitoring
 *
 * Design: async pipe handles subscribe/unsubscribe automatically,
 * preventing memory leaks without manual ngOnDestroy cleanup.
 */

import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import {
  AnalyticsService,
  CacheHitRate,
  RuntimeStat,
  InferenceLog,
} from '../../core/services/analytics.service';
import { Observable } from 'rxjs';

@Component({
  selector: 'app-analytics',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './analytics.component.html',
  styleUrl: './analytics.component.scss',
})
export class AnalyticsComponent implements OnInit {
  cacheHitRate$!: Observable<CacheHitRate>;
  runtimeDistribution$!: Observable<RuntimeStat[]>;
  recentLogs$!: Observable<InferenceLog[]>;

  constructor(private analyticsService: AnalyticsService) {}

  ngOnInit() {
    this.cacheHitRate$ = this.analyticsService.getCacheHitRate();
    this.runtimeDistribution$ = this.analyticsService.getRuntimeDistribution();
    this.recentLogs$ = this.analyticsService.getRecentLogs(10);
  }

  /** Color per LLM runtime — matches Flutter AI panel personality colors */
  getRuntimeColor(runtime: string): string {
    const colors: Record<string, string> = {
      'gemini-2.5-flash': '#ce93d8',
      'dart': '#f48fb1',
      'go': '#90caf9',
      'cache': '#a5d6a7',
      'ollama': '#a5d6a7',
      'none': '#ef9a9a',
    };
    return colors[runtime] ?? '#e0e0e0';
  }

  formatLatency(ms: number): string {
    if (ms < 1) return `${ms.toFixed(2)}ms ⚡`;
    if (ms < 1000) return `${Math.round(ms)}ms`;
    return `${(ms / 1000).toFixed(1)}s`;
  }
}
