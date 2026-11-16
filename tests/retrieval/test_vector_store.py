"""Tests de l'index vectoriel en mémoire : ranger des chunks avec leur vecteur, retrouver les plus proches."""

import pytest

from mini_rag.domain.models import Chunk, Source
from mini_rag.retrieval.vector_store import InMemoryVectorStore


def chunk(text: str, page: int = 1) -> Chunk:
    return Chunk(text=text, source=Source(file="doc.pdf", page=page), index=0)


@pytest.fixture
def store() -> InMemoryVectorStore:
    """Trois chunks dans un espace à 2 dimensions : un « nord », un « est » et un « nord-est »."""
    store = InMemoryVectorStore()
    store.add(
        [chunk("nord", page=1), chunk("est", page=2), chunk("nord-est", page=3)],
        [[0.0, 1.0], [1.0, 0.0], [1.0, 1.0]],
    )
    return store


def test_results_are_sorted_from_the_closest_to_the_farthest(store: InMemoryVectorStore):
    results = store.search([0.1, 1.0], k=3)  # presque plein nord

    assert [r.chunk.text for r in results] == ["nord", "nord-est", "est"]
    assert results[0].score > results[1].score > results[2].score


def test_k_limits_the_number_of_results(store: InMemoryVectorStore):
    results = store.search([0.0, 1.0], k=2)

    assert len(results) == 2


def test_k_larger_than_the_store_returns_everything(store: InMemoryVectorStore):
    assert len(store.search([0.0, 1.0], k=50)) == 3


def test_an_empty_store_returns_no_result():
    assert InMemoryVectorStore().search([1.0, 0.0], k=3) == []


def test_the_score_is_the_cosine_similarity(store: InMemoryVectorStore):
    results = store.search([0.0, 1.0], k=3)

    assert results[0].score == pytest.approx(1.0)  # « nord » : même direction
    assert results[2].score == pytest.approx(0.0)  # « est » : perpendiculaire


def test_equal_scores_keep_insertion_order():
    store = InMemoryVectorStore()
    store.add([chunk("premier"), chunk("second")], [[1.0, 0.0], [1.0, 0.0]])

    results = store.search([1.0, 0.0], k=2)

    assert [r.chunk.text for r in results] == ["premier", "second"]


def test_k_must_be_at_least_1(store: InMemoryVectorStore):
    with pytest.raises(ValueError):
        store.search([0.0, 1.0], k=0)


def test_chunks_and_vectors_must_be_the_same_number():
    with pytest.raises(ValueError):
        InMemoryVectorStore().add([chunk("a"), chunk("b")], [[1.0, 0.0]])


def test_all_vectors_must_have_the_same_dimension(store: InMemoryVectorStore):
    with pytest.raises(ValueError, match="3"):
        store.add([chunk("intrus")], [[1.0, 0.0, 0.0]])


def test_the_query_must_have_the_dimension_of_the_stored_vectors(store: InMemoryVectorStore):
    with pytest.raises(ValueError, match="3"):
        store.search([1.0, 0.0, 0.0], k=1)


def test_the_store_reports_its_size(store: InMemoryVectorStore):
    assert len(store) == 3


def test_vectors_added_together_to_an_empty_store_must_also_share_a_dimension():
    with pytest.raises(ValueError):
        InMemoryVectorStore().add([chunk("a"), chunk("b")], [[1.0, 0.0], [1.0, 0.0, 0.0]])
