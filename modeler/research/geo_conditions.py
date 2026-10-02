"""Observed geographic numeric gates. Missing is not treated as zero."""

from __future__ import annotations

from dataclasses import dataclass


def present(value) -> bool:
    return value is not None and not isinstance(value, str)


def negative_change(value) -> bool:
    return present(value) and value < 0


def complete_sum(mapping, identities: tuple[str, ...]) -> float | None:
    """Sum comparable components; any missing identity stays missing."""
    if mapping is None or not identities:
        return None
    total = 0.0
    for identity in identities:
        value = mapping.get(identity)
        if not present(value):
            return None
        total += value
    return total


OFFSET_GREATER = "greater"
OFFSET_EXACT = "exact"
OFFSET_PARTIAL = "partial"
_INTERNATIONAL_REVENUE_IDS = ("china_mainland", "rest_of_world")


def revenue_offset_kind(americas_change, international_sum) -> str | None:
    """Classify an Americas-decline offset only from complete comparable sums.

    An offset requires an observed Americas decline and a strictly positive
    international total. Observed zero is not missing; neither zero nor a
    negative total is an offset or an international-growth claim.
    Partial means ``0 < international_sum < abs(americas_change)``.
    """
    if not present(americas_change) or americas_change >= 0:
        return None
    if not present(international_sum):
        return None
    if international_sum <= 0:
        return None
    decline = abs(americas_change)
    if international_sum > decline:
        return OFFSET_GREATER
    if international_sum == decline:
        return OFFSET_EXACT
    return OFFSET_PARTIAL


def international_identities(view) -> tuple[str, ...]:
    identities = tuple(
        identity
        for identity in getattr(view, "geo_identities", ())
        if identity != "americas"
    )
    return identities or _INTERNATIONAL_REVENUE_IDS


def geo_amounts_at(view, latest: int) -> dict:
    amounts = getattr(view, "geo_revenue_amount_changes", None)
    if amounts and latest < len(amounts):
        return amounts[latest] or {}
    fallback = getattr(view, "geo_contribution_amounts", None)
    if fallback and latest < len(fallback):
        return fallback[latest] or {}
    return {}


def geo_profit_at(view, latest: int) -> dict:
    profits = getattr(view, "geo_profit_changes", None)
    if profits and latest < len(profits):
        return profits[latest] or {}
    return {}


@dataclass(frozen=True)
class GeographicClaimConditions:
    """Observed numeric gates for geographic conclusions.

    Revenue offset, Americas profit decline, weaker consolidated profit and
    increased corporate burden are independent. A missing component is not
    treated as zero. Signed reconciling items add to segment profit changes
    to equal the consolidated change; a negative reconciling change increases
    the corporate/unallocated burden.
    """

    americas_revenue: float | None
    international_revenue: float | None
    revenue_offset: str | None
    americas_profit: float | None
    americas_profit_declined: bool
    reconciling: float | None
    corporate_burden_increased: bool
    consolidated_profit: float | None
    consolidated_profit_weaker: bool


def geographic_claim_conditions(view, latest: int) -> GeographicClaimConditions:
    amounts = geo_amounts_at(view, latest)
    profit = geo_profit_at(view, latest)
    americas_revenue = amounts.get("americas")
    international_revenue = complete_sum(amounts, international_identities(view))
    americas_profit = profit.get("americas")
    reconciling_series = getattr(view, "geo_reconciling_profit_change", None)
    reconciling = (
        None
        if reconciling_series is None or latest >= len(reconciling_series)
        else reconciling_series[latest]
    )
    consolidated_series = getattr(view, "geo_consolidated_profit_change", None)
    consolidated = (
        None
        if consolidated_series is None or latest >= len(consolidated_series)
        else consolidated_series[latest]
    )
    return GeographicClaimConditions(
        americas_revenue=americas_revenue if present(americas_revenue) else None,
        international_revenue=international_revenue,
        revenue_offset=revenue_offset_kind(americas_revenue, international_revenue),
        americas_profit=americas_profit if present(americas_profit) else None,
        americas_profit_declined=negative_change(americas_profit),
        reconciling=reconciling if present(reconciling) else None,
        corporate_burden_increased=negative_change(reconciling),
        consolidated_profit=consolidated if present(consolidated) else None,
        consolidated_profit_weaker=negative_change(consolidated),
    )


def latest_index(view) -> int | None:
    for index in range(len(view.periods) - 1, -1, -1):
        return index
    return None


def label_at(view, index: int) -> str:
    return view.labels[index]


def period_labels(view, indexes: tuple[int, ...]) -> tuple[str, ...]:
    return tuple(label_at(view, index) for index in indexes if 0 <= index < len(view.labels))
