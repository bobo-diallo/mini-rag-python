"""Métriques de recherche : le rang de la bonne page, hit@k et MRR, plus le score qu'un classement au hasard obtiendrait."""

from collections.abc import Sequence

from mini_rag.domain.models import SearchResult


def rank_of_page(results: Sequence[SearchResult], expected_page: int) -> int | None:
    """Position (à partir de 1) du premier résultat qui vient de la page attendue, ou None s'il est absent."""
    for position, result in enumerate(results, start=1):
        if result.chunk.source.page == expected_page:
            return position
    return None


def hit_rate(ranks: Sequence[int | None], k: int) -> float:
    """hit@k : part des questions dont la bonne page figure dans les `k` premiers résultats."""
    _require_questions(ranks)
    return sum(1 for rank in ranks if rank is not None and rank <= k) / len(ranks)


def mean_reciprocal_rank(ranks: Sequence[int | None]) -> float:
    """MRR : moyenne de 1/rang. Bonne page en 1er = 1, en 2e = 0,5, en 4e = 0,25 ; absente = 0."""
    _require_questions(ranks)
    return sum(1 / rank for rank in ranks if rank is not None) / len(ranks)


def random_hit_rate(page_count: int, k: int) -> float:
    """hit@k qu'on obtiendrait en classant les pages au hasard : la référence à battre."""
    return min(k, page_count) / page_count


def random_mrr(page_count: int) -> float:
    """MRR qu'on obtiendrait au hasard : la bonne page est en moyenne à n'importe quel rang de 1 à n."""
    return sum(1 / rank for rank in range(1, page_count + 1)) / page_count


def _require_questions(ranks: Sequence[int | None]) -> None:
    if not ranks:
        raise ValueError("Impossible de calculer une métrique sans aucune question.")
