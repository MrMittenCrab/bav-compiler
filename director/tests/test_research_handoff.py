"""Handoff tests: Modeler does not select; Director interprets before publication."""

from __future__ import annotations

from dataclasses import replace
from datetime import date

import pytest

from composer.research.drivers import (
    _growth_argument,
    _margin_source_note,
    calendar_limitation,
    render_drivers_markdown,
    selected_figure_names,
)
from composer.research.selection import (
    component_direction_phrase,
    format_question_magnitude,
    select_driver_argument,
)
from director.current_build import prepare_company_input, resolve_company
from director.research import complete_driver_selection, complete_drivers_view
from interpreter.selection import calendar_limitation_applies, interpret_driver_selection
from modeler.research.drivers_view import assemble_drivers_view as assemble_numeric


def test_modeler_import_boundary_excludes_downstream_owners():
    import modeler.research.cfo as cfo
    import modeler.research.drivers_view as drivers_view
    import modeler.research.eligibility as eligibility
    import modeler.research.geo_conditions as geo_conditions
    import interpreter.selection as interpreter_selection

    for module in (cfo, drivers_view, eligibility, geo_conditions):
        source = open(module.__file__, encoding="utf-8").read()
        assert "import composer" not in source
        assert "from composer" not in source
        assert "import director" not in source
        assert "from director" not in source
        assert "import interpreter" not in source
        assert "from interpreter" not in source
    interp_source = open(interpreter_selection.__file__, encoding="utf-8").read()
    assert "import composer" not in interp_source
    assert "from composer" not in interp_source


def test_modeler_assembly_does_not_select_arguments(tmp_path):
    company = resolve_company("Lululemon")
    fin = prepare_company_input(company, tmp_path / "input")
    numeric = assemble_numeric(fin, company.name)
    assert numeric.selection is None
    assert numeric.relationship_findings == ()
    assert numeric.attributions
    assert numeric.revenue
    assert numeric.reported_operating_margin_change


def test_director_interprets_before_publication_selection(tmp_path):
    company = resolve_company("Lululemon")
    fin = prepare_company_input(company, tmp_path / "input")
    numeric = assemble_numeric(fin, company.name)
    interpretation = interpret_driver_selection(numeric)
    assert interpretation.questions
    assert all(not item.publication for item in interpretation.questions)
    assert all(not item.figure_question for item in interpretation.questions)
    selection = select_driver_argument(numeric, interpretation)
    assert selection.principal_ids[0] == "operating_margin_bridge"
    completed = complete_drivers_view(fin, company.name)
    assert completed.selection is not None
    assert completed.selection.principal_ids == selection.principal_ids
    assert completed.relationship_findings


def test_composer_consumes_completed_judgments_without_recomputing(tmp_path):
    company = resolve_company("Lululemon")
    fin = prepare_company_input(company, tmp_path / "input")
    view = complete_drivers_view(fin, company.name)
    original = view.selection
    assert original is not None
    text = render_drivers_markdown(view)
    assert "operating-margin" in text.lower()
    assert selected_figure_names(view) == ("margin.png", "geography.png")
    mutated = replace(view, selection=original)
    assert mutated.selection is original
    assert render_drivers_markdown(mutated) == text
    recomputed = complete_driver_selection(view)
    assert recomputed.principal_ids == original.principal_ids
    assert recomputed.figure_ids == original.figure_ids


