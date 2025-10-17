"""Backend abstraction for language models."""

from abc import ABC, abstractmethod
from typing import List


class Backend(ABC):
    """Abstract language model backend."""

    @abstractmethod
    def generate(self, prompt: str, history: List[str] | None = None) -> str:
        """Generate a response given a prompt and optional history."""
        raise NotImplementedError
