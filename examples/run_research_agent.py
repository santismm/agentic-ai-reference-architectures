"""Runnable demo: a small research agent.

No API key required — it uses the deterministic ``EchoModel`` so the output is
stable. Swap in ``vertex_model(...)`` (see ``agentic_ref.models``) to run it
against a real model.

    python examples/run_research_agent.py
"""

from __future__ import annotations

from agentic_ref import Agent, EchoModel, Tracer, default_registry
from agentic_ref.hitl import HumanGate, auto_approve


def main() -> None:
    agent = Agent(
        model=EchoModel(),
        tools=default_registry(),
        gate=HumanGate(approver=auto_approve),  # demo: approve side-effecting tools
        tracer=Tracer(sink=print),  # stream structured spans to stdout
    )

    goal = "Search and explain what the EU AI Act is."
    print(f"\nGOAL: {goal}\n" + "-" * 60)
    result = agent.run(goal)

    print("-" * 60)
    print(f"ANSWER:  {result.answer}")
    print(f"STEPS:   {result.steps}")
    print(f"ACTIONS: {result.approved_actions} approved / {result.denied_actions} denied")


if __name__ == "__main__":
    main()
