# ADR 001: Local inference with an isolated search environment

Status: accepted for the workshop implementation.

## Context

The audience should see the complete document-to-answer path and understand where
privacy depends on network policy, mounts, model configuration, and evidence.
The presentation machine is an Apple Silicon Mac with 24 GB memory.

## Decision

Use Python for ingestion and MCP tools, Qdrant as the primary vector store,
SQLite for exact catalog queries, Ollama for local embeddings and generation,
OpenCode as the harness, and Docker sbx around the harness and Compose services.
Keep a second local vector adapter behind the same retrieval contract to make
portability concrete without complicating the primary path.

The presentation and the runtime use
[Gemma 4 E2B IT](https://huggingface.co/google/gemma-4-E2B-it) for generation and
`nomic-embed-text:v1.5` for embeddings; see [model references](../../models/README.md).

Start with read-only agent tools. Administrative ingestion, source replacement,
and reset are explicit CLI actions. Use page-local citations and deterministic
IDs. Store corpus and generated state outside version control.

## Consequences

Host Ollama preserves native acceleration but expands the local trust boundary.
Its cloud settings need separate verification. Synthetic lending documents make
the data flow tangible without presenting a legal or credit decision engine.
Exact filters complement semantic search; a second adapter proves the separation
between retrieval behavior and infrastructure.

Rehearsal is a release gate. Record actual versions, test results, corpus counts,
model latency, and any blocked sandbox setup steps rather than labeling an
untested path demo-ready.
