# MCP tools: evidence, not administrative authority

The server speaks Streamable HTTP at `http://127.0.0.1:8765/mcp` and can also run
over stdio. OpenCode calls the tools; Ollama receives their descriptions and
results through OpenCode. Ollama does not connect to MCP itself.

| Tool | Purpose | Bounds |
|---|---|---|
| `search_documents` | Semantic clause retrieval, optionally within one agreement | 2,000-character query, 1–10 hits |
| `get_passage` | Read a returned chunk by UUID | One bounded chunk; no file paths |
| `list_documents` | Exact category, frequency, and inclusive minimum-principal filter | 1–50 documents, explicit pagination |
| `get_repayment_schedule` | Read validated PDF table rows | 1–24 rows, explicit pagination |
| `corpus_status` | Inspect counts and embedding identity | No document content |

All tools advertise read-only annotations. Those annotations describe behavior;
the actual implementation also has no shell, upload, arbitrary URL, ingestion,
deletion, or arbitrary file-read tool. Schema validation rejects excessive limits.
HTTP Host/Origin validation provides DNS-rebinding protection. There is no user
authentication: bind this single-user demo to loopback, never a public interface.

## Example exchange

```json
{
  "name": "search_documents",
  "arguments": {
    "query": "early repayment fees and restrictions",
    "document_id": "DEMO-LA-2026-001",
    "limit": 3
  }
}
```

Results contain `id`, `document_id`, `source`, `sha256`, `page`, `ordinal`, `text`,
`citation`, `score`, and an `untrusted_document_content` marker. The marker is an
instruction to the consuming application about provenance, not a security filter.
The model must still treat quoted document instructions as evidence only.

For “above $10 million,” pass `min_principal_cents: 1000000001`. The filter is
inclusive, so passing `1000000000` means “at least $10 million.” Money is always
integer USD cents, not floating point dollars. Follow `next_offset` until null
before making a claim about all matching documents.

## Separation of duties

The presenter ingests or removes sources through the CLI. OpenCode's workshop
agent has only these five MCP tools enabled. Code editing, shell commands, web
tools, other agents, and arbitrary file reads are denied. To create a report,
the presenter can save the harness's output locally; the model does not need
write access to the corpus or database.

The current SDK dependency deliberately stays on the supported MCP Python 1.x
line (`<2`) and is locked in `uv.lock`. The contract is tested through a real
stdio handshake and an HTTP smoke command, not just direct Python function calls.
