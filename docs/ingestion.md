# From a PDF to trustworthy retrieval evidence

## What the importer does

1. Find PDFs under the explicitly supplied source directory.
2. Reject symlinks, files above 25 MiB, encrypted PDFs, and more than 250 pages.
3. Extract text locally with pypdf. Empty/scanned pages fail with an OCR message;
   nothing is sent to a hosted document parser.
4. Recognize the workshop's specimen layout and extract page-one fields with
   deterministic patterns. Unknown layouts fail, rather than inventing metadata.
5. Parse repayment tables into six columns, preserving source page numbers.
6. Check row arithmetic, installment sequence, balance continuity, and final zero
   balance using integer cents.
7. Split each page into up to 180 words with a 30-word overlap. A chunk never
   crosses a page, making citations simple and auditable.
8. Embed locally in batches of 16 and index only after the source is validated.

This parser is intentionally tailored to the supplied 40 specimens. Adapting it
to arbitrary contracts requires schema/layout validation and a new parser version.
Local OCR is an extension, not a silently available feature.

## Provenance

Each chunk carries a deterministic UUID, document ID, filename, SHA-256, page,
ordinal, and text. The UUID includes parser version and source hash. A changed
file produces new IDs. The SQLite catalog records metadata, schedule rows, parser
version, and readiness state. The embedding identity includes the model's digest,
so reusing a mutable model tag cannot silently mix incompatible embeddings.

The service records `indexing` before replacing vector rows and `ready` only after
success. A failed replacement is marked `failed`; stale or partial passages are
filtered out of retrieval. This is fail-closed per document, not a distributed
transaction between Qdrant and SQLite. Re-run ingestion to repair a failed document.

An unchanged ready document is skipped. Files removed from the source directory
are not silently deleted from the index: `verify-sources` reports the mismatch.
Use the explicit administrative `remove` command, or reset/rebuild the demo index.

## Embeddings and search

The default is `nomic-embed-text:v1.5`. Nomic's document/query prefixes are applied
separately. Embedding truncation is disabled; overlong input must fail visibly.
The response count, dimensions, finite values, and nonzero vectors are validated.

Agreement IDs are exact filters, not semantic text. Otherwise a query containing
an ID can rank the repeated PDF headers above the actual requested clause. The
service removes those IDs from the embedding query and infers a filter when one
unique agreement ID is present.

Qdrant uses cosine similarity. The second implementation stores vectors in SQLite
and performs an exact cosine scan. It is deliberately small and explainable,
with O(N × dimensions) query cost; it is not a replacement for a production ANN
index. Both implementations pass the same search/filter/replacement/removal tests.

## Tables need a different path

Flattened table text remains searchable as evidence, but a generated answer should
not infer column relationships from it. `get_repayment_schedule` returns validated
structured rows. `list_documents` provides exact portfolio predicates. These tools
avoid asking a language model to do exhaustive selection or financial arithmetic
over a handful of vector hits.

## Reproducibility versus performance

Package versions are locked in `uv.lock`; the sandbox and Qdrant images are pinned
by digest. Record model digests during rehearsal because downloaded model tags can
change. Changing the embedding model, parser identity, or backend requires a fresh
index. Use different index directories/collections for independent experiments.
Warm models before walking on stage, and never include model downloads in live
demo timing.
