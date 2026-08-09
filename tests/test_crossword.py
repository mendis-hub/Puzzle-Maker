"""
tests/test_crossword.py
────────────────────────
Automated tests covering crossword generator, vector PDF renderer, and ZIP exporter.
"""

from __future__ import annotations

import io
import zipfile
import pytest

from crossword.generator import CrosswordGrid, generate_crossword, parse_word_inputs
from crossword.renderer import build_puzzle_pdf, build_answer_pdf
from crossword.exporter import export_crossword_zip


SAMPLE_WORDS = [
    "RADICULITIS: Nerve root inflammation",
    "RHINORRHAGIA: Nose bleed",
    "XEROPHTHALMIA: Dry eye condition",
    "QUERATOPLASTY: Corneal surgery",
    "RHINORRHOEA: Nasal discharge",
    "ORCHITIS: Testicular inflammation",
    "ADACRYA: Deficient lacrimation",
]


class TestCrosswordGenerator:

    def test_parse_inputs(self):
        parsed = parse_word_inputs(["PYTHON: Programming language", "FASTAPI", "MAZE: Solution path"])
        assert len(parsed) == 3
        assert parsed[0].word == "PYTHON"
        assert parsed[0].clue == "Programming language"
        assert parsed[1].word == "FASTAPI"
        assert parsed[1].clue == "FASTAPI"

    def test_returns_crossword_grid(self):
        cg = generate_crossword(SAMPLE_WORDS, seed=42)
        assert isinstance(cg, CrosswordGrid)
        assert cg.rows > 0 and cg.cols > 0
        assert len(cg.placements) > 0

    def test_clue_numbering(self):
        cg = generate_crossword(SAMPLE_WORDS, seed=42)
        assert len(cg.cell_numbers) > 0
        for pl in cg.placements:
            assert pl.number > 0

    def test_reproducible_with_seed(self):
        cg1 = generate_crossword(SAMPLE_WORDS, seed=123)
        cg2 = generate_crossword(SAMPLE_WORDS, seed=123)
        assert cg1.grid == cg2.grid
        assert cg1.placed_words == cg2.placed_words

    def test_overlong_word_reported_missed(self):
        """Words longer than the canvas must be reported missed, not crash."""
        cg = generate_crossword(["HELLO: Greeting", "X" * 90 + ": absurd"], seed=1)
        assert "HELLO" in cg.placed_words
        assert "X" * 90 in cg.missed_words
        # grid must still be valid (no negative-index corruption)
        for p in cg.placements:
            for r, c in p.cells:
                assert 0 <= r < cg.rows and 0 <= c < cg.cols

    def test_all_too_long_raises(self):
        """If no word fits the canvas, generation fails cleanly."""
        with pytest.raises(ValueError):
            generate_crossword(["X" * 90 + ": a", "Y" * 95 + ": b"], seed=1)

    def test_parse_tuple_and_dict_inputs(self):
        parsed = parse_word_inputs([("PYTHON", "A snake"), {"word": "MAZE", "clue": "Labyrinth"}])
        assert len(parsed) == 2
        assert parsed[0].word == "PYTHON" and parsed[0].clue == "A snake"
        assert parsed[1].word == "MAZE" and parsed[1].clue == "Labyrinth"

    def test_parse_deduplicates(self):
        parsed = parse_word_inputs(["PYTHON: A", "PYTHON: B", "python: C"])
        assert len(parsed) == 1


class TestCrosswordPDFRenderer:

    def test_puzzle_pdf(self):
        cg = generate_crossword(SAMPLE_WORDS, seed=42)
        buf = build_puzzle_pdf(cg, title="Test Crossword")
        assert isinstance(buf, io.BytesIO)
        assert buf.read(4) == b"%PDF"

    def test_answer_pdf(self):
        cg = generate_crossword(SAMPLE_WORDS, seed=42)
        buf = build_answer_pdf(cg, title="Test Crossword Key")
        assert isinstance(buf, io.BytesIO)
        assert buf.read(4) == b"%PDF"


class TestCrosswordExporter:

    def test_export_zip(self):
        zip_buf = export_crossword_zip(SAMPLE_WORDS, seed=42, title="Medical Crossword")
        assert isinstance(zip_buf, io.BytesIO)
        assert zip_buf.read(2) == b"PK"

        zip_buf.seek(0)
        with zipfile.ZipFile(zip_buf) as zf:
            names = zf.namelist()
            assert "crossword_puzzle.pdf" in names
            assert "crossword_answer.pdf" in names
            for name in names:
                data = zf.read(name)
                assert data[:4] == b"%PDF"
