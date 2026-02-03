'use client';

import { Link2, AlertTriangle } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface CorrelationData {
  pair: string;
  correlation: number;
  normal_range: [number, number];
  breakout: boolean;
  lead_asset: string;
}

interface CorrelationDisplayProps {
  correlations?: CorrelationData[];
  loading: boolean;
}

export function CorrelationDisplay({ correlations = [], loading }: CorrelationDisplayProps) {
  const getCorrelationColor = (correlation: number, breakout: boolean) => {
    if (breakout) {
      return {
        bg: 'bg-red-500/10',
        border: 'border-red-500/30',
        text: 'text-red-400',
        bar: '#ef4444',
      };
    }

    if (correlation > 0.7) {
      return {
        bg: 'bg-green-500/10',
        border: 'border-green-500/30',
        text: 'text-green-400',
        bar: '#22c55e',
      };
    }

    if (correlation > 0.3) {
      return {
        bg: 'bg-blue-500/10',
        border: 'border-blue-500/30',
        text: 'text-blue-400',
        bar: '#3b82f6',
      };
    }

    return {
      bg: 'bg-slate-500/10',
      border: 'border-slate-500/30',
      text: 'text-slate-400',
      bar: '#94a3b8',
    };
  };

  const chartData = correlations.map((c) => ({
    pair: c.pair.split('|').join(' / '),
    correlation: parseFloat((c.correlation * 100).toFixed(1)),
    breakout: c.breakout ? 1 : 0,
  }));

  if (loading) {
    return (
      <div className="card animate-pulse">
        <h2 className="text-xl font-bold mb-4">Asset Correlations</h2>
        <div className="h-64 bg-slate-700 rounded"></div>
      </div>
    );
  }

  const breakouts = correlations.filter((c) => c.breakout);

  return (
    <div className="card">
      <div className="flex items-center gap-2 mb-6">
        <Link2 className="w-5 h-5 text-cyan-400" />
        <h2 className="text-xl font-bold">Asset Correlations</h2>
        {breakouts.length > 0 && (
          <span className="ml-auto bg-red-500/10 text-red-400 px-2 py-1 rounded text-sm font-semibold flex items-center gap-1">
            <AlertTriangle className="w-3 h-3" />
            {breakouts.length} breakout
          </span>
        )}
      </div>

      {correlations.length > 0 ? (
        <>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="pair" stroke="#94a3b8" angle={-45} textAnchor="end" height={80} />
              <YAxis stroke="#94a3b8" domain={[0, 100]} />
              <Tooltip
                contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155' }}
                labelStyle={{ color: '#cbd5e1' }}
                formatter={(value: any) => `${value}%`}
              />
              <Bar dataKey="correlation" fill="#3b82f6" />
            </BarChart>
          </ResponsiveContainer>

          <div className="mt-6 space-y-2">
            {correlations.map((corr, idx) => {
              const colors = getCorrelationColor(corr.correlation, corr.breakout);
              const [minRange, maxRange] = corr.normal_range;

              return (
                <div
                  key={idx}
                  className={`border rounded-lg p-3 ${colors.bg} ${colors.border}`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-sm">{corr.pair.replace('|', ' / ')}</span>
                      {corr.breakout && (
                        <span className="text-xs bg-red-500/20 text-red-400 px-2 py-0.5 rounded">
                          BREAKOUT
                        </span>
                      )}
                      {corr.lead_asset && (
                        <span className="text-xs bg-slate-700 text-slate-300 px-2 py-0.5 rounded">
                          Lead: {corr.lead_asset}
                        </span>
                      )}
                    </div>
                    <span className={`text-sm font-bold ${colors.text}`}>
                      {(corr.correlation * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
                    <div
                      className={`h-1.5 transition-all`}
                      style={{
                        width: `${Math.min(100, (corr.correlation * 100) || 0)}%`,
                        backgroundColor: colors.bar,
                      }}
                    ></div>
                  </div>
                  <p className="text-xs text-slate-400 mt-1">
                    Normal range: {(minRange * 100).toFixed(1)}% - {(maxRange * 100).toFixed(1)}%
                  </p>
                </div>
              );
            })}
          </div>
        </>
      ) : (
        <div className="text-center py-12 text-slate-400">
          <Link2 className="w-12 h-12 mx-auto mb-2 opacity-20" />
          <p>No correlation data available</p>
        </div>
      )}
    </div>
  );
}
