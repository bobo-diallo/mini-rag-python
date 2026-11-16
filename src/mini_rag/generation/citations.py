"""Relier les « [n] » d'une réponse aux extraits réellement fournis : la source vient du code, jamais du modèle."""

import re
from collections.abc import Sequence
from dataclasses import dataclass

from mini_rag.domain.models import SearchResult

# Un groupe entre crochets : « [2] », « [1, 2] », « [1;2] ». Pas « [note] », « [1 2] » ni « [1 ».
CITATION_GROUP = re.compile(r"\[(\d+(?:\s*[,;]\s*\d+)*)\]")


@dataclass(frozen=True)
class ResolvedCitations:
    cited: tuple[SearchResult, ...]  # sources réellement citées, sans doublon, dans l'ordre d'apparition
    invalid: tuple[int, ...]  # numéros cités qui ne correspondent à aucun extrait : invention à signaler


def resolve_citations(answer: str, sources: Sequence[SearchResult]) -> ResolvedCitations:
    """Les extraits sont numérotés à partir de 1 dans le prompt : « [1] » désigne `sources[0]`."""
    cited: list[SearchResult] = []
    invalid: list[int] = []
    seen: set[int] = set()  # numéros déjà traités : un même numéro n'est compté qu'une fois

    for group in CITATION_GROUP.finditer(answer):
        for number in (int(part) for part in re.split(r"[,;]", group.group(1))):
            if number in seen:
                continue
            seen.add(number)
            # Bornes explicites : sans elles, sources[0 - 1] serait sources[-1], le DERNIER élément.
            if 1 <= number <= len(sources):
                cited.append(sources[number - 1])
            else:
                invalid.append(number)
    return ResolvedCitations(cited=tuple(cited), invalid=tuple(invalid))
