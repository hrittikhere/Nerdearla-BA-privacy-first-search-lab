"""Verify a real harness tool call and an exact evidence quote using the small model."""

import argparse
import json
import re
import subprocess
import time

from workshop import ROOT, SBX, STATE, local_env, sandbox_exec, warm_models

PROMPT = (
    'Use loans_search_documents with query "fees and voluntary prepayment", '
    'document_id "DEMO-LA-2026-001", limit 3. After the tool result, return exactly two lines: '
    "line 1 is \"The borrower may prepay on a scheduled due date after paying that date's "
    'scheduled installment." and line 2 is "DEMO-LA-2026-001, page 2". '
    "Do not add another sentence or infer a notice period. Do not echo the tool result."
)
EXPECTED = "The borrower may prepay on a scheduled due date after paying that date's scheduled installment."
JURISDICTION_PROMPT = (
    'Use loans_search_documents with query "governing law dispute forum jurisdiction", '
    'document_id "DEMO-LA-2026-001", limit 3. After the tool result, return exactly two lines: '
    'line 1 is "Governing law and dispute forum are intentionally not designated." and '
    'line 2 is "DEMO-LA-2026-001, page 2". Do not add another sentence or jurisdiction. '
    "Do not echo the tool result."
)
JURISDICTION_EXPECTED = "Governing law and dispute forum are intentionally not designated."
# The small model intermittently answers from the prompt without calling the tool.
ATTEMPTS = 3


def decode(stream):
    """subprocess reports partial output as bytes on timeout, even under text=True."""
    if stream is None:
        return ""
    return stream.decode(errors="replace") if isinstance(stream, bytes) else stream


def launch(command, args, cap):
    """Run the harness once. Exceeding the cap is a failed check, not a crash."""
    try:
        done = subprocess.run(
            command,
            cwd=ROOT,
            env=local_env() if args.local else None,
            # sbx forwards stdin as a pipe even when the presenter uses a terminal.
            # OpenCode reads that pipe to EOF before it submits the argv prompt.
            # Give this noninteractive run EOF immediately instead of waiting for
            # the harness timeout to close sbx and finally release the prompt.
            stdin=subprocess.DEVNULL,
            text=True,
            capture_output=True,
            timeout=cap,
        )
        return done.stdout, done.stderr, done.returncode, False
    except subprocess.TimeoutExpired as exc:
        # Keep the partial transcript: it shows how far the harness got.
        print(f"Harness exceeded its {cap}s cap. Reporting the partial transcript.")
        return decode(exc.stdout), decode(exc.stderr), None, True


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
    warm_models()
    if not args.local:
        # An idle sandbox stops and loses its Compose services. The agent's MCP call
        # would then hang until the timeout, so restore them before timing anything.
        sandbox_exec(["docker", "compose", "up", "-d", "--wait"])
        # Container health is not the same as a reachable endpoint. A harness that
        # starts too early sees no tools and answers from the prompt alone.
        for _ in range(30):
            probe = sandbox_exec(
                ["curl", "--fail", "--silent", "--max-time", "5", "http://127.0.0.1:8765/health"],
                capture=True,
                check=False,
            )
            if probe.returncode == 0:
                break
            time.sleep(2)
        else:
            raise RuntimeError("MCP endpoint did not answer inside the sandbox")
    cap = 150 if args.local else 300
    started = time.monotonic()
    # Retry only the skipped-tool-call flake, so a rehearsal reports the harness
    # rather than the dice. A timeout is never retried: it would multiply the cap.
    for attempt in range(1, ATTEMPTS + 1):
        stdout, stderr, exit_code, timed_out = launch(command, args, cap)
        events = [json.loads(line) for line in stdout.splitlines() if line.startswith("{")]
        report = assess(events, expected)
        report["passed"] = report["passed"] and exit_code == 0
        if report["passed"] or timed_out or attempt == ATTEMPTS:
            break
        print(f"Attempt {attempt}/{ATTEMPTS} produced no verified answer; retrying.")
    (STATE / f"rehearsal-{args.case}.jsonl").write_text(stdout)
    (STATE / f"rehearsal-{args.case}.stderr").write_text(stderr)
    for event in events:
        if event.get("type") == "tool_use":
            part = event["part"]
            print("ACTUAL TOOL CALL:", part.get("tool"), json.dumps(part["state"].get("input")))
            print("TOOL RESULT:", part["state"].get("output", part["state"].get("error")))
        elif event.get("type") == "text":
            print("MODEL RESPONSE:", event["part"]["text"])
    report.update(
        seconds=round(time.monotonic() - started, 2),
        exit_code=exit_code,
        timed_out=timed_out,
        attempts=attempt,
        mode="local" if args.local else "sbx",
        model="Gemma 4 E2B IT / 16K context",
        case=args.case,
    )
    (STATE / f"rehearsal-{args.case}-report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
