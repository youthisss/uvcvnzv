"""Refresh the committed data snapshot from Elexon.

Usage (from backend/): uv run python ../scripts/refresh_data.py [START END]
Dates are YYYY-MM-DD; END is exclusive.
"""

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.ingest import DEFAULT_END, DEFAULT_START, refresh  # noqa: E402
from app.store import DATA_DIR  # noqa: E402

if __name__ == "__main__":
    start = date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_START
    end = date.fromisoformat(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_END
    refresh(DATA_DIR, start, end)
