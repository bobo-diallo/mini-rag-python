"""Évaluer la recherche : poser chaque question au Retriever et noter où se classe la bonne page."""

from collections.abc import Sequence
from dataclasses import dataclass

from mini_rag.domain.models import SearchResult
from mini_rag.evaluation.metrics import rank_of_page
from mini_rag.evaluation.questions import EvalQuestion
from mini_rag.retrieval.retriever import Retriever


@dataclass(frozen=True)
class QuestionOutcome:
    """Ce qui s'est passé pour une question : le rang de la bonne page, et ce que la recherche a rendu."""

    question: EvalQuestion
    rank: int | None  # None : la bonne page n'est pas dans les k premiers résultats
    top: tuple[SearchResult, ...]


def evaluate_retrieval(
    retriever: Retriever, questions: Sequence[EvalQuestion], k: int
) -> list[QuestionOutcome]:
    """Pour chaque question, garde les `k` meilleurs résultats et cherche la page attendue parmi eux."""
    outcomes = []
    for question in questions:
        results = retriever.search(question.question, k)
        outcomes.append(
            QuestionOutcome(
                question=question,
                rank=rank_of_page(results, question.expected_page),
                top=tuple(results),
            )
        )
    return outcomes
