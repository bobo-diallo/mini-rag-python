"""Tests de la commande mini-rag-eval-answers, avec de faux composants : pas besoin d'Ollama."""

import json
import re
import shutil
from collections.abc import Sequence
from pathlib import Path

import pytest

from mini_rag.config import Settings
from mini_rag.evaluation.answers_cli import main
from mini_rag.generation.chat_model import ChatModel, Completion, GenerationError, TokenUsage
from mini_rag.retrieval.embedder import Embedder

TWO_PAGES = Path(__file__).parent.parent / "fixtures" / "two-pages.pdf"


class PageWordEmbedder(Embedder):
    """Les deux pages de la fixture parlent de « Premiere » et de « Deuxieme » ; une autre question n'a aucun mot connu."""

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        return [self.embed_query(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        words = re.findall(r"\w+", text.lower())
        # La troisième dimension reste à 1 : elle évite un vecteur nul pour une question hors sujet.
        return [float(words.count("premiere")), float(words.count("deuxieme")), 0.05]


class ScriptedChatModel(ChatModel):
    def __init__(self, text: str = "C'est là [1].") -> None:
        self.text = text
        self.calls = 0

    def generate(self, prompt: str) -> Completion:
        self.calls += 1
        return Completion(text=self.text, tokens=TokenUsage(prompt=100, generated=10))


class DownChatModel(ChatModel):
    def generate(self, prompt: str) -> Completion:
        raise GenerationError("Ollama injoignable (test)")


@pytest.fixture
def workspace(tmp_path: Path) -> dict[str, Path]:
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    shutil.copy(TWO_PAGES, corpus / "two-pages.pdf")
    questions = tmp_path / "questions.json"
    questions.write_text(json.dumps([{"question": "premiere page ?", "expected_page": 1}]))
    out_of_scope = tmp_path / "out-of-scope.json"
    out_of_scope.write_text(json.dumps([{"question": "capitale du Japon ?"}]))
    return {"corpus": corpus, "questions": questions, "out_of_scope": out_of_scope}


def run(workspace, chat_model=None, extra=(), settings=None) -> int:
    argv = [
        "--corpus", str(workspace["corpus"]),
        "--questions", str(workspace["questions"]),
        "--out-of-scope", str(workspace["out_of_scope"]),
        *extra,
    ]  # fmt: skip
    return main(
        argv,
        embedder=PageWordEmbedder(),
        chat_model=chat_model or ScriptedChatModel(),
        settings=settings or Settings(_env_file=None),
    )


def test_the_report_summarizes_both_kinds_of_questions(workspace, capsys):
    code = run(workspace)

    out = capsys.readouterr().out
    assert code == 0
    assert "Questions du guide : 1" in out
    assert "hors sujet : 1" in out
    assert "Réponses données" in out and "1/1" in out
    assert "Citations vérifiées" in out
    assert "Bonne page citée" in out
    assert "Refus justifiés" in out


def test_an_out_of_scope_question_is_refused_without_calling_the_model(workspace, capsys):
    model = ScriptedChatModel()

    run(workspace, chat_model=model)

    out = capsys.readouterr().out
    assert "refusés par le seuil seul (sans appel au modèle) : 1/1" in out
    assert model.calls == 1  # une seule question du guide a atteint le modèle


def test_each_question_is_asked_once_per_run_and_the_report_says_so(workspace, capsys):
    model = ScriptedChatModel()

    run(workspace, chat_model=model, extra=["--runs", "3"])

    out = capsys.readouterr().out
    assert "3 passages" in out
    assert model.calls == 3  # 1 question du guide x 3 passages ; la question hors sujet ne l'appelle pas


def test_show_answers_prints_what_the_model_wrote(workspace, capsys):
    run(workspace, chat_model=ScriptedChatModel("Réponse très reconnaissable [1]."), extra=["--show-answers"])

    assert "Réponse très reconnaissable [1]." in capsys.readouterr().out


def test_an_uncited_answer_is_visible_in_the_table(workspace, capsys):
    run(workspace, chat_model=ScriptedChatModel("Sans aucune référence."))

    out = capsys.readouterr().out
    assert "Citations vérifiées : 0/1" in out
    assert "Bonne page citée    : 0/1" in out


def test_tokens_and_time_are_reported(workspace, capsys):
    run(workspace)

    out = capsys.readouterr().out
    assert "Tokens : 110" in out
    assert "Durée totale" in out


@pytest.mark.parametrize("runs", ["0", "-2"])
def test_runs_must_be_at_least_1(workspace, capsys, runs):
    assert run(workspace, extra=["--runs", runs]) == 1
    assert "passage" in capsys.readouterr().err


def test_a_missing_question_file_fails_clearly(workspace, capsys):
    workspace["questions"].unlink()

    assert run(workspace) == 1
    assert "questions.json" in capsys.readouterr().err


def test_a_missing_out_of_scope_file_fails_clearly(workspace, capsys):
    workspace["out_of_scope"].unlink()

    assert run(workspace) == 1
    assert "out-of-scope.json" in capsys.readouterr().err


def test_a_model_failure_is_reported_without_a_traceback(workspace, capsys):
    code = run(workspace, chat_model=DownChatModel())

    captured = capsys.readouterr()
    assert code == 1
    assert "Ollama injoignable (test)" in captured.err
    assert "Traceback" not in captured.err


def test_claude_selected_without_a_key_is_reported_clearly(workspace, capsys):
    settings = Settings(_env_file=None, chat_provider="anthropic")  # pas de clé

    code = main(
        ["--corpus", str(workspace["corpus"]), "--questions", str(workspace["questions"]),
         "--out-of-scope", str(workspace["out_of_scope"])],
        embedder=PageWordEmbedder(),
        settings=settings,
    )  # fmt: skip

    captured = capsys.readouterr()
    assert code == 1
    assert "ANTHROPIC_API_KEY" in captured.err
    assert "Traceback" not in captured.err
