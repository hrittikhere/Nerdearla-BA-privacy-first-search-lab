# Operations and troubleshooting

## Repository map

```text
src/privacy_lab/
  documents.py     PDF parsing, exact metadata, tables, page-local chunks
  embeddings.py    Local Ollama embedding client and model digest checks
  catalog.py       Exact metadata and readiness state
  vectors.py       Qdrant and SQLite implementations of one contract
  service.py       Ingestion, retrieval, provenance, stale-data filtering
  mcp_server.py    Five bounded read-only tools and HTTP health
  cli.py           Administrative CLI and protocol smoke check
scripts/
  workshop.py      Host setup and Enter-to-advance presentation conductor
  evaluate.py      Source-checked retrieval acceptance cases
  rehearse.py      Actual OpenCode tool-call and quotation check
sandbox/spec.yaml  Credential-free kit and local model endpoint
compose.yaml       Private database, MCP, and explicit ingestion container
models/Modelfile    Small local generation model with bounded context
data/source/       Downloaded PDFs; ignored by Git and Docker builds
data/index/        Local development index; ignored by Git
.local/            Local processes, harness install, logs, reports; ignored
```

## Useful commands

```bash
# Local service health and corpus state
curl http://127.0.0.1:11435/api/status
curl http://127.0.0.1:8765/health
./workshop doctor --local

# Reproducible code/protocol checks; no corpus or model download required
uv sync --frozen --group dev
PYTHONPATH=src uv run pytest -q
uv run ruff check src scripts tests
uv run ruff format --check src scripts tests

# Actual corpus/model checks
OLLAMA_URL=http://127.0.0.1:11435 PYTHONPATH=src uv run python scripts/evaluate.py
python3 scripts/rehearse.py --local
python3 scripts/rehearse.py --local --case jurisdiction

# Sandbox services and logs
sbx exec -w "$PWD" privacy-search-lab docker compose ps
sbx exec -w "$PWD" privacy-search-lab docker compose logs --tail 50 mcp
sbx exec -w "$PWD" privacy-search-lab docker compose logs --tail 50 qdrant
sbx exec -w "$PWD" privacy-search-lab opencode --version
```

The main sandbox does not publish MCP to the host. Run its health and protocol
checks inside the sandbox. A healthy local server on your Mac does not prove that
the sandbox's MCP server is healthy.

## Common failures

**Not authenticated to Docker:** run `./workshop login` and complete the browser
device flow. The command verifies the resulting session and runs `sbx diagnose`.
`docker login` and Docker Desktop sign-in do not necessarily authenticate sbx.
The kit can validate without authentication; sandbox creation cannot.

**`/var/run/docker.sock` is missing inside sbx:** the plain OpenCode template has
the Docker CLI but no private daemon socket. The current kit pins the
`opencode-docker` template. Remove only the outdated `privacy-search-lab` sandbox,
then rerun preparation; this also removes that sandbox's service volumes.

**Docker Hub redirects return 403 during preparation:** current Docker Hub layers
can be served through `production.cloudfront.docker.com`. Preparation adds that
sandbox-scoped rule temporarily and removes it in `finally`. Rerun preparation;
do not add a permanent broad registry allowance.

**OpenCode prints malformed JSON instead of calling MCP:** the base template may
ship a different OpenCode release. Preparation pins 1.18.31 inside the sandbox
and warms the Ollama provider package before closing preparation egress.

**Global policy is Balanced/Open:** the preparation script does not reset your
global policy. Inspect `sbx policy ls privacy-search-lab --wide`. Configure the
intended policy explicitly before making an isolation claim. Avoid disrupting
unrelated sandboxes. Organization governance may require an administrator.

**Port 11435 has cloud enabled:** the script refuses it. Inspect the process on
that port; stop or reconfigure it intentionally. Do not turn a regular hosted-model
session into a workshop session by merely renaming its model.

**Small model calls a tool but invents the answer:** inspect the returned passages.
Use an explicit agreement filter, a short semantic query, and the exact-quote
prompt. Run `scripts/rehearse.py`. This is a deliberately narrow quality gate;
small-model general reasoning is not guaranteed.

**Memory pressure:** use the shipped 3B model and 16K context, close unrelated
model sessions, and keep the sandbox at the configured 3 GiB. Do not raise context
to 100K+ during the dry run. Download size does not equal inference memory: KV
cache and concurrent requests also consume RAM.

**Tensor size/load error in an old model:** `ollama show MODEL` can reveal an
incompatible/corrupt model before inference. The initial machine's GPT-OSS weights
failed this check; the workshop uses the small supported local model. Do not
automatically download or select a larger model as a fallback.

**Python cannot import the editable package on macOS:** check the `.venv` editable
`.pth` file. macOS hidden flags can cause Python to ignore it. The conductor sets
`PYTHONPATH` to this repository's `src/` for local execution; the container installs
a non-editable package. The explicit `PYTHONPATH=src` development commands avoid
depending on that local filesystem flag.

**Docker uses an unrelated Buildx builder:** `docker buildx ls` shows the selected
builder. For standalone Docker Desktop validation, use
`BUILDX_BUILDER=desktop-linux docker compose build`. This changes only the command's
environment, not the global builder selection. Inside sbx use its own builder.

**Index identity changed:** do not mix vectors from different models or parser
versions. Stop consumers and create a fresh index. For backend experiments use
separate catalog directories and Qdrant collections.

**Scanned or unsupported PDF:** ingestion stops. The workshop does not silently
call an OCR SaaS service. Add a locally tested OCR/layout adapter with provenance
before importing that document format.

## Lifecycle and retention

`./workshop stop` stops only the named sandbox; volumes persist. The dedicated host
Ollama process and model downloads remain local. `./workshop reset --yes` removes
this Compose project's generated service volumes inside the named sandbox. It
keeps source PDFs and host models. The default refuses destructive reset without
the explicit flag. Never run global Docker prune as part of a workshop reset.

Local development stores process IDs in `.local/`. Inspect ownership and command
before stopping a process; PIDs can be reused. Stop the local MCP server before
removing `data/index/`. Source PDFs, vectors, transcripts, and reports are distinct
data copies with distinct retention requirements.

Removing a document through `privacy-lab remove DOCUMENT_ID` hides it from readers,
deletes vector rows, and removes its catalog record. It does not delete the source
PDF or past model conversations. If vector deletion fails, the non-ready catalog
state prevents the old evidence from being served; repair/reset explicitly.

## Extending the workshop

To add a vector backend, implement the four-method protocol and run the shared
contract tests. To add document formats, preserve provenance and reject ambiguous
metadata. To add remote/multi-user MCP access, design authentication, authorization,
transport security, and retention first. To add web retrieval, declare a separate
online mode and its data-exposure boundary; the current presentation makes no web
requests for grounding.

## Standalone container validation

To run Compose alongside the local MCP server, publish its MCP endpoint on a
separate loopback port. This exercises Qdrant and container packaging without
claiming sbx isolation. Start the dedicated Ollama endpoint first.

```bash
./workshop models-start
BUILDX_BUILDER=desktop-linux docker compose build
LAB_MCP_PORT=8766 docker compose up -d --wait
LAB_MCP_PORT=8766 docker compose run --rm ingest
PYTHONPATH=src uv run privacy-lab mcp-smoke --url http://127.0.0.1:8766/mcp
LAB_MCP_PORT=8766 docker compose exec -T mcp python - < scripts/evaluate.py
```
