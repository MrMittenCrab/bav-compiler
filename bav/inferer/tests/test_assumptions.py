"""Canonical neutral assumption origin/stance."""

import pytest
from types import MappingProxyType

from bav.inferer.assumptions import (
    ORIGIN_INFERER,
    STANCE_NEUTRAL,
    AssumptionSet,
    canonical_neutral_assumptions,
    is_canonical_neutral,
)


def _nested_payload():
    return {
        "classificationOverrides": {
            "Lease liability": {"bucket": "operating", "notes": ["base"]},
        },
        "normalizationCandidates": [
            {
                "id": "impairment",
                "tags": ["nonrecurring"],
                "meta": {"source": "caller"},
            }
        ],
    }


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


def test_direct_construction_owns_nested_payload():
    payload = _nested_payload()
    constructed = AssumptionSet(
        origin=ORIGIN_INFERER,
        stance=STANCE_NEUTRAL,
        payload=payload,
    )
    payload["classificationOverrides"]["Lease liability"]["bucket"] = "financing"
    payload["classificationOverrides"]["Lease liability"]["notes"].append("caller")
    payload["classificationOverrides"]["Extra"] = {"bucket": "x"}
    payload["normalizationCandidates"][0]["tags"].append("caller")
    payload["normalizationCandidates"][0]["meta"]["source"] = "mutated"
    payload["normalizationCandidates"].append({"id": "added"})

    assert constructed.origin == ORIGIN_INFERER
    assert constructed.stance == STANCE_NEUTRAL
    assert isinstance(constructed.payload, MappingProxyType)
    assert constructed.payload["classificationOverrides"] == {
        "Lease liability": {"bucket": "operating", "notes": ["base"]},
    }
    assert constructed.payload["normalizationCandidates"] == [
        {"id": "impairment", "tags": ["nonrecurring"], "meta": {"source": "caller"}},
    ]
    assert constructed.payload["classificationOverrides"] is not payload["classificationOverrides"]
    with pytest.raises(TypeError):
        constructed.payload["classificationOverrides"] = {}  # type: ignore[index]


def test_canonical_neutral_owns_nested_caller_payload():
    payload = _nested_payload()
    base = canonical_neutral_assumptions(payload)
    payload["classificationOverrides"]["Lease liability"]["notes"].append("caller")
    payload["normalizationCandidates"][0]["tags"].append("caller")
    payload["normalizationCandidates"][0]["meta"]["source"] = "mutated"

    assert is_canonical_neutral(base)
    assert set(base.payload) == {"classificationOverrides", "normalizationCandidates"}
    assert base.payload["classificationOverrides"]["Lease liability"] == {
        "bucket": "operating",
        "notes": ["base"],
    }
    assert base.payload["normalizationCandidates"][0] == {
        "id": "impairment",
        "tags": ["nonrecurring"],
        "meta": {"source": "caller"},
    }
