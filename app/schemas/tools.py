from typing import Any

from pydantic import BaseModel, Field, model_validator


class ToolChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    enabled_tools: list[str] | None = None
    max_iterations: int | None = Field(default=None, ge=1, le=20)
    system_prompt: str | None = None

    @model_validator(mode="after")
    def validate_enabled_tools(self) -> "ToolChatRequest":
        if self.enabled_tools is not None and not self.enabled_tools:
            raise ValueError("enabled_tools must not be empty when provided")
        return self


class ToolCallRecord(BaseModel):
    tool: str
    args: dict[str, Any]
    result: str
    error: str | None = None


class ToolChatResponse(BaseModel):
    reply: str
    model: str
    tool_calls_made: list[ToolCallRecord]


class ToolInfo(BaseModel):
    name: str
    description: str
    parameters: dict[str, Any]


class ToolListResponse(BaseModel):
    tools: list[ToolInfo]
