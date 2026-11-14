"""Fabrique un PDF fictif de plusieurs pages, sans aucune dépendance (PDF écrit à la main).

Usage : python scripts/generate_fictional_pdf.py tests/fixtures/fictional-report.pdf

Le texte est tiré d'un petit vocabulaire avec une graine fixe : le résultat est toujours le même,
et ne contient aucune donnée réelle. Sert à comparer le découpage Python et TypeScript.
"""

import random
import sys
import textwrap
from pathlib import Path

VOCABULARY = (
    "le la les un une des de du et ou mais donc car dans sur sous avec sans pour par "
    "projet rapport budget equipe client service module version etape objectif risque "
    "analyse mesure resultat calendrier livraison qualite document decision reunion "
    "ordinateur reseau donnees fichier dossier utilisateur systeme application serveur"
).split()

PAGE_COUNT = 6
LINES_PER_PAGE = 48
LINE_WIDTH = 90  # caractères par ligne


def generate_paragraphs(seed: int = 42) -> list[str]:
    rng = random.Random(seed)
    paragraphs = []
    for _ in range(40):
        words = [rng.choice(VOCABULARY) for _ in range(rng.randint(40, 160))]
        paragraphs.append(" ".join(words).capitalize() + ".")
    return paragraphs


def paginate(paragraphs: list[str]) -> list[list[str]]:
    """Découpe les paragraphes en lignes, puis en pages. Une ligne vide sépare deux paragraphes."""
    lines: list[str] = []
    for paragraph in paragraphs:
        lines += textwrap.wrap(paragraph, LINE_WIDTH) + [""]
    pages = [lines[i : i + LINES_PER_PAGE] for i in range(0, len(lines), LINES_PER_PAGE)]
    return pages[:PAGE_COUNT]


def page_stream(lines: list[str]) -> bytes:
    """Les instructions PDF d'une page : police Helvetica 11, une ligne après l'autre."""
    instructions = ["BT", "/F1 11 Tf", "14 TL", "50 800 Td"]
    for line in lines:
        instructions.append(f"({line}) Tj" if line else "")
        instructions.append("T*")  # passe à la ligne suivante
    instructions.append("ET")
    return "\n".join(i for i in instructions if i).encode("latin-1")


def write_pdf(pages: list[list[str]]) -> bytes:
    """Assemble les objets PDF et la table des positions (xref) qui permet de les retrouver."""
    # Numéros d'objets : 1 = catalogue, 2 = liste des pages, 3 = police,
    # puis pour chaque page : un objet page et un objet contenu.
    objects: dict[int, bytes] = {
        1: b"<< /Type /Catalog /Pages 2 0 R >>",
        3: b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    }
    page_numbers = []
    for i, lines in enumerate(pages):
        page_number, content_number = 4 + 2 * i, 5 + 2 * i
        page_numbers.append(page_number)
        stream = page_stream(lines)
        objects[page_number] = (
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
            f"/Resources << /Font << /F1 3 0 R >> >> /Contents {content_number} 0 R >>"
        ).encode()
        objects[content_number] = f"<< /Length {len(stream)} >>\nstream\n".encode() + stream + b"\nendstream"
    kids = " ".join(f"{number} 0 R" for number in page_numbers)
    objects[2] = f"<< /Type /Pages /Kids [{kids}] /Count {len(pages)} >>".encode()

    output = bytearray(b"%PDF-1.4\n")
    positions = {}
    for number in sorted(objects):
        positions[number] = len(output)
        output += f"{number} 0 obj\n".encode() + objects[number] + b"\nendobj\n"

    xref_start = len(output)
    total = len(objects) + 1
    output += f"xref\n0 {total}\n".encode() + b"0000000000 65535 f \n"
    for number in sorted(objects):
        output += f"{positions[number]:010d} 00000 n \n".encode()
    output += f"trailer\n<< /Size {total} /Root 1 0 R >>\nstartxref\n{xref_start}\n%%EOF\n".encode()
    return bytes(output)


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage : python scripts/generate_fictional_pdf.py <file.pdf>", file=sys.stderr)
        return 1
    pages = paginate(generate_paragraphs())
    destination = Path(sys.argv[1])
    destination.write_bytes(write_pdf(pages))
    print(f"{destination} : {len(pages)} pages")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
