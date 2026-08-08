"""
api/routes.py
─────────────
All API route handlers, kept separate from app setup for testability.
"""
from __future__ import annotations

import asyncio
import io
import random
from functools import partial

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from api.models import (
    GenerateRequest,
    WordSearchRequest,
    HealthResponse,
    WordSearchPreviewResponse,
    MazePreviewResponse,
    PlacementModel,
    CrosswordRequest,
    CrosswordPlacementModel,
    CrosswordPreviewResponse,
)
from exporter import export_maze_zip
from maze.generator import generate_maze
from maze.solver import solve_maze
from wordsearch.generator import generate_wordsearch
from wordsearch.exporter import export_wordsearch_zip
from crossword.generator import generate_crossword
from crossword.exporter import export_crossword_zip

router = APIRouter()

_VERSION = "1.0.0"


# ── health ────────────────────────────────────────────────────────────────────

@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Liveness check",
    tags=["meta"],
)
async def health() -> HealthResponse:
    """Returns 200 OK when the service is up."""
    return HealthResponse(status="ok", version=_VERSION)


# ── preview wordsearch ────────────────────────────────────────────────────────

@router.post(
    "/preview/wordsearch",
    response_model=WordSearchPreviewResponse,
    summary="Generate word search grid JSON for live preview",
    tags=["wordsearch"],
)
async def preview_wordsearch(req: WordSearchRequest) -> WordSearchPreviewResponse:
    """Runs Python wordsearch generator and returns grid JSON for 100% accurate web preview."""
    loop = asyncio.get_running_loop()
    seed_used = req.seed if req.seed is not None else random.randint(1, 999999)

    try:
        wg = await loop.run_in_executor(
            None,
            partial(
                generate_wordsearch,
                words=req.words,
                rows=req.rows,
                cols=req.cols,
                seed=seed_used,
            ),
        )
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    placements_data = [
        PlacementModel(
            word=pl.word,
            row=pl.row,
            col=pl.col,
            dr=pl.dr,
            dc=pl.dc,
            cells=[[r, c] for r, c in pl.cells],
        )
        for pl in wg.placements
    ]

    return WordSearchPreviewResponse(
        rows=wg.rows,
        cols=wg.cols,
        grid=wg.grid,
        placements=placements_data,
        hidden_words=wg.hidden_words,
        missed_words=wg.missed_words,
        seed_used=seed_used,
    )


# ── preview maze ──────────────────────────────────────────────────────────────

@router.post(
    "/preview/maze",
    response_model=MazePreviewResponse,
    summary="Generate maze grid JSON for live preview",
    tags=["maze"],
)
async def preview_maze(req: GenerateRequest) -> MazePreviewResponse:
    """Runs Python maze generator & solver, returning grid JSON for 100% accurate web preview."""
    loop = asyncio.get_running_loop()
    seed_used = req.seed if req.seed is not None else random.randint(1, 999999)

    try:
        def _build():
            m = generate_maze(size=req.size, seed=seed_used, shape=req.shape)
            s = solve_maze(m)
            return m, s

        maze, solution = await loop.run_in_executor(None, _build)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return MazePreviewResponse(
        rows=maze.rows,
        cols=maze.cols,
        grid=maze.grid,
        start=list(maze.start),
        end=list(maze.end),
        solution=[[r, c] for r, c in solution],
        seed_used=seed_used,
    )


# ── generate maze ──────────────────────────────────────────────────────────────

@router.post(
    "/generate",
    summary="Generate a maze and return a ZIP of two B&W PDFs",
    response_description="application/zip containing maze_puzzle.pdf and maze_answer.pdf",
    tags=["maze"],
)
async def generate_maze_zip(req: GenerateRequest) -> StreamingResponse:
    """
    Accepts maze parameters, runs the DFS generator + BFS solver + ReportLab
    renderer entirely in memory, and streams the resulting ZIP back to the client.
    """
    loop = asyncio.get_running_loop()

    try:
        zip_buf: io.BytesIO = await loop.run_in_executor(
            None,
            partial(
                export_maze_zip,
                size=req.size,
                seed=req.seed,
                shape=req.shape,
                title=req.title,
                puzzle_filename="maze_puzzle.pdf",
                answer_filename="maze_answer.pdf",
            ),
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Generation failed: {exc}") from exc

    dim = req.size if req.size % 2 == 1 else req.size + 1
    filename = f"maze_{dim}x{dim}.zip"

    return StreamingResponse(
        content=zip_buf,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Maze-Size": str(dim),
            "X-Maze-Seed": str(req.seed) if req.seed is not None else "random",
        },
    )


