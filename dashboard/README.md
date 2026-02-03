# Crypto Narrative Regimes Dashboard

Real-time market analysis and monitoring dashboard for cryptocurrency regime detection, liquidation cascade tracking, volatility monitoring, and cross-asset correlation analysis.

## Features

### Real-Time Monitoring
- **10-second polling** for live market updates (configurable from 5s to 60s)
- **Live event stream** displaying cascades, volatility changes, and regime shifts
- **Automatic alerts** for critical market conditions
- **Time-series visualization** of liquidation cascades over 24 hours

### Market Analysis
- **Liquidation Cascade Detection** - Identify rapid liquidation velocity and side bias (LONG/SHORT)
- **Funding Rate Anomalies** - Detect extreme funding levels and mean-reversion signals
- **Volatility Regimes** - Classify market into STABLE, HIGH_VOL, EXPLOSIVE, or EXTREME states
- **Multi-Timeframe Analysis** - Cross-timeframe regime confirmation with confidence scores
- **Asset Correlations** - Monitor BTC/ETH/SOL relationships and detect breakdowns

### Visualization
- Real-time charts using Recharts
- Color-coded alerts by severity (CRITICAL, WARNING, INFO)
- Responsive design for desktop and tablet
- Live status indicators with auto-refresh rates

### Customization
- **Update frequency selector** - Choose between 5s, 10s, 30s, 1m intervals
- **Pause/resume** data fetching for manual inspection
- **Manual refresh** button for on-demand updates
- **Dismissible alerts** with type filtering

## Pages

### Main Dashboard (`/`)
Comprehensive overview with:
- Header metrics (cascades, volatility events, correlation breaks)
- Metrics panel with regime breakdown and recent alerts
- Cascade detection visualization
- Volatility regime analysis
- Market regime display
- Asset correlation matrix

### Real-Time Monitor (`/realtime`)
Dedicated real-time streaming page with:
- Live symbol metrics
- Updateable polling interval (1s to 10s)
- Pause/play controls
- Timestamp tracking
- Regime and confidence scores

## Setup

### Prerequisites
- Node.js 18+
- Backend Python service running on `http://localhost:8000` (configurable via `BACKEND_URL`)
- Binance.US API access

### Installation

```bash
cd dashboard
npm install
```

### Environment Variables

Create `.env.local`:
```env
# Optional: Backend API URL (defaults to http://localhost:8000)
BACKEND_URL=http://localhost:8000

# Optional: Update frequency in milliseconds (default: 10000)
NEXT_PUBLIC_UPDATE_INTERVAL=10000
```

### Running

Development:
```bash
npm run dev
```
Visit `http://localhost:3000`

Production:
```bash
npm run build
npm start
```

## API Routes

The dashboard includes REST API routes that proxy to the Python backend:

- `GET /api/features` - Current market regimes and features
- `GET /api/cascades?hours=24` - Liquidation cascades in time range
- `GET /api/volatility` - Volatility regime analysis
- `GET /api/correlation` - Asset correlation matrix

All routes support real-time polling with configurable intervals.

## Components

### Header
- Real-time metric display
- Cascade/volatility/correlation counters
- Live status indicator
- Update frequency selector
- Last update timestamp

### MetricsPanel
- Quick-glance statistics
- Regime breakdown
- Recent alert display
- Color-coded event types

### CascadeDisplay
- 24-hour liquidation chart
- Individual cascade details
- LONG/SHORT liquidation breakdown
- Severity classification

### RegimeDisplay
- Current regime for each symbol
- Confidence scores
- Risk multipliers
- Regime breakdown by timeframe

### VolatilityDisplay
- Market volatility classification
- Volatility index over time
- Risk factor calculations
- Clustering detection

### CorrelationDisplay
- Asset pair correlations
- Correlation breakout detection
- Leading asset identification
- Historical correlation ranges

### EventsStream
- Real-time event ticker
- Event type filtering
- Severity badges
- Dismissible alerts

### RealtimeMonitor
- Symbol-by-symbol live feed
- Configurable polling (1s-10s)
- Pause/resume controls
- Manual refresh

## Styling

Built with:
- **Tailwind CSS** for utility-based styling
- **Recharts** for charts and visualizations
- **Lucide Icons** for consistent iconography
- **Dark theme** optimized for crypto market monitoring

Theme colors:
- Primary: Sky Blue (`#0ea5e9`)
- Accent: Orange (`#f97316`)
- Success: Green (`#22c55e`)
- Danger: Red (`#ef4444`)
- Background: Slate 950 (`#030712`)

## Performance

- SWR for intelligent data fetching with revalidation
- Minimal re-renders with React hooks optimization
- Lazy loading for heavy components
- Efficient CSS with Tailwind purging

## Browser Support

- Chrome/Chromium 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Development

### Architecture
- **Next.js 14** with App Router
- **TypeScript** for type safety
- **SWR** for data fetching
- **Recharts** for visualizations

### File Structure
```
dashboard/
├── app/
│   ├── page.tsx              # Main dashboard
│   ├── realtime/page.tsx     # Real-time monitor
│   ├── api/
│   │   ├── features/
│   │   ├── cascades/
│   │   ├── volatility/
│   │   └── correlation/
│   ├── globals.css
│   └── layout.tsx
├── components/
│   ├── header.tsx
│   ├── metrics-panel.tsx
│   ├── cascade-display.tsx
│   ├── regime-display.tsx
│   ├── volatility-display.tsx
│   ├── correlation-display.tsx
│   ├── events-stream.tsx
│   └── live-indicator.tsx
├── package.json
└── README.md
```

### Adding New Metrics

1. Create API route in `/app/api/[metric]/route.ts`
2. Create display component in `/components/[metric]-display.tsx`
3. Import and add to main dashboard page
4. Style using Tailwind and theme colors

### Testing

```bash
npm run dev
# Visit http://localhost:3000
# Check browser console for errors
# Verify data fetching from backend
```

## Troubleshooting

### Data not loading
- Check backend is running on correct port (default `http://localhost:8000`)
- Verify `BACKEND_URL` environment variable if on different host
- Check browser console for CORS errors

### Updates not happening
- Ensure update frequency is not 0
- Check Network tab in DevTools for failed requests
- Verify backend API is returning valid JSON

### Performance issues
- Reduce update frequency (increase interval)
- Check for too many open network requests
- Monitor memory usage with DevTools

## Future Enhancements

- WebSocket support for true real-time (replacing polling)
- Historical data export (CSV/JSON)
- Custom alert rules and webhooks
- User preferences storage
- Dark/light theme toggle
- Mobile app version
- Email/SMS notifications

## License

Part of Crypto Narrative Regimes project
