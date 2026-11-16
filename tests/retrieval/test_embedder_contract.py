"""Tests du contrat Embedder : une classe qui le déclare doit en respecter toutes les méthodes."""

import pytest

from mini_rag.retrieval.embedder import Embedder
from mini_rag.retrieval.ollama_embedder import OllamaEmbedder


def test_ollama_embedder_declares_that_it_implements_the_contract():
    # __mro__ liste la classe puis tous ses parents : Embedder doit y figurer.
    assert Embedder in OllamaEmbedder.__mro__


def test_a_class_declaring_the_contract_but_forgetting_a_method_cannot_be_created():
    class Forgetful(Embedder):
        def embed_documents(self, texts):
            return []

        # embed_query est oubliée

    with pytest.raises(TypeError, match="embed_query"):
        Forgetful()


def test_a_class_declaring_the_contract_and_implementing_it_can_be_created():
    class Complete(Embedder):
        def embed_documents(self, texts):
            return []

        def embed_query(self, text):
            return []

    assert Complete().embed_query("x") == []
