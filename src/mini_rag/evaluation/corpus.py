"""Le corpus d'une évaluation : un dossier qui contient exactement un PDF."""

from pathlib import Path


class CorpusError(Exception):
    """Le dossier de corpus n'est pas utilisable ; le message dit pourquoi."""


def find_single_pdf(folder: Path) -> Path:
    """Un seul PDF : sinon « page 3 » ne dirait pas de quel fichier on parle."""
    if not folder.is_dir():
        raise CorpusError(f"Dossier de corpus introuvable : {folder}")
    pdfs = sorted(p for p in folder.iterdir() if p.suffix.lower() == ".pdf")
    if not pdfs:
        raise CorpusError(f"Aucun PDF dans {folder}.")
    if len(pdfs) > 1:
        raise CorpusError(
            f"Le corpus doit contenir un seul PDF (les numéros de page seraient ambigus), il y en a {len(pdfs)} dans {folder}."
        )
    return pdfs[0]
