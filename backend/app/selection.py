"""As-of forecast selection.

Core rule: for a target `startTime`, only forecasts that were *published before the
decision was made* may be used, and among those the one with the greatest `publishTime`
wins. The globally latest forecast for a target is never used (look-ahead leakage).
"""

from __future__ import annotations

from datetime import time

import pandas as pd

UK_TZ = "Europe/London"
FORECAST_COLS = ["startTime", "publishTime", "generation"]


def dedupe(forecasts: pd.DataFrame) -> pd.DataFrame:
    """Drop repeated (startTime, publishTime) pairs, keeping the last row received."""
    return (
        forecasts[FORECAST_COLS]
        .drop_duplicates(["startTime", "publishTime"], keep="last")
        .reset_index(drop=True)
    )


def day_ahead_decision_time(start: pd.Series, gate: time, tz: str = UK_TZ) -> pd.Series:
    """Decision instant (UTC) for each target: the day before its local delivery day, at `gate`.

    `gate` is a UK wall-clock time. In January (GMT) it equals UTC.
    """
    local_day = start.dt.tz_convert(tz).dt.tz_localize(None).dt.normalize()
    naive = local_day - pd.DateOffset(days=1) + pd.Timedelta(hours=gate.hour, minutes=gate.minute)
    local = naive.dt.tz_localize(tz, ambiguous=True, nonexistent="shift_forward")
    return local.dt.tz_convert("UTC")


def _latest_per_target(rows: pd.DataFrame) -> pd.DataFrame:
    if rows.empty:
        return rows
    idx = rows.groupby("startTime")["publishTime"].idxmax()
    return rows.loc[idx].sort_values("startTime").reset_index(drop=True)


def select_day_ahead(forecasts: pd.DataFrame, gate: time) -> pd.DataFrame:
    """One forecast row per target: latest publishTime <= (D-1 at `gate`).

    Targets with no forecast published before the gate are absent from the result.
    """
    f = dedupe(forecasts)
    f["decisionTime"] = day_ahead_decision_time(f["startTime"], gate)
    return _latest_per_target(f[f["publishTime"] <= f["decisionTime"]])


def select_horizon(forecasts: pd.DataFrame, horizon_hours: float) -> pd.DataFrame:
    """One forecast row per target: latest publishTime <= startTime - horizon_hours."""
    f = dedupe(forecasts)
    f["decisionTime"] = f["startTime"] - pd.Timedelta(hours=horizon_hours)
    return _latest_per_target(f[f["publishTime"] <= f["decisionTime"]])
