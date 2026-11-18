from pydantic import BaseModel, model_validator
from .document import FinancialDocument

class TokenizedContext(BaseModel):
    document: FinancialDocument
    tokens: list[str]
    # Character offset of each token in document.content, used to recover the
    # original text (spacing and all) for any span of tokens.
    token_offsets: list[int]

    @model_validator(mode="after")
    def _offsets_match_tokens(self) -> "TokenizedContext":
        if len(self.token_offsets) != len(self.tokens):
            raise ValueError("token_offsets must have one entry per token.")
        return self
