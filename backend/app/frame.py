"""Build the aligned actual-vs-forecast frame on the hourly grid."""

from __future__ import annotations

from datetime import time
from typing import Literal

import pandas as pd

from app.selection import UK_TZ, select_day_ahead, select_horizon

Mode = Literal["day_ahead", "horizon"]


def hourly_actuals(fuelhh: pd.DataFrame) -> pd.Series:
    """Mean of the two half-hours of each hour; hours missing a half-hour become NaN."""
    a = fuelhh.drop_duplicates("startTime", keep="last").set_index("startTime")["generation"]
    a = a.sort_index().astype(float)
    grouped = a.groupby(pd.DatetimeIndex(a.index).floor("1h"))
    hourly = grouped.mean()
    hourly[grouped.count() < 2] = float("nan")
    hourly.index.name = "startTime"
    return hourly


def build_frame(
    actuals_hourly: pd.Series,
    forecasts: pd.DataFrame,
    start: pd.Timestamp,
    end: pd.Timestamp,
    mode: Mode = "day_ahead",
    gate: time = time(9, 0),
    horizon_hours: float = 24,
    persistence_lag_hours: int = 24,
) -> pd.DataFrame:
    """Hourly rows for targets in [start, end) with the as-of forecast, actual and baseline.

    Columns: startTime, actual, forecast, publishTime, lead_hours, error, persistence.
    Missing forecasts/actuals stay as NaN rows so gaps are visible, not silently dropped.
    """
    grid = pd.date_range(start, end, freq="1h", inclusive="left", name="startTime")
    if mode == "day_ahead":
        chosen = select_day_ahead(forecasts, gate)
    else:
        chosen = select_horizon(forecasts, horizon_hours)
    chosen = chosen.set_index("startTime")
    df = pd.DataFrame(index=grid)
    df["actual"] = actuals_hourly.reindex(grid)
    df["forecast"] = chosen["generation"].reindex(grid).astype(float)
    df["publishTime"] = chosen["publishTime"].reindex(grid)
    df["lead_hours"] = (df.index.to_series() - df["publishTime"]).dt.total_seconds() / 3600
    df["error"] = df["forecast"] - df["actual"]
    lagged = grid - pd.Timedelta(hours=persistence_lag_hours)
    df["persistence"] = actuals_hourly.reindex(lagged).to_numpy()
    return df.reset_index()


def hour_of_day(start: pd.Series) -> pd.Series:
    """UK local hour of day for each target."""
    return start.dt.tz_convert(UK_TZ).dt.hour
