"""Identical retrieval contract for Qdrant and an educational SQLite exact scan."""

import json
import math
import sqlite3
from pathlib import Path
from typing import Protocol

from qdrant_client import QdrantClient, models

from privacy_lab.documents import Chunk


class VectorStore(Protocol):
    def replace(
        self, document_id: str, chunks: list[Chunk], vectors: list[list[float]]
    ) -> None: ...
    def search(self, vector: list[float], limit: int, document_id: str | None) -> list[dict]: ...
    def get(self, chunk_id: str) -> dict | None: ...
    def delete(self, document_id: str) -> None: ...


def cosine(a: list[float], b: list[float]) -> float:
    if len(a) != len(b):
        raise ValueError("Embedding dimension mismatch")
    norm = math.sqrt(sum(x * x for x in a) * sum(x * x for x in b))
    if not norm:
        raise ValueError("Zero vector is not a valid embedding")
    return sum(x * y for x, y in zip(a, b, strict=True)) / norm


class SQLiteVectors:
    """Small-corpus baseline, O(N*d) search. Not a scalable ANN database."""

    def __init__(self, path: Path):
        self.path = path
        with sqlite3.connect(path) as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS vectors (id TEXT PRIMARY KEY, doc TEXT, payload TEXT, vector TEXT)"
            )

    def replace(self, document_id, chunks, vectors):
        with sqlite3.connect(self.path) as db:
            db.execute("DELETE FROM vectors WHERE doc=?", (document_id,))
            db.executemany(
                "INSERT INTO vectors VALUES (?, ?, ?, ?)",
                [
                    (c.id, document_id, c.model_dump_json(), json.dumps(v))
                    for c, v in zip(chunks, vectors, strict=True)
                ],
            )

    def search(self, vector, limit, document_id=None):
        with sqlite3.connect(self.path) as db:
            rows = db.execute(
                "SELECT payload, vector FROM vectors WHERE (? IS NULL OR doc=?)",
                (document_id, document_id),
            ).fetchall()
        hits = [{"chunk": json.loads(p), "score": cosine(vector, json.loads(v))} for p, v in rows]
        return sorted(hits, key=lambda h: (-h["score"], h["chunk"]["id"]))[:limit]

    def get(self, chunk_id):
        with sqlite3.connect(self.path) as db:
            row = db.execute("SELECT payload FROM vectors WHERE id=?", (chunk_id,)).fetchone()
        return json.loads(row[0]) if row else None

    def delete(self, document_id):
        with sqlite3.connect(self.path) as db:
            db.execute("DELETE FROM vectors WHERE doc=?", (document_id,))


class QdrantVectors:
    def __init__(self, url: str, collection: str, client=None):
        self.client = client or QdrantClient(url=url, timeout=30)
        self.collection = collection

    @staticmethod
    def doc_filter(document_id):
        return models.Filter(
            must=[
                models.FieldCondition(key="document_id", match=models.MatchValue(value=document_id))
            ]
        )

    def replace(self, document_id, chunks, vectors):
        dimension = len(vectors[0])
        if not self.client.collection_exists(self.collection):
            self.client.create_collection(
                self.collection,
                vectors_config=models.VectorParams(size=dimension, distance=models.Distance.COSINE),
            )
        info = self.client.get_collection(self.collection)
        if info.config.params.vectors.size != dimension:
            raise ValueError("Qdrant embedding dimension mismatch; use a fresh index")
        self.delete(document_id)
        points = [
            models.PointStruct(id=c.id, vector=v, payload=c.model_dump())
            for c, v in zip(chunks, vectors, strict=True)
        ]
        for start in range(0, len(points), 64):
            self.client.upsert(self.collection, points=points[start : start + 64], wait=True)

    def search(self, vector, limit, document_id=None):
        if not self.client.collection_exists(self.collection):
            return []
        result = self.client.query_points(
            self.collection,
            query=vector,
            limit=limit,
            query_filter=self.doc_filter(document_id) if document_id else None,
            with_payload=True,
        )
        return [{"chunk": p.payload, "score": p.score} for p in result.points]

    def get(self, chunk_id):
        if not self.client.collection_exists(self.collection):
            return None
        rows = self.client.retrieve(self.collection, ids=[chunk_id], with_payload=True)
        return rows[0].payload if rows else None

    def delete(self, document_id):
        if self.client.collection_exists(self.collection):
            self.client.delete(
                self.collection,
                points_selector=models.FilterSelector(filter=self.doc_filter(document_id)),
                wait=True,
            )
