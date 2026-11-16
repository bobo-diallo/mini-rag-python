"""Commande `mini-rag-eval-retrieval` : mesure si la recherche par le sens retrouve la bonne page."""

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from mini_rag.config import Settings
from mini_rag.evaluation.metrics import hit_rate, mean_reciprocal_rank, random_hit_rate, random_mrr
from mini_rag.evaluation.questions import load_questions
from mini_rag.evaluation.retrieval_eval import QuestionOutcome, evaluate_retrieval
from mini_rag.ingestion.chunker import chunk_pages
from mini_rag.ingestion.pdf_loader import PdfLoader
from mini_rag.retrieval.embedder import Embedder, EmbeddingError
from mini_rag.retrieval.ollama_embedder import OllamaEmbedder
from mini_rag.retrieval.retriever import Retriever
from mini_rag.retrieval.vector_store import InMemoryVectorStore

DEFAULT_CORPUS = "eval/corpus"
DEFAULT_QUESTIONS = "eval/retrieval-questions.json"


def main(
    argv: Sequence[str] | None = None,
    *,
    embedder: Embedder | None = None,
    settings: Settings | None = None,
) -> int:
    """Rend 0 si la mesure a eu lieu, 1 sinon. `embedder` et `settings` sont injectables : les tests y mettent des faux."""
    args = _parse_args(argv)
    if args.k < 1:
        return _fail(f"k doit valoir au moins 1 (reçu {args.k}).")

    settings = settings or Settings()
    corpus_pdf = _find_the_corpus_pdf(Path(args.corpus))
    if isinstance(corpus_pdf, str):  # une chaîne = un message d'erreur
        return _fail(corpus_pdf)

    try:
        questions = load_questions(args.questions)
    except FileNotFoundError:
        return _fail(f"Fichier de questions introuvable : {args.questions}")
    except ValueError as error:  # JSON illisible ou contenu invalide
        return _fail(f"Fichier de questions invalide ({args.questions}) : {error}")

    chunks = chunk_pages(PdfLoader().load(corpus_pdf))
    model_label = type(embedder).__name__ if embedder else settings.embedding_model
    embedder = embedder or OllamaEmbedder(model=settings.embedding_model, base_url=settings.ollama_url)
    retriever = Retriever(embedder, InMemoryVectorStore(), settings.embedding_batch_size)

    try:
        retriever.index(chunks)
        outcomes = evaluate_retrieval(retriever, questions, args.k)
    except EmbeddingError as error:
        return _fail(str(error))

    page_count = len({chunk.source.page for chunk in chunks})
    print(f"Corpus : {corpus_pdf.name} — {len(chunks)} chunks, {page_count} pages | modèle : {model_label} | k = {args.k}")
    print(f"Questions : {len(outcomes)}\n")
    _print_table(outcomes)
    _print_summary(outcomes, page_count)
    return 0


def _find_the_corpus_pdf(folder: Path) -> Path | str:
    """Le PDF du corpus, ou un message d'erreur. Un seul PDF : sinon « page 3 » ne dirait pas de quel fichier."""
    if not folder.is_dir():
        return f"Dossier de corpus introuvable : {folder}"
    pdfs = sorted(p for p in folder.iterdir() if p.suffix.lower() == ".pdf")
    if not pdfs:
        return f"Aucun PDF dans {folder}."
    if len(pdfs) > 1:
        return f"Le corpus doit contenir un seul PDF (les numéros de page seraient ambigus), il y en a {len(pdfs)} dans {folder}."
    return pdfs[0]


def _print_table(outcomes: Sequence[QuestionOutcome]) -> None:
    print(f"{'#':>3}  {'rang':>4}  {'attendue':>8}  {'trois premières pages (score)':<38}  question")
    for number, outcome in enumerate(outcomes, start=1):
        rank = "-" if outcome.rank is None else str(outcome.rank)
        top3 = " · ".join(f"p{r.chunk.source.page} ({r.score:.2f})" for r in outcome.top[:3])
        question = outcome.question.question
        print(f"{number:>3}  {rank:>4}  {outcome.question.expected_page:>8}  {top3:<38}  {question[:60]}")
    print()


def _print_summary(outcomes: Sequence[QuestionOutcome], page_count: int) -> None:
    ranks = [outcome.rank for outcome in outcomes]
    total = len(ranks)
    for k in (1, 3):
        hits = sum(1 for rank in ranks if rank is not None and rank <= k)
        print(f"hit@{k} : {hits}/{total} = {hit_rate(ranks, k) * 100:.0f}%")
    print(f"MRR   : {mean_reciprocal_rank(ranks):.2f}")
    print(
        f"Hasard (référence) : hit@3 = {random_hit_rate(page_count, 3) * 100:.0f}%, "
        f"MRR = {random_mrr(page_count):.2f}"
    )


def _fail(message: str) -> int:
    print(message, file=sys.stderr)
    return 1


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="mini-rag-eval-retrieval",
        description="Mesure la qualité de la recherche par le sens (rang de la bonne page, hit@k, MRR).",
    )
    parser.add_argument("--corpus", default=DEFAULT_CORPUS, help="dossier contenant le PDF du corpus")
    parser.add_argument("--questions", default=DEFAULT_QUESTIONS, help="fichier JSON des questions")
    parser.add_argument("--k", type=int, default=10, help="nombre de résultats gardés pour chaque question")
    return parser.parse_args(argv)


if __name__ == "__main__":
    raise SystemExit(main())
