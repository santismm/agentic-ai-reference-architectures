"""Model abstraction.

The whole point of a reference architecture is that the *shape* of the system
does not depend on which model you plug in. Everything in this package talks to
the :class:`LLM` protocol below, never to a concrete provider.

``EchoModel`` is a deterministic, dependency-free policy so the examples and
tests run offline with no API key. A thin Vertex AI adapter is provided as an
*optional* extra (``pip install '.[vertex]'``) to show where a real model slots
in — it is imported lazily so the core stays installable anywhere.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


@dataclass
class Message:
    role: str  # "system" | "user" | "assistant" | "tool"
    content: str


@dataclass
class ToolCall:
    name: str
    arguments: dict


@dataclass
class Completion:
    """A single model step: either free text, or a request to call a tool."""

    text: str = ""
    tool_call: ToolCall | None = None
    raw: dict = field(default_factory=dict)

    @property
    def is_tool_call(self) -> bool:
        return self.tool_call is not None


@runtime_checkable
class LLM(Protocol):
    """The only model interface the rest of the package depends on."""

    def complete(self, messages: list[Message], tools: list[dict]) -> Completion:
        ...


class EchoModel:
    """A deterministic stand-in policy for offline demos and tests.

    It implements a tiny ReAct-style policy: if a tool whose name appears in the
    user goal has not been called yet, it calls it; once it has an observation,
    it produces a final answer. This is *not* a real model — it exists so the
    architecture is runnable and testable with zero external dependencies.
    """

    def __init__(self, seed: int = 0) -> None:
        self.seed = seed
        self._calls: list[str] = []

    def complete(self, messages: list[Message], tools: list[dict]) -> Completion:
        goal = next((m.content for m in messages if m.role == "user"), "")
        observations = [m.content for m in messages if m.role == "tool"]

        # Pick a tool that the goal mentions and that we have not used yet.
        for spec in tools:
            name = spec["name"]
            if name in goal.lower() or any(k in goal.lower() for k in spec.get("triggers", [])):
                if name not in self._calls:
                    self._calls.append(name)
                    return Completion(tool_call=ToolCall(name=name, arguments=self._extract_args(goal, spec)))

        # No (more) tools to call -> finalize using whatever we observed.
        summary = " ".join(observations) if observations else "No tool was required."
        return Completion(text=f"Done. {summary}".strip())

    @staticmethod
    def _extract_args(goal: str, spec: dict) -> dict:
        """Best-effort argument extraction for the demo tools."""
        numbers = [float(n) for n in re.findall(r"-?\d+(?:\.\d+)?", goal)]
        params = spec.get("parameters", {}).get("properties", {})
        args: dict = {}
        if "expression" in params:
            m = re.search(r"[-+*/().\d\s]+", goal)
            args["expression"] = (m.group(0).strip() if m else "0") or "0"
        if "query" in params:
            args["query"] = goal
        if "a" in params and len(numbers) >= 1:
            args["a"] = numbers[0]
        if "b" in params and len(numbers) >= 2:
            args["b"] = numbers[1]
        return args


def vertex_model(model: str = "gemini-2.5-pro", **kwargs) -> LLM:  # pragma: no cover
    """Optional Vertex AI adapter (requires ``pip install '.[vertex]'``).

    Imported lazily so the core package has no cloud dependency. Returns an
    object satisfying the :class:`LLM` protocol. Tool-calling wiring is left as a
    clearly-marked integration point rather than hidden magic.
    """
    try:
        import vertexai
        from vertexai.generative_models import GenerativeModel
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "Vertex AI extra not installed. Run: pip install '.[vertex]' "
            "and authenticate with `gcloud auth application-default login`."
        ) from exc

    vertexai.init(**kwargs)
    client = GenerativeModel(model)

    class _VertexLLM:
        def complete(self, messages: list[Message], tools: list[dict]) -> Completion:
            prompt = "\n".join(f"{m.role}: {m.content}" for m in messages)
            resp = client.generate_content(prompt)
            return Completion(text=resp.text, raw={"model": model})

    return _VertexLLM()


def tool_to_schema(name: str, description: str, parameters: dict, triggers: list[str]) -> dict:
    return {
        "name": name,
        "description": description,
        "parameters": parameters,
        "triggers": triggers,
    }


def parse_json_args(text: str) -> dict:
    """Tolerant JSON parse used when a real model returns tool arguments."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {}
