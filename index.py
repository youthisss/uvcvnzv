"""Vercel entrypoint: exposes the FastAPI app (API plus the built frontend) from backend/."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "backend"))

from app.api import app  # noqa: E402,F401