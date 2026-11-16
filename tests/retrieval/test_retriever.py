"""Tests du Retriever : indexer des chunks (texte vers vecteur vers index), puis retrouver les plus proches."""

from collections.abc import Sequence

import pytest

from mini_rag.domain.models import Chunk, Source
from mini_rag.retrieval.embedder import Embedder
from mini_rag.retrieval.retriever import Retriever
from mini_rag.retrieval.vector_store import InMemoryVectorStore

# Trois thèmes ; un mot-clé fait monter la dimension de son thème. Les textes de test contiennent
# tous au moins un mot-clé : un vecteur nul n'aurait pas de direction (voir cosine_similarity).
TOPICS = {"chat": 0, "chaton": 0, "taxe": 1, "impôt": 1, "avion": 2, "vol": 2}


class TopicEmbedder(Embedder):
    """Faux embedder « thématique » : le sens d'un texte = le nombre de mots-clés de chaque thème.

    Il note chaque appel dans `calls` sous la forme ("documents", nombre de textes) ou ("query", texte).
    """

    def __init__(self) -> None:
        self.calls: list[tuple[str, object]] = []

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        self.calls.append(("documents", len(texts)))
        return [self._vector(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        self.calls.append(("query", text))
        return self._vector(text)

    @staticmethod
    def _vector(text: str) -> list[float]:
        vector = [0.0, 0.0, 0.0]
        for word in text.lower().replace(".", " ").replace("'", " ").split():
            if word in TOPICS:
                vector[TOPICS[word]] += 1.0
        return vector


def make_chunk(text: str, page: int, file: str = "guide.pdf") -> Chunk:
    return Chunk(text=text, source=Source(file=file, page=page), index=0)


CAT = make_chunk("Le chat dort sur le canapé.", page=1)
TAX = make_chunk("La taxe est due en avril.", page=2)
PLANE = make_chunk("L'avion décolle à midi.", page=3)


@pytest.fixture
def embedder() -> TopicEmbedder:
    return TopicEmbedder()


@pytest.fixture
def retriever(embedder: TopicEmbedder) -> Retriever:
    return Retriever(embedder=embedder, store=InMemoryVectorStore(), batch_size=16)


def test_a_question_finds_the_chunk_with_the_closest_meaning(retriever: Retriever):
    retriever.index([CAT, TAX, PLANE])

    results = retriever.search("Mon chaton est malade", k=1)

    assert [r.chunk for r in results] == [CAT]


def test_results_keep_their_source_so_that_they_can_be_cited(retriever: Retriever):
    # La taxe est volontairement en première position : un décalage ou une inversion se verrait.
    retriever.index([TAX, CAT, PLANE])

    best = retriever.search("Quel impôt dois-je payer ?", k=1)[0]

    assert best.chunk.id == "guide.pdf#p2-c0"
    assert best.chunk.source.page == 2


def test_results_are_sorted_from_the_closest_to_the_farthest(retriever: Retriever):
    mixed = make_chunk("Le chat prend l'avion pour un vol vers la taxe.", page=4)  # un peu de chaque thème
    retriever.index([PLANE, mixed, CAT])

    scores = [r.score for r in retriever.search("chat chaton", k=3)]

    assert scores == sorted(scores, reverse=True)
    assert len(scores) == 3


def test_indexing_sends_the_chunk_texts_in_batches_then_a_question_makes_one_more_call(embedder: TopicEmbedder):
    retriever = Retriever(embedder=embedder, store=InMemoryVectorStore(), batch_size=2)
    chunks = [make_chunk("Le chat dort.", page=n) for n in range(1, 6)]  # 5 chunks

    retriever.index(chunks)
    retriever.search("chat", k=1)

    assert embedder.calls == [("documents", 2), ("documents", 2), ("documents", 1), ("query", "chat")]


def test_indexing_nothing_makes_no_call(retriever: Retriever, embedder: TopicEmbedder):
    retriever.index([])

    assert embedder.calls == []


def test_searching_an_empty_index_returns_no_result(retriever: Retriever):
    assert retriever.search("chat", k=3) == []


def test_indexing_twice_adds_to_the_index(retriever: Retriever):
    retriever.index([CAT])
    retriever.index([TAX])

    assert len(retriever.search("chat taxe", k=10)) == 2


def test_progress_of_the_indexing_is_reported(retriever: Retriever):
    progress: list[tuple[int, int]] = []

    retriever.index([CAT, TAX, PLANE], on_progress=lambda done, total: progress.append((done, total)))

    assert progress == [(3, 3)]  # un seul lot de 3 (taille de lot : 16)


def test_k_must_be_at_least_1(retriever: Retriever):
    retriever.index([CAT])

    with pytest.raises(ValueError):
        retriever.search("chat", k=0)


def test_the_batch_size_is_checked_at_creation(embedder: TopicEmbedder):
    with pytest.raises(ValueError):
        Retriever(embedder=embedder, store=InMemoryVectorStore(), batch_size=0)
