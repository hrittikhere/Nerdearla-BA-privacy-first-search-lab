# Model references

The workshop's generation model is
**[Gemma 4 E2B IT](https://huggingface.co/google/gemma-4-E2B-it)**, pulled from
Ollama as `gemma4:e2b`. Use this name in the architecture, diagram, and
presentation when discussing local generation and tool selection. The corpus
embedding model remains `nomic-embed-text:v1.5`.

## Runnable setup

| Item | Model or setting |
|---|---|
| Documentation and diagram | Gemma 4 E2B IT |
| Executable generation model | Gemma 4 E2B IT (`gemma4:e2b`) |
| OpenCode model alias | `privacy-lab-local` |
| Demo context / output budget | 16,384 / 2,048 tokens |
| Document and query embeddings | `nomic-embed-text:v1.5` |

Documentation and runtime now name the same generation model. `./workshop
prepare` pulls `gemma4:e2b`, then builds the `privacy-lab-local` alias from
[the Modelfile](Modelfile), which fixes the demo context at 16,384 tokens and
temperature at zero. [OpenCode configuration](../opencode.json) selects that
alias through the local provider.

The Hugging Face repository identifies the reference weights; `gemma4:e2b` is the
Ollama tag that serves them locally, and it is the instruction-tuned build
([`google/gemma-4-E2B-it`](https://huggingface.co/google/gemma-4-E2B-it)) rather than
the base model, because the workshop needs tool selection. E2B is the "effective 2B"
edge build of Gemma 4: roughly 5.1B stored parameters at Q4_K_M, about 7.2 GB on disk.
Budget download time and unified memory accordingly.

Changing the generation model does not invalidate the index: only the embedding
model identity and digest are recorded in it. Changing the embedding model or
the parser still requires a fresh index.

Timings and tool-call results in the [verification record](../docs/verification.md)
state which model produced them. Temperature zero is not a guarantee of
factuality or identical output, and tool-call reliability differs between models.
