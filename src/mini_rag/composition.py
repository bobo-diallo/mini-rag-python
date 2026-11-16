"""Le point d'assemblage : le seul endroit qui connaît toutes les pièces et les branche ensemble.

Les autres modules ne dépendent que d'interfaces ; ici, on choisit les vraies implémentations (Ollama)
à partir des réglages. Les tests et les commandes peuvent y substituer des faux.
"""

from collections.abc import Sequence

from mini_rag.config import Settings
from mini_rag.domain.models import Chunk
from mini_rag.generation.answerer import Answerer, AnswerOptions
from mini_rag.generation.chat_model import ChatModel
from mini_rag.generation.ollama_chat_model import OllamaChatModel
from mini_rag.retrieval.embedder import Embedder
from mini_rag.retrieval.ollama_embedder import OllamaEmbedder
from mini_rag.retrieval.retriever import Retriever
from mini_rag.retrieval.vector_store import InMemoryVectorStore


def build_answerer(
    chunks: Sequence[Chunk],
    settings: Settings,
    *,
    embedder: Embedder | None = None,
    chat_model: ChatModel | None = None,
) -> Answerer:
    """Indexe les chunks et rend un Answerer prêt à répondre. `embedder` et `chat_model` remplacent Ollama (tests)."""
    embedder = embedder or OllamaEmbedder(model=settings.embedding_model, base_url=settings.ollama_url)
    chat_model = chat_model or OllamaChatModel(
        model=settings.chat_model,
        base_url=settings.ollama_url,
        num_ctx=settings.num_ctx,
        max_output_tokens=settings.max_output_tokens,
    )
    retriever = Retriever(embedder, InMemoryVectorStore(), settings.embedding_batch_size)
    retriever.index(chunks)
    options = AnswerOptions(
        k=settings.top_k,
        min_score=settings.min_score,
        context_limit=settings.num_ctx,
        max_output_tokens=settings.max_output_tokens,
    )
    return Answerer(retriever, chat_model, options)
