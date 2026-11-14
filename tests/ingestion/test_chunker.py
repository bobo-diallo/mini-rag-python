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


# --- Coupures naturelles : paragraphes, lignes, mots -------------------------------------------


def test_on_coupe_au_saut_de_paragraphe_plutot_qu_au_milieu_d_un_mot():
    paragraphe_1 = " ".join(["alpha"] * 100)  # 599 caractères
    paragraphe_2 = " ".join(["beta"] * 120)  # 599 caractères
    texte = paragraphe_1 + "\n\n" + paragraphe_2  # 1200 caractères : trop long pour un seul chunk

    chunks = chunk_pages([page(texte)])

    assert [c.text for c in chunks] == [paragraphe_1, paragraphe_2]


def test_un_mot_n_est_jamais_coupe_quand_une_coupure_a_l_espace_est_possible():
    mots = [f"mot{i:03d}" for i in range(200)]  # 200 mots de 6 caractères
    texte = " ".join(mots)

    chunks = chunk_pages([page(texte)], ChunkOptions(size=100, overlap=20))

    assert len(chunks) > 1
    assert all(len(c.text) <= 100 for c in chunks)
    for chunk in chunks:
        assert set(chunk.text.split()) <= set(mots)  # chaque morceau est un mot entier


def test_un_chunk_ne_commence_ni_ne_finit_par_un_blanc():
    texte = " ".join(f"mot{i:03d}" for i in range(200))

    chunks = chunk_pages([page(texte)], ChunkOptions(size=100, overlap=20))

    assert all(c.text == c.text.strip() for c in chunks)


# --- Référence : LangChain (utilisé par la version TypeScript) ---------------------------------
# On ne remplace pas notre code par la bibliothèque : on vérifie qu'on obtient les mêmes extraits.

from langchain_text_splitters import RecursiveCharacterTextSplitter  # noqa: E402


def _phrases(nombre_de_mots: int, prefixe: str) -> str:
    return " ".join(f"{prefixe}{i}" for i in range(nombre_de_mots))


TEXTES_DE_REFERENCE = {
    "court": "Un texte court.",
    "sans_separateur": TEXTE_LONG,
    "paragraphes": "\n\n".join(_phrases(n, "p") for n in (120, 450, 30, 700, 300)),
    "lignes": "\n".join(_phrases(n, "l") for n in (80, 200, 40, 160, 500)),
    "mots_et_paragraphes": "\n\n".join(
        [_phrases(300, "a"), _phrases(10, "b") + "\n" + _phrases(250, "c"), _phrases(900, "d")]
    ),
    "mot_geant_entre_deux_phrases": "debut du texte " + TEXTE_LONG + " fin du texte",
}


@pytest.mark.parametrize("nom", TEXTES_DE_REFERENCE)
@pytest.mark.parametrize("size,overlap", [(1000, 200), (100, 20), (50, 0), (300, 299)])
def test_memes_extraits_que_langchain(nom: str, size: int, overlap: int):
    texte = TEXTES_DE_REFERENCE[nom]
    attendu = RecursiveCharacterTextSplitter(chunk_size=size, chunk_overlap=overlap).split_text(texte)

    obtenu = [c.text for c in chunk_pages([page(texte)], ChunkOptions(size=size, overlap=overlap))]

    assert obtenu == attendu
