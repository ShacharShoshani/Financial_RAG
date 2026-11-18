from pydantic import BaseModel
from .token_context import TokenizedContext
from .text_chunk import TextChunk

class EmbeddingContext(BaseModel):
    tokenized_context: TokenizedContext
    chunk: TextChunk
    embedding: list[float]
