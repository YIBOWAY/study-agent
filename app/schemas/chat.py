from typing import Optional, List

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User input message")
    system_prompt: Optional[str] = Field(
        default=None,
        description="Optional system prompt override for learning purposes",
    )


class ChatResponse(BaseModel):
    reply: str
    model: str


class ExtractRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Input text to extract information from")


class ExtractResponse(BaseModel):
    summary: str
    keywords: List[str]
    sentiment: str
    model: str
