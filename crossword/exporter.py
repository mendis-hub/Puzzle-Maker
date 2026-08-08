"""
crossword/exporter.py
──────────────────────
In-memory ZIP bundler for crossword puzzles.
"""

from __future__ import annotations

import io
import zipfile
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Union

from crossword.generator import generate_crossword
from crossword.renderer import build_puzzle_pdf, build_answer_pdf


def export_crossword_zip(
    words: List[Union[str, Tuple[str, str], Dict[str, str]]],
    seed: Optional[int] = None,
    title: str = "Crossword puzzle",
    puzzle_filename: str = "crossword_puzzle.pdf",
    answer_filename: str = "crossword_answer.pdf",
) -> io.BytesIO:
    """
    Generate a crossword puzzle, render both PDFs, and return a zip archive
    — entirely in memory.
    """
    if not words:
        raise ValueError("At least one word must be provided.")

    # Step 1: Generate crossword layout
    cg = generate_crossword(words=words, seed=seed)

    # Step 2: Render PDFs
    timestamp = datetime.now().strftime("%Y-%m-%d")
    footer = f"{title}  ·  {cg.rows}×{cg.cols} grid  ·  {timestamp}"

    puzzle_buf = build_puzzle_pdf(cg, title=title, footer=footer)
    answer_buf = build_answer_pdf(
        cg,
        title=f"{title} — Answer Key",
        footer=f"{footer}  ·  {len(cg.placed_words)} words placed",
    )

    # Step 3: Zip
    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, mode="w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        zf.writestr(puzzle_filename, puzzle_buf.read())
        zf.writestr(answer_filename, answer_buf.read())

    zip_buf.seek(0)
    return zip_buf
