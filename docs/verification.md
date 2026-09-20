# Verification record

This file distinguishes implementation from evidence of execution. The public
repository must not imply that a sandbox was exercised merely because its YAML
validated. The initial validation date is **20 September 2026**.

## Environment

Apple Silicon Mac, 24 GiB unified memory. Python 3.12.11, Ollama 0.32.15,
OpenCode 1.18.31 for the local harness, Docker sbx 0.43.0. The dry-run generation
model is Llama 3.2 3B at 16K context and temperature zero; embeddings use
nomic-embed-text:v1.5. Model identities are recorded in the local index.

## Verified

- **21 automated tests** pass: money precision, page-local chunk identity, table
  corruption rejection, both vector adapter contracts, exact filtering/pagination,
  stale/partial document rejection, incompatible model rejection, local endpoint
  restrictions, actual MCP stdio handshake/schema errors, idempotence, interrupted
  indexing recovery, removal, policy audit failure cases, and rehearsal validation.
- All **40 source PDFs** parse: **178 pages**, **481 chunks**, **1,744 repayment rows**.
  Page-one metadata and full schedules reconcile. A repayment table was also
  rendered and visually checked against extraction.
- Real local Ollama embeddings populate both the SQLite vector implementation
  and the containerized Qdrant backend; all 40 documents are ready in each.
  Source SHA-256 verification passes for the local corpus.
- Six real-corpus acceptance checks pass: four clause retrieval cases, the exact
  count of **10 quarterly loans strictly above $10 million**, and the 12-row
  agreement-001 schedule ending at zero balance. These checks pass against both
  the local SQLite backend and the Docker Compose Qdrant backend.
- The actual HTTP MCP server completes tool discovery, a catalog call, and an
  invalid-request rejection against both local and containerized servers. This
  is separate from the automated stdio test.
- The small-model harness makes real `loans_search_documents` calls and passes
  both narrow quotation/citation gates: prepayment and unspecified jurisdiction.
  Warm local rehearsals took **5.27 seconds** and **5.10 seconds**, respectively.
  This is an observation from one machine/run, not a performance guarantee.
- The dedicated host Ollama endpoint reports cloud support disabled.
- OpenCode configuration validates against the published schema's local structure.
- Docker Compose builds and runs on Docker Desktop, ingests all 40 PDFs into
  Qdrant, and passes MCP and retrieval checks. This validates the service stack,
  not sbx isolation. The sbx kit passes `sbx kit validate`.

## Important rehearsal findings

The 3B model can still omit a citation or paraphrase when an exact quote was
requested. Earlier rehearsals failed the quotation gate. The harness agent now
sets temperature zero explicitly, and the prepared prompt requests source wording.
An earlier open-ended jurisdiction prompt also produced an invalid tool request
and unsupported prose. Both generated-answer steps now stop the walkthrough on a
failed evidence gate, even if OpenCode exits successfully. Passing these narrow
checks does not establish general answer reliability. Show the
retrieved evidence and run the gate again before the event.

An agreement ID embedded in a semantic query initially caused repeated PDF headers
to outrank the desired clause. A regression fix now separates IDs into filters.
The initial machine's old GPT-OSS model files could not be loaded; no large model
is used or downloaded as a fallback. The small-model choice is intentional.

## Pending release gates

1. **Actual sbx creation and execution:** blocked on Docker account authentication.
   `sbx ls --json` currently reports “Not authenticated to Docker.” Run `sbx login`.
2. **Full sandbox policy and egress verification:** pending the running sandbox,
   including validation of the CLI's actual policy JSON against the conservative
   audit parser, local endpoint access, and deny-log evidence from both processes
   and nested service containers.
3. **Full guided rehearsal inside sbx:** execute all steps using cached dependencies
   and the same small model intended for the presentation.

Until those gates pass, call this a working local demo with a prepared sandbox
integration, not a fully rehearsed isolated workshop.

## Reproduce

```bash
PYTHONPATH=src uv run pytest -q
uv run ruff check src scripts tests
uv run ruff format --check src scripts tests
./workshop doctor --local
OLLAMA_URL=http://127.0.0.1:11435 PYTHONPATH=src uv run python scripts/evaluate.py
python3 scripts/rehearse.py --local
python3 scripts/rehearse.py --local --case jurisdiction
sbx kit validate ./sandbox
docker compose config --quiet

# After Docker authentication
./workshop prepare
./workshop doctor
./workshop privacy-check
python3 scripts/rehearse.py
./workshop demo
```

Generated evidence lives under `.local/` and is excluded from Git. Update this
record with what actually ran and its result; never replace a failure with an
assumed success.
