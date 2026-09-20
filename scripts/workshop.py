#!/usr/bin/env python3
"""Standard-library host conductor. Actual data handling lives in privacy_lab."""

import argparse
import json
import os
import shlex
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / ".local"
SBX = "privacy-search-lab"
OLLAMA = "http://127.0.0.1:11435"
MODEL = "privacy-lab-local"
EMBED = "nomic-embed-text:v1.5"
OPENCODE_VERSION = "1.18.31"
SOURCE = ROOT / "data/source"
FOLDER = "https://drive.google.com/drive/folders/1hSegm8i5YgFJfEuHNIDEigXVIDf_5kjv"
PREP_HOSTS = [
    "registry-1.docker.io",
    "auth.docker.io",
    "production.cloudfront.docker.com",
    "production.cloudflare.docker.com",
    "*.r2.cloudflarestorage.com",
    "ghcr.io",
    "pkg-containers.githubusercontent.com",
    "pypi.org",
    "files.pythonhosted.org",
    "registry.npmjs.org",
]


def run(args, *, capture=False, check=True, env=None, timeout=None):
    args = [str(a) for a in args]
    print("$ " + shlex.join(args), flush=True)
    return subprocess.run(
        args, cwd=ROOT, env=env, text=True, capture_output=capture, check=check, timeout=timeout
    )


def get_json(url):
    with urllib.request.urlopen(url, timeout=5) as response:
        return json.load(response)


def require(binary):
    if not shutil.which(binary):
        raise RuntimeError(f"Missing {binary}. See docs/quickstart.md.")


def sbx_state():
    """Return the authenticated local sandbox list, or fail with useful context."""
    result = run(["sbx", "ls", "--json"], capture=True, check=False)
    if result.returncode:
        detail = (result.stderr or result.stdout or "unknown sbx error").strip()
        return None, detail
    try:
        payload = json.loads(result.stdout)
        sandboxes = payload["sandboxes"]
        if not isinstance(sandboxes, list):
            raise TypeError
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        raise RuntimeError("sbx returned an unexpected sandbox-list response") from exc
    return sandboxes, ""


def ensure_sbx_login(interactive=True):
    """Verify Docker authentication and optionally complete the device flow."""
    require("sbx")
    run(["sbx", "version"])
    sandboxes, detail = sbx_state()
    if sandboxes is not None:
        print("Docker sbx authentication is ready.")
        return sandboxes
    if "not authenticated" not in detail.lower():
        raise RuntimeError(f"Docker sbx preflight failed: {detail}")
    if not interactive:
        raise RuntimeError("Docker sbx is not authenticated. Run ./workshop login in a terminal.")
    print("Docker sbx needs authentication; starting its browser device flow.")
    run(["sbx", "login"])
    sandboxes, detail = sbx_state()
    if sandboxes is None:
        raise RuntimeError(f"Docker sbx login did not complete: {detail}")
    print("Docker sbx login verified.")
    return sandboxes


def sandbox_exists(sandboxes):
    return any(item.get("name") == SBX for item in sandboxes if isinstance(item, dict))


def ensure_sbx_policy():
    """Initialize Locked Down once without resetting an existing user policy."""
    result = run(["sbx", "policy", "ls", "--json"], capture=True, check=False)
    if result.returncode == 0:
        print("Existing Docker sbx policy retained; preparation rules are sandbox-scoped.")
        return
    detail = (result.stderr or result.stdout or "unknown policy error").strip()
    if "has not been initialized" not in detail.lower():
        raise RuntimeError(f"Unable to inspect Docker sbx policy: {detail}")
    run(["sbx", "policy", "init", "deny-all"])
    print("Initialized Docker sbx with the Locked Down (deny-all) policy.")


