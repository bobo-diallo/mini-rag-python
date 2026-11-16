"""Tests du client de génération Ollama. Les tests unitaires utilisent un faux serveur : aucun réseau, aucun modèle."""

import json

import httpx
import pytest

from mini_rag.generation.chat_model import ChatModel, Completion, GenerationError, TokenUsage
from mini_rag.generation.ollama_chat_model import OllamaChatModel


def chat_model_answering(handler) -> OllamaChatModel:
    """Un OllamaChatModel branché sur un faux serveur : `handler` reçoit la requête et rend la réponse."""
    client = httpx.Client(transport=httpx.MockTransport(handler))
    return OllamaChatModel(
        model="llama3.2:3b",
        base_url="http://ollama.test:11434",
        num_ctx=4096,
        max_output_tokens=512,
        client=client,
    )


def ollama_reply(**fields) -> httpx.Response:
    return httpx.Response(200, json={"response": "Bonjour.", "prompt_eval_count": 44, "eval_count": 8, **fields})


def test_sends_the_prompt_with_stable_settings_to_the_generate_endpoint():
    received = {}

    def handler(request: httpx.Request) -> httpx.Response:
        received["method"] = request.method
        received["url"] = str(request.url)
        received["body"] = json.loads(request.content)
        return ollama_reply()

    chat_model_answering(handler).generate("Dis bonjour.")

    assert received["method"] == "POST"
    assert received["url"] == "http://ollama.test:11434/api/generate"
    assert received["body"] == {
        "model": "llama3.2:3b",
        "prompt": "Dis bonjour.",
        "stream": False,  # une seule réponse complète, pas un flux de morceaux
        "options": {"temperature": 0, "num_ctx": 4096, "num_predict": 512},
    }


def test_returns_the_text_and_the_token_counts():
    completion = chat_model_answering(lambda request: ollama_reply(response="Il est bleu.")).generate("Q ?")

    assert completion == Completion(text="Il est bleu.", tokens=TokenUsage(prompt=44, generated=8))
    assert completion.tokens.total == 52


def test_missing_token_counts_are_not_invented():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"response": "Salut."})

    assert chat_model_answering(handler).generate("Q ?").tokens is None


def test_the_text_is_returned_as_received_without_cleaning():
    completion = chat_model_answering(lambda request: ollama_reply(response="  Réponse.\n")).generate("Q ?")

    assert completion.text == "  Réponse.\n"


@pytest.mark.parametrize("prompt", ["", "   ", "\n\t"])
def test_a_blank_prompt_is_refused_without_any_request(prompt: str):
    def handler(request: httpx.Request) -> httpx.Response:
        raise AssertionError("aucune requête ne devrait partir")

    with pytest.raises(ValueError, match="vide"):
        chat_model_answering(handler).generate(prompt)


def test_a_trailing_slash_in_the_base_url_is_tolerated():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/generate"
        return ollama_reply()

    client = httpx.Client(transport=httpx.MockTransport(handler))
    model = OllamaChatModel(
        model="m", base_url="http://ollama.test:11434/", num_ctx=1024, max_output_tokens=64, client=client
    )

    assert model.generate("Q ?").text == "Bonjour."


def test_an_unknown_model_gives_a_clear_error_with_the_server_message_and_the_fix():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"error": "model 'llama3.2:3b' not found"})

    with pytest.raises(GenerationError) as error:
        chat_model_answering(handler).generate("Q ?")

    assert "model 'llama3.2:3b' not found" in str(error.value)
    assert "ollama pull llama3.2:3b" in str(error.value)


def test_an_unreachable_server_gives_a_clear_error_naming_the_address():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connexion refusée")

    with pytest.raises(GenerationError, match="injoignable.*http://ollama.test:11434"):
        chat_model_answering(handler).generate("Q ?")


def test_a_timeout_is_reported_as_a_slow_answer_not_as_a_missing_server():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("trop long")

    with pytest.raises(GenerationError, match="temps"):
        chat_model_answering(handler).generate("Q ?")


@pytest.mark.parametrize("body", [{"autre": 1}, {"response": 42}, {"response": None}])
def test_a_response_without_text_is_rejected(body):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=body)

    with pytest.raises(GenerationError, match="response"):
        chat_model_answering(handler).generate("Q ?")


def test_ollama_chat_model_declares_the_contract_and_a_forgetful_class_cannot_be_created():
    assert ChatModel in OllamaChatModel.__mro__

    class Forgetful(ChatModel):
        pass

    with pytest.raises(TypeError, match="generate"):
        Forgetful()


# --- Test d'intégration : le vrai Ollama, le vrai llama3.2:3b ----------------------------------
# Sauté automatiquement si le serveur n'est pas joignable (par exemple sur GitHub Actions).


@pytest.mark.ollama
def test_the_real_llama_answers_and_reports_its_token_counts(real_ollama_url: str):
    model = OllamaChatModel(
        model="llama3.2:3b", base_url=real_ollama_url, num_ctx=2048, max_output_tokens=30
    )

    completion = model.generate("Réponds uniquement par le mot : oui.")

    assert completion.text.strip() != ""
    assert completion.tokens is not None
    assert completion.tokens.prompt > 0
    assert 0 < completion.tokens.generated <= 30  # num_predict plafonne la longueur de la réponse
