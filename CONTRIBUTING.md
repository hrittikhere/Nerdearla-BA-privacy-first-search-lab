# Contributing

Keep each change understandable as one focused commit: parser behavior, retrieval,
protocol, sandbox setup, documentation, or a specific bug fix. Explain the user
behavior and include meaningful validation. Do not squash the workshop's learning
history into one initial implementation commit.

```bash
uv sync --frozen --group dev
uv run ruff check src scripts tests
uv run ruff format --check src scripts tests
PYTHONPATH=src uv run pytest -q
```

Tests use synthetic values and in-memory Qdrant; they do not download the corpus,
call hosted models, or require credentials. The real-corpus acceptance check and
OpenCode rehearsal are separate, explicit operations described in the runbook.

Never commit source PDFs, vectors, model weights, `.env` files, generated reports,
credentials, or harness histories. Update `uv.lock` with dependency changes. Bump
the parser identity when its output changes and document index migration/rebuild.
Do not weaken a privacy check to turn a failed rehearsal green.
