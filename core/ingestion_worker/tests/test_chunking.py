import pytest
from datetime import datetime, timezone
from utils import chunk_tokenized_context, subword_counts
from schemas import FinancialDocument, TokenizedContext


class FakeEncoding:
    def __init__(self, word_ids: list[int]):
        self._word_ids = word_ids

    def word_ids(self) -> list[int]:
        return self._word_ids


class FakeTokenizer:
    """Stands in for the model tokenizer: each comma adds one extra subword."""

    def __call__(self, text, *, is_split_into_words, add_special_tokens):
        assert is_split_into_words and not add_special_tokens
        word_ids: list[int] = []
        for i, token in enumerate(text):
            word_ids.extend([i] * (1 + token.count(",")))
        return FakeEncoding(word_ids)


def make_context(content: str) -> TokenizedContext:
    """Whitespace-tokenize `content`, recording each token's character offset."""
    tokens, offsets, pos = [], [], 0
    for token in content.split():
        pos = content.index(token, pos)
        tokens.append(token)
        offsets.append(pos)
        pos += len(token)
    document = FinancialDocument(
        title="Test",
        content=content,
        ticker_symbol="AAPL",
        document_type="historical_company_facts",
        publish_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
        publisher="SEC EDGAR",
        source_url="https://www.sec.gov/",
    )
    return TokenizedContext(document=document, tokens=tokens, token_offsets=offsets)


def test_subword_counts_maps_each_token():
    assert subword_counts(["a", "1,000", "b"], FakeTokenizer()) == [1, 2, 1]


def test_subword_counts_empty():
    assert subword_counts([], FakeTokenizer()) == []


def test_short_document_is_one_chunk():
    context = make_context("Apple reported revenue.")

    chunks = chunk_tokenized_context(context, FakeTokenizer(), max_subwords=10, overlap_subwords=2)

    assert len(chunks) == 1
    assert chunks[0].text == "Apple reported revenue."
    assert (chunks[0].index, chunks[0].token_start, chunks[0].token_end) == (0, 0, 3)


def test_empty_document_has_no_chunks():
    assert chunk_tokenized_context(make_context(""), FakeTokenizer(), 10, 2) == []


def test_chunks_respect_budget_and_overlap():
    context = make_context("t0 t1 t2 t3 t4 t5 t6 t7 t8 t9")

    chunks = chunk_tokenized_context(context, FakeTokenizer(), max_subwords=4, overlap_subwords=1)

    assert [(c.token_start, c.token_end) for c in chunks] == [(0, 4), (3, 7), (6, 10)]
    assert [c.index for c in chunks] == [0, 1, 2]
    assert chunks[1].text == "t3 t4 t5 t6"


def test_budget_counts_subwords_not_tokens():
    # "1,000,000" is 3 subwords, so it fills most of a 4-subword chunk alone.
    context = make_context("a 1,000,000 b c")

    chunks = chunk_tokenized_context(context, FakeTokenizer(), max_subwords=4, overlap_subwords=0)

    assert [c.text for c in chunks] == ["a 1,000,000", "b c"]


def test_chunk_text_preserves_original_spacing():
    context = make_context("Net  income:\n$4.2B   total")

    chunks = chunk_tokenized_context(context, FakeTokenizer(), max_subwords=10, overlap_subwords=0)

    assert chunks[0].text == "Net  income:\n$4.2B   total"


def test_oversized_token_becomes_its_own_chunk():
    context = make_context("a 1,2,3,4,5,6 b")

    chunks = chunk_tokenized_context(context, FakeTokenizer(), max_subwords=3, overlap_subwords=1)

    assert [c.text for c in chunks] == ["a", "1,2,3,4,5,6", "b"]


def test_overlap_must_be_smaller_than_budget():
    with pytest.raises(ValueError):
        chunk_tokenized_context(make_context("a b"), FakeTokenizer(), max_subwords=2, overlap_subwords=2)
