#!/usr/bin/env python
"""
Simple script to start the FastAPI backend server.

Usage:
    python start_backend.py

Or with uvicorn directly:
    uvicorn backend.api.main:app --reload --host 127.0.0.1 --port 8000
"""

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "backend.api.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info",
    )

