# Presenter runbook: 60 minutes

## Before the room opens

- Complete `./workshop prepare` with the actual sandbox, not only `--local`.
- Run `./workshop login` first if the Docker device session may have expired.
- Run `./workshop doctor`, `./workshop privacy-check`, and the small-model rehearsal.
- Check every effective allow rule and corresponding deny evidence. No npm, PyPI,
  model downloads, or container builds should be needed during presentation.
- Run one semantic query and one model request to warm caches. Stop unrelated
  heavyweight inference jobs. Keep the 3B/16K configuration for the dry run.
- Open the README's numbered end-to-end workflow diagram, an agreement PDF, and two terminals:
  the walkthrough and `sbx`/policy logs.
- Use a large terminal font. Keep `.local/` transcripts off shared/public screens
  if attendees substitute private data later.
- Have the source PDFs and cached dependencies already present. Never silently
  substitute a hosted model if venue networking or local inference fails.

## Timing and teaching points

| Minutes | Activity | Audience takeaway |
|---|---|---|
| 0–5 | Follow steps 3–8 across the workflow diagram | “Local” is a property of every data hop |
| 5–10 | Inspect the fictional corpus and page provenance | Evidence precedes embeddings |
| 10–18 | Parse, chunk, inspect one chunk, explain embeddings | Chunk boundaries trade context for precision |
| 18–25 | Semantic clause search and exact portfolio filters | Top-k search cannot establish exhaustive coverage |
| 25–30 | Read repayment rows; repeat ingestion | Tables need structure; ingestion needs idempotence |
| 30–40 | MCP discovery and OpenCode tool-call trace | The harness orchestrates; the model selects tools |
| 40–47 | Blocked external request with local retrieval succeeding | Policy is visible enforcement, not a promise in a prompt |
| 47–53 | Unsupported question and small-model limitations | A citation is not automatic factual verification |
| 53–60 | Adapter comparison, exercises, questions | Components are replaceable; contracts matter |

## Enter-to-advance flow

```bash
./workshop demo
```

The walkthrough prints each command before running it. Explain the output before
pressing Enter again. `s` skips a step, `q` exits, and failures print the exact
`--from-step` command to resume. The automatic mode is for rehearsal, not a reason
to race through evidence inspection.

1. **Preflight:** show 40 ready documents and the locked embedding identity.
2. **Corpus:** identify the parser/model metadata and local storage boundary.
3. **Idempotence:** rerun ingestion; expect 40 unchanged, zero newly indexed.
4. **Semantic search:** point at page 2 and open the matching PDF page.
5. **Exact filter:** show 10 loans strictly above $10 million with quarterly payments.
6. **Schedule:** distinguish payment, interest, principal, and closing balance.
7. **MCP:** show the five tool names and input validation working.
8. **Harness:** watch the actual tool request, evidence, and answer. The prepared
   small-model prompt requests an exact quote so the audience can verify it.
   A failed quotation/citation gate stops the walkthrough.
9. **Absence:** ask for an actual governing jurisdiction and inspect the limitation
   stated in the specimen. This step also requires a matching evidence quote.
   Do not claim the entire corpus proves legal compliance.
10. **Boundary:** show denied external traffic and a successful local search.

## Phrases worth saying explicitly

“These embeddings are derived from the documents; they are not anonymization.”

“The model is allowed to ask for evidence. It is not allowed to administer the
database or decide which network destinations to permit.”

“This exact filter is exhaustive over the ready catalog. These three semantic
search hits are not exhaustive over the corpus.”

“The source text is untrusted. A sentence inside a loan agreement cannot grant
permission to execute a command.”

“We tested a small quotation task with a 3B model. That does not establish that
every answer from it will be accurate.”

## If something fails on stage

| Failure | Recovery |
|---|---|
| Model is slow | Show the returned passages first; use the short exact-quote prompt and warmed 3B model |
| Model invents a claim | Compare it to the evidence openly; this is a grounding failure, not a reason to hide the trace |
| Sandbox cannot start | Explain the limitation; use the clearly labeled local path for ingestion/MCP only |
| Compose services exited between sessions | Run `./workshop doctor`; it restores cached services before checking them |
| Harness prints a tool call as text | Rerun `./workshop prepare` to restore the pinned OpenCode version and provider cache |
| External access succeeds | Stop the privacy claim and inspect effective allow rules |
| Retrieval finds the wrong page | Narrow by agreement ID and inspect the query; do not treat a score as confidence |
| Service fails | Use the health and logs commands in the operations guide, then resume the failed step |

Do not present saved output as a live execution. If using a previous transcript,
label it as recorded and state which environment produced it.
