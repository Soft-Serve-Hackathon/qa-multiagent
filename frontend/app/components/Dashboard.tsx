'use client';

import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';

// ─── Types ────────────────────────────────────────────────────────────────────

interface SeverityBreakdown { P1: number; P2: number; P3: number; P4: number; }
interface StatusBreakdown {
  received: number; triaging: number; deduplicated: number;
  ticketed: number; notified: number; resolved: number;
}
interface ModuleCount { module: string; count: number; }
interface RecentIncident {
  incident_id: number;
  trace_id: string;
  title: string;
  status: string;
  severity?: string;
  affected_module?: string;
  confidence_score?: number;
  trello_card_id?: string;
  trello_card_url?: string;
  deduplicated: boolean;
  created_at: string;
}
interface DashboardStats {
  total_incidents: number;
  severity_breakdown: SeverityBreakdown;
  status_breakdown: StatusBreakdown;
  top_modules: ModuleCount[];
  avg_triage_ms?: number;
  avg_ticket_ms?: number;
  deduplication_rate: number;
  recent_incidents: RecentIncident[];
  pipeline_success_rate: number;
}

// ─── Constants ────────────────────────────────────────────────────────────────

const SEVERITY_STYLES: Record<string, { bg: string; text: string; bar: string; label: string }> = {
  P1: { bg: 'bg-red-100',    text: 'text-red-700',    bar: 'bg-red-500',    label: 'P1 Critical' },
  P2: { bg: 'bg-orange-100', text: 'text-orange-700', bar: 'bg-orange-400', label: 'P2 High' },
  P3: { bg: 'bg-yellow-100', text: 'text-yellow-700', bar: 'bg-yellow-400', label: 'P3 Medium' },
  P4: { bg: 'bg-slate-100',  text: 'text-slate-600',  bar: 'bg-slate-400',  label: 'P4 Low' },
};

const STATUS_STYLES: Record<string, { dot: string; label: string }> = {
  received:     { dot: 'bg-blue-400',    label: 'Received' },
  triaging:     { dot: 'bg-yellow-400',  label: 'Triaging' },
  deduplicated: { dot: 'bg-purple-400',  label: 'Deduplicated' },
  ticketed:     { dot: 'bg-indigo-400',  label: 'Ticketed' },
  notified:     { dot: 'bg-green-400',   label: 'Notified' },
  resolved:     { dot: 'bg-emerald-500', label: 'Resolved' },
};

// ─── Sub-components ───────────────────────────────────────────────────────────

function StatCard({
  label, value, sub, accent,
}: {
  label: string; value: string | number; sub?: string; accent?: string;
}) {
  return (
    <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-5 flex flex-col gap-1">
      <p className="text-xs font-medium text-slate-500 uppercase tracking-wide">{label}</p>
      <p className={`text-3xl font-bold ${accent ?? 'text-slate-900'}`}>{value}</p>
      {sub && <p className="text-xs text-slate-400 mt-0.5">{sub}</p>}
    </div>
  );
}

function SeverityBar({ severity, count, total }: { severity: string; count: number; total: number }) {
  const style = SEVERITY_STYLES[severity];
  const pct = total > 0 ? Math.round((count / total) * 100) : 0;
  return (
    <div className="flex items-center gap-3">
      <span className={`text-xs font-bold w-20 shrink-0 ${style.text}`}>{style.label}</span>
      <div className="flex-1 bg-slate-100 rounded-full h-2 overflow-hidden">
        <div className={`h-2 rounded-full transition-all duration-500 ${style.bar}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs text-slate-500 w-12 text-right shrink-0">
        {count} <span className="text-slate-400">({pct}%)</span>
      </span>
    </div>
  );
}

function ModuleBar({ module, count, max }: { module: string; count: number; max: number }) {
  const pct = max > 0 ? Math.round((count / max) * 100) : 0;
  return (
    <div className="flex items-center gap-3">
      <span className="text-xs font-mono text-slate-700 w-24 shrink-0 truncate">{module}</span>
      <div className="flex-1 bg-slate-100 rounded-full h-2 overflow-hidden">
        <div className="h-2 rounded-full bg-blue-400 transition-all duration-500" style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs text-slate-500 w-6 text-right shrink-0">{count}</span>
    </div>
  );
}

function SeverityBadge({ severity }: { severity?: string }) {
  if (!severity) return <span className="text-slate-400 text-xs">—</span>;
  const style = SEVERITY_STYLES[severity];
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-bold ${style.bg} ${style.text}`}>
      {severity}
    </span>
  );
}

function StatusDot({ status }: { status: string }) {
  const style = STATUS_STYLES[status] ?? { dot: 'bg-slate-300', label: status };
  return (
    <span className="inline-flex items-center gap-1.5">
      <span className={`w-2 h-2 rounded-full shrink-0 ${style.dot}`} />
      <span className="text-xs text-slate-600 capitalize">{style.label}</span>
    </span>
  );
}

