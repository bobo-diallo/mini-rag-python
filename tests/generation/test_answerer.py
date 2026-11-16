"""Tests de l'Answerer : chercher, décider de répondre ou non, interroger le modèle, vérifier ses citations."""

from collections.abc import Sequence

import pytest

from mini_rag.domain.models import Chunk, SearchResult, Source
from mini_rag.generation.answerer import Answerer, AnswerOptions
from mini_rag.generation.chat_model import ChatModel, Completion, GenerationError, TokenUsage
from mini_rag.generation.prompt import NO_ANSWER, build_prompt, estimate_tokens


class FakeSearcher:
    """Faux moteur de recherche : rend des résultats préparés et note ce qu'on lui demande."""

    def __init__(self, results: Sequence[SearchResult]) -> None:
        self.results = list(results)
        self.calls: list[tuple[str, int]] = []

    def search(self, question: str, k: int) -> list[SearchResult]:
        self.calls.append((question, k))
        return self.results


class FakeChatModel(ChatModel):
    """Faux modèle : rend une réponse préparée et note les prompts reçus."""

    def __init__(self, text: str = "Réponse [1].", tokens: TokenUsage | None = None) -> None:
        self.text = text
        self.tokens = tokens
        self.prompts: list[str] = []

    def generate(self, prompt: str) -> Completion:
        self.prompts.append(prompt)
        return Completion(text=self.text, tokens=self.tokens)


def result(text: str, page: int, score: float) -> SearchResult:
    chunk = Chunk(text=text, source=Source(file="guide.pdf", page=page), index=0)
    return SearchResult(chunk=chunk, score=score)


def options(**changes) -> AnswerOptions:
    values = {"k": 4, "min_score": 0.55, "context_limit": 4096, "max_output_tokens": 512}
    return AnswerOptions(**{**values, **changes})


def four_results() -> list[SearchResult]:
    return [result(f"Texte de la page {n}.", page=n, score=0.9 - n / 10) for n in range(1, 5)]


QUESTION = "Quel jour est-on prélevé ?"


def test_it_asks_the_searcher_for_k_results():
    searcher = FakeSearcher(four_results())

    Answerer(searcher, FakeChatModel(), options(k=3)).answer(QUESTION)

    assert searcher.calls == [(QUESTION, 3)]


# --- Refus sans appeler le modèle -------------------------------------------------------------


def test_nothing_found_means_a_refusal_without_calling_the_model():
    model = FakeChatModel()

    reply = Answerer(FakeSearcher([]), model, options()).answer(QUESTION)

    assert reply.text == NO_ANSWER
    assert reply.answered is False
    assert reply.citations == ()
    assert model.prompts == []


def test_a_best_score_below_the_threshold_means_a_refusal_without_calling_the_model():
    weak = [result("Texte.", page=1, score=0.54)]
    model = FakeChatModel()

    reply = Answerer(FakeSearcher(weak), model, options(min_score=0.55)).answer(QUESTION)

    assert reply.answered is False
    assert reply.retrieved == tuple(weak)  # on garde ce qui a été trouvé, pour comprendre le refus
    assert reply.used_extracts == 0
    assert model.prompts == []


def test_a_best_score_equal_to_the_threshold_is_enough_to_answer():
    exact = [result("Texte.", page=1, score=0.55)]
    model = FakeChatModel("Oui [1].")

    reply = Answerer(FakeSearcher(exact), model, options(min_score=0.55)).answer(QUESTION)

    assert reply.answered is True
    assert len(model.prompts) == 1


# --- Réponse et vérification des citations ----------------------------------------------------


def test_the_prompt_sent_to_the_model_holds_the_numbered_extracts_in_ranking_order_and_the_question():
    model = FakeChatModel()
    found = four_results()

    Answerer(FakeSearcher(found), model, options()).answer(QUESTION)

    assert model.prompts == [build_prompt(QUESTION, [r.chunk for r in found])]


def test_a_cited_number_becomes_a_verified_source_taken_from_the_extracts():
    found = four_results()

    reply = Answerer(FakeSearcher(found), FakeChatModel("Le cinq du mois [2]."), options()).answer(QUESTION)

    assert reply.answered is True
    assert reply.text == "Le cinq du mois [2]."
    assert reply.citations == (found[1],)
    assert reply.invalid_citations == ()


def test_an_invented_number_is_reported_and_never_turned_into_a_source():
    reply = Answerer(FakeSearcher(four_results()), FakeChatModel("Selon [2] et [9]."), options()).answer(QUESTION)

    assert [c.chunk.source.page for c in reply.citations] == [2]
    assert reply.invalid_citations == (9,)


def test_the_answer_is_cleaned_of_surrounding_whitespace():
    reply = Answerer(FakeSearcher(four_results()), FakeChatModel("  \n Oui [1].\n"), options()).answer(QUESTION)

    assert reply.text == "Oui [1]."


