import { fetchGraphQL } from '../../../lib/graphql';
import { cookies } from 'next/headers';

// We define our exact GraphQL query to pull live analytics
export const dynamic = 'force-dynamic';

const DASHBOARD_QUERY = `
  query {
    analyticsCacheHitRate { total cacheHits hitRate }
    analyticsRuntimeDistribution { runtime count avgLatencyMs }
    analyticsTopDetections { label count avgConfidence }
  }
`;

export default async function DashboardPage() {
  // We fetch data directly on the server before the HTML is even sent to the browser
  const response = await fetchGraphQL(DASHBOARD_QUERY);
  const stats = response.data;
  
  // We ensure fallbacks in case the analytics DB is fresh/empty
  const total = stats?.analyticsCacheHitRate?.total ?? 0;
  const hitRate = stats?.analyticsCacheHitRate?.hitRate ?? 0;
  const topLabel = stats?.analyticsTopDetections?.[0]?.label ?? 'items';

  return (
    <div className="w-full max-w-3xl flex flex-col items-center animate-fade-in-up mt-12">
      
      {/* Header Area */}
      <div className="text-center mb-10">
        <h1 className="text-4xl font-extrabold mb-4 text-white drop-shadow-md">
          Dashboard Analytics ⚡
        </h1>
        <p className="text-gray-300 text-lg leading-relaxed max-w-2xl mx-auto">
          System processed <span className="text-white font-bold">{total} inferences</span>, with 
          <span className="text-green-400 font-semibold"> {hitRate}%</span> served directly from cache. 
          The model is heavily detecting {topLabel}s.
        </p>
      </div>

      {/* Glassmorphism Table connecting to actual data */}
      <div className="w-full bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl overflow-hidden shadow-2xl">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="border-b border-white/10 bg-black/20">
              <th className="py-4 px-6 text-xs font-bold text-gray-400 tracking-wider uppercase">Metric</th>
              <th className="py-4 px-6 text-xs font-bold text-gray-400 tracking-wider uppercase text-right">Value</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            <tr className="hover:bg-white/10 transition-colors">
              <td className="py-4 px-6 text-sm text-gray-300">Total Inferences</td>
              <td className="py-4 px-6 text-sm font-semibold text-right text-white">{total}</td>
            </tr>
            <tr className="hover:bg-white/10 transition-colors bg-white/[0.02]">
              <td className="py-4 px-6 text-sm text-gray-300">Cache Hit Rate</td>
              <td className="py-4 px-6 text-sm font-bold text-green-400 text-right">{hitRate}%</td>
            </tr>
            <tr className="hover:bg-white/10 transition-colors">
              <td className="py-4 px-6 text-sm text-gray-300">Cache Hits (Instant)</td>
              <td className="py-4 px-6 text-sm font-semibold text-right text-white">
                {stats?.analyticsCacheHitRate?.cacheHits ?? 0}
              </td>
            </tr>
            
            {/* We map over dynamic runtimes from Go/Python/Dart */}
            {stats?.analyticsRuntimeDistribution?.map((rt: any) => (
              <tr key={rt.runtime} className="hover:bg-white/10 transition-colors">
                <td className="py-4 px-6 text-sm text-gray-300 capitalize">Runtime — {rt.runtime}</td>
                <td className="py-4 px-6 text-sm font-semibold text-right text-white">
                  {rt.count} req · avg {Math.round(rt.avgLatencyMs)}ms
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
