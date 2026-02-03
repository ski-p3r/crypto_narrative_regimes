'use client';

import { Activity, AlertCircle } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface VolatilityData {
  symbol: string;
  ts: string;
  vol_24h: number;
  price: number;
  vol_regime: string;
  risk_mult: number;
}

interface VolatilityDisplayProps {
  volatilities: VolatilityData[];
  loading: boolean;
}

export function VolatilityDisplay({ volatilities, loading }: VolatilityDisplayProps) {
  const getVolRegimeColor = (regime: string) => {
    switch (regime) {
      case 'STABLE':
        return {
          bg: 'bg-green-500/10',
          border: 'border-green-500/30',
          text: 'text-green-400',
          icon: '☀️',
        };
      case 'HIGH_VOL':
        return {
          bg: 'bg-orange-500/10',
          border: 'border-orange-500/30',
          text: 'text-orange-400',
          icon: '📈',
        };
      case 'EXPLOSIVE':
        return {
          bg: 'bg-red-500/10',
          border: 'border-red-500/30',
          text: 'text-red-400',
          icon: '💥',
        };
      default:
        return {
          bg: 'bg-slate-500/10',
          border: 'border-slate-500/30',
          text: 'text-slate-400',
          icon: '❓',
        };
    }
  };

  const chartData = volatilities.map((v) => ({
    symbol: v.symbol,
    volatility: (v.vol_24h * 100).toFixed(2),
    vol_24h: v.vol_24h,
  }));

  if (loading) {
    return (
      <div className="card animate-pulse">
        <h2 className="text-xl font-bold mb-4">Volatility Analysis</h2>
        <div className="h-64 bg-slate-700 rounded"></div>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="flex items-center gap-2 mb-6">
        <Activity className="w-5 h-5 text-purple-400" />
        <h2 className="text-xl font-bold">Volatility Regimes (24h)</h2>
      </div>

      {volatilities.length > 0 ? (
        <>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="symbol" stroke="#94a3b8" />
              <YAxis stroke="#94a3b8" label={{ value: 'Volatility (%)', angle: -90, position: 'insideLeft' }} />
              <Tooltip
                contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155' }}
                labelStyle={{ color: '#cbd5e1' }}
                formatter={(value: any) => `${parseFloat(value).toFixed(2)}%`}
              />
              <Bar dataKey="volatility" fill="#a855f7" />
            </BarChart>
          </ResponsiveContainer>

          <div className="mt-6 space-y-3">
            {volatilities.map((vol, idx) => {
              const regimeInfo = getVolRegimeColor(vol.vol_regime);
              const volPercent = (vol.vol_24h * 100).toFixed(2);

              return (
                <div
                  key={idx}
                  className={`border rounded-lg p-3 ${regimeInfo.bg} ${regimeInfo.border}`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className="text-2xl">{regimeInfo.icon}</span>
                      <span className="font-semibold">{vol.symbol}</span>
                      <span className={`text-xs font-semibold ${regimeInfo.text}`}>
                        {vol.vol_regime}
                      </span>
                    </div>
                    <span className="text-xs font-mono text-slate-400">
                      {new Date(vol.ts).toLocaleTimeString()}
                    </span>
                  </div>

                  <div className="flex items-center justify-between text-sm">
                    <div>
                      <p className="text-xs text-slate-400">24h Volatility</p>
                      <p className={`font-bold text-lg ${regimeInfo.text}`}>{volPercent}%</p>
                    </div>
                    <div>
                      <p className="text-xs text-slate-400">Risk Multiplier</p>
                      <p className="font-bold text-lg text-orange-400">
                        {vol.risk_mult.toFixed(1)}x
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-slate-400">Price</p>
                      <p className="font-bold text-lg text-sky-400">
                        ${vol.price.toLocaleString('en-US', { maximumFractionDigits: 0 })}
                      </p>
                    </div>
                  </div>

                  <div className="mt-2 w-full bg-slate-800 rounded-full h-1">
                    <div
                      className={`h-1 rounded-full transition-all ${regimeInfo.text.replace('text-', 'bg-')}`}
                      style={{ width: `${Math.min(vol.vol_24h * 1000, 100)}%` }}
                    ></div>
                  </div>
                </div>
              );
            })}
          </div>
        </>
      ) : (
        <div className="text-center py-12 text-slate-400">
          <AlertCircle className="w-12 h-12 mx-auto mb-2 opacity-20" />
          <p>No volatility data available</p>
        </div>
      )}
    </div>
  );
}
