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

### 2. Verify the setup

```bash
uv run python --version   # Python 3.15.2
uv run pytest             # all tests should pass
```

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

**Dependencies seem out of date after a pull**: Run `uv sync` again to match `uv.lock`.

**Starting with a clean environment**: Delete the virtual environment and sync again:

```bash
rm -rf .venv
uv sync
```