def test_supplied_calendar_and_eligibility_judgments_override_observations(tmp_path):
    company = resolve_company("Lululemon")
    fin = prepare_company_input(company, tmp_path / "input")
    numeric = assemble_numeric(fin, company.name)
    view = complete_drivers_view(fin, company.name)
    observed = interpret_driver_selection(numeric)
    assert numeric.fifty_three_week_period is not None
    assert numeric.fifty_three_week_period in numeric.periods
    assert observed.calendar_limited is True
    assert observed.margin_material is True
    assert observed.geo_story is True
    assert view.selection.calendar_limited is True
    assert "53-week" in calendar_limitation(view)
    assert "operating_margin_bridge" in view.selection.principal_ids
    assert "geographic_localization" in view.selection.principal_ids

    denied = replace(
        observed,
        calendar_limited=False,
        margin_material=False,
        geo_story=False,
    )
    denied_selection = select_driver_argument(numeric, denied)
    denied_view = replace(view, selection=denied_selection)
    denied_text = render_drivers_markdown(denied_view)
    assert denied_selection.calendar_limited is False
    assert calendar_limitation(denied_view) == ""
    assert "53-week" not in denied_text
    assert "operating_margin_bridge" not in denied_selection.principal_ids
    assert "geographic_localization" not in denied_selection.principal_ids
    assert numeric.reported_operating_margin_change[-1] not in (None, 0)

    zero_margin = replace(
        numeric,
        reported_operating_margin_change=tuple(
            0.0 if value is not None else None
            for value in (numeric.reported_operating_margin_change or ())
        ),
        fifty_three_week_period=None,
    )
    zero_observed = interpret_driver_selection(zero_margin)
    assert zero_observed.calendar_limited is False
    assert zero_observed.margin_material is False
    forced = replace(zero_observed, calendar_limited=True, margin_material=True)
    forced_selection = select_driver_argument(zero_margin, forced)
    forced_view = replace(view, fifty_three_week_period=None, selection=forced_selection)
    assert forced_selection.calendar_limited is True
    assert "operating_margin_bridge" in forced_selection.principal_ids
    forced_calendar = calendar_limitation(forced_view)
    assert forced_calendar
    assert "53-week" in forced_calendar
    assert "fiscal 2024" in forced_calendar or "The period" in forced_calendar


def test_calendar_applicability_absent_out_of_axis_and_issuer_labels(tmp_path):
    company = resolve_company("Lululemon")
    fin = prepare_company_input(company, tmp_path / "input")
    view = complete_drivers_view(fin, company.name)
    numeric = assemble_numeric(fin, company.name)
    assert calendar_limitation_applies(numeric) is True
    normal = calendar_limitation(view)
    assert normal.startswith("FY2024, the year ended 2 February 2025, is a 53-week year")
    assert "fiscal 2024" not in normal
    assert "exclude or realign that extra week" in normal

    absent = replace(numeric, fifty_three_week_period=None)
    assert calendar_limitation_applies(absent) is False
    with pytest.raises(ValueError, match="completed selection"):
        calendar_limitation(absent)

    outside = date(1999, 1, 31)
    out_of_axis = replace(numeric, fifty_three_week_period=outside)
    assert calendar_limitation_applies(out_of_axis) is False
    supplied = replace(interpret_driver_selection(out_of_axis), calendar_limited=True)
    out_view = replace(
        view,
        fifty_three_week_period=outside,
        selection=select_driver_argument(out_of_axis, supplied),
    )
    out_text = calendar_limitation(out_view)
    assert "31 January 1999" in out_text
    assert "53-week" in out_text

    renamed = replace(
        view,
        issuer_fiscal_name="fiscal 2023",
        selection=replace(view.selection, calendar_limited=True),
    )
    renamed_text = calendar_limitation(renamed)
    assert renamed_text.startswith("FY2024, the year ended 2 February 2025, is a 53-week year")
    assert "the issuer names it fiscal 2023" in renamed_text


