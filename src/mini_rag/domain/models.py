"""Les trois types de base : où est un passage (Source), une page lue (PageText), un extrait (Chunk)."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Source:
    """Où se trouve un passage : de quoi le citer (fichier + page)."""

    file: str
    page: int  # numéro de page, à partir de 1

    def __post_init__(self) -> None:
        # Appelé juste après la création de l'objet : on refuse une page invalide dès le départ.
        if self.page < 1:
            raise ValueError(f"Les pages commencent à 1, reçu : {self.page}")


@dataclass(frozen=True)
class PageText:
    """Le texte d'une page entière, tel que lu dans le PDF."""

    source: Source
    text: str


@dataclass(frozen=True)
class Chunk:
    """Un morceau de page, prêt à être indexé, qui garde sa source."""

    text: str
    source: Source
    index: int  # rang du chunk dans sa page, à partir de 0

    @property
    def id(self) -> str:
        """Identifiant stable et unique : `<fichier>#p<page>-c<n>`."""
        return f"{self.source.file}#p{self.source.page}-c{self.index}"