# ── generate word search ───────────────────────────────────────────────────────

@router.post(
    "/generate/wordsearch",
    summary="Generate a word search and return a ZIP of two PDFs",
    response_description="application/zip containing wordsearch_puzzle.pdf and wordsearch_answer.pdf",
    tags=["wordsearch"],
)
async def generate_wordsearch_zip(req: WordSearchRequest) -> StreamingResponse:
    """
    Accepts word list + grid parameters, generates a word-search puzzle,
    and streams the resulting ZIP back to the client — entirely in memory.
    """
    loop = asyncio.get_running_loop()

    try:
        zip_buf: io.BytesIO = await loop.run_in_executor(
            None,
            partial(
                export_wordsearch_zip,
                words=req.words,
                rows=req.rows,
                cols=req.cols,
                seed=req.seed,
                title=req.title,
                puzzle_filename="wordsearch_puzzle.pdf",
                answer_filename="wordsearch_answer.pdf",
            ),
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Generation failed: {exc}") from exc

    filename = f"wordsearch_{req.rows}x{req.cols}.zip"

    return StreamingResponse(
        content=zip_buf,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-WS-Size": f"{req.rows}x{req.cols}",
            "X-WS-Words": str(len(req.words)),
        },
    )


# ── preview crossword ─────────────────────────────────────────────────────────

@router.post(
    "/preview/crossword",
    response_model=CrosswordPreviewResponse,
    summary="Generate crossword grid JSON for live preview",
    tags=["crossword"],
)
async def preview_crossword(req: CrosswordRequest) -> CrosswordPreviewResponse:
    """Runs Python crossword generator and returns grid JSON for 100% accurate web preview."""
    loop = asyncio.get_running_loop()
    seed_used = req.seed if req.seed is not None else random.randint(1, 999999)

    try:
        cg = await loop.run_in_executor(
            None,
            partial(
                generate_crossword,
                words=req.words,
                seed=seed_used,
            ),
        )
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    placements_data = [
        CrosswordPlacementModel(
            word=p.word,
            clue=p.clue,
            row=p.row,
            col=p.col,
            direction=p.direction,
            number=p.number,
        )
        for p in cg.placements
    ]
    across_data = [
        CrosswordPlacementModel(
            word=p.word,
            clue=p.clue,
            row=p.row,
            col=p.col,
            direction=p.direction,
            number=p.number,
        )
        for p in cg.across_placements
    ]
    down_data = [
        CrosswordPlacementModel(
            word=p.word,
            clue=p.clue,
            row=p.row,
            col=p.col,
            direction=p.direction,
            number=p.number,
        )
        for p in cg.down_placements
    ]

    cell_nums_str = {f"{r},{c}": num for (r, c), num in cg.cell_numbers.items()}

    return CrosswordPreviewResponse(
        rows=cg.rows,
        cols=cg.cols,
        grid=cg.grid,
        placements=placements_data,
        across_placements=across_data,
        down_placements=down_data,
        cell_numbers=cell_nums_str,
        placed_words=cg.placed_words,
        missed_words=cg.missed_words,
        seed_used=seed_used,
    )


# ── generate crossword ────────────────────────────────────────────────────────

@router.post(
    "/generate/crossword",
    summary="Generate a crossword puzzle and return a ZIP of two PDFs",
    response_description="application/zip containing crossword_puzzle.pdf and crossword_answer.pdf",
    tags=["crossword"],
)
async def generate_crossword_zip(req: CrosswordRequest) -> StreamingResponse:
    """
    Accepts word/clue list, generates a crossword puzzle, and streams
    the resulting ZIP back to the client — entirely in memory.
    """
    loop = asyncio.get_running_loop()

    try:
        zip_buf: io.BytesIO = await loop.run_in_executor(
            None,
            partial(
                export_crossword_zip,
                words=req.words,
                seed=req.seed,
                title=req.title,
                puzzle_filename="crossword_puzzle.pdf",
                answer_filename="crossword_answer.pdf",
            ),
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Generation failed: {exc}") from exc

    filename = "crossword_puzzle.zip"

    return StreamingResponse(
        content=zip_buf,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Crossword-Placed": str(len(req.words)),
        },
    )

