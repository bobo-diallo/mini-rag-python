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


def _split_text(text: str, options: ChunkOptions) -> list[str]:
    if len(text) <= options.size:
        return [text]
    raise NotImplementedError("Découpage des textes longs : prochain test.")
