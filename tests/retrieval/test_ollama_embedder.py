"""Tests de l'embedder Ollama. Les tests unitaires utilisent un faux serveur : aucun réseau, aucun modèle."""

import json

import httpx
import pytest

from mini_rag.retrieval.embedder import EmbeddingError
from mini_rag.retrieval.ollama_embedder import OllamaEmbedder


def embedder_answering(handler) -> OllamaEmbedder:
    """Un OllamaEmbedder branché sur un faux serveur : `handler` reçoit la requête et rend la réponse."""
    client = httpx.Client(transport=httpx.MockTransport(handler))
    return OllamaEmbedder(model="bge-m3", base_url="http://ollama.test:11434", client=client)


def test_sends_the_texts_and_the_model_to_the_embed_endpoint_and_returns_the_vectors():
    received = {}

    def handler(request: httpx.Request) -> httpx.Response:
        received["method"] = request.method
        received["url"] = str(request.url)
        received["body"] = json.loads(request.content)
        return httpx.Response(200, json={"embeddings": [[0.1, 0.2], [0.3, 0.4]]})

    vectors = embedder_answering(handler).embed_documents(["bonjour", "chat"])

    assert received["method"] == "POST"
    assert received["url"] == "http://ollama.test:11434/api/embed"
    assert received["body"] == {"model": "bge-m3", "input": ["bonjour", "chat"]}
    assert vectors == [[0.1, 0.2], [0.3, 0.4]]


def test_a_query_gives_a_single_vector():
    def handler(request: httpx.Request) -> httpx.Response:
        assert json.loads(request.content)["input"] == ["une question"]
        return httpx.Response(200, json={"embeddings": [[0.5, 0.6]]})

    assert embedder_answering(handler).embed_query("une question") == [0.5, 0.6]


def test_no_text_means_no_request():
    def handler(request: httpx.Request) -> httpx.Response:
        raise AssertionError("aucune requête ne devrait partir")

    assert embedder_answering(handler).embed_documents([]) == []


def test_a_trailing_slash_in_the_base_url_is_tolerated():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/embed"
        return httpx.Response(200, json={"embeddings": [[1.0]]})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    embedder = OllamaEmbedder(model="bge-m3", base_url="http://ollama.test:11434/", client=client)

    assert embedder.embed_query("x") == [1.0]


def test_an_unknown_model_gives_a_clear_error_with_the_server_message_and_the_fix():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"error": "model 'bge-m3' not found"})

    with pytest.raises(EmbeddingError) as error:
        embedder_answering(handler).embed_documents(["x"])

    assert "model 'bge-m3' not found" in str(error.value)
    assert "ollama pull bge-m3" in str(error.value)


def test_an_unreachable_server_gives_a_clear_error_naming_the_address():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connexion refusée")

    with pytest.raises(EmbeddingError, match="injoignable.*http://ollama.test:11434"):
        embedder_answering(handler).embed_documents(["x"])


def test_a_response_without_embeddings_is_rejected():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"autre": 1})

    with pytest.raises(EmbeddingError, match="embeddings"):
        embedder_answering(handler).embed_documents(["x"])


def test_a_response_with_the_wrong_number_of_vectors_is_rejected():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"embeddings": [[1.0]]})  # 1 vecteur pour 2 textes

    with pytest.raises(EmbeddingError, match="1 vecteurs pour 2 textes"):
        embedder_answering(handler).embed_documents(["a", "b"])


# --- Test d'intégration : le vrai Ollama, le vrai bge-m3 -------------------------------------
# Sauté automatiquement si le serveur n'est pas joignable (par exemple sur GitHub Actions).


@pytest.mark.ollama
def test_the_real_bge_m3_gives_1024_dimensional_vectors(real_ollama_url: str):
    vector = OllamaEmbedder(model="bge-m3", base_url=real_ollama_url).embed_query("bonjour")

    assert len(vector) == 1024
    assert all(isinstance(x, float) for x in vector)


@pytest.mark.ollama
def test_the_real_bge_m3_puts_close_meanings_closer_than_unrelated_ones(real_ollama_url: str):
    from mini_rag.retrieval.similarity import cosine_similarity

    embedder = OllamaEmbedder(model="bge-m3", base_url=real_ollama_url)
    cat, kitten, tax = embedder.embed_documents(
        ["Le chat dort sur le canapé.", "Un chaton fait la sieste sur le sofa.", "La déclaration de revenus est due en avril."]
    )

    assert cosine_similarity(cat, kitten) > cosine_similarity(cat, tax)
