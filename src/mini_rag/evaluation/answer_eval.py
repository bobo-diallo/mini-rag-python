"""Évaluer les réponses : poser chaque question à l'Answerer (plusieurs fois), puis compter ce qui s'est passé."""

import time
from collections.abc import Sequence
from dataclasses import dataclass

from mini_rag.evaluation.questions import EvalQuestion
from mini_rag.generation.answerer import Answerer, Reply


@dataclass(frozen=True)
class AnswerSample:
    """Une question posée une fois : ce qu'on attendait, ce qu'on a reçu, et le temps que ça a pris."""

    question: str
    expected_page: int | None  # None : question hors sujet, les documents ne contiennent pas la réponse
    reply: Reply
    seconds: float

    @property
    def answerable(self) -> bool:
        return self.expected_page is not None

    @property
    def cited_expected_page(self) -> bool:
        """Le modèle a-t-il cité (avec une citation vérifiée) la page qui contient la réponse ?"""
        return self.expected_page is not None and any(
            source.chunk.source.page == self.expected_page for source in self.reply.citations
        )


@dataclass(frozen=True)
class AnswerSummary:
    # Questions dont la réponse EST dans les documents
    answerable_total: int
    answered: int  # le système a répondu (au lieu de refuser)
    wrongly_refused: int  # il a refusé alors que la réponse existait
    with_citation: int  # parmi les réponses données : au moins une citation vérifiée
    without_invalid_citation: int  # parmi les réponses données : aucun numéro inventé
    cited_expected_page: int  # la page qui contient la réponse est bien citée
    # Questions dont la réponse n'est PAS dans les documents
    out_of_scope_total: int
    correctly_refused: int
    refused_without_calling_the_model: int  # refusées par le seuil seul : aucun token consommé
    answered_out_of_scope: int  # le système a répondu quand même : une réponse inventée
    # Coût
    total_seconds: float
    total_tokens: int


def summarize(samples: Sequence[AnswerSample]) -> AnswerSummary:
    answerable = [s for s in samples if s.answerable]
    out_of_scope = [s for s in samples if not s.answerable]
    given = [s for s in answerable if s.reply.answered]
    refused = [s for s in out_of_scope if not s.reply.answered]

    return AnswerSummary(
        answerable_total=len(answerable),
        answered=len(given),
        wrongly_refused=len(answerable) - len(given),
        with_citation=sum(1 for s in given if s.reply.citations),
        without_invalid_citation=sum(1 for s in given if not s.reply.invalid_citations),
        cited_expected_page=sum(1 for s in answerable if s.cited_expected_page),
        out_of_scope_total=len(out_of_scope),
        correctly_refused=len(refused),
        refused_without_calling_the_model=sum(1 for s in refused if s.reply.used_extracts == 0),
        answered_out_of_scope=len(out_of_scope) - len(refused),
        total_seconds=sum(s.seconds for s in samples),
        total_tokens=sum(s.reply.tokens.total for s in samples if s.reply.tokens),
    )


def evaluate_answers(
    answerer: Answerer,
    questions: Sequence[EvalQuestion],
    out_of_scope: Sequence[str],
    runs: int,
) -> list[AnswerSample]:
    """Pose chaque question `runs` fois (la génération n'est pas strictement reproductible : un passage ne suffit pas)."""
    if runs < 1:
        raise ValueError(f"Il faut au moins 1 passage (reçu {runs}).")

    asked = [(q.question, q.expected_page) for q in questions] + [(text, None) for text in out_of_scope]
    samples = []
    for question, expected_page in asked:
        for _ in range(runs):
            start = time.perf_counter()
            reply = answerer.answer(question)
            samples.append(
                AnswerSample(question, expected_page, reply, seconds=time.perf_counter() - start)
            )
    return samples
