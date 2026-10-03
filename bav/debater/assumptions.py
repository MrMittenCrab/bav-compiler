"""Stance-conditioned assumption copies. Cannot overwrite the canonical neutral set."""

from __future__ import annotations

from copy import deepcopy
from types import MappingProxyType
from typing import Any, Mapping

from bav.inferer.assumptions import (
    ORIGIN_INFERER,
    STANCE_NEUTRAL,
    AssumptionSet,
    is_canonical_neutral,
)

ORIGIN_DEBATER = "debater"


class NeutralAssumptionOverwriteError(ValueError):
    """Raised when a Debater path tries to mutate canonical neutral assumptions."""


def stance_conditioned_assumptions(
    base: AssumptionSet,
    *,
    stance: str,
    payload: Mapping[str, Any] | None = None,
) -> AssumptionSet:
    """Return a new stance-conditioned set. The canonical object is never mutated."""
    if not stance or stance == STANCE_NEUTRAL:
        raise NeutralAssumptionOverwriteError(
            "Debater assumption sets must declare a non-neutral stance"
        )
    if is_canonical_neutral(base):
        data = deepcopy(dict(payload) if payload is not None else dict(base.payload))
        return AssumptionSet(
            origin=ORIGIN_DEBATER,
            stance=stance,
            payload=MappingProxyType(data),
        )
    data = deepcopy(dict(payload) if payload is not None else dict(base.payload))
    return AssumptionSet(
        origin=ORIGIN_DEBATER,
        stance=stance,
        payload=MappingProxyType(data),
    )


def forbid_neutral_overwrite(target: AssumptionSet) -> None:
    if target.origin == ORIGIN_INFERER and target.stance == STANCE_NEUTRAL:
        raise NeutralAssumptionOverwriteError(
            "Debater cannot overwrite canonical inferer/neutral assumptions"
        )
