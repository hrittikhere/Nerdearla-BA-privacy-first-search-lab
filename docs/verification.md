# Verification record

This file distinguishes implementation from evidence of execution. The public
repository must not imply that a sandbox was exercised merely because its YAML
validated. The initial validation date is **20 September 2026**.

The runtime generation model moved to
[Gemma 4 E2B IT](https://huggingface.co/google/gemma-4-E2B-it) (`gemma4:e2b`) on
**22 September 2026**, so documentation and executable setup now name the same model.
The execution evidence in the section below was recorded with the previous Llama 3.2 3B
setup and is kept for its non-generation results; anything that depends on the
generation model must be re-run. Gemma runs are recorded separately under
[Gemma 4 E2B IT runs](#gemma-4-e2b-it-runs). See [model references](../models/README.md).

## Environment

Apple Silicon Mac, 24 GiB unified memory. Python 3.12.11, Ollama 0.32.15,
OpenCode 1.18.31 for both local and sandbox harnesses, Docker sbx 0.43.0 with the
pinned `opencode-docker` template. The dry-run generation model is Llama 3.2 3B
at 16K context and temperature zero; embeddings use
nomic-embed-text:v1.5. Model identities are recorded in the local index.

## Verified

- **24 automated tests** pass: money precision, page-local chunk identity, table
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
- Docker sbx authentication, diagnostics, custom-kit creation, private Docker
  daemon, Compose build/start, 40-document ingestion, source verification, MCP
  discovery, and all ten guided demo steps pass in one uninterrupted run.
- After preparation, the effective sbx network allowlist contains only
  `localhost:11435`. Policy checks deny external ports 80 and 443; real requests
  from the OpenCode environment and MCP container are denied and appear in the
  policy log. Local Ollama access and retrieval still succeed afterward.
- Both quotation gates pass from OpenCode inside sbx with real MCP calls. Observed
  warm sandbox runs took **8.80 seconds** and **6.60 seconds**. These are reference
  observations, not performance guarantees.

## Important rehearsal findings

The 3B model can still omit a citation or paraphrase when an exact quote was
requested. Earlier rehearsals failed the quotation gate. The harness agent now
sets temperature zero explicitly, and the prepared prompt requests a two-line
source quotation and citation format.
An earlier open-ended jurisdiction prompt also produced an invalid tool request
and unsupported prose. Both generated-answer steps now stop the walkthrough on a
failed evidence gate, even if OpenCode exits successfully. Passing these narrow
checks does not establish general answer reliability. Show the
retrieved evidence and run the gate again before the event.

An agreement ID embedded in a semantic query initially caused repeated PDF headers
to outrank the desired clause. A regression fix now separates IDs into filters.
The model also once added whitespace to a structured document ID; the service now
normalizes and validates that bounded identifier before applying the exact filter.
The initial machine's old GPT-OSS model files could not be loaded; no large model
is used or downloaded as a fallback. The small-model choice is intentional.

The first sbx rehearsal exposed three concrete integration faults: the plain
OpenCode template had no private Docker socket, Docker Hub redirected a layer to
an unlisted CloudFront host, and the template's OpenCode 1.18.23 emitted malformed
text instead of an MCP call. The kit now pins the Docker-enabled template,
preparation temporarily permits the observed registry redirect, and both paths
pin OpenCode 1.18.31. A later VM/private-daemon restart stopped Compose services;
the doctor preflight now restores cached services before checking them.

## Gemma 4 E2B IT runs

Recorded on **22 September 2026** on an Apple M5 Mac, 24 GiB unified memory,
macOS 27.0. Ollama 0.34.2, OpenCode 1.18.31, project Python 3.12.12, host conductor
Python 3.14.7. Generation model `gemma4:e2b` (Gemma 4 E2B IT, 5.1B stored parameters,
Q4_K_M, 7.2 GB download) built into the `privacy-lab-local` alias at 16K context and
temperature zero; embeddings unchanged at `nomic-embed-text:v1.5`. Ollama reports
1.9 GB resident at 16K context, 100% GPU.

The Docker sbx path was also re-run for this model change; see
[Docker sbx runs](#docker-sbx-runs) below. `privacy-check` was not passed, for the
reason recorded there.

- `uv run pytest -q`: **24 passed**. `ruff check` and `ruff format --check` clean.
- `./workshop prepare --local`: pulls `gemma4:e2b`, downloads the 40-PDF corpus, and
  reports `indexed: 40`, `unchanged: 0` on a fresh index.
- `./workshop doctor --local`: PASS, 40 documents ready, source hashes match.
- `scripts/evaluate.py`: all real-corpus acceptance checks pass, including the
  **10 quarterly loans strictly above $10 million** and the 12-row agreement-001
  schedule ending at zero balance.
- Quotation gates with real `loans_search_documents` calls: the prepayment case
  passed **5 of 5** runs; the jurisdiction case passed **10 of 11**. The single
  failure is described below.
- Observed wall-clock times for a passing rehearsal ranged from **18.44 to 29.14
  seconds**, typically around 22 seconds. The Llama 3.2 3B observation recorded
  above came from a different machine; treat both as observations, not guarantees.
- `./workshop demo --local --auto`: all **10 steps** complete in one uninterrupted
  run, exit code 0. An earlier attempt stopped at step 9; see below.

### Docker sbx runs

Re-run on **22 September 2026** with sbx **0.45.0**, one version ahead of the 0.43.0
recorded above. The sandbox was recreated from scratch on this machine.

- `./workshop doctor` created `privacy-search-lab`, built the service image, pulled
  Qdrant, started Compose, ingested all 40 PDFs, and passed the MCP smoke test and
  source verification inside the microVM.
- `./workshop demo --auto`: steps **1 through 9 pass**, including from a stopped
  sandbox. Both quotation gates pass from OpenCode inside the sandbox, calling host
  Ollama through `host.docker.internal:11435`. Observed sandbox rehearsals ran between
  **29.12 and 54.0 seconds**, slower than the local-mode 18 to 29 seconds.
- Step 10 (`privacy-check`) **fails** on this machine, by design. Its global sbx policy
  was already initialized as `balanced`, which allows roughly 180 external destinations.
  `ensure_sbx_policy()` deliberately never resets an existing global policy, and the
  audit refuses to certify an allowlist containing anything but `localhost:11435`.
  Presenting the egress boundary requires a `deny-all` global policy
  (`sbx policy reset` then `sbx policy init deny-all`), which changes every sandbox on
  the host. Until that is done, the isolation claim is unproven here and must not be
  made on stage.

### Fixed: an idle sandbox stopped and broke steps 8 and 9

A sandbox that goes idle stops, and its Compose services do not come back with it.
`docker compose ps` in a restarted sandbox lists nothing. Only step 1 restored the
services, so a VM that stopped during the Enter-to-advance pauses left the MCP
endpoint dead for the rest of the walkthrough. The agent's tool call then hung until
`rehearse.py` gave up, with `subprocess.TimeoutExpired` after 150 seconds.

Two runs immediately after a restart also completed without any tool call at all: the
harness started before the endpoint answered, so the model saw no tools and produced
the requested sentence from the prompt alone.

`rehearse.py` now restores the Compose services itself in sbx mode, then polls
`http://127.0.0.1:8765/health` from inside the sandbox until it answers, before timing
anything. Container health is not the same as a reachable endpoint. The sbx timeout is
also raised from 150 to 300 seconds, since a sandbox rehearsal legitimately takes 29 to
54 seconds and a cold start adds to that. Verified: four rehearsals started from a
stopped sandbox, all passing with a real tool call, and a full `./workshop demo --auto`
from a stopped sandbox reaching step 10.

### Fixed: the generation model unloaded between demo steps

Ollama unloads an idle model after five minutes by default, and reloading these weights
costs enough to matter against a rehearsal timeout. The dedicated workshop Ollama now
runs with `OLLAMA_KEEP_ALIVE=-1`, and `doctor` and each rehearsal preload both the
generation and embedding models before anything is timed. `ollama ps` reports both as
resident `Forever` after `./workshop doctor`.

### Fixed: preparation egress rules were never removed on sbx 0.45.0

`prepare` temporarily allows ten registry hosts, then removes them in a `finally`
block. On sbx 0.45.0 `sbx policy rm` refuses to act without a confirmation, so every
removal failed with `stdin is not a terminal; use --force to skip confirmation`. The
calls used `check=False`, so the failures were silent and all ten preparation rules
stayed in the sandbox policy after preparation finished.

The removal now passes `--force` and prints a warning naming any host it could not
remove. Verified: after the fix the sandbox-scoped policy contains only the kit's
`localhost:11435` rule. This is the one case where the repository's own claim, that
preparation rules are removed before presentation, was not true in practice.

### Observed failure: the model answered without calling the tool

In one jurisdiction rehearsal out of eleven, the model returned the requested
sentence and the `DEMO-LA-2026-001, page 2` citation without issuing any MCP call.
`observed_successful_search_tool_call` and `expected_sentence_in_tool_evidence` both
failed, the rehearsal exited non-zero, and `./workshop demo --local --auto` stopped at
step 9. That run took 12.51 seconds, against roughly 22 for a run that retrieves.

The gate worked exactly as intended. Because the rehearsal prompt states the sentence
it expects, a model that skips retrieval can still produce correct-looking output, and
only the tool-call check distinguishes the two. Nothing was changed in response: this
is a real property of a small local model, and the demo should stop when it happens.
A rerun of the same step succeeded, as did six consecutive jurisdiction rehearsals
afterward.

### The raw tool-output echo, and the prompt change

During an earlier evaluation on the larger Gemma 4 E4B build, since removed from this
machine, the model once emitted the entire raw `loans_search_documents` JSON result
before the two requested lines. The requested sentence and citation were correct, but
`any_long_prose_quotes_match_evidence` failed on quoted strings inside the echoed
JSON, such as the source SHA-256, which are not passage text.

The workshop agent prompt in [opencode.json](../opencode.json) and both rehearsal
prompts therefore state explicitly that the raw tool result must not be echoed, quoted
wholesale, or reformatted. That wording is still in place and no echo has been observed
on E2B. This is a prompt change, not a weaker gate: the evidence checks are unchanged.
An echo can still recur, and it should stay visible on stage if it does.

## Remaining limits and event-day gates

1. Repeat `./workshop doctor`, `./workshop privacy-check`, and both quotation gates
   on the presentation machine immediately before the session.
2. Review all effective organization, global, kit, and sandbox rules. The finite
   denial probes do not prove that every untested destination is blocked.
3. Keep the cached `gemma4:e2b` weights, packages, and images. Model output can vary
   even at temperature zero, and a failed evidence gate should remain visible.
4. Linux and Windows/WSL have not been rehearsed by this verification record.

The reference machine is demo-ready as of **20 September 2026**. This status is
evidence for that environment and run, not a permanent guarantee for later CLI,
model-tag, policy, or host changes.

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

./workshop login
./workshop prepare
./workshop doctor
./workshop privacy-check
python3 scripts/rehearse.py
./workshop demo
```

Generated evidence lives under `.local/` and is excluded from Git. Update this
record with what actually ran and its result; never replace a failure with an
assumed success.
