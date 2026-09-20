# Quickstart: prepare once, present locally

## Choose your path

| Path | Purpose | Isolation claim |
|---|---|---|
| Docker sbx + Compose + Qdrant | Main workshop architecture | MicroVM and audited egress policy |
| `--local` + SQLite vectors | Fast development and small-model dry run | Local processing only; no sandbox containment |

Both paths use the same parser, embeddings, catalog, five MCP tools, and OpenCode
configuration. Do not describe a local-mode run as a successful sbx demonstration.

## Prerequisites

- Apple Silicon Mac is the initial target. Linux with a working sbx installation
  can use the same architecture; Windows/WSL is not yet rehearsed.
- Python 3.11–3.13, `uv`, Ollama, and Git.
- Main path: Docker Sandboxes (`sbx` 0.43.0 was used to validate the kit) and a
  Docker account. Docker Desktop is useful for standalone Compose development;
  sbx uses its own Docker daemon.
- Local path: Node/npm to install pinned OpenCode 1.18.31 under `.local/`.
- Download space for models, sandbox template, service images, and packages.
  Prepare well before the session; first-run downloads depend on your connection.

On macOS, install sbx from Docker's official Homebrew tap:

```bash
brew tap docker/tap
brew install docker/tap/sbx
sbx login
```

Complete Docker's browser sign-in yourself. Never paste credentials into the
repository or an agent conversation. Existing global sandbox policy is not reset
by the workshop script.

## Clone and prepare

```bash
git clone https://github.com/rudrakshkarpe/privacy-first-search-lab.git
cd privacy-first-search-lab
./workshop prepare
./workshop doctor
./workshop privacy-check
./workshop demo
```

Preparation starts a dedicated host Ollama process at `127.0.0.1:11435` with
`OLLAMA_NO_CLOUD=1`. It shares your existing model files, but does not change your
regular Ollama service at port 11434. `/api/status` must report cloud disabled.

The script downloads the corpus if absent, obtains the small language model and
embedding model, creates the sandbox, temporarily permits dependency destinations,
builds the Compose services, indexes the corpus, and removes its preparation
allow rules. Failures stop the script; they are not treated as successful setup.
Review effective policy before showing a privacy claim.

## Fast dry run without sandbox authentication

```bash
./workshop prepare --local
./workshop doctor --local
./workshop demo --local
```

This uses Llama 3.2 3B with a **16K demo context**, not GPT-OSS or another large
model. OpenCode's general coding guidance recommends larger context windows;
this deliberately constrained, read-only five-tool exercise is smaller. Keep
requests short and inspect evidence. Small models can call tools correctly and
still produce unsupported prose.

Use `./workshop opencode --local` for an interactive harness, or omit `--local`
for the sandbox. No hosted-provider API key is required for this workshop.

## Presentation controls

```bash
./workshop demo --from-step 4
./workshop demo --auto
```

Enter runs the displayed step. `s` skips it and `q` exits. A failed command stops
the walkthrough and prints a resume command. `--auto` is for rehearsal/recording;
it does not conceal failures. Model wording is nondeterministic even at temperature
zero. The model can vary its tool calls; the script does not fake them.

## Corpus availability

The provided Drive folder is an inbound preparation source, not a runtime search
dependency. The downloaded PDFs live under `data/source/` and stay out of Git and
Docker build contexts. If automated Drive download fails, download the folder
manually, extract it under `data/source/`, and run the inspect command in
[the exercises](exercises.md). Do not add real private records to the public repo.

## Before you announce “demo ready”

Read [verification status](verification.md). Require the full corpus, source-hash
checks, MCP handshake, meaningful retrieval checks, an observed small-model tool
call, and the actual sandbox network checks. A valid Compose file or kit alone is
not evidence that the sandbox ran.
