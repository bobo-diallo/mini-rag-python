"""Commande `mini-rag-eval-answers` : mesure si les réponses citent leurs sources et si le système refuse à bon escient."""

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from mini_rag.composition import build_answerer
from mini_rag.config import Settings
from mini_rag.evaluation.answer_eval import AnswerSample, evaluate_answers, summarize
from mini_rag.evaluation.corpus import CorpusError, find_single_pdf
from mini_rag.evaluation.questions import load_out_of_scope_questions, load_questions
from mini_rag.generation.chat_model import ChatModel, GenerationError
from mini_rag.ingestion.chunker import chunk_pages
from mini_rag.ingestion.pdf_loader import PdfLoader
from mini_rag.retrieval.embedder import Embedder, EmbeddingError

DEFAULT_CORPUS = "eval/corpus"
DEFAULT_QUESTIONS = "eval/retrieval-questions.json"
DEFAULT_OUT_OF_SCOPE = "eval/out-of-scope-questions.json"


def main(
    argv: Sequence[str] | None = None,
    *,
    embedder: Embedder | None = None,
    chat_model: ChatModel | None = None,
    settings: Settings | None = None,
) -> int:
    """Rend 0 si la mesure a eu lieu, 1 sinon. Les composants sont injectables : les tests y mettent des faux."""
    args = _parse_args(argv)
    if args.runs < 1:
        return _fail(f"Il faut au moins 1 passage (reçu {args.runs}).")

    settings = settings or Settings()
    try:
        corpus_pdf = find_single_pdf(Path(args.corpus))
        questions = load_questions(args.questions)
        out_of_scope = load_out_of_scope_questions(args.out_of_scope)
    except CorpusError as error:
        return _fail(str(error))
    except FileNotFoundError as error:
        return _fail(f"Fichier introuvable : {error.filename}")
    except ValueError as error:  # JSON illisible ou contenu invalide
        return _fail(f"Fichier de questions invalide : {error}")

    chunks = chunk_pages(PdfLoader().load(corpus_pdf))
    try:
        answerer = build_answerer(chunks, settings, embedder=embedder, chat_model=chat_model)
        samples = evaluate_answers(answerer, questions, out_of_scope, args.runs)
    except (EmbeddingError, GenerationError) as error:
        return _fail(str(error))

    embedding_label = type(embedder).__name__ if embedder else settings.embedding_model
    chat_label = type(chat_model).__name__ if chat_model else settings.chat_model
    print(
        f"Corpus : {corpus_pdf.name} — {len(chunks)} chunks | recherche : {embedding_label} | "
        f"génération : {chat_label} | k = {settings.top_k} | seuil = {settings.min_score:.2f}"
    )
    passes = f"{args.runs} passage{'s' if args.runs > 1 else ''} par question"
    print(f"Questions du guide : {len(questions)} | hors sujet : {len(out_of_scope)} | {passes}\n")
    _print_table(samples, args.runs)
    if args.show_answers:
        _print_answers(samples)
    _print_summary(samples)
    return 0


def _print_table(samples: Sequence[AnswerSample], runs: int) -> None:
    """Une ligne par question, qui regroupe ses passages : « 2/3 » = vrai pour 2 passages sur 3."""
    print(f"{'#':>3}  {'type':<10}  {'att.':>4}  {'répondu':>7}  {'citée':>5}  {'bonne p.':>8}  {'durée':>6}  question")
    for number, start in enumerate(range(0, len(samples), runs), start=1):
        group = samples[start : start + runs]
        first = group[0]
        answered = sum(1 for s in group if s.reply.answered)
        cited = sum(1 for s in group if s.reply.citations)
        right_page = sum(1 for s in group if s.cited_expected_page)
        seconds = sum(s.seconds for s in group) / len(group)
        kind = "guide" if first.answerable else "hors sujet"
        expected = str(first.expected_page) if first.answerable else "-"
        print(
            f"{number:>3}  {kind:<10}  {expected:>4}  {f'{answered}/{runs}':>7}  {f'{cited}/{runs}':>5}  "
            f"{(f'{right_page}/{runs}' if first.answerable else '-'):>8}  {seconds:>5.1f}s  {first.question[:60]}"
        )
    print()


def _print_answers(samples: Sequence[AnswerSample]) -> None:
    print("Réponses du modèle :")
    for sample in samples:
        print(f"- {sample.question}\n    → {' '.join(sample.reply.text.split())}")
    print()


def _print_summary(samples: Sequence[AnswerSample]) -> None:
    summary = summarize(samples)

    def line(label: str, count: int, total: int) -> str:
        share = f" = {count / total * 100:.0f}%" if total else ""
        return f"{label:<20}: {count}/{total}{share}"

    print("--- Questions du guide (la réponse est dans les documents) ---")
    print(line("Réponses données", summary.answered, summary.answerable_total))
    print(line("Citations vérifiées", summary.with_citation, summary.answered))
    print(line("Sans numéro inventé", summary.without_invalid_citation, summary.answered))
    print(line("Bonne page citée", summary.cited_expected_page, summary.answerable_total))
    print(line("Refus à tort", summary.wrongly_refused, summary.answerable_total))
    print("\n--- Questions hors sujet (la réponse n'est PAS dans les documents) ---")
    print(line("Refus justifiés", summary.correctly_refused, summary.out_of_scope_total))
    by_threshold = summary.refused_without_calling_the_model
    print(f"  dont refusés par le seuil seul (sans appel au modèle) : {by_threshold}/{summary.out_of_scope_total}")
    print(line("Réponses inventées", summary.answered_out_of_scope, summary.out_of_scope_total))
    print(f"\nTokens : {summary.total_tokens} | Durée totale : {summary.total_seconds:.1f} s")


def _fail(message: str) -> int:
    print(message, file=sys.stderr)
    return 1


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="mini-rag-eval-answers",
        description="Mesure les citations vérifiées et les refus justifiés, sur des questions du guide et des questions hors sujet.",
    )
    parser.add_argument("--corpus", default=DEFAULT_CORPUS, help="dossier contenant le PDF du corpus")
    parser.add_argument("--questions", default=DEFAULT_QUESTIONS, help="questions dont la réponse est dans le guide")
    parser.add_argument("--out-of-scope", default=DEFAULT_OUT_OF_SCOPE, help="questions dont la réponse n'y est pas")
    parser.add_argument("--runs", type=int, default=1, help="passages par question (la génération varie d'un passage à l'autre)")
    parser.add_argument("--show-answers", action="store_true", help="affiche le texte de chaque réponse du modèle")
    return parser.parse_args(argv)


if __name__ == "__main__":
    raise SystemExit(main())
