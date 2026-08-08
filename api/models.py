"""
api/models.py
─────────────
Pydantic v2 request / response schemas for the Puzzle Generator API.
"""
from __future__ import annotations

from typing import Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class GenerateRequest(BaseModel):
    """Body accepted by POST /api/generate (maze)."""

    size: int = Field(
        default=21,
        ge=5,
        le=101,
        description="Grid dimension (5–101). Even values are rounded up to the next odd integer.",
    )
    seed: Optional[int] = Field(
        default=None,
        description="Optional RNG seed for reproducible mazes. Omit for a random maze.",
    )
    shape: str = Field(
        default="square",
        description="Maze geometric shape: square, circle, heart, triangle, diamond, octagon, cross, vrect.",
    )
    title: str = Field(
        default="Maze Puzzle",
        min_length=1,
        max_length=80,
        description="Heading printed at the top of both PDF pages.",
    )

    @field_validator("size")
    @classmethod
    def enforce_odd(cls, v: int) -> int:
        """Round even sizes up so the DFS grid parity is always satisfied."""
        return v if v % 2 == 1 else v + 1

    model_config = {"json_schema_extra": {"example": {"size": 21, "seed": 42, "title": "My Maze"}}}


class WordSearchRequest(BaseModel):
    """Body accepted by POST /api/generate/wordsearch."""

    words: List[str] = Field(
        description="List of words to hide in the grid (1–30 words, each 2–20 alpha chars).",
        min_length=1,
        max_length=30,
    )
    rows: int = Field(
        default=15,
        ge=5,
        le=30,
        description="Number of grid rows (5–30).",
    )
    cols: int = Field(
        default=15,
        ge=5,
        le=30,
        description="Number of grid columns (5–30).",
    )
    seed: Optional[int] = Field(
        default=None,
        description="Optional RNG seed for reproducibility.",
    )
    title: str = Field(
        default="Word Search",
        min_length=1,
        max_length=80,
        description="Heading printed at the top of both PDF pages.",
    )

    @field_validator("words")
    @classmethod
    def sanitise_words(cls, v: List[str]) -> List[str]:
        """Strip non-alpha chars, upper-case, deduplicate, limit length."""
        seen: set[str] = set()
        out: List[str] = []
        for w in v:
            clean = "".join(ch for ch in w.upper() if ch.isalpha())
            if clean and len(clean) >= 2 and clean not in seen:
                seen.add(clean)
                out.append(clean)
        if not out:
            raise ValueError("No valid words provided (must contain at least one alpha word ≥ 2 letters).")
        return out

    model_config = {
        "json_schema_extra": {
            "example": {
                "words": ["PYTHON", "FASTAPI", "MAZE", "PUZZLE"],
                "rows": 15,
                "cols": 15,
                "seed": 42,
                "title": "My Word Search",
            }
        }
    }


class PlacementModel(BaseModel):
    word: str
    row: int
    col: int
    dr: int
    dc: int
    cells: List[List[int]]


class WordSearchPreviewResponse(BaseModel):
    rows: int
    cols: int
    grid: List[List[str]]
    placements: List[PlacementModel]
    hidden_words: List[str]
    missed_words: List[str]
    seed_used: int


class MazePreviewResponse(BaseModel):
    rows: int
    cols: int
    grid: List[List[int]]
    start: List[int]
    end: List[int]
    solution: List[List[int]]
    seed_used: int


class HealthResponse(BaseModel):
    status: str
    version: str


class CrosswordRequest(BaseModel):
    """Body accepted by POST /api/generate/crossword and POST /api/preview/crossword."""

    words: List[str] = Field(
        description="List of words (or 'WORD: Clue' entries) to generate crossword (1–50 entries).",
        min_length=1,
        max_length=50,
    )
    seed: Optional[int] = Field(
        default=None,
        description="Optional RNG seed for reproducible layout.",
    )
    title: str = Field(
        default="Crossword puzzle",
        min_length=1,
        max_length=80,
        description="Heading printed at the top of both PDF pages.",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "words": [
                    "RADICULITIS: Nerve root inflammation",
                    "RHINORRHAGIA: Nose bleed",
                    "XEROPHTHALMIA: Dry eye condition",
                    "QUERATOPLASTY: Corneal surgery",
                    "RHINORRHOEA: Nasal discharge",
                    "ORCHITIS: Testicular inflammation",
                    "ADACRYA: Deficient lacrimation",
                ],
                "seed": 42,
                "title": "Medical Crossword",
            }
        }
    }


class CrosswordPlacementModel(BaseModel):
    word: str
    clue: str
    row: int
    col: int
    direction: str
    number: int


class CrosswordPreviewResponse(BaseModel):
    rows: int
    cols: int
    grid: List[List[Optional[str]]]
    placements: List[CrosswordPlacementModel]
    across_placements: List[CrosswordPlacementModel]
    down_placements: List[CrosswordPlacementModel]
    cell_numbers: Dict[str, int]
    placed_words: List[str]
    missed_words: List[str]
    seed_used: int

