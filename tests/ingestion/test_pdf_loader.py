"""Tests du lecteur de PDF : une entrée par page non vide, numérotée à partir de 1."""

from pathlib import Path

import pytest
from pypdf import PdfReader, PdfWriter

from mini_rag.ingestion.pdf_loader import PdfLoader

FIXTURE = Path(__file__).parent.parent / "fixtures" / "deux-pages.pdf"


def test_rend_une_entree_par_page_numerotee_a_partir_de_1():
    pages = PdfLoader().load(FIXTURE)

    assert [p.source.page for p in pages] == [1, 2]


def test_la_source_indique_le_nom_du_fichier_pas_le_chemin_complet():
    pages = PdfLoader().load(FIXTURE)

    assert all(p.source.file == "deux-pages.pdf" for p in pages)


def test_extrait_le_texte_de_chaque_page():
    pages = PdfLoader().load(FIXTURE)

    assert "Premiere page fictive" in pages[0].text
    assert "Deuxieme page fictive" in pages[1].text


def test_accepte_un_chemin_sous_forme_de_texte():
    pages = PdfLoader().load(str(FIXTURE))

    assert len(pages) == 2


def test_echoue_clairement_si_le_fichier_n_existe_pas(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        PdfLoader().load(tmp_path / "absent.pdf")


def test_ignore_les_pages_sans_texte_mais_garde_la_vraie_numerotation(tmp_path: Path):
    # On fabrique un PDF de 3 pages : une page de texte, une page blanche, une page de texte.
    modele = PdfReader(FIXTURE)
    ecrivain = PdfWriter()
    ecrivain.add_page(modele.pages[0])
    ecrivain.add_blank_page(width=200, height=200)
    ecrivain.add_page(modele.pages[1])
    chemin = tmp_path / "avec-page-blanche.pdf"
    with chemin.open("wb") as fichier:
        ecrivain.write(fichier)

    pages = PdfLoader().load(chemin)

    # La page blanche (n° 2) disparaît, mais la dernière page reste la n° 3 : la citation reste exacte.
    assert [p.source.page for p in pages] == [1, 3]
