"""Tests de la configuration : les réglages viennent de l'environnement ou d'un fichier .env, jamais du code."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from mini_rag.config import Settings

REPOSITORY_ROOT = Path(__file__).parent.parent
SETTING_VARIABLES = ("OLLAMA_URL", "EMBEDDING_MODEL", "EMBEDDING_BATCH_SIZE")


@pytest.fixture(autouse=True)
def clean_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Retire du décor les variables qu'un développeur aurait pu définir, pour que le test soit prévisible."""
    for name in SETTING_VARIABLES:
        monkeypatch.delenv(name, raising=False)


def test_defaults_work_without_any_configuration():
    settings = Settings(_env_file=None)  # _env_file=None : ne lit aucun fichier .env

    assert settings.ollama_url == "http://localhost:11434"
    assert settings.embedding_model == "bge-m3"
    assert settings.embedding_batch_size == 16


def test_environment_variables_override_the_defaults(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("OLLAMA_URL", "http://serveur-ia:9999")
    monkeypatch.setenv("EMBEDDING_MODEL", "qwen3-embedding:0.6b")
    monkeypatch.setenv("EMBEDDING_BATCH_SIZE", "4")

    settings = Settings(_env_file=None)

    assert settings.ollama_url == "http://serveur-ia:9999"
    assert settings.embedding_model == "qwen3-embedding:0.6b"
    assert settings.embedding_batch_size == 4  # le texte « 4 » est converti en entier


def test_values_are_read_from_a_dot_env_file(tmp_path: Path):
    env_file = tmp_path / ".env"
    env_file.write_text("OLLAMA_URL=http://depuis-le-fichier:1234\nEMBEDDING_MODEL=embeddinggemma\n")

    settings = Settings(_env_file=env_file)

    assert settings.ollama_url == "http://depuis-le-fichier:1234"
    assert settings.embedding_model == "embeddinggemma"


def test_an_environment_variable_wins_over_the_dot_env_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    env_file = tmp_path / ".env"
    env_file.write_text("EMBEDDING_MODEL=depuis-le-fichier\n")
    monkeypatch.setenv("EMBEDDING_MODEL", "depuis-l-environnement")

    assert Settings(_env_file=env_file).embedding_model == "depuis-l-environnement"


def test_unknown_variables_in_the_dot_env_file_are_ignored(tmp_path: Path):
    env_file = tmp_path / ".env"
    env_file.write_text("UNE_AUTRE_VARIABLE=1\nEMBEDDING_MODEL=bge-m3\n")

    assert Settings(_env_file=env_file).embedding_model == "bge-m3"


@pytest.mark.parametrize("value", ["0", "-3", "beaucoup"])
def test_an_invalid_batch_size_is_rejected(monkeypatch: pytest.MonkeyPatch, value: str):
    monkeypatch.setenv("EMBEDDING_BATCH_SIZE", value)

    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_the_example_file_lists_exactly_the_variables_the_settings_know():
    # Le fichier .env.example est la documentation des réglages : il doit rester synchronisé avec le code.
    lines = (REPOSITORY_ROOT / ".env.example").read_text().splitlines()
    documented = {line.split("=")[0] for line in lines if line.strip() and not line.startswith("#")}

    assert documented == set(SETTING_VARIABLES)
    assert {name.upper() for name in Settings.model_fields} == set(SETTING_VARIABLES)
