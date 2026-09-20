import math

import httpx


class OllamaEmbeddings:
    def __init__(self, url: str, model: str):
        self.url, self.model = url, model

    def identity(self) -> dict:
        # Respect sbx-managed proxy variables. Redirects are intentionally disabled.
        with httpx.Client(timeout=30) as client:
            response = client.get(f"{self.url}/api/tags")
            response.raise_for_status()
            models = response.json()["models"]
        selected = next((m for m in models if m["name"] == self.model), None)
        if not selected or not selected.get("digest") or selected.get("remote_host"):
            raise ValueError(f"Download local embedding model {self.model!r} before ingestion")
        return {"model": self.model, "digest": selected["digest"]}

    def embed(self, texts: list[str], *, query: bool = False) -> list[list[float]]:
        if not texts:
            return []
        # Nomic's trained task prefixes improve retrieval. Other models receive raw text.
        prefix = (
            ("search_query: " if query else "search_document: ")
            if self.model.startswith("nomic-embed-text")
            else ""
        )
        with httpx.Client(timeout=180) as client:
            response = client.post(
                f"{self.url}/api/embed",
                json={
                    "model": self.model,
                    "input": [prefix + t for t in texts],
                    "truncate": False,
                    "keep_alive": "5m",
                },
            )
            response.raise_for_status()
        vectors = response.json()["embeddings"]
        if len(vectors) != len(texts):
            raise ValueError("Embedding response count mismatch")
        dimension = len(vectors[0])
        if not dimension or any(
            len(v) != dimension
            or not all(math.isfinite(x) for x in v)
            or sum(x * x for x in v) == 0
            for v in vectors
        ):
            raise ValueError("Invalid embedding response")
        return vectors
