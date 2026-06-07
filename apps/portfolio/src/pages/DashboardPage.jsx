import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';

// ─── Fireworks ────────────────────────────────────────────────────────────────
// Pure CSS fireworks — no library, zero bundle cost.
// Three particles positioned behind the table, blurred for depth effect.
const Fireworks = () => (
  <div className="fireworks-wrapper" aria-hidden="true">
    {[...Array(3)].map((_, i) => (
      <div key={i} className={`firework firework-${i + 1}`}>
        {[...Array(8)].map((_, j) => (
          <span key={j} className="particle" style={{ '--i': j }} />
        ))}
      </div>
    ))}
  </div>
);

// ─── Stats table rows ─────────────────────────────────────────────────────────
const StatRow = ({ label, value, highlight }) => (
  <tr className={`stat-row ${highlight ? 'stat-row--highlight' : ''}`}>
    <td className="stat-label">{label}</td>
    <td className="stat-value">{value}</td>
  </tr>
);

// ─── Main component ───────────────────────────────────────────────────────────
const DashboardPage = () => {
  const { user, logout } = useAuth();
  const [stats, setStats] = useState(null);
  const [aiMessage, setAiMessage] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user) return;
    fetchStats();
  }, [user]);

  const fetchStats = async () => {
    try {
      // Fetch analytics from Express Analytics via GraphQL gateway
      const res = await fetch('http://localhost:4000/graphql', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: `query {
            analyticsCacheHitRate { total cacheHits hitRate }
            analyticsRuntimeDistribution { runtime count avgLatencyMs }
            analyticsTopDetections { label count avgConfidence }
          }`,
        }),
      });

      const { data } = await res.json();

      setStats(data);

      // Generate a personalized AI message based on the data
      const total = data?.analyticsCacheHitRate?.total ?? 0;
      const hitRate = data?.analyticsCacheHitRate?.hitRate ?? 0;
      const topLabel = data?.analyticsTopDetections?.[0]?.label ?? 'objects';

      setAiMessage(
        total === 0
          ? `Welcome back, ${user.username}! Ready to start detecting? Point the camera and let the AI do its thing.`
          : `Hey ${user.username} — ${total} inference${total !== 1 ? 's' : ''} processed, ` +
            `${hitRate}% served from cache at lightning speed. ` +
            `Your model loves detecting ${topLabel}s. Keep it up! ⚡`
      );
    } catch (err) {
      setAiMessage(`Welcome back, ${user?.username}! Your detection history will appear here.`);
    } finally {
      setLoading(false);
    }
  };

  if (!user) {
    return (
      <div className="dashboard-loading">
        <span className="spinner" />
      </div>
    );
  }

  return (
    <>
      <style>{`
        /* ── Layout ─────────────────────────────────────────── */
        .dashboard {
          min-height: 100vh;
          background: #0f0f1a;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          padding: 2rem 1rem;
          font-family: 'Inter', sans-serif;
          position: relative;
          overflow: hidden;
        }

        .dashboard-loading {
          min-height: 100vh;
          display: flex;
          align-items: center;
          justify-content: center;
          background: #0f0f1a;
        }

        .spinner {
          width: 40px;
          height: 40px;
          border: 3px solid #2a2a3e;
          border-top-color: #7c6af7;
          border-radius: 50%;
          animation: spin 0.8s linear infinite;
        }

        @keyframes spin { to { transform: rotate(360deg); } }

        /* ── Fireworks ──────────────────────────────────────── */
        .fireworks-wrapper {
          position: absolute;
          inset: 0;
          pointer-events: none;
          z-index: 0;
        }

        .firework {
          position: absolute;
          width: 4px;
          height: 4px;
        }

        .firework-1 { top: 20%; left: 15%; }
        .firework-2 { top: 30%; right: 18%; }
        .firework-3 { top: 60%; left: 60%; }

        .particle {
          position: absolute;
          width: 3px;
          height: 3px;
          border-radius: 50%;
          background: hsl(calc(var(--i) * 45deg), 80%, 65%);
          animation: burst 2.4s ease-out infinite;
          animation-delay: calc(var(--i) * 0.1s + 0.8s);
          transform-origin: center;
          opacity: 0;
          filter: blur(0.5px);
        }

        @keyframes burst {
          0%   { transform: translate(0, 0) scale(1); opacity: 1; }
          60%  { opacity: 0.8; }
          100% {
            transform:
              translate(
                calc(cos(calc(var(--i) * 45deg)) * 40px),
                calc(sin(calc(var(--i) * 45deg)) * 40px)
              )
              scale(0);
            opacity: 0;
          }
        }

        /* ── AI Message ─────────────────────────────────────── */
        .ai-message {
          position: relative;
          z-index: 1;
          max-width: 600px;
          text-align: center;
          margin-bottom: 2rem;
          animation: fadeUp 0.6s ease both;
        }

        .ai-message h1 {
          font-size: 1.75rem;
          font-weight: 700;
          color: #e2e0ff;
          margin-bottom: 0.75rem;
        }

        .ai-message p {
          font-size: 1rem;
          color: #9d9bbf;
          line-height: 1.6;
        }

        @keyframes fadeUp {
          from { opacity: 0; transform: translateY(16px); }
          to   { opacity: 1; transform: translateY(0); }
        }

        /* ── Stats table ─────────────────────────────────────── */
        .stats-card {
          position: relative;
          z-index: 1;
          width: 100%;
          max-width: 600px;
          background: rgba(255, 255, 255, 0.04);
          backdrop-filter: blur(12px);
          border: 1px solid rgba(255, 255, 255, 0.08);
          border-radius: 16px;
          overflow: hidden;
          animation: fadeUp 0.6s 0.15s ease both;
        }

        .stats-card table {
          width: 100%;
          border-collapse: collapse;
        }

        .stats-card thead th {
          padding: 0.875rem 1.25rem;
          text-align: left;
          font-size: 0.7rem;
          font-weight: 600;
          letter-spacing: 0.08em;
          text-transform: uppercase;
          color: #5a5880;
          background: rgba(255,255,255,0.02);
          border-bottom: 1px solid rgba(255,255,255,0.06);
        }

        .stat-row td {
          padding: 0.875rem 1.25rem;
          border-bottom: 1px solid rgba(255,255,255,0.04);
          font-size: 0.9rem;
          transition: background 0.15s ease;
        }

        .stat-row:last-child td { border-bottom: none; }

        .stat-row:hover td {
          background: rgba(124, 106, 247, 0.08);
          cursor: default;
        }

        .stat-row--highlight .stat-value {
          color: #a5d6a7;
          font-weight: 600;
        }

        .stat-label { color: #7a78a0; }
        .stat-value { color: #e2e0ff; text-align: right; font-weight: 500; }

        /* ── Logout ──────────────────────────────────────────── */
        .logout-btn {
          position: relative;
          z-index: 1;
          margin-top: 1.5rem;
          padding: 0.5rem 1.5rem;
          background: transparent;
          border: 1px solid rgba(255,255,255,0.12);
          border-radius: 8px;
          color: #5a5880;
          font-size: 0.8rem;
          cursor: pointer;
          transition: all 0.2s ease;
          animation: fadeUp 0.6s 0.3s ease both;
        }

        .logout-btn:hover {
          border-color: #ef9a9a;
          color: #ef9a9a;
        }
      `}</style>

      <div className="dashboard">
        <Fireworks />

        {/* AI Message */}
        <div className="ai-message">
          <h1>Hey, {user.username} 👋</h1>
          <p>{loading ? 'Fetching your stats...' : aiMessage}</p>
        </div>

        {/* Stats table */}
        {!loading && stats && (
          <div className="stats-card">
            <table>
              <thead>
                <tr>
                  <th>Metric</th>
                  <th style={{ textAlign: 'right' }}>Value</th>
                </tr>
              </thead>
              <tbody>
                <StatRow
                  label="Total Inferences"
                  value={stats.analyticsCacheHitRate?.total ?? 0}
                />
                <StatRow
                  label="Cache Hit Rate"
                  value={`${stats.analyticsCacheHitRate?.hitRate ?? 0}%`}
                  highlight
                />
                <StatRow
                  label="Cache Hits (⚡ instant)"
                  value={stats.analyticsCacheHitRate?.cacheHits ?? 0}
                />
                {stats.analyticsRuntimeDistribution?.map((rt) => (
                  <StatRow
                    key={rt.runtime}
                    label={`Runtime — ${rt.runtime}`}
                    value={`${rt.count} req · avg ${rt.avgLatencyMs < 1 ? rt.avgLatencyMs.toFixed(2) : Math.round(rt.avgLatencyMs)}ms`}
                  />
                ))}
                {stats.analyticsTopDetections?.slice(0, 3).map((d) => (
                  <StatRow
                    key={d.label}
                    label={`Most detected — ${d.label}`}
                    value={`${d.count}× · ${(d.avgConfidence * 100).toFixed(1)}% conf`}
                  />
                ))}
              </tbody>
            </table>
          </div>
        )}

        <button className="logout-btn" onClick={logout}>
          Log out
        </button>
      </div>
    </>
  );
};

export default DashboardPage;
