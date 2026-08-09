"""
tests/test_wordsearch.py
────────────────────────
Automated tests covering the word-search generator, PDF renderer,
ZIP exporter, and API endpoints.

Run with:
    python -m pytest tests/test_wordsearch.py -v
"""

from __future__ import annotations

import io
import zipfile

import pytest

from wordsearch.generator import (
    DIRECTIONS,
    FORWARD_DIRECTIONS,
    EMPTY,
    WordGrid,
    generate_wordsearch,
)
from wordsearch.exporter import export_wordsearch_zip

SAMPLE_WORDS = ["PYTHON", "FASTAPI", "MAZE", "PUZZLE", "SOLVER"]


# ═══════════════════════════════════════════════════════════════════════════════
#  Generator tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestWordSearchGenerator:

    def test_returns_word_grid(self):
        wg = generate_wordsearch(SAMPLE_WORDS, rows=15, cols=15, seed=42)
        assert isinstance(wg, WordGrid)

    def test_grid_dimensions(self):
        wg = generate_wordsearch(SAMPLE_WORDS, rows=12, cols=18, seed=1)
        assert wg.rows == 12 and wg.cols == 18

    def test_grid_fully_filled(self):
        """After generation there must be no EMPTY cells left."""
        wg = generate_wordsearch(SAMPLE_WORDS, rows=10, cols=10, seed=2)
        for row in wg.grid:
            for cell in row:
                assert cell != EMPTY
                assert cell.isalpha() and cell.isupper()

    def test_all_words_hidden_or_missed(self):
        wg = generate_wordsearch(SAMPLE_WORDS, rows=15, cols=15, seed=3)
        assert set(wg.hidden_words) | set(wg.missed_words) == set(SAMPLE_WORDS)

    def test_placements_within_bounds(self):
        wg = generate_wordsearch(SAMPLE_WORDS, rows=15, cols=15, seed=4)
        for pl in wg.placements:
            for r, c in pl.cells:
                assert 0 <= r < wg.rows
                assert 0 <= c < wg.cols

    def test_placement_cells_match_word(self):
        wg = generate_wordsearch(SAMPLE_WORDS, rows=15, cols=15, seed=5)
        for pl in wg.placements:
            letters = [wg.grid[r][c] for r, c in pl.cells]
            assert "".join(letters) == pl.word

    def test_placement_directions_are_valid(self):
        wg = generate_wordsearch(SAMPLE_WORDS, rows=15, cols=15, seed=6)
        for pl in wg.placements:
            assert (pl.dr, pl.dc) in DIRECTIONS

    def test_reproducible_with_seed(self):
        w1 = generate_wordsearch(SAMPLE_WORDS, rows=15, cols=15, seed=99)
        w2 = generate_wordsearch(SAMPLE_WORDS, rows=15, cols=15, seed=99)
        assert w1.grid == w2.grid
        assert [(p.word, p.row, p.col, p.dr, p.dc) for p in w1.placements] == \
               [(p.word, p.row, p.col, p.dr, p.dc) for p in w2.placements]

    def test_different_seeds_differ(self):
        w1 = generate_wordsearch(SAMPLE_WORDS, rows=15, cols=15, seed=1)
        w2 = generate_wordsearch(SAMPLE_WORDS, rows=15, cols=15, seed=2)
        assert w1.grid != w2.grid

    def test_words_sanitised(self):
        """Non-alpha chars stripped, case normalised, duplicates removed."""
        wg = generate_wordsearch(["p-y-t-h-o-n!", "python", "  MAZE  ", "123"], rows=10, cols=10, seed=7)
        assert "PYTHON" in wg.hidden_words or "PYTHON" in wg.missed_words
        assert "MAZE" in wg.hidden_words or "MAZE" in wg.missed_words
        assert len(wg.hidden_words) + len(wg.missed_words) == 2

    def test_empty_words_dropped(self):
        """Empty / non-alpha words are dropped; single letters are allowed."""
        wg = generate_wordsearch(["A", "B!", "  ", "OK"], rows=10, cols=10, seed=8)
        names = set(wg.hidden_words) | set(wg.missed_words)
        assert names == {"OK", "A", "B"}

    def test_overlong_word_reported_missed(self):
        """Words longer than the grid must be reported, not silently dropped."""
        wg = generate_wordsearch(["HI", "SUPERCALIFRAGILISTICEXPIALIDOCIOUS"], rows=8, cols=8, seed=9)
        assert "SUPERCALIFRAGILISTICEXPIALIDOCIOUS" in wg.missed_words
        assert wg.missed_words.count("SUPERCALIFRAGILISTICEXPIALIDOCIOUS") == 1

    def test_grid_too_small_raises(self):
        with pytest.raises(ValueError):
            generate_wordsearch(SAMPLE_WORDS, rows=4, cols=10)

    def test_forward_directions_only(self):
        """Restricting to forward directions must never place reverse words."""
        wg = generate_wordsearch(SAMPLE_WORDS, rows=20, cols=20, seed=10,
                                 directions=FORWARD_DIRECTIONS)
        for pl in wg.placements:
            assert pl.dr >= 0
            assert pl.dc >= 0

    def test_all_8_directions_reachable(self):
        """Across a sweep of seeds, every supported direction gets used."""
        dirs_used = set()
        words = ["PYTHON", "FASTAPI", "MAZE", "PUZZLE", "SOLVER", "ALGORITHM",
                 "BREADTH", "RECURSION", "CANVAS", "VECTOR"]
        for seed in range(80):
            wg = generate_wordsearch(words, rows=25, cols=25, seed=seed)
            dirs_used |= {(p.dr, p.dc) for p in wg.placements}
        assert dirs_used == set(DIRECTIONS), f"missing directions: {set(DIRECTIONS) - dirs_used}"

    def test_no_duplicate_placements(self):
        """The same word must not appear twice in placements."""
        wg = generate_wordsearch(SAMPLE_WORDS, rows=15, cols=15, seed=11)
        words = [p.word for p in wg.placements]
        assert len(words) == len(set(words))


