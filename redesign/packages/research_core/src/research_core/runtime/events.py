from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from research_core.runtime.immutability import freeze_json_value, thaw_json_value


class RunEventType(StrEnum):
    MODEL_REQUEST = "model_request"
    MODEL_RESPONSE = "model_response"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    SKILL_LOAD = "skill_load"
    SKILL_STEP = "skill_step"
    MEMORY_RECALL = "memory_recall"
    MEMORY_WRITE = "memory_write"
    DELEGATE_START = "delegate_start"
    DELEGATE_EVENT = "delegate_event"
    DELEGATE_FINISH = "delegate_finish"
    COMPACTION_START = "compaction_start"
    COMPACTION_FINISH = "compaction_finish"
    EVAL_RESULT = "eval_result"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class RunEvent:
    id: str
    run_id: str
    type: RunEventType
    payload: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("id must not be empty")
        if not self.run_id.strip():
            raise ValueError("run_id must not be empty")
        object.__setattr__(self, "payload", freeze_json_value(dict(self.payload)))

    def to_record(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "run_id": self.run_id,
            "type": self.type.value,
            "payload": thaw_json_value(self.payload),
        }
