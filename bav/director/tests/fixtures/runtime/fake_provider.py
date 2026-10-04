#!/usr/bin/env python3
"""Local fake provider process for Director runtime tests. Makes no live calls."""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path


def _observe(workspace: Path) -> dict:
    files = sorted(
        str(path.relative_to(workspace))
        for path in workspace.rglob("*")
        if path.is_file()
    )
    snapshot = {}
    snap_path = workspace / "snapshot.json"
    if snap_path.is_file():
        snapshot = json.loads(snap_path.read_text(encoding="utf-8"))
    return {
        "cwd": os.getcwd(),
        "workspace": str(workspace),
        "files": files,
        "role": snapshot.get("role"),
        "proposition": snapshot.get("proposition"),
        "source_ids": [item.get("source_id") for item in snapshot.get("sources") or []],
        "has_target_md": (workspace / "TARGET.md").exists(),
        "has_session_md": (workspace / "SESSION.md").exists(),
        "has_implementation_md": (workspace / "IMPLEMENTATION.md").exists(),
        "has_agents_md": (workspace / "AGENTS.md").exists(),
        "has_project_cli_json": (workspace / ".cursor" / "cli.json").exists(),
        "cursor_config_dir": os.environ.get("CURSOR_CONFIG_DIR"),
        "cursor_data_dir": os.environ.get("CURSOR_DATA_DIR"),
        "home": os.environ.get("HOME"),
        "has_cursor_api_key": "CURSOR_API_KEY" in os.environ,
        "env_names": sorted(os.environ),
        "runtime_version": "fake-provider-1",
        "contains_company_context": snapshot.get("contains_company_context"),
        "candidate_argument": snapshot.get("candidate_argument"),
        "prior_review": snapshot.get("prior_review"),
    }


def _ok(role: str, observed: dict, source_id: str) -> dict:
    return {
        "type": "result",
        "role": role,
        "model": os.environ.get("BAV_RUNTIME_MODEL"),
        "observed": observed,
        "requests": [
            {"operation": "inspect_approved_source", "arguments": {"source_id": source_id}}
        ],
        "output": {
            "kind": f"{role}_proposal",
            "payload": {"source_id": source_id, "note": "synthetic"},
        },
    }


def main() -> int:
    workspace = Path(os.environ.get("BAV_RUNTIME_WORKSPACE") or os.getcwd())
    role = os.environ.get("BAV_RUNTIME_ROLE") or "planner"
    scenario = os.environ.get("BAV_FAKE_SCENARIO") or "ok"
    observed = _observe(workspace)
    source_ids = observed.get("source_ids") or ["src-approved"]
    source_id = source_ids[0]

    if scenario == "timeout":
        time.sleep(30)
        return 0
    if scenario == "interrupt":
        time.sleep(30)
        return 0
    if scenario == "error":
        sys.stdout.write(json.dumps(_ok(role, observed, source_id)))
        sys.stdout.flush()
        return 2
    if scenario == "malformed":
        sys.stdout.write("{not-json")
        return 0
    if scenario == "truncated":
        sys.stdout.write('{"type":"result","role":"planner","output":{"kind":"x"')
        return 0
    if scenario == "missing_result":
        sys.stdout.write(json.dumps({"type": "result", "role": role, "observed": observed}))
        return 0
    if scenario == "empty":
        return 0
    if scenario == "denied_ops":
        payload = {
            "type": "result",
            "role": role,
            "observed": observed,
            "requests": [
                {"operation": "inspect_approved_source", "arguments": {"source_id": source_id}},
                {"operation": "shell", "arguments": {"command": "uname"}},
                {"operation": "write", "arguments": {"path": "probe-write.txt"}},
                {"operation": "mcp", "arguments": {"name": "GetDynamicTools"}},
                {"operation": "fetch", "arguments": {"url": "https://example.com"}},
                {"operation": "search", "arguments": {"query": "lululemon"}},
                {"operation": "unknown_tool", "arguments": {}},
                {
                    "operation": "inspect_approved_source",
                    "arguments": {"source_id": source_id, "path": "/etc/hosts"},
                },
                {
                    "operation": "inspect_approved_source",
                    "arguments": {"source_id": source_id, "path": "../TARGET.md"},
                },
                {
                    "operation": "inspect_approved_source",
                    "arguments": {"source_id": source_id, "path": "sources/escape"},
                },
                {
                    "operation": "apply_source_policy",
                    "arguments": {"source_id": "src-instructions"},
                },
                {
                    "operation": "inspect_approved_source",
                    "arguments": {
                        "source_id": "src-instructions",
                        "treat_as": "instruction",
                    },
                },
                {
                    "operation": "inspect_approved_source",
                    "arguments": {"source_id": "src-unrelated"},
                },
            ],
            "output": {"kind": f"{role}_proposal", "payload": {"note": "denials"}},
        }
        sys.stdout.write(json.dumps(payload))
        return 0

    sys.stdout.write(json.dumps(_ok(role, observed, source_id)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
