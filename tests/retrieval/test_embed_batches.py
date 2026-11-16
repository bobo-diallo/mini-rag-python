"""Tests du calcul des embeddings par lots : quelques textes à la fois, pas des centaines."""

import pytest

from mini_rag.retrieval.embedder import embed_in_batches

TEXTS = ["a", "bb", "ccc", "dddd", "eeeee"]  # longueurs 1 à 5


def test_vectors_come_back_in_the_order_of_the_texts(fake_embedder):
    vectors = embed_in_batches(fake_embedder, TEXTS, batch_size=2)

    # Le faux embedder rend [longueur, 1.0] : l'ordre des longueurs prouve l'ordre des textes.
    assert vectors == [[1.0, 1.0], [2.0, 1.0], [3.0, 1.0], [4.0, 1.0], [5.0, 1.0]]


def test_texts_are_sent_in_batches_of_the_requested_size(fake_embedder):
    embed_in_batches(fake_embedder, TEXTS, batch_size=2)

    assert fake_embedder.calls == [["a", "bb"], ["ccc", "dddd"], ["eeeee"]]


def test_a_batch_larger_than_the_list_makes_a_single_call(fake_embedder):
    embed_in_batches(fake_embedder, TEXTS, batch_size=100)

    assert len(fake_embedder.calls) == 1


def test_no_text_means_no_call_and_no_vector(fake_embedder):
    assert embed_in_batches(fake_embedder, [], batch_size=4) == []
    assert fake_embedder.calls == []


def test_the_batch_size_must_be_at_least_1(fake_embedder):
    with pytest.raises(ValueError):
        embed_in_batches(fake_embedder, TEXTS, batch_size=0)


def test_progress_is_reported_after_each_batch(fake_embedder):
    progress: list[tuple[int, int]] = []

    embed_in_batches(
        fake_embedder, TEXTS, batch_size=2, on_progress=lambda done, total: progress.append((done, total))
    )

    assert progress == [(2, 5), (4, 5), (5, 5)]
