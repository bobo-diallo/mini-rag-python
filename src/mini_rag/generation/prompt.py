"""Le prompt : ce qu'on envoie au modèle. Consigne stricte + extraits numérotés + question."""

import math
from collections.abc import Sequence

from mini_rag.domain.models import Chunk

# Phrase fixe pour « les documents ne le disent pas » : le modèle la reprend, le code la reconnaît.
NO_ANSWER = "Je ne sais pas : les documents fournis ne contiennent pas cette information."


def estimate_tokens(text: str) -> int:
    """Estimation volontairement pessimiste (3 caractères par token).

    On préfère retirer un extrait de trop que laisser Ollama tronquer le prompt en silence.
    """
    return math.ceil(len(text) / 3)


def build_prompt(question: str, extracts: Sequence[Chunk]) -> str:
    """Consigne, puis extraits numérotés, puis question. Les numéros servent à citer : le code retrouve la source."""
    if not extracts:
        raise ValueError("Prompt impossible : aucun extrait à fournir au modèle.")

    numbered = "\n\n".join(f"[{number}] {chunk.text}" for number, chunk in enumerate(extracts, start=1))
    return "\n".join(
        [
            "Tu es un assistant qui répond en français, uniquement à partir des extraits numérotés ci-dessous.",
            "",
            "Règles :",
            "- Utilise uniquement les extraits : aucune connaissance extérieure.",
            "- Cite les extraits que tu utilises avec leur numéro entre crochets, par exemple [1] ou [2].",
            f"- Si les extraits ne contiennent pas la réponse, réponds exactement : « {NO_ANSWER} »",
            "",
            "Extraits :",
            numbered,
            "",
            f"Question : {question}",
            "Réponse :",
        ]
    )
