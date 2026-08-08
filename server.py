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

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from api.routes import router

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition", "X-Maze-Size", "X-Maze-Seed"],
)

# ── API routes ────────────────────────────────────────────────────────────────

app.include_router(router, prefix="/api")

# ── static assets (CSS, JS, images if any) ───────────────────────────────────

app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

# ── SPA catch-all — serve index.html for every non-API route ─────────────────

@app.get("/", include_in_schema=False)
async def serve_index() -> FileResponse:
    return FileResponse("frontend/index.html")


# ── dev entry-point ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
