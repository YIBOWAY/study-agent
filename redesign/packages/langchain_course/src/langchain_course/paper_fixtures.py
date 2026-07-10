"""Local paper fixtures for the LangChain track research labs (no network)."""

from __future__ import annotations

from langchain_course.research import PaperDoc


def default_paper_docs() -> list[PaperDoc]:
    return [
        PaperDoc(
            id="paper_1",
            uri="paper://rag-evaluation-survey",
            title="RAG Evaluation Survey",
            content=(
                "RAG evaluation should report retrieval quality and citation "
                "grounding. Evidence links help readers audit generated claims."
            ),
        ),
        PaperDoc(
            id="paper_2",
            uri="paper://citation-mapping",
            title="Citation Mapping for Research Assistants",
            content=(
                "Citation mapping connects every report claim to a quote, "
                "source URI, and paper title."
            ),
        ),
        PaperDoc(
            id="paper_3",
            uri="paper://local-fixtures",
            title="Why Local Fixtures Beat Live Search in Labs",
            content=(
                "Local paper fixtures keep labs deterministic. Learners inspect "
                "evidence chains without network retrieval or embeddings."
            ),
        ),
    ]
