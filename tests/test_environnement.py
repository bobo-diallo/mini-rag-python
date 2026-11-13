"""Test de départ : vérifie que l'environnement Python et le paquet sont bien en place."""

import sys

import mini_rag


def test_python_est_assez_recent():
    # tuple comparé à tuple : (3, 12, 4) >= (3, 12) est vrai.
    assert sys.version_info >= (3, 12)


def test_le_paquet_expose_sa_version():
    assert mini_rag.__version__ == "0.1.0"
