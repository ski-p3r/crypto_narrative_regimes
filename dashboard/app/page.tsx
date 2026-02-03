'use client';

import { useState, useEffect } from 'react';
import useSWR from 'swr';
import { Header } from '@/components/header';
import { CascadeDisplay } from '@/components/cascade-display';
import { RegimeDisplay } from '@/components/regime-display';
import { VolatilityDisplay } from '@/components/volatility-display';

const fetcher = (url: string) => fetch(url).then((res) => res.json());

export default function Dashboard() {
  const [mounted, setMounted] = useState(false);
  const [lastUpdate, setLastUpdate] = useState(new Date());

  // Fetch data
  const { data: featuresData, isLoading: featuresLoading } = useSWR(
    '/api/features',
    fetcher,
    { refreshInterval: 30000 }
  );

  const { data: cascadesData, isLoading: cascadesLoading } = useSWR(
    '/api/cascades?hours=24',
    fetcher,
    { refreshInterval: 30000 }
  );

  const { data: volatilityData, isLoading: volatilityLoading } = useSWR(
    '/api/volatility',
    fetcher,
    { refreshInterval: 30000 }
  );

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (featuresData || cascadesData || volatilityData) {
      setLastUpdate(new Date());
    }
  }, [featuresData, cascadesData, volatilityData]);

  if (!mounted) {
    return null;
  }

  const cascadeCount = cascadesData?.cascades?.length || 0;
  const volatilityEvents = volatilityData?.volatility_regimes?.filter(
    (v: any) => v.vol_regime === 'HIGH_VOL' || v.vol_regime === 'EXPLOSIVE'
  ).length || 0;

  const regimes = featuresData?.regimes || [];
  const cascades = cascadesData?.cascades || [];
  const volatilities = volatilityData?.volatility_regimes || [];

  return (
    <main className="min-h-screen bg-slate-950">
      <Header
        lastUpdate={lastUpdate}
        cascadeCount={cascadeCount}
        volatilityEvents={volatilityEvents}
      />

      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Left column */}
          <div className="space-y-8">
            <CascadeDisplay cascades={cascades} loading={cascadesLoading} />
            <VolatilityDisplay volatilities={volatilities} loading={volatilityLoading} />
          </div>

          {/* Right column */}
          <div>
            <RegimeDisplay regimes={regimes} loading={featuresLoading} />
          </div>
        </div>

        {/* Footer */}
        <div className="mt-12 pt-8 border-t border-slate-700">
          <p className="text-xs text-slate-500 text-center">
            Crypto Narrative Regimes Dashboard • Real-time data from Binance.US
            <br />
            Features: Liquidation Cascades • Funding Anomalies • Volatility Regimes • Multi-Timeframe Analysis
          </p>
        </div>
      </div>
    </main>
  );
}