def local_env():
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src")
    env.update(
        OLLAMA_URL=OLLAMA,
        OLLAMA_HOST="127.0.0.1:11435",
        OLLAMA_NO_CLOUD="1",
        LAB_BACKEND="sqlite",
        LAB_INDEX_DIR=str(ROOT / "data/index"),
        LAB_OLLAMA_OPENAI_URL=OLLAMA + "/v1",
        OPENCODE_DISABLE_AUTOUPDATE="true",
        OPENCODE_DISABLE_MODELS_FETCH="true",
        OPENCODE_DISABLE_DEFAULT_PLUGINS="true",
        OPENCODE_DISABLE_LSP_DOWNLOAD="true",
        OPENCODE_DISABLE_CLAUDE_CODE="true",
    )
    # Keep workshop harness configuration and conversations separate from user settings.
    for key, directory in [
        ("XDG_CONFIG_HOME", "config"),
        ("XDG_DATA_HOME", "share"),
        ("XDG_CACHE_HOME", "cache"),
        ("XDG_STATE_HOME", "state"),
    ]:
        env[key] = str(STATE / "opencode-home" / directory)
    return env


def models_start():
    require("ollama")
    STATE.mkdir(exist_ok=True)
    try:
        status = get_json(OLLAMA + "/api/status")
    except (OSError, urllib.error.URLError):
        with (STATE / "ollama.log").open("a") as log:
            process = subprocess.Popen(
                ["ollama", "serve"],
                cwd=ROOT,
                env=local_env(),
                stdin=subprocess.DEVNULL,
                stdout=log,
                stderr=log,
                start_new_session=True,
            )
        (STATE / "ollama.pid").write_text(str(process.pid))
        for _ in range(40):
            if process.poll() is not None:
                raise RuntimeError("Workshop Ollama exited; inspect .local/ollama.log") from None
            try:
                status = get_json(OLLAMA + "/api/status")
                break
            except OSError:
                time.sleep(0.25)
        else:
            raise RuntimeError("Workshop Ollama did not start")
    if status.get("cloud", {}).get("disabled") is not True:
        raise RuntimeError(
            "Port 11435 is occupied by Ollama with cloud enabled; refusing to use it"
        )
    print("Workshop Ollama is local-only on 127.0.0.1:11435.")


def models_prepare():
    models_start()
    names = {m["name"] for m in get_json(OLLAMA + "/api/tags")["models"]}
    for name in [EMBED, "llama3.2:latest"]:
        if name not in names:
            run(["ollama", "pull", name], env=local_env())
    run(["ollama", "create", MODEL, "-f", "models/Modelfile"], env=local_env())


def fetch():
    require("uv")
    paths = list(SOURCE.rglob("*.pdf"))
    if len(paths) == 40:
        print("40 PDFs already present; skipping network download.")
        return
    if paths:
        raise RuntimeError(
            "Partial/custom corpus present. Complete it manually or use a separate source folder."
        )
    run(["uvx", "--from", "gdown==5.2.0", "gdown", "--folder", FOLDER, "-O", str(SOURCE) + "/"])


def sandbox_exec(args, *, capture=False, check=True, tty=False):
    command = ["sbx", "exec"]
    if tty:
        command += ["-it"]
    return run(command + ["-w", str(ROOT), SBX] + list(args), capture=capture, check=check)


def lab(args, local=False, *, capture=False):
    if local:
        return run(
            ["uv", "run", "--frozen", "privacy-lab"] + list(args), env=local_env(), capture=capture
        )
    return sandbox_exec(
        ["docker", "compose", "exec", "-T", "mcp", "privacy-lab"] + list(args), capture=capture
    )


def start_local_mcp():
    try:
        get_json("http://127.0.0.1:8765/health")
        print("MCP endpoint is already running; doctor will validate its corpus.")
        return
    except OSError:
        pass
    with (STATE / "mcp.log").open("a") as log:
        process = subprocess.Popen(
            [str(ROOT / ".venv/bin/privacy-lab"), "serve"],
            cwd=ROOT,
            env=local_env(),
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=log,
            start_new_session=True,
        )
    (STATE / "mcp.pid").write_text(str(process.pid))
    for _ in range(40):
        if process.poll() is not None:
            raise RuntimeError("MCP process exited; inspect .local/mcp.log")
        try:
            get_json("http://127.0.0.1:8765/health")
            return
        except OSError:
            time.sleep(0.25)
    raise RuntimeError("MCP server did not start")


