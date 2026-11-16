"""Commande `mini-rag-ask` : poser une question à des PDF et lire la réponse avec ses sources vérifiées."""

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from mini_rag.composition import build_answerer
from mini_rag.config import Settings
from mini_rag.generation.answerer import Reply
from mini_rag.generation.chat_model import ChatModel, GenerationError
from mini_rag.ingestion.chunker import chunk_pages
from mini_rag.ingestion.pdf_loader import PdfLoader
from mini_rag.retrieval.embedder import Embedder, EmbeddingError

DEFAULT_CORPUS = "eval/corpus"  # le guide fictif du projet ; `--corpus` pour viser un autre dossier


def main(
    argv: Sequence[str] | None = None,
    *,
    embedder: Embedder | None = None,
    chat_model: ChatModel | None = None,
    settings: Settings | None = None,
) -> int:
    """Rend 0 si la question a reçu une réponse ou un refus honnête, 1 en cas d'erreur."""
    args = _parse_args(argv)
    question = args.question.strip()
    if not question:
        return _fail("La question est vide.")

    folder = Path(args.corpus)
    if not folder.is_dir():
        return _fail(f"Dossier de corpus introuvable : {folder}")
    pdfs = sorted(p for p in folder.iterdir() if p.suffix.lower() == ".pdf")
    if not pdfs:
        return _fail(f"Aucun PDF dans {folder}.")

    settings = settings or Settings()
    loader = PdfLoader()
    chunks = chunk_pages([page for pdf in pdfs for page in loader.load(pdf)])

    try:
        answerer = build_answerer(chunks, settings, embedder=embedder, chat_model=chat_model)
        reply = answerer.answer(question)
    except (EmbeddingError, GenerationError) as error:
        return _fail(str(error))

    _print_reply(question, reply, settings, args.verbose)
    return 0


def _print_reply(question: str, reply: Reply, settings: Settings, verbose: bool) -> None:
    print(f"Question : {question}\n")
    print(f"Réponse :\n{reply.text}\n")

    if reply.answered:
        if reply.citations:
            print("Sources vérifiées :")
            for source in reply.citations:
                print(f"  - {source.chunk.source.file}, page {source.chunk.source.page} (score {source.score:.2f})")
        elif not reply.invalid_citations:
            print("⚠ Aucune citation vérifiable : cette réponse n'est appuyée par aucune source.")
        if reply.invalid_citations:
            numbers = ", ".join(f"[{n}]" for n in reply.invalid_citations)
            print(f"⚠ Le modèle a cité des extraits qui n'existent pas : {numbers}. Ces références sont à ignorer.")
    else:
        reason = "Aucun appel au modèle" if reply.used_extracts == 0 else "le modèle a répondu qu'il ne sait pas"
        best = f"meilleur extrait : page {reply.retrieved[0].chunk.source.page}, score {reply.retrieved[0].score:.2f}, " if reply.retrieved else ""
        print(f"({reason} ; {best}seuil : {settings.min_score:.2f})")

    if reply.tokens:
        print(f"Tokens : {reply.tokens.prompt} lus + {reply.tokens.generated} écrits = {reply.tokens.total}")

    if verbose:
        print(f"\nExtraits retrouvés ({len(reply.retrieved)}, dont {reply.used_extracts} envoyés au modèle) :")
        for rank, found in enumerate(reply.retrieved, start=1):
            sent = "envoyé" if rank <= reply.used_extracts else "non envoyé"
            preview = " ".join(found.chunk.text.split())[:80]
            print(f"  {rank}. page {found.chunk.source.page} — score {found.score:.2f} — {sent} — {preview}…")


def _fail(message: str) -> int:
    print(message, file=sys.stderr)
    return 1


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="mini-rag-ask",
        description="Pose une question aux PDF d'un dossier et affiche la réponse avec ses sources vérifiées.",
    )
    parser.add_argument("question", help="la question, entre guillemets")
    parser.add_argument("--corpus", default=DEFAULT_CORPUS, help="dossier contenant les PDF")
    parser.add_argument("--verbose", action="store_true", help="liste tous les extraits retrouvés, avec leur score")
    return parser.parse_args(argv)


if __name__ == "__main__":
    raise SystemExit(main())
