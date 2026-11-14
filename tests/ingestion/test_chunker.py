"""Tests du découpeur : cas simples (page vide, texte court, réglages invalides)."""

import pytest

from mini_rag.domain.models import PageText, Source
from mini_rag.ingestion.chunker import ChunkOptions, chunk_pages


def page(text: str, number: int = 1, file: str = "doc.pdf") -> PageText:
    return PageText(source=Source(file=file, page=number), text=text)


def test_les_reglages_par_defaut_sont_1000_et_200():
    options = ChunkOptions()

    assert options.size == 1000
    assert options.overlap == 200


def test_un_chevauchement_egal_ou_superieur_a_la_taille_est_refuse():
    with pytest.raises(ValueError):
        ChunkOptions(size=100, overlap=100)


def test_une_page_vide_ou_blanche_ne_donne_aucun_chunk():
    chunks = chunk_pages([page(""), page("   \n  ", number=2)])

    assert chunks == []


def test_un_texte_court_donne_un_seul_chunk_avec_sa_source():
    chunks = chunk_pages([page("Un texte court.", number=3)])

    assert len(chunks) == 1
    assert chunks[0].text == "Un texte court."
    assert chunks[0].id == "doc.pdf#p3-c0"


def test_le_rang_du_chunk_repart_de_zero_a_chaque_page():
    chunks = chunk_pages([page("Page un.", number=1), page("Page deux.", number=2)])

    assert [c.id for c in chunks] == ["doc.pdf#p1-c0", "doc.pdf#p2-c0"]