def opencode(local=False, prompt=None):
    args = ["run", "--agent", "workshop", prompt] if prompt else []
    if local:
        binary = ROOT / ".local/opencode/node_modules/.bin/opencode"
        if not binary.exists():
            raise RuntimeError("Run ./workshop prepare --local to install the pinned harness")
        return run([binary] + args, env=local_env())
    return sandbox_exec(["opencode"] + args, tty=not bool(prompt))


def prepare(local=False):
    models_prepare()
    fetch()
    if local:
        require("uv")
        run(["uv", "sync", "--frozen", "--group", "dev"])
        lab(["ingest", str(SOURCE)], True)
        require("npm")
        run(
            [
                "npm",
                "install",
                "--prefix",
                ".local/opencode",
                f"opencode-ai@{OPENCODE_VERSION}",
                "--no-audit",
                "--no-fund",
            ]
        )
        start_local_mcp()
        print("LOCAL DEVELOPMENT MODE: no sbx network isolation is claimed.")
        return
    sandboxes = ensure_sbx_login()
    # One-time initialization never resets existing policy or stops other sandboxes.
    ensure_sbx_policy()
    if not sandbox_exists(sandboxes):
        run(["sbx", "kit", "validate", "./sandbox"])
        run(
            [
                "sbx",
                "create",
                "--name",
                SBX,
                "--memory",
                "3g",
                "--cpus",
                "4",
                "--skills",
                "off",
                "./sandbox",
                str(ROOT),
            ]
        )
    else:
        print(f"Reusing existing sandbox {SBX}; sbx is the source of truth.")
    docker_socket = sandbox_exec(["test", "-S", "/var/run/docker.sock"], check=False)
    if docker_socket.returncode:
        raise RuntimeError(
            "The existing sandbox has no private Docker socket. Remove only "
            f"{SBX} with 'sbx rm {SBX}', then rerun ./workshop prepare."
        )
    enabled = []
    try:
        for host in PREP_HOSTS:
            run(["sbx", "policy", "allow", "network", "--sandbox", SBX, host])
            enabled.append(host)
        sandbox_exec(["docker", "compose", "build"])
        sandbox_exec(["docker", "compose", "pull", "qdrant"])
        sandbox_exec(["docker", "compose", "up", "-d", "--wait"])
        sandbox_exec(["docker", "compose", "run", "--rm", "ingest"])
        current_opencode = sandbox_exec(["opencode", "--version"], capture=True)
        if current_opencode.stdout.strip() != OPENCODE_VERSION:
            sandbox_exec(
                [
                    "npm",
                    "install",
                    "--global",
                    f"opencode-ai@{OPENCODE_VERSION}",
                    "--no-audit",
                    "--no-fund",
                ]
            )
        # Resolve provider packages before closing preparation egress.
        sandbox_exec(["opencode", "models", "ollama"])
    finally:
        for host in enabled:
            run(
                ["sbx", "policy", "rm", "network", "--sandbox", SBX, "--resource", host],
                check=False,
            )
    doctor(False)


