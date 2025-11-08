#!/usr/bin/env python
"""
Simple script to start the FastAPI backend server.

Usage:
    python start_backend.py

Or with uvicorn directly:
    uvicorn backend.api.main:app --reload --host 127.0.0.1 --port 8000
"""

import os
import sys
import uvicorn


# Reload is opt-in via environment variable for development only.
RELOAD_TRUE_VALUES = {"1", "true", "True", "TRUE", "yes", "Yes", "YES", "on", "ON"}


def should_enable_reload() -> bool:
    """
    Determine whether uvicorn should run in reload mode.

    Reload is disabled by default for packaged builds.
    Set AI_TUTOR_BACKEND_RELOAD=1 (or true/yes/on) to force reload in development.
    """
    reload_env = os.getenv("AI_TUTOR_BACKEND_RELOAD")
    if reload_env is None:
        return False

    return reload_env in RELOAD_TRUE_VALUES


if __name__ == "__main__":
    reload_enabled = should_enable_reload()
    
    # Debug output
    print(
        "[Backend Startup] "
        f"AI_TUTOR_BACKEND_RELOAD={os.getenv('AI_TUTOR_BACKEND_RELOAD')}, "
        f"reload={reload_enabled}"
    )
    
    server_kwargs = {
        "app": "backend.api.main:app",
        "host": "127.0.0.1",
        "port": 8000,
        "log_level": "info",
    }

    if reload_enabled:
        print("[Backend Startup] Launching Uvicorn with reload=True")
        uvicorn.run(reload=True, **server_kwargs)
    else:
        print("[Backend Startup] Launching Uvicorn with reload=False")
        from uvicorn import Config, Server

        config = Config(**server_kwargs)
        server = Server(config)
        server.run()

