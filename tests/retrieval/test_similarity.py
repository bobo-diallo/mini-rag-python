"""Tests de la similarité cosinus : l'angle entre deux vecteurs, pas leur longueur."""

import pytest

from mini_rag.retrieval.similarity import cosine_similarity


def test_identical_vectors_have_a_similarity_of_1():
    assert cosine_similarity([1.0, 2.0, 3.0], [1.0, 2.0, 3.0]) == pytest.approx(1.0)


def test_length_does_not_matter_only_direction():
    # [2, 4, 6] est [1, 2, 3] multiplié par 2 : même direction, donc même sens.
    assert cosine_similarity([1.0, 2.0, 3.0], [2.0, 4.0, 6.0]) == pytest.approx(1.0)


def test_perpendicular_vectors_have_a_similarity_of_0():
    assert cosine_similarity([1.0, 0.0], [0.0, 1.0]) == pytest.approx(0.0)


def test_opposite_vectors_have_a_similarity_of_minus_1():
    assert cosine_similarity([1.0, 2.0], [-1.0, -2.0]) == pytest.approx(-1.0)


def test_a_known_value():
    # cos(45°) = √2 / 2 : [1, 0] et [1, 1] forment un angle de 45 degrés.
    assert cosine_similarity([1.0, 0.0], [1.0, 1.0]) == pytest.approx(0.7071067811865476)


def test_different_dimensions_are_rejected():
    with pytest.raises(ValueError, match="2.*3"):
        cosine_similarity([1.0, 2.0], [1.0, 2.0, 3.0])


def test_a_zero_vector_is_rejected_because_its_direction_is_undefined():
    with pytest.raises(ValueError):
        cosine_similarity([0.0, 0.0], [1.0, 2.0])
