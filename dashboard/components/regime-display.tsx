'use client';

import { TrendingUp, Zap } from 'lucide-react';

interface RegimeData {
  symbol: string;
  ts: string;
  regime: string;
  confidence: number;
  long_bias: number;
  risk_mult: number;
}

interface RegimeDisplayProps {
  regimes: RegimeData[];
  loading: boolean;
}

export function RegimeDisplay({ regimes, loading }: RegimeDisplayProps) {
  const getRegimeColor = (regime: string) => {
    switch (regime) {
      case 'SPOT_IGNITION':
        return {
          bg: 'bg-red-500/10',
          border: 'border-red-500/30',
          text: 'text-red-400',
          label: 'Ignition',
          icon: '🔥',
        };
      case 'SPOT_COOLING':
        return {
          bg: 'bg-blue-500/10',
          border: 'border-blue-500/30',
          text: 'text-blue-400',
          label: 'Cooling',
          icon: '❄️',
        };
      case 'SPOT_CHOP':
        return {
          bg: 'bg-yellow-500/10',
          border: 'border-yellow-500/30',
          text: 'text-yellow-400',
          label: 'Choppy',
          icon: '〰️',
        };
      default:
        return {
          bg: 'bg-slate-500/10',
          border: 'border-slate-500/30',
          text: 'text-slate-400',
          label: 'Neutral',
          icon: '→',
        };
    }
  };

  const groupedBySymbol = regimes.reduce(
    (acc, regime) => {
      if (!acc[regime.symbol]) {
        acc[regime.symbol] = [];
      }
      acc[regime.symbol].push(regime);
      return acc;
    },
    {} as Record<string, RegimeData[]>
  );

  if (loading) {
    return (
      <div className="card animate-pulse">
        <h2 className="text-xl font-bold mb-4">Market Regimes</h2>
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-20 bg-slate-700 rounded"></div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="flex items-center gap-2 mb-6">
        <TrendingUp className="w-5 h-5 text-sky-400" />
        <h2 className="text-xl font-bold">Market Regimes</h2>
      </div>

      <div className="space-y-4">
        {Object.entries(groupedBySymbol).map(([symbol, regimeList]) => {
          const latest = regimeList[0];
          if (!latest) return null;

          const regimeInfo = getRegimeColor(latest.regime);
          const confidencePercent = Math.round(latest.confidence * 100);

          return (
            <div
              key={symbol}
              className={`border rounded-lg p-4 ${regimeInfo.bg} ${regimeInfo.border}`}
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-2xl">{regimeInfo.icon}</span>
                    <h3 className="text-lg font-bold">{symbol}</h3>
                    <span className={`text-sm font-semibold ${regimeInfo.text}`}>
                      {regimeInfo.label}
                    </span>
                  </div>
                  <p className="text-xs text-slate-400">
                    {new Date(latest.ts).toLocaleString()}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-xs text-slate-400">Confidence</p>
                  <p className={`text-lg font-bold ${regimeInfo.text}`}>{confidencePercent}%</p>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-2 text-sm">
                <div className="bg-slate-800/50 rounded p-2">
                  <p className="text-xs text-slate-400">Long Bias</p>
                  <p className={`font-semibold ${latest.long_bias > 0 ? 'text-green-400' : 'text-red-400'}`}>
                    {(latest.long_bias * 100).toFixed(0)}%
                  </p>
                </div>
                <div className="bg-slate-800/50 rounded p-2">
                  <p className="text-xs text-slate-400">Risk Mult</p>
                  <p className={`font-semibold ${latest.risk_mult > 1 ? 'text-orange-400' : 'text-slate-400'}`}>
                    {latest.risk_mult.toFixed(1)}x
                  </p>
                </div>
                <div className="bg-slate-800/50 rounded p-2">
                  <p className="text-xs text-slate-400">Regime</p>
                  <p className="font-semibold text-slate-300">{latest.regime}</p>
                </div>
              </div>

              <div className="mt-3">
                <div className="w-full bg-slate-800 rounded-full h-1.5">
                  <div
                    className={`h-1.5 rounded-full transition-all ${regimeInfo.text.replace('text-', 'bg-')}`}
                    style={{ width: `${confidencePercent}%` }}
                  ></div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
