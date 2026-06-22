from __future__ import annotations

import argparse
import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.services.agent_evaluator import AgentEvalCase, evaluate_agent_batch
from app.services.llm_service import LLMService
from app.services.memory_service import MemoryService
from app.services.multi_agent import run_multi_agent
from app.services.rag_service import RAGService
from app.services.research import run_agent, run_agent_v2, run_workflow
from app.services.tool_registry import ToolRegistry

RESULTS_DIR = Path("eval/results")


def load_agent_cases(path: str | Path) -> list[AgentEvalCase]:
    cases: list[AgentEvalCase] = []
    with Path(path).open("r", encoding="utf-8") as file:
        for line in file:
            if not line.strip():
                continue
            row = json.loads(line)
            cases.append(
                {
                    "topic": row["topic"],
                    "expected_keywords": list(row.get("expected_keywords", [])),
                    "mode": row.get("mode", "agent_v2"),
                    "max_iterations": int(row.get("max_iterations", 3)),
                }
            )
    return cases


def _build_runner(
    mode: str,
    *,
    rag_service: RAGService,
    llm_service: LLMService,
    tool_registry: ToolRegistry,
    memory_service: MemoryService,
):
    if mode == "workflow":
        async def _runner(topic: str, max_iterations: int, top_k: int) -> dict[str, Any]:
            return await run_workflow(
                topic=topic,
                max_iterations=max_iterations,
                top_k=top_k,
                rag_service=rag_service,
                llm_service=llm_service,
                tool_registry=tool_registry,
            )

        return _runner

    if mode == "agent":
        async def _runner(topic: str, max_iterations: int, top_k: int) -> dict[str, Any]:
            return await run_agent(
                topic=topic,
                max_iterations=max_iterations,
                top_k=top_k,
                rag_service=rag_service,
                llm_service=llm_service,
                tool_registry=tool_registry,
            )

        return _runner

    if mode == "multi_agent":
        async def _runner(topic: str, max_iterations: int, top_k: int) -> dict[str, Any]:
            return await run_multi_agent(
                topic=topic,
                max_iterations=max_iterations,
                top_k=top_k,
                rag_service=rag_service,
                llm_service=llm_service,
                tool_registry=tool_registry,
                memory_service=memory_service,
                session_id="",
            )

        return _runner

    async def _runner(topic: str, max_iterations: int, top_k: int) -> dict[str, Any]:
        return await run_agent_v2(
            topic=topic,
            max_iterations=max_iterations,
            top_k=top_k,
            rag_service=rag_service,
            llm_service=llm_service,
            tool_registry=tool_registry,
            memory_service=memory_service,
            session_id="",
        )

    return _runner


async def run_agent_evaluation(
    mode: str,
    limit: int,
    cases_path: str | Path = "eval/agent_topics.jsonl",
) -> dict[str, Any]:
    llm_service = LLMService()
    rag_service = RAGService(llm_service=llm_service)
    tool_registry = ToolRegistry(rag_service=rag_service)
    memory_service = MemoryService(data_dir="eval/runtime_memory")
    cases = load_agent_cases(cases_path)[:limit]
    filtered_cases = [{**case, "mode": mode} for case in cases]
    result = await evaluate_agent_batch(
        filtered_cases,
        _build_runner(
            mode,
            rag_service=rag_service,
            llm_service=llm_service,
            tool_registry=tool_registry,
            memory_service=memory_service,
        ),
        top_k=5,
    )
    result["mode"] = mode
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_path = RESULTS_DIR / f"agent_eval_{timestamp}.json"
    output_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    return result


async def main() -> None:
    parser = argparse.ArgumentParser(description="Run Agent evaluation.")
    parser.add_argument("--mode", default="agent_v2")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--cases", default="eval/agent_topics.jsonl")
    args = parser.parse_args()

    result = await run_agent_evaluation(args.mode, args.limit, args.cases)
    print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    asyncio.run(main())
