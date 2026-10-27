import math
from datetime import time

import numpy as np
import pandas as pd

from app.frame import build_frame, hourly_actuals
from app.metrics import compute_metrics


def ts(s: str) -> pd.Timestamp:
    return pd.Timestamp(s, tz="UTC")


def empty_forecasts() -> pd.DataFrame:
    return pd.DataFrame({
        "startTime": pd.to_datetime([], utc=True),
        "publishTime": pd.to_datetime([], utc=True),
        "generation": pd.Series([], dtype=float),
    })


def test_metrics_known_values():
    df = pd.DataFrame({
        "actual": [100.0, 200.0, 300.0, 400.0],
        "forecast": [110.0, 190.0, 330.0, 400.0],  # errors +10, -10, +30, 0
    })
    m = compute_metrics(df)
    assert m.n == 4
    assert m.mae == 12.5
    assert math.isclose(m.rmse, math.sqrt((100 + 100 + 900) / 4))
    assert m.bias == 7.5
    assert math.isclose(m.nmae, 12.5 / 250)
    assert m.pct_over_forecast == 0.5
    assert m.error_p50 == 5.0


def test_metrics_ignores_nan_rows_and_handles_empty():
    df = pd.DataFrame({"actual": [1.0, np.nan], "forecast": [np.nan, 2.0]})
    m = compute_metrics(df)
    assert m.n == 0
    assert m.mae is None


def test_skill_vs_persistence():
    df = pd.DataFrame({
        "actual": [100.0, 100.0],
        "forecast": [110.0, 90.0],      # MAE 10
        "persistence": [140.0, 60.0],   # MAE 40
    })
    assert compute_metrics(df).skill_vs_persistence == 0.75


def test_skill_uses_only_rows_with_persistence():
    df = pd.DataFrame({
        "actual": [100.0, 100.0],
        "forecast": [100.0, 0.0],       # second row would wreck MAE_f if included
        "persistence": [150.0, np.nan],
    })
    m = compute_metrics(df)
    assert m.n_persistence == 1
    assert m.skill_vs_persistence == 1.0


def _fuelhh(vals):
    idx = pd.date_range("2026-01-01", periods=len(vals), freq="30min", tz="UTC")
    return pd.DataFrame({"startTime": idx, "generation": vals})


def test_hourly_actuals_mean_and_missing_half_hour():
    s = hourly_actuals(_fuelhh([100, 200, 300, 500]).drop(index=[3]))
    assert s.iloc[0] == 150.0
    assert math.isnan(s.iloc[1])  # only one half-hour present


def test_build_frame_alignment_and_gaps():
    actuals = pd.Series(
        [100.0, 200.0], index=pd.DatetimeIndex([ts("2026-01-02T00:00"), ts("2026-01-02T01:00")])
    )
    fc = pd.DataFrame({
        "startTime": [ts("2026-01-02T00:00")],
        "publishTime": [ts("2026-01-01T07:30")],
        "generation": [120],
    })
    df = build_frame(actuals, fc, ts("2026-01-02"), ts("2026-01-02T03:00"))
    assert len(df) == 3
    assert df.loc[0, "forecast"] == 120.0
    assert df.loc[0, "error"] == 20.0
    assert df.loc[0, "lead_hours"] == 16.5
    assert math.isnan(df.loc[1, "forecast"])      # missing forecast kept as a gap
    assert math.isnan(df.loc[2, "actual"])        # missing actual kept as a gap


def test_build_frame_persistence_uses_previous_day():
    actuals = pd.Series(
        [10.0, 20.0],
        index=pd.DatetimeIndex([ts("2026-01-01T12:00"), ts("2026-01-02T12:00")]),
    )
    df = build_frame(
        actuals, empty_forecasts(), ts("2026-01-02T12:00"), ts("2026-01-02T13:00"), gate=time(9, 0)
    )
    assert df.loc[0, "persistence"] == 10.0
