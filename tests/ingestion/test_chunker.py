"""Tests du découpeur : cas simples, texte long, coupures naturelles, comparaison avec LangChain."""

import pytest
from langchain_text_splitters import RecursiveCharacterTextSplitter

from mini_rag.domain.models import PageText, Source
from mini_rag.ingestion.chunker import ChunkOptions, chunk_pages


def page(text: str, number: int = 1, file: str = "doc.pdf") -> PageText:
    return PageText(source=Source(file=file, page=number), text=text)


# --- Cas simples : page vide, texte court, réglages invalides ----------------------------------


def test_default_settings_are_1000_and_200():
    options = ChunkOptions()

    assert options.size == 1000
    assert options.overlap == 200


def test_an_overlap_equal_to_or_above_the_size_is_rejected():
    with pytest.raises(ValueError):
        ChunkOptions(size=100, overlap=100)


def test_an_empty_or_blank_page_gives_no_chunk():
    chunks = chunk_pages([page(""), page("   \n  ", number=2)])

    assert chunks == []


def test_a_short_text_gives_a_single_chunk_with_its_source():
    chunks = chunk_pages([page("Un texte court.", number=3)])

    assert len(chunks) == 1
    assert chunks[0].text == "Un texte court."
    assert chunks[0].id == "doc.pdf#p3-c0"


def test_chunk_index_restarts_at_zero_on_each_page():
    chunks = chunk_pages([page("Page un.", number=1), page("Page deux.", number=2)])

    assert [c.id for c in chunks] == ["doc.pdf#p1-c0", "doc.pdf#p2-c0"]


# --- Texte long : chevauchement ----------------------------------------------------------------

# Texte sans espaces ni répétition : chaque bloc de 4 chiffres est unique,
# donc un décalage d'un seul caractère dans un chunk serait détecté.
LONG_TEXT = "".join(f"{i:04d}" for i in range(625))  # 2500 caractères


def test_a_long_text_is_split_with_overlap():
    chunks = chunk_pages([page(LONG_TEXT)])

    # pas = taille - chevauchement = 800 : débuts aux positions 0, 800 et 1600
    assert [c.text for c in chunks] == [
        LONG_TEXT[0:1000],
        LONG_TEXT[800:1800],
        LONG_TEXT[1600:2500],
    ]


def test_no_chunk_exceeds_the_size():
    chunks = chunk_pages([page(LONG_TEXT)])

    assert all(len(c.text) <= 1000 for c in chunks)


def test_the_end_of_a_chunk_is_repeated_at_the_start_of_the_next_one():
    chunks = chunk_pages([page(LONG_TEXT)])

    assert chunks[0].text[-200:] == chunks[1].text[:200]


def test_no_useless_chunk_when_the_text_ends_exactly():
    # taille 10, chevauchement 3, texte de 17 caractères : [0:10] puis [7:17], et on s'arrête
    text = "0123456789ABCDEFG"

    chunks = chunk_pages([page(text)], ChunkOptions(size=10, overlap=3))

    assert [c.text for c in chunks] == ["0123456789", "789ABCDEFG"]


def test_ids_of_a_same_page_are_numbered_in_order():
    chunks = chunk_pages([page(LONG_TEXT, number=4)])

    assert [c.id for c in chunks] == ["doc.pdf#p4-c0", "doc.pdf#p4-c1", "doc.pdf#p4-c2"]


# --- Coupures naturelles : paragraphes, lignes, mots -------------------------------------------


def test_cuts_at_the_paragraph_break_rather_than_in_the_middle_of_a_word():
    paragraph_1 = " ".join(["alpha"] * 100)  # 599 caractères
    paragraph_2 = " ".join(["beta"] * 120)  # 599 caractères
    text = paragraph_1 + "\n\n" + paragraph_2  # 1200 caractères : trop long pour un seul chunk

    chunks = chunk_pages([page(text)])

    assert [c.text for c in chunks] == [paragraph_1, paragraph_2]


def test_a_word_is_never_cut_when_a_cut_at_a_space_is_possible():
    words = [f"mot{i:03d}" for i in range(200)]  # 200 mots de 6 caractères
    text = " ".join(words)

    chunks = chunk_pages([page(text)], ChunkOptions(size=100, overlap=20))

    assert len(chunks) > 1
    assert all(len(c.text) <= 100 for c in chunks)
    for chunk in chunks:
        assert set(chunk.text.split()) <= set(words)  # chaque morceau est un mot entier


def test_a_chunk_neither_starts_nor_ends_with_whitespace():
    text = " ".join(f"mot{i:03d}" for i in range(200))

    chunks = chunk_pages([page(text)], ChunkOptions(size=100, overlap=20))

    assert all(c.text == c.text.strip() for c in chunks)


# --- Référence : LangChain (utilisé par la version TypeScript) ---------------------------------
# On ne remplace pas notre code par la bibliothèque : on vérifie qu'on obtient les mêmes extraits.


def _words(count: int, prefix: str) -> str:
    return " ".join(f"{prefix}{i}" for i in range(count))


REFERENCE_TEXTS = {
    "short": "Un texte court.",
    "no_separator": LONG_TEXT,
    "paragraphs": "\n\n".join(_words(n, "p") for n in (120, 450, 30, 700, 300)),
    "lines": "\n".join(_words(n, "l") for n in (80, 200, 40, 160, 500)),
    "words_and_paragraphs": "\n\n".join(
        [_words(300, "a"), _words(10, "b") + "\n" + _words(250, "c"), _words(900, "d")]
    ),
    "giant_word_between_phrases": "debut du texte " + LONG_TEXT + " fin du texte",
}


@pytest.mark.parametrize("name", REFERENCE_TEXTS)
@pytest.mark.parametrize("size,overlap", [(1000, 200), (100, 20), (50, 0), (300, 299)])
def test_same_chunks_as_langchain(name: str, size: int, overlap: int):
    text = REFERENCE_TEXTS[name]
    expected = RecursiveCharacterTextSplitter(chunk_size=size, chunk_overlap=overlap).split_text(text)

    actual = [c.text for c in chunk_pages([page(text)], ChunkOptions(size=size, overlap=overlap))]

    assert actual == expected
