import { NextResponse } from 'next/server';
import { Pool } from 'pg';

const pool = new Pool({
  connectionString: process.env.DB_URL,
});

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const hours = searchParams.get('hours') || '24';
    
    const client = await pool.connect();
    
    try {
      // Compute cascade events from recent liquidation data
      const cascadeQuery = `
        WITH liq_data AS (
          SELECT 
            ts,
            symbol,
            long_liq_usd,
            short_liq_usd,
            (long_liq_usd + short_liq_usd) as total_liq,
            LAG(long_liq_usd + short_liq_usd) OVER (PARTITION BY symbol ORDER BY ts) as prev_total
          FROM market_metrics
          WHERE ts > NOW() - INTERVAL '${hours} hours'
        )
        SELECT 
          symbol,
          ts,
          total_liq,
          long_liq_usd,
          short_liq_usd,
          CASE 
            WHEN long_liq_usd > short_liq_usd THEN 'LONG'
            WHEN short_liq_usd > long_liq_usd THEN 'SHORT'
            ELSE 'BALANCED'
          END as side_bias,
          CASE 
            WHEN total_liq > 500000 THEN 'CRITICAL'
            WHEN total_liq > 100000 THEN 'WARNING'
            ELSE 'INFO'
          END as severity
        FROM liq_data
        WHERE total_liq > 50000
        ORDER BY ts DESC
        LIMIT 50
      `;

      const result = await client.query(cascadeQuery);

      return NextResponse.json({
        cascades: result.rows,
        count: result.rows.length,
        timestamp: new Date().toISOString(),
      });
    } finally {
      client.release();
    }
  } catch (error) {
    console.error('Error fetching cascades:', error);
    return NextResponse.json(
      { error: 'Failed to fetch cascades' },
      { status: 500 }
    );
  }
}
