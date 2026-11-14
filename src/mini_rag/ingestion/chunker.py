"""Découpe des pages en chunks. Un chunk ne franchit jamais une page : sa citation reste exacte."""

from collections.abc import Sequence
from dataclasses import dataclass

from mini_rag.domain.models import Chunk, PageText


@dataclass(frozen=True)
class ChunkOptions:
    """Réglages du découpage, en caractères. Valeurs de départ : 1000 / 200, qu'on mesurera plus tard."""

    size: int = 1000  # taille maximale d'un chunk
    overlap: int = 200  # caractères répétés entre deux chunks consécutifs

    def __post_init__(self) -> None:
        if self.overlap >= self.size:
            raise ValueError(
                f"Le chevauchement ({self.overlap}) doit être inférieur à la taille ({self.size})."
            )


def chunk_pages(pages: Sequence[PageText], options: ChunkOptions = ChunkOptions()) -> list[Chunk]:
    """Découpe chaque page séparément ; les pages vides sont ignorées."""
    chunks: list[Chunk] = []
    for page in pages:
        if page.text.strip() == "":
            continue
        for index, piece in enumerate(_split_text(page.text, options)):
            chunks.append(Chunk(text=piece, source=page.source, index=index))
    return chunks


# Du plus naturel au moins naturel : paragraphe, ligne, mot, puis caractère en dernier recours.
SEPARATORS = ("\n\n", "\n", " ", "")


def _split_text(text: str, options: ChunkOptions, separators: Sequence[str] = SEPARATORS) -> list[str]:
    """Découpage récursif : on coupe au séparateur le plus naturel présent dans le texte.

    Les morceaux assez petits sont recollés par `_merge` jusqu'à approcher la taille visée ;
    un morceau trop grand est redécoupé avec les séparateurs suivants (d'où « récursif »).
    """
    # 1. Premier séparateur réellement présent dans le texte ("" = couper caractère par caractère).
    separator, remaining = separators[-1], ()
    for position, candidate in enumerate(separators):
        if candidate == "":
            separator = candidate
            break
        if candidate in text:
            separator, remaining = candidate, separators[position + 1 :]
            break

    # 2. Coupe, puis tri : petits morceaux d'un côté, trop grands de l'autre.
    chunks: list[str] = []
    small: list[str] = []
    for piece in _cut_before_separator(text, separator):
        if len(piece) < options.size:
            small.append(piece)
            continue
        chunks.extend(_merge(small, options))
        small = []
        if remaining:
            chunks.extend(_split_text(piece, options, remaining))  # on redécoupe plus finement
        else:
            chunks.append(piece)  # plus aucun séparateur : on garde tel quel
    chunks.extend(_merge(small, options))
    return chunks


def _cut_before_separator(text: str, separator: str) -> list[str]:
    """Coupe le texte à chaque séparateur, qui reste collé au début du morceau suivant."""
    if separator == "":
        return list(text)
    first, *others = text.split(separator)
    pieces = [first] + [separator + other for other in others]
    return [piece for piece in pieces if piece != ""]


def _merge(pieces: Sequence[str], options: ChunkOptions) -> list[str]:
    """Recolle des petits morceaux en chunks d'au plus `size` caractères, avec chevauchement."""
    merged: list[str] = []
    current: list[str] = []  # morceaux du chunk en cours de construction
    total = 0  # longueur cumulée des morceaux de `current`

    for piece in pieces:
        if total + len(piece) > options.size and current:
            _keep_non_empty(merged, "".join(current))
            # On retire des morceaux au début pour ne garder que le chevauchement, et assez de place.
            while total > options.overlap or (total + len(piece) > options.size and total > 0):
                total -= len(current[0])
                current = current[1:]
        current.append(piece)
        total += len(piece)

    _keep_non_empty(merged, "".join(current))
    return merged


def _keep_non_empty(destination: list[str], text: str) -> None:
    """Ajoute le texte nettoyé des blancs de début et de fin, sauf s'il est vide."""
    cleaned = text.strip()
    if cleaned:
        destination.append(cleaned)
