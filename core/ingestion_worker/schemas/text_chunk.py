from pydantic import BaseModel


class TextChunk(BaseModel):
    """A contiguous span of a tokenized document, sized to fit the embedding model."""

    index: int  # Position of this chunk within its document
    text: str  # Original document text covered by the chunk
    token_start: int  # First spaCy token index (inclusive)
    token_end: int  # Last spaCy token index (exclusive)
