"""
wordsearch/exporter.py
──────────────────────
In-memory ZIP bundler for word-search puzzles.

Pipeline
────────
    1. generate_wordsearch()    → WordGrid          (pure Python, no I/O)
    2. build_puzzle_pdf()       → BytesIO            (ReportLab B&W vectors)
    3. build_answer_pdf()       → BytesIO            (ReportLab B&W vectors)
    4. zipfile.ZipFile()        → zip BytesIO        (stdlib, no I/O)
"""

from __future__ import annotations

import io
import zipfile
from datetime import datetime
from typing import List, Optional

from wordsearch.generator import generate_wordsearch
from wordsearch.renderer import build_puzzle_pdf, build_answer_pdf


def export_wordsearch_zip(
    words:            List[str],
    rows:             int = 15,
    cols:             int = 15,
    seed:             Optional[int] = None,
    title:            str = "Word Search",
    puzzle_filename:  str = "wordsearch_puzzle.pdf",
    answer_filename:  str = "wordsearch_answer.pdf",
) -> io.BytesIO:
    """
    Generate a word-search, render both PDFs, and return a zip archive
    — entirely in memory.

    Parameters
    ----------
    words            : words to hide in the grid
    rows, cols       : grid dimensions (5–30)
    seed             : RNG seed for reproducibility
    title            : heading on both PDF pages
    puzzle_filename  : entry name for puzzle PDF in the zip
    answer_filename  : entry name for answer PDF in the zip

    Returns
    -------
    io.BytesIO
        In-memory zip seeked to position 0.
    """
    if not (5 <= rows <= 40) or not (5 <= cols <= 40):
        raise ValueError(f"rows and cols must be between 5 and 40, got {rows}×{cols}")
    if not words:
        raise ValueError("At least one word must be provided.")

    # Step 1: Generate
    wg = generate_wordsearch(words=words, rows=rows, cols=cols, seed=seed)

    # Step 2: Render PDFs
    timestamp = datetime.now().strftime("%Y-%m-%d")
    footer    = f"{title}  ·  {wg.rows}×{wg.cols} grid  ·  {timestamp}"

    puzzle_buf = build_puzzle_pdf(wg, title=title, footer=footer)
    answer_buf = build_answer_pdf(
        wg,
        title=f"{title} — Answer Key",
        footer=f"{footer}  ·  {len(wg.hidden_words)} words hidden",
    )

    # Step 3: Zip
    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, mode="w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        zf.writestr(puzzle_filename, puzzle_buf.read())
        zf.writestr(answer_filename, answer_buf.read())

    zip_buf.seek(0)
    return zip_buf
