import { NextResponse } from 'next/server';
import { Pool } from 'pg';

const pool = new Pool({
  connectionString: process.env.DB_URL,
});

export async function GET() {
  try {
    // Fetch latest market metrics and features
    const client = await pool.connect();
    
    try {
      // Get latest market data
      const marketData = await client.query(`
        SELECT 
          symbol,
          ts,
          price,
          volume,
          ret_1h,
          long_liq_usd,
          short_liq_usd,
          funding
        FROM market_metrics
        WHERE ts > NOW() - INTERVAL '7 days'
        ORDER BY symbol, ts DESC
        LIMIT 100
      `);

      // Get latest regimes
      const regimes = await client.query(`
        SELECT 
          symbol,
          ts,
          regime,
          confidence,
          long_bias,
          risk_mult
        FROM regimes
        WHERE ts > NOW() - INTERVAL '7 days'
        ORDER BY symbol, ts DESC
        LIMIT 30
      `);

      return NextResponse.json({
        market_metrics: marketData.rows,
        regimes: regimes.rows,
        timestamp: new Date().toISOString(),
      });
    } finally {
      client.release();
    }
  } catch (error) {
    console.error('Error fetching features:', error);
    return NextResponse.json(
      { error: 'Failed to fetch features' },
      { status: 500 }
    );
  }
}
