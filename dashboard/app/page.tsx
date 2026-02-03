'use client';

import { useState, useEffect, useRef } from 'react';
import useSWR from 'swr';
import { Header } from '@/components/header';
import { CascadeDisplay } from '@/components/cascade-display';
import { RegimeDisplay } from '@/components/regime-display';
import { VolatilityDisplay } from '@/components/volatility-display';
import { MetricsPanel } from '@/components/metrics-panel';
import { CorrelationDisplay } from '@/components/correlation-display';

const fetcher = (url: string) => fetch(url).then((res) => res.json());

export default function Dashboard() {
  const [mounted, setMounted] = useState(false);
  const [lastUpdate, setLastUpdate] = useState(new Date());
  const [updateFrequency, setUpdateFrequency] = useState(10000); // 10 seconds for real-time
  const [alerts, setAlerts] = useState<Array<{ id: string; type: string; message: string; timestamp: Date }>>([]);
  const alertsRef = useRef<typeof alerts>([]);

  // Fetch data with real-time polling
  const { data: featuresData, isLoading: featuresLoading, mutate: mutateFeaturesData } = useSWR(
    '/api/features',
    fetcher,
    { refreshInterval: updateFrequency, revalidateOnFocus: false }
  );

  const { data: cascadesData, isLoading: cascadesLoading, mutate: mutateCascadesData } = useSWR(
    '/api/cascades?hours=24',
    fetcher,
    { refreshInterval: updateFrequency, revalidateOnFocus: false }
  );

  const { data: volatilityData, isLoading: volatilityLoading, mutate: mutateVolatilityData } = useSWR(
    '/api/volatility',
    fetcher,
    { refreshInterval: updateFrequency, revalidateOnFocus: false }
  );

  const { data: correlationData, isLoading: correlationLoading } = useSWR(
    '/api/correlation',
    fetcher,
    { refreshInterval: updateFrequency * 2, revalidateOnFocus: false }
  );

  // Initialize and set up interval for real-time updates
  useEffect(() => {
    setMounted(true);
    
    // Manual refresh interval for aggressive real-time updates
    const interval = setInterval(() => {
      mutateFeaturesData();
      mutateCascadesData();
      mutateVolatilityData();
    }, updateFrequency);

    return () => clearInterval(interval);
  }, [updateFrequency, mutateFeaturesData, mutateCascadesData, mutateVolatilityData]);

  // Track updates and create alerts
  useEffect(() => {
    if (cascadesData?.cascades && cascadesData.cascades.length > (alertsRef.current.length || 0)) {
      const newCascade = cascadesData.cascades[0];
      if (newCascade) {
        const alert = {
          id: `cascade-${Date.now()}`,
          type: 'LIQUIDATION',
          message: `${newCascade.symbol} - ${newCascade.severity} cascade detected`,
          timestamp: new Date(),
        };
        setAlerts((prev) => [alert, ...prev].slice(0, 10));
        alertsRef.current = [...alerts, alert];
      }
    }

    if (volatilityData?.volatility_regimes) {
      const extremeVol = volatilityData.volatility_regimes.find(
        (v: any) => v.vol_regime === 'EXPLOSIVE' || v.vol_regime === 'EXTREME'
      );
      if (extremeVol && !alertsRef.current.some((a) => a.message.includes(extremeVol.symbol))) {
        const alert = {
          id: `vol-${Date.now()}`,
          type: 'VOLATILITY',
          message: `${extremeVol.symbol} - ${extremeVol.vol_regime} volatility detected`,
          timestamp: new Date(),
        };
        setAlerts((prev) => [alert, ...prev].slice(0, 10));
      }
    }

    setLastUpdate(new Date());
  }, [cascadesData, volatilityData]);

  if (!mounted) {
    return null;
  }

  const cascadeCount = cascadesData?.cascades?.length || 0;
  const volatilityEvents = volatilityData?.volatility_regimes?.filter(
    (v: any) => v.vol_regime === 'HIGH_VOL' || v.vol_regime === 'EXPLOSIVE'
  ).length || 0;
  const correlationBreaks = correlationData?.correlation_breaks || [];

  const regimes = featuresData?.regimes || [];
  const cascades = cascadesData?.cascades || [];
  const volatilities = volatilityData?.volatility_regimes || [];

  return (
    <main className="min-h-screen bg-slate-950">
      <Header
        lastUpdate={lastUpdate}
        cascadeCount={cascadeCount}
        volatilityEvents={volatilityEvents}
        correlationBreaks={correlationBreaks.length}
        updateFrequency={updateFrequency}
        onFrequencyChange={setUpdateFrequency}
      />

      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Metrics Panel */}
        <MetricsPanel
          cascadeCount={cascadeCount}
          volatilityEvents={volatilityEvents}
          correlationBreaks={correlationBreaks.length}
          regimes={regimes}
          alerts={alerts}
        />

        {/* Main Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mt-8">
          {/* Left column */}
          <div className="lg:col-span-2 space-y-8">
            <CascadeDisplay cascades={cascades} loading={cascadesLoading} />
            <VolatilityDisplay volatilities={volatilities} loading={volatilityLoading} />
          </div>

          {/* Right column */}
          <div className="space-y-8">
            <RegimeDisplay regimes={regimes} loading={featuresLoading} />
            <CorrelationDisplay correlations={correlationData?.correlations} loading={correlationLoading} />
          </div>
        </div>

        {/* Footer */}
        <div className="mt-12 pt-8 border-t border-slate-700">
          <p className="text-xs text-slate-500 text-center">
            Crypto Narrative Regimes Dashboard • Real-time data from Binance.US
            <br />
            Features: Liquidation Cascades • Funding Anomalies • Volatility Regimes • Multi-Timeframe Analysis
            <br />
            Update Frequency: {updateFrequency / 1000}s • Last Update: {lastUpdate.toLocaleTimeString()}
          </p>
        </div>
      </div>
    </main>
  );
}
