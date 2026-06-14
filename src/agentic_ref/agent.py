"""The agent loop.

This is where the six concerns compose:

    plan -> (think -> [HITL] -> act -> observe)* -> finalize

Each concern lives in its own module and is injected here. That is the whole
thesis of this repository: an agent is not a prompt, it is a small system whose
parts you can test, swap and operate independently.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .hitl import HumanGate
from .memory import Episode, EpisodicMemory, WorkingMemory
from .models import LLM
from .observability import Tracer
from .planning import Planner
from .tools import ToolRegistry


@dataclass
class AgentResult:
    answer: str
    steps: int
    approved_actions: int
    denied_actions: int
    trace: list = field(default_factory=list)


class Agent:
    def __init__(
        self,
        model: LLM,
        tools: ToolRegistry,
        *,
        planner: Planner | None = None,
        gate: HumanGate | None = None,
        episodic: EpisodicMemory | None = None,
        tracer: Tracer | None = None,
        max_steps: int = 6,
    ) -> None:
        self.model = model
        self.tools = tools
        self.planner = planner or Planner()
        self.gate = gate or HumanGate()
        self.episodic = episodic or EpisodicMemory()
        self.tracer = tracer or Tracer()
        self.max_steps = max_steps

    def run(self, goal: str, system: str = "You are a helpful, careful agent.") -> AgentResult:
        working = WorkingMemory()
        working.add("system", system)

        # Recall: cheap win if we have solved something similar before.
        for past in self.episodic.recall(goal):
            working.add("system", f"Recall from a past run: {past.outcome}")

        working.add("user", goal)

        with self.tracer.span("plan", goal=goal):
            plan = self.planner.plan(goal, [s["name"] for s in self.tools.schemas()])

        approved = denied = 0
        answer = ""
        steps = 0

        for steps in range(1, self.max_steps + 1):
            with self.tracer.span("think", step=steps) as s:
                completion = self.model.complete(working.transcript(), self.tools.schemas())
                s.set(tool_call=completion.tool_call.name if completion.is_tool_call else None)

            if not completion.is_tool_call:
                answer = completion.text
                step = plan.next_open()
                if step:
                    step.done = True
                break

            call = completion.tool_call
            tool = self.tools.get(call.name)

            decision = self.gate.review(tool, call.arguments)
            with self.tracer.span("hitl", tool=call.name) as s:
                s.set(approved=decision.approved, note=decision.note)
            if not decision.approved:
                denied += 1
                working.add("tool", f"Action '{call.name}' was not approved: {decision.note}")
                continue
            approved += 1

            with self.tracer.span("act", tool=call.name) as s:
                observation = tool.fn(**call.arguments)
                s.set(observation=observation)
            working.add("tool", observation)

            step = plan.next_open()
            if step:
                step.done = True

        self.episodic.remember(Episode(goal=goal, outcome=answer, steps=steps))
        return AgentResult(
            answer=answer,
            steps=steps,
            approved_actions=approved,
            denied_actions=denied,
            trace=self.tracer.spans,
        )
