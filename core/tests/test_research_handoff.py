"""Handoff tests: Modeler does not select; Director interprets before publication."""

from __future__ import annotations

from dataclasses import replace

from composer.research.drivers import render_drivers_markdown, selected_figure_names
from composer.research.selection import select_driver_argument
from core.current_build import prepare_company_input, resolve_company
from director.research import complete_driver_selection, complete_drivers_view
from interpreter.selection import interpret_driver_selection
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
