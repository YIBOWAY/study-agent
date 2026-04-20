from fastapi import FastAPI

from app.api.routes.chat import router as chat_router
from app.api.routes.health import router as health_router
from app.api.routes.rag import router as rag_router
from app.api.routes.research import router as research_router
from app.api.routes.tools import router as tools_router
from app.core.config import get_settings
from app.core.logging import setup_logging

setup_logging()
settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    debug=settings.app_debug,
)

app.include_router(health_router)
app.include_router(chat_router)
app.include_router(rag_router)
app.include_router(tools_router)
app.include_router(research_router)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "message": "Phase 0 + Phase 1 backend is running",
        "docs": "/docs",
    }
