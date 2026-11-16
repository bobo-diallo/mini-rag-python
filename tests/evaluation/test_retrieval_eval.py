"""Test de evaluate_retrieval : poser chaque question au Retriever et noter le rang de la bonne page."""

import re
from collections.abc import Sequence

from mini_rag.domain.models import Chunk, Source
from mini_rag.evaluation.questions import EvalQuestion
from mini_rag.evaluation.retrieval_eval import evaluate_retrieval
from mini_rag.retrieval.embedder import Embedder
from mini_rag.retrieval.retriever import Retriever
from mini_rag.retrieval.vector_store import InMemoryVectorStore

VOCABULARY = ("alpha", "beta", "gamma")


class WordEmbedder(Embedder):
    """Faux embedder : le vecteur d'un texte compte les occurrences de alpha, beta et gamma."""

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        return [self.embed_query(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        words = re.findall(r"\w+", text.lower())
        return [float(words.count(word)) for word in VOCABULARY]


def page_chunk(text: str, page: int) -> Chunk:
    return Chunk(text=text, source=Source(file="g.pdf", page=page), index=0)


def indexed_retriever() -> Retriever:
    retriever = Retriever(embedder=WordEmbedder(), store=InMemoryVectorStore(), batch_size=8)
    retriever.index([page_chunk("alpha", 1), page_chunk("beta", 2), page_chunk("gamma", 3)])
    return retriever


def test_each_question_gets_the_rank_of_its_expected_page():
    questions = [EvalQuestion("alpha ?", expected_page=1), EvalQuestion("beta ?", expected_page=2)]

    outcomes = evaluate_retrieval(indexed_retriever(), questions, k=3)

    assert [o.rank for o in outcomes] == [1, 1]


def test_a_question_whose_page_comes_later_gets_a_later_rank():
    # « beta » classe la page 2 en tête ; la page 1 est à égalité avec la 3 (score 0) : l'ordre d'indexation tranche.
    outcomes = evaluate_retrieval(indexed_retriever(), [EvalQuestion("beta ?", expected_page=3)], k=3)

    assert outcomes[0].rank == 3


def test_a_page_outside_the_first_k_has_no_rank():
    outcomes = evaluate_retrieval(indexed_retriever(), [EvalQuestion("beta ?", expected_page=3)], k=2)

    assert outcomes[0].rank is None


def test_the_outcome_keeps_the_question_and_the_pages_found_in_order():
    outcomes = evaluate_retrieval(indexed_retriever(), [EvalQuestion("gamma ?", expected_page=3)], k=3)

    outcome = outcomes[0]
    assert outcome.question == EvalQuestion("gamma ?", expected_page=3)
    assert [r.chunk.source.page for r in outcome.top] == [3, 1, 2]
