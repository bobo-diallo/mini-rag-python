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


# Texte sans espaces ni répétition : chaque bloc de 4 chiffres est unique,
# donc un décalage d'un seul caractère dans un chunk serait détecté.
TEXTE_LONG = "".join(f"{i:04d}" for i in range(625))  # 2500 caractères


def test_un_texte_long_est_decoupe_avec_chevauchement():
    chunks = chunk_pages([page(TEXTE_LONG)])

    # pas = taille - chevauchement = 800 : débuts aux positions 0, 800 et 1600
    assert [c.text for c in chunks] == [
        TEXTE_LONG[0:1000],
        TEXTE_LONG[800:1800],
        TEXTE_LONG[1600:2500],
    ]


def test_aucun_chunk_ne_depasse_la_taille():
    chunks = chunk_pages([page(TEXTE_LONG)])

    assert all(len(c.text) <= 1000 for c in chunks)


def test_la_fin_d_un_chunk_est_repetee_au_debut_du_suivant():
    chunks = chunk_pages([page(TEXTE_LONG)])

    assert chunks[0].text[-200:] == chunks[1].text[:200]


def test_pas_de_chunk_inutile_quand_le_texte_tombe_pile():
    # taille 10, chevauchement 3, texte de 17 caractères : [0:10] puis [7:17], et on s'arrête
    texte = "0123456789ABCDEFG"

    chunks = chunk_pages([page(texte)], ChunkOptions(size=10, overlap=3))

    assert [c.text for c in chunks] == ["0123456789", "789ABCDEFG"]


def test_les_ids_d_une_meme_page_sont_numerotes_dans_l_ordre():
    chunks = chunk_pages([page(TEXTE_LONG, number=4)])

    assert [c.id for c in chunks] == ["doc.pdf#p4-c0", "doc.pdf#p4-c1", "doc.pdf#p4-c2"]
