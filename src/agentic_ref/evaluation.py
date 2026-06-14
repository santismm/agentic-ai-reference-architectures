"""Evaluation.

Agents regress silently. The only defense is an offline eval suite that runs in
CI on every change. This is a deliberately small, dependency-free harness: a case
is a goal plus a checker; a report is pass-rate plus per-case detail. Wire it into
``pytest`` or run it standalone.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from .agent import Agent, AgentResult

Checker = Callable[[AgentResult], bool]


@dataclass
class Case:
    name: str
    goal: str
    check: Checker


@dataclass
class CaseResult:
    name: str
    passed: bool
    answer: str


@dataclass
class Report:
    results: list[CaseResult] = field(default_factory=list)

    @property
    def pass_rate(self) -> float:
        if not self.results:
            return 0.0
        return sum(r.passed for r in self.results) / len(self.results)

    def summary(self) -> str:
        lines = [f"{'PASS' if r.passed else 'FAIL'}  {r.name}" for r in self.results]
        lines.append(f"\npass rate: {self.pass_rate:.0%} ({sum(r.passed for r in self.results)}/{len(self.results)})")
        return "\n".join(lines)


def evaluate(agent_factory: Callable[[], Agent], cases: list[Case]) -> Report:
    """Run each case on a *fresh* agent so cases don't leak state into each other."""
    report = Report()
    for case in cases:
        agent = agent_factory()
        result = agent.run(case.goal)
        report.results.append(
            CaseResult(name=case.name, passed=case.check(result), answer=result.answer)
        )
    return report


def contains(substring: str) -> Checker:
    return lambda result: substring.lower() in result.answer.lower()
