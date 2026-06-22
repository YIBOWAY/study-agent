from __future__ import annotations

import operator
from typing import Annotated, NotRequired, TypedDict


class ResearchSearchResult(TypedDict):
    source: str
    query: str
    text_snippet: str
    score: float
    title: str
    url: str | None


class ResearchStep(TypedDict):
    node: str
    action: str
    output_summary: str
    timestamp: str


class ResearchState(TypedDict):
    topic: str
    queries: Annotated[list[str], operator.add]
    search_results: Annotated[list[ResearchSearchResult], operator.add]
    report: str
    steps: Annotated[list[ResearchStep], operator.add]
    iteration: int
    max_iterations: int
    evaluation: str
    top_k: int
    plan: NotRequired[list[str]]
    current_step: NotRequired[str]
    reflection: NotRequired[str]
    session_id: NotRequired[str]
    prior_insights: NotRequired[list[str]]
