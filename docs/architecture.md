# Architecture and trust boundaries

[![End-to-end workshop workflow with product logos, runtime boundaries, data stores, and numbered ingestion and question-answering paths](assets/workshop-workflow.svg)](assets/workshop-workflow.svg)

The top map shows where each component runs; the two workflow lanes show process
order. The same stores and host models serve both paths. Return to the
[main workshop guide](../README.md#workflow) for setup and demo commands.

## Follow the diagram

The blue indexing lane prepares the corpus:

1. Verify the PDF corpus and mount it read-only into the ingestion container.
2. Extract pages, create chunks with stable citation IDs, and validate metadata
   and repayment schedules.
3. Call host Ollama to embed passage text with `nomic-embed-text:v1.5`.
4. Persist vectors and passages in Qdrant; store exact fields, schedules, source
   hashes, and ingestion state in SQLite. Structured fields bypass embedding.

The purple answering lane follows a live audience question:

5. Send the question to OpenCode; the small local model selects a tool and
   OpenCode issues the MCP call.
6. Validate the request and retrieve evidence through the five read-only MCP
   tools. Semantic search uses local query embeddings and Qdrant; exact filters
   and repayment schedules use SQLite.
7. Return passages with document IDs and page numbers, or structured records,
   through MCP to OpenCode. Repeat the tool loop as needed.
8. OpenCode sends the evidence to the local model and displays its cited answer.

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
