"""Similarité cosinus : mesure à quel point deux vecteurs pointent dans la même direction."""

import math
from collections.abc import Sequence


def cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
    """Rend 1 si les vecteurs ont la même direction (sens proche), 0 s'ils sont sans rapport, -1 s'ils sont opposés.

    La longueur des vecteurs ne compte pas : seul l'angle entre eux est mesuré.
    """
    if len(a) != len(b):
        raise ValueError(f"Dimensions différentes : {len(a)} contre {len(b)}.")

    dot = sum(x * y for x, y in zip(a, b))  # produit scalaire : somme des produits terme à terme
    norm_a = math.sqrt(sum(x * x for x in a))  # longueur du vecteur a
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        raise ValueError("Vecteur nul : sa direction est indéfinie.")
    return dot / (norm_a * norm_b)
