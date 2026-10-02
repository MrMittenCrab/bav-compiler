"""Mechanical Driver eligibility. Nonzero change is not economic materiality."""

from __future__ import annotations

from modeler.research.geo_conditions import present


def latest_change(series, latest: int | None):
    if series is None or latest is None or latest >= len(series):
        return None
    value = series[latest]
    return value if present(value) else None


def margin_is_eligible(view, latest: int | None) -> bool:
    """True when the latest reported operating-margin change is a nonzero number."""
    change = latest_change(getattr(view, "reported_operating_margin_change", None), latest)
    return change is not None and change != 0
