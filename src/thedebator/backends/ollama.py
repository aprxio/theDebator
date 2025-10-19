"""Ollama backend implementation."""

from typing import Generator, List

import ollama

from .base import Backend


class OllamaBackend(Backend):
    """Generate responses using a local Ollama model."""

    def __init__(self, model: str, max_history_tokens: int = 2000) -> None:
        self.model = model
        self.max_history_tokens = max_history_tokens

    def generate(self, prompt: str, history: List[str] | None = None) -> str:
        """Generate a complete response with token budget management."""
        # Take only recent history to prevent token overflow
        history_blocks = ""
        if history:
            # Estimate ~4 chars per token, keep last N turns within budget
            char_budget = self.max_history_tokens * 4
            recent = []
            char_count = 0
            for turn in reversed(history):
                if char_count + len(turn) > char_budget:
                    break
                recent.insert(0, turn)
                char_count += len(turn)
            history_blocks = "\n\n".join(recent)

        full_prompt = f"{history_blocks}\n\n{prompt}" if history_blocks else prompt

        response = ollama.generate(
            model=self.model,
            prompt=full_prompt,
            options={
                "num_ctx": 4096,  # explicit context window
                "num_gpu": 1,  # force Metal acceleration on M2
            },
        )

        # Log token metrics for debugging
        if "eval_count" in response:
            eval_count = response.get("eval_count", 0)
            eval_duration = response.get("eval_duration", 1) / 1e9  # nanoseconds to seconds
            tokens_per_sec = eval_count / max(eval_duration, 0.001)
            print(f"[{self.model}] Generated {eval_count} tokens @ {tokens_per_sec:.1f} tok/s")

        return response["response"]

    def generate_stream(
        self, prompt: str, history: List[str] | None = None
    ) -> Generator[str, None, None]:
        """Stream tokens as they're generated for real-time output."""
        history_blocks = ""
        if history:
            char_budget = self.max_history_tokens * 4
            recent = []
            char_count = 0
            for turn in reversed(history):
                if char_count + len(turn) > char_budget:
                    break
                recent.insert(0, turn)
                char_count += len(turn)
            history_blocks = "\n\n".join(recent)

        full_prompt = f"{history_blocks}\n\n{prompt}" if history_blocks else prompt

        stream = ollama.generate(
            model=self.model,
            prompt=full_prompt,
            stream=True,
            options={
                "num_ctx": 4096,
                "num_gpu": 1,
            },
        )

        for chunk in stream:
            if "response" in chunk:
                yield chunk["response"]
