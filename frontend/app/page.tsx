'use client';

import { useState } from 'react';
import IncidentForm from './components/IncidentForm';
import StatusTracker from './components/StatusTracker';

type PageState = 'form' | 'tracking';

export default function Home() {
  const [pageState, setPageState] = useState<PageState>('form');
  const [traceId, setTraceId] = useState<string | null>(null);
  const [inlineError, setInlineError] = useState<string | null>(null);

  const handleFormSubmit = (newTraceId: string) => {
    setTraceId(newTraceId);
    setPageState('tracking');
    setInlineError(null);
  };

  const handleFormError = (errorMsg: string) => {
    setInlineError(errorMsg);
    // Keep pageState as 'form' — don't lose the form
  };

  const handleReset = () => {
    setPageState('form');
    setTraceId(null);
    setInlineError(null);
  };

  return (
    <main className="container-custom">
      <header className="text-center mb-8">
        <h1 className="text-3xl font-bold text-slate-900 mb-1">
          SRE Incident Triage
        </h1>
        <p className="text-sm text-slate-500">
          Report production issues and get instant AI-powered analysis
        </p>
      </header>

      <div className="bg-white rounded-2xl shadow-md p-8">
        {pageState === 'form' && (
          <IncidentForm
            onSubmit={handleFormSubmit}
            onError={handleFormError}
            inlineError={inlineError}
          />
        )}

        {pageState === 'tracking' && traceId && (
          <StatusTracker traceId={traceId} onReset={handleReset} />
        )}
      </div>

      <footer className="mt-8 text-center text-slate-400 text-xs">
        <p>Powered by AI-driven SRE automation</p>
      </footer>
    </main>
  );
}
