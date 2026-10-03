"""Debater featuring: which driver IDs carry, support, or remain auditable."""

from __future__ import annotations

from dataclasses import dataclass

from bav.inferer.selection import DriverInterpretation

@dataclass(frozen=True)
class DriverRoleAssignment:
    principal_ids: tuple[str, ...]
    secondary_ids: tuple[str, ...]
    appendix_ids: tuple[str, ...]
    excluded_ids: tuple[str, ...]
    figure_ids: tuple[str, ...]
    combined_ids: tuple[str, ...]


def assign_driver_roles(view, interpretation: DriverInterpretation, investigated) -> DriverRoleAssignment:
    principals: list[str] = []
    secondaries: list[str] = []
    appendix: list[str] = []
    excluded: list[str] = []
    figures: list[str] = []
    combined: list[str] = []
    by_id = {item.identifier: item for item in investigated}
    footprint = by_id.get("footprint_intensity")
    compsales = by_id.get("comparable_sales")
    spsf = by_id.get("sales_per_square_foot")
    geo = by_id.get("geographic_localization")
    margin = by_id.get("operating_margin_bridge")
    attribution = by_id.get("management_margin_attribution")
    cash = by_id.get("cash_conversion")
    if margin and interpretation.margin_material:
        principals.append(margin.identifier)
        if margin.figure_purpose:
            figures.append(margin.figure_purpose)
    elif margin:
        appendix.append(margin.identifier)

    if attribution and attribution.claims and margin:
        appendix.append(attribution.identifier)
        combined.append(attribution.identifier)
    elif attribution:
        if attribution.claims:
            appendix.append(attribution.identifier)
        else:
            excluded.append(attribution.identifier)

    if geo and interpretation.geo_story:
        principals.append(geo.identifier)
        if geo.figure_purpose:
            figures.append(geo.figure_purpose)
    elif geo:
        secondaries.append(geo.identifier)

    if interpretation.footprint_diverged and footprint and not interpretation.geo_story:
        principals.append(footprint.identifier)
        if footprint.figure_purpose:
            figures.append(footprint.figure_purpose)
    elif footprint:
        appendix.append(footprint.identifier)

    if compsales:
        appendix.append(compsales.identifier)

    if spsf:
        excluded.append(spsf.identifier)

    if interpretation.cash_visible and cash and not principals:
        principals.append(cash.identifier)
        if cash.figure_purpose:
            figures.append(cash.figure_purpose)
    elif interpretation.cash_visible and cash:
        secondaries.append(cash.identifier)
    elif cash:
        appendix.append(cash.identifier)

    return DriverRoleAssignment(
        principal_ids=tuple(principals),
        secondary_ids=tuple(secondaries),
        appendix_ids=tuple(appendix),
        excluded_ids=tuple(excluded),
        figure_ids=tuple(dict.fromkeys(figures)),
        combined_ids=tuple(combined),
    )
