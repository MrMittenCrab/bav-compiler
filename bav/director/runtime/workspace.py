"""Dedicated isolated workspace outside the checkout instruction ancestry."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Mapping

from bav.director.repository import repository_root
from bav.director.runtime.contract import ApprovedSnapshot
from bav.director.runtime.policy import intended_research_policy, snapshot_dict


REPO_INSTRUCTION_NAMES = frozenset(
    {
        "TARGET.md",
        "SESSION.md",
        "IMPLEMENTATION.md",
        "AGENTS.md",
        "RESULT.md",
    }
)


class IsolatedWorkspace:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.workspace = root / "workspace"
        self.config_dir = root / "cursor-config"
        self.data_dir = root / "cursor-data"
        self.home = root / "home"
        self.sources = self.workspace / "sources"

    def paths(self) -> dict[str, str]:
        return {
            "root": str(self.root),
            "workspace": str(self.workspace),
            "config_dir": str(self.config_dir),
            "data_dir": str(self.data_dir),
            "home": str(self.home),
        }


def create_isolated_workspace(
    snapshot: ApprovedSnapshot,
    *,
    checkout: Path | None = None,
) -> IsolatedWorkspace:
    checkout = (checkout or repository_root()).resolve()
    root = Path(tempfile.mkdtemp(prefix="bav-research-runtime-"))
    isolated = IsolatedWorkspace(root)
    if _is_within_checkout(isolated.root, checkout):
        _cleanup(isolated.root)
        raise RuntimeError("isolated workspace resolved inside the checkout")
    isolated.workspace.mkdir()
    isolated.config_dir.mkdir()
    isolated.data_dir.mkdir()
    isolated.home.mkdir()
    isolated.sources.mkdir()
    (isolated.workspace / "snapshot.json").write_text(
        json.dumps(snapshot_dict(snapshot), indent=2) + "\n",
        encoding="utf-8",
    )
    policy = intended_research_policy()
    (isolated.config_dir / "cli-config.json").write_text(
        json.dumps(policy, indent=2) + "\n",
        encoding="utf-8",
    )
    for source in snapshot.sources:
        name = Path(source.relative_name).name
        if name in REPO_INSTRUCTION_NAMES:
            continue
        (isolated.sources / name).write_text(source.text, encoding="utf-8")
    return isolated


def isolated_environment(
    isolated: IsolatedWorkspace,
    extra: Mapping[str, str] | None = None,
) -> dict[str, str]:
    path_entries = []
    for item in (os.environ.get("PATH") or "").split(os.pathsep):
        if item:
            path_entries.append(item)
    env = {
        "PATH": os.pathsep.join(path_entries) or "/usr/bin:/bin",
        "HOME": str(isolated.home),
        "CURSOR_CONFIG_DIR": str(isolated.config_dir),
        "CURSOR_DATA_DIR": str(isolated.data_dir),
        "LANG": "C",
        "LC_ALL": "C",
    }
    if extra:
        env.update(extra)
    return env


def workspace_file_names(isolated: IsolatedWorkspace) -> list[str]:
    names = []
    for path in isolated.workspace.rglob("*"):
        if path.is_file():
            names.append(str(path.relative_to(isolated.workspace)))
    return sorted(names)


def assert_no_repo_instructions(isolated: IsolatedWorkspace, checkout: Path) -> None:
    for name in REPO_INSTRUCTION_NAMES:
        if (isolated.workspace / name).exists() or (isolated.root / name).exists():
            raise RuntimeError(f"repository instruction leaked into workspace: {name}")
    project_cli = isolated.workspace / ".cursor" / "cli.json"
    if project_cli.exists():
        raise RuntimeError("coding-agent project policy leaked into workspace")
    if (isolated.root / ".cursor").exists():
        raise RuntimeError("coding-agent configuration directory leaked into workspace")
    if _is_within_checkout(isolated.root, checkout):
        raise RuntimeError("workspace is inside the checkout")


def _is_within_checkout(path: Path, checkout: Path) -> bool:
    try:
        path.resolve().relative_to(checkout.resolve())
        return True
    except ValueError:
        return False


def _cleanup(root: Path) -> None:
    for path in sorted(root.rglob("*"), reverse=True):
        if path.is_file() or path.is_symlink():
            path.unlink(missing_ok=True)
        elif path.is_dir():
            path.rmdir()
    root.rmdir()


def cleanup_workspace(isolated: IsolatedWorkspace) -> None:
    if isolated.root.exists():
        _cleanup(isolated.root)
