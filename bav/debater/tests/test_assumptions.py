"""Debater cannot overwrite canonical neutral/base assumptions."""

import pytest

from bav.debater.assumptions import (
    ORIGIN_DEBATER,
    NeutralAssumptionOverwriteError,
    forbid_neutral_overwrite,
    stance_conditioned_assumptions,
)
from bav.inferer.assumptions import (
    STANCE_NEUTRAL,
    canonical_neutral_assumptions,
    is_canonical_neutral,
)


def _nested_payload(*, source: str):
    return {
        "classificationOverrides": {
            "Lease liability": {"bucket": "operating", "notes": [source]},
        },
        "normalizationCandidates": [
            {
                "id": "impairment",
                "tags": ["nonrecurring"],
                "meta": {"source": source},
            }
        ],
    }


def _nested_snapshot(*, source: str):
    return {
        "classificationOverrides": {
            "Lease liability": {"bucket": "operating", "notes": [source]},
        },
        "normalizationCandidates": [
            {
                "id": "impairment",
                "tags": ["nonrecurring"],
                "meta": {"source": source},
            }
        ],
    }


def test_stance_copy_does_not_mutate_canonical():
    base = canonical_neutral_assumptions(
        {"classificationOverrides": {}, "normalizationCandidates": []}
    )
    copy = stance_conditioned_assumptions(base, stance="bull")
    assert copy.origin == ORIGIN_DEBATER
    assert copy.stance == "bull"
    assert is_canonical_neutral(base)
    assert copy.payload == base.payload
    assert copy is not base


def test_debater_cannot_declare_neutral_or_overwrite_canonical():
    base = canonical_neutral_assumptions()
    with pytest.raises(NeutralAssumptionOverwriteError):
        stance_conditioned_assumptions(base, stance=STANCE_NEUTRAL)
    with pytest.raises(NeutralAssumptionOverwriteError):
        forbid_neutral_overwrite(base)


def test_default_payload_route_isolates_nested_mutations():
    caller = _nested_payload(source="caller")
    base = canonical_neutral_assumptions(caller)
    bull = stance_conditioned_assumptions(base, stance="bull")
    bear = stance_conditioned_assumptions(base, stance="bear")

    bull.payload["classificationOverrides"]["Lease liability"]["bucket"] = "financing"
    bull.payload["classificationOverrides"]["Lease liability"]["notes"].append("bull")
    bull.payload["classificationOverrides"]["Extra"] = {"bucket": "bull"}
    bull.payload["normalizationCandidates"][0]["tags"].append("bull")
    bull.payload["normalizationCandidates"][0]["meta"]["source"] = "bull"
    bull.payload["normalizationCandidates"].append({"id": "bull-only"})

    assert dict(base.payload) == _nested_snapshot(source="caller")
    assert dict(bear.payload) == _nested_snapshot(source="caller")
    assert is_canonical_neutral(base)
    assert bull.origin == ORIGIN_DEBATER and bull.stance == "bull"
    assert bear.origin == ORIGIN_DEBATER and bear.stance == "bear"
    assert bull.payload["classificationOverrides"] is not base.payload["classificationOverrides"]
    assert bull.payload["normalizationCandidates"] is not base.payload["normalizationCandidates"]
    assert (
        bull.payload["normalizationCandidates"][0]["tags"]
        is not base.payload["normalizationCandidates"][0]["tags"]
    )

    caller["classificationOverrides"]["Lease liability"]["bucket"] = "mutated"
    caller["normalizationCandidates"][0]["tags"].append("caller")
    assert dict(base.payload) == _nested_snapshot(source="caller")
    assert dict(bear.payload) == _nested_snapshot(source="caller")
    assert "Extra" in bull.payload["classificationOverrides"]


def test_explicit_payload_route_isolates_nested_mutations():
    caller_base = _nested_payload(source="base")
    caller_explicit = _nested_payload(source="explicit")
    base = canonical_neutral_assumptions(caller_base)
    bull = stance_conditioned_assumptions(
        base, stance="bull", payload=caller_explicit
    )
    bear = stance_conditioned_assumptions(base, stance="bear")

    bull.payload["classificationOverrides"]["Lease liability"]["notes"].append("bull")
    bull.payload["normalizationCandidates"][0]["meta"]["source"] = "bull"
    bull.payload["normalizationCandidates"].append({"id": "bull-only"})

    assert dict(base.payload) == _nested_snapshot(source="base")
    assert dict(bear.payload) == _nested_snapshot(source="base")
    assert dict(bull.payload)["classificationOverrides"]["Lease liability"]["notes"] == [
        "explicit",
        "bull",
    ]
    assert set(bull.payload) == {"classificationOverrides", "normalizationCandidates"}

    caller_explicit["classificationOverrides"]["Lease liability"]["bucket"] = "mutated"
    caller_explicit["normalizationCandidates"][0]["tags"].append("caller")
    caller_base["normalizationCandidates"].append({"id": "caller-base"})
    assert dict(base.payload) == _nested_snapshot(source="base")
    assert bull.payload["normalizationCandidates"][0]["tags"] == ["nonrecurring"]
    assert bull.payload["normalizationCandidates"][0]["meta"]["source"] == "bull"
