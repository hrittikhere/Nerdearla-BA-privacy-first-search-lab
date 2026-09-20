import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path("scripts").resolve()))


def module(name):
    spec = importlib.util.spec_from_file_location(name, Path("scripts") / f"{name}.py")
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def test_policy_audit_rejects_extra_or_unknown_allowances():
    audit = module("privacy_audit").audit_allow_rules
    good = {"policies": [{"rules": [{"decision": "allow", "resources": ["localhost:11435"]}]}]}
    assert audit(good)["external_allowances"] == 0
    with pytest.raises(ValueError, match="External/broad"):
        audit({"rules": [{"decision": "allow", "resources": ["localhost:11435", "**"]}]})
    with pytest.raises(ValueError, match="Unrecognized"):
        audit({"decision": "allow", "resources": {"all": True}})
    with pytest.raises(ValueError, match="No recognizable"):
        audit({"unknown_schema": "local only"})


def test_rehearsal_requires_real_tool_evidence_and_matching_answer():
    rehearsal = module("rehearse")
    expected = rehearsal.EXPECTED
    import json

    call = {
        "type": "tool_use",
        "part": {
            "tool": "loans_search_documents",
            "state": {"status": "completed", "output": json.dumps({"hits": [{"text": expected}]})},
        },
    }
    answer = {"type": "text", "part": {"text": f'"{expected}" (DEMO-LA-2026-001, page 2)'}}
    assert rehearsal.assess([call, answer])["passed"]
    assert not rehearsal.assess([answer])["passed"]
    invented = {
        "type": "text",
        "part": {"text": "Requires 15 days' notice. DEMO-LA-2026-001, page 2"},
    }
    assert not rehearsal.assess([call, invented])["passed"]


def test_sbx_login_runs_device_flow_and_verifies_it(monkeypatch):
    workshop = module("workshop")
    responses = iter(
        [
            subprocess.CompletedProcess([], 0),
            subprocess.CompletedProcess([], 1, "", "Not authenticated to Docker"),
            subprocess.CompletedProcess([], 0),
            subprocess.CompletedProcess([], 0, '{"sandboxes": []}', ""),
        ]
    )
    calls = []

    def fake_run(args, **_kwargs):
        calls.append(args)
        return next(responses)

    monkeypatch.setattr(workshop, "require", lambda _binary: None)
    monkeypatch.setattr(workshop, "run", fake_run)
    assert workshop.ensure_sbx_login() == []
    assert ["sbx", "login"] in calls


def test_sandbox_existence_uses_sbx_state_not_a_marker_file():
    workshop = module("workshop")
    assert workshop.sandbox_exists([{"name": workshop.SBX}])
    assert not workshop.sandbox_exists([])


def test_existing_sbx_policy_is_retained(monkeypatch):
    workshop = module("workshop")
    calls = []

    def fake_run(args, **_kwargs):
        calls.append(args)
        return subprocess.CompletedProcess([], 0, '{"policies": []}', "")

    monkeypatch.setattr(workshop, "run", fake_run)
    workshop.ensure_sbx_policy()
    assert calls == [["sbx", "policy", "ls", "--json"]]
