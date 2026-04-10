'use client';

import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import {
  IconInbox, IconCpuChip, IconBeaker, IconWrench, IconTicket, IconBell, IconCheckCircle,
  IconCheck, IconMinus, IconXMark, IconChevronDown, IconClipboard,
  IconArrowUpRight, IconArrowPath, IconExclamationTriangle, IconSpinner,
} from './Icons';

// ─── Types ────────────────────────────────────────────────────────────────────

interface StatusTrackerProps {
  incidentId: number;
  traceId: string;
  onReset: () => void;
}

interface IncidentStatus {
  incident_id: number;
  trace_id: string;
  title: string;
  status: string;
  severity?: string;
  affected_module?: string;
  confidence_score?: number;
  technical_summary?: string;
  suggested_files?: string[];
  trello_card_id?: string;
  trello_card_url?: string;
  deduplicated?: boolean;
  linked_ticket_id?: number;
}

interface ObsEvent {
  id: number;
  stage: string;
  status: string;
  duration_ms: number;
  metadata: Record<string, any>;
  created_at: string;
}

type StageState = 'pending' | 'active' | 'done' | 'skipped' | 'error';

// ─── Pipeline Definition ─────────────────────────────────────────────────────

const PIPELINE_STAGES = [
  {
    key: 'ingest',
    label: 'Ingest & Validate',
    Icon: IconInbox,
    description: 'Validates input, detects prompt injection, assigns trace ID',
  },
  {
    key: 'triage',
    label: 'AI Triage',
    Icon: IconCpuChip,
    description: 'Claude analyzes the incident and searches the Medusa.js codebase',
  },
  {
    key: 'qa_scope',
    label: 'QA Scope',
    Icon: IconBeaker,
    description: 'Evaluates test coverage and proposes regression tests',
  },
  {
    key: 'fix_recommendation',
    label: 'Fix Recommendation',
    Icon: IconWrench,
    description: 'Proposes a concrete fix with risk assessment',
  },
  {
    key: 'ticket',
    label: 'Ticket Creation',
    Icon: IconTicket,
    description: 'Checks for duplicates and creates enriched Trello card',
  },
  {
    key: 'notify',
    label: 'Notifications',
    Icon: IconBell,
    description: 'Sends Slack alert to team and confirmation email to reporter',
  },
  {
    key: 'resolved',
    label: 'Resolved',
    Icon: IconCheckCircle,
    description: 'Incident resolved — resolution email sent to reporter',
  },
];

const TERMINAL_INCIDENT_STATUSES = ['notified', 'resolved', 'deduplicated', 'error'];

const SEVERITY_CONFIG: Record<string, { bg: string; text: string; border: string; label: string }> = {
  P1: { bg: 'bg-red-500/10',    text: 'text-red-600',    border: 'border-red-200',    label: 'P1 · Critical' },
  P2: { bg: 'bg-orange-500/10', text: 'text-orange-600', border: 'border-orange-200', label: 'P2 · High' },
  P3: { bg: 'bg-yellow-500/10', text: 'text-yellow-700', border: 'border-yellow-200', label: 'P3 · Medium' },
  P4: { bg: 'bg-slate-100',     text: 'text-slate-500',  border: 'border-slate-200',  label: 'P4 · Low' },
};

// ─── Helpers ─────────────────────────────────────────────────────────────────

function fmtDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}

function getStageState(stageKey: string, events: ObsEvent[], isComplete: boolean): StageState {
  const event = events.find(e => e.stage === stageKey);
  if (event) {
    if (['success', 'deduplicated'].includes(event.status)) return 'done';
    if (event.status === 'skipped') return 'skipped';
    if (event.status === 'error') return 'error';
  }
  if (isComplete) return 'pending';
  const stageIdx = PIPELINE_STAGES.findIndex(s => s.key === stageKey);
  const allPriorSettled = PIPELINE_STAGES.slice(0, stageIdx).every(s =>
    events.some(e => e.stage === s.key)
  );
  return allPriorSettled ? 'active' : 'pending';
}

