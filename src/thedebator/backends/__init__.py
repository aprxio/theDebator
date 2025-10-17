"""Model backends."""

from .base import Backend
from .ollama import OllamaBackend

__all__ = [
    "Backend",
    "OllamaBackend",
]
