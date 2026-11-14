"""Tests de la commande de comptage : pour chaque PDF d'un dossier, pages et chunks."""

import shutil
from pathlib import Path

import pytest
from pypdf import PdfWriter

from mini_rag.cli import main

FIXTURE = Path(__file__).parent / "fixtures" / "deux-pages.pdf"


@pytest.fixture
def dossier_avec_pdf(tmp_path: Path) -> Path:
    """Un dossier contenant un PDF (copie de la fixture) et un fichier qui n'est pas un PDF."""
    shutil.copy(FIXTURE, tmp_path / "b-deux-pages.pdf")
    shutil.copy(FIXTURE, tmp_path / "a-deux-pages.PDF")  # extension en majuscules : acceptée
    (tmp_path / "notes.txt").write_text("pas un pdf")
    return tmp_path


def test_affiche_pages_et_chunks_de_chaque_pdf(dossier_avec_pdf: Path, capsys):
    code = main([str(dossier_avec_pdf)])

    sortie = capsys.readouterr().out
    assert code == 0
    assert "pages : 2" in sortie
    assert "chunks : 2" in sortie  # une phrase courte par page : un chunk par page


def test_les_pdf_sont_listes_par_ordre_alphabetique_et_les_autres_fichiers_ignores(
    dossier_avec_pdf: Path, capsys
):
    main([str(dossier_avec_pdf)])

    sortie = capsys.readouterr().out
    assert sortie.index("a-deux-pages.PDF") < sortie.index("b-deux-pages.pdf")
    assert "notes.txt" not in sortie


def test_rappelle_les_reglages_du_decoupage(dossier_avec_pdf: Path, capsys):
    main([str(dossier_avec_pdf)])

    assert "taille 1000, chevauchement 200" in capsys.readouterr().out


def test_dossier_sans_pdf_echoue_avec_un_message_sur_la_sortie_d_erreur(tmp_path: Path, capsys):
    code = main([str(tmp_path)])

    capture = capsys.readouterr()
    assert code == 1
    assert "Aucun PDF" in capture.err
    assert capture.out == ""


def test_dossier_inexistant_echoue_clairement(tmp_path: Path, capsys):
    code = main([str(tmp_path / "absent")])

    assert code == 1
    assert "absent" in capsys.readouterr().err


def test_un_pdf_sans_aucun_texte_donne_zero_chunk_sans_planter(tmp_path: Path, capsys):
    ecrivain = PdfWriter()
    ecrivain.add_blank_page(width=200, height=200)
    with (tmp_path / "vide.pdf").open("wb") as fichier:
        ecrivain.write(fichier)

    code = main([str(tmp_path)])

    sortie = capsys.readouterr().out
    assert code == 0
    assert "pages : 0" in sortie
    assert "chunks : 0" in sortie
