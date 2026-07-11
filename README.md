# Micro-Cap Quant Engine

A random-selection, fixed-holding-period backtesting engine for US micro-cap
stocks, with a FastAPI backend and a React dashboard.

- **Backend** (`backend/`): FastAPI + pandas/numpy/yfinance. Fetches daily
  prices for a ~500-ticker micro-cap universe, resamples weekly, and
  simulates randomly-drawn, equal-weight baskets held for a configurable
  number of weeks.
- **Frontend** (`frontend/`): React + Vite + Tailwind dashboard that drives
  the backend and visualizes results (equity curve, trade ledger, rebalance
  summary, historical run averages).

## Prerequisites

Install these first:

- **Python 3.10+** — https://www.python.org/downloads/ (make sure `python`
  and `pip` are on your PATH)
- **Node.js 18+** (includes npm) — https://nodejs.org/

Verify both are installed:

```
python --version
node --version
npm --version
```

## 1. Clone the repo

```
git clone https://github.com/Moksh-Sanghavi/USA-Microcap-Backtest.git
cd USA-Microcap-Backtest
```

## 2. Install backend dependencies

```
cd backend
pip install -r requirements.txt
cd ..
```

(Optional but recommended: create a virtual environment first, e.g.
`python -m venv .venv` then activate it — `.venv\Scripts\activate` on
Windows or `source .venv/bin/activate` on macOS/Linux — before running the
`pip install` above.)

## 3. Install frontend dependencies

```
cd frontend
npm install
cd ..
```

## 4. Run the app

### Windows — one-command start/stop

From the project root:

```
start.bat
```

This launches both servers in the background:
- Backend: http://127.0.0.1:8050 (interactive API docs at `/docs`)
- Frontend: http://127.0.0.1:3050 — open this in your browser

To stop both:

```
stop.bat
```

Logs are written to `.logs/`, and PIDs are tracked in `.pids/` (both
git-ignored, created automatically).

### macOS/Linux, or manual start on Windows

The start/stop scripts are Windows-only (PowerShell). On other platforms,
or if you just want to run things manually, use two terminals:

```
# Terminal 1 — backend
cd backend
uvicorn main:app --reload --port 8050

# Terminal 2 — frontend
cd frontend
npm run dev
```

Then open http://localhost:3050.

## Notes

- The backend's CORS config only allows requests from
  `http://localhost:3050` — if you change the frontend's port (in
  `frontend/vite.config.js`), update `backend/main.py` to match.
- First run will take longer since it downloads ~500 tickers' price history
  from Yahoo Finance; subsequent runs reuse a local cache
  (`backend/price_cache/`, valid for 24h) unless it's stale.
- Each backtest run is recorded to `backend/backtest_history.json` (capped
  at the last 100 runs) to power the "Historical Averages" tab. Both this
  file and the price cache are git-ignored — they're local runtime state,
  not part of the source.
