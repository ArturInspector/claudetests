from __future__ import annotations

from pydantic import BaseModel, Field


class SocraticAnalyzeRequest(BaseModel):
    question: str = Field(min_length=3)
    answer: str = Field(min_length=3)
    topic: str | None = Field(default=None, min_length=2, max_length=255)
    mode: str | None = Field(default="practice", pattern="^(practice|interview)$")
    session_id: int | None = None
    required_terms: list[str] | None = None


class SocraticMove(BaseModel):
    type: str
    text: str
    rationale: str | None = None
    difficulty: str | None = None
    target: str | None = None


class GraphHint(BaseModel):
    concept: str
    status: str | None = None
    action: str | None = None


class SocraticBlock(BaseModel):
    moves: list[SocraticMove] = []
    next_step: str | None = None


class AnalysisBlock(BaseModel):
    understanding: float
    confidence: float | None = None
    misconceptions: list[dict] | None = None
    nextDifficulty: str | None = None
    gaps: list[dict] | None = None


class SocraticAnalyzeResponse(BaseModel):
    analysis: AnalysisBlock
    socratic: SocraticBlock
    graph: dict | None = None
    blind_zones: list[str] | None = None

