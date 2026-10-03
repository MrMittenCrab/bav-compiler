"""Margin-relationship judgments: claim typology, recurrence, and causal limits."""

from __future__ import annotations

from dataclasses import dataclass

from bav.modeler.reported_margin import (
    KIND_OBSERVED,
    KIND_REPORTED_FACT,
    KIND_UNESTABLISHED,
    ImpairmentChargeObservations,
    LatestAdjacentMovement,
)

CONTRADICTION_BOTH_REDUCED = "both_reduced"
CONTRADICTION_DIRECTION_DIFFERS = "direction_differs"
CONTRADICTION_NONE = "none_required"


@dataclass(frozen=True)
class DisclosedChargeInterpretation:
    kind: str
    episodic: bool


@dataclass(frozen=True)
class UnsupportedMixInterpretation:
    kind: str
    established: bool


@dataclass(frozen=True)
class LatestMovementInterpretation:
    kind: str
    contradiction_class: str
    established: bool


def interpret_disclosed_charges(
    observations: ImpairmentChargeObservations,
) -> DisclosedChargeInterpretation:
    return DisclosedChargeInterpretation(kind=KIND_REPORTED_FACT, episodic=True)


def interpret_unsupported_mix() -> UnsupportedMixInterpretation:
    return UnsupportedMixInterpretation(kind=KIND_UNESTABLISHED, established=False)


def interpret_latest_movement(
    movement: LatestAdjacentMovement,
) -> LatestMovementInterpretation:
    if movement.both_reduced_om:
        contradiction = CONTRADICTION_BOTH_REDUCED
    elif movement.gm_opposes_om or movement.sga_opposes_om:
        contradiction = CONTRADICTION_DIRECTION_DIFFERS
    else:
        contradiction = CONTRADICTION_NONE
    return LatestMovementInterpretation(
        kind=KIND_OBSERVED,
        contradiction_class=contradiction,
        established=movement.established,
    )


def interpret_margin_relationships() -> UnsupportedMixInterpretation:
    return interpret_unsupported_mix()