def doctor(local=False):
    status = get_json(OLLAMA + "/api/status")
    if status.get("cloud", {}).get("disabled") is not True:
        raise RuntimeError("Workshop Ollama cloud-disable check failed")
    if not local:
        # A sandbox VM or its private Docker daemon can restart between rehearsal
        # sessions. Restore the cached services before checking their state.
        sandbox_exec(["docker", "compose", "up", "-d", "--wait"])
    result = lab(["status"], local, capture=True)
    data = json.loads(result.stdout)
    print(json.dumps(data, indent=2))
    if data["states"].get("ready") != 40 or any(
        data["states"].get(k, 0) for k in ["failed", "indexing"]
    ):
        raise RuntimeError("Expected 40 ready documents and no failed/incomplete documents")
    lab(["mcp-smoke"], local)
    if local:
        lab(["verify-sources", str(SOURCE)], True)
        print("PASS: local functional checks. Sandbox isolation has NOT been tested in this mode.")
    else:
        sandbox_exec(["docker", "compose", "run", "--rm", "ingest", "verify-sources", "/corpus"])
        run(["sbx", "policy", "ls", SBX, "--wide"])
        print("Functional checks passed. Run ./workshop privacy-check before presentation.")


def privacy_check(local=False):
    if local:
        raise RuntimeError(
            "Privacy boundary checks require sbx; --local is only a development mode"
        )
    if get_json(OLLAMA + "/api/status").get("cloud", {}).get("disabled") is not True:
        raise RuntimeError("Host Ollama has cloud support enabled")
    from privacy_audit import audit_allow_rules

    rules = run(
        ["sbx", "policy", "ls", SBX, "--type", "network", "--decision", "allow", "--json"],
        capture=True,
    )
    print(json.dumps(audit_allow_rules(json.loads(rules.stdout)), indent=2))
    run(["sbx", "policy", "ls", SBX, "--wide"])
    for target, expected in [
        ("localhost:11435", "Allowed:"),
        ("example.com:443", "Denied:"),
        ("example.com:80", "Denied:"),
        ("api.openai.com:443", "Denied:"),
        ("registry.npmjs.org:443", "Denied:"),
    ]:
        result = run(
            ["sbx", "policy", "check", "network", "--sandbox", SBX, target],
            capture=True,
            check=False,
        )
        print(result.stdout, end="")
        if expected.lower() not in result.stdout.lower():
            raise RuntimeError(f"Policy did not report {expected} for {target}")
    sandbox_exec(
        ["curl", "--fail", "--max-time", "10", "http://host.docker.internal:11435/api/status"]
    )
    # Plain HTTP makes the policy denial visible without depending on whether the
    # application container trusts the sandbox proxy's generated TLS certificate.
    probe = "import urllib.request; urllib.request.urlopen('http://example.com', timeout=10)"
    # A failed request is necessary, but policy evidence above and logs below are also required.
    agent = sandbox_exec(["curl", "--fail", "--max-time", "10", "https://example.com"], check=False)
    container = sandbox_exec(
        ["docker", "compose", "exec", "-T", "mcp", "python", "-c", probe], check=False
    )
    if agent.returncode == 0 or container.returncode == 0:
        raise RuntimeError("External request succeeded; presentation isolation gate FAILED")
    lab(["search", "early repayment fees", "--document-id", "DEMO-LA-2026-001", "--limit", "1"])
    run(["sbx", "policy", "log", SBX, "--limit", "20"])
    print(
        "Probe checks passed. Inspect the full policy list and corresponding deny log entries; "
        "these sampled destinations are not proof that every other destination is blocked."
    )


