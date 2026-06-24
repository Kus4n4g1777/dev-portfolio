export const dynamic = 'force-dynamic';
import { fetchGraphQL } from '../../lib/graphql';

const AUDIT_QUERY = `
  query {
    auditLogs(limit: 50) {
      id
      event_type
      payload
      timestamp
    }
  }
`;

type AuditLog = {
  id: string;
  event_type: string;
  payload: string;
  timestamp: string;
};

function eventBadgeColor(eventType: string) {
  if (eventType.includes('error') || eventType.includes('fail')) return 'bg-red-500/20 text-red-400 border-red-500/30';
  if (eventType.includes('inference') || eventType.includes('llm')) return 'bg-orange-500/20 text-orange-400 border-orange-500/30';
  if (eventType.includes('cache')) return 'bg-green-500/20 text-green-400 border-green-500/30';
  return 'bg-blue-500/20 text-blue-400 border-blue-500/30';
}

export default async function AuditPage() {
  let logs: AuditLog[] = [];

  try {
    const response = await fetchGraphQL(AUDIT_QUERY);
    logs = response.data?.auditLogs ?? [];
  } catch {
    logs = [];
  }

  return (
    <div className="w-full max-w-4xl flex flex-col items-center animate-fade-in-up mt-12">

      <div className="text-center mb-10">
        <h1 className="text-4xl font-extrabold mb-4 text-white drop-shadow-md">
          Audit Logs 🔍
        </h1>
        <p className="text-gray-300 text-lg leading-relaxed max-w-2xl mx-auto">
          {logs.length > 0
            ? `${logs.length} events captured from the Kafka pipeline via Django.`
            : 'No events yet — logs will appear as the system processes inferences.'}
        </p>
      </div>

      {logs.length === 0 && (
        <div className="w-full bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl p-12 text-center shadow-2xl">
          <p className="text-5xl mb-4">📭</p>
          <p className="text-gray-400 text-sm">
            Send some prompts via the LLM Gateway to generate audit events.
          </p>
        </div>
      )}

      {logs.length > 0 && (
        <div className="w-full bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl overflow-hidden shadow-2xl">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-white/10 bg-black/20">
                <th className="py-4 px-6 text-xs font-bold text-gray-400 tracking-wider uppercase">Event</th>
                <th className="py-4 px-6 text-xs font-bold text-gray-400 tracking-wider uppercase">Payload</th>
                <th className="py-4 px-6 text-xs font-bold text-gray-400 tracking-wider uppercase text-right">Timestamp</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {logs.map((log) => (
                <tr key={log.id} className="hover:bg-white/10 transition-colors">
                  <td className="py-4 px-6">
                    <span className={`text-xs font-semibold px-3 py-1 rounded-full border ${eventBadgeColor(log.event_type)}`}>
                      {log.event_type}
                    </span>
                  </td>
                  <td className="py-4 px-6 text-sm text-gray-300 font-mono max-w-xs truncate">
                    {log.payload}
                  </td>
                  <td className="py-4 px-6 text-sm text-gray-400 text-right whitespace-nowrap">
                    {new Date(log.timestamp).toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
