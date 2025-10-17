"""Ollama backend implementation."""

from typing import List

import ollama

from .base import Backend


class OllamaBackend(Backend):
    """Generate responses using a local Ollama model."""

    def __init__(self, model: str) -> None:
        self.model = model

    def generate(self, prompt: str, history: List[str] | None = None) -> str:
        history_blocks = "\n\n".join(history[-6:]) if history else ""
        full_prompt = f"{history_blocks}\n\n{prompt}" if history_blocks else prompt
        response = ollama.generate(model=self.model, prompt=full_prompt)
        return response["response"]
