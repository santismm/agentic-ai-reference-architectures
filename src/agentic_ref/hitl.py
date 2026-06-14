"""Human-in-the-loop (HITL).

Production agents must be able to *pause* before doing something consequential
and ask a human. The gate is policy-driven: any side-effecting tool, or any tool
whose arguments trip a policy rule, requires approval. The approver is injected,
so the same agent runs:

* unattended in CI with an ``auto_deny`` / ``auto_approve`` policy, or
* interactively with a real human at a console / Slack / web UI.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .tools import Tool


@dataclass
class ApprovalRequest:
    tool: str
    arguments: dict
    reason: str


@dataclass
class ApprovalDecision:
    approved: bool
    note: str = ""


Approver = Callable[[ApprovalRequest], ApprovalDecision]


def auto_approve(_: ApprovalRequest) -> ApprovalDecision:
    return ApprovalDecision(approved=True, note="auto-approved (non-interactive)")


def auto_deny(req: ApprovalRequest) -> ApprovalDecision:
    return ApprovalDecision(approved=False, note=f"auto-denied: {req.reason}")


def console_approver(req: ApprovalRequest) -> ApprovalDecision:  # pragma: no cover
    answer = input(f"[HITL] Approve {req.tool}({req.arguments})? {req.reason} [y/N] ")
    return ApprovalDecision(approved=answer.strip().lower() == "y")


class HumanGate:
    def __init__(self, approver: Approver = auto_deny) -> None:
        self.approver = approver

    def requires_approval(self, tool: Tool, arguments: dict) -> str | None:
        """Return a reason string if approval is needed, else ``None``."""
        if tool.side_effecting:
            return f"'{tool.name}' has side effects"
        return None

    def review(self, tool: Tool, arguments: dict) -> ApprovalDecision:
        reason = self.requires_approval(tool, arguments)
        if reason is None:
            return ApprovalDecision(approved=True, note="no approval required")
        return self.approver(ApprovalRequest(tool=tool.name, arguments=arguments, reason=reason))