def test_shared_direction_wording_preserves_reconstruction_qualifications(tmp_path):
    company = resolve_company("Lululemon")
    fin = prepare_company_input(company, tmp_path / "input")
    view = complete_drivers_view(fin, company.name)
    interpretation = interpret_driver_selection(assemble_numeric(fin, company.name))
    margin = next(
        item for item in interpretation.questions if item.identifier == "operating_margin_bridge"
    )
    assert "gross-margin" not in margin.strongest_conclusion
    assert "SG&A" not in margin.strongest_conclusion
    assert "reconstructed from disclosed components" in margin.strongest_conclusion
    complete_text = render_drivers_markdown(view)
    complete_main = complete_text.split("## Appendix", 1)[0]
    assert "Gross-margin contraction and a higher SG&A ratio account for" in complete_main
    assert "as an identity" in complete_main

    assert component_direction_phrase(-0.02, -0.01) == (
        "gross-margin contraction and a higher SG&A ratio"
    )
    assert component_direction_phrase(0.02, 0.01) == (
        "gross-margin expansion and a lower SG&A ratio"
    )
    assert component_direction_phrase(0.0, -0.01) == "a higher SG&A ratio"
    assert component_direction_phrase(-0.02, 0.0) == "gross-margin contraction"
    assert component_direction_phrase(None, 0.01) == "a lower SG&A ratio"
    assert component_direction_phrase(0.02, None) == "gross-margin expansion"
    assert component_direction_phrase(0.0, 0.0) == ""
    assert component_direction_phrase(None, None) == ""

    latest = len(view.periods) - 1

    def _swap(series, value):
        values = list(series)
        values[latest] = value
        return tuple(values)

    partial = replace(
        view,
        contribution_residual=_swap(view.contribution_residual, 0.02),
        operating_margin_residual=_swap(view.operating_margin_residual, 0.02),
        operating_margin_change_residual=_swap(
            view.operating_margin_change_residual, 0.02
        ),
        reconstruction_complete=_swap(view.reconstruction_complete, False),
        selection=None,
    )
    partial_interp = interpret_driver_selection(partial)
    partial_margin = next(
        item for item in partial_interp.questions if item.identifier == "operating_margin_bridge"
    )
    assert "partial" in partial_margin.strongest_conclusion
    assert "residual remains" in partial_margin.strongest_conclusion
    assert "gross-margin" not in partial_margin.strongest_conclusion
    partial = replace(partial, selection=select_driver_argument(partial, partial_interp))
    partial_main = render_drivers_markdown(partial).split("## Appendix", 1)[0]
    assert "residual remains" in partial_main
    assert "does not identify a price, mix or cost mechanism" in partial_main
    assert "account for the reported operating-margin change as an identity" not in partial_main

    opposing = replace(
        view,
        reported_operating_margin_change=_swap(view.reported_operating_margin_change, 0.01),
        gross_margin_contribution=_swap(view.gross_margin_contribution, -0.02),
        sga_ratio_contribution=_swap(view.sga_ratio_contribution, 0.005),
        contribution_residual=_swap(view.contribution_residual, 0.025),
        reconstruction_complete=_swap(view.reconstruction_complete, False),
        selection=None,
    )
    opposing = replace(
        opposing, selection=select_driver_argument(opposing, interpret_driver_selection(opposing))
    )
    opposing_main = render_drivers_markdown(opposing).split("## Appendix", 1)[0]
    assert "gross-margin contraction" in opposing_main.casefold()
    assert "lower sg&a ratio" in opposing_main.casefold()
    assert "residual remains" in opposing_main


def test_interpreter_leaves_composer_formatting_unrendered(tmp_path):
    company = resolve_company("Lululemon")
    fin = prepare_company_input(company, tmp_path / "input")
    numeric = assemble_numeric(fin, company.name)
    interpretation = interpret_driver_selection(numeric)
    assert interpretation.questions
    assert all(item.magnitude == "" for item in interpretation.questions)
    assert all(item.publication == "" for item in interpretation.questions)
    assert all(item.publication_reason == "" for item in interpretation.questions)
    assert all(item.figure_purpose is None for item in interpretation.questions)
    assert all(item.figure_question is None for item in interpretation.questions)
    assert all(all(claim.wording == "" for claim in item.claims) for item in interpretation.questions)

    selection = select_driver_argument(numeric, interpretation)
    footprint = selection.question("footprint_intensity")
    compsales = selection.question("comparable_sales")
    margin = selection.question("operating_margin_bridge")
    geo = selection.question("geographic_localization")
    attribution = selection.question("management_margin_attribution")
    cash = selection.question("cash_conversion")
    latest = len(numeric.periods) - 1
    store_g = numeric.store_growth[latest]
    rev_g = numeric.revenue_growth[latest]
    intensity = numeric.revenue_per_store[latest] / numeric.revenue_per_store[latest - 1] - 1.0
    om = numeric.reported_operating_margin_change[latest]
    assert footprint.magnitude == (
        f"store-count growth {store_g:.4%} versus revenue growth {rev_g:.4%}"
        f"; company-wide revenue per store {intensity:.4%}"
    )
    latest_comp = next(
        point
        for point in reversed(numeric.comparable_sales)
        if point.period == numeric.periods[latest]
    )
    assert compsales.magnitude == (
        f"{latest_comp.percent:.0f}% on the latest stated population and basis"
    )
    assert margin.magnitude == f"operating-margin change {om:.4%}"
    assert geo.magnitude == (
        f"consolidated operating-profit change {numeric.geo_consolidated_profit_change[latest]}"
    )
    assert attribution.magnitude.startswith("approximately ")
    assert "approximately $275 million" in attribution.magnitude
    assert "CFO change" in cash.magnitude
    assert all(item.publication for item in selection.questions if item.identifier != "sales_per_square_foot")


