"""Verify a real harness tool call and an exact evidence quote using the small model."""

import argparse
import json
import re
import subprocess
import time

from workshop import ROOT, SBX, STATE, local_env

PROMPT = (
    'Use loans_search_documents with query "fees and voluntary prepayment", '
    'document_id "DEMO-LA-2026-001", limit 3. Quote the relevant prepayment sentence '
    "exactly and cite its page. Do not infer any notice period."
)
EXPECTED = "The borrower may prepay on a scheduled due date after paying that date's scheduled installment."


def assess(events):
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
        "expected_sentence_in_tool_evidence": any(EXPECTED in text for text in evidence),
        "answer_contains_expected_sentence": EXPECTED.lower() in answer.lower(),
        "answer_names_document": "DEMO-LA-2026-001" in answer,
        "answer_names_page_two": bool(re.search(r"(?:page|p\.)\s*2", answer, re.I)),
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
    args = parser.parse_args()
    STATE.mkdir(exist_ok=True)
    harness = ["opencode", "run", "--format", "json", "--agent", "workshop", PROMPT]
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
    (STATE / "rehearsal.jsonl").write_text(result.stdout)
    (STATE / "rehearsal.stderr").write_text(result.stderr)
    events = [json.loads(line) for line in result.stdout.splitlines() if line.startswith("{")]
    report = assess(events)
    report.update(
        seconds=round(time.monotonic() - started, 2),
        exit_code=result.returncode,
        mode="local" if args.local else "sbx",
        model="Llama 3.2 3B / 16K context",
    )
    report["passed"] = report["passed"] and result.returncode == 0
    (STATE / "rehearsal-report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
