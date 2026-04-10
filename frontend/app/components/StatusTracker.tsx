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

const SEVERITY_CONFIG: Record<string, { bg: string; text: string; ring: string; label: string }> = {
  P1: { bg: 'bg-red-600',    text: 'text-white',     ring: 'ring-red-200',    label: 'P1 CRITICAL' },
  P2: { bg: 'bg-orange-500', text: 'text-white',     ring: 'ring-orange-200', label: 'P2 HIGH' },
  P3: { bg: 'bg-yellow-400', text: 'text-slate-900', ring: 'ring-yellow-200', label: 'P3 MEDIUM' },
  P4: { bg: 'bg-slate-400',  text: 'text-white',     ring: 'ring-slate-200',  label: 'P4 LOW' },
};

// ─── Helpers ─────────────────────────────────────────────────────────────────

function fmtDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}

function getStageState(
  stageKey: string,
  events: ObsEvent[],
  isComplete: boolean,
): StageState {
  const event = events.find(e => e.stage === stageKey);

  if (event) {
    if (['success', 'deduplicated'].includes(event.status)) return 'done';
    if (event.status === 'skipped') return 'skipped';
    if (event.status === 'error') return 'error';
  }

  if (isComplete) return 'pending';

  // Active = first stage with no event, after all preceding stages are done/skipped
  const stageIdx = PIPELINE_STAGES.findIndex(s => s.key === stageKey);
  const allPriorSettled = PIPELINE_STAGES.slice(0, stageIdx).every(s =>
    events.some(e => e.stage === s.key)
  );

  return allPriorSettled ? 'active' : 'pending';
}

function stageClasses(state: StageState) {
  const base = 'relative flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center text-base font-bold transition-all duration-300';
  switch (state) {
    case 'done':    return `${base} bg-green-500 text-white shadow-sm`;
    case 'skipped': return `${base} bg-amber-400 text-white`;
    case 'error':   return `${base} bg-red-500 text-white`;
    case 'active':  return `${base} bg-blue-600 text-white ring-4 ring-blue-200 animate-pulse`;
    default:        return `${base} bg-slate-200 text-slate-400`;
  }
}

