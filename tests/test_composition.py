"""Tests de build_answerer : le seul endroit qui assemble embedder, index, retriever, modèle et Answerer."""

import re
from collections.abc import Sequence

import pytest

from mini_rag.composition import build_answerer, build_chat_model, describe_chat_model
from mini_rag.config import ConfigurationError, Settings
from mini_rag.domain.models import Chunk, Source
from mini_rag.generation.anthropic_chat_model import AnthropicChatModel
from mini_rag.generation.chat_model import ChatModel, Completion
from mini_rag.generation.ollama_chat_model import OllamaChatModel
from mini_rag.retrieval.embedder import Embedder


class WordEmbedder(Embedder):
    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        return [self.embed_query(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        words = re.findall(r"\w+", text.lower())
        return [float(words.count("alpha")), float(words.count("beta"))]


class CountingChatModel(ChatModel):
    def __init__(self) -> None:
        self.calls = 0

    def generate(self, prompt: str) -> Completion:
        self.calls += 1
        return Completion(text="Voilà [1].", tokens=None)


def chunk(text: str, page: int) -> Chunk:
    return Chunk(text=text, source=Source(file="g.pdf", page=page), index=0)


CHUNKS = [chunk("alpha", 1), chunk("beta", 2), chunk("alpha beta", 3)]


def test_the_assembled_answerer_answers_from_the_indexed_chunks():
    answerer = build_answerer(CHUNKS, Settings(_env_file=None), embedder=WordEmbedder(), chat_model=CountingChatModel())

    reply = answerer.answer("alpha ?")

    assert reply.answered is True
    assert reply.citations[0].chunk.source.page == 1


def test_top_k_comes_from_the_settings():
    settings = Settings(_env_file=None, top_k=2)

    reply = build_answerer(CHUNKS, settings, embedder=WordEmbedder(), chat_model=CountingChatModel()).answer("alpha ?")

    assert len(reply.retrieved) == 2


def test_min_score_comes_from_the_settings_and_a_refusal_does_not_call_the_model():
    model = CountingChatModel()
    settings = Settings(_env_file=None, min_score=1.0)  # seul un score parfait suffirait

    reply = build_answerer(CHUNKS, settings, embedder=WordEmbedder(), chat_model=model).answer("alpha beta ?")

    assert reply.answered is False
    assert model.calls == 0


# --- Choix du fournisseur de génération --------------------------------------------------------


def test_the_default_provider_is_local_ollama():
    assert isinstance(build_chat_model(Settings(_env_file=None)), OllamaChatModel)


def test_the_anthropic_provider_builds_a_claude_client_without_any_network_call():
    settings = Settings(_env_file=None, chat_provider="anthropic", anthropic_api_key="sk-ant-test")

    assert isinstance(build_chat_model(settings), AnthropicChatModel)


@pytest.mark.parametrize("key", [None, "", "   "])
def test_the_anthropic_provider_without_a_key_explains_what_to_set(key):
    settings = Settings(_env_file=None, chat_provider="anthropic", anthropic_api_key=key)

    with pytest.raises(ConfigurationError, match="ANTHROPIC_API_KEY"):
        build_chat_model(settings)


def test_a_missing_key_fails_before_any_embedding_work_is_done():
    calls = []

    class RecordingEmbedder(WordEmbedder):
        def embed_documents(self, texts):
            calls.append(len(texts))
            return super().embed_documents(texts)

    settings = Settings(_env_file=None, chat_provider="anthropic")  # pas de clé

    with pytest.raises(ConfigurationError):
        build_answerer(CHUNKS, settings, embedder=RecordingEmbedder())

    assert calls == []  # on n'a calculé aucun vecteur pour rien


def test_the_report_label_names_the_model_that_really_answers():
    local = Settings(_env_file=None)
    remote = Settings(_env_file=None, chat_provider="anthropic", anthropic_api_key="sk-ant-test")

    assert describe_chat_model(local) == "llama3.2:3b (Ollama, local)"
    assert describe_chat_model(remote) == "claude-haiku-5-5 (Anthropic, à distance)"
