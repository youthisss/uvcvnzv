"""HTTP API. Delivery days are UK-local; January is GMT so they equal UTC days."""

from __future__ import annotations

import math
from datetime import date, time
from typing import Annotated, Any

import pandas as pd
from fastapi import Depends, FastAPI, HTTPException, Query
from pydantic import BaseModel

from app.frame import Mode, build_frame, hour_of_day
from app.metrics import Metrics, compute_metrics
from app.selection import dedupe
from app.store import DataStore, get_store

# The brief only concerns decisions made in January 2026.
MIN_DAY = date(2026, 1, 1)
MAX_DAY = date(2026, 1, 31)
HORIZON_BUCKET_HOURS = 6
MAX_LEAD_HOURS = 72
GATE_PATTERN = r"^([01]\d|2[0-3]):[0-5]\d$"

app = FastAPI(title="Wind forecast evaluation", version="0.1.0")

GateQuery = Annotated[str, Query(pattern=GATE_PATTERN, description="Gate time HH:MM, UK local")]
TargetQuery = Annotated[str, Query(description="Target startTime, e.g. 2026-01-15T12:00:00Z")]


class Params(BaseModel):
    from_: date
    to: date
    mode: Mode
    gate: str
    h: float

    @property
    def start(self) -> pd.Timestamp:
        return pd.Timestamp(self.from_, tz="UTC")

    @property
    def end(self) -> pd.Timestamp:
        return pd.Timestamp(self.to, tz="UTC") + pd.Timedelta(days=1)

    @property
    def gate_time(self) -> time:
        return time.fromisoformat(self.gate)


def params(
    from_: Annotated[date, Query(alias="from")] = MIN_DAY,
    to: date = MAX_DAY,
    mode: Mode = "day_ahead",
    gate: GateQuery = "09:00",
    h: Annotated[float, Query(ge=0, le=MAX_LEAD_HOURS)] = 24,
) -> Params:
    if to < from_:
        raise HTTPException(422, "`to` must be on or after `from`")
    if from_ < MIN_DAY or to > MAX_DAY:
        raise HTTPException(422, f"delivery days must be within {MIN_DAY}..{MAX_DAY}")
    return Params(from_=from_, to=to, mode=mode, gate=gate, h=h)


P = Annotated[Params, Depends(params)]
S = Annotated[DataStore, Depends(get_store)]


def _clean(v: Any) -> Any:
    if isinstance(v, float) and math.isnan(v):
        return None
    if isinstance(v, pd.Timestamp):
        return None if pd.isna(v) else v.isoformat()
    if v is pd.NaT:
        return None
    return v


def _records(df: pd.DataFrame) -> list[dict[str, Any]]:
    return [{str(k): _clean(v) for k, v in row.items()} for row in df.to_dict("records")]


def _frame(p: Params, store: DataStore) -> pd.DataFrame:
    return build_frame(
        store.actuals_hourly,
        store.forecasts,
        p.start,
        p.end,
        mode=p.mode,
        gate=p.gate_time,
        horizon_hours=p.h,
    )


class SeriesPoint(BaseModel):
    startTime: str
    actual: float | None
    forecast: float | None
    publishTime: str | None
    leadHours: float | None
    error: float | None
    persistence: float | None


class SeriesResponse(BaseModel):
    mode: Mode
    gate: str | None
    horizonHours: float | None
    points: list[SeriesPoint]


@app.get("/api/health")
def health(store: S) -> dict[str, Any]:
    return {
        "status": "ok",
        "forecastRows": len(store.forecasts),
        "actualHours": int(store.actuals_hourly.notna().sum()),
        "allowedRange": [str(MIN_DAY), str(MAX_DAY)],
    }


@app.get("/api/series", response_model=SeriesResponse)
def series(p: P, store: S) -> SeriesResponse:
    df = _frame(p, store).rename(columns={"lead_hours": "leadHours"})
    return SeriesResponse(
        mode=p.mode,
        gate=p.gate if p.mode == "day_ahead" else None,
        horizonHours=p.h if p.mode == "horizon" else None,
        points=[SeriesPoint(**r) for r in _records(df)],
    )


