from collections import Counter
from typing import Protocol

from schemas import TokenizedContext, TextChunk


class SubwordTokenizer(Protocol):
    """The slice of a Hugging Face fast tokenizer that chunking relies on."""

    def __call__(self, text: list[str], *, is_split_into_words: bool, add_special_tokens: bool): ...


def subword_counts(tokens: list[str], tokenizer: SubwordTokenizer) -> list[int]:
    """How many embedding-model subword tokens each spaCy token turns into."""
    if not tokens:
        return []
    encoding = tokenizer(tokens, is_split_into_words=True, add_special_tokens=False)
    per_token = Counter(word_id for word_id in encoding.word_ids() if word_id is not None)
    return [per_token[i] for i in range(len(tokens))]


def chunk_tokenized_context(
    context: TokenizedContext,
    tokenizer: SubwordTokenizer,
    max_subwords: int,
    overlap_subwords: int,
) -> list[TextChunk]:
    """
    Split a tokenized document into overlapping chunks that each fit the embedding
    model's input limit.

    Chunk boundaries fall on spaCy token boundaries, and chunk size is measured in the
    embedding model's own subword tokens, so numeric-heavy text (where one spaCy token
    can become many subwords) is never silently truncated by the model. A single spaCy
    token longer than `max_subwords` becomes a chunk of its own.

    Args:
        context: The document and its spaCy tokens/offsets.
        tokenizer: The embedding model's tokenizer.
        max_subwords: Maximum subword tokens per chunk, excluding special tokens.
        overlap_subwords: Approximate subword tokens shared between consecutive chunks.
    """
    if overlap_subwords >= max_subwords:
        raise ValueError("overlap_subwords must be smaller than max_subwords.")

    tokens = context.tokens
    counts = subword_counts(tokens, tokenizer)
    content = context.document.content
    chunks: list[TextChunk] = []

    start = 0
    while start < len(tokens):
        # Grow the chunk until the next token would exceed the budget.
        end, size = start, 0
        while end < len(tokens) and (end == start or size + counts[end] <= max_subwords):
            size += counts[end]
            end += 1

        char_start = context.token_offsets[start]
        char_end = context.token_offsets[end - 1] + len(tokens[end - 1])
        chunks.append(
            TextChunk(
                index=len(chunks),
                text=content[char_start:char_end],
                token_start=start,
                token_end=end,
            )
        )

        if end == len(tokens):
            break

        # Step back from `end` to share roughly `overlap_subwords` with the next chunk,
        # always moving forward by at least one token.
        next_start, overlap = end, 0
        while next_start - 1 > start and overlap + counts[next_start - 1] <= overlap_subwords:
            next_start -= 1
            overlap += counts[next_start]
        start = next_start

    return chunks
