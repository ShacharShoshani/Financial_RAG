# Ingestion Worker: Environment Setup

This guide covers setting up a local development environment for the ingestion worker in [`core/ingestion_worker/`](../../core/ingestion_worker/).

## Prerequisites

| Tool | Version | Notes |
|------|---------|-------|
| [uv](https://docs.astral.sh/uv/) | recent release | Manages the Python version, virtual environment, and dependencies |
| Python | 3.15.2 | Pinned in `.python-version`. uv installs it for you if it's missing |

### Install uv

macOS / Linux:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Or with Homebrew:

```bash
brew install uv
```

Check the install:

```bash
uv --version
```

## Setup

Run all commands from the ingestion worker directory:

```bash
cd core/ingestion_worker
```

### 1. Install Python and dependencies

```bash
uv sync
```

This command:

- installs Python 3.15.2 if you don't have it (from `.python-version`)
- creates a virtual environment in `core/ingestion_worker/.venv/`
- installs the exact dependency versions locked in `uv.lock`

### 2. Download the spaCy language model

```bash
uv run spacy download en_core_web_sm
```

This downloads spaCy's small English pipeline (`en_core_web_sm`) into the virtual environment. It isn't installed by `uv sync`, so run this again whenever you recreate `.venv`.

### 3. Configure environment variables

Copy the example file and fill in the values:

```bash
cp .env.example .env
```

| Variable | Required | Purpose |
|----------|----------|---------|
| `APP_NAME` | no | Application name sent in the SEC `User-Agent` header. Defaults to `DefaultRAGProject/1.0` |
| `SEC_CONTACT_EMAIL` | yes | Contact email sent in the SEC `User-Agent` header. The SEC requires one on every request, and `main.py` exits if it's missing |

`.env` is gitignored, so your values stay local.

### 4. Verify the setup

```bash
uv run python --version   # Python 3.15.2
uv run pytest             # all tests should pass
```

## Running the worker

```bash
uv run python main.py
```

This fetches the historical EDGAR facts for the companies listed in `TARGET_COMPANIES` in `main.py`, then tokenizes each document with spaCy.

On the first run, the worker downloads the SEC Company Facts bulk dataset (about 1 GB compressed) and extracts it into `.data/sec_historical/`. Later runs reuse the extracted files and skip the download. To download a fresh copy, delete `.data/sec_historical/`.

## Day-to-day usage

`uv run` executes a command inside the project's virtual environment, so you don't need to activate it first:

```bash
uv run pytest                     # run the test suite
uv run pytest tests/test_document.py -v   # run one test file
uv run python                     # interactive shell with project deps
```

If you'd rather activate the environment yourself (for example, so your editor or shell picks it up):

```bash
source .venv/bin/activate
pytest
deactivate
```

### Managing dependencies

Use uv instead of `pip` so that `pyproject.toml` and `uv.lock` stay in sync:

```bash
uv add <package>          # add a runtime dependency
uv add --dev <package>    # add a development-only dependency
uv remove <package>       # remove a dependency
uv lock --upgrade         # upgrade locked versions within the constraints
```

Commit both `pyproject.toml` and `uv.lock` after changing dependencies.

## Project layout

```
core/ingestion_worker/
├── .python-version     # pinned Python version
├── .env.example        # template for .env (copy it and fill in your values)
├── .data/              # downloaded datasets (gitignored)
├── main.py             # entry point: fetches and tokenizes documents
├── pyproject.toml      # project metadata and dependencies
├── uv.lock             # locked dependency versions (commit this)
├── schemas/            # Pydantic models (e.g. FinancialDocument)
├── sources/            # data source connectors
└── tests/              # pytest test suite
```

## Editor setup (VS Code)

Point the Python extension at the project interpreter:

1. Open the Command Palette (`Cmd+Shift+P`).
2. Run **Python: Select Interpreter**.
3. Choose `core/ingestion_worker/.venv/bin/python`.

## Troubleshooting

**`uv: command not found`**: The uv install directory (usually `~/.local/bin`) is not on your `PATH`. Restart your shell, or add it to `PATH` in `~/.zshrc`.

**`OSError: [E050] Can't find model 'en_core_web_sm'`**: The spaCy model isn't installed in the current virtual environment. Run `uv run spacy download en_core_web_sm`.

**`❌ Error: SEC_CONTACT_EMAIL is missing from the .env file.`**: Create `.env` from `.env.example` and set `SEC_CONTACT_EMAIL`. See [Configure environment variables](#3-configure-environment-variables).

**Dependencies seem out of date after a pull**: Run `uv sync` again to match `uv.lock`.

**Starting with a clean environment**: Delete the virtual environment and sync again:

```bash
rm -rf .venv
uv sync
uv run spacy download en_core_web_sm
```
