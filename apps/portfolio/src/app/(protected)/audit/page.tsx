export const dynamic = 'force-dynamic';
import { fetchGraphQL } from '../../../lib/graphql';

const AUDIT_QUERY = `
  query GetAuditLogs($limit: Int, $offset: Int, $runtime: String, $cache: String) {
    auditLogs(limit: $limit, offset: $offset, runtime: $runtime, cache: $cache) {
      total
      logs {
        id
        event_type
        payload
        timestamp
      }
    }
  }
`;

type AuditLog = {
  id: string;
  event_type: string;
  payload: string;
  timestamp: string;
};

const PAGE_SIZE = 20;
const RUNTIMES = ['cache', 'gemini-2.5-flash', 'dart', 'go', 'none'];

export default async function AuditPage({
  searchParams,
}: {
  searchParams: Promise<{ page?: string; runtime?: string; cache?: string }>;
}) {
  const params  = await searchParams;
  const page    = Math.max(1, parseInt(params.page ?? '1', 10));
  const runtime = params.runtime ?? '';
  const cache   = params.cache   ?? '';
  const offset  = (page - 1) * PAGE_SIZE;

  let logs: AuditLog[] = [];
  let total = 0;

  try {
    const response = await fetchGraphQL(AUDIT_QUERY, {
      limit:   PAGE_SIZE,
      offset,
      runtime: runtime || null,
      cache:   cache   || null,
    });
    logs  = response.data?.auditLogs?.logs  ?? [];
    total = response.data?.auditLogs?.total ?? 0;
  } catch {
    logs  = [];
    total = 0;
  }

  const totalPages = Math.ceil(total / PAGE_SIZE);
  const hasFilter  = runtime || cache;

  const buildUrl = (overrides: Record<string, string>) => {
    const q = new URLSearchParams();
    const merged = { page: '1', runtime, cache, ...overrides };
    if (parseInt(merged.page) > 1) q.set('page', merged.page);
    if (merged.runtime) q.set('runtime', merged.runtime);
    if (merged.cache)   q.set('cache',   merged.cache);
    return '/audit' + (q.toString() ? '?' + q.toString() : '');
  };

  return (
    <div className="w-full max-w-5xl flex flex-col items-center mt-12">

      {/* Header */}
      <div className="text-center mb-8">
        <h1 className="text-4xl font-extrabold mb-4 text-white drop-shadow-md">
          Audit Logs 🔍
        </h1>
        <p className="text-gray-300 text-lg leading-relaxed max-w-2xl mx-auto">
          {total > 0
            ? `${total} events captured from the Kafka pipeline via Django.`
            : 'No events yet — logs will appear as the system processes inferences.'}
        </p>
      </div>

      {/* Filter controls — same width as table */}
      <div className="w-full flex items-center justify-between mb-4 gap-4">

        {/* Runtime — left */}
        <div className="flex items-center gap-2 bg-white/5 border border-white/10 rounded-xl px-4 py-2">
          <span className="text-xs text-gray-400 uppercase tracking-wider font-bold shrink-0">Runtime</span>
          <div className="flex gap-1 flex-wrap">
            <a href={buildUrl({ runtime: '', page: '1' })}
              className={`px-3 py-1 rounded-lg text-xs font-medium transition-colors ${runtime === '' ? 'bg-orange-500 text-white' : 'text-gray-400 hover:text-white hover:bg-white/10'}`}>
              all
            </a>
            {RUNTIMES.map((r) => (
              <a key={r} href={buildUrl({ runtime: r, page: '1' })}
                className={`px-3 py-1 rounded-lg text-xs font-medium transition-colors ${runtime === r ? 'bg-orange-500 text-white' : 'text-gray-400 hover:text-white hover:bg-white/10'}`}>
                {r}
              </a>
            ))}
          </div>
        </div>

        {/* Clear — center, only when filter active */}
        {hasFilter ? (
          <a href="/audit"
            className="shrink-0 px-4 py-2 rounded-xl text-xs text-gray-400 hover:text-white border border-white/10 hover:bg-white/10 transition-colors whitespace-nowrap">
            clear ✕
          </a>
        ) : (
          <div className="shrink-0 w-20" />
        )}

        {/* Cache — right */}
        <div className="flex items-center gap-2 bg-white/5 border border-white/10 rounded-xl px-4 py-2">
          <span className="text-xs text-gray-400 uppercase tracking-wider font-bold shrink-0">Cache</span>
          <div className="flex gap-1">
            {([['', 'all'], ['hit', 'HIT ⚡'], ['miss', 'MISS']] as [string, string][]).map(([val, label]) => (
              <a key={val || 'all'} href={buildUrl({ cache: val, page: '1' })}
                className={`px-3 py-1 rounded-lg text-xs font-medium transition-colors ${cache === val ? 'bg-orange-500 text-white' : 'text-gray-400 hover:text-white hover:bg-white/10'}`}>
                {label}
              </a>
            ))}
          </div>
        </div>

      </div>

      {/* Table container — fixed min-height so page doesn't shift */}
      <div className="w-full bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl overflow-hidden shadow-2xl min-h-[520px] flex flex-col">

        {logs.length === 0 ? (
          <div className="flex-1 flex flex-col items-center justify-center p-12 text-center">
            <p className="text-5xl mb-4">📭</p>
            <p className="text-gray-400 text-sm">
              {hasFilter
                ? 'No events matching the selected filters.'
                : 'No events yet — send prompts via the LLM Gateway to generate audit events.'}
            </p>
          </div>
        ) : (
          <>
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-white/10 bg-black/20">
                  <th className="py-4 px-6 text-xs font-bold text-gray-400 tracking-wider uppercase">Event</th>
                  <th className="py-4 px-6 text-xs font-bold text-gray-400 tracking-wider uppercase">Runtime</th>
                  <th className="py-4 px-6 text-xs font-bold text-gray-400 tracking-wider uppercase">Cache</th>
                  <th className="py-4 px-6 text-xs font-bold text-gray-400 tracking-wider uppercase">Latency</th>
                  <th className="py-4 px-6 text-xs font-bold text-gray-400 tracking-wider uppercase text-right">Timestamp</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {logs.map((log) => {
                  let parsed: Record<string, unknown> = {};
                  try { parsed = JSON.parse(log.payload); } catch {}
                  const llm       = parsed.llm   as Record<string, unknown> | undefined;
                  const cacheData = parsed.cache as Record<string, unknown> | undefined;
                  const rt        = String(llm?.runtime ?? '-');
                  const cacheHit  = Boolean(cacheData?.hit);
                  const latency   = llm?.latency_ms != null
                    ? `${Number(llm.latency_ms).toFixed(1)}ms` : '-';
                  const rtColor   =
                    rt === 'cache'            ? 'text-green-400'  :
                    rt === 'gemini-2.5-flash' ? 'text-purple-400' :
                    rt === 'dart'             ? 'text-blue-400'   :
                    rt === 'go'               ? 'text-cyan-400'   : 'text-gray-500';

                  return (
                    <tr key={log.id} className="hover:bg-white/10 transition-colors">
                      <td className="py-4 px-6">
                        <span className="text-xs font-semibold px-3 py-1 rounded-full border bg-blue-500/20 text-blue-400 border-blue-500/30">
                          {log.event_type}
                        </span>
                      </td>
                      <td className={`py-4 px-6 text-sm font-mono font-medium ${rtColor}`}>{rt}</td>
                      <td className="py-4 px-6">
                        {cacheHit
                          ? <span className="text-xs font-semibold px-2 py-1 rounded-full bg-green-500/20 text-green-400 border border-green-500/30">HIT ⚡</span>
                          : <span className="text-xs font-semibold px-2 py-1 rounded-full bg-gray-500/20 text-gray-400 border border-gray-500/30">MISS</span>
                        }
                      </td>
                      <td className="py-4 px-6 text-sm text-gray-400 font-mono">{latency}</td>
                      <td className="py-4 px-6 text-sm text-gray-400 text-right whitespace-nowrap">
                        {new Date(log.timestamp).toLocaleString()}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>

            {/* Pagination — pinned to bottom of container */}
            {totalPages > 1 && (
              <div className="mt-auto flex items-center justify-between px-6 py-4 border-t border-white/10 bg-black/10">
                <span className="text-xs text-gray-400">
                  Page {page} of {totalPages} · {total} total events
                </span>
                <div className="flex gap-2">
                  {page > 1 && (
                    <a href={buildUrl({ page: String(page - 1) })}
                      className="px-4 py-2 text-xs rounded-lg bg-white/10 hover:bg-white/20 text-white transition-colors">
                      ← Prev
                    </a>
                  )}
                  {page < totalPages && (
                    <a href={buildUrl({ page: String(page + 1) })}
                      className="px-4 py-2 text-xs rounded-lg bg-white/10 hover:bg-white/20 text-white transition-colors">
                      Next →
                    </a>
                  )}
                </div>
              </div>
            )}
          </>
        )}
      </div>

    </div>
  );
}
