from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class StepRecord(BaseModel):
    node: str
    action: str
    output_summary: str = Field(..., max_length=200)
    timestamp: str


class ResearchRequest(BaseModel):
    topic: str = Field(..., min_length=2)
    mode: Literal["workflow", "agent"]
    max_iterations: int = Field(default=3, ge=1, le=10)
    top_k: int = Field(default=5, ge=1, le=20)


class ResearchResponse(BaseModel):
    topic: str
    mode: Literal["workflow", "agent"]
    report: str
    queries: list[str]
    steps: list[StepRecord]
    iterations_used: int
    search_result_count: int