class GroupMetrics(BaseModel):
    key: str
    metrics: Metrics


class MetricsResponse(BaseModel):
    mode: Mode
    summary: Metrics
    byHour: list[GroupMetrics]
    missingForecasts: int
    missingActuals: int


@app.get("/api/metrics", response_model=MetricsResponse)
def metrics(p: P, store: S) -> MetricsResponse:
    df = _frame(p, store)
    hours = hour_of_day(df["startTime"])
    by_hour = [
        GroupMetrics(key=f"{int(h):02d}:00", metrics=compute_metrics(g))
        for h, g in df.groupby(hours, sort=True)
    ]
    return MetricsResponse(
        mode=p.mode,
        summary=compute_metrics(df),
        byHour=by_hour,
        missingForecasts=int(df["forecast"].isna().sum()),
        missingActuals=int(df["actual"].isna().sum()),
    )


class HorizonBucket(BaseModel):
    label: str
    fromHours: int
    toHours: int
    metrics: Metrics


@app.get("/api/error-by-horizon", response_model=list[HorizonBucket])
def error_by_horizon(p: P, store: S) -> list[HorizonBucket]:
    """Error by lead time, pooling every published forecast for targets in range.

    Lead time = startTime - publishTime. Only future-looking rows (lead >= 0) are used.
    """
    f = dedupe(store.forecasts)
    f = f[(f["startTime"] >= p.start) & (f["startTime"] < p.end)].copy()
    f["lead"] = (f["startTime"] - f["publishTime"]).dt.total_seconds() / 3600
    f = f[(f["lead"] >= 0) & (f["lead"] < MAX_LEAD_HOURS)].copy()
    f["actual"] = f["startTime"].map(store.actuals_hourly)
    f["forecast"] = f["generation"].astype(float)
    bucket = (f["lead"] // HORIZON_BUCKET_HOURS).astype(int) * HORIZON_BUCKET_HOURS
    return [
        HorizonBucket(
            label=f"{lo}-{lo + HORIZON_BUCKET_HOURS}h",
            fromHours=int(lo),
            toHours=int(lo) + HORIZON_BUCKET_HOURS,
            metrics=compute_metrics(g),
        )
        for lo, g in f.groupby(bucket, sort=True)
    ]


class Revision(BaseModel):
    publishTime: str
    leadHours: float
    forecast: float
    usedByGate: bool


class RevisionsResponse(BaseModel):
    target: str
    actual: float | None
    revisions: list[Revision]


@app.get("/api/revisions", response_model=RevisionsResponse)
def revisions(target: TargetQuery, store: S, gate: GateQuery = "09:00") -> RevisionsResponse:
    """How the forecast for one target changed across publishTimes."""
    try:
        t = pd.Timestamp(target)
    except ValueError as e:
        raise HTTPException(422, "invalid `target` timestamp") from e
    t = t.tz_localize("UTC") if t.tzinfo is None else t.tz_convert("UTC")
    f = dedupe(store.forecasts)
    f = f[f["startTime"] == t].sort_values("publishTime")
    if f.empty:
        raise HTTPException(404, "no forecasts for this target")
    used = build_frame(
        store.actuals_hourly,
        store.forecasts,
        t,
        t + pd.Timedelta(hours=1),
        gate=time.fromisoformat(gate),
    )["publishTime"].iloc[0]
    actual = store.actuals_hourly.get(t)
    return RevisionsResponse(
        target=t.isoformat(),
        actual=None if actual is None or pd.isna(actual) else float(actual),
        revisions=[
            Revision(
                publishTime=r["publishTime"].isoformat(),
                leadHours=(t - r["publishTime"]).total_seconds() / 3600,
                forecast=float(r["generation"]),
                usedByGate=bool(pd.notna(used) and r["publishTime"] == used),
            )
            for r in f.to_dict("records")
        ],
    )
