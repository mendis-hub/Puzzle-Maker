"""
crossword/generator.py
───────────────────────
Crossword puzzle generator algorithm with strict placement rules and standard clue numbering.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Union


# ── data structures ───────────────────────────────────────────────────────────

@dataclass
class WordInput:
    word: str
    clue: str


@dataclass
class Placement:
    """Records a word placed on the crossword grid."""
    word:      str
    clue:      str
    row:       int                      # 0-indexed row
    col:       int                      # 0-indexed col
    direction: str                      # 'H' (Horizontal) or 'V' (Vertical)
    number:    int = 0                  # Clue number (1, 2, 3...)

    @property
    def dr(self) -> int:
        return 0 if self.direction == "H" else 1

    @property
    def dc(self) -> int:
        return 1 if self.direction == "H" else 0

    @property
    def cells(self) -> List[Tuple[int, int]]:
        """List of (row, col) coordinates occupied by this word."""
        return [
            (self.row + i * self.dr, self.col + i * self.dc)
            for i in range(len(self.word))
        ]


@dataclass
class CrosswordGrid:
    """
    Container for generated Crossword puzzle.
    """
    rows:              int
    cols:              int
    grid:              List[List[Optional[str]]]
    placements:        List[Placement]
    across_placements: List[Placement]
    down_placements:   List[Placement]
    cell_numbers:      Dict[Tuple[int, int], int]
    placed_words:      List[str]
    missed_words:      List[str]

    def letter_at(self, r: int, c: int) -> Optional[str]:
        return self.grid[r][c]


# ── public API ────────────────────────────────────────────────────────────────

def parse_word_inputs(raw_inputs: List[Union[str, Tuple[str, str], Dict[str, str]]]) -> List[WordInput]:
    """
    Parse inputs in various formats into clean WordInput objects.
    Supported inputs:
      - "WORD: Clue description"
      - "WORD - Clue description"
      - "WORD" (clue defaults to WORD)
      - ("WORD", "Clue")
      - {"word": "WORD", "clue": "Clue"}
    """
    results: List[WordInput] = []
    seen_words: set[str] = set()

    for item in raw_inputs:
        w_raw = ""
        c_raw = ""
        if isinstance(item, str):
            if ":" in item:
                parts = item.split(":", 1)
                w_raw, c_raw = parts[0], parts[1]
            elif "-" in item:
                parts = item.split("-", 1)
                w_raw, c_raw = parts[0], parts[1]
            else:
                w_raw, c_raw = item, item
        elif isinstance(item, (list, tuple)) and len(item) >= 2:
            w_raw, c_raw = str(item[0]), str(item[1])
        elif isinstance(item, dict):
            w_raw = str(item.get("word", ""))
            c_raw = str(item.get("clue", w_raw))
        else:
            continue

        clean_w = "".join(ch for ch in w_raw.upper() if ch.isalpha())
        clean_c = c_raw.strip() if c_raw.strip() else clean_w

        if len(clean_w) >= 2 and clean_w not in seen_words:
            seen_words.add(clean_w)
            results.append(WordInput(word=clean_w, clue=clean_c))

    return results


def generate_crossword(
    words: List[Union[str, Tuple[str, str], Dict[str, str]]],
    seed: Optional[int] = None,
    max_attempts: int = 15,
) -> CrosswordGrid:
    """
    Generate an interlocking crossword layout from a list of words / clues.
    """
    parsed = parse_word_inputs(words)
    if not parsed:
        raise ValueError("No valid words provided (must contain alpha words ≥ 2 letters).")

    rng = random.Random(seed)

    best_result = None
    best_score = -1e9

    # Run multiple placement attempts with varied word orders to find optimal interlocking layout
    for attempt in range(max_attempts):
        candidate_words = list(parsed)
        if attempt > 0:
            # Shuffle order slightly while preferring longer words
            rng.shuffle(candidate_words)
            candidate_words.sort(key=lambda item: len(item.word) + rng.randint(0, 3), reverse=True)
        else:
            # First attempt: strictly longest-first
            candidate_words.sort(key=lambda item: len(item.word), reverse=True)

        res = _build_single_layout(candidate_words, rng)
        if res["score"] > best_score:
            best_score = res["score"]
            best_result = res

    if not best_result or not best_result["placements"]:
        raise ValueError("Failed to place any words into a crossword layout.")

    # Trim layout to bounding box & compute clue numbers
    return _finalize_crossword_grid(best_result, parsed)


# ── layout algorithm implementation ─────────────────────────────────────────

def _build_single_layout(word_inputs: List[WordInput], rng: random.Random) -> dict:
    CANVAS_SIZE = 80
    MID = CANVAS_SIZE // 2
    grid: List[List[Optional[str]]] = [[None] * CANVAS_SIZE for _ in range(CANVAS_SIZE)]

    placements: List[Placement] = []
    missed: List[str] = []

    # Place the first word that fits horizontally in the center as the seed.
    # Words longer than the canvas can never be placed — report them as missed
    # instead of corrupting the grid with negative indices.
    seed = None
    for item in word_inputs:
        if len(item.word) <= CANVAS_SIZE - 2:
            seed = item
            break
        missed.append(item.word)

    if seed is None:
        return {
            "score": -1e9,
            "placements": [],
            "missed": missed,
            "grid": grid,
            "min_r": 0,
            "max_r": -1,
            "min_c": 0,
            "max_c": -1,
        }

    r0 = MID
    c0 = MID - len(seed.word) // 2
    p0 = Placement(word=seed.word, clue=seed.clue, row=r0, col=c0, direction="H")

    _apply_placement(grid, p0)
    placements.append(p0)

    # Place remaining words
    for item in word_inputs:
        if item.word == seed.word:
            continue
        if len(item.word) > CANVAS_SIZE - 2:
            missed.append(item.word)
            continue
        candidates = _find_valid_placements(item, grid, CANVAS_SIZE, placements)
        if not candidates:
            missed.append(item.word)
            continue

        # Score candidates and pick best
        scored_candidates = []
        for cand in candidates:
            sc = _score_placement(cand, grid, placements, CANVAS_SIZE)
            scored_candidates.append((sc, cand))

        scored_candidates.sort(key=lambda x: x[0], reverse=True)
        best_cand = scored_candidates[0][1]

        _apply_placement(grid, best_cand)
        placements.append(best_cand)

    # Compute bounding box
    min_r, max_r = CANVAS_SIZE, -1
    min_c, max_c = CANVAS_SIZE, -1
    total_intersections = 0

    for pl in placements:
        for r, c in pl.cells:
            min_r = min(min_r, r)
            max_r = max(max_r, r)
            min_c = min(min_c, c)
            max_c = max(max_c, c)

    # Calculate overall layout score
    w_box = max_c - min_c + 1
    h_box = max_r - min_r + 1
    aspect_ratio_penalty = abs(w_box - h_box) * 5
    area_penalty = w_box * h_box

    score = (
        len(placements) * 10000
        - len(missed) * 5000
        - area_penalty
        - aspect_ratio_penalty
    )

    return {
        "score": score,
        "placements": placements,
        "missed": missed,
        "grid": grid,
        "min_r": min_r,
        "max_r": max_r,
        "min_c": min_c,
        "max_c": max_c,
    }


def _apply_placement(grid: List[List[Optional[str]]], pl: Placement) -> None:
    for i, ch in enumerate(pl.word):
        grid[pl.row + i * pl.dr][pl.col + i * pl.dc] = ch


def _find_valid_placements(
    item: WordInput,
    grid: List[List[Optional[str]]],
    canvas_size: int,
    placed_list: List[Placement],
) -> List[Placement]:
    valid: List[Placement] = []
    word = item.word
    w_len = len(word)

    # Find letter overlaps with placed words
    for pl in placed_list:
        other_word = pl.word
        opp_dir = "V" if pl.direction == "H" else "H"

        for idx_self, char_self in enumerate(word):
            for idx_other, char_other in enumerate(other_word):
                if char_self != char_other:
                    continue

                # Cell of intersection
                inter_r = pl.row + idx_other * pl.dr
                inter_c = pl.col + idx_other * pl.dc

                # Start cell for candidate word
                if opp_dir == "H":
                    start_r = inter_r
                    start_c = inter_c - idx_self
                else:
                    start_r = inter_r - idx_self
                    start_c = inter_c

                cand = Placement(
                    word=word,
                    clue=item.clue,
                    row=start_r,
                    col=start_c,
                    direction=opp_dir,
                )

                if _is_placement_valid(cand, grid, canvas_size):
                    valid.append(cand)

    return valid


def _is_placement_valid(
    pl: Placement, grid: List[List[Optional[str]]], canvas_size: int
) -> bool:
    word = pl.word
    w_len = len(word)
    dr, dc = pl.dr, pl.dc
    pdr, pdc = pl.dc, pl.dr  # Perpendicular direction

    # 1. Canvas bounds check
    if pl.row < 1 or pl.col < 1:
        return False
    end_r = pl.row + (w_len - 1) * dr
    end_c = pl.col + (w_len - 1) * dc
    if end_r >= canvas_size - 1 or end_c >= canvas_size - 1:
        return False

    # 2. Before-start and after-end cell MUST be empty
    before_r, before_c = pl.row - dr, pl.col - dc
    after_r, after_c = end_r + dr, end_c + dc
    if grid[before_r][before_c] is not None or grid[after_r][after_c] is not None:
        return False

    has_intersection = False

    # 3. Cell-by-cell validation
    for i, ch in enumerate(word):
        r = pl.row + i * dr
        c = pl.col + i * dc
        existing = grid[r][c]

        if existing is not None:
            if existing != ch:
                return False
            has_intersection = True
        else:
            # For non-intersection empty cell, perpendicular neighbours MUST be empty
            side1_r, side1_c = r + pdr, c + pdc
            side2_r, side2_c = r - pdr, c - pdc
            if grid[side1_r][side1_c] is not None or grid[side2_r][side2_c] is not None:
                return False

    return has_intersection


def _score_placement(
    pl: Placement,
    grid: List[List[Optional[str]]],
    placed_list: List[Placement],
    canvas_size: int,
) -> float:
    # Count intersections
    intersections = 0
    for r, c in pl.cells:
        if grid[r][c] is not None:
            intersections += 1

    # Distance from center
    center = canvas_size / 2.0
    mid_r = pl.row + (len(pl.word) / 2.0) * pl.dr
    mid_c = pl.col + (len(pl.word) / 2.0) * pl.dc
    dist_sq = (mid_r - center) ** 2 + (mid_c - center) ** 2

    return (intersections * 500.0) - dist_sq


def _finalize_crossword_grid(result: dict, original_inputs: List[WordInput]) -> CrosswordGrid:
    min_r, max_r = result["min_r"], result["max_r"]
    min_c, max_c = result["min_c"], result["max_c"]
    raw_grid = result["grid"]
    placements = result["placements"]

    rows = max_r - min_r + 1
    cols = max_c - min_c + 1

    # Build trimmed 2D grid
    grid: List[List[Optional[str]]] = [[None] * cols for _ in range(rows)]
    for r in range(rows):
        for c in range(cols):
            grid[r][c] = raw_grid[min_r + r][min_c + c]

    # Adjust placement coordinates
    adjusted_placements: List[Placement] = []
    for pl in placements:
        adj = Placement(
            word=pl.word,
            clue=pl.clue,
            row=pl.row - min_r,
            col=pl.col - min_c,
            direction=pl.direction,
        )
        adjusted_placements.append(adj)

    # Assign clue numbers scanning top-to-bottom, left-to-right
    cell_numbers: Dict[Tuple[int, int], int] = {}
    next_number = 1

    for r in range(rows):
        for c in range(cols):
            starts = [p for p in adjusted_placements if p.row == r and p.col == c]
            if starts:
                cell_numbers[(r, c)] = next_number
                for p in starts:
                    p.number = next_number
                next_number += 1

    across_placements = [p for p in adjusted_placements if p.direction == "H"]
    down_placements = [p for p in adjusted_placements if p.direction == "V"]

    across_placements.sort(key=lambda p: p.number)
    down_placements.sort(key=lambda p: p.number)

    placed_words = [p.word for p in adjusted_placements]
    all_input_words = [item.word for item in original_inputs]
    missed_words = [w for w in all_input_words if w not in placed_words]

    return CrosswordGrid(
        rows=rows,
        cols=cols,
        grid=grid,
        placements=adjusted_placements,
        across_placements=across_placements,
        down_placements=down_placements,
        cell_numbers=cell_numbers,
        placed_words=placed_words,
        missed_words=missed_words,
    )
