"""Conversation loop between agents."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Tuple

from thedebator.agents import ExplainerAgent, ReviewerAgent
from thedebator.retrieval import DocumentChunk, VectorStore


@dataclass
class ConversationTurn:
    speaker: str
    message: str
    citations: List[str] = field(default_factory=list)


@dataclass
class Conversation:
    explainer: ExplainerAgent
    reviewer: ReviewerAgent
    rounds: int
    store: VectorStore | None = None
    top_k: int = 3
    history: List[ConversationTurn] = field(default_factory=list)

    def run(self, topic: str) -> List[ConversationTurn]:
        prompt = topic
        for _ in range(self.rounds):
            explainer_context, explainer_citations = self._build_context(prompt)
            explainer_response = self.explainer.respond(
                prompt,
                context=explainer_context,
                history=self._history_text(),
            )
            self.history.append(
                ConversationTurn(self.explainer.name, explainer_response, explainer_citations)
            )

            reviewer_context, reviewer_citations = self._build_context(explainer_response)
            reviewer_response = self.reviewer.respond(
                explainer_response,
                context=reviewer_context,
                history=self._history_text(),
            )
            self.history.append(
                ConversationTurn(self.reviewer.name, reviewer_response, reviewer_citations)
            )
            prompt = reviewer_response
        return self.history

    def save_markdown(self, output_path: Path) -> None:
        lines = ["# Debate Discussion", ""]
        for turn in self.history:
            lines.append(f"## {turn.speaker}")
            lines.append(turn.message.strip())
            if turn.citations:
                lines.append(f"_Sources_: {' '.join(turn.citations)}")
            lines.append("")
        output_path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")

    def _history_text(self) -> List[str]:
        return [f"{turn.speaker}: {turn.message}" for turn in self.history]

    def _build_context(self, query: str) -> Tuple[str, List[str]]:
        if not self.store or not query.strip():
            return "", []

        chunks = self.store.similarity_search(query, k=self.top_k)
        if not chunks:
            return "", []

        return self._format_chunks(chunks)

    def _format_chunks(self, chunks: List[DocumentChunk]) -> Tuple[str, List[str]]:
        context_lines: List[str] = []
        citations: List[str] = []
        for chunk in chunks:
            citation = f"[p.{chunk.page}]"
            if citation not in citations:
                citations.append(citation)
            snippet = chunk.content.replace("\n", " ").strip()
            context_lines.append(f"{citation} {snippet}")
        return "\n".join(context_lines), citations
