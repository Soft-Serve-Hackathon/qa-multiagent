'use client';

import { useState, useEffect } from 'react';
import { IconShieldExclamation } from './Icons';

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
    const interval = setInterval(checkMockMode, 30000);
    return () => clearInterval(interval);
  }, []);

  if (isLoading || isMockMode === null || !isMockMode) return null;

  return (
    <div className="fixed top-4 right-4 z-50 inline-flex items-center gap-2.5 px-3.5 py-2 bg-amber-500/10 border border-amber-400/40 rounded-[10px]">
      <span className="relative flex h-1.5 w-1.5 shrink-0">
        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75" />
        <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-amber-500" />
      </span>
      <IconShieldExclamation className="w-3.5 h-3.5 text-amber-600 shrink-0" />
      <div>
        <p className="text-xs font-medium tracking-widest uppercase text-amber-700 leading-none">
          Mock mode
        </p>
        <p className="text-[10px] text-amber-500 font-normal mt-0.5 leading-none">
          No real integrations
        </p>
      </div>
    </div>
  );
}