"""Vercel FastAPI entrypoint - imports from backend/."""
from backend.main import app as app

# Vercel expects 'app' at module root
