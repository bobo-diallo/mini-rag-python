"""Génération de texte en local par Ollama (`POST /api/generate`) : aucun texte ne quitte ta machine."""

import httpx

from mini_rag.generation.chat_model import ChatModel, Completion, GenerationError, TokenUsage


class OllamaChatModel(ChatModel):
    """Envoie un prompt à un modèle d'Ollama (par exemple `llama3.2:3b`) et rend sa réponse."""

    def __init__(
        self,
        model: str,
        base_url: str,
        num_ctx: int,
        max_output_tokens: int,
        timeout: float = 120.0,
        client: httpx.Client | None = None,
    ) -> None:
        self._model = model
        self._base_url = base_url.rstrip("/")
        self._num_ctx = num_ctx  # fenêtre de contexte : au-delà, Ollama tronque le prompt en silence
        self._max_output_tokens = max_output_tokens
        self._timeout = timeout
        self._client = client or httpx.Client(timeout=timeout)

    def generate(self, prompt: str) -> Completion:
        if prompt.strip() == "":
            raise ValueError("Prompt vide : rien à envoyer au modèle.")

        body = {
            "model": self._model,
            "prompt": prompt,
            "stream": False,  # une seule réponse complète, pas un flux de morceaux
            # Température 0 : réponses les plus stables et factuelles, ce qu'on veut face à des documents.
            "options": {"temperature": 0, "num_ctx": self._num_ctx, "num_predict": self._max_output_tokens},
        }
        try:
            response = self._client.post(f"{self._base_url}/api/generate", json=body)
        except httpx.TimeoutException as error:
            raise GenerationError(
                f"Ollama n'a pas répondu à temps (plus de {self._timeout:g} s) : le modèle est peut-être "
                "en cours de chargement, ou trop lent pour ce prompt."
            ) from error
        except httpx.HTTPError as error:
            raise GenerationError(
                f"Ollama injoignable à {self._base_url} ({error}). Le serveur est-il lancé (`ollama serve`) ?"
            ) from error

        if response.is_error:
            raise GenerationError(self._describe_http_error(response))

        data = response.json()
        text = data.get("response")
        if not isinstance(text, str):
            raise GenerationError("Réponse d'Ollama inattendue : la clé « response » est absente ou n'est pas du texte.")
        return Completion(text=text, tokens=self._read_tokens(data))

    @staticmethod
    def _read_tokens(data: dict) -> TokenUsage | None:
        prompt, generated = data.get("prompt_eval_count"), data.get("eval_count")
        if isinstance(prompt, int) and isinstance(generated, int):
            return TokenUsage(prompt=prompt, generated=generated)
        return None

    def _describe_http_error(self, response: httpx.Response) -> str:
        """Le message du serveur, plus la commande qui règle le cas le plus fréquent (modèle absent)."""
        try:
            detail = response.json().get("error", response.text)
        except ValueError:
            detail = response.text
        message = f"Ollama a répondu {response.status_code} : {detail}"
        if response.status_code == 404:
            message += f" — essayez `ollama pull {self._model}`."
        return message
