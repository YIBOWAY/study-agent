from __future__ import annotations

from app.core.config import get_settings
from app.services.guardrails_service import GuardrailsService
from app.services.tracing_service import TracingService

settings = get_settings()
guardrails_service = GuardrailsService(settings)
tracing_service = TracingService(settings) if settings.tracing_enabled else None


def get_guardrails_service() -> GuardrailsService | None:
    if not settings.guardrails_enabled:
        return None
    return guardrails_service


def get_tracing_service() -> TracingService | None:
    return tracing_service
