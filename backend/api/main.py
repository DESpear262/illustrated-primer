"""
FastAPI application for AI Tutor Proof of Concept.

Provides REST API endpoints for all facade methods and WebSocket support
for live updates. Designed for Tauri integration with localhost-only CORS policy.
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Dict, Any
import logging

from src.config import DB_PATH, FAISS_INDEX_PATH
from src.interface_common.app_facade import AppFacade
from backend.api.facade import set_facade, get_facade as _get_facade
from backend.api.routes import (
    db,
    index,
    ai,
    chat,
    graph,
    hover,
    review,
    import_route,
    refresh,
    progress,
    websocket as websocket_route,
)

# Configure logging
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI app.
    
    Initializes facade on startup and cleans up on shutdown.
    """
    global facade
    
    # Startup
    logger.info("Initializing FastAPI application...")
    facade_instance = AppFacade(db_path=DB_PATH, index_path=FAISS_INDEX_PATH)
    set_facade(facade_instance)
    logger.info("Facade initialized successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down FastAPI application...")
    set_facade(None)


# Create FastAPI app
app = FastAPI(
    title="AI Tutor API",
    description="REST API for AI Tutor Proof of Concept",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS - localhost only
# Include common development ports for Vite and other dev servers
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite default port
        "http://localhost:3000",  # Common React dev port
        "http://localhost:8080",  # Common dev port
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8080",
        "http://localhost",       # Fallback for port 80
        "http://127.0.0.1",       # Fallback for port 80
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(db.router, prefix="/api/db", tags=["database"])
app.include_router(index.router, prefix="/api/index", tags=["index"])
app.include_router(ai.router, prefix="/api/ai", tags=["ai"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(graph.router, prefix="/api/graph", tags=["graph"])
app.include_router(hover.router, prefix="/api/hover", tags=["hover"])
app.include_router(review.router, prefix="/api/review", tags=["review"])
app.include_router(import_route.router, prefix="/api/import", tags=["import"])
app.include_router(refresh.router, prefix="/api/refresh", tags=["refresh"])
app.include_router(progress.router, prefix="/api/progress", tags=["progress"])
app.include_router(websocket_route.router, prefix="/ws", tags=["websocket"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "AI Tutor API", "version": "1.0.0"}


@app.get("/api/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}


# Re-export get_facade for convenience
get_facade = _get_facade

