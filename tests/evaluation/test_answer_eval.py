"""Tests de l'évaluation des réponses : poser les questions à l'Answerer, puis compter ce qui s'est passé."""

from collections.abc import Sequence

import pytest

from mini_rag.domain.models import Chunk, SearchResult, Source
from mini_rag.evaluation.answer_eval import AnswerSample, evaluate_answers, summarize
from mini_rag.evaluation.questions import EvalQuestion
from mini_rag.generation.answerer import Answerer, AnswerOptions, Reply
from mini_rag.generation.chat_model import ChatModel, Completion, TokenUsage
from mini_rag.generation.prompt import NO_ANSWER


def found(page: int, score: float = 0.9) -> SearchResult:
    chunk = Chunk(text=f"page {page}", source=Source(file="g.pdf", page=page), index=0)
    return SearchResult(chunk=chunk, score=score)


def reply(*, answered=True, citations=(), invalid=(), used=1, tokens=None) -> Reply:
    return Reply(
        text="x" if answered else NO_ANSWER,
        answered=answered,
        citations=tuple(citations),
        invalid_citations=tuple(invalid),
        retrieved=(found(1),),
        used_extracts=used,
        tokens=tokens,
    )


def sample(expected_page, **reply_fields) -> AnswerSample:
    return AnswerSample(question="Q ?", expected_page=expected_page, reply=reply(**reply_fields), seconds=0.5)


# --- Un échantillon : une question posée une fois ------------------------------------------------


def test_a_sample_knows_whether_it_cited_the_expected_page():
    assert sample(2, citations=[found(2)]).cited_expected_page is True
    assert sample(2, citations=[found(5)]).cited_expected_page is False
    assert sample(2).cited_expected_page is False


def test_an_out_of_scope_sample_never_cites_the_expected_page():
    assert sample(None, citations=[found(2)]).cited_expected_page is False
    assert sample(None).answerable is False
    assert sample(3).answerable is True


# --- Le résumé : les compteurs ------------------------------------------------------------------


def test_the_summary_counts_answerable_questions_by_outcome():
    samples = [
        sample(1, citations=[found(1)]),  # répondu, cité, bonne page
        sample(2, citations=[found(9)]),  # répondu, cité, mauvaise page
        sample(3),  # répondu sans aucune citation
        sample(4, citations=[found(4)], invalid=[7]),  # bonne page citée, mais un numéro inventé en plus
        sample(5, answered=False),  # refus à tort
    ]

    summary = summarize(samples)

    assert summary.answerable_total == 5
    assert summary.answered == 4
    assert summary.with_citation == 3
    assert summary.without_invalid_citation == 3  # 4 réponses données, dont une a inventé [7]
    assert summary.cited_expected_page == 2
    assert summary.wrongly_refused == 1


def test_the_summary_counts_out_of_scope_questions_by_outcome():
    samples = [
        sample(None, answered=False, used=0),  # refusé par le seuil, sans appeler le modèle
        sample(None, answered=False, used=3),  # refusé par le modèle lui-même
        sample(None, citations=[found(2)]),  # répondu : le système a inventé une réponse
    ]

    summary = summarize(samples)

    assert summary.out_of_scope_total == 3
    assert summary.correctly_refused == 2
    assert summary.refused_without_calling_the_model == 1
    assert summary.answered_out_of_scope == 1


def test_the_summary_adds_up_time_and_tokens_when_they_are_known():
    samples = [
        sample(1, citations=[found(1)], tokens=TokenUsage(prompt=100, generated=20)),
        sample(2, citations=[found(2)], tokens=TokenUsage(prompt=200, generated=30)),
        sample(None, answered=False, used=0),  # aucun appel au modèle : pas de tokens
    ]

    summary = summarize(samples)

    assert summary.total_seconds == pytest.approx(1.5)
    assert summary.total_tokens == 350


# --- Poser les questions à un vrai Answerer (avec un faux moteur et un faux modèle) --------------


class FixedSearcher:
    def __init__(self, results: Sequence[SearchResult]) -> None:
        self.results = list(results)

    def search(self, question: str, k: int) -> list[SearchResult]:
        return self.results


class ScriptedModel(ChatModel):
    """Rend les réponses préparées l'une après l'autre."""

    def __init__(self, *texts: str) -> None:
        self.texts = list(texts)
        self.calls = 0

    def generate(self, prompt: str) -> Completion:
        text = self.texts[self.calls % len(self.texts)]
        self.calls += 1
        return Completion(text=text, tokens=None)


def make_answerer(results, model) -> Answerer:
    options = AnswerOptions(k=4, min_score=0.55, context_limit=4096, max_output_tokens=512)
    return Answerer(FixedSearcher(results), model, options)


def test_each_question_is_asked_the_requested_number_of_times():
    model = ScriptedModel("Oui [1].")
    answerer = make_answerer([found(2)], model)

    samples = evaluate_answers(
        answerer, [EvalQuestion("Q1 ?", 2), EvalQuestion("Q2 ?", 2)], out_of_scope=["Hors sujet ?"], runs=3
    )

    assert len(samples) == 9  # (2 + 1) questions x 3 passages
    assert [s.question for s in samples[:3]] == ["Q1 ?"] * 3  # les passages d'une même question se suivent
    assert model.calls == 9


def test_samples_carry_the_expected_page_and_none_for_out_of_scope_questions():
    samples = evaluate_answers(
        make_answerer([found(2)], ScriptedModel("Oui [1].")), [EvalQuestion("Q1 ?", 2)], ["Hors sujet ?"], runs=1
    )

    assert [(s.question, s.expected_page) for s in samples] == [("Q1 ?", 2), ("Hors sujet ?", None)]


def test_a_low_score_search_gives_refusals_without_calling_the_model():
    model = ScriptedModel("Ne devrait jamais servir.")
    weak = make_answerer([found(2, score=0.1)], model)

    samples = evaluate_answers(weak, [], out_of_scope=["Hors sujet ?"], runs=2)

    assert all(not s.reply.answered for s in samples)
    assert model.calls == 0


def test_the_duration_of_each_question_is_measured():
    samples = evaluate_answers(make_answerer([found(2)], ScriptedModel("Oui [1].")), [EvalQuestion("Q ?", 2)], [], runs=1)

    assert samples[0].seconds >= 0


def test_at_least_one_run_is_required():
    with pytest.raises(ValueError, match="passage"):
        evaluate_answers(make_answerer([found(2)], ScriptedModel("x")), [EvalQuestion("Q ?", 2)], [], runs=0)
