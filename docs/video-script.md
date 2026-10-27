# Video script (max 10 min)

All numbers below come from `uv run python ../scripts/findings.py` (run in `backend/`) on the committed January 2026 snapshot.
Re-run it before recording; if a number changes, update it here.

## Part 1 - Client pitch (about 5 min)

**1. The decision (0:00-0:45).** Every day you commit to day-ahead power for tomorrow. The less wind you expect, the more
thermal you buy. So the question is not "what is the forecast" but "what did we know at decision time, and how wrong is that usually".

**2. Demo flow (0:45-2:30).**
- Open the app, full month, gate 09:00. Point at the decision card: the forecast `publishTime` in use. For 1 January it is the
  31 December 07:30 publish, i.e. only what existed at the gate.
- Show the chart: forecast (orange) mostly above actual (blue); the shaded band is the error.
- Show the revisions panel: for 15 Jan 12:00 the forecast moved between about 10.4 and 11.9 GW across issues; the actual was 9.8 GW.

**3. What January 2026 showed (2:30-4:00).**
- Typical miss: MAE 2,142 MW (18.5% of average wind), RMSE 2,612 MW.
- **The forecast was too high**: bias +1,852 MW, above actual in 85% of hours and on 27 of 31 days. Following it blindly means under-buying.
- Worst day: 28 Jan, forecast about 5.4 GW above a very low-wind day (mean actual 5.8 GW). 11 and 12 Jan were also about 4.8 GW too high.
- The over-forecast is larger when wind is high: +2,372 MW in the windiest third of hours vs +1,479 MW in the calmest third.
- It beats the naive "same as yesterday" baseline by 46% on MAE (3,960 MW for persistence).
- Older forecasts are worse: MAE 1.8 GW at 0-6 h lead, about 2.4 GW beyond 42 h.

**4. How to use it for the buying decision (4:00-4:40).** Treat the forecast as a central estimate and add a buffer from the
error distribution: in January the forecast overshot by less than 4,300 MW in 90% of hours (P95: 5,307 MW). Also correct for the
average bias if it persists, and be most careful on high-wind forecasts.

**5. Next steps (4:40-5:00).** Longer history to see if the bias is seasonal, check the day-ahead gate with the client (a later
gate such as 16:00 cuts MAE to 1,981 MW but may be past the market deadline), add price/cost and quantile forecasting.

## Part 2 - Tech lead walkthrough (about 5 min)

1. **Architecture (0:00-1:00).** Elexon -> `ingest.py` -> committed csv.gz snapshot -> `selection.py` -> `frame.py` -> `metrics.py` -> FastAPI -> React.
   No runtime dependency on Elexon; refresh script for new data. Draw this as a simple box diagram.
2. **The as-of definition and why (1:00-2:15).** Show `selection.py`. Latest `publishTime <= D-1 gate`, never the global latest (look-ahead leakage).
   Gate in UK wall-clock time (BST-safe, tested). Mention the gate sensitivity: 09:00 uses the 07:30 publish, 09:30 uses the 09:30 publish.
3. **Data gotchas (2:15-3:00).** `WINDFOR` only filters by publish time -> ingest from December. Hourly vs half-hourly. Rows with negative lead excluded.
4. **Code tour (3:00-4:00).** `frame.py` (alignment, gaps kept as NaN), `metrics.py`, `api.py` (validation), frontend `lib/` and `components/`.
5. **Tests and practices (4:00-4:40).** 29 pytest tests (selection edge cases first), 6 vitest tests, ruff, mypy, ESLint, CI workflow, small commits, anonymous repo.
6. **Limitations and next steps (4:40-5:00).** Gate to confirm, one month of data, persistence baseline generosity, unexplained bias, add Docker deploy.