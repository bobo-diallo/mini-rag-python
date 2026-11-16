"""Tests de build_answerer : le seul endroit qui assemble embedder, index, retriever, modèle et Answerer."""

import re
from collections.abc import Sequence

from mini_rag.composition import build_answerer
from mini_rag.config import Settings
from mini_rag.domain.models import Chunk, Source
from mini_rag.generation.chat_model import ChatModel, Completion
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
