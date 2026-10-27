"""Download WINDFOR and FUELHH (WIND) from Elexon BMRS into parquet snapshots."""

from __future__ import annotations

import time as _time
from collections.abc import Iterator
from datetime import date, timedelta
from pathlib import Path

import httpx
import pandas as pd

BASE = "https://data.elexon.co.uk/bmrs/api/v1/datasets"
# Forecasts for 1 Jan targets are published in December, so ingest starts early.
DEFAULT_START = date(2025, 12, 1)
DEFAULT_END = date(2026, 2, 1)  # exclusive


def _get(client: httpx.Client, url: str, params: dict[str, str]) -> list[dict]:
    for attempt in range(4):
        try:
            r = client.get(url, params=params)
            if r.status_code in (429, 500, 502, 503, 504):
                raise httpx.HTTPStatusError("retryable", request=r.request, response=r)
            r.raise_for_status()
            return r.json()
        except (httpx.TransportError, httpx.HTTPStatusError):
            if attempt == 3:
                raise
            _time.sleep(2**attempt)
    return []


def _chunks(start: date, end: date, step_days: int) -> Iterator[tuple[date, date]]:
    d = start
    while d < end:
        yield d, min(d + timedelta(days=step_days), end)
        d += timedelta(days=step_days)


def fetch_windfor(client: httpx.Client, start: date, end: date) -> pd.DataFrame:
    """WINDFOR can only be filtered by publish time, so chunk by publish day."""
    rows: list[dict] = []
    for a, b in _chunks(start, end, 1):
        rows += _get(
            client,
            f"{BASE}/WINDFOR/stream",
            {"publishDateTimeFrom": f"{a}T00:00:00Z", "publishDateTimeTo": f"{b}T00:00:00Z"},
        )
    return normalize_windfor(rows)


def fetch_fuelhh_wind(client: httpx.Client, start: date, end: date) -> pd.DataFrame:
    """Wind actuals by settlement date, chunked weekly. `end` is exclusive."""
    rows: list[dict] = []
    for a, b in _chunks(start, end, 7):
        rows += _get(
            client,
            f"{BASE}/FUELHH/stream",
            {
                "settlementDateFrom": str(a),
                "settlementDateTo": str(b - timedelta(days=1)),
                "fuelType": "WIND",
            },
        )
    return normalize_fuelhh(rows)


def normalize_windfor(rows: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(rows, columns=["publishTime", "startTime", "generation"])
    for c in ("publishTime", "startTime"):
        df[c] = pd.to_datetime(df[c], utc=True)
    df = df.drop_duplicates(["startTime", "publishTime"], keep="last")
    return df.sort_values(["publishTime", "startTime"]).reset_index(drop=True)


def normalize_fuelhh(rows: list[dict]) -> pd.DataFrame:
    cols = ["startTime", "settlementDate", "settlementPeriod", "fuelType", "generation"]
    df = pd.DataFrame(rows, columns=cols)
    df["startTime"] = pd.to_datetime(df["startTime"], utc=True)
    df = df[df["fuelType"] == "WIND"].drop_duplicates("startTime", keep="last")
    return df.sort_values("startTime").reset_index(drop=True)


def refresh(out_dir: Path, start: date = DEFAULT_START, end: date = DEFAULT_END) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    with httpx.Client(timeout=60) as client:
        wf = fetch_windfor(client, start, end)
        fh = fetch_fuelhh_wind(client, start, end)
    wf.to_parquet(out_dir / "windfor.parquet", index=False)
    fh.to_parquet(out_dir / "fuelhh_wind.parquet", index=False)
    print(f"windfor: {len(wf)} rows, fuelhh wind: {len(fh)} rows -> {out_dir}")
