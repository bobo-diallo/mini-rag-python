"""Tests des types du domaine : de quoi citer un passage (fichier + page)."""

import dataclasses

import pytest

from mini_rag.domain.models import Chunk, PageText, Source


def test_un_chunk_a_un_identifiant_stable_fichier_page_numero():
    source = Source(file="rapport.pdf", page=2)

    chunk = Chunk(text="Un extrait.", source=source, index=0)

    assert chunk.id == "rapport.pdf#p2-c0"


def test_les_types_sont_non_modifiables():
    source = Source(file="rapport.pdf", page=1)

    with pytest.raises(dataclasses.FrozenInstanceError):
        source.page = 5


def test_une_page_commence_a_1():
    with pytest.raises(ValueError):
        Source(file="rapport.pdf", page=0)


def test_une_page_garde_sa_source_et_son_texte():
    page = PageText(source=Source(file="a.pdf", page=3), text="Bonjour")

    assert page.source.page == 3
    assert page.text == "Bonjour"
