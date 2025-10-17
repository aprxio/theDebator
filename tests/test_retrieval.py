from thedebator.retrieval.pdf import PDFIngestor
from thedebator.retrieval.types import DocumentChunk


def test_pdf_ingestor_iter_chunks(monkeypatch, tmp_path):
    pdf_path = tmp_path / "sample.pdf"
    pdf_path.write_text("placeholder", encoding="utf-8")

    ingestor = PDFIngestor(pdf_path)

    monkeypatch.setattr(PDFIngestor, "read_pages", lambda self: ["word " * 20])

    chunks = list(ingestor.iter_chunks(chunk_size=5, chunk_overlap=2))

    assert chunks
    assert isinstance(chunks[0], DocumentChunk)
    assert chunks[0].page == 1
