"""Tests du chargement des questions d'évaluation : un fichier JSON, validé entrée par entrée."""

import json
from pathlib import Path

import pytest

from mini_rag.evaluation.questions import EvalQuestion, load_questions

REAL_FILE = Path(__file__).parent.parent.parent / "eval" / "retrieval-questions.json"


def write(tmp_path: Path, content) -> Path:
    path = tmp_path / "questions.json"
    path.write_text(json.dumps(content), encoding="utf-8")
    return path


def test_loads_questions_with_their_expected_page(tmp_path: Path):
    path = write(tmp_path, [{"question": "Où ?", "expected_page": 3}])

    assert load_questions(path) == [EvalQuestion(question="Où ?", expected_page=3)]


def test_the_real_question_file_loads():
    questions = load_questions(REAL_FILE)

    assert len(questions) == 12
    assert all(q.expected_page >= 1 for q in questions)


def test_a_missing_file_fails_clearly(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        load_questions(tmp_path / "absent.json")


@pytest.mark.parametrize(
    "content, expected_message",
    [
        ({"question": "pas une liste"}, "liste"),
        ([], "aucune question"),
        (["pas un objet"], "n° 1"),
        ([{"expected_page": 1}], "question"),
        ([{"question": "   ", "expected_page": 1}], "question"),
        ([{"question": "Où ?"}], "expected_page"),
        ([{"question": "Où ?", "expected_page": "3"}], "expected_page"),
        ([{"question": "Où ?", "expected_page": 0}], "expected_page"),
    ],
)
def test_invalid_content_is_rejected_with_a_message_naming_the_problem(tmp_path: Path, content, expected_message):
    with pytest.raises(ValueError, match=expected_message):
        load_questions(write(tmp_path, content))