def test_an_answer_without_any_citation_is_still_an_answer_but_with_no_verified_source():
    reply = Answerer(FakeSearcher(four_results()), FakeChatModel("Oui, sans doute."), options()).answer(QUESTION)

    assert reply.answered is True
    assert reply.citations == ()
    assert reply.invalid_citations == ()


def test_the_token_counts_of_the_model_are_passed_along():
    usage = TokenUsage(prompt=300, generated=40)

    reply = Answerer(FakeSearcher(four_results()), FakeChatModel(tokens=usage), options()).answer(QUESTION)

    assert reply.tokens == usage


# --- Le modèle dit « je ne sais pas » ----------------------------------------------------------


@pytest.mark.parametrize("model_text", [NO_ANSWER, "je ne sais pas.", "  JE NE SAIS PAS : rien là-dessus", "\nJe ne sais pas"])
def test_a_model_answer_starting_with_je_ne_sais_pas_is_a_refusal(model_text: str):
    usage = TokenUsage(prompt=200, generated=15)
    found = four_results()

    reply = Answerer(FakeSearcher(found), FakeChatModel(model_text, tokens=usage), options()).answer(QUESTION)

    assert reply.answered is False
    assert reply.text == NO_ANSWER  # toujours la phrase fixe, quelle que soit la façon dont le modèle l'a écrite
    assert reply.citations == ()
    assert reply.used_extracts == 4  # le modèle a bien été appelé avec ces extraits
    assert reply.tokens == usage  # et ses tokens ont bien été consommés


def test_je_ne_sais_pas_in_the_middle_of_a_real_answer_is_not_a_refusal():
    text = "Le délai est de trente jours [1]. Je ne sais pas pour le reste."

    reply = Answerer(FakeSearcher(four_results()), FakeChatModel(text), options()).answer(QUESTION)

    assert reply.answered is True
    assert reply.citations[0].chunk.source.page == 1


# --- La place disponible dans la fenêtre du modèle ---------------------------------------------


def long_results(count: int) -> list[SearchResult]:
    return [result("x" * 300, page=n, score=0.9 - n / 100) for n in range(1, count + 1)]


def test_extracts_that_do_not_fit_are_dropped_starting_with_the_worst_ranked():
    found = long_results(4)
    max_output = 100
    # On fixe la fenêtre pour que le prompt à 2 extraits tienne exactement, et pas celui à 3.
    two_fit = estimate_tokens(build_prompt(QUESTION, [r.chunk for r in found[:2]]))
    model = FakeChatModel("Oui [1].")

    reply = Answerer(
        FakeSearcher(found), model, options(context_limit=two_fit + max_output, max_output_tokens=max_output)
    ).answer(QUESTION)

    assert reply.used_extracts == 2
    assert model.prompts == [build_prompt(QUESTION, [r.chunk for r in found[:2]])]
    assert reply.retrieved == tuple(found)  # la recherche, elle, en avait trouvé 4


def test_a_citation_beyond_the_extracts_really_sent_is_invalid_even_if_the_search_found_more():
    found = long_results(4)
    max_output = 100
    two_fit = estimate_tokens(build_prompt(QUESTION, [r.chunk for r in found[:2]]))

    reply = Answerer(
        FakeSearcher(found),
        FakeChatModel("Selon [3]."),  # l'extrait 3 existe dans la recherche, mais n'a pas été envoyé
        options(context_limit=two_fit + max_output, max_output_tokens=max_output),
    ).answer(QUESTION)

    assert reply.citations == ()
    assert reply.invalid_citations == (3,)


def test_at_least_one_extract_is_always_kept_even_if_it_does_not_fit_alone():
    found = long_results(3)

    reply = Answerer(
        FakeSearcher(found), FakeChatModel("Oui [1]."), options(context_limit=200, max_output_tokens=150)
    ).answer(QUESTION)

    assert reply.used_extracts == 1


# --- Erreurs et réglages invalides --------------------------------------------------------------


def test_a_model_failure_is_not_hidden():
    class DownModel(ChatModel):
        def generate(self, prompt: str) -> Completion:
            raise GenerationError("Ollama injoignable (test)")

    with pytest.raises(GenerationError, match="injoignable"):
        Answerer(FakeSearcher(four_results()), DownModel(), options()).answer(QUESTION)


@pytest.mark.parametrize(
    "changes",
    [
        {"k": 0},
        {"max_output_tokens": 0},
        {"context_limit": 512, "max_output_tokens": 512},  # aucune place pour le prompt
        {"min_score": 1.5},
        {"min_score": -1.5},
    ],
)
def test_invalid_options_are_rejected_at_creation(changes):
    with pytest.raises(ValueError):
        options(**changes)
