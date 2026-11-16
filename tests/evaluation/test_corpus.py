"""Tests de find_single_pdf : le corpus d'une évaluation est un dossier qui contient exactement un PDF."""

import shutil
from pathlib import Path

import pytest

from mini_rag.evaluation.corpus import CorpusError, find_single_pdf

TWO_PAGES = Path(__file__).parent.parent / "fixtures" / "two-pages.pdf"


def test_returns_the_only_pdf_of_the_folder(tmp_path: Path):
    shutil.copy(TWO_PAGES, tmp_path / "guide.PDF")  # extension en majuscules : acceptée
    (tmp_path / "notes.txt").write_text("pas un pdf")

    assert find_single_pdf(tmp_path) == tmp_path / "guide.PDF"


def test_a_missing_folder_is_reported(tmp_path: Path):
    with pytest.raises(CorpusError, match="introuvable.*absent"):
        find_single_pdf(tmp_path / "absent")


def test_a_folder_without_pdf_is_reported(tmp_path: Path):
    with pytest.raises(CorpusError, match="Aucun PDF"):
        find_single_pdf(tmp_path)


def test_several_pdfs_are_refused_because_page_numbers_would_be_ambiguous(tmp_path: Path):
    shutil.copy(TWO_PAGES, tmp_path / "a.pdf")
    shutil.copy(TWO_PAGES, tmp_path / "b.pdf")

    with pytest.raises(CorpusError, match="un seul PDF"):
        find_single_pdf(tmp_path)
