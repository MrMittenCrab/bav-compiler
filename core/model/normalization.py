"""Compatibility façade. Implementation lives in modeler.normalization and interpreter.normalization."""

from interpreter.normalization import CONSEQUENCE_PROMPT
from modeler.normalization import (
    NORMALIZATION_TREATMENTS,
    NormalizationCandidateSpec,
    NormalizationCase,
    NormalizationSeries,
    SUPPORTED_NORMALIZATION_SCOPE,
    compute_normalization_series,
    normalization_cases,
    resolve_income_statement_identity,
    resolve_income_statement_selector,
    zero_normalization_series,
)
from modeler.normalization import (
    _candidate_period_values,
    _case_by_id,
    _label_match_key,
    _line_has_nonzero_value,
    _parse_candidate,
    _parse_selector,
    _stable_override_selector,
)
