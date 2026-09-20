# Model references

The workshop's generation reference is
**[Gemma 4 E4B IT — `google/gemma-4-E4B-it`](https://huggingface.co/google/gemma-4-E4B-it)**.
Use this name in the architecture, diagram, and presentation when discussing
local generation and tool selection. The corpus embedding model remains
`nomic-embed-text:v1.5`.

## Reference versus runnable setup

| Item | Model or setting |
|---|---|
| Documentation and diagram | Gemma 4 E4B IT |
| Existing executable generation model | Llama 3.2 3B (`llama3.2:latest`) |
| Existing OpenCode model alias | `privacy-lab-local` |
| Existing demo context / output budget | 16,384 / 2,048 tokens |
| Document and query embeddings | `nomic-embed-text:v1.5` |

This is a documentation update. It does not download weights, change the
[Modelfile](Modelfile), change [OpenCode configuration](../opencode.json), or
re-run the sandbox and model rehearsals. `./workshop prepare` retains its
existing behavior. Recorded timings and tool-call results in the
[verification record](../docs/verification.md) refer to the model used in those
runs, not to Gemma.

The Hugging Face repository identifies the reference model; it is not an Ollama
model tag. A runtime migration would require selecting a compatible local build,
updating model preparation and harness metadata, and rehearsing actual MCP calls
and citation checks with that build.
