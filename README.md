# Financial RAG Project

An experimental Retrieval-Augmented Generation (RAG) system for answering questions about public companies' financials.

The project pulls financial data from public sources such as SEC EDGAR, turns it into plain-text documents, and stores them in a vector database (Chroma) so an LLM can retrieve relevant facts when it answers a question.

## Status

| Component | Location | State |
|-----------|----------|-------|
| Ingestion worker | [`core/ingestion_worker/`](core/ingestion_worker/) | In progress |
| Backend | [`core/backend/`](core/backend/) | Not started |
| Frontend | [`core/frontend/`](core/frontend/) | Not started |
| Vector store | [`data/chroma_db/`](data/chroma_db/) | Not started |

### Ingestion worker

The ingestion worker is a Python service (managed with [uv](https://docs.astral.sh/uv/)) that collects data and normalizes it:

- **`BaseFetcher`** ([`sources/base.py`](core/ingestion_worker/sources/base.py)) is the abstract base for every data source. Each source implements two steps: `_fetch_raw` downloads the raw data, and `_preprocess` converts it into documents.
- **`HistoricalEdgarFetcher`** ([`sources/historical_edgar.py`](core/ingestion_worker/sources/historical_edgar.py)) downloads the SEC EDGAR Company Facts bulk dataset (`companyfacts.zip`) and turns each XBRL fact into one natural-language sentence.
- **`FinancialDocument`** ([`schemas/document.py`](core/ingestion_worker/schemas/document.py)) is the Pydantic model every fetcher returns: a title, a list of sentences, the ticker, document type, publish date, publisher, and source URL.

## Quick start

```bash
cd core/ingestion_worker
uv sync
cp .env.example .env      # then set APP_NAME and SEC_CONTACT_EMAIL
uv run pytest
uv run python main.py     # fetches Apple's (AAPL) historical facts as a demo
```

The SEC requires a contact email in the `User-Agent` header of every request, so `SEC_CONTACT_EMAIL` must be set. See the [ingestion worker setup guide](docs/setup_guides/ingestion_worker.md) for the full instructions.

## Repository layout

```text
.
├── core/
│   ├── ingestion_worker/   # data fetchers and preprocessing (Python)
│   ├── backend/            # API service (planned)
│   └── frontend/           # user interface (planned)
├── data/
│   └── chroma_db/          # local vector database (planned)
└── docs/                   # project documentation (see index below)
```

## Documentation index

### Setup guides

- [Ingestion Worker: Environment Setup](docs/setup_guides/ingestion_worker.md): installing uv and Python, syncing dependencies, running tests, managing packages, and configuring VS Code.

### Data sources

- [EDGAR Historical Data: Terminology Guide](docs/edgar_historical_data/README.md): the fields and terms in the SEC Company Facts dataset (CIK, XBRL, taxonomies, units, frames, and form types) and the current limitations of how the project converts facts to sentences.

### Architecture

- [`docs/architecture/`](docs/architecture/): no documents yet.

### API specs

- [`docs/api_specs/`](docs/api_specs/): no documents yet.
