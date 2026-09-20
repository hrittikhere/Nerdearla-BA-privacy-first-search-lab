# Privacy First Search Lab

**Build local document search, expose it through MCP, and query it with a small local model in OpenCode.**

A hands-on workshop for **[Nerdearla Argentina 2026](https://nerdearla.com/en/argentina/2026/)**,
accompanying *Building Privacy-First Vector Search Pipelines With Local LLMs*.

Lab by [Rudraksh Karpe](https://github.com/rudrakshkarpe),
[Hrittik Roy](https://github.com/hrittikhere), and
[Shivay Lamba](https://github.com/shivaylamba).

Index PDFs, search clauses, filter structured records, and follow real MCP tool
calls through to answers with source citations. Docker sbx contains the agent and
search services; Ollama runs inference locally on the host.

[Workflow](#workflow) · [Quickstart](#quickstart) · [Run the demo](#run-the-demo) · [Ask your own questions](#ask-your-own-questions) · [Guides](#guides)

## Workflow

[![Workshop runtime map and workflows: Docker sbx, OpenCode, MCP, Python, Ollama, Qdrant, and SQLite](docs/assets/workshop-workflow.svg)](docs/assets/workshop-workflow.svg)

**Index:** PDF → page-aware chunks → local embeddings → Qdrant.
SQLite stores exact metadata, repayment schedules, and source provenance.

**Answer:** question → OpenCode → local model → MCP retrieval → cited evidence
→ local answer. OpenCode coordinates the tool calls; Ollama runs the models.

Docker sbx provides a microVM with its own Docker daemon. Compose runs the
importer, MCP service, Qdrant, and SQLite catalog inside that boundary. Host Ollama
uses local hardware acceleration through a scoped endpoint.

| Model | Role |
|---|---|
| Llama 3.2 3B, with a 16K context | Tool selection and answer generation |
| nomic-embed-text:v1.5 | Document and query embeddings |

See the [architecture guide](docs/architecture.md) for the numbered walkthrough
and [Docker sbx guide](docs/sandbox.md) for isolation and network policy.

## Quickstart

The workshop targets an Apple Silicon Mac. Install Git, Python 3.11–3.13,
[uv](https://docs.astral.sh/uv/), [Ollama](https://ollama.com/), and Docker Sandboxes.
Sandbox setup also requires a Docker account. See the
[setup guide](docs/quickstart.md) for platform notes.

Install sbx on macOS:

```bash
brew tap docker/tap
brew install docker/tap/sbx
```

Clone the lab and prepare the sandbox:

```bash
git clone https://github.com/rudrakshkarpe/Nerdearla-BA-privacy-first-search-lab.git
cd Nerdearla-BA-privacy-first-search-lab

./workshop login
./workshop prepare
./workshop doctor
./workshop privacy-check
```

Preparation downloads the corpus and models, installs dependencies and OpenCode,
starts the services, and indexes the PDFs. Complete it before the workshop;
first-run downloads need internet access. No hosted-model API key is required.

For a host-only dry run, install Node/npm and use:

```bash
./workshop prepare --local
./workshop doctor --local
./workshop demo --local
```

Local mode uses SQLite for vector search and runs without sbx isolation.

## Run the demo

```bash
./workshop demo
```

Press **Enter** to advance, **s** to skip, or **q** to exit. The walkthrough covers
corpus inspection, ingestion, semantic search, exact filters, repayment schedules,
MCP discovery, local model tool calls, and sandbox network controls. Each command
is displayed before it runs; a failed step prints a resume command.

```bash
./workshop demo --from-step 4   # Resume at semantic search
./workshop demo --auto         # Rehearse without pauses
./workshop stop                # Stop the workshop sandbox
```

Add `--local` to demo commands for a host-only run. See the
[presenter runbook](docs/presenter.md) for the 60-minute session and
[exercises](docs/exercises.md) for attendee activities.

## Ask your own questions

Open the configured OpenCode harness after preparation:

```bash
./workshop opencode             # Inside Docker sbx
./workshop opencode --local     # Host-only mode
```

Try these prompts:

- “What does DEMO-LA-2026-001 say about voluntary prepayment? Cite the page.”
- “List quarterly loans above $10 million using exact filters.”
- “Show the repayment schedule for DEMO-LA-2026-001.”

The workshop agent has five read-only MCP tools:

| Tool | Purpose |
|---|---|
| `search_documents` | Find similar passages and clauses |
| `get_passage` | Retrieve a specific passage with its source |
| `list_documents` | Filter exact document metadata |
| `get_repayment_schedule` | Read structured repayment rows |
| `corpus_status` | Inspect corpus and index state |

The MCP endpoint is `http://127.0.0.1:8765/mcp` inside the sandbox, or on the host
in local mode. See the [tool reference](docs/mcp-tools.md) for schemas and limits.

## Corpus

The lab uses **40 fictional loan agreements** from the supplied
[Drive folder](https://drive.google.com/drive/folders/1hSegm8i5YgFJfEuHNIDEigXVIDf_5kjv).
Preparation downloads them into `data/source/`; the repository contains the
[provenance manifest](data/manifest.json), not the PDFs.

The parser is tailored to these specimens. Source hashes, page numbers, and chunk
IDs connect retrieved evidence to the original document. See
[data handling](data/README.md) and [ingestion](docs/ingestion.md) before adapting
it to another corpus.

## Privacy boundaries

Models and indexes run locally. The sandbox is configured to allow the local
inference endpoint and deny unrelated outbound traffic; `privacy-check` audits
the effective policy. Source documents and tool results remain untrusted evidence.

This is a single-user workshop: MCP binds to loopback without user authentication,
and local storage is not automatically encrypted. PDFs, indexes, logs, and
conversations stay out of Git. See [security and scope](SECURITY.md) for details.

## Guides

| Guide | What it covers |
|---|---|
| [Quickstart](docs/quickstart.md) | Prerequisites and setup modes |
| [Architecture](docs/architecture.md) | Data flow, component ownership, and design choices |
| [Docker sbx](docs/sandbox.md) | Sandbox configuration and local inference access |
| [Ingestion](docs/ingestion.md) | Parsing, chunking, provenance, and index lifecycle |
| [MCP tools](docs/mcp-tools.md) | Tool schemas, pagination, and evidence |
| [Exercises](docs/exercises.md) | Hands-on experiments |
| [Presenter runbook](docs/presenter.md) | Session timing and demo delivery |
| [Operations](docs/operations.md) | Troubleshooting, services, and cleanup |

See [Contributing](CONTRIBUTING.md) for development and testing. Code and
documentation are [MIT licensed](LICENSE); documents, models, and third-party
assets retain their own terms.
