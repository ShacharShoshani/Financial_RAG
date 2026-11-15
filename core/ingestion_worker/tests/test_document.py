import pytest
from datetime import datetime, timezone
from pydantic import HttpUrl, ValidationError
from schemas import FinancialDocument

def test_financial_document_creation_success():
    """Test that a valid dictionary successfully creates a FinancialDocument object."""
    valid_data = {
        "title": "Apple Q3 Earnings Report",
        "sentences": [
            "Apple reported strong earnings driven by services.",
            "iPhone revenue grew year over year.",
        ],
        "ticker_symbol": "AAPL",
        "document_type": "earnings_call",
        "publish_date": datetime(2026, 11, 14, 15, 30, tzinfo=timezone.utc),
        "publisher": "Financial Modeling Prep",
        "source_url": HttpUrl("https://www.sec.gov/Archives/edgar/daily-index/xbrl/companyfacts.zip")
    }
    
    doc = FinancialDocument(**valid_data)
    
    assert doc.title == "Apple Q3 Earnings Report"
    assert doc.sentences == [
        "Apple reported strong earnings driven by services.",
        "iPhone revenue grew year over year.",
    ]
    assert doc.ticker_symbol == "AAPL"
    assert doc.document_type == "earnings_call"
    assert str(doc.source_url) == "https://www.sec.gov/Archives/edgar/daily-index/xbrl/companyfacts.zip"


def test_financial_document_invalid_document_type():
    """Test that Pydantic enforces the Literal constraint."""
    invalid_data = {
        "title": "Random Blog Post",
        "sentences": ["Just some thoughts on the market."],
        "ticker_symbol": "AAPL",
        "document_type": "opinion_piece",
        "publish_date": datetime.now(timezone.utc),
        "publisher": "Medium",
        "source_url": "https://medium.com/some-post"
    }
    
    with pytest.raises(ValidationError) as exc_info:
        FinancialDocument(**invalid_data)
    
    assert "document_type" in str(exc_info.value)
    assert "Input should be" in str(exc_info.value)


def test_financial_document_invalid_url():
    """Test that Pydantic rejects malformed URLs."""
    invalid_url_data = {
        "title": "Tesla News",
        "sentences": ["Tesla announces new model."],
        "ticker_symbol": "TSLA",
        "document_type": "news",
        "publish_date": datetime.now(timezone.utc),
        "publisher": "Yahoo Finance",
        "source_url": "not-a-valid-url" 
    }
    
    with pytest.raises(ValidationError) as exc_info:
        FinancialDocument(**invalid_url_data)
        
    assert "source_url" in str(exc_info.value)
    assert "Input should be a valid URL" in str(exc_info.value)


def test_financial_document_missing_required_field():
    """Test that omitting a required field raises an error."""
    missing_field_data = {
        "title": "Incomplete Data",
        "sentences": ["Missing ticker symbol."],
        "document_type": "news",
        "publish_date": datetime.now(timezone.utc),
        "publisher": "Unknown",
        "source_url": "https://example.com"
    }
    
    with pytest.raises(ValidationError) as exc_info:
        FinancialDocument(**missing_field_data)
        
    assert "ticker_symbol" in str(exc_info.value)
    assert "Field required" in str(exc_info.value)


def test_financial_document_sentences_must_be_list():
    """Test that a plain string is rejected for the sentences field."""
    invalid_sentences_data = {
        "title": "Apple News",
        "sentences": "Apple announces a new product.",
        "ticker_symbol": "AAPL",
        "document_type": "news",
        "publish_date": datetime.now(timezone.utc),
        "publisher": "Yahoo Finance",
        "source_url": "https://example.com"
    }

    with pytest.raises(ValidationError) as exc_info:
        FinancialDocument(**invalid_sentences_data)

    assert "sentences" in str(exc_info.value)
    assert "Input should be a valid list" in str(exc_info.value)
