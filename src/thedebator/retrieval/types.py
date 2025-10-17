"""Shared retrieval data structures."""

from dataclasses import dataclass


@dataclass
class DocumentChunk:
    """A single chunk of document text with citation metadata."""

    chunk_id: str
    content: str
    page: int