function connectorClass(state: StageState) {
  switch (state) {
    case 'done':    return 'bg-green-400';
    case 'skipped': return 'bg-amber-300';
    case 'error':   return 'bg-red-400';
    case 'active':  return 'bg-blue-300';
    default:        return 'bg-slate-200';
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
        <div className="bg-slate-50 rounded p-2 border border-slate-200">
          <p className="text-xs font-semibold text-slate-600 mb-1">Technical Summary</p>
          <p className="text-xs text-slate-700 leading-relaxed">{incident.technical_summary}</p>
        </div>
      )}
      {incident?.suggested_files && incident.suggested_files.length > 0 && (
        <div>
          <p className="text-xs font-semibold text-slate-600 mb-1">Suggested files</p>
          <div className="space-y-0.5">
            {incident.suggested_files.map(f => (
              <div key={f} className="font-mono text-xs bg-slate-100 text-slate-800 px-2 py-0.5 rounded truncate">{f}</div>
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
      <MetaRow label="Reproduced" value={meta.reproduced ? 'yes' : 'no'} />
      <MetaRow label="Failing tests" value={meta.failing_tests_count} />
      <MetaRow label="New tests proposed" value={meta.new_tests_count} />
      <MetaRow label="Coverage files" value={meta.coverage_files_found} />
      <MetaRow label="Module" value={meta.module} />
    </div>
  );
}

function FixDetail({ meta }: { meta: Record<string, any> }) {
  if (meta.error) return <ErrorDetail message={meta.error} />;
  const riskColors: Record<string, string> = {
    low: 'text-green-700 bg-green-50',
    medium: 'text-amber-700 bg-amber-50',
    high: 'text-red-700 bg-red-50',
  };
  const riskClass = riskColors[meta.risk_level] || 'text-slate-700 bg-slate-50';
  return (
    <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
      <div className="col-span-2 flex items-center gap-2">
        <span className="text-slate-500">Risk level:</span>
        <span className={`px-2 py-0.5 rounded font-bold uppercase text-xs ${riskClass}`}>{meta.risk_level || '—'}</span>
      </div>
      <MetaRow label="Proposed files" value={meta.proposed_files_count} />
      <MetaRow label="Module" value={meta.module} />
    </div>
  );
}

function TicketDetail({ meta }: { meta: Record<string, any> }) {
  return (
    <div className="space-y-2">
      <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
        {meta.linked_card_id || meta.card_id ? (
          <MetaRow label="Card ID" value={meta.linked_card_id || meta.card_id} />
        ) : null}
        {meta.similarity_score != null && (
          <MetaRow label="Similarity" value={`${Math.round(meta.similarity_score * 100)}%`} />
        )}
        <MetaRow label="QA included" value={meta.qa_included ? 'yes' : '—'} />
        <MetaRow label="Fix included" value={meta.fix_included ? 'yes' : '—'} />
        <MetaRow label="Mode" value={meta.mock ? 'mock' : 'real'} />
      </div>
      {meta.card_url && (
        <a
          href={meta.card_url}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1 text-xs text-blue-600 hover:underline font-medium"
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
      <MetaRow label="Email" value={meta.email_ok ? 'sent' : 'failed'} />
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
    <p className="text-xs text-red-600 bg-red-50 rounded p-2 font-mono break-all">{message}</p>
  );
}

function MetaRow({ label, value }: { label: string; value: any }) {
  if (value == null || value === '') return null;
  return (
    <>
      <span className="text-slate-400 truncate">{label}</span>
      <span className="text-slate-800 font-medium truncate">{String(value)}</span>
    </>
  );
}

function StageDetailContent({
  stageKey,
  meta,
  incident,
}: {
  stageKey: string;
  meta: Record<string, any>;
  incident: IncidentStatus | null;
}) {
  switch (stageKey) {
    case 'ingest':            return <IngestDetail meta={meta} />;
    case 'triage':            return <TriageDetail meta={meta} incident={incident} />;
    case 'qa_scope':          return <QaDetail meta={meta} />;
    case 'fix_recommendation':return <FixDetail meta={meta} />;
    case 'ticket':            return <TicketDetail meta={meta} />;
    case 'notify':            return <NotifyDetail meta={meta} />;
    case 'resolved':          return <ResolvedDetail meta={meta} />;
    default:                  return null;
  }
}

// ─── Progress Bar ─────────────────────────────────────────────────────────────

function PipelineProgress({ events, isComplete }: { events: ObsEvent[]; isComplete: boolean }) {
  const total = PIPELINE_STAGES.length - 1; // exclude 'resolved' from normal progress
  const done = events.filter(e =>
    ['success', 'deduplicated', 'skipped'].includes(e.status) &&
    e.stage !== 'resolved'
  ).length;
  const pct = isComplete ? 100 : Math.round((done / total) * 100);

  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs text-slate-500">
        <span>{isComplete ? 'Pipeline complete' : `${done} / ${total} stages`}</span>
        <span>{pct}%</span>
      </div>
      <div className="h-1.5 bg-slate-200 rounded-full overflow-hidden">
        <div
          className="h-full bg-gradient-to-r from-blue-500 to-green-500 rounded-full transition-all duration-700 ease-out"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

// ─── Stage Card ───────────────────────────────────────────────────────────────

function StageCard({
  stage,
  state,
  event,
  incident,
  isLast,
  defaultOpen,
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
    active: 'Running…',
    done: event?.status === 'deduplicated' ? 'Deduplicated' : 'Done',
    skipped: 'Skipped',
    error: 'Error',
  };

  const stateTextColor: Record<StageState, string> = {
    pending: 'text-slate-400',
    active: 'text-blue-600',
    done: 'text-green-600',
    skipped: 'text-amber-600',
    error: 'text-red-600',
  };

  const hasDetail = state === 'done' || state === 'skipped' || state === 'error';

  return (
    <div className="flex items-start gap-3">
      {/* Left: circle + connector */}
      <div className="flex flex-col items-center">
        <div className={stageClasses(state)}>
          {state === 'active' ? (
            <IconSpinner className="w-4 h-4" />
          ) : state === 'done' ? (
            <IconCheck className="w-4 h-4" />
          ) : state === 'skipped' ? (
            <IconMinus className="w-4 h-4" />
          ) : state === 'error' ? (
            <IconXMark className="w-4 h-4" />
          ) : (
            <stage.Icon className="w-5 h-5" />
          )}
        </div>
        {!isLast && (
          <div className={`w-0.5 h-8 mt-1 rounded-full transition-colors duration-500 ${connectorClass(state)}`} />
        )}
      </div>

      {/* Right: content */}
      <div className="flex-1 pb-6 min-w-0">
        <div
          className={`flex items-start justify-between gap-2 ${hasDetail ? 'cursor-pointer' : ''}`}
          onClick={() => hasDetail && setExpanded(v => !v)}
        >
          <div className="min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <span className={`text-sm font-semibold ${state === 'pending' ? 'text-slate-400' : 'text-slate-900'}`}>
                {stage.label}
              </span>
              <span className={`text-xs font-medium ${stateTextColor[state]}`}>
                {stateLabel[state]}
              </span>
              {event?.duration_ms != null && (
                <span className="text-xs text-slate-400 tabular-nums">{fmtDuration(event.duration_ms)}</span>
              )}
            </div>
            {state === 'active' && (
              <p className="text-xs text-slate-500 mt-0.5">{stage.description}</p>
            )}
            {state === 'pending' && (
              <p className="text-xs text-slate-400 mt-0.5">{stage.description}</p>
            )}
          </div>
          {hasDetail && (
            <IconChevronDown className={`w-4 h-4 text-slate-400 flex-shrink-0 transition-transform duration-200 ${expanded ? 'rotate-180' : ''}`} />
          )}
        </div>

        {/* Inline key metrics for done stages */}
        {state === 'done' && event && !expanded && (
          <div className="mt-1 flex flex-wrap gap-x-3 gap-y-0.5">
            <StageInlineSummary stageKey={stage.key} meta={event.metadata} />
          </div>
        )}

        {/* Expanded detail */}
        {hasDetail && expanded && event && (
          <div className="mt-2 bg-slate-50 border border-slate-200 rounded-lg p-3">
            <StageDetailContent stageKey={stage.key} meta={event.metadata} incident={incident} />
          </div>
        )}
      </div>
    </div>
  );
}

// ─── Inline summary (collapsed view) ─────────────────────────────────────────

function StageInlineSummary({
  stageKey,
  meta,
}: {
  stageKey: string;
  meta: Record<string, any>;
}) {
  const chip = (text: string, color = 'text-slate-500') => (
    <span key={text} className={`text-xs ${color}`}>{text}</span>
  );

  switch (stageKey) {
    case 'ingest':
      return <>{chip(`attachment: ${meta.attachment_type || 'none'}`)}</>;
    case 'triage':
      return <>
        {meta.severity_detected && chip(meta.severity_detected, 'text-orange-600 font-semibold')}
        {meta.module_detected && chip(`module: ${meta.module_detected}`)}
        {meta.confidence != null && chip(`${Math.round(meta.confidence * 100)}% confidence`)}
        {meta.files_found != null && chip(`${meta.files_found} files`)}
      </>;
    case 'qa_scope':
      return <>
        {chip(meta.reproduced ? 'reproduced' : 'not reproduced', meta.reproduced ? 'text-green-600' : 'text-slate-500')}
        {meta.new_tests_count > 0 && chip(`${meta.new_tests_count} test(s) proposed`, 'text-cyan-600')}
      </>;
    case 'fix_recommendation':
      return <>
        {meta.risk_level && chip(`risk: ${meta.risk_level}`,
          meta.risk_level === 'high' ? 'text-red-600 font-semibold'
          : meta.risk_level === 'medium' ? 'text-amber-600'
          : 'text-green-600'
        )}
        {meta.proposed_files_count > 0 && chip(`${meta.proposed_files_count} file(s)`)}
      </>;
    case 'ticket':
      return <>
        {meta.linked_card_id ? chip(`linked to ${meta.linked_card_id}`, 'text-amber-600') : chip('card created', 'text-green-600')}
        {meta.similarity_score != null && chip(`${Math.round(meta.similarity_score * 100)}% match`)}
      </>;
    case 'notify':
      return <>
        {chip(`slack: ${meta.slack_ok ? 'sent' : 'failed'}`, meta.slack_ok ? 'text-green-600' : 'text-red-500')}
        {chip(`email: ${meta.email_ok ? 'sent' : 'failed'}`, meta.email_ok ? 'text-green-600' : 'text-red-500')}
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

  const isComplete = incident
    ? TERMINAL_INCIDENT_STATUSES.includes(incident.status)
    : false;

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
    const interval = setInterval(() => {
      if (!isComplete) fetchData();
    }, 2000);
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

  // Which stage to auto-expand: last completed or current active
  const lastDoneKey = [...PIPELINE_STAGES].reverse().find(s =>
    events.some(e => e.stage === s.key && ['success', 'deduplicated', 'skipped'].includes(e.status))
  )?.key;

  return (
    <div className="space-y-6">

      {/* ── Trace ID ───────────────────────────────────────────────────────── */}
      <div className="bg-slate-100 rounded-lg p-3">
        <div className="flex items-center justify-between mb-1">
          <p className="text-xs text-slate-500 font-medium uppercase tracking-wide">Trace ID</p>
          <button
            onClick={handleCopy}
            className="text-xs text-slate-500 hover:text-slate-800 flex items-center gap-1 px-2 py-0.5 rounded border border-slate-300 hover:border-slate-400 bg-white transition-colors"
          >
            {copied ? <IconCheck className="w-3 h-3" /> : <IconClipboard className="w-3 h-3" />}
            {copied ? 'Copied' : 'Copy'}
          </button>
        </div>
        <code className="font-mono text-xs text-slate-800 break-all">{traceId}</code>
      </div>

      {/* ── Severity badge ────────────────────────────────────────────────── */}
      {severityConfig && (
        <div className="flex items-center gap-3 flex-wrap">
          <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-bold ring-4 ${severityConfig.bg} ${severityConfig.text} ${severityConfig.ring}`}>
            {severityConfig.label}
          </span>
          {incident?.affected_module && (
            <span className="text-sm text-slate-600">
              Module: <span className="font-semibold text-slate-900">{incident.affected_module}</span>
            </span>
          )}
          {incident?.confidence_score != null && (
            <span className="text-xs text-slate-400">{Math.round(incident.confidence_score * 100)}% confidence</span>
          )}
        </div>
      )}

      {/* ── Deduplicated banner ───────────────────────────────────────────── */}
      {isDeduplicated && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg px-4 py-3">
          <p className="text-sm font-semibold text-amber-900 flex items-center gap-1.5">
            <IconExclamationTriangle className="w-4 h-4" /> Duplicate Detected
          </p>
          <p className="text-xs text-amber-700 mt-0.5">
            This incident matches an existing open ticket.
            {incident?.linked_ticket_id ? ` Linked to ticket #${incident.linked_ticket_id}.` : ''}
          </p>
        </div>
      )}

      {/* ── Progress bar ──────────────────────────────────────────────────── */}
      <PipelineProgress events={events} isComplete={isComplete} />

      {/* ── Pipeline stages ───────────────────────────────────────────────── */}
      <div>
        <h2 className="text-sm font-semibold text-slate-700 uppercase tracking-wide mb-4">
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
      {trelloUrl && incident?.trello_card_id && incident.trello_card_id !== 'pending' && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4 flex items-center justify-between gap-4">
          <div>
            <p className="text-sm font-semibold text-green-900">Trello card created</p>
            <p className="text-xs text-green-700 font-mono mt-0.5">{incident.trello_card_id}</p>
          </div>
          <a
            href={trelloUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="flex-shrink-0 inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-green-600 text-white text-sm font-semibold hover:bg-green-700 transition-colors"
          >
            Open in Trello <IconArrowUpRight className="w-3.5 h-3.5" />
          </a>
        </div>
      )}

      {/* ── Error ─────────────────────────────────────────────────────────── */}
      {error && (
        <p className="text-xs text-amber-600 bg-amber-50 border border-amber-200 rounded px-3 py-2">{error}</p>
      )}

      {/* ── Footer status + reset ─────────────────────────────────────────── */}
      <div className="flex items-center justify-between gap-3 pt-2 border-t border-slate-100">
        <span className="text-xs text-slate-400 flex items-center gap-1">
          {isComplete ? (
            <><IconCheck className="w-3 h-3 text-green-500" /> Status: {incident?.status?.toUpperCase()}</>
          ) : (
            <><IconArrowPath className="w-3 h-3 animate-spin" /> Polling — {incident?.status ?? '…'}</>
          )}
        </span>
        <button
          onClick={onReset}
          className="text-sm px-4 py-1.5 rounded-lg border border-slate-300 text-slate-600 hover:bg-slate-50 transition-colors"
        >
          New incident
        </button>
      </div>

    </div>
  );
}
