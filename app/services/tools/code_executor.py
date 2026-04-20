from __future__ import annotations

from dataclasses import dataclass
import asyncio
import os
import sys
import tempfile
from typing import Any


@dataclass(frozen=True)
class BuiltinTool:
    name: str
    description: str
    parameters: dict[str, Any]
    handler: Any


_BLOCKED_PATTERNS = [
    "import os",
    "import sys",
    "import subprocess",
    "import shutil",
    "__import__",
    "eval(",
    "exec(",
    "open(",
    "rm ",
    "del ",
    "import socket",
    "import http",
    "import requests",
]
_MAX_CODE_LENGTH = 5000
_DEFAULT_TIMEOUT = 10
_MAX_TIMEOUT = 30
_OUTPUT_LIMIT = 2000


async def _execute_python(arguments: dict[str, Any]) -> str:
    code = str(arguments.get("code") or "")
    if not code.strip():
        raise ValueError("code is required")
    if len(code) > _MAX_CODE_LENGTH:
        raise ValueError("code is too long")

    lowered_code = code.lower()
    for pattern in _BLOCKED_PATTERNS:
        if pattern in lowered_code:
            raise ValueError(f"Blocked unsafe keyword: {pattern}")

    timeout = _parse_timeout(arguments.get("timeout", _DEFAULT_TIMEOUT))
    temp_path = ""
    process: asyncio.subprocess.Process | None = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".py", delete=False) as handle:
            handle.write(code)
            temp_path = handle.name

        process = await asyncio.create_subprocess_exec(
            sys.executable,
            temp_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(process.communicate(), timeout=timeout)
        except asyncio.TimeoutError as exc:
            process.kill()
            await process.communicate()
            raise ValueError(f"Python execution timed out after {timeout} seconds") from exc

        stdout = _truncate_output(stdout_bytes.decode("utf-8", errors="replace"))
        stderr = _truncate_output(stderr_bytes.decode("utf-8", errors="replace"))
        return (
            f"Exit code: {process.returncode}\n\n"
            f"STDOUT:\n{stdout or '(empty)'}\n\n"
            f"STDERR:\n{stderr or '(empty)'}"
        )
    finally:
        if process is not None and process.returncode is None:
            process.kill()
            await process.communicate()
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


def _parse_timeout(value: Any) -> int:
    try:
        timeout = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("timeout must be an integer between 1 and 30") from exc
    if timeout < 1 or timeout > _MAX_TIMEOUT:
        raise ValueError("timeout must be between 1 and 30")
    return timeout


def _truncate_output(value: str) -> str:
    if len(value) <= _OUTPUT_LIMIT:
        return value
    return value[:_OUTPUT_LIMIT] + "\n...[truncated]"


def build_code_executor_tool() -> BuiltinTool:
    return BuiltinTool(
        name="execute_python",
        description="Execute a Python code snippet in a sandboxed subprocess and return stdout/stderr.",
        parameters={
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Python code to execute.",
                },
                "timeout": {
                    "type": "integer",
                    "description": "Execution timeout in seconds.",
                    "default": _DEFAULT_TIMEOUT,
                },
            },
            "required": ["code"],
        },
        handler=_execute_python,
    )
