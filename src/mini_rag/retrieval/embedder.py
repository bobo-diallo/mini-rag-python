"""Embeddings : transformer du texte en vecteurs qui représentent son sens."""

from collections.abc import Callable, Sequence
from typing import Protocol


class Embedder(Protocol):
    """Tout objet qui sait transformer du texte en vecteurs.

    C'est une *interface* : le reste du code dépend de ces deux méthodes, jamais d'un modèle précis.
    Changer de modèle (Ollama, Hugging Face...) ou utiliser un faux dans les tests ne touche donc
    à aucune autre ligne. Un `Protocol` n'a pas besoin qu'on déclare « implémente Embedder » :
    il suffit d'avoir les bonnes méthodes (typage « structurel »).
    """

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        """Un vecteur par texte, dans le même ordre."""
        ...

    def embed_query(self, text: str) -> list[float]:
        """Le vecteur d'une question."""
        ...


def embed_in_batches(
    embedder: Embedder,
    texts: Sequence[str],
    batch_size: int,
    on_progress: Callable[[int, int], None] | None = None,
) -> list[list[float]]:
    """Calcule les embeddings par lots (Ollama reçoit quelques textes à la fois, pas des centaines).

    Rend les vecteurs dans l'ordre des textes. `on_progress(fait, total)` est appelé après chaque lot.
    """
    if batch_size < 1:
        raise ValueError(f"La taille d'un lot doit être d'au moins 1 (reçu {batch_size}).")

    vectors: list[list[float]] = []
    for start in range(0, len(texts), batch_size):
        batch = texts[start : start + batch_size]
        vectors.extend(embedder.embed_documents(batch))
        if on_progress is not None:
            on_progress(start + len(batch), len(texts))
    return vectors
