from pathlib import Path

import pytest

from privacy_lab.config import Settings
from privacy_lab.documents import Chunk
from privacy_lab.service import SearchService


class Embeddings:
    calls = 0

    def identity(self):
        return {"model": "fixture", "digest": "fixed"}

    def embed(self, texts, query=False):
        self.calls += 1
        return [[1.0, 0.0] for _ in texts]


def fixture_document():
    doc = {"document_id": "test", "sha256": "first", "source": "fixture.pdf", "schedule": []}
    chunk = Chunk(
        id="c7e1e0b0-96e1-4c91-bc32-1cf61642a287",
        document_id="test",
        sha256="first",
        source="fixture.pdf",
        page=1,
        ordinal=1,
        text="fictional clause",
    )
    return doc, [chunk]


def test_idempotence_does_not_repeat_embedding_work(tmp_path, monkeypatch):
    monkeypatch.setattr("privacy_lab.service.parse_pdf", lambda _: fixture_document())
    embedder = Embeddings()
    service = SearchService(Settings(index_dir=tmp_path), embedder=embedder)
    assert service.ingest([Path("fixture.pdf")])["indexed"] == 1
    assert service.ingest([Path("fixture.pdf")])["unchanged"] == 1
    assert embedder.calls == 1
    service.remove("test")
    assert service.catalog.get("test") is None
    assert service.catalog.stats()["states"] == {}


def test_failed_vector_write_is_not_visible_and_can_be_retried(tmp_path, monkeypatch):
    monkeypatch.setattr("privacy_lab.service.parse_pdf", lambda _: fixture_document())
    service = SearchService(Settings(index_dir=tmp_path), embedder=Embeddings())
    original = service.store.replace

    def failed(*_):
        raise RuntimeError("simulated interrupted vector write")

    monkeypatch.setattr(service.store, "replace", failed)
    with pytest.raises(RuntimeError, match="interrupted"):
        service.ingest([Path("fixture.pdf")])
    assert service.catalog.get("test") is None
    assert service.catalog.stats()["states"] == {"failed": 1}
    monkeypatch.setattr(service.store, "replace", original)
    assert service.ingest([Path("fixture.pdf")])["indexed"] == 1
    assert service.catalog.get("test") is not None
