"""Tests double as the offline eval suite (run in CI)."""

from __future__ import annotations

from agentic_ref import Agent, EchoModel, Tracer, default_registry
from agentic_ref.evaluation import Case, contains, evaluate
from agentic_ref.hitl import HumanGate, auto_approve, auto_deny
from agentic_ref.tools import Tool


def make_agent(approver=auto_approve) -> Agent:
    return Agent(
        model=EchoModel(),
        tools=default_registry(),
        gate=HumanGate(approver=approver),
        tracer=Tracer(),
    )


def test_agent_uses_tool_and_answers():
    result = make_agent().run("Search and explain what the EU AI Act is.")
    assert "risk" in result.answer.lower()
    assert result.approved_actions >= 1


def test_calculator_path():
    result = make_agent().run("Calculate 21 * 2")
    assert "42" in result.answer


def test_observability_emits_spans():
    result = make_agent().run("Search what is rag")
    names = {s.name for s in result.trace}
    assert {"plan", "think", "act"} <= names


def test_hitl_blocks_side_effecting_tool():
    reg = default_registry()
    reg.register(
        Tool(
            name="send_email",
            description="Send an email.",
            fn=lambda **_: "sent",
            parameters={"type": "object", "properties": {"query": {"type": "string"}}},
            triggers=["send_email"],
            side_effecting=True,
        )
    )
    agent = Agent(model=EchoModel(), tools=reg, gate=HumanGate(approver=auto_deny))
    result = agent.run("Use send_email to notify the team")
    assert result.denied_actions >= 1


def test_eval_harness():
    cases = [
        Case("eu-ai-act", "Search and explain the EU AI Act.", contains("risk")),
        Case("arithmetic", "Calculate 2 * 20", contains("40")),
    ]
    report = evaluate(make_agent, cases)
    assert report.pass_rate == 1.0
