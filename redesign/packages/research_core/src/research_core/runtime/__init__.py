"""Runtime message and event contracts."""

from research_core.runtime.context import ContextBuilder
from research_core.runtime.events import RunEvent, RunEventType
from research_core.runtime.messages import AgentMessage, MessageRole
from research_core.runtime.runner import AgentRunner, AgentRunResult
from research_core.runtime.tools import (
    ToolCall,
    ToolDefinition,
    ToolResult,
    ToolRuntime,
    UnknownToolError,
)
from research_core.runtime.trajectory import event_type_sequence, events_to_records

__all__ = [
    "AgentMessage",
    "AgentRunResult",
    "AgentRunner",
    "ContextBuilder",
    "MessageRole",
    "RunEvent",
    "RunEventType",
    "ToolCall",
    "ToolDefinition",
    "ToolResult",
    "ToolRuntime",
    "UnknownToolError",
    "event_type_sequence",
    "events_to_records",
]
