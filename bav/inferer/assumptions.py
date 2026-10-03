"""Canonical neutral/base assumption sets. Origin and stance are explicit."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping

ORIGIN_INFERER = "inferer"
STANCE_NEUTRAL = "neutral"


@dataclass(frozen=True)
class AssumptionSet:
    origin: str
    stance: str
    payload: Mapping[str, Any]

    def __post_init__(self) -> None:
        owned = deepcopy(dict(self.payload))
        object.__setattr__(self, "payload", MappingProxyType(owned))


def canonical_neutral_assumptions(
    payload: Mapping[str, Any] | None = None,
) -> AssumptionSet:
    """Wrap the existing assumption payload without changing sidecar keys."""
    data = dict(
        payload
        or {
            "classificationOverrides": {},
            "normalizationCandidates": [],
        }
    )
    return AssumptionSet(
        origin=ORIGIN_INFERER,
        stance=STANCE_NEUTRAL,
        payload=MappingProxyType(data),
    )


def is_canonical_neutral(assumptions: AssumptionSet) -> bool:
    return assumptions.origin == ORIGIN_INFERER and assumptions.stance == STANCE_NEUTRAL
