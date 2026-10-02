"""Emphasis cannot establish Driver eligibility; attribution remains evidence."""

from __future__ import annotations

from dataclasses import replace

from composer.research.drivers import render_drivers_markdown
from core.current_build import prepare_company_input, resolve_company
from core.research.selection import PUBLICATION_MAIN, select_driver_argument
from director.research import complete_drivers_view


def _replace_latest(series, value):
    values = list(series)
    values[-1] = value
    return tuple(values)


def test_attribution_survives_missing_zero_and_nonzero_margin(tmp_path):
    company = resolve_company("Lululemon")
    fin = prepare_company_input(company, tmp_path / "input")
    base = complete_drivers_view(fin, company.name)
    assert base.attributions
    quantified = any(item.approximate_amount for item in base.attributions)
    assert quantified
    assert "approximately $275 million" in render_drivers_markdown(base)
    assert "operating_margin_bridge" in base.selection.principal_ids
    assert "management_margin_attribution" not in base.selection.principal_ids
    assert "management_margin_attribution" not in base.selection.main_body_ids

    zero = replace(
        base,
        reported_operating_margin_change=tuple(
            0.0 if value is not None else None
            for value in (base.reported_operating_margin_change or ())
        ),
        selection=None,
    )
    zero = replace(zero, selection=select_driver_argument(zero))
    zero_text = render_drivers_markdown(zero)
    assert "approximately $275 million" in zero_text
    assert "management_margin_attribution" not in zero.selection.principal_ids
    assert "operating_margin_bridge" not in zero.selection.principal_ids
    main = zero_text.split("## Appendix", 1)[0]
    assert "Management attributes the latest-year pressure" not in main

    missing = replace(
        base,
        reported_operating_margin_change=tuple(
            None for _ in (base.reported_operating_margin_change or ())
        ),
        gross_margin_contribution=tuple(
            None for _ in (base.gross_margin_contribution or ())
        ),
        selection=None,
    )
    missing = replace(missing, selection=select_driver_argument(missing))
    missing_text = render_drivers_markdown(missing)
    assert "approximately $275 million" in missing_text
    assert missing.selection.question("management_margin_attribution") is not None
    assert "management_margin_attribution" not in missing.selection.principal_ids
    assert "management_margin_attribution" not in missing.selection.main_body_ids
    missing_main = missing_text.split("## Appendix", 1)[0]
    assert "Management attributes the latest-year pressure" not in missing_main


def test_qualitative_attribution_does_not_promote_eligibility(tmp_path):
    company = resolve_company("Lululemon")
    fin = prepare_company_input(company, tmp_path / "input")
    base = complete_drivers_view(fin, company.name)
    qualitative = tuple(
        replace(item, approximate_amount=None) for item in base.attributions
    )
    view = replace(base, attributions=qualitative, selection=None)
    view = replace(view, selection=select_driver_argument(view))
    text = render_drivers_markdown(view)
    assert "qualitative" in text
    claim = view.selection.question("management_margin_attribution").claims[0]
    assert claim.status == "supported_as_attribution"
    assert "not independently verified" in claim.qualifiers
    assert "outside the accounting bridge" in claim.qualifiers
    assert "management_margin_attribution" not in view.selection.principal_ids
    assert view.selection.question("management_margin_attribution").publication != PUBLICATION_MAIN


def test_comparable_sales_presence_is_not_independent_support(tmp_path):
    company = resolve_company("Lululemon")
    fin = prepare_company_input(company, tmp_path / "input")
    base = complete_drivers_view(fin, company.name)
    assert base.comparable_sales
    only_compsales = replace(
        base,
        reported_operating_margin_change=tuple(
            0.0 if value is not None else None
            for value in (base.reported_operating_margin_change or ())
        ),
        geo_identities=(),
        geo_contributions=tuple({} for _ in base.geo_contributions),
        geo_revenue_amount_changes=tuple({} for _ in (base.geo_revenue_amount_changes or ())),
        geo_profit_changes=tuple({} for _ in (base.geo_profit_changes or ())),
        geo_reconciling_profit_change=tuple(
            None for _ in (base.geo_reconciling_profit_change or ())
        ),
        geo_consolidated_profit_change=tuple(
            None for _ in (base.geo_consolidated_profit_change or ())
        ),
        store_growth=tuple(None for _ in base.store_growth),
        cfo=tuple(None for _ in (base.cfo or ())),
        net_income=tuple(None for _ in (base.net_income or ())),
        selection=None,
    )
    only_compsales = replace(
        only_compsales, selection=select_driver_argument(only_compsales)
    )
    assert only_compsales.comparable_sales
    assert "comparable_sales" not in only_compsales.selection.principal_ids
    assert "comparable_sales" not in only_compsales.selection.main_body_ids
    assert only_compsales.selection.question("comparable_sales") is not None
    text = render_drivers_markdown(only_compsales)
    appendix = text.split("## Appendix", 1)[1]
    assert "comparable sales" in appendix.lower() or "Comparable-sales" in appendix


def test_independent_evidence_does_not_require_management_disclosure(tmp_path):
    company = resolve_company("Lululemon")
    fin = prepare_company_input(company, tmp_path / "input")
    base = complete_drivers_view(fin, company.name)
    stripped = replace(base, attributions=(), selection=None)
    stripped = replace(stripped, selection=select_driver_argument(stripped))
    assert "operating_margin_bridge" in stripped.selection.principal_ids
    assert "geographic_localization" in stripped.selection.principal_ids
    text = render_drivers_markdown(stripped)
    assert "approximately $275 million" not in text
    assert "operating-margin" in text.lower()
    assert "China Mainland" in text
    attribution = stripped.selection.question("management_margin_attribution")
    assert attribution is not None
    assert attribution.publication != PUBLICATION_MAIN
