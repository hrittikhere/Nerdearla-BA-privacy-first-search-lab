import os
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse


def local_url(url: str, hosts: set[str]) -> str:
    parsed = urlparse(url)
    if (
        parsed.scheme != "http"
        or parsed.hostname not in hosts
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
        or parsed.path not in ("", "/")
    ):
        raise ValueError(f"Expected an explicit local HTTP endpoint; got {url!r}")
    return url.rstrip("/")


@dataclass
class Settings:
    index_dir: Path = field(default_factory=lambda: Path(os.getenv("LAB_INDEX_DIR", "data/index")))
    backend: str = field(default_factory=lambda: os.getenv("LAB_BACKEND", "sqlite"))
    ollama_url: str = field(
        default_factory=lambda: os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
    )
    embedding_model: str = field(
        default_factory=lambda: os.getenv("EMBEDDING_MODEL", "nomic-embed-text:v1.5")
    )
    qdrant_url: str = field(
        default_factory=lambda: os.getenv("QDRANT_URL", "http://127.0.0.1:6333")
    )
    collection: str = "privacy_lab_v1"

    def __post_init__(self):
        if self.backend not in {"sqlite", "qdrant"}:
            raise ValueError("LAB_BACKEND must be sqlite or qdrant")
        self.ollama_url = local_url(
            self.ollama_url, {"localhost", "127.0.0.1", "host.docker.internal"}
        )
        self.qdrant_url = local_url(self.qdrant_url, {"localhost", "127.0.0.1", "qdrant"})
        if "cloud" in self.embedding_model.lower():
            raise ValueError("Cloud embedding models are not supported")
        self.index_dir.mkdir(parents=True, exist_ok=True)
