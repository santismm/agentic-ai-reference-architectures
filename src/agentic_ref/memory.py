"""Memory.

Two distinct concerns are deliberately separated:

* **Working memory** — the scratchpad for the current run (messages, tool
  observations). Ephemeral.
* **Episodic memory** — durable records of past runs the agent can recall to
  avoid repeating work. Backed by a pluggable store; the default is in-memory so
  it runs anywhere, but the interface is the same one a vector DB would satisfy.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .models import Message


@dataclass
class WorkingMemory:
    messages: list[Message] = field(default_factory=list)

    def add(self, role: str, content: str) -> None:
        self.messages.append(Message(role=role, content=content))

    def transcript(self) -> list[Message]:
        return list(self.messages)


@dataclass
class Episode:
    goal: str
    outcome: str
    steps: int


class EpisodicMemory:
    """Pluggable recall store. Default impl is a keyword match over past goals.

    Swap ``recall`` for an embedding search to get semantic recall — the rest of
    the architecture does not change.
    """

    def __init__(self) -> None:
        self._episodes: list[Episode] = []

    def remember(self, episode: Episode) -> None:
        self._episodes.append(episode)

    def recall(self, goal: str, k: int = 1) -> list[Episode]:
        scored = sorted(
            self._episodes,
            key=lambda e: _overlap(goal, e.goal),
            reverse=True,
        )
        return [e for e in scored[:k] if _overlap(goal, e.goal) > 0]

    def __len__(self) -> int:
        return len(self._episodes)


def _overlap(a: str, b: str) -> int:
    return len(set(a.lower().split()) & set(b.lower().split()))
