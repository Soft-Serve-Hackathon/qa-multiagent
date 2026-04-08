'use client';

import { useState } from 'react';
import IncidentForm from './components/IncidentForm';
import StatusTracker from './components/StatusTracker';

type PageState = 'form' | 'tracking' | 'error';

export default function Home() {
  const [pageState, setPageState] = useState<PageState>('form');
  const [traceId, setTraceId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFormSubmit = (newTraceId: string) => {
    setTraceId(newTraceId);
    setPageState('tracking');
    setError(null);
  };

  const handleFormError = (errorMsg: string) => {
    setError(errorMsg);
    setPageState('error');
  };

  const handleReset = () => {
    setPageState('form');
    setTraceId(null);
    setError(null);
  };

  return (
    <main className="container-custom">
      <header className="text-center mb-12">
        <h1 className="text-4xl font-bold text-slate-900 mb-2">
          SRE Incident Triage
        </h1>
        <p className="text-lg text-slate-600">
          Report production issues and get instant AI-powered analysis
        </p>
      </header>

      <div className="bg-white rounded-2xl shadow-lg p-8">
        {pageState === 'form' && (
          <IncidentForm
            onSubmit={handleFormSubmit}
            onError={handleFormError}
          />
        )}

        {pageState === 'tracking' && traceId && (
          <StatusTracker traceId={traceId} onReset={handleReset} />
        )}

        {pageState === 'error' && error && (
          <div className="alert alert-error">
            <p className="font-semibold">Error</p>
            <p>{error}</p>
            <button
              onClick={handleReset}
              className="button-secondary mt-4"
            >
              Try Again
            </button>
          </div>
        )}
      </div>

      <footer className="mt-12 text-center text-slate-600 text-sm">
        <p>Powered by AI-driven SRE automation</p>
      </footer>
    </main>
  );
}
