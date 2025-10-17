"""Explainer agent implementation."""

from thedebator.backends import Backend

from .agent import Agent


class ExplainerAgent(Agent):
    """Explains the paper claims."""

    def __init__(self, backend: Backend) -> None:
        super().__init__(name="Explainer A", backend=backend)

    def system_prompt(self) -> str:
        return (
            "You are Explainer A. Provide clear, grounded explanations of the scientific paper. "
            "Reference the paper text and cite pages using [p.X] annotations."
        )
