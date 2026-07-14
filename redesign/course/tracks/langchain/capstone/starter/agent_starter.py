"""LC Capstone starter — fill TODOs until starter tests pass.

Do not import research_core. Use langchain_course only.

Hints (import when you implement TODOs):
- langchain_course.fake_models: deterministic BaseChatModel for the offline path
- langchain_course.research: PaperDoc, EvidenceItem, ClaimItem,
  LangChainPaperRetriever, ResearchReport, build_claim_links
- langchain_course.memory: Notebook, MemoryNote, MemoryKind, MemoryWritePolicy
- langchain_course.skills: SkillLoader
- langchain_course.workbench: WorkbenchSnapshot and panel adapters
- langchain_course.production: RunDiagnostics, JsonlStepStore, ApprovalPolicy,
  SandboxPolicy
- langchain_course.agent_kernel: AgentStep
- langchain_course.agent_kernel: run_tool_calling_agent; do not hand-build the
  main tool trail just to satisfy tests
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from langchain_course.agent_kernel import AgentStep
from langchain_course.memory import MemoryNote
from langchain_course.production import RunDiagnostics
from langchain_course.research import EvidenceItem, PaperDoc, ResearchReport
from langchain_course.workbench import WorkbenchSnapshot

CAPSTONE_ROOT = Path(__file__).resolve().parents[1]
FIXTURES_PATH = CAPSTONE_ROOT / "paper_fixtures" / "papers.json"
SKILL_PATH = CAPSTONE_ROOT / "skills" / "citation-check"

RESEARCH_QUESTION = (
    "Does citation grounding matter for trustworthy RAG evaluation, "
    "and what should a local research assistant remember or delegate "
    "when producing a cited report?"
)


@dataclass(slots=True)
class CapstoneResult:
    docs: list[PaperDoc]
    evidence: list[EvidenceItem]
    report: ResearchReport
    links: list[Any]
    memory_notes: list[MemoryNote]
    skill_name: str
    steps: list[AgentStep]
    snapshot: WorkbenchSnapshot
    diagnostics: RunDiagnostics
    jsonl_path: Path


def load_paper_docs(path: Path = FIXTURES_PATH) -> list[PaperDoc]:
    # TODO: parse papers.json into PaperDoc list with stable ids paper_1..
    raise NotImplementedError("TODO: load_paper_docs")


def build_evidence_and_report(
    docs: list[PaperDoc],
) -> tuple[list[EvidenceItem], ResearchReport]:
    # TODO: retrieve, extract quotes, build ClaimItems with evidence_ids
    raise NotImplementedError("TODO: build_evidence_and_report")


def run_capstone(*, jsonl_path: Path | None = None) -> CapstoneResult:
    # TODO: compose Parts 1–7 offline:
    # load fixtures → evidence/report/links → memory → skill → steps →
    # WorkbenchSnapshot → RunDiagnostics → JsonlStepStore
    raise NotImplementedError("TODO: run_capstone")
