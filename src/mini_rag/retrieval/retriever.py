"""Le Retriever assemble les trois pièces : embedder (texte vers vecteur), index (rangement), similarité."""

from collections.abc import Callable, Sequence

from mini_rag.domain.models import Chunk, SearchResult
from mini_rag.retrieval.embedder import Embedder, embed_in_batches
from mini_rag.retrieval.vector_store import InMemoryVectorStore


class Retriever:
    """Indexe des chunks, puis retrouve ceux dont le sens est le plus proche d'une question.

    Il reçoit ses pièces par le constructeur (injection de dépendances) : il ne sait pas quel modèle
    calcule les vecteurs, ni comment ils sont comparés.
    """

    def __init__(self, embedder: Embedder, store: InMemoryVectorStore, batch_size: int) -> None:
        if batch_size < 1:  # on échoue dès la création plutôt qu'au premier appel à index()
            raise ValueError(f"La taille d'un lot doit être d'au moins 1 (reçu {batch_size}).")
        self._embedder = embedder
        self._store = store
        self._batch_size = batch_size

    def index(
        self, chunks: Sequence[Chunk], on_progress: Callable[[int, int], None] | None = None
    ) -> None:
        """Calcule le vecteur de chaque chunk (par lots) et les range dans l'index."""
        vectors = embed_in_batches(
            self._embedder, [chunk.text for chunk in chunks], self._batch_size, on_progress
        )
        self._store.add(chunks, vectors)

    def search(self, question: str, k: int) -> list[SearchResult]:
        """Les `k` chunks les plus proches de la question, du plus proche au plus éloigné."""
        return self._store.search(self._embedder.embed_query(question), k)
