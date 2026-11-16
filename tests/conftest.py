"""Outils partagés par tous les tests."""

import pytest


@pytest.fixture(scope="session")
def real_ollama_url() -> str:
    """Adresse du vrai Ollama, ou saut du test si le serveur n'est pas joignable."""
    import httpx

    from mini_rag.config import Settings

    url = Settings().ollama_url  # la même adresse que le reste du projet (variable OLLAMA_URL ou .env)
    try:
        httpx.get(f"{url}/api/version", timeout=2.0)
    except httpx.HTTPError:
        pytest.skip("Ollama n'est pas joignable : test d'intégration sauté")
    return url