def demo(local=False, start=1, auto=False):
    mode = "local development (no sandbox isolation)" if local else "Docker sbx"
    print(f"Privacy First Search Lab — {mode}")
    steps = [
        ("Preflight: every layer must be ready", lambda: doctor(local)),
        ("Inspect the corpus and its provenance", lambda: lab(["status"], local)),
        (
            "Re-ingest unchanged sources: demonstrate idempotence",
            lambda: (
                lab(["ingest", str(SOURCE)], True)
                if local
                else sandbox_exec(["docker", "compose", "run", "--rm", "ingest"])
            ),
        ),
        (
            "Semantic retrieval: inspect cited evidence before an answer",
            lambda: lab(
                [
                    "search",
                    "fees and voluntary prepayment",
                    "--document-id",
                    "DEMO-LA-2026-001",
                    "--limit",
                    "3",
                ],
                local,
            ),
        ),
        (
            "Exact filtering: quarterly loans above $10 million",
            lambda: lab(
                ["list", "--frequency", "quarterly", "--min-principal-cents", "1000000001"], local
            ),
        ),
        (
            "Read validated repayment rows",
            lambda: lab(["schedule", "DEMO-LA-2026-001", "--limit", "3"], local),
        ),
        ("Discover the real MCP tools", lambda: lab(["mcp-smoke"], local)),
        (
            "Watch OpenCode call the search tool and cite its answer",
            lambda: run([sys.executable, "scripts/rehearse.py"] + (["--local"] if local else [])),
        ),
        (
            "An unsupported question should not produce an invented fact",
            lambda: run(
                [sys.executable, "scripts/rehearse.py", "--case", "jurisdiction"]
                + (["--local"] if local else [])
            ),
        ),
        (
            "Prove the network boundary",
            lambda: (
                print("Local mode ends here. Run the sbx path to demonstrate network containment.")
                if local
                else privacy_check(False)
            ),
        ),
    ]
    if not 1 <= start <= len(steps):
        raise RuntimeError("--from-step must be between 1 and 10")
    for index, (title, action) in enumerate(steps, 1):
        if index < start:
            continue
        print(f"\n{'=' * 68}\nSTEP {index}/{len(steps)} — {title}\n{'=' * 68}")
        if not auto:
            answer = input("Enter: run | s: skip | q: quit > ").strip().lower()
            if answer == "q":
                return
            if answer == "s":
                continue
        try:
            action()
        except (RuntimeError, subprocess.CalledProcessError, OSError) as exc:
            print(
                f"Step failed: {exc}\nResume: ./workshop demo {'--local ' if local else ''}--from-step {index}"
            )
            raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command",
        choices=[
            "login",
            "models-start",
            "models-prepare",
            "fetch",
            "prepare",
            "doctor",
            "demo",
            "opencode",
            "privacy-check",
            "stop",
            "reset",
        ],
    )
    parser.add_argument(
        "--local", action="store_true", help="Development mode without sbx isolation"
    )
    parser.add_argument("--from-step", type=int, default=1)
    parser.add_argument("--auto", action="store_true", help="Run demo without Enter pauses")
    parser.add_argument(
        "--yes", action="store_true", help="Confirm deletion of this demo's generated index"
    )
    args = parser.parse_args()
    STATE.mkdir(exist_ok=True)
    try:
        if args.command == "login":
            if args.local:
                raise RuntimeError("The login command is only for the Docker sbx path")
            ensure_sbx_login()
            run(["sbx", "diagnose"])
        elif args.command == "models-start":
            models_start()
        elif args.command == "models-prepare":
            models_prepare()
        elif args.command == "fetch":
            fetch()
        elif args.command == "prepare":
            prepare(args.local)
        elif args.command == "doctor":
            doctor(args.local)
        elif args.command == "demo":
            demo(args.local, args.from_step, args.auto)
        elif args.command == "opencode":
            opencode(args.local)
        elif args.command == "privacy-check":
            privacy_check(args.local)
        elif args.command == "stop":
            if args.local:
                raise RuntimeError(
                    "Local processes are identified in .local/*.pid; inspect them before stopping."
                )
            run(["sbx", "stop", SBX])
        elif args.command == "reset":
            if not args.yes:
                raise RuntimeError(
                    "Reset deletes only demo indexes. Re-run with --yes after reviewing docs/operations.md."
                )
            if args.local:
                raise RuntimeError(
                    "Stop the local MCP server first, then remove data/index manually."
                )
            sandbox_exec(["docker", "compose", "down", "--volumes"])
            print(
                "Demo service volumes removed; PDFs and host models retained. Run prepare to rebuild."
            )
    except (RuntimeError, subprocess.CalledProcessError, OSError, ValueError) as exc:
        print(f"Workshop stopped: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
