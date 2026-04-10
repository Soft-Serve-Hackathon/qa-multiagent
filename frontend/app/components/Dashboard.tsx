'use client';

import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import {
  IconInbox, IconCpuChip, IconLink, IconTicket, IconBell, IconCheckCircle,
  IconArrowUpRight, IconArrowPath, IconExclamationTriangle,
} from './Icons';

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
  P1: { bg: 'bg-red-500/10',    text: 'text-red-600',    bar: 'bg-red-500',    label: 'P1 · Critical' },
  P2: { bg: 'bg-orange-500/10', text: 'text-orange-600', bar: 'bg-orange-400', label: 'P2 · High' },
  P3: { bg: 'bg-yellow-500/10', text: 'text-yellow-700', bar: 'bg-yellow-400', label: 'P3 · Medium' },
  P4: { bg: 'bg-slate-100',     text: 'text-slate-500',  bar: 'bg-slate-300',  label: 'P4 · Low' },
};

const STATUS_STYLES: Record<string, { dot: string; text: string; label: string }> = {
  received:     { dot: 'bg-blue-400',    text: 'text-blue-500',    label: 'Received' },
  triaging:     { dot: 'bg-yellow-400',  text: 'text-yellow-600',  label: 'Triaging' },
  deduplicated: { dot: 'bg-purple-400',  text: 'text-purple-500',  label: 'Deduplicated' },
  ticketed:     { dot: 'bg-indigo-400',  text: 'text-indigo-500',  label: 'Ticketed' },
  notified:     { dot: 'bg-cyan-400',    text: 'text-cyan-600',    label: 'Notified' },
  resolved:     { dot: 'bg-emerald-400', text: 'text-emerald-500', label: 'Resolved' },
};

// ─── Sub-components ───────────────────────────────────────────────────────────

function StatCard({
  label, value, sub, accent,
}: {
  label: string; value: string | number; sub?: string; accent?: string;
}) {
  return (
    <div className="bg-white rounded-2xl border border-slate-100 p-5 flex flex-col gap-1">
      <p className="text-xs font-medium tracking-widest uppercase text-slate-400">{label}</p>
      <p className={`text-[28px] font-semibold tracking-[-0.02em] leading-none mt-1 ${accent ?? 'text-slate-900'}`}>
        {value}
      </p>
      {sub && <p className="text-xs text-slate-400 mt-1 font-normal">{sub}</p>}
    </div>
  );
}

function SeverityBar({ severity, count, total }: { severity: string; count: number; total: number }) {
  const style = SEVERITY_STYLES[severity];
  const pct = total > 0 ? Math.round((count / total) * 100) : 0;
  return (
    <div className="flex items-center gap-3">
      <span className={`text-xs font-medium w-24 shrink-0 ${style.text}`}>{style.label}</span>
      <div className="flex-1 bg-slate-100 rounded-full h-1.5 overflow-hidden">
        <div className={`h-1.5 rounded-full transition-all duration-500 ${style.bar}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs text-slate-400 w-14 text-right shrink-0 tabular-nums">
        {count} <span className="text-slate-300">·</span> {pct}%
      </span>
    </div>
  );
}

function ModuleBar({ module, count, max }: { module: string; count: number; max: number }) {
  const pct = max > 0 ? Math.round((count / max) * 100) : 0;
  return (
    <div className="flex items-center gap-3">
      <span className="text-xs font-mono text-slate-600 w-28 shrink-0 truncate">{module}</span>
      <div className="flex-1 bg-slate-100 rounded-full h-1.5 overflow-hidden">
        <div className="h-1.5 rounded-full bg-indigo-400 transition-all duration-500" style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs text-slate-400 w-6 text-right shrink-0 tabular-nums">{count}</span>
    </div>
  );
}

function SeverityBadge({ severity }: { severity?: string }) {
  if (!severity) return <span className="text-slate-300 text-xs">—</span>;
  const style = SEVERITY_STYLES[severity];
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium ${style.bg} ${style.text}`}>
      {severity}
    </span>
  );
}

