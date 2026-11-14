"""Tests de la commande de comptage : pour chaque PDF d'un dossier, pages et chunks."""

import shutil
from pathlib import Path

import pytest
from pypdf import PdfWriter

from mini_rag.cli import main

FIXTURE = Path(__file__).parent / "fixtures" / "two-pages.pdf"


@pytest.fixture
def folder_with_pdfs(tmp_path: Path) -> Path:
    """Un dossier contenant deux PDF (copies de la fixture) et un fichier qui n'est pas un PDF."""
    shutil.copy(FIXTURE, tmp_path / "b-two-pages.pdf")
    shutil.copy(FIXTURE, tmp_path / "a-two-pages.PDF")  # extension en majuscules : acceptée
    (tmp_path / "notes.txt").write_text("pas un pdf")
    return tmp_path


def test_prints_pages_and_chunks_of_each_pdf(folder_with_pdfs: Path, capsys):
    code = main([str(folder_with_pdfs)])

    output = capsys.readouterr().out
    assert code == 0
    assert "pages : 2" in output
    assert "chunks : 2" in output  # une phrase courte par page : un chunk par page


def test_pdfs_are_listed_alphabetically_and_other_files_ignored(folder_with_pdfs: Path, capsys):
    main([str(folder_with_pdfs)])

    output = capsys.readouterr().out
    assert output.index("a-two-pages.PDF") < output.index("b-two-pages.pdf")
    assert "notes.txt" not in output


def test_recalls_the_chunking_settings(folder_with_pdfs: Path, capsys):
    main([str(folder_with_pdfs)])

    assert "taille 1000, chevauchement 200" in capsys.readouterr().out


def test_folder_without_pdf_fails_with_a_message_on_the_error_output(tmp_path: Path, capsys):
    code = main([str(tmp_path)])

    captured = capsys.readouterr()
    assert code == 1
    assert "Aucun PDF" in captured.err
    assert captured.out == ""


def test_missing_folder_fails_clearly(tmp_path: Path, capsys):
    code = main([str(tmp_path / "absent")])

    assert code == 1
    assert "absent" in capsys.readouterr().err


def test_a_pdf_without_any_text_gives_zero_chunks_without_crashing(tmp_path: Path, capsys):
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    with (tmp_path / "empty.pdf").open("wb") as file:
        writer.write(file)

    code = main([str(tmp_path)])

    output = capsys.readouterr().out
    assert code == 0
    assert "pages : 0" in output
    assert "chunks : 0" in output
