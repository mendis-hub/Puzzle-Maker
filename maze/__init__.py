"""
Puzzle Generator — maze sub-package
Exports the public API surface used by the PDF layer.
"""
from .generator import MazeGrid, generate_maze
from .solver import solve_maze

__all__ = ["MazeGrid", "generate_maze", "solve_maze"]
