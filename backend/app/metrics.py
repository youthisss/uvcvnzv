"""Forecast accuracy metrics. Error is always forecast - actual (positive = over-forecast)."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
from pydantic import BaseModel


class Metrics(BaseModel):
    n: int
    mae: float | None = None
    rmse: float | None = None
    bias: float | None = None
    nmae: float | None = None  # MAE / mean(actual)
    mean_actual: float | None = None
    # Share of periods where forecast > actual, i.e. the buyer under-buys.
    pct_over_forecast: float | None = None
    # Quantiles of (forecast - actual) in MW; a positive value is a suggested buffer.
    error_p50: float | None = None
    error_p90: float | None = None
    error_p95: float | None = None
    # Skill vs persistence on the rows where all three series exist: 1 - MAE_f / MAE_p.
    persistence_mae: float | None = None
    skill_vs_persistence: float | None = None
    n_persistence: int = 0


def _finite(x: float) -> float | None:
    return None if math.isnan(x) else float(x)


def compute_metrics(df: pd.DataFrame) -> Metrics:
    """`df` needs `forecast` and `actual`; `persistence` is optional. NaN rows are ignored."""
    valid = df.dropna(subset=["forecast", "actual"])
    n = len(valid)
    if n == 0:
        return Metrics(n=0)
    err = valid["forecast"] - valid["actual"]
    mean_actual = float(valid["actual"].mean())
    mae = float(err.abs().mean())
    out = Metrics(
        n=n,
        mae=mae,
        rmse=float(np.sqrt((err**2).mean())),
        bias=float(err.mean()),
        nmae=mae / mean_actual if mean_actual > 0 else None,
        mean_actual=mean_actual,
        pct_over_forecast=float((err > 0).mean()),
        error_p50=float(err.quantile(0.5)),
        error_p90=float(err.quantile(0.9)),
        error_p95=float(err.quantile(0.95)),
    )
    if "persistence" in df:
        common = valid.dropna(subset=["persistence"])
        if len(common):
            mae_f = float((common["forecast"] - common["actual"]).abs().mean())
            mae_p = float((common["persistence"] - common["actual"]).abs().mean())
            out.n_persistence = len(common)
            out.persistence_mae = mae_p
            out.skill_vs_persistence = _finite(1 - mae_f / mae_p) if mae_p > 0 else None
    return out