def _swap_latest(series, value):
    values = list(series)
    values[-1] = value
    return tuple(values)


def _block_downstream_recompute(monkeypatch):
    def boom(*_args, **_kwargs):
        raise AssertionError("downstream recomputation")

    monkeypatch.setattr(
        "modeler.research.drivers_view.margin_reconstruction_complete", boom
    )
    monkeypatch.setattr(
        "modeler.research.drivers_view.revenue_per_store_growth_from_levels", boom
    )
    import composer.research.drivers as composer_drivers
    import composer.research.selection as composer_selection
    import interpreter.selection as interpreter_selection

    for module in (composer_drivers, composer_selection, interpreter_selection):
        if hasattr(module, "margin_reconstruction_complete"):
            monkeypatch.setattr(module, "margin_reconstruction_complete", boom)


def test_supplied_intensity_overrides_level_implied_growth(tmp_path, monkeypatch):
    company = resolve_company("Lululemon")
    fin = prepare_company_input(company, tmp_path / "input")
    numeric = assemble_numeric(fin, company.name)
    _block_downstream_recompute(monkeypatch)
    latest = len(numeric.periods) - 1
    implied = (
        numeric.revenue_per_store[latest] / numeric.revenue_per_store[latest - 1] - 1.0
    )
    supplied = 0.25 if implied < 0 else -0.25
    assert abs(supplied - implied) > 0.1
    forced = replace(
        numeric,
        revenue_per_store_growth=_swap_latest(numeric.revenue_per_store_growth, supplied),
    )
    interpretation = interpret_driver_selection(forced)
    assert all(item.magnitude == "" for item in interpretation.questions)
    selection = select_driver_argument(forced, interpretation)
    magnitude = selection.question("footprint_intensity").magnitude
    assert f"{supplied:.4%}" in magnitude
    assert f"{implied:.4%}" not in magnitude
    published = replace(interpretation, geo_story=False, footprint_diverged=True)
    published_selection = select_driver_argument(forced, published)
    assert "footprint_intensity" in published_selection.principal_ids
    rendered = render_drivers_markdown(replace(forced, selection=published_selection))
    if supplied < 0:
        assert f"fell {abs(supplied) * 100:.2f}%" in rendered
    else:
        assert "company-wide revenue per period-end store fell" not in rendered
        assert f"{implied:.4%}" not in rendered


