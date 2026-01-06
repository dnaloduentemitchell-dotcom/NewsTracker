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
# 0) Allow local scripts for your user (run once if needed)
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned

# 1) From the repo root, install dependencies (creates backend\.venv)
scripts\setup_windows.ps1

# 2) Start backend + frontend in separate PowerShell windows
scripts\run_all.ps1

# 3) Open the app in your browser
Start-Process http://127.0.0.1:5173
```

## Step-by-Step Setup (PowerShell)
```powershell
# 1) Clone the repo and enter it
git clone <YOUR_REPO_URL>
cd NewsTracker

# 2) Confirm Python + Node are available
python --version
node --version

# 3) Run the setup script (installs backend + frontend deps)
scripts\setup_windows.ps1
```

## Run the Backend Only (PowerShell)
```powershell
scripts\run_backend.ps1
```
Backend is available at `http://127.0.0.1:8000`.

## Run the Frontend Only (PowerShell)
```powershell
scripts\run_frontend.ps1
```
Frontend is available at `http://127.0.0.1:5173` (proxied API calls to backend).

## Manual Run (if you prefer not to use scripts)
```powershell
# Backend
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:PYTHONPATH = (Get-Location).Path
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

```powershell
# Frontend (new PowerShell window)
cd frontend
npm install
npm run dev
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
- **Ports already in use**: If `8000` or `5173` are taken, stop the other process or change the port in `scripts/run_backend.ps1` or `frontend/vite.config.ts`.

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
