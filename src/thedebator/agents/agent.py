"""Base agent abstraction."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List

from thedebator.backends import Backend


@dataclass
class Agent(ABC):
    """Agent with a role and backend."""

    name: str
    backend: Backend

    @abstractmethod
    def system_prompt(self) -> str:
        """Return the system prompt describing the agent."""
        raise NotImplementedError

    def respond(self, message: str, context: str = "", history: List[str] | None = None) -> str:
        parts = [self.system_prompt()]
        if context:
            parts.append("Context:\n" + context)
        parts.append("Message:\n" + message)
        prompt = "\n\n".join(parts)
        return self.backend.generate(prompt, history=history)
