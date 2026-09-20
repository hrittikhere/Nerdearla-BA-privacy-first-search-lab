import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path


class Catalog:
    def __init__(self, path: Path):
        self.path = path
        with self.connect() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY, state TEXT NOT NULL, data TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS config (key TEXT PRIMARY KEY, value TEXT NOT NULL);
            """)

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=30)
        try:
            with db:
                yield db
        finally:
            db.close()

    def config(self) -> dict | None:
        with self.connect() as db:
            row = db.execute("SELECT value FROM config WHERE key='index'").fetchone()
        return json.loads(row[0]) if row else None

    def ensure_config(self, identity: dict):
        existing = self.config()
        if existing and existing != identity:
            raise ValueError(
                "Index identity changed (model/digest/parser/backend). Use a fresh index."
            )
        with self.connect() as db:
            db.execute("INSERT OR IGNORE INTO config VALUES ('index', ?)", (json.dumps(identity),))

    def put(self, doc: dict, state: str):
        with self.connect() as db:
            db.execute(
                "INSERT OR REPLACE INTO documents VALUES (?, ?, ?)",
                (doc["document_id"], state, json.dumps(doc)),
            )

    def get(self, document_id: str) -> dict | None:
        with self.connect() as db:
            row = db.execute(
                "SELECT data FROM documents WHERE id=? AND state='ready'", (document_id,)
            ).fetchone()
        return json.loads(row[0]) if row else None

    def list(
        self,
        *,
        frequency: str | None = None,
        min_principal_cents: int = 0,
        category: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> dict:
        if frequency not in {None, "monthly", "quarterly"}:
            raise ValueError("frequency must be monthly or quarterly")
        if not 1 <= limit <= 50 or offset < 0 or min_principal_cents < 0:
            raise ValueError("Invalid pagination or principal filter")
        with self.connect() as db:
            rows = [
                json.loads(r[0])
                for r in db.execute("SELECT data FROM documents WHERE state='ready' ORDER BY id")
            ]
        rows = [
            d
            for d in rows
            if d["principal_cents"] >= min_principal_cents
            and (frequency is None or d["frequency"] == frequency)
            and (category is None or d["category"] == category)
        ]
        return {
            "total": len(rows),
            "offset": offset,
            "next_offset": offset + limit if offset + limit < len(rows) else None,
            "documents": [
                {k: v for k, v in d.items() if k != "schedule"}
                for d in rows[offset : offset + limit]
            ],
        }

    def stats(self) -> dict:
        with self.connect() as db:
            states = dict(db.execute("SELECT state, COUNT(*) FROM documents GROUP BY state"))
        return {"states": states, "identity": self.config()}
