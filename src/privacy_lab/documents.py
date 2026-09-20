"""Deterministic parsing for the supplied specimen format; no model extraction."""

import hashlib
import re
import uuid
from decimal import Decimal
from pathlib import Path

from pydantic import BaseModel
from pypdf import PdfReader

PARSER_VERSION = "loan-v1-page-chunks-180-30"


class Chunk(BaseModel):
    id: str
    document_id: str
    source: str
    sha256: str
    page: int
    ordinal: int
    text: str

    @property
    def citation(self) -> str:
        return f"{self.document_id}, p. {self.page}, chunk {self.ordinal}"


def cents(value: str) -> int:
    amount = Decimal(value.replace("$", "").replace(",", "")) * 100
    if amount != amount.to_integral_value():
        raise ValueError("Money must have at most two decimal places")
    return int(amount)


def required(pattern: str, text: str) -> str:
    match = re.search(pattern, text, re.MULTILINE)
    if not match:
        raise ValueError(f"Unsupported specimen layout: missing {pattern}")
    return match.group(1).strip()


def metadata(first_page: str) -> dict:
    """Fail closed if the workshop's known metadata fields are not present."""
    return {
        "document_id": required(r"(DEMO-LA-\d{4}-\d{3})", first_page),
        "borrower": required(r"Loan agreement\s+Fictional[^\n]*\n([^\n]+)", first_page),
        "category": required(r"^([A-Z ]+) / CUSTOMER \d+ OF \d+", first_page).lower(),
        "principal_cents": cents(required(r"PRINCIPAL / USD\s+(\$[\d,]+(?:\.\d{2})?)", first_page)),
        "annual_rate_percent": required(r"FIXED ANNUAL RATE\s+([\d.]+)%", first_page),
        "term_months": int(required(r"LOAN TERM\s+(\d+) months", first_page)),
        "frequency": required(r"Repayment frequency\s+\d+ (monthly|quarterly)", first_page),
        "metadata_page": 1,
    }


def page_chunks(text: str, document_id: str, source: str, digest: str, page: int) -> list[Chunk]:
    words = text.split()
    chunks = []
    for start in range(0, len(words), 150):
        body = " ".join(words[start : start + 180])
        ordinal = len(chunks) + 1
        key = f"{PARSER_VERSION}:{document_id}:{digest}:{page}:{ordinal}"
        chunks.append(
            Chunk(
                id=str(uuid.uuid5(uuid.NAMESPACE_URL, key)),
                document_id=document_id,
                source=source,
                sha256=digest,
                page=page,
                ordinal=ordinal,
                text=body,
            )
        )
        if start + 180 >= len(words):
            break
    return chunks


def schedule_rows(text: str, page: int) -> list[dict]:
    """Recover complete six-column rows, never guess absent cells."""
    if "Annex A | Repayment schedule" not in text:
        return []
    money = r"(\$[\d,]+\.\d{2})"
    pattern = rf"(?:^|\n)\s*(\d+)\s+(\d{{1,2}} [A-Za-z]{{3}} \d{{4}})\s+{money}\s+{money}\s+{money}\s+{money}"
    rows = []
    for m in re.finditer(pattern, text):
        payment, interest, principal, balance = [cents(v) for v in m.groups()[2:]]
        if payment != interest + principal:
            raise ValueError(f"Schedule arithmetic mismatch on page {page}")
        rows.append(
            {
                "installment": int(m[1]),
                "due_date": m[2],
                "payment_cents": payment,
                "interest_cents": interest,
                "principal_cents": principal,
                "closing_balance_cents": balance,
                "page": page,
            }
        )
    if not rows:
        raise ValueError(f"Schedule page {page} could not be parsed; OCR/layout review required")
    return rows


def parse_pdf(path: Path) -> tuple[dict, list[Chunk]]:
    if path.is_symlink() or path.stat().st_size > 25 * 1024 * 1024:
        raise ValueError("Symlinks and PDFs larger than 25 MiB are not accepted")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    reader = PdfReader(path)
    if reader.is_encrypted or not 1 <= len(reader.pages) <= 250:
        raise ValueError("Encrypted PDFs and PDFs outside 1–250 pages are not accepted")
    pages = [p.extract_text() or "" for p in reader.pages]
    if any(len(p.strip()) < 30 for p in pages):
        raise ValueError("Empty or scanned page: local OCR is required before ingestion")
    doc = metadata(pages[0])
    doc.update(source=path.name, sha256=digest, pages=len(pages), parser=PARSER_VERSION)
    doc["schedule"] = [row for i, p in enumerate(pages, 1) for row in schedule_rows(p, i)]
    expected = doc["term_months"] // (3 if doc["frequency"] == "quarterly" else 1)
    rows = doc["schedule"]
    if [r["installment"] for r in rows] != list(range(1, expected + 1)):
        raise ValueError("Incomplete or duplicated repayment schedule")
    balance = doc["principal_cents"]
    for row in rows:
        balance -= row["principal_cents"]
        if row["closing_balance_cents"] != balance:
            raise ValueError("Schedule principal balance does not reconcile")
    if balance != 0:
        raise ValueError("Schedule does not fully amortize")
    chunks = [
        c
        for i, p in enumerate(pages, 1)
        for c in page_chunks(p, doc["document_id"], path.name, digest, i)
    ]
    doc["chunks"] = len(chunks)
    return doc, chunks
