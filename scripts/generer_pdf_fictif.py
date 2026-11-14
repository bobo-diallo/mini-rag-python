"""Fabrique un PDF fictif de plusieurs pages, sans aucune dépendance (PDF écrit à la main).

Usage : python scripts/generer_pdf_fictif.py tests/fixtures/rapport-fictif.pdf

Le texte est tiré d'un petit vocabulaire avec une graine fixe : le résultat est toujours le même,
et ne contient aucune donnée réelle. Sert à comparer le découpage Python et TypeScript.
"""

import random
import sys
import textwrap
from pathlib import Path

VOCABULAIRE = (
    "le la les un une des de du et ou mais donc car dans sur sous avec sans pour par "
    "projet rapport budget equipe client service module version etape objectif risque "
    "analyse mesure resultat calendrier livraison qualite document decision reunion "
    "ordinateur reseau donnees fichier dossier utilisateur systeme application serveur"
).split()

PAGES = 6
LIGNES_PAR_PAGE = 48
LARGEUR_LIGNE = 90  # caractères par ligne


def generer_paragraphes(graine: int = 42) -> list[str]:
    hasard = random.Random(graine)
    paragraphes = []
    for _ in range(40):
        mots = [hasard.choice(VOCABULAIRE) for _ in range(hasard.randint(40, 160))]
        paragraphes.append(" ".join(mots).capitalize() + ".")
    return paragraphes


def mettre_en_pages(paragraphes: list[str]) -> list[list[str]]:
    """Découpe les paragraphes en lignes, puis en pages. Une ligne vide sépare deux paragraphes."""
    lignes: list[str] = []
    for paragraphe in paragraphes:
        lignes += textwrap.wrap(paragraphe, LARGEUR_LIGNE) + [""]
    pages = [lignes[i : i + LIGNES_PAR_PAGE] for i in range(0, len(lignes), LIGNES_PAR_PAGE)]
    return pages[:PAGES]


def flux_de_page(lignes: list[str]) -> bytes:
    """Les instructions PDF d'une page : police Helvetica 11, une ligne après l'autre."""
    instructions = ["BT", "/F1 11 Tf", "14 TL", "50 800 Td"]
    for ligne in lignes:
        instructions.append(f"({ligne}) Tj" if ligne else "")
        instructions.append("T*")  # passe à la ligne suivante
    instructions.append("ET")
    return "\n".join(i for i in instructions if i).encode("latin-1")


def ecrire_pdf(pages: list[list[str]]) -> bytes:
    """Assemble les objets PDF et la table des positions (xref) qui permet de les retrouver."""
    n = len(pages)
    # Numéros d'objets : 1 = catalogue, 2 = liste des pages, 3 = police,
    # puis pour chaque page : un objet page et un objet contenu.
    objets: dict[int, bytes] = {
        1: b"<< /Type /Catalog /Pages 2 0 R >>",
        3: b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    }
    numeros_pages = []
    for i, lignes in enumerate(pages):
        numero_page, numero_contenu = 4 + 2 * i, 5 + 2 * i
        numeros_pages.append(numero_page)
        flux = flux_de_page(lignes)
        objets[numero_page] = (
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
            f"/Resources << /Font << /F1 3 0 R >> >> /Contents {numero_contenu} 0 R >>"
        ).encode()
        objets[numero_contenu] = f"<< /Length {len(flux)} >>\nstream\n".encode() + flux + b"\nendstream"
    kids = " ".join(f"{numero} 0 R" for numero in numeros_pages)
    objets[2] = f"<< /Type /Pages /Kids [{kids}] /Count {n} >>".encode()

    sortie = bytearray(b"%PDF-1.4\n")
    positions = {}
    for numero in sorted(objets):
        positions[numero] = len(sortie)
        sortie += f"{numero} 0 obj\n".encode() + objets[numero] + b"\nendobj\n"

    debut_xref = len(sortie)
    total = len(objets) + 1
    sortie += f"xref\n0 {total}\n".encode() + b"0000000000 65535 f \n"
    for numero in sorted(objets):
        sortie += f"{positions[numero]:010d} 00000 n \n".encode()
    sortie += f"trailer\n<< /Size {total} /Root 1 0 R >>\nstartxref\n{debut_xref}\n%%EOF\n".encode()
    return bytes(sortie)


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage : python scripts/generer_pdf_fictif.py <fichier.pdf>", file=sys.stderr)
        return 1
    pages = mettre_en_pages(generer_paragraphes())
    destination = Path(sys.argv[1])
    destination.write_bytes(ecrire_pdf(pages))
    print(f"{destination} : {len(pages)} pages")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
