'use client';

import { useState } from 'react';
import IncidentForm from './components/IncidentForm';
import StatusTracker from './components/StatusTracker';
import Dashboard from './components/Dashboard';

type ActiveTab = 'incident' | 'dashboard';
type IncidentState = 'form' | 'tracking';

export default function Home() {
  const [activeTab, setActiveTab] = useState<ActiveTab>('incident');
  const [incidentState, setIncidentState] = useState<IncidentState>('form');
  const [incidentId, setIncidentId] = useState<number | null>(null);
  const [traceId, setTraceId] = useState<string | null>(null);
  const [inlineError, setInlineError] = useState<string | null>(null);

  const handleFormSubmit = (newIncidentId: number, newTraceId: string) => {
    setIncidentId(newIncidentId);
    setTraceId(newTraceId);
    setIncidentState('tracking');
    setInlineError(null);
  };

  const handleFormError = (errorMsg: string) => {
    setInlineError(errorMsg);
  };

  const handleReset = () => {
    setIncidentState('form');
    setIncidentId(null);
    setTraceId(null);
    setInlineError(null);
  };

  const tabs: { id: ActiveTab; label: string; icon: string }[] = [
    { id: 'incident', label: 'Report Incident', icon: '🚨' },
    { id: 'dashboard', label: 'Dashboard', icon: '📊' },
  ];

  return (
    <main className="min-h-screen">

      {/* ── Header ─────────────────────────────────────────────────────────── */}
      <div className="border-b border-slate-200 bg-white shadow-sm">
        <div className="max-w-6xl mx-auto px-4 pt-6 pb-0">
          <div className="text-center mb-5">
            <h1 className="text-3xl font-bold text-slate-900 mb-1">
              SRE Incident Triage
            </h1>
            <p className="text-sm text-slate-500">
              Report production issues and get instant AI-powered analysis
            </p>
          </div>

          {/* ── Tab bar ──────────────────────────────────────────────────────── */}
          <div className="flex gap-1" role="tablist">
            {tabs.map(tab => (
              <button
                key={tab.id}
                role="tab"
                aria-selected={activeTab === tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={[
                  'flex items-center gap-2 px-5 py-2.5 text-sm font-medium rounded-t-lg border-b-2 transition-all duration-150',
                  activeTab === tab.id
                    ? 'border-blue-600 text-blue-700 bg-blue-50'
                    : 'border-transparent text-slate-500 hover:text-slate-700 hover:bg-slate-50',
                ].join(' ')}
              >
                <span>{tab.icon}</span>
                {tab.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* ── Tab content ──────────────────────────────────────────────────────── */}

      {activeTab === 'incident' && (
        <div className="max-w-xl mx-auto px-4 py-8">
          <div className="bg-white rounded-2xl shadow-md p-8">
            {incidentState === 'form' && (
              <IncidentForm
                onSubmit={handleFormSubmit}
                onError={handleFormError}
                inlineError={inlineError}
              />
            )}
            {incidentState === 'tracking' && incidentId && traceId && (
              <StatusTracker incidentId={incidentId} traceId={traceId} onReset={handleReset} />
            )}
          </div>

          <footer className="mt-8 text-center text-slate-400 text-xs">
            <p>Powered by AI-driven SRE automation</p>
          </footer>
        </div>
      )}

      {activeTab === 'dashboard' && (
        <div className="max-w-6xl mx-auto px-4 py-8">
          <Dashboard />
        </div>
      )}

    </main>
  );
}
