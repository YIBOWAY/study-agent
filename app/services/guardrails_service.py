from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.core.config import Settings


class GuardrailsService:
    def __init__(self, settings: "Settings") -> None:
        self.settings = settings
        self._high_risk_patterns = [
            "ignore previous instructions",
            "ignore the above",
            "disregard the above",
            "reveal your prompt",
            "忽略之前的指令",
            "忘记之前的设定",
        ]
        self._medium_risk_patterns = [
            "you are now",
            "pretend to be",
            "system prompt",
            "请扮演",
        ]
        # Phone: matches 11 contiguous digits OR 3-4-4 / 3-3-4 split by space/dash/dot.
        # We anchor with non-digit boundaries to avoid hitting longer numeric strings (e.g. IDs).
        self._sensitive_patterns = [
            (
                "phone",
                re.compile(
                    r"(?<!\d)(?:\d{11}|\d{3}[\s\-.]\d{4}[\s\-.]\d{4}|\d{3}[\s\-.]\d{3}[\s\-.]\d{5})(?!\d)"
                ),
                "[PHONE]",
            ),
            ("email", re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"), "[EMAIL]"),
            ("id_number", re.compile(r"(?<!\d)\d{17}[\dXx](?!\d)"), "[ID_NUMBER]"),
        ]
        self._dangerous_argument_patterns = [
            ";",
            "&&",
            "||",
            "`",
            "$(",
            "powershell",
            "cmd.exe",
        ]

    def check_input(self, user_input: str) -> dict[str, Any]:
        lowered = user_input.lower()
        high_matches = [
            {"pattern": pattern, "type": "injection"}
            for pattern in self._high_risk_patterns
            if pattern.lower() in lowered
        ]
        if high_matches:
            return {
                "safe": False,
                "risk_level": "high",
                "matches": high_matches,
                "sanitized_input": "Input blocked by guardrails due to prompt-injection risk.",
            }

        medium_matches = [
            {"pattern": pattern, "type": "injection"}
            for pattern in self._medium_risk_patterns
            if pattern.lower() in lowered
        ]
        if medium_matches:
            safe = not self.settings.guardrails_strict_mode
            return {
                "safe": safe,
                "risk_level": "medium",
                "matches": medium_matches,
                "sanitized_input": (
                    user_input
                    if safe
                    else "Input blocked by guardrails due to prompt-injection risk."
                ),
            }

        return {
            "safe": True,
            "risk_level": "low",
            "matches": [],
            "sanitized_input": user_input,
        }

    def sanitize_output(self, text: str) -> dict[str, Any]:
        sanitized = text
        redactions: list[dict[str, Any]] = []
        for redaction_type, pattern, replacement in self._sensitive_patterns:
            sanitized, count = pattern.subn(replacement, sanitized)
            if count:
                redactions.append({"type": redaction_type, "count": count})
        return {"sanitized": sanitized, "redactions": redactions}

    def validate_tool_call(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if not self._is_tool_allowed(tool_name):
            return {"safe": False, "reason": f"Tool '{tool_name}' is not allowed by guardrails."}

        flattened = self._flatten_arguments(arguments).lower()
        for pattern in self._dangerous_argument_patterns:
            if pattern in flattened:
                return {
                    "safe": False,
                    "reason": f"Tool arguments contain blocked pattern: {pattern.strip()}",
                }
        return {"safe": True, "reason": "ok"}

    def _is_tool_allowed(self, tool_name: str) -> bool:
        if tool_name.startswith("mcp__"):
            allowed_mcp_tools = self._parse_csv_setting(self.settings.guardrails_allowed_mcp_tools)
            return "*" in allowed_mcp_tools or tool_name in allowed_mcp_tools

        allowed_tools = self._parse_csv_setting(self.settings.guardrails_allowed_tools)
        return "*" in allowed_tools or tool_name in allowed_tools

    @staticmethod
    def _parse_csv_setting(value: str) -> set[str]:
        return {item.strip() for item in value.split(",") if item.strip()}

    def _flatten_arguments(self, value: Any) -> str:
        if isinstance(value, dict):
            return " ".join(self._flatten_arguments(item) for item in value.values())
        if isinstance(value, list):
            return " ".join(self._flatten_arguments(item) for item in value)
        return str(value)
