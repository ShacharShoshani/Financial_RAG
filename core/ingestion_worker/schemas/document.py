from pydantic import BaseModel, HttpUrl
from typing import Literal, List
from datetime import datetime


class FinancialDocument(BaseModel):
    title: str
    sentences: List[str]
    description: str = ""
    ticker_symbol: str
    document_type: Literal[
        "news", "earnings_call", "sec_filing", "summary", "historical_company_facts"
    ]
    publish_date: datetime
    publisher: str
    source_url: HttpUrl
