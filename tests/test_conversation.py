from pathlib import Path

from thedebator.agents.explainer import ExplainerAgent
from thedebator.agents.reviewer import ReviewerAgent
from thedebator.backends.base import Backend
from thedebator.conversation import Conversation
from thedebator.retrieval.types import DocumentChunk


class FakeBackend(Backend):
    def __init__(self, label: str) -> None:
        self.label = label
        self.last_prompt: str | None = None
        self.history: list[str] = []

    def generate(self, prompt: str, history=None) -> str:
        self.last_prompt = prompt
        self.history = list(history or [])
        return f"{self.label} reply"


class FakeStore:
    def __init__(self) -> None:
        self.calls = []

    def similarity_search(self, query: str, k: int = 3):
        self.calls.append((query, k))
        return [DocumentChunk(chunk_id="c1", content="Cells divide faster.", page=2)]


def test_conversation_produces_citations(tmp_path: Path) -> None:
    backend = FakeBackend(label="agent")
    explainer = ExplainerAgent(backend=backend)
    reviewer = ReviewerAgent(backend=backend)
    store = FakeStore()

    conversation = Conversation(
        explainer=explainer,
        reviewer=reviewer,
        rounds=1,
        store=store,
        top_k=1,
    )

    history = conversation.run("Explain cell growth")

    assert history[0].citations == ["[p.2]"]
    assert "Context:" in backend.last_prompt

    output_path = tmp_path / "discussion.md"
    conversation.save_markdown(output_path)

    content = output_path.read_text(encoding="utf-8")
    assert "[p.2]" in content
