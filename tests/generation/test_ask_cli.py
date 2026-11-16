"""Tests de la commande mini-rag-ask, avec de faux composants : pas besoin d'Ollama."""

import re
import shutil
from collections.abc import Sequence
from pathlib import Path

import pytest

from mini_rag.config import Settings
from mini_rag.generation.chat_model import ChatModel, Completion, GenerationError, TokenUsage
from mini_rag.generation.cli import main
from mini_rag.generation.prompt import NO_ANSWER
from mini_rag.retrieval.embedder import Embedder, EmbeddingError

TWO_PAGES = Path(__file__).parent.parent / "fixtures" / "two-pages.pdf"


class PageWordEmbedder(Embedder):
    """Les deux pages de la fixture parlent de « Premiere » et de « Deuxieme » : c'est tout ce que ce faux voit."""

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        return [self.embed_query(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        words = re.findall(r"\w+", text.lower())
        return [float(words.count("premiere")), float(words.count("deuxieme"))]


class ScriptedChatModel(ChatModel):
    def __init__(self, text: str = "C'est la première page [1].", tokens: TokenUsage | None = None) -> None:
        self.text = text
        self.tokens = tokens
        self.prompts: list[str] = []

    def generate(self, prompt: str) -> Completion:
        self.prompts.append(prompt)
        return Completion(text=self.text, tokens=self.tokens)


class FailingChatModel(ChatModel):
    def generate(self, prompt: str) -> Completion:
        raise GenerationError("Ollama injoignable (test)")


class FailingEmbedder(Embedder):
    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        raise EmbeddingError("Embeddings indisponibles (test)")

    def embed_query(self, text: str) -> list[float]:
        raise EmbeddingError("Embeddings indisponibles (test)")


@pytest.fixture
def corpus(tmp_path: Path) -> Path:
    folder = tmp_path / "corpus"
    folder.mkdir()
    shutil.copy(TWO_PAGES, folder / "two-pages.pdf")
    return folder


def run(question, corpus, chat_model=None, extra=(), settings=None, embedder=None) -> int:
    argv = [question, "--corpus", str(corpus), *extra]
    return main(
        argv,
        embedder=embedder or PageWordEmbedder(),
        chat_model=chat_model or ScriptedChatModel(),
        settings=settings or Settings(_env_file=None),
    )


def test_prints_the_answer_and_the_verified_source_with_file_and_page(corpus: Path, capsys):
    code = run("premiere page ?", corpus)

    out = capsys.readouterr().out
    assert code == 0
    assert "C'est la première page [1]." in out
    assert "Sources vérifiées" in out
    assert "two-pages.pdf, page 1" in out


def test_the_model_receives_the_question_and_the_extracts(corpus: Path, capsys):
    model = ScriptedChatModel()

    run("premiere page ?", corpus, chat_model=model)

    assert "Question : premiere page ?" in model.prompts[0]
    assert "Premiere page fictive" in model.prompts[0]


def test_an_answer_without_any_citation_is_flagged_as_unsupported(corpus: Path, capsys):
    run("premiere page ?", corpus, chat_model=ScriptedChatModel("Je crois que oui."))

    assert "Aucune citation vérifiable" in capsys.readouterr().out


def test_an_invented_citation_number_is_flagged(corpus: Path, capsys):
    run("premiere page ?", corpus, chat_model=ScriptedChatModel("Selon [9], oui."))

    out = capsys.readouterr().out
    assert "[9]" in out
    assert "n'existent pas" in out


def test_a_refusal_below_the_threshold_says_so_and_never_calls_the_model(corpus: Path, capsys):
    model = ScriptedChatModel()

    # « premiere deuxieme » donne un cosinus de 0,71 avec chaque page : sous un seuil de 1,0.
    code = run("premiere deuxieme", corpus, chat_model=model, settings=Settings(_env_file=None, min_score=1.0))

    out = capsys.readouterr().out
    assert code == 0  # refuser honnêtement n'est pas une erreur
    assert NO_ANSWER in out
    assert "Aucun appel au modèle" in out
    assert "seuil : 1.00" in out
    assert model.prompts == []


def test_a_refusal_by_the_model_is_reported_as_such(corpus: Path, capsys):
    run("premiere page ?", corpus, chat_model=ScriptedChatModel("Je ne sais pas, désolé."))

    out = capsys.readouterr().out
    assert NO_ANSWER in out
    assert "le modèle a répondu qu'il ne sait pas" in out
    assert "Sources vérifiées" not in out


def test_token_usage_is_shown_when_the_model_reports_it(corpus: Path, capsys):
    run("premiere page ?", corpus, chat_model=ScriptedChatModel(tokens=TokenUsage(prompt=120, generated=15)))

    assert "120 lus + 15 écrits = 135" in capsys.readouterr().out


def test_verbose_lists_every_extract_found_with_its_score(corpus: Path, capsys):
    run("premiere page ?", corpus, extra=["--verbose"])

    out = capsys.readouterr().out
    assert "Extraits retrouvés" in out
    assert "page 1" in out and "page 2" in out
    assert "score" in out


def test_several_pdfs_can_be_asked_at_once(corpus: Path, capsys):
    shutil.copy(TWO_PAGES, corpus / "another.pdf")

    assert run("premiere page ?", corpus) == 0


@pytest.mark.parametrize("question", ["", "   "])
def test_an_empty_question_is_refused(corpus: Path, capsys, question: str):
    assert run(question, corpus) == 1
    assert "question" in capsys.readouterr().err


def test_a_missing_corpus_folder_fails_clearly(tmp_path: Path, capsys):
    assert run("premiere page ?", tmp_path / "absent") == 1
    assert "absent" in capsys.readouterr().err


def test_a_corpus_without_pdf_fails_clearly(tmp_path: Path, capsys):
    empty = tmp_path / "empty"
    empty.mkdir()

    assert run("premiere page ?", empty) == 1
    assert "Aucun PDF" in capsys.readouterr().err


@pytest.mark.parametrize(
    "failure, message",
    [
        ({"chat_model": FailingChatModel()}, "Ollama injoignable (test)"),
        ({"embedder": FailingEmbedder()}, "Embeddings indisponibles (test)"),
    ],
)
def test_a_failure_of_a_component_is_reported_without_a_traceback(corpus: Path, capsys, failure, message):
    code = run("premiere page ?", corpus, **failure)

    captured = capsys.readouterr()
    assert code == 1
    assert message in captured.err
    assert "Traceback" not in captured.err
