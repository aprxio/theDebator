"""PDF ingestion utilities."""

from itertools import islice
from pathlib import Path
from typing import Iterable, Iterator, List

from PyPDF2 import PdfReader

from .types import DocumentChunk


class PDFIngestor:
    """Read PDF files and yield contextual chunks with page citations."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)

    def read_pages(self) -> List[str]:
        """Return all pages as a list of strings."""
        reader = PdfReader(str(self.path))
        return [page.extract_text() or "" for page in reader.pages]

    def iter_chunks(
        self,
        chunk_size: int = 800,
        chunk_overlap: int = 200,
    ) -> Iterable[DocumentChunk]:
        """Yield overlapping chunks enriched with page numbers."""

        for page_number, page_text in enumerate(self.read_pages(), start=1):
            if not page_text.strip():
                continue

            words = page_text.split()
            if not words:
                continue

            chunk_words = max(chunk_size, 1)
            overlap_words = min(chunk_overlap, chunk_words - 1) if chunk_words > 1 else 0
            step = max(chunk_words - overlap_words, 1)

            for chunk_index, chunk in enumerate(_window(words, chunk_words, step)):
                content = " ".join(chunk).strip()
                if not content:
                    continue
                chunk_id = f"p{page_number}-c{chunk_index}"
                yield DocumentChunk(chunk_id=chunk_id, content=content, page=page_number)


def _window(words: List[str], size: int, step: int) -> Iterator[List[str]]:
    """Slide a window across words with overlap."""
    if size <= 0:
        size = 1
    if step <= 0:
        step = 1

    start = 0
    total = len(words)
    while start < total:
        chunk = list(islice(words, start, start + size))
        if not chunk:
            break
        yield chunk
        if start + size >= total:
            break
        start += step
