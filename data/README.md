# Corpus handling

`source/` is the local import directory. The supplied sample corpus is committed at
`source/dummy_loan_agreements_40/`; anything else you add under `source/`, and all
derived indexes, are ignored by Git. The Docker build allowlist excludes `source/`, so building an image does not upload
source PDFs to the build context.

The supplied corpus comprises 40 fictional loan agreements and a text customer
index. Its own index identifies all people, addresses, amounts, and entities as
invented. It is a specimen dataset with no selected governing jurisdiction.

`manifest.json` records filenames, SHA-256 hashes, page counts, and chunk counts
for the reviewed source snapshot. It contains no document bodies. Use it to detect
changes to the committed files; `verify-sources` compares them with the index.

```bash
./workshop fetch   # skips the download when the committed PDFs are present
PYTHONPATH=src uv run privacy-lab inspect data/source
```

If importing different documents, use a different index and adapt the deterministic
parser. Do not assume an arbitrary PDF shares the specimen's metadata/table layout.
Do not commit generated embeddings: vector payloads include document passages.
