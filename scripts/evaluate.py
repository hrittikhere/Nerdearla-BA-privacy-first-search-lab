"""Small, source-checked retrieval acceptance set. Requires a populated local index."""

import json
import time

from privacy_lab.config import Settings
from privacy_lab.service import SearchService

CASES = [
    ("fees and voluntary prepayment", "DEMO-LA-2026-001", 2, "revised schedule"),
    ("payment default cure period", "DEMO-LA-2026-001", 2, "15 calendar days"),
    ("transfer and confidentiality disclosures", "DEMO-LA-2026-001", 2, "confidential"),
    ("governing law dispute forum jurisdiction", "DEMO-LA-2026-001", 2, "not designated"),
]


def main():
    service = SearchService(Settings())
    outcomes = []
    for query, doc, page, phrase in CASES:
        started = time.monotonic()
        hits = service.search(query, 3, doc)["hits"]
        passed = any(h["page"] == page and phrase in h["text"] for h in hits)
        outcomes.append(
            {
                "query": query,
                "passed": passed,
                "seconds": round(time.monotonic() - started, 3),
                "returned_pages": [h["page"] for h in hits],
            }
        )
    exact = service.catalog.list(frequency="quarterly", min_principal_cents=1000000001)
    outcomes.append(
        {
            "case": "quarterly loans strictly above $10 million",
            "passed": exact["total"] == 10,
            "total": exact["total"],
        }
    )
    rows = service.schedule("DEMO-LA-2026-001")["rows"]
    outcomes.append(
        {
            "case": "agreement 001 amortizes in 12 rows",
            "passed": len(rows) == 12 and rows[-1]["closing_balance_cents"] == 0,
        }
    )
    print(json.dumps({"passed": all(o["passed"] for o in outcomes), "checks": outcomes}, indent=2))
    return 0 if all(o["passed"] for o in outcomes) else 1


if __name__ == "__main__":
    raise SystemExit(main())
