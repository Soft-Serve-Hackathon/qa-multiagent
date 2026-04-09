'use client';

import { useState, useEffect } from 'react';

export default function MockModeIndicator() {
  const [isMockMode, setIsMockMode] = useState<boolean | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const checkMockMode = async () => {
      try {
        const response = await fetch('/api/health');
        const data = await response.json();
        setIsMockMode(data.mock_mode === true);
      } catch (error) {
        console.error('Failed to check mock mode:', error);
        setIsMockMode(null);
      } finally {
        setIsLoading(false);
      }
    };

    checkMockMode();
    // Check every 30 seconds in case mode changes
    const interval = setInterval(checkMockMode, 30000);

    return () => clearInterval(interval);
  }, []);

  if (isLoading || isMockMode === null || !isMockMode) {
    return null;
  }

  return (
    <div
      className="fixed top-4 right-4 z-50 px-4 py-2 bg-amber-100 border-2 border-amber-400 rounded-lg shadow-lg"
      style={{
        animation: 'pulse 2s infinite',
      }}
    >
      <div className="flex items-center gap-2">
        <span className="text-2xl">🎭</span>
        <div>
          <p className="text-sm font-bold text-amber-900">MOCK MODE</p>
          <p className="text-xs text-amber-700">No real integrations</p>
        </div>
      </div>
      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.7; }
        }
      `}</style>
    </div>
  );
}
