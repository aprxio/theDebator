"""PDF ingestion utilities."""

from itertools import islice
from pathlib import Path
from typing import Iterable, Iterator, List, Tuple

from PyPDF2 import PdfReader

from .types import DocumentChunk


class PDFIngestor:
    """Read PDF files and yield contextual chunks with page citations."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)

    def read_pages(self) -> List[Tuple[int, str]]:
        """Return all pages as list of (page_number, text) tuples."""
        reader = PdfReader(str(self.path))
        return [(i + 1, page.extract_text() or "") for i, page in enumerate(reader.pages)]

    def iter_chunks(
        self,
        chunk_size: int = 800,
        chunk_overlap: int = 200,
    ) -> Iterable[DocumentChunk]:
        """Yield overlapping chunks with page tracking across boundaries."""
        pages = self.read_pages()

        # Build full text with page position tracking
        full_text_parts = []
        page_positions = []  # track where each page starts in full text
        current_pos = 0

        for page_num, text in pages:
            if not text.strip():
                continue
            page_positions.append((page_num, current_pos))
            full_text_parts.append(text)
            current_pos += len(text) + 1  # +1 for space separator

        if not full_text_parts:
            return

        full_text = " ".join(full_text_parts)
        words = full_text.split()

        if not words:
            return

        chunk_words = max(chunk_size, 1)
        overlap_words = min(chunk_overlap, chunk_words - 1) if chunk_words > 1 else 0
        step = max(chunk_words - overlap_words, 1)

        for chunk_index, chunk in enumerate(_window(words, chunk_words, step)):
            content = " ".join(chunk).strip()
            if not content:
                continue

            # Determine page from character position in full text
            chunk_start = full_text.find(chunk[0]) if chunk else 0
            page = 1
            for pg_num, pg_pos in reversed(page_positions):
                if chunk_start >= pg_pos:
                    page = pg_num
                    break

            chunk_id = f"p{page}-c{chunk_index}"
            yield DocumentChunk(chunk_id=chunk_id, content=content, page=page)


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
