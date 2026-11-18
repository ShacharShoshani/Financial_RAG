import pytest
from datetime import datetime, timezone
from pydantic import ValidationError
from schemas import FinancialDocument, TokenizedContext


@pytest.fixture
def financial_document() -> FinancialDocument:
    return FinancialDocument(
        title="Apple Q3 Earnings Report",
        content="Apple reported strong earnings.",
        ticker_symbol="AAPL",
        document_type="earnings_call",
        publish_date=datetime(2026, 11, 14, 15, 30, tzinfo=timezone.utc),
        publisher="Financial Modeling Prep",
        source_url="https://www.sec.gov/Archives/edgar/daily-index/xbrl/companyfacts.zip",
    )


def test_tokenized_context_creation_success(financial_document):
    """Test that a valid document and token list create a TokenizedContext."""
    tokens = ["Apple", "reported", "strong", "earnings", "."]

    context = TokenizedContext(document=financial_document, tokens=tokens)

    assert context.document == financial_document
    assert context.document.ticker_symbol == "AAPL"
    assert context.tokens == tokens


def test_tokenized_context_accepts_empty_tokens(financial_document):
    """Test that an empty token list is allowed."""
    context = TokenizedContext(document=financial_document, tokens=[])

    assert context.tokens == []


def test_tokenized_context_accepts_document_as_dict(financial_document):
    """Test that a nested dict is validated into a FinancialDocument."""
    context = TokenizedContext(
        document=financial_document.model_dump(), tokens=["Apple"]
    )

    assert isinstance(context.document, FinancialDocument)
    assert context.document == financial_document


def test_tokenized_context_missing_document():
    """Test that omitting the document raises an error."""
    with pytest.raises(ValidationError) as exc_info:
        TokenizedContext(tokens=["Apple"])

    assert "document" in str(exc_info.value)
    assert "Field required" in str(exc_info.value)


def test_tokenized_context_missing_tokens(financial_document):
    """Test that omitting the tokens raises an error."""
    with pytest.raises(ValidationError) as exc_info:
        TokenizedContext(document=financial_document)

    assert "tokens" in str(exc_info.value)
    assert "Field required" in str(exc_info.value)


def test_tokenized_context_invalid_document():
    """Test that an invalid nested document is rejected."""
    with pytest.raises(ValidationError) as exc_info:
        TokenizedContext(document={"title": "Incomplete"}, tokens=["Apple"])

    assert "document.ticker_symbol" in str(exc_info.value)


def test_tokenized_context_tokens_must_be_list(financial_document):
    """Test that a plain string is rejected for the tokens field."""
    with pytest.raises(ValidationError) as exc_info:
        TokenizedContext(document=financial_document, tokens="Apple reported")

    assert "tokens" in str(exc_info.value)
    assert "Input should be a valid list" in str(exc_info.value)


def test_tokenized_context_tokens_must_be_strings(financial_document):
    """Test that non-string tokens are rejected."""
    with pytest.raises(ValidationError) as exc_info:
        TokenizedContext(document=financial_document, tokens=["Apple", 42])

    assert "tokens.1" in str(exc_info.value)
    assert "Input should be a valid string" in str(exc_info.value)
