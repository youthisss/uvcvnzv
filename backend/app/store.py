from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import pandas as pd

from app.frame import hourly_actuals

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


@dataclass(frozen=True)
class DataStore:
    forecasts: pd.DataFrame
    actuals_hourly: pd.Series


def load_store(data_dir: Path = DATA_DIR) -> DataStore:
    wf = pd.read_parquet(data_dir / "windfor.parquet")
    fh = pd.read_parquet(data_dir / "fuelhh_wind.parquet")
    return DataStore(forecasts=wf, actuals_hourly=hourly_actuals(fh))


@lru_cache(maxsize=1)
def get_store() -> DataStore:
    return load_store()
