"""
exporter.py
───────────
In-memory zip bundler — no hard drive I/O at any step.
"""

from __future__ import annotations

import io
import zipfile
from datetime import datetime
from typing import Optional

from maze.generator import generate_maze
from maze.solver import solve_maze
from pdf.renderer import build_answer_pdf, build_puzzle_pdf


def export_maze_zip(
    size: int = 21,
    seed: Optional[int] = None,
    shape: str = "square",
    title: str = "Maze Puzzle",
    puzzle_filename: str = "maze_puzzle.pdf",
    answer_filename: str = "maze_answer.pdf",
) -> io.BytesIO:
    """
    Generate a shaped maze, solve it, render both PDFs, and return a zip archive
    — all **entirely in memory**. The filesystem is never touched.
    """
    if not (5 <= size <= 101):
        raise ValueError(f"size must be between 5 and 101, got {size}")

    # ── step 1: generate shaped maze ──────────────────────────────────────────
    maze = generate_maze(size=size, seed=seed, shape=shape)

    # ── step 2: solve maze (BFS — guaranteed shortest path) ───────────────────
    solution = solve_maze(maze)

    if not solution:
        raise RuntimeError("Maze solver returned an empty path — the maze may be malformed.")

    # ── step 3: render puzzle PDF (no solution overlay) ───────────────────────
    timestamp = datetime.now().strftime("%Y-%m-%d")
    footer    = f"{title}  ·  {maze.rows}×{maze.cols} grid ({shape.title()})  ·  {timestamp}"

    puzzle_buf = build_puzzle_pdf(
        maze,
        title=title,
        footer=footer,
    )

    # ── step 4: render answer PDF (solution path overlaid) ────────────────────
    answer_buf = build_answer_pdf(
        maze,
        solution_path=solution,
        title=f"{title} — Answer Key",
        footer=f"{footer}  ·  Solution: {len(solution)} steps",
    )

    # ── step 5: zip both BytesIO buffers — no filesystem writes ───────────────
    zip_buf = io.BytesIO()

    with zipfile.ZipFile(
        zip_buf,
        mode="w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=6,
    ) as zf:
        zf.writestr(puzzle_filename, puzzle_buf.read())
        zf.writestr(answer_filename, answer_buf.read())

    zip_buf.seek(0)
    return zip_buf


def get_zip_manifest(zip_buf: io.BytesIO) -> list[dict]:
    """Inspect an in-memory zip buffer and return metadata for each entry."""
    zip_buf.seek(0)
    manifest = []
    with zipfile.ZipFile(zip_buf, mode="r") as zf:
        for info in zf.infolist():
            ratio = (
                1 - info.compress_size / info.file_size
                if info.file_size
                else 0.0
            )
            manifest.append({
                "filename":      info.filename,
                "file_size":     info.file_size,
                "compress_size": info.compress_size,
                "compress_ratio": f"{ratio:.1%}",
            })
    zip_buf.seek(0)
    return manifest
