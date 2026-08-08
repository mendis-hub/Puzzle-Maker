"""
tests/test_api.py
─────────────────
Integration tests for the FastAPI endpoints using TestClient (HTTPX).

Run with:
    python -m pytest tests/test_api.py -v
"""
from __future__ import annotations

import io
import zipfile

import pytest
from fastapi.testclient import TestClient

from server import app

client = TestClient(app)


# ── health ────────────────────────────────────────────────────────────────────

class TestHealth:

    def test_returns_200(self):
        r = client.get("/api/health")
        assert r.status_code == 200

    def test_status_field(self):
        r = client.get("/api/health")
        assert r.json()["status"] == "ok"

    def test_version_present(self):
        r = client.get("/api/health")
        assert "version" in r.json()


# ── /api/generate ─────────────────────────────────────────────────────────────

class TestGenerate:

    def _post(self, **kwargs):
        payload = {"size": 11, "title": "Test Maze", **kwargs}
        return client.post("/api/generate", json=payload)

    def test_happy_path_200(self):
        r = self._post()
        assert r.status_code == 200

    def test_content_type_zip(self):
        r = self._post()
        assert "application/zip" in r.headers["content-type"]

    def test_content_disposition_header(self):
        r = self._post()
        cd = r.headers.get("content-disposition", "")
        assert "attachment" in cd
        assert ".zip" in cd

    def test_body_is_valid_zip(self):
        r = self._post()
        buf = io.BytesIO(r.content)
        assert zipfile.is_zipfile(buf)

    def test_zip_has_two_entries(self):
        r = self._post()
        with zipfile.ZipFile(io.BytesIO(r.content)) as zf:
            assert len(zf.namelist()) == 2

    def test_zip_entries_are_valid_pdfs(self):
        r = self._post()
        with zipfile.ZipFile(io.BytesIO(r.content)) as zf:
            for name in zf.namelist():
                assert zf.read(name)[:4] == b"%PDF", f"{name} is not a valid PDF"

    def test_custom_seed_accepted(self):
        r = self._post(seed=42)
        assert r.status_code == 200

    def test_null_seed_accepted(self):
        r = self._post(seed=None)
        assert r.status_code == 200

    def test_even_size_rounded_up(self):
        """Even size → Pydantic validator rounds up → header reflects odd dim."""
        r = client.post("/api/generate", json={"size": 10, "title": "T"})
        assert r.status_code == 200
        assert "11x11" in r.headers.get("content-disposition", "")

    def test_x_maze_size_header(self):
        r = self._post()
        assert r.headers.get("x-maze-size") == "11"

    def test_x_maze_seed_header_random(self):
        r = self._post(seed=None)
        assert r.headers.get("x-maze-seed") == "random"

    def test_x_maze_seed_header_fixed(self):
        r = self._post(seed=99)
        assert r.headers.get("x-maze-seed") == "99"

    def test_size_too_small_422(self):
        r = client.post("/api/generate", json={"size": 3, "title": "T"})
        assert r.status_code == 422

    def test_size_too_large_422(self):
        r = client.post("/api/generate", json={"size": 105, "title": "T"})
        assert r.status_code == 422

    def test_title_too_long_422(self):
        r = client.post("/api/generate", json={"size": 11, "title": "x" * 81})
        assert r.status_code == 422

    def test_missing_body_422(self):
        r = client.post("/api/generate")
        assert r.status_code == 422

    @pytest.mark.parametrize("size", [11, 21, 31])
    def test_various_sizes(self, size):
        r = client.post("/api/generate", json={"size": size, "title": "Parametrised"})
        assert r.status_code == 200
        assert zipfile.is_zipfile(io.BytesIO(r.content))


# ── frontend ───────────────────────────────────────────────────────────────────

class TestFrontend:

    def test_root_returns_html(self):
        r = client.get("/")
        assert r.status_code == 200
        assert "text/html" in r.headers["content-type"]

    def test_html_contains_title(self):
        r = client.get("/")
        assert "Maze Puzzle Generator" in r.text or "Puzzle Generator" in r.text

    def test_html_contains_generate_button(self):
        r = client.get("/")
        assert "generateBtn" in r.text or "Generate" in r.text


# ── crossword API ─────────────────────────────────────────────────────────────

class TestCrosswordAPI:

    def test_preview_crossword_200(self):
        payload = {
            "words": ["PYTHON: Language", "MAZE: Grid puzzle", "SOLVER: Algorithm"],
            "seed": 42,
            "title": "Preview Test",
        }
        r = client.post("/api/preview/crossword", json=payload)
        assert r.status_code == 200
        data = r.json()
        assert "rows" in data and "cols" in data
        assert "grid" in data
        assert len(data["placements"]) > 0

    def test_generate_crossword_zip_200(self):
        payload = {
            "words": ["PYTHON: Language", "MAZE: Grid puzzle", "SOLVER: Algorithm"],
            "seed": 42,
            "title": "Crossword Test",
        }
        r = client.post("/api/generate/crossword", json=payload)
        assert r.status_code == 200
        assert "application/zip" in r.headers["content-type"]
        buf = io.BytesIO(r.content)
        assert zipfile.is_zipfile(buf)
        with zipfile.ZipFile(buf) as zf:
            assert len(zf.namelist()) == 2
            assert "crossword_puzzle.pdf" in zf.namelist()
            assert "crossword_answer.pdf" in zf.namelist()

