"""Vercel entry point: Vercel runs files in /api as serverless functions.

It reuses the exact same FastAPI app as local development and Docker.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.main import app  # noqa: E402,F401  (Vercel looks for the ASGI `app` object)
