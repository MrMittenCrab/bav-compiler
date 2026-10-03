"""Canonical neutral assumption origin/stance."""

from types import MappingProxyType

from bav.inferer.assumptions import (
    ORIGIN_INFERER,
    STANCE_NEUTRAL,
    canonical_neutral_assumptions,
    is_canonical_neutral,
)


def test_canonical_neutral_set_is_explicit_and_immutable():
    base = canonical_neutral_assumptions()
    assert base.origin == ORIGIN_INFERER
    assert base.stance == STANCE_NEUTRAL
    assert is_canonical_neutral(base)
    assert isinstance(base.payload, MappingProxyType)
    assert "classificationOverrides" in base.payload
    assert "normalizationCandidates" in base.payload
    try:
        base.payload["classificationOverrides"] = {"x": 1}  # type: ignore[index]
    except TypeError:
        return
    raise AssertionError("canonical payload must not be writable")
