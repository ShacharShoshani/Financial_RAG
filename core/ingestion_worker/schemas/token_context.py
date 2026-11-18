from pydantic import BaseModel
from .document import FinancialDocument

class TokenizedContext(BaseModel):
    document: FinancialDocument
    tokens: list[str]