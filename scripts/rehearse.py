"""Verify a real harness tool call and an exact evidence quote using the small model."""

import argparse
import json
import re
import subprocess
import time

from workshop import ROOT, SBX, STATE, local_env

PROMPT = (
    'Use loans_search_documents with query "fees and voluntary prepayment", '
    'document_id "DEMO-LA-2026-001", limit 3. After the tool result, return exactly two lines: '
    "line 1 is \"The borrower may prepay on a scheduled due date after paying that date's "
    'scheduled installment." and line 2 is "DEMO-LA-2026-001, page 2". '
    "Do not add another sentence or infer a notice period."
)
EXPECTED = "The borrower may prepay on a scheduled due date after paying that date's scheduled installment."
JURISDICTION_PROMPT = (
    'Use loans_search_documents with query "governing law dispute forum jurisdiction", '
    'document_id "DEMO-LA-2026-001", limit 3. After the tool result, return exactly two lines: '
    'line 1 is "Governing law and dispute forum are intentionally not designated." and '
    'line 2 is "DEMO-LA-2026-001, page 2". Do not add another sentence or jurisdiction.'
)
JURISDICTION_EXPECTED = "Governing law and dispute forum are intentionally not designated."


def assess(events, expected=EXPECTED):
    calls = [e["part"] for e in events if e.get("type") == "tool_use"]
    search = [
        c
        for c in calls
        if c.get("tool") == "loans_search_documents"
        and c.get("state", {}).get("status") == "completed"
    ]
    answer = "\n".join(e["part"]["text"] for e in events if e.get("type") == "text")
    evidence = []
    for call in search:
        try:
            result = json.loads(call["state"]["output"])
            evidence += [h["text"] for h in result["hits"]]
        except (KeyError, TypeError, json.JSONDecodeError):
            continue
    quotes = [
        q for q in re.findall(r'["“]([^"”]+)["”]', answer) if len(q) > 30 and not q.endswith(".pdf")
    ]
    checks = {
        "observed_successful_search_tool_call": bool(search),
        "expected_sentence_in_tool_evidence": any(expected in text for text in evidence),
        "answer_contains_expected_sentence": expected.lower() in answer.lower(),
        "answer_names_document": "DEMO-LA-2026-001" in answer,
        "answer_names_page_two": bool(re.search(r"(?:page|p\.)\s*:?\s*2", answer, re.I)),
        "any_long_prose_quotes_match_evidence": all(
            any(q.lower() in text.lower() for text in evidence) for q in quotes
        ),
    }
    return {
        "passed": all(checks.values()),
        "checks": checks,
        "tool_names": [c.get("tool") for c in calls],
        "limitation": "A narrow golden quotation check, not general factuality verification.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--local", action="store_true")
    parser.add_argument("--case", choices=["prepayment", "jurisdiction"], default="prepayment")
    args = parser.parse_args()
    STATE.mkdir(exist_ok=True)
    prompt = PROMPT if args.case == "prepayment" else JURISDICTION_PROMPT
    expected = EXPECTED if args.case == "prepayment" else JURISDICTION_EXPECTED
    harness = ["opencode", "run", "--format", "json", "--agent", "workshop", prompt]
    command = (
        [str(ROOT / ".local/opencode/node_modules/.bin/opencode")] + harness[1:]
        if args.local
        else ["sbx", "exec", "-w", str(ROOT), SBX] + harness
    )
    started = time.monotonic()
    result = subprocess.run(
        command,
        cwd=ROOT,
        env=local_env() if args.local else None,
        text=True,
        capture_output=True,
        timeout=150,
    )
    (STATE / f"rehearsal-{args.case}.jsonl").write_text(result.stdout)
    (STATE / f"rehearsal-{args.case}.stderr").write_text(result.stderr)
    events = [json.loads(line) for line in result.stdout.splitlines() if line.startswith("{")]
    for event in events:
        if event.get("type") == "tool_use":
            part = event["part"]
            print("ACTUAL TOOL CALL:", part.get("tool"), json.dumps(part["state"].get("input")))
            print("TOOL RESULT:", part["state"].get("output", part["state"].get("error")))
        elif event.get("type") == "text":
            print("MODEL RESPONSE:", event["part"]["text"])
    report = assess(events, expected)
    report.update(
        seconds=round(time.monotonic() - started, 2),
        exit_code=result.returncode,
        mode="local" if args.local else "sbx",
        model="Llama 3.2 3B / 16K context",
        case=args.case,
    )
    report["passed"] = report["passed"] and result.returncode == 0
    (STATE / f"rehearsal-{args.case}-report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
