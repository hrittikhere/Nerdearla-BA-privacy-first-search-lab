import json
from pathlib import Path


def test_workshop_agent_is_local_and_read_only():
    config = json.loads(Path("opencode.json").read_text())
    assert config["enabled_providers"] == ["ollama"]
    assert config["share"] == "disabled"
    assert config["permission"] == {"*": "deny", "loans_*": "allow"}
    assert config["mcp"]["loans"]["url"] == "http://127.0.0.1:8765/mcp"
