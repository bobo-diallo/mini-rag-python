"""Index vectoriel en mémoire : on y range des chunks avec leur vecteur, puis on cherche les plus proches."""

from collections.abc import Sequence

from mini_rag.domain.models import Chunk, SearchResult
from mini_rag.retrieval.similarity import cosine_similarity


class InMemoryVectorStore:
    """Garde les chunks et leurs vecteurs dans des listes ; disparaît à la fin du programme.

    La recherche compare la question à *tous* les vecteurs un par un : simple et suffisant pour
    quelques milliers de chunks. L'index persistant (story 04) viendra pour aller plus loin.
    """

    def __init__(self) -> None:
        self._chunks: list[Chunk] = []
        self._vectors: list[Sequence[float]] = []

    def __len__(self) -> int:
        return len(self._chunks)

    def add(self, chunks: Sequence[Chunk], vectors: Sequence[Sequence[float]]) -> None:
        """Ajoute des chunks avec leur vecteur (le chunk n° i va avec le vecteur n° i)."""
        if len(chunks) != len(vectors):
            raise ValueError(f"{len(chunks)} chunks pour {len(vectors)} vecteurs : il en faut autant.")
        # Dimension de référence : celle de l'index s'il contient déjà des vecteurs, sinon celle du lot.
        reference = len(self._vectors[0]) if self._vectors else (len(vectors[0]) if vectors else 0)
        for vector in vectors:
            self._check_dimension(vector, reference)
        self._chunks.extend(chunks)
        self._vectors.extend(vectors)

    def search(self, query_vector: Sequence[float], k: int) -> list[SearchResult]:
        """Rend les `k` chunks les plus proches de la question, du plus proche au plus éloigné."""
        if k < 1:
            raise ValueError(f"k doit valoir au moins 1 (reçu {k}).")
        if not self._chunks:
            return []
        self._check_dimension(query_vector, len(self._vectors[0]))

        results = [
            SearchResult(chunk=chunk, score=cosine_similarity(query_vector, vector))
            for chunk, vector in zip(self._chunks, self._vectors)
        ]
        # `sorted` est stable : à score égal, l'ordre d'ajout est conservé.
        results.sort(key=lambda result: result.score, reverse=True)
        return results[:k]

    @staticmethod
    def _check_dimension(vector: Sequence[float], expected: int) -> None:
        """Tous les vecteurs d'un index ont la même dimension."""
        if len(vector) != expected:
            raise ValueError(f"Dimension {len(vector)} reçue, mais {expected} était attendue.")
