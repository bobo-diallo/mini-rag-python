"""Tests du lecteur de PDF : une entrée par page non vide, numérotée à partir de 1."""

from pathlib import Path

import pytest
from pypdf import PdfReader, PdfWriter

from mini_rag.ingestion.pdf_loader import PdfLoader

FIXTURE = Path(__file__).parent.parent / "fixtures" / "two-pages.pdf"


def test_returns_one_entry_per_page_numbered_from_1():
    pages = PdfLoader().load(FIXTURE)

    assert [p.source.page for p in pages] == [1, 2]


def test_source_holds_the_file_name_not_the_full_path():
    pages = PdfLoader().load(FIXTURE)

    assert all(p.source.file == "two-pages.pdf" for p in pages)


def test_extracts_the_text_of_each_page():
    pages = PdfLoader().load(FIXTURE)

    assert "Premiere page fictive" in pages[0].text
    assert "Deuxieme page fictive" in pages[1].text


def test_accepts_a_path_given_as_a_string():
    pages = PdfLoader().load(str(FIXTURE))

    assert len(pages) == 2


def test_fails_clearly_when_the_file_does_not_exist(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        PdfLoader().load(tmp_path / "absent.pdf")


def test_skips_pages_without_text_but_keeps_real_page_numbers(tmp_path: Path):
    # On fabrique un PDF de 3 pages : une page de texte, une page blanche, une page de texte.
    source_pdf = PdfReader(FIXTURE)
    writer = PdfWriter()
    writer.add_page(source_pdf.pages[0])
    writer.add_blank_page(width=200, height=200)
    writer.add_page(source_pdf.pages[1])
    path = tmp_path / "with-blank-page.pdf"
    with path.open("wb") as file:
        writer.write(file)

    pages = PdfLoader().load(path)

    # La page blanche (n° 2) disparaît, mais la dernière page reste la n° 3 : la citation reste exacte.
    assert [p.source.page for p in pages] == [1, 3]
