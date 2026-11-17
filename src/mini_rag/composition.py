"""Le point d'assemblage : le seul endroit qui connaît toutes les pièces et les branche ensemble.

Les autres modules ne dépendent que d'interfaces ; ici, on choisit les vraies implémentations (Ollama)
à partir des réglages. Les tests et les commandes peuvent y substituer des faux.
"""

from collections.abc import Sequence

from mini_rag.config import ConfigurationError, Settings
from mini_rag.domain.models import Chunk
from mini_rag.generation.answerer import Answerer, AnswerOptions
from mini_rag.generation.anthropic_chat_model import AnthropicChatModel
from mini_rag.generation.chat_model import ChatModel
from mini_rag.generation.ollama_chat_model import OllamaChatModel
from mini_rag.retrieval.embedder import Embedder
from mini_rag.retrieval.ollama_embedder import OllamaEmbedder
from mini_rag.retrieval.retriever import Retriever
from mini_rag.retrieval.vector_store import InMemoryVectorStore


def build_chat_model(settings: Settings) -> ChatModel:
    """Le modèle qui rédige les réponses, choisi par `CHAT_PROVIDER` : Ollama (local) ou Claude (à distance)."""
    if settings.chat_provider == "anthropic":
        key = settings.anthropic_api_key.get_secret_value().strip() if settings.anthropic_api_key else ""
        if not key:
            raise ConfigurationError(
                "CHAT_PROVIDER=anthropic exige une clé d'API : définissez ANTHROPIC_API_KEY dans votre fichier .env "
                "(ou dans l'environnement). Voir .env.example."
            )
        return AnthropicChatModel(
            model=settings.anthropic_model,
            max_output_tokens=settings.max_output_tokens,
            api_key=key,
            timeout=settings.chat_timeout,
        )
    return OllamaChatModel(
        model=settings.chat_model,
        base_url=settings.ollama_url,
        num_ctx=settings.num_ctx,
        max_output_tokens=settings.max_output_tokens,
        timeout=settings.chat_timeout,
    )


def build_answerer(
    chunks: Sequence[Chunk],
    settings: Settings,
    *,
    embedder: Embedder | None = None,
    chat_model: ChatModel | None = None,
) -> Answerer:
    """Indexe les chunks et rend un Answerer prêt à répondre. `embedder` et `chat_model` remplacent Ollama (tests)."""
    # Le modèle de génération d'abord : s'il est mal configuré, on échoue avant de calculer le moindre vecteur.
    chat_model = chat_model or build_chat_model(settings)
    embedder = embedder or OllamaEmbedder(model=settings.embedding_model, base_url=settings.ollama_url)
    retriever = Retriever(embedder, InMemoryVectorStore(), settings.embedding_batch_size)
    retriever.index(chunks)
    options = AnswerOptions(
        k=settings.top_k,
        min_score=settings.min_score,
        context_limit=settings.num_ctx,
        max_output_tokens=settings.max_output_tokens,
    )
    return Answerer(retriever, chat_model, options)
