"""Tests des types du domaine : de quoi citer un passage (fichier + page)."""

import dataclasses

import pytest

from mini_rag.domain.models import Chunk, PageText, Source


def test_a_chunk_has_a_stable_id_made_of_file_page_and_index():
    source = Source(file="rapport.pdf", page=2)

    chunk = Chunk(text="Un extrait.", source=source, index=0)

    assert chunk.id == "rapport.pdf#p2-c0"


def test_types_are_immutable():
    source = Source(file="rapport.pdf", page=1)

    with pytest.raises(dataclasses.FrozenInstanceError):
        source.page = 5


def test_page_numbers_start_at_1():
    with pytest.raises(ValueError):
        Source(file="rapport.pdf", page=0)


def test_a_page_keeps_its_source_and_text():
    page = PageText(source=Source(file="a.pdf", page=3), text="Bonjour")

    assert page.source.page == 3
    assert page.text == "Bonjour"
