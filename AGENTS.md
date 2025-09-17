# Repository Guidelines

## Project Structure & Module Organization
- `main_0905.py` orchestrates CLI flows; shared configuration helpers live in `main_helper_0905.py`.
- Document ingestion and Neo4j loaders reside in `doc_parser/`; code understanding utilities split between `code_parser/` and `code_generator/`.
- Graph-specific pipelines sit in `graphrag_gpt/`; database adapters in `db_integration/`; persistent embeddings in `chroma_db_store/`.
- Experimental source documents stay under `data/src/`; regression tests in `tests/`; long-lived reports belong in `doc/` or `htmlcov/` rather than module folders.

## Build, Test, and Development Commands
- `uv pip install -r requirements.txt` (fallback: `pip install -r requirements.txt`) installs dependencies.
- `uv run python main_0905.py -f full_pipeline` drives the end-to-end ingest workflow.
- `uv run python main_0905.py -f qa -q "<question>"` handles a single QA turn for quick checks.
- `uv run pytest` or `uv run pytest --cov=.` runs the suite and refreshes `htmlcov/` coverage artifacts.
- `uv run ruff check .`, `uv run black --check .`, and `uv run flake8` enforce linting and formatting.

## Coding Style & Naming Conventions
- Target Python 3.10-3.12 with BlackÅfs 88-character limit; use snake_case for modules/functions, PascalCase for classes, and UPPER_CASE for constants.
- Prefer type hints on public APIs and co-locate helpers with their domain package; keep CLI wiring confined to `main_0905.py`.
- Resolve lint conflicts by following BlackÅfs layout and adding narrow Ruff suppressions (e.g., `# noqa: F401`) rather than broad disables.

## Testing Guidelines
- Write pytest functions as `test_<feature>_<scenario>()`; share reusable fixtures in `tests/conftest.py`.
- Mock Neo4j and Chroma connectors from `db_integration/` when external calls would occur.
- Regenerate `htmlcov/index.html` after modifying ingest or QA flows and capture before/after metrics in PR notes when behavior shifts.

## Commit & Pull Request Guidelines
- Use descriptive, sentence-style commit messages (often Japanese in history) and reference issues via `Refs: #123` when applicable.
- PRs should explain motivation, list verification commands, note required `.env` updates, and attach screenshots for UI or visualization tweaks.

## Security & Configuration Tips
- Store credentials in the repo-root `.env`; never commit secrets or generated vector stores.
- Update `.gitignore` for new secret-backed assets and document required environment variables plus defaults in `README.md`.
