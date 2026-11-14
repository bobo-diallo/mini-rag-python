"""Commande `mini-rag-chunks` : pour chaque PDF d'un dossier, combien de pages et de chunks.

Sert à mesurer le découpage et à le comparer avec la version TypeScript.
"""

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from mini_rag.ingestion.chunker import ChunkOptions, chunk_pages
from mini_rag.ingestion.pdf_loader import PdfLoader

DEFAULT_DIRECTORY = "data/public"


def main(argv: Sequence[str] | None = None) -> int:
    """Point d'entrée. Rend 0 si tout va bien, 1 sinon (code de sortie du programme)."""
    args = _parse_args(argv)
    directory = Path(args.directory)

    if not directory.is_dir():
        print(f"Dossier introuvable : {directory}", file=sys.stderr)
        return 1

    files = sorted(p for p in directory.iterdir() if p.suffix.lower() == ".pdf")
    if not files:
        print(f"Aucun PDF dans {directory}.", file=sys.stderr)
        return 1

    options = ChunkOptions()
    print(
        f"Dossier : {directory} — taille {options.size}, chevauchement {options.overlap} (caractères)\n"
    )

    loader = PdfLoader()
    for file in files:
        pages = loader.load(file)
        chunks = chunk_pages(pages, options)

        print(f"■ {file.name}")
        print(f"  pages : {len(pages)}")
        if chunks:
            sizes = [len(c.text) for c in chunks]
            average = round(sum(sizes) / len(sizes))
            print(f"  chunks : {len(chunks)} — taille moyenne {average}, min {min(sizes)}, max {max(sizes)}")
        else:
            print("  chunks : 0")

        for chunk in chunks[: args.samples]:
            extract = " ".join(chunk.text.split())[:160]  # espaces et retours à la ligne réduits à un espace
            print(f"  [{chunk.id}] {extract}…")
        print()
    return 0


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="mini-rag-chunks",
        description="Compte les pages et les chunks de chaque PDF d'un dossier.",
    )
    parser.add_argument("directory", nargs="?", default=DEFAULT_DIRECTORY, help="dossier de PDF")
    parser.add_argument("--samples", type=int, default=2, help="nombre d'extraits à afficher par PDF")
    return parser.parse_args(argv)


if __name__ == "__main__":
    raise SystemExit(main())