function stageClasses(state: StageState) {
  const base = 'relative flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center transition-all duration-300';
  switch (state) {
    case 'done':    return `${base} bg-emerald-500/15 text-emerald-600 ring-1 ring-emerald-300`;
    case 'skipped': return `${base} bg-amber-500/10 text-amber-600 ring-1 ring-amber-200`;
    case 'error':   return `${base} bg-red-500/10 text-red-500 ring-1 ring-red-200`;
    case 'active':  return `${base} bg-indigo-500/10 text-indigo-600 ring-2 ring-indigo-300 animate-pulse`;
    default:        return `${base} bg-slate-100 text-slate-300`;
  }
}

function connectorClass(state: StageState) {
  switch (state) {
    case 'done':    return 'bg-emerald-200';
    case 'skipped': return 'bg-amber-200';
    case 'error':   return 'bg-red-200';
    case 'active':  return 'bg-indigo-200';
    default:        return 'bg-slate-100';
  }
}

// ─── Stage Detail Renderers ───────────────────────────────────────────────────

function IngestDetail({ meta }: { meta: Record<string, any> }) {
  return (
    <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
      <MetaRow label="Attachment" value={meta.attachment_type || 'none'} />
      <MetaRow label="Injection check" value={meta.injection_check === 'passed' ? 'passed' : 'checked'} />
    </div>
  );
}