def test_supplied_reconstruction_overrides_residuals_in_both_directions(
    tmp_path, monkeypatch
):
    company = resolve_company("Lululemon")
    fin = prepare_company_input(company, tmp_path / "input")
    numeric = assemble_numeric(fin, company.name)
    view = complete_drivers_view(fin, company.name)
    _block_downstream_recompute(monkeypatch)
    latest = len(numeric.periods) - 1
    assert numeric.reconstruction_complete[latest] is True

    forced_partial = replace(
        numeric,
        reconstruction_complete=_swap_latest(numeric.reconstruction_complete, False),
    )
    partial_interp = interpret_driver_selection(forced_partial)
    partial_margin = next(
        item
        for item in partial_interp.questions
        if item.identifier == "operating_margin_bridge"
    )
    assert "partial" in partial_margin.strongest_conclusion
    assert "reconstructed from disclosed components" not in partial_margin.strongest_conclusion
    partial_selection = select_driver_argument(forced_partial, partial_interp)
    partial_q = partial_selection.question("operating_margin_bridge")
    assert "partial" in partial_q.strongest_conclusion
    assert "partly explain" in (partial_q.figure_question or "")
    assert "as an identity" not in partial_q.claims[0].wording
    partial_decision = next(
        item
        for item in partial_selection.decisions
        if item.identifier == "operating_margin_bridge"
    )
    assert "partial" in partial_decision.reason
    partial_view = replace(forced_partial, selection=partial_selection)
    partial_text = render_drivers_markdown(partial_view)
    partial_main = partial_text.split("## Appendix", 1)[0]
    assert "residual remains" in partial_main
    assert "account for the reported operating-margin change as an identity" not in partial_main
    assert "Partial signed decomposition" in _margin_source_note(partial_view, latest)

    forced_complete = replace(
        numeric,
        contribution_residual=_swap_latest(numeric.contribution_residual, 0.02),
        operating_margin_residual=_swap_latest(numeric.operating_margin_residual, 0.02),
        operating_margin_change_residual=_swap_latest(
            numeric.operating_margin_change_residual, 0.02
        ),
        reconstruction_complete=_swap_latest(numeric.reconstruction_complete, True),
    )
    complete_interp = interpret_driver_selection(forced_complete)
    complete_margin = next(
        item
        for item in complete_interp.questions
        if item.identifier == "operating_margin_bridge"
    )
    assert "reconstructed from disclosed components" in complete_margin.strongest_conclusion
    complete_selection = select_driver_argument(forced_complete, complete_interp)
    complete_q = complete_selection.question("operating_margin_bridge")
    assert "reconstruct" in (complete_q.figure_question or "")
    assert "as an identity" in complete_q.claims[0].wording
    complete_decision = next(
        item
        for item in complete_selection.decisions
        if item.identifier == "operating_margin_bridge"
    )
    assert "reconstructs the latest profit outcome" in complete_decision.reason
    complete_view = replace(view, selection=complete_selection)
    complete_view = replace(
        complete_view,
        contribution_residual=forced_complete.contribution_residual,
        operating_margin_residual=forced_complete.operating_margin_residual,
        operating_margin_change_residual=forced_complete.operating_margin_change_residual,
        reconstruction_complete=forced_complete.reconstruction_complete,
    )
    complete_main = render_drivers_markdown(complete_view).split("## Appendix", 1)[0]
    assert "account for the reported operating-margin change as an identity" in complete_main
    assert "Signed identity only" in _margin_source_note(complete_view, latest)


def test_absent_completed_results_fail_closed(tmp_path, monkeypatch):
    company = resolve_company("Lululemon")
    fin = prepare_company_input(company, tmp_path / "input")
    numeric = assemble_numeric(fin, company.name)
    view = complete_drivers_view(fin, company.name)
    _block_downstream_recompute(monkeypatch)
    latest = len(numeric.periods) - 1
    footprint = view.selection.question("footprint_intensity")
    missing_growth = replace(numeric, revenue_per_store_growth=None)
    with pytest.raises(ValueError, match="completed intensity growth"):
        format_question_magnitude(missing_growth, footprint, latest)
    with pytest.raises(ValueError, match="completed intensity growth"):
        _growth_argument(replace(view, revenue_per_store_growth=None), latest, with_figure=False)
    published = replace(
        interpret_driver_selection(numeric),
        geo_story=False,
        footprint_diverged=True,
    )
    published_selection = select_driver_argument(numeric, published)
    with pytest.raises(ValueError, match="completed intensity growth"):
        render_drivers_markdown(
            replace(view, revenue_per_store_growth=None, selection=published_selection)
        )
    missing_recon = replace(numeric, reconstruction_complete=None)
    with pytest.raises(ValueError, match="completed reconstruction"):
        interpret_driver_selection(missing_recon)
    interpretation = interpret_driver_selection(numeric)
    with pytest.raises(ValueError, match="completed reconstruction"):
        select_driver_argument(replace(numeric, reconstruction_complete=None), interpretation)
    with pytest.raises(ValueError, match="completed reconstruction"):
        render_drivers_markdown(replace(view, reconstruction_complete=None))
