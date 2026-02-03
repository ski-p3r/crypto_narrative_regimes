# Dashboard Quick Start (5 minutes)

## Prerequisites
- Backend running on `http://localhost:8000`
- Node.js 18+

## Steps

### 1. Install Dependencies
```bash
cd dashboard
npm install
```
**Takes ~30 seconds**

### 2. Start Development Server
```bash
npm run dev
```
**Output:**
```
> ready - started server on 0.0.0.0:3000
```

### 3. Open Dashboard
Visit **http://localhost:3000**

You should see:
- Header with 4 metric cards (Cascades, Volatility Events, Correlation Breaks, Live status)
- Metrics panel showing regime breakdown and recent alerts
- 3-column grid with:
  - Left: Cascades and Volatility charts
  - Right: Market Regimes and Correlations

### 4. Control Real-Time Updates

In the **top-right corner** of the header:
- Dropdown to select update frequency (5s, 10s, 30s, 1m)
- Select **5s** for maximum real-time updates

### 5. View Live Events (Optional)

Visit **http://localhost:3000/realtime** for dedicated real-time monitor with:
- Per-symbol metrics
- Faster polling options (1s, 2.5s, 5s, 10s)
- Play/pause controls
- Manual refresh button

## What You Should See

### If Backend is Running
- Green live indicator in header
- Dashboard fills with data from Binance.US
- Charts update every 10 seconds (by default)
- Events appear in recent alerts

### If Backend is NOT Running
- Mock data appears in charts (for development)
- No real events in alert stream
- Console shows connection warnings

## Common Settings

### Ultra Real-Time (aggressive)
```
Update Frequency: 5 seconds
Visit: Dashboard homepage
Check: Events stream updates constantly
```

### High Frequency (recommended)
```
Update Frequency: 10 seconds
Visit: Dashboard homepage
Check: Smooth chart updates, not overwhelming
```

### Low Frequency (when testing)
```
Update Frequency: 60 seconds
Visit: Dashboard homepage
Check: Reduced API load
```

## File Locations

```
Dashboard files are in: /dashboard/
├── app/page.tsx          # Main dashboard
├── app/realtime/page.tsx # Real-time monitor
├── components/           # All UI components
├── app/api/             # API routes
└── package.json         # Dependencies
```

## Troubleshooting

### Port 3000 already in use?
```bash
npm run dev -- -p 3001
# Then visit http://localhost:3001
```

### Backend connection error?
1. Check backend is running: `curl http://localhost:8000/api/features`
2. If backend on different host, set env var:
   ```bash
   BACKEND_URL=http://your-backend-host:port npm run dev
   ```

### Data not updating?
1. Check browser console (F12 → Console tab)
2. Check Network tab for failed requests
3. Try manual refresh button in header
4. Try pausing and resuming in realtime page

### Charts not showing?
1. If using mock data, this is normal during development
2. Check browser console for Recharts errors
3. Verify backend is returning valid JSON

## Next Steps

### Customize Dashboard
Edit `/dashboard/components/header.tsx` to add your own metrics

### Add New Chart
1. Create `/dashboard/components/my-chart.tsx`
2. Add to `/dashboard/app/page.tsx`
3. Style with Tailwind classes

### Change Update Frequency
Edit `/dashboard/app/page.tsx` line ~20:
```tsx
const [updateFrequency, setUpdateFrequency] = useState(10000); // Change to 5000 for 5s
```

### Change Theme Colors
Edit `/dashboard/app/globals.css` variables:
```css
:root {
  --primary: #0ea5e9;      /* Change color */
  --accent: #f97316;
  ...
}
```

## Production Deployment

### Build for Production
```bash
npm run build
npm start
```

### Deploy to Vercel
```bash
vercel deploy
```

### Deploy to Docker
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
```

## Backend Integration

Dashboard expects these API routes from backend:

### GET /api/features
```json
{
  "regimes": [
    {
      "symbol": "BTC/USDT",
      "regime": "SPOT_IGNITION",
      "confidence": 0.85,
      "risk_mult": 1.2,
      "ts": "2024-01-15T10:30:00Z"
    }
  ]
}
```

### GET /api/cascades
```json
{
  "cascades": [
    {
      "symbol": "BTC/USDT",
      "ts": "2024-01-15T10:30:00Z",
      "total_liq": 1500000,
      "long_liq_usd": 1000000,
      "short_liq_usd": 500000,
      "side_bias": "LONG",
      "severity": "CRITICAL"
    }
  ]
}
```

### GET /api/volatility
```json
{
  "volatility_regimes": [
    {
      "symbol": "BTC/USDT",
      "vol_regime": "HIGH_VOL",
      "vol_index": 0.08,
      "risk_factor": 1.5
    }
  ]
}
```

## Need Help?

- Check `/dashboard/README.md` for full documentation
- Review component files for implementation details
- Check browser console (F12) for JavaScript errors
- Enable Next.js debug: `DEBUG=* npm run dev`

Happy monitoring! 📊
