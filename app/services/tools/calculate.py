from __future__ import annotations

import ast
from dataclasses import dataclass
import math
from typing import Any


@dataclass(frozen=True)
class BuiltinTool:
    name: str
    description: str
    parameters: dict[str, Any]
    handler: Any


_ALLOWED_BINARY_OPERATORS = {
    ast.Add: lambda left, right: left + right,
    ast.Sub: lambda left, right: left - right,
    ast.Mult: lambda left, right: left * right,
    ast.Div: lambda left, right: left / right,
    ast.FloorDiv: lambda left, right: left // right,
    ast.Mod: lambda left, right: left % right,
    ast.Pow: lambda left, right: left**right,
}
_ALLOWED_UNARY_OPERATORS = {
    ast.UAdd: lambda value: +value,
    ast.USub: lambda value: -value,
}
_ALLOWED_FUNCTIONS = {
    "sqrt": math.sqrt,
    "abs": abs,
    "round": round,
}
_MAX_EXPRESSION_LENGTH = 200
_MAX_EXPONENT_ABS = 100


def _evaluate_expression(node: ast.AST) -> float:
    if isinstance(node, ast.Expression):
        return _evaluate_expression(node.body)
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return float(node.value)
        raise ValueError("Only numeric constants are allowed.")
    if isinstance(node, ast.BinOp):
        operator = _ALLOWED_BINARY_OPERATORS.get(type(node.op))
        if operator is None:
            raise ValueError("Unsupported binary operator.")
        left = _evaluate_expression(node.left)
        right = _evaluate_expression(node.right)
        if isinstance(node.op, ast.Pow) and abs(right) > _MAX_EXPONENT_ABS:
            raise ValueError("Exponent is too large.")
        return float(operator(left, right))
    if isinstance(node, ast.UnaryOp):
        operator = _ALLOWED_UNARY_OPERATORS.get(type(node.op))
        if operator is None:
            raise ValueError("Unsupported unary operator.")
        return float(operator(_evaluate_expression(node.operand)))
    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name):
            raise ValueError("Only direct function calls are allowed.")
        function = _ALLOWED_FUNCTIONS.get(node.func.id)
        if function is None:
            raise ValueError(f"Function '{node.func.id}' is not allowed.")
        if node.keywords:
            raise ValueError("Keyword arguments are not allowed.")
        arguments = [_evaluate_expression(argument) for argument in node.args]
        return float(function(*arguments))
    raise ValueError("Unsupported expression.")


async def _calculate(arguments: dict[str, Any]) -> str:
    expression = str(arguments.get("expression") or "").strip()
    if not expression:
        raise ValueError("expression is required")
    if len(expression) > _MAX_EXPRESSION_LENGTH:
        raise ValueError("expression is too long")

    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as exc:
        raise ValueError("expression has invalid syntax") from exc
    value = _evaluate_expression(tree)
    if not math.isfinite(value):
        raise ValueError("expression result must be finite")
    if value.is_integer():
        return str(int(value))
    return str(value)


def build_calculate_tool() -> BuiltinTool:
    return BuiltinTool(
        name="calculate",
        description="Safely evaluate a mathematical expression.",
        parameters={
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Mathematical expression using numbers and safe functions.",
                }
            },
            "required": ["expression"],
        },
        handler=_calculate,
    )
