# Forex News Impact Tracker

Production-ready local web app that ingests permitted news sources, analyzes market impact, and streams a live dashboard. Built for **Windows 10/11 without Docker**.

## Features
- Continuous news ingestion from RSS + allowed HTML fetchers (robots.txt respected).
- Impact engine for FX, commodities, and crypto (with strong baseline for XAU/USD).
- Real-time updates via Server-Sent Events (SSE).
- Alerts with debouncing and stored history.
- Demo mode that replays stored items for testing.
- SQLite-first (zero setup), with easy upgrade path later.

## Prerequisites
- **Python 3.11+** (https://python.org)
- **Node.js LTS** (https://nodejs.org)
- PowerShell on Windows 10/11

## Quick Start (PowerShell)
```powershell
# 1) Setup dependencies
scripts\setup_windows.ps1

# 2) Run both backend + frontend
scripts\run_all.ps1

# 3) Open the app
Start-Process http://127.0.0.1:5173
```

Backend API runs at `http://127.0.0.1:8000`.

## Demo Mode
The default sources include a **Demo Replay** source so you can see data immediately. You can disable it or add your own RSS sources in the UI or via API.

## Windows Troubleshooting
- **Execution policy**: If PowerShell blocks scripts, run:
  ```powershell
  Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
  ```
- **Virtual env activation**: If venv activation fails, ensure you are using Windows PowerShell and not Git Bash.

## API Endpoints
- `GET /api/news?symbol=&source=&min_confidence=`
- `GET /api/news/{id}`
- `GET /api/analysis/latest?symbol=`
- `GET /api/sources`
- `POST /api/sources`
- `POST /api/alerts`
- `GET /api/alerts/history`
- `GET /api/stream`

## Source Configuration
Example source payload:
```json
{
  "name": "My RSS",
  "type": "rss",
  "config": {"url": "https://example.com/rss"},
  "enabled": true
}
```

Supported source types:
- `rss`
- `html`
- `demo`

## Alerts
Create an alert via API:
```json
{
  "name": "Gold bullish",
  "rule": {"symbol": "XAU/USD", "min_confidence": 75, "direction": "bullish"},
  "enabled": true
}
```

## Tests
```powershell
cd backend
pytest
```

## License
MIT
