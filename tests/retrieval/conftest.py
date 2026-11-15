"""Outils partagés par les tests de recherche : un faux fournisseur de vecteurs, sans Ollama."""

from collections.abc import Sequence

import pytest


class FakeEmbedder:
    """Faux Embedder rapide et prévisible. Il note chaque appel dans `calls` pour qu'on puisse le vérifier.

    Le vecteur d'un texte est [longueur du texte, 1.0] : deux dimensions, jamais nul.
    """

    def __init__(self) -> None:
        self.calls: list[list[str]] = []  # un élément par appel à embed_documents

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        self.calls.append(list(texts))
        return [[float(len(text)), 1.0] for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return [float(len(text)), 1.0]


@pytest.fixture
def fake_embedder() -> FakeEmbedder:
    return FakeEmbedder()


@pytest.fixture(scope="session")
def real_ollama_url() -> str:
    """Adresse du vrai Ollama, ou saut du test si le serveur n'est pas joignable."""
    import httpx

    url = "http://localhost:11434"
    try:
        httpx.get(f"{url}/api/version", timeout=2.0)
    except httpx.HTTPError:
        pytest.skip("Ollama n'est pas joignable : test d'intégration sauté")
    return url
