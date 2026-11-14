"""Parité avec la version TypeScript : mêmes pages et mêmes chunks sur le même PDF fictif."""

from pathlib import Path

from mini_rag.ingestion.chunker import chunk_pages
from mini_rag.ingestion.pdf_loader import PdfLoader

FICTIONAL_REPORT = Path(__file__).parent.parent / "fixtures" / "rapport-fictif.pdf"


def test_fictional_report_gives_the_same_statistics_as_the_typescript_version():
    pages = PdfLoader().load(FICTIONAL_REPORT)
    chunks = chunk_pages(pages)
    sizes = [len(chunk.text) for chunk in chunks]

    # Valeurs mesurées avec `npm run chunks` du projet mini-rag-local sur ce même PDF.
    assert len(pages) == 6
    assert len(chunks) == 29
    assert round(sum(sizes) / len(sizes)) == 877
    assert min(sizes) == 354
    assert max(sizes) == 999
