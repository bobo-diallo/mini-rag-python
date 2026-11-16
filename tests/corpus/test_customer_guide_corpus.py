"""Tests du corpus d'évaluation : un guide client fictif de 10 pages et 12 questions dont la page attendue est connue."""

import json
import subprocess
import sys
from pathlib import Path

from mini_rag.ingestion.chunker import chunk_pages
from mini_rag.ingestion.pdf_loader import PdfLoader

ROOT = Path(__file__).parent.parent.parent
GUIDE = ROOT / "eval" / "corpus" / "fictional-customer-guide.pdf"
QUESTIONS = ROOT / "eval" / "retrieval-questions.json"
SCRIPT = ROOT / "scripts" / "generate_guide_pdf.py"


def load_questions() -> list[dict]:
    return json.loads(QUESTIONS.read_text(encoding="utf-8"))


def test_the_guide_has_ten_pages_all_with_text():
    pages = PdfLoader().load(GUIDE)

    assert [p.source.page for p in pages] == list(range(1, 11))


def test_the_guide_announces_that_it_is_fictional():
    first_page = PdfLoader().load(GUIDE)[0]

    assert "fictif" in first_page.text


def test_accented_characters_survive_the_pdf():
    pages = PdfLoader().load(GUIDE)

    assert "préavis" in pages[4].text  # page 5 : résiliation
    assert "données" in pages[8].text  # page 9 : données personnelles


def test_each_page_makes_exactly_one_chunk_so_that_page_and_chunk_match():
    chunks = chunk_pages(PdfLoader().load(GUIDE))

    assert len(chunks) == 10
    assert [c.source.page for c in chunks] == list(range(1, 11))


def test_there_are_twelve_well_formed_questions():
    questions = load_questions()

    assert len(questions) == 12
    for entry in questions:
        assert entry["question"].strip().endswith("?")
        assert isinstance(entry["expected_page"], int)
        assert 1 <= entry["expected_page"] <= 10


def test_every_page_is_the_target_of_at_least_one_question():
    targeted = {entry["expected_page"] for entry in load_questions()}

    assert targeted == set(range(1, 11))


def test_the_pdf_is_exactly_what_the_script_generates(tmp_path: Path):
    # Le PDF versionné doit rester synchronisé avec le script qui contient le texte.
    regenerated = tmp_path / "regenerated.pdf"

    subprocess.run([sys.executable, str(SCRIPT), str(regenerated)], check=True, capture_output=True)

    assert regenerated.read_bytes() == GUIDE.read_bytes()
