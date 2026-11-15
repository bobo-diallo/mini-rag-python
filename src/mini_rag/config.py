"""Configuration centralisée : les réglages viennent de l'environnement ou d'un fichier `.env`, jamais du code.

Ordre de priorité (du plus fort au plus faible) :
1. les variables d'environnement du terminal ou du serveur ;
2. le fichier `.env` (personnel, jamais commité ; modèle : `.env.example`) ;
3. les valeurs par défaut ci-dessous.
"""

from pydantic import Field
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
