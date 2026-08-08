"""
maze/solver.py
──────────────
BFS solver that finds the *shortest* solution path through a MazeGrid.

Algorithm
─────────
Standard breadth-first search on the open (PATH) cells of the grid,
guaranteeing the minimum-step solution — equivalent to:

    from collections import deque

    def solve(grid, start, end):
        queue = deque([(start, [start])])
        seen  = {start}
        while queue:
            pos, path = queue.popleft()
            if pos == end:
                return path
            for nb in neighbours(pos):
                if nb not in seen:
                    seen.add(nb)
                    queue.append((nb, path + [nb]))
        return []   # unsolvable (impossible for a perfect maze)

We store a ``came_from`` dict instead of carrying the full path in the
queue, reconstructing it once the exit is reached — O(n) memory vs O(n²).
"""

from __future__ import annotations

from collections import deque
from typing import Dict, List, Optional, Tuple

from .generator import MazeGrid


SolutionPath = List[Tuple[int, int]]


def solve_maze(maze: MazeGrid) -> SolutionPath:
    """
    Find the shortest path from ``maze.start`` to ``maze.end`` using BFS.

    Parameters
    ----------
    maze : MazeGrid
        A populated maze produced by :func:`~maze.generator.generate_maze`.

    Returns
    -------
    list[tuple[int, int]]
        Ordered list of ``(row, col)`` coordinates forming the solution,
        inclusive of start and end cells.  Returns ``[]`` only if the maze
        is not connected (which cannot happen for a perfect maze).

    Notes
    -----
    Time complexity  : O(R × C)
    Space complexity : O(R × C)
    """
    start: Tuple[int, int] = maze.start
    end:   Tuple[int, int] = maze.end

    # came_from[cell] = previous cell on the shortest path
    came_from: Dict[Tuple[int, int], Optional[Tuple[int, int]]] = {start: None}

    queue: deque[Tuple[int, int]] = deque([start])

    while queue:
        current = queue.popleft()

        if current == end:
            return _reconstruct(came_from, end)

        for neighbour in maze.neighbours(*current):
            if neighbour not in came_from:
                came_from[neighbour] = current
                queue.append(neighbour)

    return []   # should never reach here for a perfect maze


# ── private helpers ───────────────────────────────────────────────────────────

def _reconstruct(
    came_from: Dict[Tuple[int, int], Optional[Tuple[int, int]]],
    end: Tuple[int, int],
) -> SolutionPath:
    """Walk the ``came_from`` chain back to the start and reverse it."""
    path: SolutionPath = []
    node: Optional[Tuple[int, int]] = end
    while node is not None:
        path.append(node)
        node = came_from[node]
    path.reverse()
    return path
