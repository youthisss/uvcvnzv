# Wind forecast check

A web app that helps an energy buying team use Elexon wind forecasts for the **day-ahead purchase decision**, and
quantifies how wrong those forecasts have been. GB national wind only, January 2026 decisions only.

- Forecasts: Elexon BMRS `WINDFOR` (hourly). Actuals: `FUELHH` with `fuelType = WIND` (30-minute).
- Backend: Python, FastAPI, pandas. Frontend: React, TypeScript, Vite, TanStack Query, Recharts.
- **Deployment link:** _not deployed yet; commands are in "Deployment" below, then paste the URL here._

## The core idea: no look-ahead

For a target hour `startTime` in delivery day `D`, the buyer decides on `D-1` at a gate time (default **09:00 UK time**).
The forecast used is the one with the greatest `publishTime` that is **<= that decision time**. The globally latest
forecast for a target is never used, because it would not have existed when the decision was made.

A second mode ("horizon") uses the latest forecast published at least `h` hours before each target, which is what the
error-by-lead-time analysis is built on.

Implemented in `backend/app/selection.py` and covered by `backend/tests/test_selection.py`.

> **Verify:** the exact day-ahead gate closure time is an assumption (09:00 UK). It is a query parameter and a UI control.
> The exploration showed the result is sensitive to it: the 09:30 publish falls just after a 09:00 gate (see `docs/data-notes.md`).

## Metrics

Error is always `forecast - actual` (positive = over-forecast = the buyer under-buys).

| Metric | Meaning |
|---|---|
| MAE, RMSE, nMAE | size of misses; nMAE = MAE / mean actual (plain MAPE is avoided because actual can approach 0) |
| Bias | mean error |
| Over-forecast share | % of hours where forecast > actual |
| Error P50 / P90 / P95 | quantiles of the signed error in MW, usable as a procurement buffer |
| Skill vs persistence | `1 - MAE / MAE_persistence`, persistence = actual at the same hour the previous day |
| By lead time, by hour of day | error pooled by forecast age, and by UK hour of delivery |

## Repository map

```
backend/
  app/selection.py   as-of forecast selection (day-ahead gate and fixed horizon)
  app/frame.py       hourly alignment of actuals/forecasts, persistence baseline
  app/metrics.py     accuracy metrics
  app/ingest.py      Elexon download (chunked, retrying) to parquet
  app/store.py       loads the committed snapshot
  app/api.py         FastAPI routes; also serves the built frontend if frontend/dist exists
  data/              committed snapshot: Dec 2025 - Jan 2026 (windfor.parquet, fuelhh_wind.parquet)
  tests/             pytest: selection edge cases, metrics, alignment, API
frontend/
  src/lib/           API client, formatting, CSV export (+ vitest tests)
  src/components/    controls, KPIs, charts, revisions panel, data table
scripts/
  refresh_data.py    re-download the snapshot from Elexon
  findings.py        prints the numbers quoted in the video script
docs/
  data-notes.md      what the Elexon data actually looks like (cadence, resolution, coverage)
  video-script.md    outline for the two-part video
.github/workflows/ci.yml   backend lint/types/tests, frontend lint/tests/build
Procfile, package.json, requirements.txt, .python-version   Heroku buildpack deploy (see Deployment)
```

## Run locally (without Docker)

Prerequisites: Python 3.11+, [uv](https://docs.astral.sh/uv/), Node 20+.

```bash
# one process, one URL: build the frontend, then let FastAPI serve it
cd frontend && npm ci && npm run build && cd ..
cd backend && uv sync && uv run uvicorn app.api:app --port 8000
# open http://localhost:8000
```

Development with hot reload: run the backend as above and `npm run dev` in `frontend/` (Vite proxies `/api` to port 8000).

Checks:

```bash
cd backend && uv run ruff check . && uv run mypy app && uv run pytest
cd frontend && npm run lint && npm test && npm run build
```

Refresh the data from Elexon (the app does **not** call Elexon at runtime, so a deployment does not depend on its uptime):

```bash
cd backend && uv run python ../scripts/refresh_data.py            # default 2025-12-01 .. 2026-02-01
```

## API

| Endpoint | Purpose |
|---|---|
| `GET /api/series?from&to&mode=day_ahead&gate=HH:MM` or `mode=horizon&h=N` | aligned actual and forecast, with the `publishTime` used per hour |
| `GET /api/metrics` (same params) | summary metrics and error by hour of day |
| `GET /api/error-by-horizon` | error pooled by forecast lead time (6 h buckets) |
| `GET /api/revisions?target=ISO&gate=HH:MM` | every forecast issued for one target hour; flags the one used at the gate |
| `GET /api/health` | snapshot sizes and allowed date range |

Interactive docs at `/docs`. Dates are limited to 2026-01-01 .. 2026-01-31.

## Data handling

- Ingest starts on 2025-12-01 because `WINDFOR` can only be filtered by publish time, and early-January targets are forecast in December.
- Resolution mismatch: `WINDFOR` is hourly, `FUELHH` is 30-minute. Actuals are averaged to hours (an hour with a missing half-hour is treated as missing).
- Duplicate `(startTime, publishTime)` rows keep the last; missing forecasts or actuals appear as gaps and are excluded from metrics, with counts shown.
- Forecast rows whose target precedes their publish time are not forecasts and are excluded from lead-time analysis.

## Assumptions and limitations

- Day-ahead gate defaults to 09:00 UK time; to be confirmed with the client.
- The persistence baseline uses the previous day's actual at the same hour, as specified. For afternoon hours that value is not yet known at a 09:00 gate, so the baseline is slightly generous to persistence and the skill figure is, if anything, understated.
- A systematic over-forecast is visible in January 2026. This app measures it but does not explain it; differences in what `WINDFOR` and `FUELHH` cover could contribute and were not investigated.
- One month of data: results describe January 2026 and are not a guarantee for other seasons.
- Single national series; no price, thermal cost or imbalance modelling.

## Deployment (Heroku, buildpack-based, no Docker)

The repo root is deployable as-is: `package.json` (`heroku-postbuild` builds the frontend), `requirements.txt` and
`.python-version` (Python deps), and `Procfile` (`uvicorn` serves the API and the built frontend on `$PORT`).
This path was verified locally on a clean copy: install from `requirements.txt` on Python 3.12, build with
`NODE_ENV=production`, start with the Procfile command. The deployment itself needs a Heroku account and a paid dyno.

```bash
# one-time: install the CLI (Windows: winget install Heroku.HerokuCLI) and log in
heroku login

# from the repo root; pick an anonymous app name
heroku create <anonymous-app-name> --buildpack heroku/nodejs
heroku buildpacks:add heroku/python          # order matters: nodejs first, then python
git push heroku main
heroku ps:scale web=1                        # only needed if no dyno is running
heroku open
curl https://<anonymous-app-name>.herokuapp.com/api/health
```

Then put the resulting URL in the deployment link at the top of this README.

Docker packaging (multi-stage `Dockerfile`, `docker-compose.yml`, `heroku.yml` for the container stack) is not included yet;
when added, switch the app with `heroku stack:set container`.

## AI tools used

This project was built with AI assistance: **Claude Code (Claude Sonnet 5.5)** helped with data exploration, code,
tests, and documentation. All AI-generated code was run, tested, and reviewed before being committed, and the numbers
quoted in the documentation come from running `scripts/findings.py` against the committed data.