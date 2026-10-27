# Data notes (Elexon BMRS)

Findings from exploring the live API (range 2025-12-01 .. 2026-02-02). Base URL: `https://data.elexon.co.uk/bmrs/api/v1/datasets`.
OpenAPI spec: `https://data.elexon.co.uk/swagger/v1/swagger.json`.

## Endpoints and parameters (from the OpenAPI spec)

| Dataset | Path | Filters |
|---|---|---|
| WINDFOR | `/WINDFOR/stream` | `publishDateTimeFrom`, `publishDateTimeTo` only. No filter on `startTime`. |
| FUELHH  | `/FUELHH/stream`  | `settlementDateFrom/To`, `publishDateTimeFrom/To`, `settlementPeriod`, `fuelType` |

Consequence: forecasts for early-January targets are only reachable by querying *publish* windows in late December,
so ingest starts at 2025-12-01 (the longest WINDFOR horizon is ~66 h, so late Dec would suffice; Dec 1 gives margin).
Requests are chunked per day (WINDFOR, ~73 rows x 8 publishes) and per week (FUELHH).

## Schemas

- WINDFOR: `dataset, publishTime, startTime, generation` (MW, int). Zero duplicates on `(startTime, publishTime)`; no nulls.
- FUELHH (WIND): `dataset, publishTime, startTime, settlementDate, settlementPeriod, fuelType, generation` (MW). No duplicates, no nulls.
  The stream returns rows newest-first, so sort before use.

## Resolution mismatch (key finding)

- **FUELHH is 30-minute** (`startTime` minutes in {00, 30}).
- **WINDFOR is hourly** (`startTime` minute is always 00).

Decision: evaluate on the **hourly** grid; the actual for hour `H` is the mean of the half-hours `H:00` and `H:30`.
Comparing against only the `H:00` half-hour gives near-identical results (Jan 2026 day-ahead MAE 2142 vs 2127 MW), so the choice is not sensitive.

## Publish cadence and horizon

- 8 publishes per day at **02:30, 04:30, 07:30, 09:30, 11:30, 15:30, 18:30, 22:30 UTC** (one extra at 12:25 on one day).
- Each publish contains 73 hourly targets, from about 25 h *before* publishTime to about 66 h after.
  Rows with `startTime < publishTime` (7,561 of 36,792) are not forecasts of the future; the horizon mode excludes `h < 0`.
- January 2026 is GMT, so UTC equals UK local time.

## Day-ahead selection

With the default gate of 09:00 UTC on D-1, the 09:30 publish is *after* the gate, so every target of day D uses the
**07:30 publish of D-1** (all 744 January hourly targets). The gate is therefore a sensitive, configurable parameter:
moving it to 09:30 or later switches to a fresher forecast. The exact day-ahead gate closure should be verified with the client.

## Coverage

- Actuals: 0 of 1,488 January half-hour slots missing.
- Forecasts: 0 of 744 January hourly targets without an as-of forecast at the 09:00 gate.
- Both datasets cover the same range; WINDFOR targets extend to 2026-02-03.

## First sanity numbers (exploration script, to be re-verified by the tested implementation)

Jan 2026, day-ahead at 09:00 UTC, hourly: MAE about 2.1 GW, RMSE about 2.6 GW, bias about +1.85 GW (over-forecast), nMAE about 18%.
