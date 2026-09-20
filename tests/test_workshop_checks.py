import importlib.util
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
