"""L'Answerer : chercher des extraits, décider si on peut répondre, interroger le modèle, vérifier ses citations."""

import re
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

from mini_rag.domain.models import SearchResult
from mini_rag.generation.chat_model import ChatModel, TokenUsage
from mini_rag.generation.citations import resolve_citations
from mini_rag.generation.prompt import NO_ANSWER, build_prompt, estimate_tokens

# Le modèle a refusé de répondre s'il commence par ces mots (majuscules et espaces de tête ignorés).
REFUSAL_START = re.compile(r"\s*je ne sais pas", re.IGNORECASE)


class Searcher(Protocol):
    """Ce dont l'Answerer a besoin d'un moteur de recherche : savoir chercher, rien d'autre.

    C'est le consommateur qui définit l'interface : le vrai `Retriever` la respecte sans rien déclarer,
    et les tests y mettent un faux.
    """

    def search(self, question: str, k: int) -> list[SearchResult]: ...


@dataclass(frozen=True)
class AnswerOptions:
    """Réglages de la réponse. Tous obligatoires : les valeurs par défaut vivent dans `Settings`."""

    k: int  # nombre d'extraits demandés à la recherche
    min_score: float  # score minimal du meilleur extrait ; en dessous, on refuse sans appeler le modèle
    context_limit: int  # fenêtre de contexte demandée à Ollama (`num_ctx`), en tokens
    max_output_tokens: int  # place réservée à la réponse dans cette fenêtre, en tokens

    def __post_init__(self) -> None:
        if self.k < 1:
            raise ValueError(f"k doit valoir au moins 1 (reçu {self.k}).")
        if self.max_output_tokens < 1:
            raise ValueError(f"max_output_tokens doit valoir au moins 1 (reçu {self.max_output_tokens}).")
        if self.context_limit <= self.max_output_tokens:
            raise ValueError(
                f"La fenêtre ({self.context_limit}) doit être plus grande que la réponse réservée "
                f"({self.max_output_tokens}) : sinon il ne reste aucune place pour le prompt."
            )
        if not -1.0 <= self.min_score <= 1.0:
            raise ValueError(f"min_score est un cosinus, donc entre -1 et 1 (reçu {self.min_score}).")


@dataclass(frozen=True)
class Reply:
    text: str
    answered: bool  # False si les documents ne permettent pas de répondre
    citations: tuple[SearchResult, ...]  # sources vérifiées par le code, citées par le modèle
    invalid_citations: tuple[int, ...]  # numéros cités par le modèle qui n'existent pas
    retrieved: tuple[SearchResult, ...]  # tout ce que la recherche a retrouvé
    used_extracts: int  # extraits réellement mis dans le prompt (0 si le modèle n'a pas été appelé)
    tokens: TokenUsage | None = None


class Answerer:
    def __init__(self, searcher: Searcher, chat_model: ChatModel, options: AnswerOptions) -> None:
        self._searcher = searcher
        self._chat_model = chat_model
        self._options = options

    def answer(self, question: str) -> Reply:
        retrieved = tuple(self._searcher.search(question, self._options.k))

        # Pas assez proche : on ne demande même pas au modèle (ça évite de l'inviter à inventer, et ça ne coûte rien).
        if not self._is_answerable(retrieved):
            return self._unanswered(retrieved)

        used = self._fit_in_context(question, retrieved)
        completion = self._chat_model.generate(build_prompt(question, [r.chunk for r in used]))
        text = completion.text.strip()

        if REFUSAL_START.match(text):
            return self._unanswered(retrieved, used_extracts=len(used), tokens=completion.tokens)

        resolved = resolve_citations(text, used)  # on ne vérifie que les extraits réellement envoyés
        return Reply(
            text=text,
            answered=True,
            citations=resolved.cited,
            invalid_citations=resolved.invalid,
            retrieved=retrieved,
            used_extracts=len(used),
            tokens=completion.tokens,
        )

    def _is_answerable(self, retrieved: Sequence[SearchResult]) -> bool:
        return bool(retrieved) and max(r.score for r in retrieved) >= self._options.min_score

    def _fit_in_context(self, question: str, retrieved: Sequence[SearchResult]) -> Sequence[SearchResult]:
        """Garde les meilleurs extraits tant que prompt + réponse tiennent dans la fenêtre (au moins un)."""
        budget = self._options.context_limit - self._options.max_output_tokens
        count = len(retrieved)
        while count > 1 and estimate_tokens(build_prompt(question, [r.chunk for r in retrieved[:count]])) > budget:
            count -= 1
        return retrieved[:count]

    @staticmethod
    def _unanswered(
        retrieved: tuple[SearchResult, ...], used_extracts: int = 0, tokens: TokenUsage | None = None
    ) -> Reply:
        return Reply(
            text=NO_ANSWER,
            answered=False,
            citations=(),
            invalid_citations=(),
            retrieved=retrieved,
            used_extracts=used_extracts,
            tokens=tokens,
        )
