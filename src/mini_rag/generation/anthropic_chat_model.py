"""Génération de texte par Claude (API d'Anthropic) : le calcul se fait à distance, pas sur ta machine.

Attention : les extraits du prompt quittent ta machine. Voir la règle du projet sur les documents confidentiels.
"""

import anthropic

from mini_rag.generation.chat_model import ChatModel, Completion, GenerationError, TokenUsage


class AnthropicChatModel(ChatModel):
    """Envoie un prompt à un modèle Claude (par défaut Haiku 5.5) et rend sa réponse."""

    def __init__(
        self,
        model: str,
        max_output_tokens: int,
        api_key: str | None = None,
        timeout: float = 120.0,
        effort: str = "low",
        client: anthropic.Anthropic | None = None,
    ) -> None:
        if client is None:
            if not api_key or not api_key.strip():
                raise ValueError("Il manque la clé d'API Anthropic (variable ANTHROPIC_API_KEY).")
            client = anthropic.Anthropic(api_key=api_key, timeout=timeout)  # 2 nouvelles tentatives automatiques
        self._client = client
        self._model = model
        self._max_output_tokens = max_output_tokens
        # Claude réfléchit avant de répondre ; `effort` règle la profondeur. « low » : réponses courtes, peu coûteuses.
        self._effort = effort

    def generate(self, prompt: str) -> Completion:
        if prompt.strip() == "":
            raise ValueError("Prompt vide : rien à envoyer au modèle.")

        # Pas de `temperature` : les modèles Claude récents n'acceptent pas de la modifier.
        try:
            response = self._client.messages.create(
                model=self._model,
                max_tokens=self._max_output_tokens,
                output_config={"effort": self._effort},
                messages=[{"role": "user", "content": prompt}],
            )
        except anthropic.AuthenticationError as error:
            raise GenerationError(
                "Clé d'API refusée par Anthropic : ANTHROPIC_API_KEY est invalide ou révoquée."
            ) from error
        except anthropic.PermissionDeniedError as error:
            raise GenerationError(f"Accès refusé par Anthropic pour le modèle {self._model} : {error.message}") from error
        except anthropic.NotFoundError as error:
            raise GenerationError(f"Modèle introuvable chez Anthropic : {self._model}. {error.message}") from error
        except anthropic.RateLimitError as error:
            raise GenerationError("Limite de débit atteinte chez Anthropic : réessayez dans un moment.") from error
        except anthropic.APITimeoutError as error:  # avant APIConnectionError : un délai dépassé en est un cas particulier
            raise GenerationError("Anthropic n'a pas répondu à temps : réessayez, ou allongez CHAT_TIMEOUT.") from error
        except anthropic.APIConnectionError as error:
            raise GenerationError(
                "Anthropic injoignable : vérifiez votre connexion à Internet."
            ) from error
        except anthropic.APIStatusError as error:
            raise GenerationError(f"Anthropic a répondu {error.status_code} : {error.message}") from error

        if response.stop_reason == "refusal":
            details = response.stop_details
            category = getattr(details, "category", None) or "non précisée"
            raise GenerationError(f"Claude a refusé de répondre (catégorie : {category}).")

        text = "".join(block.text for block in response.content if block.type == "text")
        if not text:
            raise GenerationError("Réponse de Claude sans texte (aucun bloc de texte reçu).")
        usage = response.usage
        return Completion(text=text, tokens=TokenUsage(prompt=usage.input_tokens, generated=usage.output_tokens))
