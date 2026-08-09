"""
server.py
─────────
FastAPI application factory and entry-point.

Run locally:
    python server.py
    # or
    uvicorn server:app --reload --port 8000
"""
from __future__ import annotations

from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from api.routes import router

# ── path anchors — resolve relative to this file, not the CWD ────────────────

_BASE_DIR = Path(__file__).resolve().parent
_FRONTEND_DIR = _BASE_DIR / "frontend"
_STATIC_DIR = _FRONTEND_DIR / "static"

# ── app factory ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="Puzzle Generator",
    description=(
        "Generates perfect DFS mazes and exports them as vector PDFs "
        "bundled in a ZIP archive — entirely in memory."
    ),
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
# NOTE: `allow_origins=["*"]` + `allow_credentials=True` is invalid per the
# Fetch spec (browsers reject the combination). The SPA is same-origin, so
# credentials are not needed — keep the wildcard but drop the credentials flag.

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=[
        "Content-Disposition",
        "X-Maze-Size",
        "X-Maze-Seed",
        "X-WS-Words",
        "X-WS-Missed",
        "X-Crossword-Placed",
        "X-Crossword-Missed",
    ],
)

# ── API routes ────────────────────────────────────────────────────────────────

app.include_router(router, prefix="/api")

# ── static assets (CSS, JS, images if any) ───────────────────────────────────

app.mount("/static", StaticFiles(directory=_STATIC_DIR), name="static")

# ── SPA catch-all — serve index.html for every non-API route ─────────────────

@app.get("/", include_in_schema=False)
async def serve_index() -> FileResponse:
    return FileResponse(_FRONTEND_DIR / "index.html")


# ── entry points ──────────────────────────────────────────────────────────────

def main() -> None:
    """Console-script entry point (``puzzle-maker``) — production mode."""
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    # `python server.py` keeps the auto-reload dev server
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
