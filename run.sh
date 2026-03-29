#!/bin/bash
# Run the backend server using uv

uv run uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload