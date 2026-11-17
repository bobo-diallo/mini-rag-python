"""Tests de resolve_citations : la source d'une citation vient du code, jamais du modèle."""

import pytest

from mini_rag.domain.models import Chunk, SearchResult, Source
from mini_rag.generation.citations import resolve_citations


def source(page: int) -> SearchResult:
    chunk = Chunk(text=f"extrait de la page {page}", source=Source(file="guide.pdf", page=page), index=0)
    return SearchResult(chunk=chunk, score=0.9)


# Trois extraits fournis au modèle : « [1] » désigne le premier, « [3] » le dernier.
SOURCES = [source(10), source(20), source(30)]


def test_a_citation_points_to_the_extract_with_that_number():
    resolved = resolve_citations("Le prélèvement a lieu le cinq [2].", SOURCES)

    assert resolved.cited == (SOURCES[1],)
    assert resolved.invalid == ()


def test_sources_are_listed_in_the_order_they_are_first_cited():
    resolved = resolve_citations("D'abord [3], puis [1].", SOURCES)

    assert resolved.cited == (SOURCES[2], SOURCES[0])


def test_a_source_cited_several_times_appears_once():
    resolved = resolve_citations("Un fait [1] et un autre fait [1], plus un troisième [2] [1].", SOURCES)

    assert resolved.cited == (SOURCES[0], SOURCES[1])


@pytest.mark.parametrize("group", ["[1, 2]", "[1,2]", "[1 ; 2]", "[1;2]"])
def test_several_numbers_in_the_same_brackets_are_all_read(group: str):
    resolved = resolve_citations(f"Deux sources concordantes {group}.", SOURCES)

    assert resolved.cited == (SOURCES[0], SOURCES[1])


def test_a_number_without_an_extract_is_reported_as_invalid():
    resolved = resolve_citations("Selon l'extrait [7], c'est vrai.", SOURCES)

    assert resolved.cited == ()
    assert resolved.invalid == (7,)


def test_zero_is_invalid_and_never_means_the_last_extract():
    # Piège Python : SOURCES[0 - 1] vaudrait SOURCES[-1], le DERNIER élément. Les extraits commencent à 1.
    resolved = resolve_citations("Voir [0].", SOURCES)

    assert resolved.cited == ()
    assert resolved.invalid == (0,)


def test_an_invalid_number_is_reported_once_even_if_repeated():
    resolved = resolve_citations("[9] puis encore [9] et [1].", SOURCES)

    assert resolved.invalid == (9,)
    assert resolved.cited == (SOURCES[0],)


def test_valid_and_invalid_numbers_in_the_same_group_are_sorted_out():
    resolved = resolve_citations("Selon [2, 8].", SOURCES)

    assert resolved.cited == (SOURCES[1],)
    assert resolved.invalid == (8,)


def test_an_answer_without_citation_gives_nothing():
    resolved = resolve_citations("Une réponse sans aucune référence.", SOURCES)

    assert resolved.cited == ()
    assert resolved.invalid == ()


@pytest.mark.parametrize("text", ["Voir [note].", "Voir [a, b].", "Voir [1.", "Voir 1].", "Voir [].", "Voir [1 2]."])
def test_brackets_that_are_not_citations_are_ignored(text: str):
    resolved = resolve_citations(text, SOURCES)

    assert resolved.cited == ()
    assert resolved.invalid == ()


def test_there_is_nothing_to_resolve_without_sources():
    resolved = resolve_citations("Voir [1].", [])

    assert resolved.cited == ()
    assert resolved.invalid == (1,)
