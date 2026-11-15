"""Embeddings calculés en local par Ollama (modèle `bge-m3` par défaut)."""

from collections.abc import Sequence

import httpx

from mini_rag.retrieval.embedder import EmbeddingError


class OllamaEmbedder:
    """Appelle l'API d'Ollama (`POST /api/embed`) : aucun texte ne quitte ta machine."""

    def __init__(
        self,
        model: str = "bge-m3",
        base_url: str = "http://localhost:11434",
        timeout: float = 60.0,
        client: httpx.Client | None = None,
    ) -> None:
        self._model = model
        self._base_url = base_url.rstrip("/")  # tolère « http://hote:11434/ » avec un / final
        # Le client HTTP peut être fourni de l'extérieur : les tests y branchent un faux serveur.
        self._client = client or httpx.Client(timeout=timeout)

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []  # rien à calculer : on évite un appel réseau inutile

        url = f"{self._base_url}/api/embed"
        try:
            response = self._client.post(url, json={"model": self._model, "input": list(texts)})
        except httpx.HTTPError as error:
            raise EmbeddingError(
                f"Ollama injoignable à {self._base_url} ({error}). Le serveur est-il lancé (`ollama serve`) ?"
            ) from error

        if response.is_error:
            raise EmbeddingError(self._describe_http_error(response))

        embeddings = response.json().get("embeddings")
        if embeddings is None:
            raise EmbeddingError("Réponse d'Ollama inattendue : la clé « embeddings » est absente.")
        if len(embeddings) != len(texts):
            raise EmbeddingError(f"Ollama a rendu {len(embeddings)} vecteurs pour {len(texts)} textes.")
        return embeddings

    def embed_query(self, text: str) -> list[float]:
        return self.embed_documents([text])[0]

    def _describe_http_error(self, response: httpx.Response) -> str:
        """Le message du serveur, plus la commande qui règle le cas le plus fréquent (modèle absent)."""
        try:
            detail = response.json().get("error", response.text)
        except ValueError:  # la réponse n'est pas du JSON
            detail = response.text
        message = f"Ollama a répondu {response.status_code} : {detail}"
        if response.status_code == 404:
            message += f" — essayez `ollama pull {self._model}`."
        return message
