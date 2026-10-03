"""Qualifications for supplied normalization grouping and treatment decisions.

Supplied grouping and treatment decisions remain supplied judgments. Mechanical
validation does not choose them or establish them as source facts.
"""

from __future__ import annotations

GROUPING_IS_ACCEPTED_SOURCE_FACT = False


def grouping_established_as_source_fact(
    authorization_kind: str | None = None,
) -> bool:
    """Independent authorization does not establish grouping as a source fact."""
    del authorization_kind
    return GROUPING_IS_ACCEPTED_SOURCE_FACT
