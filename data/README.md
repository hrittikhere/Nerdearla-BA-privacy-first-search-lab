# Corpus handling

`source/` is the local import directory. It and derived indexes are ignored by Git.
The Docker build allowlist also excludes them, so building an image does not upload
source PDFs to the build context.

The supplied corpus comprises 40 fictional loan agreements and a text customer
index. Its own index identifies all people, addresses, amounts, and entities as
invented. It is a specimen dataset with no selected governing jurisdiction.

`manifest.json` records filenames, SHA-256 hashes, page counts, and chunk counts
for the reviewed source snapshot. It contains no document bodies. Use it to detect
changes in downloads; the source remains subject to its own redistribution terms.
The repository's MIT license applies to code/documentation, not these PDFs.

```bash
./workshop fetch
PYTHONPATH=src uv run privacy-lab inspect data/source
```

If importing different documents, use a different index and adapt the deterministic
parser. Do not assume an arbitrary PDF shares the specimen's metadata/table layout.
Do not commit generated embeddings: vector payloads include document passages.
