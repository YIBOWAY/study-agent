from __future__ import annotations

import operator
from typing import Annotated, TypedDict

from app.services.research.state import ResearchSearchResult, ResearchStep


class MultiAgentState(TypedDict):
    topic: str
    queries: Annotated[list[str], operator.add]
    search_results: Annotated[list[ResearchSearchResult], operator.add]
    report: str
    steps: Annotated[list[ResearchStep], operator.add]
    plan: list[str]
    current_step: str
    current_phase: str
    iteration: int
    max_iterations: int
    top_k: int
    analysis: str
    evaluation: str
    review_verdict: str
    review_feedback: str
    revision_count: int
    session_id: str
    prior_insights: list[str]
