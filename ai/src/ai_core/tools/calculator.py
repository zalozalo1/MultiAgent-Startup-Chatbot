"""Safe arithmetic calculator tool (AST-based, no eval of arbitrary code)."""

import ast
import operator

from langchain_core.tools import StructuredTool

_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _evaluate(node: ast.AST) -> float:
    if isinstance(node, ast.Expression):
        return _evaluate(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_evaluate(node.left), _evaluate(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_evaluate(node.operand))
    raise ValueError(f"Unsupported expression element: {ast.dump(node)}")


async def calculator(expression: str) -> str:
    """Evaluate an arithmetic expression, e.g. market sizing math like
    '2500000 * 0.03 * 12'. Supports + - * / // % ** and parentheses."""
    try:
        result = _evaluate(ast.parse(expression.strip(), mode="eval"))
    except Exception as exc:
        return f"Could not evaluate '{expression}': {exc}"
    if isinstance(result, float) and result.is_integer():
        result = int(result)
    return f"{expression} = {result}"


def make_calculator_tool() -> StructuredTool:
    return StructuredTool.from_function(
        coroutine=calculator,
        name="calculator",
        description=(
            "Evaluate an arithmetic expression, e.g. market sizing math like "
            "'2500000 * 0.03 * 12'. Supports + - * / // % ** and parentheses."
        ),
    )
