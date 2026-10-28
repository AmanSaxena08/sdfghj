# Wind Forecast Monitor

A web app for a GB energy supplier's day-ahead trading desk. For every hour of January 2026 delivery, it shows **the latest national wind forecast the desk had when it bought power on the day before**, sets it against **what the wind actually generated**, and measures **how far that forecast can be trusted**.

**Live app:** _add your Vercel URL here_

![React](https://img.shields.io/badge/frontend-React%20%2B%20TypeScript-0f766e) ![FastAPI](https://img.shields.io/badge/backend-Python%20%2B%20FastAPI-0f766e)

---

## What it answers

1. **What did the wind forecast say when we had to decide?** The day-ahead purchase is made the day before delivery, at the auction gate closure. For each delivery hour the app picks the newest forecast published at or before that moment.
2. **How wrong is that forecast, in numbers?** The app reports typical miss (MAE), systematic lean (bias), large-miss sensitivity (RMSE), and the wind shortfall to plan for (90th percentile). It also breaks these down by day, by error size and by how far ahead the forecast was made.

### Key findings (January 2026, decision at 09:20)

| Measure | Value |
|---|---|
| Typical miss (MAE) | **2,022 MW**, 17.9% of average wind output |
| Systematic lean (bias) | **+1,746 MW**: the forecast promised more wind than came |
| Wind shortfall to plan for (P90) | In 9 of 10 hours, wind fell short of the forecast by no more than **4,154 MW** |
| Lead time | Errors grow from ~1.7 GW (0–6 h ahead) to ~2.3 GW (42 h+). Day-ahead decisions rely on 12–42 h-ahead forecasts. |
| Later gate closure | Deciding at 09:50 (N2EX) instead of 09:20 (EPEX) uses a newer forecast and cuts MAE slightly, to 1,996 MW |

The strong positive bias is worth raising with the client. It means a buyer relying on the raw forecast would systematically under-buy. Possible causes to check further: curtailment of wind farms (lower metered output than the weather allowed), or differences in which wind farms each dataset covers.

---

## How it works

```
 Elexon BMRS API ──► scripts/fetch_data.py ──► backend/data/*.csv  (stored, versioned in git)
                                                     │  loaded once per process
                                               FastAPI backend
                         forecast_select.py (which forecast did the buyer have?)
                         metrics.py         (how wrong was it?)
                                                     │  JSON over /api/*
                                               React frontend (charts, KPIs)
```

### The core rule

For a delivery hour on day **D**, the decision time is **day D−1 at the gate closure** in UK local time (default 09:20, EPEX GB day-ahead auction; 09:50 for N2EX; or any custom time). The chosen forecast is the **newest one published at or before** that time. Forecasts published later are ignored, because the buyer could not have seen them.

```
error = forecast − actual        (positive = forecast too high = less wind than promised)
```

### Data

| Dataset | Used fields | Notes |
|---|---|---|
| `FUELHH`, `fuelType = WIND` | `startTime`, `generation` | Actual output, every 30 min |
| `WINDFOR` | `startTime`, `publishTime`, `generation` | Hourly forecasts, re-published ~8× a day, up to ~3 days ahead |

- **Period:** decisions on 1–31 Jan 2026 mean delivery days of 2 Jan to 1 Feb 2026.
- **Hourly comparison:** forecasts are hourly, so each is compared with the actual for the same hour (the :00 half-hour).
- **Cleaning:** wind rows only, duplicates removed, and "forecast" rows for hours already in the past at publish time dropped.
- **Time zones:** stored and compared in UTC; delivery days and decision times are computed in `Europe/London`, so the logic stays correct across British Summer Time.

### Why the data is stored, not fetched live

January 2026 is in the past, so the data barely changes. Storing it makes the app fast, keeps the demo working even if Elexon is slow or down, and needs no database on a free host.

The data is still checked for changes:
- `python -m scripts.fetch_data --check` re-downloads, compares row by row with the stored files and exits with code 1 if anything changed (forecasts are snapshots and never change; actuals can occasionally be revised).
- `.github/workflows/refresh-data.yml` re-fetches weekly and commits only if the data changed, which triggers a fresh Vercel deploy.
- `backend/data/manifest.json` records when the data was fetched, row counts and checksums.

---

## Project structure

```
.
├── api/index.py                  # Vercel serverless entry point (wraps the FastAPI app)
├── backend/
│   ├── app/
│   │   ├── config.py             # period, timezone, gate-closure presets
│   │   ├── models.py             # Actual / Forecast record types
│   │   ├── cleaning.py           # raw Elexon JSON -> clean records
│   │   ├── data_loader.py        # CSV read/write, cached dataset
│   │   ├── forecast_select.py    # the core rule: forecast available at decision time
│   │   ├── metrics.py            # MAE, RMSE, bias, percentiles, histogram
│   │   ├── schemas.py            # API response shapes (Pydantic)
│   │   └── main.py               # FastAPI routes
│   ├── data/                     # actuals.csv, forecasts.csv, manifest.json
│   ├── scripts/fetch_data.py     # download / refresh / --check
│   ├── tests/                    # pytest: rule, metrics, cleaning, API
│   ├── Dockerfile
│   └── requirements*.txt
├── frontend/
│   ├── src/
│   │   ├── api/                  # typed API client + response types
│   │   ├── hooks/                # data loading, theme colours for charts
│   │   ├── components/           # Controls, KpiCards, the four charts, Panel
│   │   ├── lib/                  # formatting (UK time, MW/GW), chart helpers
│   │   └── App.tsx
│   ├── nginx.conf                # Docker: serve the app, proxy /api to the backend
│   └── Dockerfile
├── docker-compose.yml
├── vercel.json                   # Vercel: build the frontend, route /api to Python
├── requirements.txt              # Python deps for Vercel
└── .github/workflows/            # CI (tests, lint, build) + weekly data refresh
```

---

## Running it

### With Docker (one command)

```bash
docker compose up --build
```

Open http://localhost:8080. The API docs are at http://localhost:8080/api/docs.

### Without Docker (for development)

Backend (Python 3.12+):

```bash
cd backend
python -m venv .venv
.venv/Scripts/activate        # macOS/Linux: source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload --port 8010
```

Frontend (Node 22+), in a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5200. Vite forwards `/api` to the backend on port 8010.

### Tests and checks

```bash
cd backend && pytest -q                 # 24 tests: selection rule, metrics, cleaning, API
cd frontend && npm run lint && npm run build
```

### Refreshing the data

```bash
cd backend
python -m scripts.fetch_data --check    # report differences only
python -m scripts.fetch_data            # rewrite the data files if anything changed
```

---

## API

| Endpoint | Returns |
|---|---|
| `GET /api/health` | `{ "status": "ok" }` |
| `GET /api/meta` | Analysis window, gate-closure presets, data provenance |
| `GET /api/series?start&end&cutoff` | Per hour: actual, chosen forecast, its publish time, hours ahead, error |
| `GET /api/metrics?start&end&cutoff` | Summary metrics, error histogram, per-day breakdown |
| `GET /api/horizon?start&end` | Accuracy of all published forecasts by hours-ahead bucket |

`start` and `end` are delivery days (`YYYY-MM-DD`, 2026-01-02 to 2026-02-01). `cutoff` is `HH:MM` UK time. Invalid input returns `422` with a message. Interactive docs are at `/api/docs`.

---

## Deployment (Vercel)

One Vercel project serves both parts from the same domain:
- `frontend/` is built to static files (`frontend/dist`).
- `api/index.py` runs the FastAPI app as a Python serverless function; `vercel.json` routes `/api/*` to it and bundles `backend/app` and `backend/data`.

To deploy: import the GitHub repo in Vercel (no settings to change, `vercel.json` covers them), or run `npx vercel --prod` from the repo root.

---

## Design decisions

- **Plain Python for the data logic, no pandas.** About 20k rows don't need a dataframe library. Without one, the serverless function is small and starts fast, and the core rule reads as straightforward code: group forecasts by target hour, then binary-search the publish times.
- **One rule, one module.** `forecast_select.py` holds the whole "what did the buyer know" logic and is covered by focused tests: day boundaries, BST, a forecast exactly at the cutoff, a forecast published too late, and a later cutoff choosing a newer forecast.
- **Same origin everywhere.** The browser always calls `/api/...`: the Vite proxy in development, nginx in Docker, rewrites on Vercel. No CORS and no environment-specific URLs.
- **Typed contract.** Pydantic schemas on the backend (also used for `/api/docs`), mirrored as TypeScript types on the frontend.
- **Cutoff is a parameter, not a constant.** Different exchanges close at different times, and the desk can see how much a later decision improves accuracy.

---

## Use of AI tools

This project was built with the help of AI tools (Claude Code by Anthropic). They were used for scaffolding, writing code and tests, and for drafting documentation. The design, data rules and results were reviewed and verified by me.
