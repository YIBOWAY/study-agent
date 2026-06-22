from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import research as research_routes
from app.api.routes import tools as tools_routes
from app.api.routes.chat import router as chat_router
from app.api.routes.eval import router as eval_router
from app.api.routes.health import router as health_router
from app.api.routes.memory import router as memory_router
from app.api.routes.mcp import router as mcp_router
from app.api.routes.observability import router as observability_router
from app.api.routes.rag import router as rag_router
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.services.mcp.runtime import get_mcp_runtime, init_mcp_runtime, shutdown_mcp_runtime

setup_logging()
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    if settings.mcp_external_servers.strip():
        await init_mcp_runtime(settings)
        runtime = get_mcp_runtime()
        tools_routes.tool_registry.attach_mcp_runtime(runtime)
        research_routes.tool_registry.attach_mcp_runtime(runtime)
    try:
        yield
    finally:
        await shutdown_mcp_runtime()


app = FastAPI(
    title=settings.app_name,
    description="Research Agent Platform - RAG, tools, memory, MCP, evaluation, and observability.",
    version="0.8.0",
    debug=settings.app_debug,
    lifespan=lifespan,
    openapi_tags=[
        {"name": "health", "description": "Health checks"},
        {"name": "chat", "description": "Basic LLM chat, extraction, and streaming chat"},
        {"name": "rag", "description": "RAG ingest, search, and grounded answer generation"},
        {"name": "tools", "description": "Tool calling with built-in and MCP tools"},
        {"name": "research", "description": "Research flows: workflow, agent, agent_v2, and multi_agent"},
        {"name": "memory", "description": "Session and long-term memory inspection"},
        {"name": "mcp", "description": "MCP server inspection and debug invocation"},
        {"name": "eval", "description": "Batch evaluation for RAG and agent flows"},
        {"name": "observability", "description": "Trace and cost inspection"},
    ],
)

app.include_router(health_router)
app.include_router(chat_router)
app.include_router(rag_router)
app.include_router(tools_routes.router)
app.include_router(research_routes.router)
app.include_router(memory_router)
app.include_router(mcp_router)
app.include_router(eval_router)
app.include_router(observability_router)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "message": "Research Agent Platform is running",
        "docs": "/docs",
    }