function TriageDetail({ meta, incident }: { meta: Record<string, any>; incident: IncidentStatus | null }) {
  return (
    <div className="space-y-3">
      <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
        <MetaRow label="Model" value={meta.model || 'claude-sonnet-4-6'} />
        <MetaRow label="Severity" value={meta.severity_detected} />
        <MetaRow label="Module" value={meta.module_detected} />
        <MetaRow label="Confidence" value={meta.confidence != null ? `${Math.round(meta.confidence * 100)}%` : undefined} />
        <MetaRow label="Files found" value={meta.files_found} />
        <MetaRow label="Reasoning steps" value={meta.reasoning_steps} />
      </div>
      {incident?.technical_summary && (
        <div className="bg-white rounded-[8px] p-2.5 border border-slate-200">
          <p className="text-[10px] font-medium tracking-widest uppercase text-slate-400 mb-1.5">Technical Summary</p>
          <p className="text-xs text-slate-700 leading-relaxed">{incident.technical_summary}</p>
        </div>
      )}
      {incident?.suggested_files && incident.suggested_files.length > 0 && (
        <div>
          <p className="text-[10px] font-medium tracking-widest uppercase text-slate-400 mb-1.5">Suggested files</p>
          <div className="space-y-0.5">
            {incident.suggested_files.map(f => (
              <div key={f} className="font-mono text-xs bg-slate-100 text-slate-700 px-2 py-0.5 rounded-md truncate">{f}</div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function QaDetail({ meta }: { meta: Record<string, any> }) {
  if (meta.error) return <ErrorDetail message={meta.error} />;
  return (
    <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
      <MetaRow label="Test coverage" value={meta.reproduced ? 'existing test found' : 'no coverage — test proposed'} />
      <MetaRow label="Failing tests" value={meta.failing_tests_count} />
      <MetaRow label="New tests proposed" value={meta.new_tests_count} />
      <MetaRow label="Coverage files" value={meta.coverage_files_found} />
      <MetaRow label="Module" value={meta.module} />
    </div>
  );
}

function FixDetail({ meta }: { meta: Record<string, any> }) {
  if (meta.error) return <ErrorDetail message={meta.error} />;
  const riskConfig: Record<string, string> = {
    low:    'text-emerald-600 bg-emerald-500/10',
    medium: 'text-amber-600 bg-amber-500/10',
    high:   'text-red-600 bg-red-500/10',
  };
  const riskClass = riskConfig[meta.risk_level] || 'text-slate-600 bg-slate-100';
  return (
    <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
      <div className="col-span-2 flex items-center gap-2">
        <span className="text-slate-400">Risk level</span>
        <span className={`px-2 py-0.5 rounded-md font-medium text-xs ${riskClass}`}>
          {meta.risk_level || '—'}
        </span>
      </div>
      <MetaRow label="Proposed files" value={meta.proposed_files_count} />
      <MetaRow label="Module" value={meta.module} />
    </div>
  );
}

function TicketDetail({ meta }: { meta: Record<string, any> }) {
  const isDedupEvent = meta.similarity_score != null;
  if (isDedupEvent) {
    const simPct = Math.round(meta.similarity_score * 100);
    const threshPct = meta.threshold != null ? Math.round(meta.threshold * 100) : 75;
    const cardUrl = meta.linked_card_url || meta.card_url;
    return (
      <div className="space-y-2.5">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-xs font-medium text-amber-700 bg-amber-500/10 border border-amber-200 px-2 py-0.5 rounded-md">
            Deduplicated
          </span>
          <span className="text-xs text-slate-400">
            {simPct}% match · {threshPct}% threshold
          </span>
        </div>
        <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
          <MetaRow label="Matched card" value={meta.linked_card_id} />
          <MetaRow label="Internal ticket" value={meta.linked_ticket_id ? `#${meta.linked_ticket_id}` : undefined} />
          <MetaRow label="Mode" value={meta.mock ? 'mock' : 'real'} />
        </div>
        {cardUrl && (
          <a
            href={cardUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 text-xs text-amber-600 hover:text-amber-800 font-medium transition-colors duration-150"
          >
            Open original Trello card <IconArrowUpRight className="w-3 h-3" />
          </a>
        )}
      </div>
    );
  }
  return (
    <div className="space-y-2.5">
      <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
        {meta.card_id ? <MetaRow label="Card ID" value={meta.card_id} /> : null}
        <MetaRow label="QA included" value={meta.qa_included ? 'yes' : '—'} />
        <MetaRow label="Fix included" value={meta.fix_included ? 'yes' : '—'} />
        <MetaRow label="Mode" value={meta.mock ? 'mock' : 'real'} />
      </div>
      {meta.card_url && (
        <a
          href={meta.card_url}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1 text-xs text-indigo-500 hover:text-indigo-700 font-medium transition-colors duration-150"
        >
          Open Trello card <IconArrowUpRight className="w-3 h-3" />
        </a>
      )}
    </div>
  );
}

function NotifyDetail({ meta }: { meta: Record<string, any> }) {
  return (
    <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
      <MetaRow label="Slack" value={meta.slack_ok ? 'sent' : 'failed'} />

      <MetaRow label="Mode" value={meta.mock ? 'mock' : 'real'} />
    </div>
  );
}

function ResolvedDetail({ meta }: { meta: Record<string, any> }) {
  return (
    <div className="text-xs">
      <MetaRow label="Resolved at" value={meta.resolved_at ? new Date(meta.resolved_at).toLocaleString() : undefined} />
    </div>
  );
}

function ErrorDetail({ message }: { message: string }) {
  return (
    <p className="text-xs text-red-500 bg-red-500/5 border border-red-200/60 rounded-[8px] p-2.5 font-mono break-all">
      {message}
    </p>
  );
}

function MetaRow({ label, value }: { label: string; value: any }) {
  if (value == null || value === '') return null;
  return (
    <>
      <span className="text-slate-400 truncate">{label}</span>
      <span className="text-slate-700 font-medium truncate">{String(value)}</span>
    </>
  );
}

function StageDetailContent({
  stageKey, meta, incident,
}: {
  stageKey: string;
  meta: Record<string, any>;
  incident: IncidentStatus | null;
}) {
  switch (stageKey) {
    case 'ingest':             return <IngestDetail meta={meta} />;
    case 'triage':             return <TriageDetail meta={meta} incident={incident} />;
    case 'qa_scope':           return <QaDetail meta={meta} />;
    case 'fix_recommendation': return <FixDetail meta={meta} />;
    case 'ticket':             return <TicketDetail meta={meta} />;
    case 'notify':             return <NotifyDetail meta={meta} />;
    case 'resolved':           return <ResolvedDetail meta={meta} />;
    default:                   return null;
  }
}

// ─── Progress Bar ─────────────────────────────────────────────────────────────

function PipelineProgress({ events, isComplete }: { events: ObsEvent[]; isComplete: boolean }) {
  const total = PIPELINE_STAGES.length - 1;
  const done = events.filter(e =>
    ['success', 'deduplicated', 'skipped'].includes(e.status) && e.stage !== 'resolved'
  ).length;
  const pct = isComplete ? 100 : Math.round((done / total) * 100);

  return (
    <div className="space-y-1.5">
      <div className="flex justify-between text-xs text-slate-400">
        <span>{isComplete ? 'Pipeline complete' : `${done} / ${total} stages`}</span>
        <span className="tabular-nums">{pct}%</span>
      </div>
      <div className="h-1 bg-slate-100 rounded-full overflow-hidden">
        <div
          className="h-full bg-gradient-to-r from-indigo-500 to-emerald-500 rounded-full transition-all duration-700 ease-out"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

// ─── Stage Card ───────────────────────────────────────────────────────────────

function StageCard({
  stage, state, event, incident, isLast, defaultOpen,
}: {
  stage: typeof PIPELINE_STAGES[0];
  state: StageState;
  event: ObsEvent | undefined;
  incident: IncidentStatus | null;
  isLast: boolean;
  defaultOpen: boolean;
}) {
  const [expanded, setExpanded] = useState(defaultOpen);

  const stateLabel: Record<StageState, string> = {
    pending: 'Waiting',
    active:  'Running',
    done:    event?.status === 'deduplicated' ? 'Deduplicated' : 'Done',
    skipped: 'Skipped',
    error:   'Error',
  };

  const stateTextColor: Record<StageState, string> = {
    pending: 'text-slate-300',
    active:  'text-indigo-500',
    done:    'text-emerald-600',
    skipped: 'text-amber-500',
    error:   'text-red-500',
  };

  const hasDetail = state === 'done' || state === 'skipped' || state === 'error';

  return (
    <div className="flex items-start gap-3">
      {/* Left: circle + connector */}
      <div className="flex flex-col items-center">
        <div className={stageClasses(state)}>
          {state === 'active'  ? <IconSpinner className="w-3.5 h-3.5" />  :
           state === 'done'    ? <IconCheck   className="w-3.5 h-3.5" />  :
           state === 'skipped' ? <IconMinus   className="w-3.5 h-3.5" />  :
           state === 'error'   ? <IconXMark   className="w-3.5 h-3.5" />  :
                                 <stage.Icon  className="w-3.5 h-3.5" />}
        </div>
        {!isLast && (
          <div className={`w-px h-7 mt-1 rounded-full transition-colors duration-500 ${connectorClass(state)}`} />
        )}
      </div>

      {/* Right: content */}
      <div className="flex-1 pb-5 min-w-0">
        <div
          className={`flex items-start justify-between gap-2 ${hasDetail ? 'cursor-pointer' : ''}`}
          onClick={() => hasDetail && setExpanded(v => !v)}
        >
          <div className="min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <span className={`text-xs font-medium ${state === 'pending' ? 'text-slate-400' : 'text-slate-800'}`}>
                {stage.label}
              </span>
              <span className={`text-[10px] font-medium ${stateTextColor[state]}`}>
                {stateLabel[state]}
                {state === 'active' && (
                  <span className="ml-0.5 animate-pulse">…</span>
                )}
              </span>
              {event?.duration_ms != null && (
                <span className="text-[10px] text-slate-300 tabular-nums">{fmtDuration(event.duration_ms)}</span>
              )}
            </div>
            {(state === 'active' || state === 'pending') && (
              <p className="text-[10px] text-slate-400 mt-0.5 leading-relaxed">{stage.description}</p>
            )}
          </div>
          {hasDetail && (
            <IconChevronDown className={`w-3.5 h-3.5 text-slate-300 flex-shrink-0 transition-transform duration-200 ${expanded ? 'rotate-180' : ''}`} />
          )}
        </div>

        {/* Inline key metrics for done stages (collapsed) */}
        {state === 'done' && event && !expanded && (
          <div className="mt-1 flex flex-wrap gap-x-3 gap-y-0.5">
            <StageInlineSummary stageKey={stage.key} meta={event.metadata} />
          </div>
        )}

        {/* Expanded detail */}
        {hasDetail && expanded && event && (
          <div className="mt-2 bg-slate-50/80 border border-slate-100 rounded-[10px] p-3">
            <StageDetailContent stageKey={stage.key} meta={event.metadata} incident={incident} />
          </div>
        )}
      </div>
    </div>
  );
}

// ─── Inline summary (collapsed view) ─────────────────────────────────────────

function StageInlineSummary({ stageKey, meta }: { stageKey: string; meta: Record<string, any> }) {
  const chip = (text: string, color = 'text-slate-400') => (
    <span key={text} className={`text-[10px] ${color}`}>{text}</span>
  );

  switch (stageKey) {
    case 'ingest':
      return <>{chip(`attachment: ${meta.attachment_type || 'none'}`)}</>;
    case 'triage':
      return <>
        {meta.severity_detected && chip(meta.severity_detected, 'text-orange-500 font-medium')}
        {meta.module_detected && chip(`module: ${meta.module_detected}`)}
        {meta.confidence != null && chip(`${Math.round(meta.confidence * 100)}% confidence`)}
        {meta.files_found != null && chip(`${meta.files_found} files`)}
      </>;
    case 'qa_scope':
      return <>
        {chip(meta.reproduced ? 'existing test found' : 'no prior coverage', meta.reproduced ? 'text-green-600' : 'text-slate-500')}
        {meta.new_tests_count > 0 && chip(`${meta.new_tests_count} test(s) proposed`, 'text-cyan-600')}
      </>;
    case 'fix_recommendation':
      return <>
        {meta.risk_level && chip(`risk: ${meta.risk_level}`,
          meta.risk_level === 'high'   ? 'text-red-500 font-medium'
          : meta.risk_level === 'medium' ? 'text-amber-500'
          : 'text-emerald-600'
        )}
        {meta.proposed_files_count > 0 && chip(`${meta.proposed_files_count} file(s)`)}
      </>;
    case 'ticket':
      return <>
        {meta.linked_card_id ? chip(`linked to ${meta.linked_card_id}`, 'text-amber-500') : chip('card created', 'text-emerald-600')}
        {meta.similarity_score != null && chip(`${Math.round(meta.similarity_score * 100)}% match`)}
      </>;
    case 'notify':
      return <>
        {chip(`slack: ${meta.slack_ok ? 'sent' : 'failed'}`, meta.slack_ok ? 'text-green-600' : 'text-red-500')}
      </>;
    default:
      return null;
  }
}

// ─── Main component ───────────────────────────────────────────────────────────

export default function StatusTracker({ incidentId, traceId, onReset }: StatusTrackerProps) {
  const [incident, setIncident] = useState<IncidentStatus | null>(null);
  const [events, setEvents] = useState<ObsEvent[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const isComplete = incident ? TERMINAL_INCIDENT_STATUSES.includes(incident.status) : false;

  const fetchData = useCallback(async () => {
    try {
      const [incRes, evRes] = await Promise.all([
        axios.get(`/api/incidents/${incidentId}`, { timeout: 5000 }),
        axios.get(`/api/observability/events?trace_id=${traceId}&limit=20`, { timeout: 5000 }),
      ]);
      setIncident(incRes.data);
      setEvents(evRes.data.events ?? []);
      setError(null);
    } catch {
      setError('Failed to fetch status — retrying…');
    }
  }, [incidentId, traceId]);

  useEffect(() => {
    fetchData();
    const interval = setInterval(() => { if (!isComplete) fetchData(); }, 2000);
    return () => clearInterval(interval);
  }, [fetchData, isComplete]);

  const handleCopy = async () => {
    try { await navigator.clipboard.writeText(traceId); } catch {}
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const severityConfig = incident?.severity ? SEVERITY_CONFIG[incident.severity] : null;
  const isDeduplicated = incident?.status === 'deduplicated' || incident?.deduplicated;
  const trelloUrl = incident?.trello_card_url
    || (incident?.trello_card_id ? `https://trello.com/c/${incident.trello_card_id}` : null);

  const lastDoneKey = [...PIPELINE_STAGES].reverse().find(s =>
    events.some(e => e.stage === s.key && ['success', 'deduplicated', 'skipped'].includes(e.status))
  )?.key;

  return (
    <div className="space-y-5">

      {/* ── Trace ID ───────────────────────────────────────────────────────── */}
      <div className="flex items-center justify-between gap-3 px-3.5 py-2.5 bg-slate-50/80 border border-slate-100 rounded-[10px]">
        <div className="min-w-0">
          <p className="text-[10px] font-medium tracking-widest uppercase text-slate-400 mb-0.5">Trace ID</p>
          <code className="font-mono text-xs text-slate-700 break-all">{traceId}</code>
        </div>
        <button
          onClick={handleCopy}
          className="inline-flex items-center gap-1.5 px-2.5 py-1.5 text-xs font-medium rounded-[8px] border border-slate-200 text-slate-500 hover:text-slate-700 hover:border-slate-300 hover:bg-white transition-all duration-150 flex-shrink-0"
        >
          {copied ? <IconCheck className="w-3 h-3 text-emerald-500" /> : <IconClipboard className="w-3 h-3" />}
          {copied ? 'Copied' : 'Copy'}
        </button>
      </div>

      {/* ── Severity badge ────────────────────────────────────────────────── */}
      {severityConfig && (
        <div className="flex items-center gap-2.5 flex-wrap">
          <span className={`inline-flex items-center px-2.5 py-1 rounded-md text-xs font-medium border ${severityConfig.bg} ${severityConfig.text} ${severityConfig.border}`}>
            {severityConfig.label}
          </span>
          {incident?.affected_module && (
            <span className="font-mono text-xs text-slate-600 bg-slate-100 px-1.5 py-0.5 rounded-md">
              {incident.affected_module}
            </span>
          )}
          {incident?.confidence_score != null && (
            <span className="text-xs text-slate-400 tabular-nums">
              {Math.round(incident.confidence_score * 100)}% confidence
            </span>
          )}
        </div>
      )}

      {/* ── Deduplicated banner ───────────────────────────────────────────── */}
      {isDeduplicated && (() => {
        const dedupEvent = events.find(e => e.stage === 'ticket' && e.status === 'deduplicated');
        const similarity = dedupEvent?.metadata?.similarity_score;
        const threshold = dedupEvent?.metadata?.threshold;
        const linkedCardId = dedupEvent?.metadata?.linked_card_id || incident?.trello_card_id;
        const linkedCardUrl = dedupEvent?.metadata?.linked_card_url || incident?.trello_card_url;
        const simPct = similarity != null ? Math.round(similarity * 100) : null;
        const threshPct = threshold != null ? Math.round(threshold * 100) : 75;
        return (
          <div className="bg-amber-500/5 border border-amber-200/60 rounded-[10px] p-4 space-y-3">
            <div className="flex items-start gap-2.5">
              <IconExclamationTriangle className="w-4 h-4 text-amber-500 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-amber-800">Duplicate incident — no new ticket created</p>
                <p className="text-xs text-amber-600 mt-0.5 leading-relaxed">
                  Automatically matched to an existing open ticket
                  {simPct != null ? ` with ${simPct}% similarity` : ''} (threshold: {threshPct}%).
                </p>
              </div>
            </div>
            {(linkedCardId || incident?.linked_ticket_id) && (
              <div className="bg-white border border-amber-200/60 rounded-[8px] px-3 py-2.5 flex items-center justify-between gap-3">
                <div className="min-w-0">
                  <p className="text-[10px] font-medium tracking-widest uppercase text-slate-400 mb-0.5">Linked ticket</p>
                  {linkedCardId && (
                    <code className="text-xs font-mono text-slate-700 truncate block">{linkedCardId}</code>
                  )}
                  {incident?.linked_ticket_id && (
                    <p className="text-[10px] text-slate-400 mt-0.5">Internal #{incident.linked_ticket_id}</p>
                  )}
                </div>
                {linkedCardUrl && (
                  <a
                    href={linkedCardUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex-shrink-0 inline-flex items-center gap-1.5 px-3 py-1.5 rounded-[8px] bg-amber-500 text-white text-xs font-medium hover:bg-amber-600 transition-colors duration-150"
                  >
                    View in Trello <IconArrowUpRight className="w-3 h-3" />
                  </a>
                )}
              </div>
            )}
          </div>
        );
      })()}

      {/* ── Progress bar ──────────────────────────────────────────────────── */}
      <PipelineProgress events={events} isComplete={isComplete} />

      {/* ── Pipeline stages ───────────────────────────────────────────────── */}
      <div>
        <h2 className="text-[10px] font-medium tracking-widest uppercase text-slate-400 mb-4">
          Pipeline — live view
        </h2>
        <div>
          {PIPELINE_STAGES.map((stage, idx) => {
            const state = getStageState(stage.key, events, isComplete);
            const event = events.find(e => e.stage === stage.key);
            const isLast = idx === PIPELINE_STAGES.length - 1;
            const defaultOpen = stage.key === lastDoneKey && state === 'done';
            return (
              <StageCard
                key={stage.key}
                stage={stage}
                state={state}
                event={event}
                incident={incident}
                isLast={isLast}
                defaultOpen={defaultOpen}
              />
            );
          })}
        </div>
      </div>

      {/* ── Trello CTA ────────────────────────────────────────────────────── */}
      {trelloUrl && incident?.trello_card_id && incident.trello_card_id !== 'pending' && !isDeduplicated && (
        <div className="bg-emerald-500/5 border border-emerald-200/60 rounded-[10px] p-4 flex items-center justify-between gap-4">
          <div>
            <p className="text-xs font-medium text-emerald-700">Trello card created</p>
            <code className="text-[10px] font-mono text-slate-500 mt-0.5 block">{incident.trello_card_id}</code>
          </div>
          <a
            href={trelloUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="flex-shrink-0 inline-flex items-center gap-1.5 px-3 py-1.5 rounded-[8px] bg-emerald-600 text-white text-xs font-medium hover:bg-emerald-700 transition-colors duration-150"
          >
            Open in Trello <IconArrowUpRight className="w-3 h-3" />
          </a>
        </div>
      )}

      {/* ── Error ─────────────────────────────────────────────────────────── */}
      {error && (
        <div className="rounded-[10px] bg-amber-500/5 border border-amber-200/60 px-3.5 py-2.5 flex items-center gap-2">
          <IconExclamationTriangle className="w-3.5 h-3.5 text-amber-500 flex-shrink-0" />
          <p className="text-xs text-amber-600">{error}</p>
        </div>
      )}

      {/* ── Footer status + reset ─────────────────────────────────────────── */}
      <div className="flex items-center justify-between gap-3 pt-3 border-t border-slate-100">
        <span className="text-xs text-slate-400 flex items-center gap-1.5">
          {isComplete ? (
            <><IconCheck className="w-3 h-3 text-emerald-500" /> {incident?.status}</>
          ) : (
            <><IconArrowPath className="w-3 h-3 animate-spin" /> {incident?.status ?? '…'}</>
          )}
        </span>
        <button
          onClick={onReset}
          className="inline-flex items-center gap-1.5 text-xs px-3.5 py-1.5 rounded-[8px] border border-slate-200 text-slate-500 hover:text-slate-700 hover:border-slate-300 hover:bg-slate-50 transition-all duration-150"
        >
          New incident
        </button>
      </div>

    </div>
  );
}