"""
tests/test_pipeline.py
──────────────────────
Automated tests covering the full maze → PDF → zip pipeline.

Run with:
    python -m pytest tests/ -v
"""

from __future__ import annotations

import io
import zipfile
from collections import deque

import pytest

# ── imports under test ────────────────────────────────────────────────────────
from maze.generator import WALL, PATH, MazeGrid, generate_maze
from maze.solver import solve_maze
from pdf.renderer import build_puzzle_pdf, build_answer_pdf
from exporter import export_maze_zip, get_zip_manifest


# ═══════════════════════════════════════════════════════════════════════════════
#  Maze generator tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestMazeGenerator:

    def test_returns_maze_grid(self):
        maze = generate_maze(size=11, seed=0)
        assert isinstance(maze, MazeGrid)

    def test_odd_dimension_preserved(self):
        maze = generate_maze(size=11, seed=0)
        assert maze.rows == 11 and maze.cols == 11

    def test_even_dimension_rounded_up(self):
        maze = generate_maze(size=10, seed=0)
        assert maze.rows == 11 and maze.cols == 11

    def test_size_too_small_raises(self):
        with pytest.raises(ValueError):
            generate_maze(size=3)

    def test_start_and_end_are_path(self):
        maze = generate_maze(size=11, seed=1)
        sr, sc = maze.start
        er, ec = maze.end
        assert maze.grid[sr][sc] == PATH
        assert maze.grid[er][ec] == PATH

    def test_grid_values_binary(self):
        """Every cell must be exactly WALL or PATH."""
        maze = generate_maze(size=15, seed=2)
        for row in maze.grid:
            for cell in row:
                assert cell in (WALL, PATH), f"unexpected cell value: {cell}"

    def test_perfect_maze_fully_connected(self):
        """
        A perfect maze is fully connected: every PATH cell must be reachable
        from the start via BFS.
        """
        maze = generate_maze(size=13, seed=3)
        visited = set()
        queue = deque([maze.start])
        visited.add(maze.start)
        while queue:
            r, c = queue.popleft()
            for nb in maze.neighbours(r, c):
                if nb not in visited:
                    visited.add(nb)
                    queue.append(nb)

        # Count all PATH cells
        all_path = {
            (r, c)
            for r in range(maze.rows)
            for c in range(maze.cols)
            if maze.grid[r][c] == PATH
        }
        assert visited == all_path, (
            f"Maze is not fully connected. "
            f"Reachable: {len(visited)}, total PATH: {len(all_path)}"
        )

    def test_cell_count(self):
        maze = generate_maze(size=21, seed=4)
        expected = (maze.rows // 2) * (maze.cols // 2)
        assert maze.cell_count == expected

    def test_reproducible_with_seed(self):
        m1 = generate_maze(size=11, seed=99)
        m2 = generate_maze(size=11, seed=99)
        assert m1.grid == m2.grid

    def test_different_seeds_differ(self):
        m1 = generate_maze(size=11, seed=1)
        m2 = generate_maze(size=11, seed=2)
        # Very unlikely to be identical
        assert m1.grid != m2.grid


# ═══════════════════════════════════════════════════════════════════════════════
#  Shaped maze tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestMazeShapes:

    @pytest.mark.parametrize("shape", ["circle", "heart", "triangle", "diamond",
                                       "octagon", "cross", "vrect"])
    def test_shape_generates_valid_maze(self, shape):
        """Every advertised shape must produce a solvable, fully-connected maze."""
        maze = generate_maze(size=21, seed=7, shape=shape)
        assert maze.shape == shape

        # All cells are WALL, PATH, or VOID (outside the shape)
        for row in maze.grid:
            for cell in row:
                assert cell in (WALL, PATH, -1)

        # All PATH cells inside shape are connected
        visited = set()
        queue = deque([maze.start])
        visited.add(maze.start)
        while queue:
            r, c = queue.popleft()
            for nb in maze.neighbours(r, c):
                if nb not in visited:
                    visited.add(nb)
                    queue.append(nb)

        all_path = {
            (r, c)
            for r in range(maze.rows)
            for c in range(maze.cols)
            if maze.grid[r][c] == PATH
        }
        assert visited == all_path, f"shape={shape} maze is not fully connected"

        # Solvable start → end
        path = solve_maze(maze)
        assert path[0] == maze.start and path[-1] == maze.end

    def test_unknown_shape_behaves_like_square(self):
        """An unknown shape keeps its label but must behave like a plain square maze."""
        maze = generate_maze(size=15, seed=1, shape="torus")
        assert maze.cell_count == (maze.rows // 2) * (maze.cols // 2)
        path = solve_maze(maze)
        assert path[0] == maze.start and path[-1] == maze.end


# ═══════════════════════════════════════════════════════════════════════════════
#  Solver tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestSolver:

    def test_solution_is_non_empty(self):
        maze = generate_maze(size=11, seed=5)
        path = solve_maze(maze)
        assert len(path) > 0

    def test_solution_starts_at_start(self):
        maze = generate_maze(size=11, seed=6)
        path = solve_maze(maze)
        assert path[0] == maze.start

    def test_solution_ends_at_end(self):
        maze = generate_maze(size=11, seed=7)
        path = solve_maze(maze)
        assert path[-1] == maze.end

    def test_solution_all_cells_are_path(self):
        maze = generate_maze(size=15, seed=8)
        path = solve_maze(maze)
        for r, c in path:
            assert maze.grid[r][c] == PATH, f"Solution passes through WALL at ({r},{c})"

    def test_solution_steps_are_adjacent(self):
        """Consecutive cells in the solution must be 4-connected neighbours."""
        maze = generate_maze(size=15, seed=9)
        path = solve_maze(maze)
        for (r1, c1), (r2, c2) in zip(path, path[1:]):
            dist = abs(r2 - r1) + abs(c2 - c1)
            assert dist == 1, f"Non-adjacent step: ({r1},{c1}) → ({r2},{c2})"

    def test_larger_maze_solvable(self):
        maze = generate_maze(size=41, seed=10)
        path = solve_maze(maze)
        assert path[-1] == maze.end


# ═══════════════════════════════════════════════════════════════════════════════
#  PDF renderer tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestPDFRenderer:

    @pytest.fixture(scope="class")
    def small_maze(self):
        return generate_maze(size=11, seed=42)

    def test_puzzle_pdf_returns_bytesio(self, small_maze):
        buf = build_puzzle_pdf(small_maze)
        assert isinstance(buf, io.BytesIO)

    def test_puzzle_pdf_starts_with_pdf_magic(self, small_maze):
        buf = build_puzzle_pdf(small_maze)
        assert buf.read(4) == b"%PDF"

    def test_puzzle_pdf_non_empty(self, small_maze):
        buf = build_puzzle_pdf(small_maze)
        buf.seek(0, 2)   # seek to end
        assert buf.tell() > 1024, "PDF is suspiciously small"

    def test_answer_pdf_returns_bytesio(self, small_maze):
        solution = solve_maze(small_maze)
        buf = build_answer_pdf(small_maze, solution)
        assert isinstance(buf, io.BytesIO)

    def test_answer_pdf_starts_with_pdf_magic(self, small_maze):
        solution = solve_maze(small_maze)
        buf = build_answer_pdf(small_maze, solution)
        assert buf.read(4) == b"%PDF"

    def test_answer_pdf_larger_than_puzzle(self, small_maze):
        """Answer PDF should be (slightly) larger due to solution path data."""
        solution = solve_maze(small_maze)
        puzzle_size = build_puzzle_pdf(small_maze).seek(0, 2) or \
                      _buf_size(build_puzzle_pdf(small_maze))
        answer_size = _buf_size(build_answer_pdf(small_maze, solution))
        assert answer_size >= puzzle_size   # allow equality for tiny mazes

    def test_pdf_seeked_to_zero(self, small_maze):
        buf = build_puzzle_pdf(small_maze)
        assert buf.tell() == 0


def _buf_size(buf: io.BytesIO) -> int:
    pos = buf.seek(0, 2)
    buf.seek(0)
    return pos


# ═══════════════════════════════════════════════════════════════════════════════
#  Exporter / zip tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestExporter:

    def test_returns_bytesio(self):
        buf = export_maze_zip(size=11, seed=0)
        assert isinstance(buf, io.BytesIO)

    def test_zip_magic_bytes(self):
        buf = export_maze_zip(size=11, seed=1)
        assert buf.read(2) == b"PK", "Buffer does not start with ZIP magic bytes"

    def test_zip_contains_two_entries(self):
        buf = export_maze_zip(size=11, seed=2)
        with zipfile.ZipFile(buf) as zf:
            assert len(zf.namelist()) == 2

    def test_zip_default_filenames(self):
        buf = export_maze_zip(size=11, seed=3)
        with zipfile.ZipFile(buf) as zf:
            names = zf.namelist()
        assert "maze_puzzle.pdf" in names
        assert "maze_answer.pdf" in names

    def test_zip_custom_filenames(self):
        buf = export_maze_zip(
            size=11, seed=4,
            puzzle_filename="p.pdf",
            answer_filename="a.pdf",
        )
        with zipfile.ZipFile(buf) as zf:
            names = zf.namelist()
        assert "p.pdf" in names and "a.pdf" in names

    def test_zip_entries_are_valid_pdfs(self):
        buf = export_maze_zip(size=11, seed=5)
        with zipfile.ZipFile(buf) as zf:
            for name in zf.namelist():
                data = zf.read(name)
                assert data[:4] == b"%PDF", f"{name} is not a valid PDF"

    def test_size_out_of_range_raises(self):
        with pytest.raises(ValueError):
            export_maze_zip(size=3)
        with pytest.raises(ValueError):
            export_maze_zip(size=105)

    def test_reproducible_zip_size(self):
        """
        Same seed → maze is identical → PDF content is structurally identical.

        ReportLab embeds a wall-clock creation timestamp in the PDF metadata
        block, so the raw byte count may differ by up to ~64 bytes between
        calls made in rapid succession.  We allow a small tolerance rather
        than fighting the library internals.
        """
        s1 = _buf_size(export_maze_zip(size=11, seed=77))
        s2 = _buf_size(export_maze_zip(size=11, seed=77))
        assert abs(s1 - s2) <= 64, (
            f"Zip sizes diverged too much: {s1} vs {s2} (delta={abs(s1-s2)} B). "
            "Check if non-deterministic data beyond the timestamp is leaking."
        )

    def test_manifest_helper(self):
        buf = export_maze_zip(size=11, seed=6)
        manifest = get_zip_manifest(buf)
        assert len(manifest) == 2
        for entry in manifest:
            assert entry["file_size"] > 0
            assert "compress_ratio" in entry

    def test_buffer_rewound_after_manifest(self):
        """get_zip_manifest must leave the buffer at position 0."""
        buf = export_maze_zip(size=11, seed=7)
        get_zip_manifest(buf)
        assert buf.tell() == 0

    @pytest.mark.parametrize("size", [11, 21, 31])
    def test_various_sizes_produce_valid_zip(self, size):
        buf = export_maze_zip(size=size, seed=0)
        with zipfile.ZipFile(buf) as zf:
            assert len(zf.namelist()) == 2
