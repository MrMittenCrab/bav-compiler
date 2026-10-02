"""Compatibility façade. Delegates without calculations, judgments, or wording."""

from __future__ import annotations

from pathlib import Path

from composer.research.drivers import (
    APPENDIX_HEADING,
    OBSOLETE_SECTIONS,
    PRINCIPAL_HEADING,
    SECONDARY_HEADING,
    WORKPAPER_FIELDS,
    drivers_filename,
    drivers_heading,
    expected_sections,
    is_principal_heading,
    placeholder_filenames,
    publish_completed_drivers,
    render_drivers_markdown,
    selected_figure_names,
    write_placeholders,
)
from core.data.interface import StandardizedFinancials
from director.research import (
    complete_drivers_view,
    publish_drivers as publish_drivers_via_director,
)
from modeler.research.cfo import is_cfo_component, selected_cfo_concepts
from modeler.research.drivers_view import (
    ComparableSalesPoint,
    DriversView,
    ManagementAttribution,
    financial_drivers_applicable,
    label_for as _label_for,
    margin_reconstruction_complete,
    unique_assessments as _unique_assessments,
)


def assemble_drivers_view(
    financials: StandardizedFinancials, display_name: str
) -> DriversView:
    return complete_drivers_view(financials, display_name)


def publish_drivers(
    financials: StandardizedFinancials,
    output: Path,
    *,
    display_name: str,
    accent: str | None = None,
) -> DriversView:
    return publish_drivers_via_director(
        financials, output, display_name=display_name, accent=accent
    )


__all__ = (
    "APPENDIX_HEADING",
    "ComparableSalesPoint",
    "DriversView",
    "ManagementAttribution",
    "OBSOLETE_SECTIONS",
    "PRINCIPAL_HEADING",
    "SECONDARY_HEADING",
    "WORKPAPER_FIELDS",
    "_label_for",
    "_unique_assessments",
    "assemble_drivers_view",
    "drivers_filename",
    "drivers_heading",
    "expected_sections",
    "financial_drivers_applicable",
    "is_cfo_component",
    "is_principal_heading",
    "margin_reconstruction_complete",
    "placeholder_filenames",
    "publish_completed_drivers",
    "publish_drivers",
    "render_drivers_markdown",
    "selected_cfo_concepts",
    "selected_figure_names",
    "write_placeholders",
)
