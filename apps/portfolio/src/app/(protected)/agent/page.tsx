'use client';

/**
 * AI Agent Page — Natural Language Interface
 *
 * Allows users to send prompts to the LangGraph agent in natural language.
 * Supports two modes:
 *
 * 1. Direct execution (require_approval: false)
 *    → Agent runs to completion immediately
 *
 * 2. Human-in-the-loop (require_approval: true)
 *    → Agent proposes a plan in natural language
 *    → User reads the plan and approves or rejects
 *    → Agent executes only after approval
 *
 * This is the pattern used in production agentic systems at big tech —
 * the agent proposes, the human approves, the agent executes.
 * No real-world action (GitHub issues, DB writes) happens without consent.
 *
 * Connects to: LangGraph Agent FastAPI service at :8003
 */

import { useState } from 'react';

// ── Types ──────────────────────────────────────────────────────────────────────

type AgentStatus = 'idle' | 'loading' | 'pending_approval' | 'completed' | 'rejected' | 'error';

interface AgentResponse {
  thread_id: string;
  status: string;
  plan: string | null;
  result: string | null;
  messages: { role: string; content: string }[];
}

// ── Example prompts for the demo ───────────────────────────────────────────────

const EXAMPLE_PROMPTS = [
  { label: '🔍 Check low confidence', prompt: 'Check the database for any detections with low confidence' },
  { label: '📋 Create sprint issues', prompt: 'Create the weekly issues for sprint 3' },
  { label: '📊 Analyze detections', prompt: 'What detections have confidence below 0.4?' },
];

// ── Main Component ─────────────────────────────────────────────────────────────

