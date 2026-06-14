"""Planning.

A planner turns a goal into an ordered set of steps before the act/observe loop
begins. Even a lightweight plan improves traceability: you can show the plan to a
human, log it, and check the agent against it. The default planner is heuristic
and deterministic; replace ``plan`` with an LLM call for open-ended goals — the
loop in :mod:`agentic_ref.agent` consumes the same ``Plan`` either way.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Step:
    description: str
    done: bool = False


@dataclass
class Plan:
    goal: str
    steps: list[Step] = field(default_factory=list)

    def next_open(self) -> Step | None:
        return next((s for s in self.steps if not s.done), None)

    @property
    def complete(self) -> bool:
        return all(s.done for s in self.steps)


class Planner:
    def plan(self, goal: str, tool_names: list[str]) -> Plan:
        steps: list[Step] = []
        g = goal.lower()
        # Heuristic decomposition: gather context, then act, then summarize.
        if any(t in g for t in ("search", "what", "explain", "find")):
            steps.append(Step("Retrieve relevant context"))
        if any(t in g for t in ("calculate", "compute", "+", "*", "sum")):
            steps.append(Step("Perform the computation"))
        steps.append(Step("Synthesize a final answer"))
        return Plan(goal=goal, steps=steps)
