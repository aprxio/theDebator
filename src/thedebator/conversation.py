"""Conversation loop between agents."""

import sys
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
    stream_output: bool = False
    history: List[ConversationTurn] = field(default_factory=list)

    def run(self, topic: str) -> List[ConversationTurn]:
        prompt = topic
        for round_num in range(self.rounds):
            if self.stream_output:
                print(f"\n{'='*60}")
                print(f"Round {round_num + 1}/{self.rounds}")
                print(f"{'='*60}\n")

            # Explainer's turn
            explainer_context, explainer_citations = self._build_context(prompt)
            explainer_response = self._generate_response(
                agent=self.explainer,
                prompt=prompt,
                context=explainer_context,
                citations=explainer_citations,
            )
            self.history.append(
                ConversationTurn(self.explainer.name, explainer_response, explainer_citations)
            )

            # Reviewer's turn
            reviewer_context, reviewer_citations = self._build_context(explainer_response)
            reviewer_response = self._generate_response(
                agent=self.reviewer,
                prompt=explainer_response,
                context=reviewer_context,
                citations=reviewer_citations,
            )
            self.history.append(
                ConversationTurn(self.reviewer.name, reviewer_response, reviewer_citations)
            )
            prompt = reviewer_response

        return self.history

    def _generate_response(
        self, agent: ExplainerAgent | ReviewerAgent, prompt: str, context: str, citations: List[str]
    ) -> str:
        """Generate response with optional streaming output."""
        # Build the full prompt with system + context + message
        parts = [agent.system_prompt()]
        if context:
            parts.append("Context:\n" + context)
        parts.append("Message:\n" + prompt)
        full_prompt = "\n\n".join(parts)

        if self.stream_output and hasattr(agent.backend, "generate_stream"):
            # Stream tokens in real-time
            print(f"\n## {agent.name}")
            response_parts = []
            for token in agent.backend.generate_stream(full_prompt, self._history_text()):
                print(token, end="", flush=True)
                sys.stdout.flush()
                response_parts.append(token)
            print()  # newline after streaming

            if citations:
                print(f"_Sources_: {' '.join(citations)}\n")

            return "".join(response_parts)
        else:
            # Standard non-streaming generation
            return agent.respond(prompt, context=context, history=self._history_text())

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
