"""Repository-root discovery for Director orchestration."""

from __future__ import annotations

from pathlib import Path


def repository_root(start: Path | None = None) -> Path:
    """Return the repository root that holds TARGET.md, bav/, build/ and legacy/."""
    here = (start or Path(__file__)).resolve()
    if here.is_file():
        here = here.parent
    for candidate in (here, *here.parents):
        if (candidate / "TARGET.md").is_file() and (candidate / "bav").is_dir():
            return candidate
    raise RuntimeError("cannot locate repository root")
