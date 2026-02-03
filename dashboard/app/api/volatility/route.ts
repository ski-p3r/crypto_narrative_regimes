import { NextResponse } from 'next/server';
import { Pool } from 'pg';

const pool = new Pool({
  connectionString: process.env.DB_URL,
});

export async function GET(request: Request) {
  try {
    const client = await pool.connect();
    
    try {
      // Compute rolling volatility by symbol
      const volQuery = `
        WITH returns AS (
          SELECT 
            symbol,
            ts,
            ret_1h,
            stddev_pop(ret_1h) OVER (
              PARTITION BY symbol 
              ORDER BY ts 
              ROWS BETWEEN 23 PRECEDING AND CURRENT ROW
            ) as vol_24h
          FROM market_metrics
          WHERE ts > NOW() - INTERVAL '7 days'
          AND ret_1h IS NOT NULL
        )
        SELECT DISTINCT ON (symbol)
          symbol,
          ts,
          vol_24h,
          price,
          CASE 
            WHEN vol_24h <= 0.01 THEN 'STABLE'
            WHEN vol_24h <= 0.05 THEN 'HIGH_VOL'
            WHEN vol_24h <= 0.10 THEN 'EXPLOSIVE'
            ELSE 'EXTREME'
          END as vol_regime,
          CASE 
            WHEN vol_24h <= 0.01 THEN 0.7
            WHEN vol_24h <= 0.05 THEN 1.2
            WHEN vol_24h <= 0.10 THEN 1.8
            ELSE 2.5
          END as risk_mult
        FROM (
          SELECT 
            symbol,
            ts,
            vol_24h,
            LAST_VALUE(price) OVER (PARTITION BY symbol ORDER BY ts) as price
          FROM returns
          WHERE ts > NOW() - INTERVAL '24 hours'
        ) latest
        ORDER BY symbol, ts DESC
      `;

      const result = await client.query(volQuery);

      return NextResponse.json({
        volatility_regimes: result.rows,
        timestamp: new Date().toISOString(),
      });
    } finally {
      client.release();
    }
  } catch (error) {
    console.error('Error fetching volatility:', error);
    return NextResponse.json(
      { error: 'Failed to fetch volatility' },
      { status: 500 }
    );
  }
}
