"""Root README remains the practical operator / Trainer guide."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

FORBIDDEN_README_TERMS = (
    "bavgems",
    "bav pipeline",
    "gemini",
    "gemini gems",
    "legacy/",
    "coverage/",
    "sentinel",
    "edgar pipeline",
    "/bav-pipeline",
    "/bav-update",
    "/bav-news",
    "/bav-brief",
    "claude code plugin",
    "hint",
    "reveal",
)


def test_root_readme_is_practical_trainer_guide():
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    for heading in (
        "# BAV Compiler",
        "## What works now",
        "## Quick start",
        "## How to practice",
        "## Inputs and scope",
        "## Planned",
    ):
        assert heading in text

    lowered = text.lower()
    for term in FORBIDDEN_README_TERMS:
        # Allow "Hint" only if somehow in Answer Key prose — plan forbids Hint/Reveal commands.
        assert term not in lowered, f"forbidden term present: {term!r}"

    assert "python -m bav build" in text
    assert "python -m bav list" in text
    assert "python -m bav check" in text
    assert "Lululemon" in text
    assert "Fast Retailing" in text
    assert "optional derivative" in text.lower() or "optional" in text.lower()
    assert re.search(r"\bhint\b", lowered) is None
    assert re.search(r"\breveal\b", lowered) is None

