from __future__ import annotations

import argparse
import asyncio
import json
from typing import Any

import httpx


async def main() -> None:
    parser = argparse.ArgumentParser(description="Manual smoke test for eval and observability routes.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8002")
    parser.add_argument("--mode", default="workflow")
    parser.add_argument("--limit", type=int, default=1)
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")
    async with httpx.AsyncClient(timeout=120) as client:
        health = await client.get(f"{base_url}/health")
        health.raise_for_status()

        research_payload = {
            "topic": "What changed in Phase 7 of this project?",
            "mode": args.mode,
            "max_iterations": 2,
            "top_k": 3,
        }
        research = await client.post(f"{base_url}/api/v1/research", json=research_payload)
        research.raise_for_status()

        agent_eval = await client.post(
            f"{base_url}/api/v1/eval/agent",
            json={"mode": args.mode, "limit": args.limit},
        )
        agent_eval.raise_for_status()

        cost = await client.get(f"{base_url}/api/v1/observability/cost")
        cost.raise_for_status()

    output: dict[str, Any] = {
        "health": health.json(),
        "research": {
            "mode": research.json().get("mode"),
            "report_preview": str(research.json().get("report", ""))[:120],
        },
        "agent_eval": {
            "total": agent_eval.json().get("total"),
            "success_rate": agent_eval.json().get("success_rate"),
        },
        "cost": cost.json(),
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
