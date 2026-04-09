'use client';

import { useState, useEffect } from 'react';
import axios from 'axios';

interface StatusTrackerProps {
  incidentId: number;
  traceId: string;
  onReset: () => void;
}

interface IncidentStatus {
  incident_id: number;
  trace_id: string;
  title: string;
  status: 'received' | 'triaging' | 'ticketed' | 'notified' | 'resolved' | 'deduplicated';
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

const SEVERITY_CONFIG: Record<string, { label: string; bg: string; text: string; ring: string }> = {
  P1: { label: 'P1 CRITICAL', bg: 'bg-red-600',    text: 'text-white',     ring: 'ring-red-200' },
  P2: { label: 'P2 HIGH',     bg: 'bg-orange-500', text: 'text-white',     ring: 'ring-orange-200' },
  P3: { label: 'P3 MEDIUM',   bg: 'bg-yellow-400', text: 'text-slate-900', ring: 'ring-yellow-200' },
  P4: { label: 'P4 LOW',      bg: 'bg-slate-400',  text: 'text-white',     ring: 'ring-slate-200' },
};

const STATUS_STAGES = [
  {
    key: 'received',
    label: 'Received',
    icon: '📥',
    activeDescription: 'Incident received — validating input and assigning trace ID...',
  },
  {
    key: 'triaging',
    label: 'AI Triage',
    icon: '🤖',
    activeDescription: 'Claude is analyzing your report and searching the Medusa.js codebase...',
  },
  {
    key: 'ticketed',
    label: 'Ticket Created',
    icon: '🎫',
    activeDescription: 'Creating enriched Trello card with technical context...',
  },
  {
    key: 'notified',
    label: 'Team Notified',
    icon: '📢',
    activeDescription: 'Sending Slack alert to #incidents and confirmation email to reporter...',
  },
  {
    key: 'resolved',
    label: 'Resolved',
    icon: '✅',
    activeDescription: 'Incident resolved. Resolution email sent to reporter.',
  },
];

const TERMINAL_STATUSES = ['notified', 'resolved', 'deduplicated'];

export default function StatusTracker({ incidentId, traceId, onReset }: StatusTrackerProps) {
  const [status, setStatus] = useState<IncidentStatus | null>(null);
  const [isPolling, setIsPolling] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    let pollInterval: NodeJS.Timeout;

    const poll = async () => {
      try {
        const response = await axios.get(`/api/incidents/${incidentId}`, { timeout: 5000 });
        setStatus(response.data);
        setError(null);
        if (TERMINAL_STATUSES.includes(response.data.status)) {
          setIsPolling(false);
        }
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to fetch status');
      }
    };

    poll();
    if (isPolling) pollInterval = setInterval(poll, 5000);

    return () => { if (pollInterval) clearInterval(pollInterval); };
  }, [incidentId, isPolling]);

  const isDeduplicated = status?.status === 'deduplicated' || status?.deduplicated;

  // For deduplicated, show as "ticketed" stage (already has a ticket)
  const effectiveStatus = isDeduplicated ? 'ticketed' : status?.status;
  const currentStageIndex = effectiveStatus
    ? STATUS_STAGES.findIndex(s => s.key === effectiveStatus)
    : -1;

  const handleCopyTraceId = async () => {
    try {
      await navigator.clipboard.writeText(traceId);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // clipboard not available
    }
  };

  const severityConfig = status?.severity ? SEVERITY_CONFIG[status.severity] : null;
  const trelloUrl = status?.trello_card_url
    || (status?.trello_card_id ? `https://trello.com/c/${status.trello_card_id}` : null);

  return (
    <div className="space-y-8">

      {/* Trace ID with Copy button */}
      <div className="bg-slate-100 rounded-lg p-4">
        <div className="flex items-center justify-between mb-1">
          <p className="text-sm text-slate-600">Trace ID</p>
          <button
            onClick={handleCopyTraceId}
            className="text-xs text-slate-500 hover:text-slate-800 transition-colors flex items-center gap-1 px-2 py-0.5 rounded border border-slate-300 hover:border-slate-400 bg-white"
          >
            {copied ? '✓ Copied' : '⧉ Copy'}
          </button>
        </div>
        <code className="font-mono text-sm text-slate-900 break-all">{traceId}</code>
        <p className="text-xs text-slate-500 mt-2">Use this ID to track your incident across all systems</p>
      </div>

      {/* Deduplicated banner */}
      {isDeduplicated && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
          <p className="text-sm font-semibold text-amber-900">Duplicate Detected</p>
          <p className="text-xs text-amber-700 mt-1">
            This incident matches an existing open ticket.
            {status?.linked_ticket_id && ` Linked to ticket #${status.linked_ticket_id}.`}
          </p>
        </div>
      )}

      {/* Severity badge — visible as soon as triage completes */}
      {severityConfig && (
        <div className="flex items-center gap-3 flex-wrap">
          <span
            className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-bold ring-4 ${severityConfig.bg} ${severityConfig.text} ${severityConfig.ring}`}
          >
            {severityConfig.label}
          </span>
          {status?.affected_module && (
            <span className="text-sm text-slate-600">
              Module: <span className="font-semibold text-slate-900">{status.affected_module}</span>
            </span>
          )}
          {status?.confidence_score !== undefined && (
            <span className="text-xs text-slate-400">
              Confidence: {Math.round(status.confidence_score * 100)}%
            </span>
          )}
        </div>
      )}

      {/* Status Timeline */}
      <div className="space-y-4">
        <h2 className="text-lg font-semibold text-slate-900">Processing Status</h2>
        <div className="relative">
          {STATUS_STAGES.map((stage, index) => {
            const isCompleted = index <= currentStageIndex;
            const isCurrent = index === currentStageIndex;

            return (
              <div key={stage.key} className="flex items-start mb-6 last:mb-0">
                {index < STATUS_STAGES.length - 1 && (
                  <div className={`absolute left-5 top-12 w-1 h-8 ${isCompleted ? 'bg-green-500' : 'bg-slate-300'}`} />
                )}
                <div
                  className={`relative flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center text-lg font-bold ${
                    isCurrent
                      ? 'bg-yellow-400 text-slate-900 ring-4 ring-yellow-200'
                      : isCompleted
                      ? 'bg-green-500 text-white'
                      : 'bg-slate-300 text-slate-600'
                  }`}
                >
                  {isCompleted && !isCurrent ? '✓' : stage.icon}
                </div>
                <div className="ml-4 flex-1 pt-1">
                  <p className={`font-semibold ${isCurrent ? 'text-slate-900' : 'text-slate-700'}`}>
                    {stage.label}
                  </p>
                  {isCurrent && (
                    <p className="text-sm text-slate-500 mt-0.5">
                      {isPolling ? stage.activeDescription : 'Complete'}
                    </p>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* AI Triage Analysis — expandable */}
      {status?.technical_summary && (
        <details className="group bg-blue-50 border border-blue-200 rounded-lg">
          <summary className="px-4 py-3 cursor-pointer text-sm font-semibold text-blue-900 flex items-center justify-between list-none select-none">
            <span>🤖 AI Triage Analysis</span>
            <span className="text-blue-400 group-open:rotate-180 transition-transform">&#9660;</span>
          </summary>
          <div className="px-4 pb-4 space-y-3 border-t border-blue-200 pt-3">
            <p className="text-sm text-blue-800">{status.technical_summary}</p>
            {status.suggested_files && status.suggested_files.length > 0 && (
              <div>
                <p className="text-xs font-semibold text-blue-700 mb-1">Suggested files to investigate:</p>
                <ul className="space-y-1">
                  {status.suggested_files.map(f => (
                    <li key={f}>
                      <code className="text-xs bg-blue-100 text-blue-900 px-2 py-0.5 rounded font-mono">{f}</code>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </details>
      )}

      {/* Trello card link */}
      {(status?.trello_card_id || trelloUrl) && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4 flex items-center justify-between gap-4">
          <div>
            <p className="text-sm font-semibold text-green-900">Trello Card Created</p>
            {status?.trello_card_id && (
              <p className="text-xs text-green-700 font-mono mt-0.5">{status.trello_card_id}</p>
            )}
          </div>
          {trelloUrl && (
            <a
              href={trelloUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="flex-shrink-0 inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-green-600 text-white text-sm font-semibold hover:bg-green-700 transition-colors"
            >
              Open in Trello &#8599;
            </a>
          )}
        </div>
      )}

      {/* Current status pill */}
      {status && (
        <div className="bg-slate-50 border border-slate-200 rounded-lg p-3 text-sm text-slate-700">
          <span className="font-medium">Status:</span>{' '}
          <span className="font-mono">{status.status.replace(/_/g, ' ').toUpperCase()}</span>
          {isPolling && !TERMINAL_STATUSES.includes(status.status) && (
            <span className="ml-2 text-xs text-slate-400">(checking every 5s)</span>
          )}
        </div>
      )}

      {/* Polling error */}
      {error && (
        <div className="alert alert-error">
          <p className="font-semibold">Status Check Failed</p>
          <p className="text-sm">{error}</p>
        </div>
      )}

      <button onClick={onReset} className="button-secondary w-full">
        Submit New Incident
      </button>
    </div>
  );
}
