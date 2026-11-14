"""Lecture d'un PDF page par page, avec `pypdf`."""

from pathlib import Path

from pypdf import PdfReader

from mini_rag.domain.models import PageText, Source


class PdfLoader:
    """Lit un PDF : une entrée par page non vide, numérotée à partir de 1."""

    def load(self, path: str | Path) -> list[PageText]:
        path = Path(path)
        reader = PdfReader(path)  # lève FileNotFoundError si le fichier n'existe pas

        pages: list[PageText] = []
        # `start=1` : enumerate compte à partir de 1, comme les numéros de page d'un lecteur PDF.
        for number, page in enumerate(reader.pages, start=1):
            text = page.extract_text()
            if text.strip() == "":
                continue  # page blanche ou image seule : rien à indexer, mais on garde la vraie numérotation
            pages.append(PageText(source=Source(file=path.name, page=number), text=text))
        return pages
