'use client';

import { useState, useEffect } from 'react';
import axios from 'axios';

interface StatusTrackerProps {
  traceId: string;
  onReset: () => void;
}

interface IncidentStatus {
  status: 'received' | 'triaged' | 'ticket_created' | 'notified' | 'resolved';
  severity?: string;
  ticket_id?: string;
  trace_id: string;
}

export default function StatusTracker({ traceId, onReset }: StatusTrackerProps) {
  const [status, setStatus] = useState<IncidentStatus | null>(null);
  const [isPolling, setIsPolling] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

  const statusStages = [
    { key: 'received', label: 'Received', icon: '📥' },
    { key: 'triaged', label: 'Triaged', icon: '🔍' },
    { key: 'ticket_created', label: 'Ticket Created', icon: '🎫' },
    { key: 'notified', label: 'Notified', icon: '📢' },
    { key: 'resolved', label: 'Resolved', icon: '✅' },
  ];

  useEffect(() => {
    let pollInterval: NodeJS.Timeout;

    const poll = async () => {
      try {
        const response = await axios.get(
          `${API_URL}/incidents/${traceId}`,
          { timeout: 5000 }
        );

        setStatus(response.data);
        setError(null);

        // Stop polling if resolved
        if (response.data.status === 'resolved') {
          setIsPolling(false);
        }
      } catch (err: any) {
        const errorMsg = err.response?.data?.detail || 'Failed to fetch status';
        setError(errorMsg);
      }
    };

    // Initial poll
    poll();

    // Set up polling interval (5 seconds while polling)
    if (isPolling) {
      pollInterval = setInterval(poll, 5000);
    }

    return () => {
      if (pollInterval) {
        clearInterval(pollInterval);
      }
    };
  }, [traceId, isPolling, API_URL]);

  const currentStageIndex = status
    ? statusStages.findIndex(s => s.key === status.status)
    : -1;

  return (
    <div className="space-y-8">
      {/* Trace ID Display */}
      <div className="bg-slate-100 rounded-lg p-4">
        <p className="text-sm text-slate-600 mb-1">Trace ID</p>
        <code className="font-mono text-sm text-slate-900 break-all">
          {traceId}
        </code>
        <p className="text-xs text-slate-500 mt-2">
          Use this ID to track your incident across all systems
        </p>
      </div>

      {/* Status Timeline */}
      <div className="space-y-4">
        <h2 className="text-lg font-semibold text-slate-900">
          Processing Status
        </h2>

        <div className="relative">
          {statusStages.map((stage, index) => {
            const isCompleted = index <= currentStageIndex;
            const isCurrent = index === currentStageIndex;

            return (
              <div
                key={stage.key}
                className="flex items-start mb-6 last:mb-0"
              >
                {/* Vertical line */}
                {index < statusStages.length - 1 && (
                  <div
                    className={`absolute left-5 top-12 w-1 h-8 ${
                      isCompleted ? 'bg-green-500' : 'bg-slate-300'
                    }`}
                  />
                )}

                {/* Circle indicator */}
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

                {/* Label */}
                <div className="ml-4 flex-1 pt-1">
                  <p
                    className={`font-semibold ${
                      isCurrent ? 'text-slate-900' : 'text-slate-700'
                    }`}
                  >
                    {stage.label}
                  </p>
                  {isCurrent && (
                    <p className="text-sm text-slate-500">
                      {isPolling
                        ? 'Processing... (checking every 5 seconds)'
                        : 'Complete'}
                    </p>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Status Details */}
      {status && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <p className="text-sm font-semibold text-blue-900 mb-2">
            Current Status
          </p>
          <div className="space-y-1 text-sm text-blue-800">
            {status.severity && (
              <p>
                <span className="font-medium">Severity:</span> {status.severity}
              </p>
            )}
            {status.ticket_id && (
              <p>
                <span className="font-medium">Ticket ID:</span> {status.ticket_id}
              </p>
            )}
            <p>
              <span className="font-medium">Status:</span>{' '}
              {status.status.replace(/_/g, ' ').toUpperCase()}
            </p>
          </div>
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="alert alert-error">
          <p className="font-semibold">Status Check Failed</p>
          <p className="text-sm">{error}</p>
        </div>
      )}

      {/* Reset Button */}
      <button onClick={onReset} className="button-secondary w-full">
        Submit New Incident
      </button>
    </div>
  );
}
