"""Le contrat d'un modèle de langage : un prompt entre, du texte sort. Aucun modèle précis ici."""

from abc import abstractmethod
from dataclasses import dataclass
from typing import Protocol


class GenerationError(RuntimeError):
    """La génération a échoué (serveur absent, modèle introuvable, réponse inattendue...).

    Tout modèle lève cette erreur-là : le reste du code n'a pas à connaître celles de `httpx`.
    """


@dataclass(frozen=True)
class TokenUsage:
    """Les tokens consommés par un appel : ce qui est facturé chez un service payant."""

    prompt: int  # tokens lus par le modèle (le prompt)
    generated: int  # tokens écrits par le modèle (la réponse)

    @property
    def total(self) -> int:
        return self.prompt + self.generated


@dataclass(frozen=True)
class Completion:
    """Ce que rend un modèle : le texte, et le décompte de tokens quand il le fournit."""

    text: str
    tokens: TokenUsage | None  # None si le modèle ne le dit pas : on ne l'invente jamais


class ChatModel(Protocol):
    """Tout objet qui sait répondre à un prompt. Le reste du code dépend de ce contrat, pas d'un modèle."""

    @abstractmethod
    def generate(self, prompt: str) -> Completion:
        """Envoie le prompt et rend la réponse."""
        ...