# ═══════════════════════════════════════════════════════════════════════════════
#  Exporter tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestWordSearchExporter:

    def test_returns_bytesio(self):
        buf = export_wordsearch_zip(SAMPLE_WORDS, rows=12, cols=12, seed=0)
        assert isinstance(buf, io.BytesIO)

    def test_zip_magic_bytes(self):
        buf = export_wordsearch_zip(SAMPLE_WORDS, rows=12, cols=12, seed=1)
        assert buf.read(2) == b"PK"

    def test_zip_contains_two_pdfs(self):
        buf = export_wordsearch_zip(SAMPLE_WORDS, rows=12, cols=12, seed=2)
        with zipfile.ZipFile(buf) as zf:
            names = zf.namelist()
            assert "wordsearch_puzzle.pdf" in names
            assert "wordsearch_answer.pdf" in names
            for name in names:
                assert zf.read(name)[:4] == b"%PDF"

    def test_custom_filenames(self):
        buf = export_wordsearch_zip(SAMPLE_WORDS, rows=12, cols=12, seed=3,
                                    puzzle_filename="p.pdf", answer_filename="a.pdf")
        with zipfile.ZipFile(buf) as zf:
            assert "p.pdf" in zf.namelist() and "a.pdf" in zf.namelist()

    def test_bad_dims_raise(self):
        with pytest.raises(ValueError):
            export_wordsearch_zip(SAMPLE_WORDS, rows=50, cols=12)

    def test_empty_words_raise(self):
        with pytest.raises(ValueError):
            export_wordsearch_zip([], rows=12, cols=12)

    def test_stats_out_param(self):
        stats: dict = {}
        export_wordsearch_zip(SAMPLE_WORDS, rows=15, cols=15, seed=4, stats=stats)
        assert "hidden" in stats and "missed" in stats
        assert stats["hidden"] + stats["missed"] == len(SAMPLE_WORDS)

    def test_stats_reflect_missed_words(self):
        stats: dict = {}
        export_wordsearch_zip(["HI", "A" * 40], rows=8, cols=8, seed=5, stats=stats)
        assert stats["hidden"] == 1
        assert stats["missed"] == 1

    def test_directions_passthrough(self):
        stats: dict = {}
        export_wordsearch_zip(SAMPLE_WORDS, rows=20, cols=20, seed=6,
                              directions=FORWARD_DIRECTIONS, stats=stats)
        assert stats["hidden"] > 0
