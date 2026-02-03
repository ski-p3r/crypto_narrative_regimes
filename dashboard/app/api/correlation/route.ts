export async function GET(request: Request) {
  try {
    // Get correlation data from Python backend
    const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000';
    const response = await fetch(`${backendUrl}/api/correlation`, {
      headers: {
        'Content-Type': 'application/json',
      },
      next: { revalidate: 10 },
    });

    if (!response.ok) {
      throw new Error(`Backend returned ${response.status}`);
    }

    const data = await response.json();

    return Response.json({
      correlations: data.correlations || [],
      correlation_breaks: data.correlation_breaks || [],
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    console.error('[v0] Correlation API error:', error);

    // Return mock data for development
    return Response.json({
      correlations: [
        {
          pair: 'BTC|ETH',
          correlation: 0.82,
          normal_range: [0.75, 0.95],
          breakout: false,
          lead_asset: 'BTC',
        },
        {
          pair: 'BTC|SOL',
          correlation: 0.65,
          normal_range: [0.6, 0.85],
          breakout: false,
          lead_asset: 'BTC',
        },
        {
          pair: 'ETH|SOL',
          correlation: 0.72,
          normal_range: [0.68, 0.88],
          breakout: false,
          lead_asset: 'ETH',
        },
      ],
      correlation_breaks: [],
      timestamp: new Date().toISOString(),
    });
  }
}