function timeAgo(isoDate: string): string {
  const diff = Date.now() - new Date(isoDate).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

// ─── Main Component ───────────────────────────────────────────────────────────

export default function Dashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());

  const fetchStats = useCallback(async () => {
    try {
      const res = await axios.get('/api/dashboard/stats', { timeout: 8000 });
      setStats(res.data);
      setError(null);
      setLastRefresh(new Date());
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, 15000);
    return () => clearInterval(interval);
  }, [fetchStats]);

  const totalSeverity =
    (stats?.severity_breakdown.P1 ?? 0) +
    (stats?.severity_breakdown.P2 ?? 0) +
    (stats?.severity_breakdown.P3 ?? 0) +
    (stats?.severity_breakdown.P4 ?? 0);

  const maxModule = stats?.top_modules[0]?.count ?? 1;

  return (
    <div className="space-y-6">

      {/* ── Sub-header ─────────────────────────────────────────────────────── */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <p className="text-sm text-slate-500">
          Live pipeline metrics · auto-refreshes every 15s
        </p>
        <div className="flex items-center gap-3">
          <span className="text-xs text-slate-400">
            Last update: {lastRefresh.toLocaleTimeString()}
          </span>
          <button
            onClick={() => { setLoading(true); fetchStats(); }}
            className="px-3 py-1.5 text-sm rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 font-medium transition-colors"
          >
            ↻ Refresh
          </button>
        </div>
      </div>

      {/* ── Error state ──────────────────────────────────────────────────────── */}
      {error && (
        <div className="alert alert-error flex items-start gap-3">
          <span className="text-red-500 text-lg leading-5 shrink-0">⚠</span>
          <div>
            <p className="font-semibold text-sm">Could not load dashboard</p>
            <p className="text-sm mt-0.5">{error}</p>
          </div>
        </div>
      )}

      {/* ── Loading skeleton ──────────────────────────────────────────────────── */}
      {loading && !stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 animate-pulse">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="bg-white rounded-2xl border border-slate-100 p-5 h-24" />
          ))}
        </div>
      )}

      {stats && (
        <>
          {/* ── KPI cards ─────────────────────────────────────────────────────── */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatCard label="Total Incidents" value={stats.total_incidents} sub="all time" />
            <StatCard
              label="Success Rate"
              value={`${Math.round(stats.pipeline_success_rate * 100)}%`}
              sub="notified + resolved"
              accent={
                stats.pipeline_success_rate >= 0.9
                  ? 'text-green-600'
                  : stats.pipeline_success_rate >= 0.7
                  ? 'text-yellow-600'
                  : 'text-red-600'
              }
            />
            <StatCard
              label="Dedup Rate"
              value={`${Math.round(stats.deduplication_rate * 100)}%`}
              sub="duplicates caught"
              accent="text-purple-600"
            />
            <StatCard
              label="Avg Triage"
              value={
                stats.avg_triage_ms != null
                  ? stats.avg_triage_ms >= 1000
                    ? `${(stats.avg_triage_ms / 1000).toFixed(1)}s`
                    : `${Math.round(stats.avg_triage_ms)}ms`
                  : '—'
              }
              sub="AI analysis time"
              accent="text-blue-600"
            />
          </div>

          {/* ── Middle row: severity + modules ────────────────────────────────── */}
          <div className="grid md:grid-cols-2 gap-4">
            <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-6 space-y-4">
              <h2 className="text-sm font-semibold text-slate-700 uppercase tracking-wide">
                Severity Distribution
              </h2>
              {totalSeverity === 0 ? (
                <p className="text-sm text-slate-400 italic">No triaged incidents yet</p>
              ) : (
                <div className="space-y-3">
                  {(['P1', 'P2', 'P3', 'P4'] as const).map(s => (
                    <SeverityBar key={s} severity={s} count={stats.severity_breakdown[s]} total={totalSeverity} />
                  ))}
                </div>
              )}
            </div>

            <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-6 space-y-4">
              <h2 className="text-sm font-semibold text-slate-700 uppercase tracking-wide">
                Top Affected Modules
              </h2>
              {stats.top_modules.length === 0 ? (
                <p className="text-sm text-slate-400 italic">No module data yet</p>
              ) : (
                <div className="space-y-3">
                  {stats.top_modules.map(m => (
                    <ModuleBar key={m.module} module={m.module} count={m.count} max={maxModule} />
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* ── Pipeline stage breakdown ───────────────────────────────────────── */}
          <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-6">
            <h2 className="text-sm font-semibold text-slate-700 uppercase tracking-wide mb-4">
              Pipeline Stage Breakdown
            </h2>
            <div className="grid grid-cols-3 sm:grid-cols-6 gap-3">
              {(
                [
                  ['received',     '📥'],
                  ['triaging',     '🤖'],
                  ['deduplicated', '🔗'],
                  ['ticketed',     '🎫'],
                  ['notified',     '📢'],
                  ['resolved',     '✅'],
                ] as const
              ).map(([key, icon]) => {
                const val = stats.status_breakdown[key as keyof StatusBreakdown];
                const style = STATUS_STYLES[key];
                return (
                  <div key={key} className="flex flex-col items-center gap-1 p-3 rounded-xl bg-slate-50 border border-slate-100">
                    <span className="text-xl">{icon}</span>
                    <span className="text-xl font-bold text-slate-900">{val}</span>
                    <span className="text-xs text-slate-500 capitalize">{style.label}</span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* ── Recent incidents table ─────────────────────────────────────────── */}
          <div className="bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
              <h2 className="text-sm font-semibold text-slate-700 uppercase tracking-wide">Recent Incidents</h2>
              <span className="text-xs text-slate-400">Last 20</span>
            </div>

            {stats.recent_incidents.length === 0 ? (
              <div className="px-6 py-12 text-center">
                <p className="text-slate-400 text-sm">No incidents yet.</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="bg-slate-50 text-xs text-slate-500 uppercase tracking-wide">
                      <th className="px-4 py-3 text-left font-medium">Title</th>
                      <th className="px-4 py-3 text-left font-medium">Severity</th>
                      <th className="px-4 py-3 text-left font-medium">Module</th>
                      <th className="px-4 py-3 text-left font-medium">Status</th>
                      <th className="px-4 py-3 text-left font-medium">Confidence</th>
                      <th className="px-4 py-3 text-left font-medium">Age</th>
                      <th className="px-4 py-3 text-left font-medium">Ticket</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-50">
                    {stats.recent_incidents.map(inc => (
                      <tr key={inc.trace_id} className="hover:bg-slate-50 transition-colors">
                        <td className="px-4 py-3 max-w-[220px]">
                          <div className="flex flex-col gap-0.5">
                            <span className="font-medium text-slate-900 truncate block" title={inc.title}>
                              {inc.title}
                            </span>
                            {inc.deduplicated && (
                              <span className="inline-flex items-center gap-1 text-xs text-purple-600 font-medium">
                                🔗 deduplicated
                              </span>
                            )}
                          </div>
                        </td>
                        <td className="px-4 py-3"><SeverityBadge severity={inc.severity} /></td>
                        <td className="px-4 py-3">
                          {inc.affected_module ? (
                            <span className="font-mono text-xs text-slate-700 bg-slate-100 px-1.5 py-0.5 rounded">
                              {inc.affected_module}
                            </span>
                          ) : (
                            <span className="text-slate-400 text-xs">—</span>
                          )}
                        </td>
                        <td className="px-4 py-3"><StatusDot status={inc.status} /></td>
                        <td className="px-4 py-3">
                          {inc.confidence_score != null ? (
                            <span className={`text-xs font-semibold ${
                              inc.confidence_score >= 0.8 ? 'text-green-600'
                              : inc.confidence_score >= 0.5 ? 'text-yellow-600'
                              : 'text-red-500'
                            }`}>
                              {Math.round(inc.confidence_score * 100)}%
                            </span>
                          ) : (
                            <span className="text-slate-400 text-xs">—</span>
                          )}
                        </td>
                        <td className="px-4 py-3 text-xs text-slate-400 whitespace-nowrap">
                          {timeAgo(inc.created_at)}
                        </td>
                        <td className="px-4 py-3">
                          {inc.trello_card_url ? (
                            <a
                              href={inc.trello_card_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="inline-flex items-center gap-1 text-xs text-blue-600 hover:text-blue-800 font-medium"
                            >
                              {inc.trello_card_id ? inc.trello_card_id.replace('mock-trello-', '#') : 'View'} ↗
                            </a>
                          ) : (
                            <span className="text-slate-400 text-xs">—</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* ── Footer latency note ────────────────────────────────────────────── */}
          {(stats.avg_triage_ms != null || stats.avg_ticket_ms != null) && (
            <div className="flex flex-wrap gap-6 px-1 pb-2 text-xs text-slate-400">
              {stats.avg_triage_ms != null && (
                <span>
                  Avg AI triage:{' '}
                  <span className="font-semibold text-slate-600">
                    {stats.avg_triage_ms >= 1000
                      ? `${(stats.avg_triage_ms / 1000).toFixed(2)}s`
                      : `${Math.round(stats.avg_triage_ms)}ms`}
                  </span>
                </span>
              )}
              {stats.avg_ticket_ms != null && (
                <span>
                  Avg ticket creation:{' '}
                  <span className="font-semibold text-slate-600">
                    {stats.avg_ticket_ms >= 1000
                      ? `${(stats.avg_ticket_ms / 1000).toFixed(2)}s`
                      : `${Math.round(stats.avg_ticket_ms)}ms`}
                  </span>
                </span>
              )}
              <span>Total processed: <span className="font-semibold text-slate-600">{stats.total_incidents}</span></span>
            </div>
          )}
        </>
      )}
    </div>
  );
}
