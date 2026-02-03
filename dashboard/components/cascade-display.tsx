'use client';

import { AlertTriangle, TrendingDown } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface CascadeEvent {
  symbol: string;
  ts: string;
  total_liq: number;
  long_liq_usd: number;
  short_liq_usd: number;
  side_bias: string;
  severity: string;
}

interface CascadeDisplayProps {
  cascades: CascadeEvent[];
  loading: boolean;
}

export function CascadeDisplay({ cascades, loading }: CascadeDisplayProps) {
  const formatUSD = (value: number) => {
    if (value >= 1000000) {
      return `$${(value / 1000000).toFixed(1)}M`;
    }
    if (value >= 1000) {
      return `$${(value / 1000).toFixed(1)}K`;
    }
    return `$${value.toFixed(0)}`;
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'CRITICAL':
        return 'bg-red-500/10 border-red-500/30 text-red-400';
      case 'WARNING':
        return 'bg-orange-500/10 border-orange-500/30 text-orange-400';
      default:
        return 'bg-blue-500/10 border-blue-500/30 text-blue-400';
    }
  };

  const getBiasBadgeColor = (bias: string) => {
    switch (bias) {
      case 'LONG':
        return 'bg-red-500/10 text-red-400 border-red-500/30';
      case 'SHORT':
        return 'bg-green-500/10 text-green-400 border-green-500/30';
      default:
        return 'bg-slate-500/10 text-slate-400 border-slate-500/30';
    }
  };

  // Group by symbol for chart
  const chartData = cascades
    .slice()
    .reverse()
    .map((c) => ({
      time: new Date(c.ts).toLocaleTimeString(),
      total: c.total_liq,
      symbol: c.symbol,
    }));

  if (loading) {
    return (
      <div className="card animate-pulse">
        <h2 className="text-xl font-bold mb-4">Liquidation Cascades</h2>
        <div className="h-64 bg-slate-700 rounded"></div>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="flex items-center gap-2 mb-6">
        <AlertTriangle className="w-5 h-5 text-orange-500" />
        <h2 className="text-xl font-bold">Liquidation Cascades (24h)</h2>
        <span className="ml-auto bg-orange-500/10 text-orange-400 px-2 py-1 rounded text-sm font-semibold">
          {cascades.length} events
        </span>
      </div>

      {cascades.length > 0 ? (
        <>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="time" stroke="#94a3b8" />
              <YAxis stroke="#94a3b8" />
              <Tooltip
                contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155' }}
                labelStyle={{ color: '#cbd5e1' }}
                formatter={(value: any) => formatUSD(value)}
              />
              <Line
                type="monotone"
                dataKey="total"
                stroke="#f97316"
                strokeWidth={2}
                dot={{ fill: '#f97316', r: 3 }}
              />
            </LineChart>
          </ResponsiveContainer>

          <div className="mt-6 space-y-3">
            {cascades.slice(0, 5).map((cascade, idx) => (
              <div
                key={idx}
                className={`border rounded-lg p-3 ${getSeverityColor(cascade.severity)}`}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="font-semibold text-sm">{cascade.symbol}</span>
                  <span className="text-xs font-mono">
                    {new Date(cascade.ts).toLocaleTimeString()}
                  </span>
                </div>
                <div className="flex items-center justify-between text-xs">
                  <div className="space-x-2">
                    <span className="font-semibold">{formatUSD(cascade.total_liq)}</span>
                    <span className={`badge ${getBiasBadgeColor(cascade.side_bias)}`}>
                      {cascade.side_bias}
                    </span>
                  </div>
                  <div className="flex gap-2 text-xs">
                    <span className="text-red-400">
                      {' '}
                      ↓ {formatUSD(cascade.long_liq_usd)}
                    </span>
                    <span className="text-green-400">
                      ↑ {formatUSD(cascade.short_liq_usd)}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </>
      ) : (
        <div className="text-center py-12 text-slate-400">
          <TrendingDown className="w-12 h-12 mx-auto mb-2 opacity-20" />
          <p>No cascade events in the last 24 hours</p>
        </div>
      )}
    </div>
  );
}
