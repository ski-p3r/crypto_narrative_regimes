'use client';

import { AlertTriangle, TrendingUp, Activity } from 'lucide-react';

interface HeaderProps {
  lastUpdate: Date;
  cascadeCount: number;
  volatilityEvents: number;
}

export function Header({ lastUpdate, cascadeCount, volatilityEvents }: HeaderProps) {
  const formatTime = (date: Date) => {
    return new Intl.DateTimeFormat('en-US', {
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: true,
    }).format(date);
  };

  return (
    <header className="bg-slate-900 border-b border-slate-700">
      <div className="max-w-7xl mx-auto px-6 py-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold text-sky-400 flex items-center gap-2">
              <TrendingUp className="w-8 h-8" />
              Crypto Narrative Regimes
            </h1>
            <p className="text-slate-400 text-sm mt-1">
              Real-time market regime analysis & liquidation cascade detection
            </p>
          </div>
          <div className="text-right">
            <p className="text-xs text-slate-500">Last updated</p>
            <p className="text-lg font-mono text-slate-200">{formatTime(lastUpdate)}</p>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-4">
          <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-slate-400 uppercase font-semibold">Cascade Events</p>
                <p className="text-2xl font-bold text-orange-400 mt-1">{cascadeCount}</p>
              </div>
              <AlertTriangle className="w-8 h-8 text-orange-500 opacity-30" />
            </div>
          </div>

          <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-slate-400 uppercase font-semibold">Volatility Events</p>
                <p className="text-2xl font-bold text-purple-400 mt-1">{volatilityEvents}</p>
              </div>
              <Activity className="w-8 h-8 text-purple-500 opacity-30" />
            </div>
          </div>

          <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-slate-400 uppercase font-semibold">Data Status</p>
                <p className="text-lg font-bold text-green-400 mt-1 flex items-center gap-1">
                  <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></span>
                  Live
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
