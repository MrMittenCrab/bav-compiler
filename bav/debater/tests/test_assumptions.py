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