function StatusDot({ status }: { status: string }) {
  const style = STATUS_STYLES[status] ?? { dot: 'bg-slate-300', text: 'text-slate-400', label: status };
  return (
    <span className="inline-flex items-center gap-1.5">
      <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${style.dot}`} />
      <span className={`text-xs ${style.text}`}>{style.label}</span>
    </span>
  );
}

function SectionCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="bg-white rounded-2xl border border-slate-100 p-6 space-y-4">
      <h2 className="text-xs font-medium tracking-widest uppercase text-slate-400">{title}</h2>
      {children}
    </div>
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
    } catch (err) {
      const e = err as any;
      setError(e?.response?.data?.detail || 'Failed to load dashboard data');
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
    <div className="space-y-5">

      {/* ── Sub-header ───────────────────────────────────────────────────────── */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <p className="text-xs text-slate-400 font-normal">
          Live pipeline metrics · auto-refreshes every 15s
        </p>
        <div className="flex items-center gap-3">
          <span className="text-xs text-slate-300 tabular-nums">
            {lastRefresh.toLocaleTimeString()}
          </span>
          <button
            onClick={() => { setLoading(true); fetchStats(); }}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-[8px] border border-slate-200 text-slate-500 hover:text-slate-700 hover:border-slate-300 hover:bg-slate-50 transition-all duration-150"
          >
            <IconArrowPath className="w-3.5 h-3.5" />
            Refresh
          </button>
        </div>
      </div>

      {/* ── Error state ──────────────────────────────────────────────────────── */}
      {error && (
        <div className="rounded-[10px] bg-red-500/5 border border-red-200/60 px-4 py-3 flex items-start gap-2.5">
          <IconExclamationTriangle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-medium text-red-600">Could not load dashboard</p>
            <p className="text-xs text-red-400 mt-0.5">{error}</p>
          </div>
        </div>
      )}

      {/* ── Loading skeleton ──────────────────────────────────────────────────── */}
      {loading && !stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 animate-pulse">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="bg-slate-50 rounded-2xl border border-slate-100 p-5 h-24" />
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
                stats.pipeline_success_rate >= 0.9 ? 'text-emerald-600'
                : stats.pipeline_success_rate >= 0.7 ? 'text-yellow-600'
                : 'text-red-500'
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
              accent="text-indigo-600"
            />
          </div>

          {/* ── Middle row: severity + modules ────────────────────────────────── */}
          <div className="grid md:grid-cols-2 gap-4">
            <SectionCard title="Severity Distribution">
              {totalSeverity === 0 ? (
                <p className="text-sm text-slate-300">No triaged incidents yet</p>
              ) : (
                <div className="space-y-3">
                  {(['P1', 'P2', 'P3', 'P4'] as const).map(s => (
                    <SeverityBar key={s} severity={s} count={stats.severity_breakdown[s]} total={totalSeverity} />
                  ))}
                </div>
              )}
            </SectionCard>

            <SectionCard title="Top Affected Modules">
              {stats.top_modules.length === 0 ? (
                <p className="text-sm text-slate-300">No module data yet</p>
              ) : (
                <div className="space-y-3">
                  {stats.top_modules.map(m => (
                    <ModuleBar key={m.module} module={m.module} count={m.count} max={maxModule} />
                  ))}
                </div>
              )}
            </SectionCard>
          </div>

          {/* ── Pipeline stage breakdown ───────────────────────────────────────── */}
          <SectionCard title="Pipeline Stage Breakdown">
            <div className="grid grid-cols-3 sm:grid-cols-6 gap-3">
              {(
                [
                  ['received',     IconInbox],
                  ['triaging',     IconCpuChip],
                  ['deduplicated', IconLink],
                  ['ticketed',     IconTicket],
                  ['notified',     IconBell],
                  ['resolved',     IconCheckCircle],
                ] as const
              ).map(([key, StageIcon]) => {
                const val = stats.status_breakdown[key as keyof StatusBreakdown];
                const style = STATUS_STYLES[key];
                return (
                  <div
                    key={key}
                    className="flex flex-col items-center gap-2 p-3 rounded-[10px] bg-slate-50/80 border border-slate-100"
                  >
                    <StageIcon className={`w-4 h-4 ${style.text}`} />
                    <span className="text-[20px] font-semibold tracking-[-0.02em] text-slate-900 leading-none">
                      {val}
                    </span>
                    <span className="text-[10px] text-slate-400 capitalize text-center leading-tight">
                      {style.label}
                    </span>
                  </div>
                );
              })}
            </div>
          </SectionCard>

          {/* ── Recent incidents table ─────────────────────────────────────────── */}
          <div className="bg-white rounded-2xl border border-slate-100 overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
              <h2 className="text-xs font-medium tracking-widest uppercase text-slate-400">
                Recent Incidents
              </h2>
              <span className="text-xs text-slate-300">Last 20</span>
            </div>

            {stats.recent_incidents.length === 0 ? (
              <div className="px-6 py-12 text-center">
                <p className="text-slate-300 text-sm">No incidents yet.</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-slate-50">
                      {['Title', 'Severity', 'Module', 'Status', 'Confidence', 'Age', 'Ticket'].map(col => (
                        <th key={col} className="px-4 py-3 text-left text-[10px] font-medium tracking-widest uppercase text-slate-400">
                          {col}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-50">
                    {stats.recent_incidents.map(inc => (
                      <tr key={inc.trace_id} className="hover:bg-slate-50/60 transition-colors duration-100">
                        <td className="px-4 py-3 max-w-[220px]">
                          <div className="flex flex-col gap-0.5">
                            <span className="text-sm font-medium text-slate-800 truncate block" title={inc.title}>
                              {inc.title}
                            </span>
                            {inc.deduplicated && (
                              <span className="inline-flex items-center gap-1 text-[10px] text-purple-500 font-medium">
                                <IconLink className="w-3 h-3" /> deduplicated
                              </span>
                            )}
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          <SeverityBadge severity={inc.severity} />
                        </td>
                        <td className="px-4 py-3">
                          {inc.affected_module ? (
                            <span className="font-mono text-xs text-slate-600 bg-slate-100 px-1.5 py-0.5 rounded-md">
                              {inc.affected_module}
                            </span>
                          ) : (
                            <span className="text-slate-300 text-xs">—</span>
                          )}
                        </td>
                        <td className="px-4 py-3">
                          <StatusDot status={inc.status} />
                        </td>
                        <td className="px-4 py-3">
                          {inc.confidence_score != null ? (
                            <span className={`text-xs font-medium tabular-nums ${
                              inc.confidence_score >= 0.8 ? 'text-emerald-600'
                              : inc.confidence_score >= 0.5 ? 'text-yellow-600'
                              : 'text-red-500'
                            }`}>
                              {Math.round(inc.confidence_score * 100)}%
                            </span>
                          ) : (
                            <span className="text-slate-300 text-xs">—</span>
                          )}
                        </td>
                        <td className="px-4 py-3 text-xs text-slate-400 whitespace-nowrap tabular-nums">
                          {timeAgo(inc.created_at)}
                        </td>
                        <td className="px-4 py-3">
                          {inc.trello_card_url ? (
                            <a
                              href={inc.trello_card_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="inline-flex items-center gap-1 text-xs text-indigo-500 hover:text-indigo-700 font-medium transition-colors duration-150"
                            >
                              {inc.trello_card_id ? inc.trello_card_id.replace('mock-trello-', '#') : 'View'}
                              <IconArrowUpRight className="w-3 h-3" />
                            </a>
                          ) : (
                            <span className="text-slate-300 text-xs">—</span>
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
                  <span className="font-medium text-slate-600 tabular-nums">
                    {stats.avg_triage_ms >= 1000
                      ? `${(stats.avg_triage_ms / 1000).toFixed(2)}s`
                      : `${Math.round(stats.avg_triage_ms)}ms`}
                  </span>
                </span>
              )}
              {stats.avg_ticket_ms != null && (
                <span>
                  Avg ticket creation:{' '}
                  <span className="font-medium text-slate-600 tabular-nums">
                    {stats.avg_ticket_ms >= 1000
                      ? `${(stats.avg_ticket_ms / 1000).toFixed(2)}s`
                      : `${Math.round(stats.avg_ticket_ms)}ms`}
                  </span>
                </span>
              )}
              <span>
                Total processed:{' '}
                <span className="font-medium text-slate-600 tabular-nums">{stats.total_incidents}</span>
              </span>
            </div>
          )}
        </>
      )}
    </div>
  );
}