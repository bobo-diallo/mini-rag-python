"""Tests du client Claude. Un faux serveur est branché sur le vrai SDK : aucun réseau, aucune vraie clé."""

import json

import anthropic
import httpx2
import pytest

from mini_rag.generation.anthropic_chat_model import AnthropicChatModel
from mini_rag.generation.chat_model import ChatModel, Completion, GenerationError, TokenUsage


def model_answering(handler) -> AnthropicChatModel:
    """Un AnthropicChatModel dont le SDK parle à un faux serveur : `handler` reçoit la requête et rend la réponse."""
    client = anthropic.Anthropic(
        api_key="sk-test",
        max_retries=0,  # pas de nouvelle tentative : un test d'erreur doit échouer tout de suite
        http_client=anthropic.DefaultHttpxClient(transport=httpx2.MockTransport(handler)),
    )
    return AnthropicChatModel(model="claude-haiku-5-5", max_output_tokens=512, client=client)


def message(content, *, stop_reason="end_turn", **extra) -> httpx2.Response:
    body = {
        "id": "msg_test",
        "type": "message",
        "role": "assistant",
        "model": "claude-haiku-5-5",
        "content": content,
        "stop_reason": stop_reason,
        "stop_sequence": None,
        "usage": {"input_tokens": 120, "output_tokens": 15},
        **extra,
    }
    return httpx2.Response(200, json=body)


def text_reply(text: str = "Bonjour [1].") -> httpx2.Response:
    return message([{"type": "text", "text": text}])


def error_reply(status: int, kind: str, text: str) -> httpx2.Response:
    return httpx2.Response(status, json={"type": "error", "error": {"type": kind, "message": text}})


def test_sends_the_prompt_as_one_user_message_with_a_low_effort_and_no_temperature():
    received = {}

    def handler(request: httpx2.Request) -> httpx2.Response:
        received["method"] = request.method
        received["path"] = request.url.path
        received["authorization"] = request.headers.get("authorization")
        received["body"] = json.loads(request.content)
        return text_reply()

    model_answering(handler).generate("Dis bonjour.")

    assert (received["method"], received["path"]) == ("POST", "/v1/messages")
    assert received["authorization"] == "Bearer sk-test"  # la clé voyage dans l'en-tête Authorization
    body = received["body"]
    assert body["model"] == "claude-haiku-5-5"
    assert body["max_tokens"] == 512
    assert body["messages"] == [{"role": "user", "content": "Dis bonjour."}]
    assert body["output_config"] == {"effort": "low"}  # réponses courtes : on évite de payer un long raisonnement
    assert "temperature" not in body  # Haiku 5.5 refuse toute température autre que celle par défaut


def test_returns_the_text_and_the_token_counts():
    completion = model_answering(lambda request: text_reply("Il est bleu.")).generate("Q ?")

    assert completion == Completion(text="Il est bleu.", tokens=TokenUsage(prompt=120, generated=15))


def test_text_blocks_are_joined_and_thinking_blocks_are_ignored():
    def handler(request: httpx2.Request) -> httpx2.Response:
        return message(
            [
                {"type": "thinking", "thinking": "", "signature": "sig"},
                {"type": "text", "text": "Première partie. "},
                {"type": "text", "text": "Seconde partie [2]."},
            ]
        )

    assert model_answering(handler).generate("Q ?").text == "Première partie. Seconde partie [2]."


def test_a_reply_without_any_text_block_is_an_error():
    with pytest.raises(GenerationError, match="texte"):
        model_answering(lambda request: message([])).generate("Q ?")


@pytest.mark.parametrize("prompt", ["", "   ", "\n\t"])
def test_a_blank_prompt_is_refused_without_any_request(prompt: str):
    def handler(request: httpx2.Request) -> httpx2.Response:
        raise AssertionError("aucune requête ne devrait partir")

    with pytest.raises(ValueError, match="vide"):
        model_answering(handler).generate(prompt)


def test_a_safety_refusal_is_reported_with_its_category():
    def handler(request: httpx2.Request) -> httpx2.Response:
        return message(
            [],
            stop_reason="refusal",
            stop_details={"type": "refusal", "category": "cyber", "explanation": "demande refusée"},
        )

    with pytest.raises(GenerationError, match="refusé.*cyber"):
        model_answering(handler).generate("Q ?")


@pytest.mark.parametrize(
    "response, expected",
    [
        (error_reply(401, "authentication_error", "invalid x-api-key"), "clé"),
        (error_reply(403, "permission_error", "interdit"), "accès"),
        (error_reply(404, "not_found_error", "model: claude-haiku-5-5"), "claude-haiku-5-5"),
        (error_reply(429, "rate_limit_error", "trop de requêtes"), "limite"),
        (error_reply(500, "api_error", "panne interne"), "500"),
    ],
)
def test_http_errors_become_a_generation_error_with_a_helpful_message(response, expected):
    with pytest.raises(GenerationError) as error:
        model_answering(lambda request: response).generate("Q ?")

    assert expected.lower() in str(error.value).lower()


def test_an_unreachable_service_gives_a_clear_error():
    def handler(request: httpx2.Request) -> httpx2.Response:
        raise httpx2.ConnectError("connexion refusée")

    with pytest.raises(GenerationError, match="injoignable"):
        model_answering(handler).generate("Q ?")


def test_a_timeout_is_reported_as_a_slow_answer():
    def handler(request: httpx2.Request) -> httpx2.Response:
        raise httpx2.ReadTimeout("trop long")

    with pytest.raises(GenerationError, match="temps"):
        model_answering(handler).generate("Q ?")


def test_a_key_is_required_when_no_client_is_provided():
    with pytest.raises(ValueError, match="clé"):
        AnthropicChatModel(model="claude-haiku-5-5", max_output_tokens=512, api_key="  ")


def test_the_class_declares_the_contract():
    assert ChatModel in AnthropicChatModel.__mro__
