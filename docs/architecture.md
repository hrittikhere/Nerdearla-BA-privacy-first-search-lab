# Architecture and trust boundaries

[![End-to-end workshop workflow with product logos, runtime boundaries, data stores, and numbered ingestion and question-answering paths](assets/workshop-workflow-gemma4.svg)](assets/workshop-workflow-gemma4.svg)

The diagram is the presentation view of the system. The sections below explain
the ownership and security limits behind each connection. Its numbered route is
also described in the [main workshop guide](../README.md#architecture-and-the-role-of-docker-sbx).

## Model reference

The diagram and the runtime both use
**[Gemma 4 E2B IT](https://huggingface.co/google/gemma-4-E2B-it)** (`gemma4:e2b`)
for generation and tool selection. `nomic-embed-text:v1.5` remains the embedding
model. See [model references](../models/README.md) for the download and memory budget.

## Two flows, one local system

**Ingestion:** source PDF → page text → bounded chunks → local embedding model →
vector store. A separate SQLite catalog records exact loan metadata and source
hashes. Ingestion is an explicit administrative command, never an agent tool.

**Question answering:** OpenCode → local LLM → MCP tool request → search service
→ local query embedding → vector lookup → cited passages → local LLM → answer.
MCP transports tool descriptions, arguments, and results; it is neither a model
nor a vector database. OpenCode orchestrates the loop; Ollama executes inference.

## Why both a vector store and a catalog?

Semantic retrieval answers “where does an agreement discuss early repayment?”
It retrieves a limited set of similar passages, not an exhaustive portfolio.
Exact filtering answers “which quarterly loans exceed $10 million?” against
validated metadata. Never use top-k vector hits to claim that every matching loan
has been found. Store money as integer cents and expose pagination explicitly.

## Components

| Component | Owns | Does not own |
|---|---|---|
| Importer | Source validation, hashes, page extraction | Model-generated facts |
| Chunker | Page-local text and stable citation IDs | Legal interpretation |
| Ollama embeddings | Local numeric representations | Access control |
| Vector adapter | Upsert, search, retrieve, source removal | Agent behavior |
| SQLite catalog | Exact metadata, ingestion manifest | Semantic ranking |
| MCP server | Validated, bounded read-only tools | Shell execution or arbitrary file reads |
| OpenCode | Tool orchestration and cited synthesis | Evidence authority |
| sbx | MicroVM and outbound policy | Host Ollama's own outbound traffic |

## Trust boundaries

1. Only the workshop directory is shared with the sandbox. Shared host files remain
   reachable according to mount permissions; isolation does not make a shared
   writable checkout immutable.
2. Compose uses the sandbox Docker daemon. Do not mount the host Docker socket,
   home directory, SSH keys, or cloud credentials.
3. Qdrant is reachable only by the search services on the private Compose network.
   Its data includes original text and must be protected like the PDFs.
4. OpenCode reaches a loopback-bound MCP endpoint within the microVM. This is a
   single-user demo boundary, not multi-user authorization.
5. Host Ollama is a deliberate, narrowly scoped local endpoint. Disable its cloud
   functionality separately and use only downloaded model identifiers.
6. Document contents and tool results are untrusted evidence. Instructions inside
   them cannot grant permission to run commands, fetch URLs, or change policy.
7. Logs and session history can contain prompts and passages. Keep them local;
   do not enable session sharing or commit rehearsal outputs.

## Preparation versus presentation

Preparation may require internet access for sbx authentication, image pulls,
packages, corpus download, and model download. Do this before the workshop.
Presentation uses cached artifacts. Effective policy must be inspected: selecting
Locked Down alone is not proof, because kits can add allow rules.

Privacy verification must check policy decisions, successful local requests, and
blocked external requests. A timeout alone does not establish a policy block.
Test traffic originating in both the agent environment and the service containers.
Host Ollama needs a separate configuration check because it is outside sbx.

## Reliability and honest limits

- Retrieval scores are similarity scores, not confidence or legal certainty.
- A cited passage supports only what it actually says. Unsupported questions must
  produce an explicit lack-of-evidence response.
- PDF layout extraction can lose table structure. Do not calculate balances by
  asking an LLM to infer columns from flattened text.
- Source replacement and re-ingestion must remove stale chunks and invalidate
  incompatible embedding dimensions or model identities.
- Index storage is local, not automatically encrypted. Host disk protection and
  retention remain operational responsibilities.
- A 24 GB Mac is the initial rehearsal target. Model/context selection must be
  measured with the sandbox running; a large advertised context is not a latency
  or memory guarantee.

## References

- [Docker Sandboxes](https://docs.docker.com/ai/sandboxes/)
- [Local network policy](https://docs.docker.com/ai/sandboxes/governance/access-controls/local/)
- [Accessing host services](https://docs.docker.com/ai/sandboxes/workflows/development/)
- [OpenCode MCP configuration](https://opencode.ai/docs/mcp-servers/)
- [Ollama and OpenCode](https://docs.ollama.com/integrations/opencode)
- [Hrittik Roy's sbx walkthrough](https://hrittikhere.com/posts/sandbox-claude-code-mcp-docker-sbx)

Commands and behavior must be checked against the installed versions. In
particular, sbx is evolving; older walkthrough syntax may differ from current CLI.
