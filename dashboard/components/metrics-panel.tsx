'use client';

import { AlertCircle, Bell, Zap } from 'lucide-react';

interface Alert {
  id: string;
  type: string;
  message: string;
  timestamp: Date;
}

interface MetricsPanelProps {
  cascadeCount: number;
  volatilityEvents: number;
  correlationBreaks: number;
  regimes: any[];
  alerts: Alert[];
}

export function MetricsPanel({
  cascadeCount,
  volatilityEvents,
  correlationBreaks,
  regimes,
  alerts,
}: MetricsPanelProps) {
  const ignitionRegimes = regimes.filter((r) => r.regime === 'SPOT_IGNITION').length;
  const coolingRegimes = regimes.filter((r) => r.regime === 'SPOT_COOLING').length;
  const chopRegimes = regimes.filter((r) => r.regime === 'SPOT_CHOP').length;

  const getAlertColor = (type: string) => {
    switch (type) {
      case 'LIQUIDATION':
        return 'bg-red-500/10 border-red-500/30 text-red-400';
      case 'VOLATILITY':
        return 'bg-purple-500/10 border-purple-500/30 text-purple-400';
      case 'CORRELATION':
        return 'bg-cyan-500/10 border-cyan-500/30 text-cyan-400';
      default:
        return 'bg-slate-500/10 border-slate-500/30 text-slate-400';
    }
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
      {/* Cascade Metrics */}
      <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
        <div className="flex items-center justify-between mb-2">
          <p className="text-xs text-slate-400 uppercase font-semibold">Cascades (24h)</p>
          <AlertCircle className="w-4 h-4 text-orange-500" />
        </div>
        <p className="text-2xl font-bold text-orange-400">{cascadeCount}</p>
        <p className="text-xs text-slate-500 mt-1">Recent liquidation events</p>
      </div>

      {/* Volatility Metrics */}
      <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
        <div className="flex items-center justify-between mb-2">
          <p className="text-xs text-slate-400 uppercase font-semibold">High Vol</p>
          <Zap className="w-4 h-4 text-purple-500" />
        </div>
        <p className="text-2xl font-bold text-purple-400">{volatilityEvents}</p>
        <p className="text-xs text-slate-500 mt-1">Active volatility events</p>
      </div>

      {/* Correlation Metrics */}
      <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
        <div className="flex items-center justify-between mb-2">
          <p className="text-xs text-slate-400 uppercase font-semibold">Corr Breaks</p>
          <Bell className="w-4 h-4 text-cyan-500" />
        </div>
        <p className="text-2xl font-bold text-cyan-400">{correlationBreaks}</p>
        <p className="text-xs text-slate-500 mt-1">Pair divergences detected</p>
      </div>

      {/* Regime Breakdown */}
      <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
        <p className="text-xs text-slate-400 uppercase font-semibold mb-2">Regimes</p>
        <div className="space-y-1 text-sm">
          {ignitionRegimes > 0 && (
            <div className="flex justify-between">
              <span className="text-slate-400">Ignition</span>
              <span className="text-red-400 font-semibold">{ignitionRegimes}</span>
            </div>
          )}
          {coolingRegimes > 0 && (
            <div className="flex justify-between">
              <span className="text-slate-400">Cooling</span>
              <span className="text-blue-400 font-semibold">{coolingRegimes}</span>
            </div>
          )}
          {chopRegimes > 0 && (
            <div className="flex justify-between">
              <span className="text-slate-400">Chop</span>
              <span className="text-yellow-400 font-semibold">{chopRegimes}</span>
            </div>
          )}
          {ignitionRegimes + coolingRegimes + chopRegimes === 0 && (
            <div className="flex justify-between">
              <span className="text-slate-400">Neutral</span>
              <span className="text-slate-400 font-semibold">{regimes.length}</span>
            </div>
          )}
        </div>
      </div>

      {/* Recent Alerts */}
      <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
        <p className="text-xs text-slate-400 uppercase font-semibold mb-2">Recent Alerts</p>
        <div className="space-y-1 max-h-20 overflow-y-auto">
          {alerts.slice(0, 3).map((alert) => (
            <div
              key={alert.id}
              className={`text-xs px-2 py-1 rounded border ${getAlertColor(alert.type)}`}
            >
              <p className="font-semibold truncate">{alert.type}</p>
              <p className="text-slate-400 text-xs">{alert.timestamp.toLocaleTimeString()}</p>
            </div>
          ))}
          {alerts.length === 0 && (
            <p className="text-xs text-slate-500">No recent alerts</p>
          )}
        </div>
      </div>
    </div>
  );
}
