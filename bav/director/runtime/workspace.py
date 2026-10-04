"""Dedicated isolated workspace outside the checkout instruction ancestry."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Mapping

from bav.director.repository import repository_root
from bav.director.runtime.contract import ApprovedSnapshot
from bav.director.runtime.policy import (
    INSTRUCTION_FILENAMES,
    build_launch_environment,
    instruction_named,
    intended_research_policy,
    managed_source_name,
    owned_file_inventory,
    snapshot_dict,
    validate_source_relative_name,
)


REPO_INSTRUCTION_NAMES = INSTRUCTION_FILENAMES


class SourceStagingError(Exception):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class IsolatedWorkspace:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.workspace = root / "workspace"
        self.config_dir = root / "cursor-config"
        self.data_dir = root / "cursor-data"
        self.home = root / "home"
        self.sources = self.workspace / "sources"
        self.inventory: list[dict[str, object]] = []

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
    try:
        isolated.inventory = _stage_sources(isolated, snapshot)
    except SourceStagingError:
        _cleanup(isolated.root)
        raise
    (isolated.workspace / "source_inventory.json").write_text(
        json.dumps({"sources": isolated.inventory}, indent=2) + "\n",
        encoding="utf-8",
    )
    return isolated


def _stage_sources(
    isolated: IsolatedWorkspace,
    snapshot: ApprovedSnapshot,
) -> list[dict[str, object]]:
    seen_ids: set[str] = set()
    seen_originals: set[str] = set()
    seen_managed: set[str] = set()
    inventory: list[dict[str, object]] = []
    for source in snapshot.sources:
        if not source.source_id or source.source_id in seen_ids:
            raise SourceStagingError("source_id_collision")
        escape = validate_source_relative_name(source.relative_name)
        if escape:
            raise SourceStagingError(escape)
        managed = managed_source_name(source.source_id)
        original = Path(source.relative_name).as_posix()
        if original in seen_originals or managed in seen_managed:
            raise SourceStagingError("source_name_collision")
        seen_ids.add(source.source_id)
        seen_originals.add(original)
        seen_managed.add(managed)
        destination = isolated.workspace / managed
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(source.text, encoding="utf-8")
        inventory.append(
            {
                "source_id": source.source_id,
                "managed_name": managed,
                "original_name": original,
                "fingerprint": source.fingerprint,
                "instruction_named": instruction_named(source.relative_name),
            }
        )
    return inventory


def isolated_environment(
    isolated: IsolatedWorkspace,
    extra: Mapping[str, str] | None = None,
    *,
    role: str = "planner",
    model: str = "",
) -> dict[str, str]:
    env, error = build_launch_environment(isolated, role=role, model=model, extra=extra)
    if error:
        raise SourceStagingError(error)
    return env


def workspace_file_names(isolated: IsolatedWorkspace) -> list[str]:
    return owned_file_inventory(isolated.workspace)


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
