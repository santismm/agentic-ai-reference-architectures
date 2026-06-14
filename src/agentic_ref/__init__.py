"""agentic_ref — reference architecture for production AI agents.

Six composable concerns: planning, tools, memory, evaluation, human-in-the-loop
and observability. See the module docstrings and the repository README.
"""

from .agent import Agent, AgentResult
from .evaluation import Case, Report, contains, evaluate
from .hitl import HumanGate, auto_approve, auto_deny, console_approver
from .memory import EpisodicMemory, WorkingMemory
from .models import LLM, Completion, EchoModel, Message
from .observability import Tracer
from .planning import Plan, Planner
from .tools import Tool, ToolRegistry, default_registry

__version__ = "0.1.0"

__all__ = [
    "Agent",
    "AgentResult",
    "Case",
    "Report",
    "contains",
    "evaluate",
    "HumanGate",
    "auto_approve",
    "auto_deny",
    "console_approver",
    "EpisodicMemory",
    "WorkingMemory",
    "LLM",
    "Completion",
    "EchoModel",
    "Message",
    "Tracer",
    "Plan",
    "Planner",
    "Tool",
    "ToolRegistry",
    "default_registry",
    "__version__",
]
