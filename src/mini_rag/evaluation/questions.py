"""Les questions d'évaluation : un fichier JSON qui associe chaque question à la page où se trouve la réponse."""

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class EvalQuestion:
    question: str
    expected_page: int  # numéro de page (à partir de 1) qui contient la réponse


def load_questions(path: str | Path) -> list[EvalQuestion]:
    """Lit et valide le fichier ; chaque erreur dit quelle entrée est en cause."""
    content = json.loads(Path(path).read_text(encoding="utf-8"))  # FileNotFoundError si le fichier manque
    if not isinstance(content, list):
        raise ValueError("Le fichier de questions doit contenir une liste.")
    if not content:
        raise ValueError("Le fichier ne contient aucune question.")
    return [_parse_entry(number, entry) for number, entry in enumerate(content, start=1)]


def _parse_entry(number: int, entry: object) -> EvalQuestion:
    if not isinstance(entry, dict):
        raise ValueError(f"Entrée n° {number} : un objet est attendu.")
    question = entry.get("question")
    if not isinstance(question, str) or not question.strip():
        raise ValueError(f"Entrée n° {number} : « question » doit être un texte non vide.")
    page = entry.get("expected_page")
    # `bool` est un sous-type de `int` en Python : on l'écarte explicitement.
    if not isinstance(page, int) or isinstance(page, bool) or page < 1:
        raise ValueError(f"Entrée n° {number} : « expected_page » doit être un entier d'au moins 1.")
    return EvalQuestion(question=question, expected_page=page)


def load_out_of_scope_questions(path: str | Path) -> list[str]:
    """Questions dont les documents ne contiennent PAS la réponse : le bon comportement est de refuser."""
    content = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(content, list):
        raise ValueError("Le fichier de questions hors sujet doit contenir une liste.")
    if not content:
        raise ValueError("Le fichier ne contient aucune question hors sujet.")

    questions = []
    for number, entry in enumerate(content, start=1):
        text = entry.get("question") if isinstance(entry, dict) else None
        if not isinstance(text, str) or not text.strip():
            raise ValueError(f"Entrée n° {number} : « question » doit être un texte non vide.")
        questions.append(text)
    return questions
