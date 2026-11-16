"""Tests des métriques : où se classe la bonne page, et que valent ces rangs en moyenne ?"""

import pytest

from mini_rag.domain.models import Chunk, SearchResult, Source
from mini_rag.evaluation.metrics import (
    hit_rate,
    mean_reciprocal_rank,
    random_hit_rate,
    random_mrr,
    rank_of_page,
)


def results_on_pages(*pages: int) -> list[SearchResult]:
    """Des résultats de recherche dont les chunks viennent des pages données, dans cet ordre."""
    return [
        SearchResult(chunk=Chunk(text="x", source=Source(file="g.pdf", page=page), index=0), score=1.0)
        for page in pages
    ]


def test_the_rank_is_the_position_of_the_expected_page_starting_at_1():
    assert rank_of_page(results_on_pages(3, 1, 2), expected_page=3) == 1
    assert rank_of_page(results_on_pages(3, 1, 2), expected_page=2) == 3


def test_a_page_missing_from_the_results_has_no_rank():
    assert rank_of_page(results_on_pages(3, 1, 2), expected_page=9) is None


def test_with_several_chunks_from_the_same_page_the_first_one_counts():
    assert rank_of_page(results_on_pages(4, 2, 2), expected_page=2) == 2


def test_hit_rate_is_the_share_of_questions_whose_page_is_in_the_first_k():
    ranks = [1, 3, None, 2]

    assert hit_rate(ranks, k=1) == 0.25
    assert hit_rate(ranks, k=3) == 0.75


def test_hit_rate_needs_at_least_one_question():
    with pytest.raises(ValueError):
        hit_rate([], k=3)


def test_mrr_averages_the_inverse_of_the_ranks_and_counts_a_miss_as_zero():
    # (1/1 + 1/2 + 0 + 1/4) / 4
    assert mean_reciprocal_rank([1, 2, None, 4]) == pytest.approx(0.4375)


def test_mrr_needs_at_least_one_question():
    with pytest.raises(ValueError):
        mean_reciprocal_rank([])


def test_random_baseline_for_hit_rate():
    # Si on classait les pages au hasard : 3 chances sur 10 que la bonne soit dans les 3 premières.
    assert random_hit_rate(page_count=10, k=3) == pytest.approx(0.3)
    assert random_hit_rate(page_count=2, k=3) == 1.0  # on ne peut pas prendre plus de pages qu'il n'y en a


def test_random_baseline_for_mrr():
    assert random_mrr(page_count=1) == 1.0
    assert random_mrr(page_count=10) == pytest.approx(0.2928968, abs=1e-6)  # (1 + 1/2 + ... + 1/10) / 10
