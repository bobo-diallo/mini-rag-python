"""Tests du prompt : ce que le modèle reçoit (consigne, extraits numérotés, question)."""

import pytest

from mini_rag.domain.models import Chunk, Source
from mini_rag.generation.prompt import NO_ANSWER, build_prompt, estimate_tokens


def extract(text: str, page: int = 1) -> Chunk:
    return Chunk(text=text, source=Source(file="guide.pdf", page=page), index=0)


def test_extracts_are_numbered_from_1_in_the_given_order():
    prompt = build_prompt("Quand ?", [extract("Premier texte."), extract("Second texte.", page=2)])

    assert "[1] Premier texte." in prompt
    assert "[2] Second texte." in prompt
    assert prompt.index("[1] Premier") < prompt.index("[2] Second")


def test_the_prompt_contains_the_question_and_ends_by_waiting_for_the_answer():
    prompt = build_prompt("Quel jour est-on prélevé ?", [extract("Texte.")])

    assert "Question : Quel jour est-on prélevé ?" in prompt
    assert prompt.endswith("Réponse :")


def test_the_order_is_instructions_then_extracts_then_question():
    prompt = build_prompt("Ma question ?", [extract("Mon extrait.")])

    assert prompt.index("uniquement à partir des extraits") < prompt.index("[1] Mon extrait.")
    assert prompt.index("[1] Mon extrait.") < prompt.index("Question : Ma question ?")


def test_the_instructions_ask_for_numbered_citations_and_give_the_exact_refusal_sentence():
    prompt = build_prompt("Q ?", [extract("Texte.")])

    assert "entre crochets" in prompt
    assert NO_ANSWER in prompt  # le code reconnaîtra cette phrase fixe dans la réponse


def test_no_extract_is_refused_because_there_is_nothing_to_answer_from():
    with pytest.raises(ValueError, match="aucun extrait"):
        build_prompt("Q ?", [])


def test_the_refusal_sentence_starts_with_je_ne_sais_pas():
    # Le code détecte un refus en cherchant ce début de phrase (voir l'Answerer).
    assert NO_ANSWER.lower().startswith("je ne sais pas")


@pytest.mark.parametrize("text, tokens", [("", 0), ("a", 1), ("abc", 1), ("abcd", 2), ("a" * 300, 100)])
def test_the_token_estimate_is_pessimistic_three_characters_per_token(text: str, tokens: int):
    assert estimate_tokens(text) == tokens
