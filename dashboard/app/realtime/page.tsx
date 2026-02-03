'use client';

import { useState, useEffect, useCallback } from 'react';
import { Activity, RefreshCw, Pause, Play, Settings } from 'lucide-react';

interface RealtimeMetric {
  symbol: string;
  price: number;
  price_change_1h: number;
  volume_24h: number;
  vol_regime: string;
  cascade_velocity: number;
  funding_rate: number;
  regime: string;
  timestamp: Date;
}

export default function RealtimePage() {
  const [metrics, setMetrics] = useState<RealtimeMetric[]>([]);
  const [isRunning, setIsRunning] = useState(true);
  const [updateInterval, setUpdateInterval] = useState(5000);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  const fetchMetrics = useCallback(async () => {
    try {
      const response = await fetch('/api/features');
      const data = await response.json();

      if (data.regimes) {
        const transformed = data.regimes.map((r: any) => ({
          symbol: r.symbol,
          regime: r.regime,
          timestamp: new Date(),
          confidence: r.confidence,
          risk_mult: r.risk_mult,
        }));
        setMetrics(transformed);
        setLastUpdate(new Date());
      }
    } catch (error) {
      console.error('[v0] Failed to fetch metrics:', error);
    }
  }, []);

  useEffect(() => {
    if (isRunning) {
      fetchMetrics();
      const interval = setInterval(fetchMetrics, updateInterval);
      return () => clearInterval(interval);
    }
  }, [isRunning, updateInterval, fetchMetrics]);

  return (
    <main className="min-h-screen bg-slate-950">
      {/* Header */}
      <header className="bg-slate-900 border-b border-slate-700 sticky top-0">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-3 h-3 bg-green-400 rounded-full animate-pulse" />
              <h1 className="text-2xl font-bold text-sky-400">Real-Time Monitor</h1>
              <span className="text-xs bg-green-500/10 text-green-400 px-2 py-1 rounded">
                Live Feed
              </span>
            </div>

            <div className="flex items-center gap-4">
              <div className="text-sm text-slate-400">
                Updated: {lastUpdate?.toLocaleTimeString() || 'Never'}
              </div>

              <div className="flex items-center gap-2 bg-slate-800 border border-slate-700 rounded-lg p-2">
                <Settings className="w-4 h-4 text-slate-400" />
                <select
                  value={updateInterval}
                  onChange={(e) => setUpdateInterval(parseInt(e.target.value))}
                  className="bg-transparent text-xs text-slate-200 outline-none"
                >
                  <option value={1000}>1s</option>
                  <option value={2500}>2.5s</option>
                  <option value={5000}>5s</option>
                  <option value={10000}>10s</option>
                </select>
              </div>

              <button
                onClick={() => setIsRunning(!isRunning)}
                className="p-2 bg-slate-800 border border-slate-700 rounded-lg hover:bg-slate-700 transition"
              >
                {isRunning ? (
                  <Pause className="w-4 h-4 text-slate-400" />
                ) : (
                  <Play className="w-4 h-4 text-slate-400" />
                )}
              </button>

              <button
                onClick={fetchMetrics}
                className="p-2 bg-slate-800 border border-slate-700 rounded-lg hover:bg-slate-700 transition"
              >
                <RefreshCw className="w-4 h-4 text-slate-400" />
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        {metrics.length > 0 ? (
          <div className="space-y-4">
            {metrics.map((metric) => (
              <div
                key={metric.symbol}
                className="bg-slate-800 border border-slate-700 rounded-lg p-4 hover:border-slate-600 transition"
              >
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <div className="w-3 h-3 bg-green-400 rounded-full animate-pulse" />
                    <h3 className="text-lg font-bold text-sky-400">{metric.symbol}</h3>
                    <span className="text-xs bg-slate-700 text-slate-300 px-2 py-1 rounded">
                      {metric.regime}
                    </span>
                  </div>

                  <div className="text-right">
                    <p className="text-sm text-slate-400">
                      Last update: {metric.timestamp.toLocaleTimeString()}
                    </p>
                  </div>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="bg-slate-700/30 rounded p-3">
                    <p className="text-xs text-slate-400">Regime</p>
                    <p className="text-lg font-bold text-sky-400 mt-1">{metric.regime}</p>
                  </div>

                  <div className="bg-slate-700/30 rounded p-3">
                    <p className="text-xs text-slate-400">Confidence</p>
                    <p className="text-lg font-bold text-green-400 mt-1">
                      {((metric as any).confidence * 100).toFixed(0)}%
                    </p>
                  </div>

                  <div className="bg-slate-700/30 rounded p-3">
                    <p className="text-xs text-slate-400">Risk Mult</p>
                    <p className="text-lg font-bold text-orange-400 mt-1">
                      {((metric as any).risk_mult || 1).toFixed(2)}x
                    </p>
                  </div>

                  <div className="bg-slate-700/30 rounded p-3">
                    <p className="text-xs text-slate-400">Status</p>
                    <div className="flex items-center gap-2 mt-1">
                      <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
                      <span className="text-sm font-semibold text-green-400">Live</span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-16">
            <Activity className="w-16 h-16 mx-auto mb-4 text-slate-500 opacity-50" />
            <p className="text-slate-400 text-lg">Loading real-time data...</p>
            <p className="text-slate-500 text-sm mt-2">Make sure the backend is running</p>
          </div>
        )}
      </div>
    </main>
  );
}
