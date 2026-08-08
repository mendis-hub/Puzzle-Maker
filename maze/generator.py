"""
maze/generator.py
─────────────────
Pure-Python Recursive Backtracker (Depth-First Search) maze generator
supporting multiple geometric shapes (Square, Circle, Heart, Star, Triangle, Diamond, Octagon, Cross).

Algorithm overview
──────────────────
The grid is a 2-D array of integers where:

    WALL = 0  ── solid wall cell
    PATH = 1  ── open passage cell

Cells are constrained by `is_inside_shape(r, c, dim, shape)`.
Entrance and exit border cells are carved open on the shape perimeter.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import List, Tuple, Set


# ── cell type constants ───────────────────────────────────────────────────────
WALL: int = 0
PATH: int = 1

# ── DFS cardinal directions (step of 2 — jump over wall cell) ────────────────
_DIRS: List[Tuple[int, int]] = [(-2, 0), (2, 0), (0, -2), (0, 2)]


def is_inside_shape(r: int, c: int, dim: int, shape: str = "square") -> bool:
    """Returns True if cell (r, c) is inside the requested geometric shape boundary."""
    if not shape or shape == "square":
        return True

    center = (dim - 1) / 2.0
    radius = center - 0.5
    if radius <= 0:
        return True

    # Normalize coords to [-1.0, 1.0]
    x = (c - center) / radius
    y = (center - r) / radius   # invert y so top is positive

    dist_sq = x * x + y * y

    if shape == "circle":
        return dist_sq <= 1.0

    elif shape == "heart":
        y_adj = y * 1.15 + 0.1
        return (x * x + y_adj * y_adj - 0.65) ** 3 - (x * x) * (y_adj ** 3) <= 0.0

    elif shape == "star":
        angle = math.atan2(y, x)
        r_val = math.sqrt(dist_sq)
        star_radius = 0.55 + 0.42 * math.cos(5 * angle - math.pi / 2)
        return r_val <= star_radius

    elif shape == "triangle":
        return (y >= -0.85) and (y <= 0.95 - 1.8 * abs(x))

    elif shape == "diamond":
        return (abs(x) + abs(y)) <= 1.02

    elif shape == "octagon":
        k = (abs(x) + abs(y)) / 1.414
        return max(abs(x), abs(y), k) <= 1.0

    elif shape == "cross":
        return (abs(x) <= 0.38 and abs(y) <= 1.0) or (abs(y) <= 0.38 and abs(x) <= 1.0)

    return True


@dataclass
class MazeGrid:
    """
    Container returned by :func:`generate_maze`.

    Attributes
    ----------
    rows, cols : int
        Outer dimensions of the raw grid (always odd).
    grid : list[list[int]]
        ``grid[r][c] == PATH`` → open cell; ``== WALL`` → solid wall.
    start : tuple[int, int]
        ``(row, col)`` of open entrance cell.
    end : tuple[int, int]
        ``(row, col)`` of open exit cell.
    shape : str
        Geometric shape mask name (square, circle, heart, star, triangle, diamond, octagon, cross).
    """
    rows:  int
    cols:  int
    grid:  List[List[int]]
    start: Tuple[int, int]
    end:   Tuple[int, int]
    shape: str = "square"
    cell_count: int = field(init=False)

    def __post_init__(self) -> None:
        self.cell_count = sum(
            1 for r in range(1, self.rows, 2) for c in range(1, self.cols, 2)
            if is_inside_shape(r, c, self.rows, self.shape)
        )

    def in_bounds(self, r: int, c: int) -> bool:
        return 0 <= r < self.rows and 0 <= c < self.cols

    def is_inside(self, r: int, c: int) -> bool:
        return self.in_bounds(r, c) and is_inside_shape(r, c, self.rows, self.shape)

    def is_path(self, r: int, c: int) -> bool:
        return self.in_bounds(r, c) and self.grid[r][c] == PATH

    def neighbours(self, r: int, c: int) -> List[Tuple[int, int]]:
        """4-connected open neighbours of cell (r, c)."""
        return [
            (r + dr, c + dc)
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]
            if self.is_path(r + dr, c + dc)
        ]


def generate_maze(size: int = 21, seed: int | None = None, shape: str = "square") -> MazeGrid:
    """
    Generate a maze inside the specified geometric shape.

    Parameters
    ----------
    size : int
        Desired grid dimension. Must be ≥ 5.
    seed : int | None
        Optional RNG seed for reproducibility.
    shape : str
        Geometric shape mask ('square', 'circle', 'heart', 'star', 'triangle', 'diamond', 'octagon', 'cross').

    Returns
    -------
    MazeGrid
        Populated shaped maze grid.
    """
    if size < 5:
        raise ValueError(f"size must be ≥ 5, got {size}")

    dim: int = size if size % 2 == 1 else size + 1
    rng = random.Random(seed)

    grid: List[List[int]] = [[WALL] * dim for _ in range(dim)]

    # Collect valid room cells inside the shape mask
    valid_rooms: List[Tuple[int, int]] = [
        (r, c) for r in range(1, dim, 2) for c in range(1, dim, 2)
        if is_inside_shape(r, c, dim, shape)
    ]

    if not valid_rooms:
        # Fallback to square if shape mask is too small
        shape = "square"
        valid_rooms = [(r, c) for r in range(1, dim, 2) for c in range(1, dim, 2)]

    dfs_start = valid_rooms[0]
    visited: Set[Tuple[int, int]] = set()

    def _push(r: int, c: int) -> None:
        visited.add((r, c))
        grid[r][c] = PATH
        dirs = rng.sample(_DIRS, len(_DIRS))
        dfs_stack.append([r, c, dirs, 0])

    dfs_stack: List[list] = []
    _push(*dfs_start)

    while dfs_stack:
        frame = dfs_stack[-1]
        r, c, dirs, di = frame

        carved = False
        while di < len(dirs):
            dr, dc = dirs[di]
            di += 1
            frame[3] = di

            nr, nc = r + dr, c + dc
            wr, wc = r + dr // 2, c + dc // 2

            if (
                0 <= nr < dim and 0 <= nc < dim
                and is_inside_shape(nr, nc, dim, shape)
                and (nr, nc) not in visited
            ):
                grid[wr][wc] = PATH
                _push(nr, nc)
                carved = True
                break

        if not carved:
            dfs_stack.pop()

    # Find entrance and exit cells on the outer perimeter of the carved maze
    open_cells = [
        (r, c) for r in range(dim) for c in range(dim)
        if grid[r][c] == PATH
    ]

    if shape == "square":
        start = (1, 0)
        end   = (dim - 2, dim - 1)
        grid[1][0] = PATH
        grid[dim - 2][dim - 1] = PATH
    else:
        # For custom shapes: entrance is top/leftmost open cell; exit is bottom/rightmost open cell
        open_cells.sort(key=lambda p: (p[0], p[1]))
        first_cell = open_cells[0]
        last_cell  = open_cells[-1]

        # Extend entrance to outer border cell if possible
        start = (first_cell[0], max(0, first_cell[1] - 1))
        end   = (last_cell[0], min(dim - 1, last_cell[1] + 1))

        grid[start[0]][start[1]] = PATH
        grid[end[0]][end[1]]     = PATH

    return MazeGrid(rows=dim, cols=dim, grid=grid, start=start, end=end, shape=shape)
