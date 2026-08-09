"""
wordsearch/generator.py
───────────────────────
Word Search puzzle generator.

Algorithm
─────────
1. Sanitise and deduplicate the word list (upper-case, alpha-only).
2. Sort words longest-first so large words get placed first (fewer conflicts).
3. For each word try up to MAX_ATTEMPTS random (row, col, direction) combos.
4. If a cell is already occupied it must contain the same letter (collision ok).
5. Fill remaining empty cells with random uppercase letters.

Directions
──────────
All eight reading directions are supported (forward & reverse, matching the
frontend's "8-direction placement" feature):

    (dr, dc) ∈ {(0, 1), (1, 0), (1, 1), (0, -1), (-1, 0), (1, -1), (-1, 1), (-1, -1)}
    • (0, 1)   = Horizontal (Left to Right)
    • (0, -1)  = Horizontal (Right to Left)
    • (1, 0)   = Vertical (Top to Bottom)
    • (-1, 0)  = Vertical (Bottom to Top)
    • (1, 1)   = Diagonal (Top-Left to Bottom-Right)
    • (1, -1)  = Diagonal (Top-Right to Bottom-Left)
    • (-1, 1)  = Diagonal (Bottom-Left to Top-Right)
    • (-1, -1) = Diagonal (Bottom-Right to Top-Left)

Callers that want forward-only puzzles (e.g. for younger solvers) can pass
``directions=[(0, 1), (1, 0), (1, 1)]`` explicitly.
"""

from __future__ import annotations

import random
import string
from dataclasses import dataclass
from typing import List, Optional, Tuple


# ── constants ─────────────────────────────────────────────────────────────────

EMPTY = "."

# All 8 reading directions (forward & reverse)
DIRECTIONS: List[Tuple[int, int]] = [
    (0, 1),    # Horizontal (Left -> Right)
    (0, -1),   # Horizontal (Right -> Left)
    (1, 0),    # Vertical (Top -> Bottom)
    (-1, 0),   # Vertical (Bottom -> Top)
    (1, 1),    # Diagonal (Top-Left -> Bottom-Right)
    (1, -1),   # Diagonal (Top-Right -> Bottom-Left)
    (-1, 1),   # Diagonal (Bottom-Left -> Top-Right)
    (-1, -1),  # Diagonal (Bottom-Right -> Top-Left)
]

# Forward-only subset — useful for simpler puzzles aimed at young solvers
FORWARD_DIRECTIONS: List[Tuple[int, int]] = [
    (0, 1),   # Horizontal (Left -> Right)
    (1, 0),   # Vertical (Top -> Bottom)
    (1, 1),   # Diagonal (Top-Left -> Bottom-Right)
]

MAX_ATTEMPTS = 500   # per word


# ── data classes ──────────────────────────────────────────────────────────────

@dataclass
class Placement:
    """Records where a word was placed in the grid."""
    word:   str
    row:    int                   # start row
    col:    int                   # start col
    dr:     int                   # row direction step
    dc:     int                   # col direction step

    @property
    def cells(self) -> List[Tuple[int, int]]:
        """Return all (row, col) cells occupied by this word."""
        return [
            (self.row + i * self.dr, self.col + i * self.dc)
            for i in range(len(self.word))
        ]


@dataclass
class WordGrid:
    """
    Container returned by :func:`generate_wordsearch`.

    Attributes
    ----------
    rows, cols      : grid dimensions
    grid            : 2-D list of uppercase letters (no EMPTY cells after fill)
    placements      : successfully placed words with their coordinates
    hidden_words    : words actually placed (subset of input)
    missed_words    : words that could not be placed (too long or no room)
    """
    rows:         int
    cols:         int
    grid:         List[List[str]]
    placements:   List[Placement]
    hidden_words: List[str]
    missed_words: List[str]

    def letter_at(self, r: int, c: int) -> str:
        return self.grid[r][c]

    def in_bounds(self, r: int, c: int) -> bool:
        return 0 <= r < self.rows and 0 <= c < self.cols


# ── public API ────────────────────────────────────────────────────────────────

def generate_wordsearch(
    words: List[str],
    rows:  int = 15,
    cols:  int = 15,
    seed:  Optional[int] = None,
    directions: Optional[List[Tuple[int, int]]] = None,
) -> WordGrid:
    """
    Generate a word-search grid using all 8 reading directions by default.

    Parameters
    ----------
    words      : list of words to hide (any case, non-alpha chars stripped)
    rows, cols : grid dimensions (5–40 each)
    seed       : RNG seed for reproducibility
    directions : subset of DIRECTIONS to allow (default: all 8 directions)

    Returns
    -------
    WordGrid
        Fully filled grid. Check ``missed_words`` for any that didn't fit.
    """
    if rows < 5 or cols < 5:
        raise ValueError(f"Grid must be at least 5×5, got {rows}×{cols}")

    dirs = directions or DIRECTIONS
    rng  = random.Random(seed)

    # Sanitise words
    clean: List[str] = []
    seen:  set[str]  = set()
    missed_words: List[str] = []
    for w in words:
        w_clean = "".join(ch for ch in w.upper() if ch.isalpha())
        if not w_clean or w_clean in seen:
            continue
        seen.add(w_clean)
        if len(w_clean) > max(rows, cols):
            # Physically impossible to fit — report honestly as missed
            missed_words.append(w_clean)
        else:
            clean.append(w_clean)

    # Sort longest-first
    clean.sort(key=len, reverse=True)

    # Initialise empty grid
    grid: List[List[str]] = [[EMPTY] * cols for _ in range(rows)]

    placements:   List[Placement] = []
    hidden_words: List[str]       = []

    for word in clean:
        placed = _try_place(word, grid, rows, cols, dirs, rng)
        if placed:
            placements.append(placed)
            hidden_words.append(word)
        else:
            missed_words.append(word)

    # Fill empties with random letters
    alphabet = string.ascii_uppercase
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == EMPTY:
                grid[r][c] = rng.choice(alphabet)

    return WordGrid(
        rows=rows,
        cols=cols,
        grid=grid,
        placements=placements,
        hidden_words=hidden_words,
        missed_words=missed_words,
    )


# ── private helpers ───────────────────────────────────────────────────────────

def _try_place(
    word:  str,
    grid:  List[List[str]],
    rows:  int,
    cols:  int,
    dirs:  List[Tuple[int, int]],
    rng:   random.Random,
) -> Optional[Placement]:
    """Attempt to place *word* at a random valid position. Returns Placement or None."""
    n = len(word)
    attempts = 0

    while attempts < MAX_ATTEMPTS:
        attempts += 1
        dr, dc = rng.choice(dirs)

        # Valid start-coordinate ranges for this (dr, dc) step
        if dr == 1:
            r_min, r_max = 0, rows - n
        elif dr == -1:
            r_min, r_max = n - 1, rows - 1
        else:
            r_min, r_max = 0, rows - 1

        if dc == 1:
            c_min, c_max = 0, cols - n
        elif dc == -1:
            c_min, c_max = n - 1, cols - 1
        else:
            c_min, c_max = 0, cols - 1

        if r_min > r_max or c_min > c_max:
            continue

        r = rng.randint(r_min, r_max)
        c = rng.randint(c_min, c_max)

        ok = True
        for i, ch in enumerate(word):
            cell = grid[r + i * dr][c + i * dc]
            if cell != EMPTY and cell != ch:
                ok = False
                break

        if ok:
            for i, ch in enumerate(word):
                grid[r + i * dr][c + i * dc] = ch
            return Placement(word=word, row=r, col=c, dr=dr, dc=dc)

    return None