export default function AgentPage() {
  const [prompt, setPrompt] = useState('');
  const [requireApproval, setRequireApproval] = useState(true);
  const [status, setStatus] = useState<AgentStatus>('idle');
  const [response, setResponse] = useState<AgentResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const AGENT_URL = process.env.NEXT_PUBLIC_AGENT_URL || 'http://localhost:8003';

  // ── Send prompt to agent ─────────────────────────────────────────────────────

  const handleSubmit = async () => {
    if (!prompt.trim()) return;
    setStatus('loading');
    setResponse(null);
    setError(null);

    try {
      const res = await fetch(`${AGENT_URL}/agent/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt, require_approval: requireApproval }),
      });

      if (!res.ok) throw new Error(`Agent error: ${res.status}`);

      const data: AgentResponse = await res.json();
      setResponse(data);
      setStatus(data.status === 'pending_approval' ? 'pending_approval' : 'completed');
    } catch (err: any) {
      setError(err.message);
      setStatus('error');
    }
  };

  // ── Approve or reject HITL action ────────────────────────────────────────────

  const handleApproval = async (approved: boolean) => {
    if (!response?.thread_id) return;
    setStatus('loading');

    try {
      const res = await fetch(`${AGENT_URL}/agent/approve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          thread_id: response.thread_id,
          approved,
          feedback: approved ? undefined : 'Rejected by user',
        }),
      });

      if (!res.ok) throw new Error(`Approval error: ${res.status}`);

      const data: AgentResponse = await res.json();
      setResponse(data);
      setStatus(approved ? 'completed' : 'rejected');
    } catch (err: any) {
      setError(err.message);
      setStatus('error');
    }
  };

  // ── Reset ────────────────────────────────────────────────────────────────────

  const handleReset = () => {
    setStatus('idle');
    setResponse(null);
    setError(null);
    setPrompt('');
  };

  // ── Render ───────────────────────────────────────────────────────────────────

  return (
    <div className="w-full max-w-3xl flex flex-col items-center animate-fade-in-up mt-12">

      {/* Header */}
      <div className="text-center mb-10">
        <h1 className="text-4xl font-extrabold mb-4 text-white drop-shadow-md">
          AI Agent 🤖
        </h1>
        <p className="text-gray-300 text-lg leading-relaxed max-w-2xl mx-auto">
          Send natural language prompts to the LangGraph agent. With{' '}
          <span className="text-orange-400 font-semibold">Human-in-the-loop</span> enabled,
          the agent proposes a plan before taking any action — you approve or reject.
        </p>
      </div>

      {/* Input area */}
      {status === 'idle' || status === 'error' ? (
        <div className="w-full bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl p-6 shadow-2xl mb-6">

          {/* Example prompts */}
          <div className="flex flex-wrap gap-2 mb-4">
            {EXAMPLE_PROMPTS.map((ex) => (
              <button
                key={ex.label}
                onClick={() => setPrompt(ex.prompt)}
                className="text-xs px-3 py-1.5 rounded-full bg-white/10 hover:bg-orange-400/20 
                           border border-white/10 hover:border-orange-400/40 
                           text-gray-300 hover:text-orange-300 transition-all"
              >
                {ex.label}
              </button>
            ))}
          </div>

          {/* Prompt textarea */}
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Ask the agent anything... e.g. 'Create the weekly issues for sprint 3'"
            rows={4}
            className="w-full bg-black/30 border border-white/10 rounded-xl p-4 text-gray-100 
                       placeholder-gray-500 focus:outline-none focus:border-orange-400/50 
                       resize-none text-sm mb-4"
          />

          {/* HITL toggle */}
          <div className="flex items-center justify-between mb-4">
            <label className="flex items-center gap-3 cursor-pointer">
              <div
                onClick={() => setRequireApproval(!requireApproval)}
                className={`w-11 h-6 rounded-full transition-colors relative ${
                  requireApproval ? 'bg-orange-500' : 'bg-white/20'
                }`}
              >
                <div className={`absolute top-0.5 w-5 h-5 rounded-full bg-white shadow transition-transform ${
                  requireApproval ? 'translate-x-5' : 'translate-x-0.5'
                }`} />
              </div>
              <span className="text-sm text-gray-300">
                Human-in-the-loop{' '}
                <span className="text-xs text-gray-500">
                  {requireApproval ? '— agent proposes plan first' : '— agent executes directly'}
                </span>
              </span>
            </label>
          </div>

          {error && (
            <p className="text-red-400 text-sm mb-4">⚠️ {error}</p>
          )}

          <button
            onClick={handleSubmit}
            disabled={!prompt.trim()}
            className="w-full py-3 rounded-xl font-semibold text-sm transition-all
                       bg-orange-500 hover:bg-orange-400 text-white
                       disabled:opacity-40 disabled:cursor-not-allowed"
          >
            Send to Agent →
          </button>
        </div>
      ) : null}

      {/* Loading */}
      {status === 'loading' && (
        <div className="w-full bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl p-10 
                        flex flex-col items-center gap-4 shadow-2xl">
          <div className="w-10 h-10 border-2 border-orange-400 border-t-transparent rounded-full animate-spin" />
          <p className="text-gray-400 text-sm">Agent is thinking...</p>
        </div>
      )}

      {/* HITL — pending approval */}
      {status === 'pending_approval' && response && (
        <div className="w-full flex flex-col gap-4">
          <div className="bg-white/5 backdrop-blur-xl border border-orange-400/30 rounded-2xl p-6 shadow-2xl">
            <div className="flex items-center gap-2 mb-4">
              <span className="w-2 h-2 rounded-full bg-orange-400 animate-pulse" />
              <h2 className="text-sm font-semibold text-orange-300 uppercase tracking-wider">
                Agent Plan — Awaiting Approval
              </h2>
            </div>
            <p className="text-gray-200 text-sm leading-relaxed whitespace-pre-wrap">
              {response.plan}
            </p>
          </div>

          <div className="flex gap-3">
            <button
              onClick={() => handleApproval(true)}
              className="flex-1 py-3 rounded-xl font-semibold text-sm bg-green-500 
                         hover:bg-green-400 text-white transition-all"
            >
              ✅ Approve — Execute
            </button>
            <button
              onClick={() => handleApproval(false)}
              className="flex-1 py-3 rounded-xl font-semibold text-sm bg-red-500/80 
                         hover:bg-red-500 text-white transition-all"
            >
              ❌ Reject
            </button>
          </div>
        </div>
      )}

      {/* Completed */}
      {(status === 'completed' || status === 'rejected') && response && (
        <div className="w-full flex flex-col gap-4">

          {/* Plan (if HITL was used) */}
          {response.plan && (
            <div className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl p-6 shadow-2xl">
              <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
                Original Plan
              </h2>
              <p className="text-gray-400 text-sm leading-relaxed whitespace-pre-wrap">
                {response.plan}
              </p>
            </div>
          )}

          {/* Result */}
          <div className={`bg-white/5 backdrop-blur-xl border rounded-2xl p-6 shadow-2xl ${
            status === 'rejected' ? 'border-red-400/30' : 'border-green-400/30'
          }`}>
            <h2 className={`text-xs font-semibold uppercase tracking-wider mb-3 ${
              status === 'rejected' ? 'text-red-400' : 'text-green-400'
            }`}>
              {status === 'rejected' ? '❌ Rejected' : '✅ Result'}
            </h2>
            <p className="text-gray-200 text-sm leading-relaxed whitespace-pre-wrap">
              {response.result}
            </p>
          </div>

          <button
            onClick={handleReset}
            className="w-full py-3 rounded-xl font-semibold text-sm 
                       bg-white/10 hover:bg-white/20 text-gray-300 transition-all"
          >
            ← New Prompt
          </button>
        </div>
      )}
    </div>
  );
}
