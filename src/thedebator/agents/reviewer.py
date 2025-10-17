"""Reviewer agent implementation."""

from thedebator.backends import Backend

from .agent import Agent


class ReviewerAgent(Agent):
    """Challenges claims and requests evidence."""

    def __init__(self, backend: Backend) -> None:
        super().__init__(name="Reviewer B", backend=backend)

    def system_prompt(self) -> str:
        return (
            "You are Reviewer B. Critically evaluate Explainer A's claims, demanding evidence and citations. "
            "Highlight weak arguments and ensure every assertion is grounded and cited as [p.X]."
        )
