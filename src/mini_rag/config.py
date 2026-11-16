"""Configuration centralisée : les réglages viennent de l'environnement ou d'un fichier `.env`, jamais du code.

Ordre de priorité (du plus fort au plus faible) :
1. les variables d'environnement du terminal ou du serveur ;
2. le fichier `.env` (personnel, jamais commité ; modèle : `.env.example`) ;
3. les valeurs par défaut ci-dessous.
"""

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Réglages du projet. Chaque champ se règle par la variable du même nom en MAJUSCULES."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # une variable inconnue dans .env n'est pas une erreur
    )

    ollama_url: str = "http://localhost:11434"
    embedding_model: str = "bge-m3"
    embedding_batch_size: int = Field(default=16, ge=1)  # ge=1 : au moins 1 texte par lot

    # Génération des réponses. Valeurs de départ reprises de la version TypeScript : on les mesure, on ne les croit pas.
    chat_model: str = "llama3.2:3b"
    num_ctx: int = Field(default=4096, ge=1)  # fenêtre de contexte demandée à Ollama, en tokens
    max_output_tokens: int = Field(default=512, ge=1)  # place réservée à la réponse dans cette fenêtre
    top_k: int = Field(default=4, ge=1)  # nombre d'extraits retrouvés pour chaque question
    min_score: float = Field(default=0.55, ge=-1.0, le=1.0)  # en dessous, on répond « je ne sais pas » sans appeler le modèle

    @model_validator(mode="after")
    def _the_window_leaves_room_for_the_prompt(self) -> "Settings":
        if self.num_ctx <= self.max_output_tokens:
            raise ValueError(
                f"La fenêtre NUM_CTX ({self.num_ctx}) doit être plus grande que MAX_OUTPUT_TOKENS "
                f"({self.max_output_tokens}) : sinon il ne reste aucune place pour le prompt."
            )
        return self
