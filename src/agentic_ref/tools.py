"""Tool layer.

Tools are how an agent affects the world. The two properties that matter for a
production system are (1) an explicit, declarative schema the model can be shown,
and (2) a clear mark of which tools are *side-effecting* so they can be gated by
human-in-the-loop review. Both are first-class here.
"""

from __future__ import annotations

import ast
import operator
from dataclasses import dataclass
from typing import Callable


@dataclass
class Tool:
    name: str
    description: str
    fn: Callable[..., str]
    parameters: dict
    triggers: list[str]
    side_effecting: bool = False  # mutates state / calls externally -> HITL candidate

    def schema(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
            "triggers": self.triggers,
        }


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        if tool.name in self._tools:
            raise ValueError(f"Tool already registered: {tool.name}")
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool:
        return self._tools[name]

    def schemas(self) -> list[dict]:
        return [t.schema() for t in self._tools.values()]

    def __contains__(self, name: str) -> bool:
        return name in self._tools

    def __len__(self) -> int:
        return len(self._tools)


# --- Reference tools (safe, dependency-free) ---------------------------------

_ALLOWED_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
}


def _safe_eval(node: ast.AST) -> float:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_OPS:
        return _ALLOWED_OPS[type(node.op)](_safe_eval(node.left), _safe_eval(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_OPS:
        return _ALLOWED_OPS[type(node.op)](_safe_eval(node.operand))
    raise ValueError("Unsupported expression")


def calculator(expression: str) -> str:
    """Evaluate a basic arithmetic expression with a safe AST walker (no eval)."""
    tree = ast.parse(expression, mode="eval")
    return str(_safe_eval(tree.body))


# A tiny, offline "knowledge base" so the search tool returns deterministic text.
_KB = {
    "agentic": "Agentic systems plan, call tools, keep memory and are evaluated and observed.",
    "rag": "RAG grounds generation in retrieved context to reduce hallucination.",
    "eu ai act": "The EU AI Act classifies systems by risk: unacceptable, high, limited, minimal.",
}


def knowledge_search(query: str) -> str:
    """Return the best matching note from a small offline knowledge base."""
    q = query.lower()
    for key, value in _KB.items():
        if key in q:
            return value
    return "No matching note found in the local knowledge base."


def default_registry() -> ToolRegistry:
    reg = ToolRegistry()
    reg.register(
        Tool(
            name="calculator",
            description="Evaluate a basic arithmetic expression.",
            fn=calculator,
            parameters={
                "type": "object",
                "properties": {"expression": {"type": "string"}},
                "required": ["expression"],
            },
            triggers=["calculate", "compute", "sum", "multiply", "+", "*"],
        )
    )
    reg.register(
        Tool(
            name="knowledge_search",
            description="Search a small local knowledge base of AI engineering notes.",
            fn=knowledge_search,
            parameters={
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
            triggers=["search", "what is", "explain", "look up", "find"],
        )
    )
    return reg
