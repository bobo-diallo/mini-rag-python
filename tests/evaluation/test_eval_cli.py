"""Tests de la commande mini-rag-eval-retrieval, avec un faux embedder : pas besoin d'Ollama."""

import json
import re
import shutil
from collections.abc import Sequence
from pathlib import Path

import pytest

from mini_rag.config import Settings
from mini_rag.evaluation.cli import main
from mini_rag.retrieval.embedder import Embedder, EmbeddingError

TWO_PAGES = Path(__file__).parent.parent / "fixtures" / "two-pages.pdf"


class PageWordEmbedder(Embedder):
    """Les deux pages de la fixture parlent de « Premiere » et de « Deuxieme » : c'est tout ce que ce faux voit."""

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        return [self.embed_query(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        words = re.findall(r"\w+", text.lower())
        return [float(words.count("premiere")), float(words.count("deuxieme"))]


class BrokenEmbedder(Embedder):
    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        raise EmbeddingError("Ollama injoignable (test)")

    def embed_query(self, text: str) -> list[float]:
        raise EmbeddingError("Ollama injoignable (test)")


@pytest.fixture
def corpus(tmp_path: Path) -> Path:
    folder = tmp_path / "corpus"
    folder.mkdir()
    shutil.copy(TWO_PAGES, folder / "two-pages.pdf")
    return folder


def write_questions(tmp_path: Path, entries) -> Path:
    path = tmp_path / "questions.json"
    path.write_text(json.dumps(entries), encoding="utf-8")
    return path


@pytest.fixture
def perfect_questions(tmp_path: Path) -> Path:
    return write_questions(
        tmp_path,
        [
            {"question": "premiere ?", "expected_page": 1},
            {"question": "deuxieme ?", "expected_page": 2},
        ],
    )


def run(corpus: Path, questions: Path, extra: Sequence[str] = (), embedder: Embedder | None = None) -> int:
    argv = ["--corpus", str(corpus), "--questions", str(questions), *extra]
    return main(argv, embedder=embedder or PageWordEmbedder(), settings=Settings(_env_file=None))


def test_a_perfect_run_scores_100_percent(corpus: Path, perfect_questions: Path, capsys):
    code = run(corpus, perfect_questions)

    out = capsys.readouterr().out
    assert code == 0
    assert "hit@1 : 2/2 = 100%" in out
    assert "hit@3 : 2/2 = 100%" in out
    assert "MRR   : 1.00" in out


def test_the_report_lists_each_question_with_its_rank(corpus: Path, perfect_questions: Path, capsys):
    run(corpus, perfect_questions)

    out = capsys.readouterr().out
    assert "premiere ?" in out
    assert "deuxieme ?" in out
    assert "2 chunks" in out


def test_a_wrong_expectation_lowers_the_scores(corpus: Path, tmp_path: Path, capsys):
    questions = write_questions(
        tmp_path,
        [
            {"question": "premiere ?", "expected_page": 1},  # trouvée en 1er
            {"question": "premiere ?", "expected_page": 2},  # la page 2 arrive en 2e
        ],
    )

    run(corpus, questions)

    out = capsys.readouterr().out
    assert "hit@1 : 1/2 = 50%" in out
    assert "MRR   : 0.75" in out


def test_the_report_gives_the_random_baseline_to_compare_with(corpus: Path, perfect_questions: Path, capsys):
    run(corpus, perfect_questions)

    # Avec 2 pages seulement, le hasard met toujours la bonne dans les 3 premières : hit@3 = 100 %, MRR = 0,75.
    assert "Hasard (référence) : hit@3 = 100%, MRR = 0.75" in capsys.readouterr().out


def test_k_limits_how_far_down_the_ranking_we_look(corpus: Path, tmp_path: Path, capsys):
    questions = write_questions(tmp_path, [{"question": "premiere ?", "expected_page": 2}])

    run(corpus, questions, extra=["--k", "1"])

    out = capsys.readouterr().out
    assert "hit@3 : 0/1 = 0%" in out  # la page 2 est au rang 2, hors des 1 résultats gardés


@pytest.mark.parametrize("extra", [["--k", "0"]])
def test_an_invalid_k_is_rejected(corpus: Path, perfect_questions: Path, capsys, extra):
    assert run(corpus, perfect_questions, extra=extra) == 1
    assert "k" in capsys.readouterr().err


def test_a_missing_corpus_folder_fails_clearly(tmp_path: Path, perfect_questions: Path, capsys):
    assert run(tmp_path / "absent", perfect_questions) == 1
    assert "absent" in capsys.readouterr().err


def test_a_corpus_without_pdf_fails_clearly(tmp_path: Path, perfect_questions: Path, capsys):
    empty = tmp_path / "empty"
    empty.mkdir()

    assert run(empty, perfect_questions) == 1
    assert "Aucun PDF" in capsys.readouterr().err


def test_a_corpus_with_several_pdfs_is_refused_because_page_numbers_would_be_ambiguous(
    corpus: Path, perfect_questions: Path, capsys
):
    shutil.copy(TWO_PAGES, corpus / "another.pdf")

    assert run(corpus, perfect_questions) == 1
    assert "un seul PDF" in capsys.readouterr().err


def test_a_missing_question_file_fails_clearly(corpus: Path, tmp_path: Path, capsys):
    assert run(corpus, tmp_path / "absent.json") == 1
    assert "absent.json" in capsys.readouterr().err


def test_an_invalid_question_file_fails_with_the_validation_message(corpus: Path, tmp_path: Path, capsys):
    broken = write_questions(tmp_path, [{"question": "Où ?"}])

    assert run(corpus, broken) == 1
    assert "expected_page" in capsys.readouterr().err


def test_an_embedding_failure_is_reported_without_a_traceback(corpus: Path, perfect_questions: Path, capsys):
    code = run(corpus, perfect_questions, embedder=BrokenEmbedder())

    captured = capsys.readouterr()
    assert code == 1
    assert "Ollama injoignable (test)" in captured.err
    assert "Traceback" not in captured.err
