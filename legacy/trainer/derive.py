"""Explicit dual-output compatibility: derive a Trainer from Modeler construction."""

from __future__ import annotations

from pathlib import Path

from modeler.build_bav import build_bav_workbook
from modeler.semantic_io import company_stem_from_output, resolve_pair_paths
from .workbook import TrainingWorkbookGenerator, remove_trainer_sidecars


def derive_trainer_workbook(bav_path: Path, trainer_path: Path | None = None) -> Path:
    """Derive a Trainer from a completed BAV without mutating the BAV."""
    bav_path = Path(bav_path)
    if trainer_path is None:
        trainer_path, _ = resolve_pair_paths(bav_path)
    generator = TrainingWorkbookGenerator(bav_path)
    return generator.derive_trainer(trainer_path)


def build_training_workbook(
    financials,
    output_path: Path,
    assumptions: dict | None = None,
    *,
    current_snapshot: bool = False,
) -> tuple[Path, Path]:
    """Existing interface: professional BAV plus optional Trainer derivation.

    Returns ``(trainer_path, bav_path)``. Consumes Modeler construction.
    """
    bav_path = build_bav_workbook(
        financials,
        output_path,
        assumptions,
        current_snapshot=current_snapshot,
    )
    trainer_path, resolved_bav = resolve_pair_paths(output_path)
    output_path = Path(output_path)
    company = company_stem_from_output(output_path.stem)
    suffix = output_path.suffix or ".xlsx"
    protected = {bav_path.resolve(), resolved_bav.resolve()}
    for stale in (
        trainer_path,
        output_path,
        output_path.with_name(f"{company}_Trainer{suffix}"),
        output_path.with_name(f"{company}_BAV_Trainer{suffix}"),
    ):
        if stale.resolve() in protected:
            continue
        remove_trainer_sidecars(stale)
    derive_trainer_workbook(bav_path, trainer_path)
    return trainer_path, bav_path
