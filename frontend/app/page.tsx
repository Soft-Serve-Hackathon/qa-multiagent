'use client';

import { useState, Suspense } from 'react';
import IncidentForm from './components/IncidentForm';
import StatusTracker from './components/StatusTracker';
import Dashboard from './components/Dashboard';
import { FeaturesSection, StatsSection, CTASection, Footer } from './components/LandingComponents';

type ActiveTab = 'incident' | 'dashboard' | 'landing';
type IncidentState = 'form' | 'tracking';

function LandingPage({ onNavigate }: { onNavigate: (tab: ActiveTab) => void }) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      {/* Navigation */}
      <nav className="sticky top-0 z-50 backdrop-blur-lg bg-white/80 border-b border-slate-200/50 shadow-sm">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-indigo-600 to-cyan-500 rounded-lg flex items-center justify-center">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <span className="text-lg font-bold bg-gradient-to-r from-indigo-600 to-cyan-600 bg-clip-text text-transparent">SRE Triage</span>
          </div>
          <button
            onClick={() => onNavigate('incident')}
            className="px-6 py-2.5 bg-indigo-600 text-white font-semibold rounded-lg hover:bg-indigo-700 transition-all duration-200 shadow-md hover:shadow-lg"
          >
            Access Platform
          </button>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative py-24 md:py-32 overflow-hidden">
        <div className="absolute top-0 right-0 w-96 h-96 bg-indigo-100 rounded-full blur-3xl opacity-30 -z-10"></div>
        <div className="absolute bottom-0 left-0 w-80 h-80 bg-cyan-100 rounded-full blur-3xl opacity-20 -z-10"></div>

        <div className="max-w-7xl mx-auto px-6 text-center">
          <div className="inline-block mb-6 px-4 py-2 bg-indigo-100 text-indigo-700 rounded-full text-sm font-semibold border border-indigo-200">
            Intelligent Incident Management Platform
          </div>

          <h1 className="mb-6 text-5xl md:text-6xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-slate-900 via-indigo-600 to-cyan-600 leading-tight">
            Production Issues Resolved Faster
          </h1>

          <p className="mx-auto mb-10 max-w-2xl text-lg md:text-xl text-slate-600 leading-relaxed">
            Transform your incident response workflow with AI-powered analysis. Report production issues, receive intelligent recommendations, and resolve faster with complete team coordination.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <button
              onClick={() => onNavigate('incident')}
              className="px-8 py-4 bg-indigo-600 text-white font-semibold rounded-lg hover:bg-indigo-700 transition-all duration-200 shadow-lg hover:shadow-xl hover:-translate-y-1"
            >
              Start Reporting
            </button>
            <button
              onClick={() => onNavigate('dashboard')}
              className="px-8 py-4 bg-white text-indigo-600 font-semibold rounded-lg border-2 border-indigo-200 hover:border-indigo-300 hover:bg-indigo-50 transition-all duration-200 shadow-md"
            >
              View Dashboard
            </button>
          </div>

          <p className="text-slate-500 text-sm mt-8">
            Trusted by SRE Teams • Open Source • Zero Setup Time
          </p>
        </div>
      </section>

      {/* Features */}
      <FeaturesSection />

      {/* Stats */}
      <StatsSection />

      {/* CTA */}
      <CTASection />

      {/* Footer */}
      <Footer />
    </div>
  );
}

export default function Home() {
  const [activeTab, setActiveTab] = useState<ActiveTab>('landing');
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

  const handleNavigate = (tab: ActiveTab) => {
    setActiveTab(tab);
  };

  if (activeTab === 'landing') {
    return <LandingPage onNavigate={handleNavigate} />;
  }

  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      {/* Header */}
      <div className="border-b border-slate-200/50 bg-white/80 backdrop-blur-md shadow-sm sticky top-0 z-40">
        <div className="max-w-6xl mx-auto px-4 pt-6 pb-0">
          <div className="flex items-center justify-between mb-5">
            <div>
              <h1 className="text-3xl font-bold text-slate-900 mb-1">
                SRE Incident Triage
              </h1>
              <p className="text-sm text-slate-500">
                Report production issues and get instant AI-powered analysis
              </p>
            </div>
            <button
              onClick={() => {
                setActiveTab('landing');
                setIncidentState('form');
                setIncidentId(null);
                setTraceId(null);
                setInlineError(null);
              }}
              className="px-4 py-2 text-indigo-600 font-semibold hover:bg-indigo-50 rounded-lg transition-all duration-200"
            >
              Back to Home
            </button>
          </div>

          {/* Tab bar */}
          <div className="flex gap-1" role="tablist">
            <button
              role="tab"
              aria-selected={activeTab === 'incident'}
              onClick={() => setActiveTab('incident')}
              className={[
                'px-5 py-2.5 text-sm font-medium rounded-t-lg border-b-2 transition-all duration-150',
                activeTab === 'incident'
                  ? 'border-indigo-600 text-indigo-700 bg-indigo-50'
                  : 'border-transparent text-slate-500 hover:text-slate-700 hover:bg-slate-50',
              ].join(' ')}
            >
              Report Incident
            </button>
            <button
              role="tab"
              aria-selected={activeTab === 'dashboard'}
              onClick={() => setActiveTab('dashboard')}
              className={[
                'px-5 py-2.5 text-sm font-medium rounded-t-lg border-b-2 transition-all duration-150',
                activeTab === 'dashboard'
                  ? 'border-indigo-600 text-indigo-700 bg-indigo-50'
                  : 'border-transparent text-slate-500 hover:text-slate-700 hover:bg-slate-50',
              ].join(' ')}
            >
              Dashboard
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
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
          <Suspense fallback={<div className="text-center text-slate-500 py-12">Loading dashboard...</div>}>
            <Dashboard />
          </Suspense>
        </div>
      )}
    </main>
  );
}
