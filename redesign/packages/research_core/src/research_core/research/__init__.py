"""Research domain contracts for the Study Agent redesign."""

from research_core.research.entities import (
    Claim,
    Evidence,
    Project,
    Report,
    ResearchRun,
    ResearchRunStatus,
    Source,
)
from research_core.research.ingestion import SourceIngestor, SourceInput
from research_core.research.retrieval import FakeRetriever, SearchResult

__all__ = [
    "Claim",
    "Evidence",
    "FakeRetriever",
    "Project",
    "Report",
    "ResearchRun",
    "ResearchRunStatus",
    "SearchResult",
    "Source",
    "SourceIngestor",
    "SourceInput",
]
