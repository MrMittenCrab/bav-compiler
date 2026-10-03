"""Modeler intensity growth and reconstruction-validity assembly."""

from __future__ import annotations

from dataclasses import replace

import pytest

from director.current_build import prepare_company_input, resolve_company
from modeler.ratio_values import SOURCE_UNAVAILABLE, UNDEFINED_RATIO
from modeler.research.drivers_view import (
    assemble_drivers_view,
    margin_reconstruction_complete,
    revenue_per_store_growth_from_levels,
)


def test_intensity_growth_positive_negative_zero_missing_and_zero_prior():
    positive = revenue_per_store_growth_from_levels((100.0, 110.0))
    assert positive[0] is None
    assert positive[1] == pytest.approx(0.1)

    negative = revenue_per_store_growth_from_levels((100.0, 90.0))
    assert negative[1] == pytest.approx(-0.1)

    zero = revenue_per_store_growth_from_levels((100.0, 100.0))
    assert zero[1] == pytest.approx(0.0)

    missing_current = revenue_per_store_growth_from_levels((100.0, None))
    assert missing_current[1] is None
    missing_prior = revenue_per_store_growth_from_levels((None, 110.0))
    assert missing_prior[1] is None
    unavailable = revenue_per_store_growth_from_levels((SOURCE_UNAVAILABLE, 110.0))
    assert unavailable[1] is None
    undefined = revenue_per_store_growth_from_levels((UNDEFINED_RATIO, 110.0))
    assert undefined[1] is None

    zero_prior = revenue_per_store_growth_from_levels((0.0, 110.0))
    assert zero_prior[1] is None

    insufficient = revenue_per_store_growth_from_levels((100.0,))
    assert insufficient == (None,)
    assert revenue_per_store_growth_from_levels(()) == ()


def test_assembly_completes_intensity_growth_and_reconstruction(tmp_path):
    lulu = resolve_company("Lululemon")
    lulu_fin = prepare_company_input(lulu, tmp_path / "lulu")
    lulu_view = assemble_drivers_view(lulu_fin, lulu.name)
    latest = len(lulu_view.periods) - 1
    assert lulu_view.revenue_per_store_growth is not None
    assert lulu_view.revenue_per_store_growth[0] is None
    implied = (
        lulu_view.revenue_per_store[latest]
        / lulu_view.revenue_per_store[latest - 1]
        - 1.0
    )
    assert lulu_view.revenue_per_store_growth[latest] == pytest.approx(implied)
    assert lulu_view.reconstruction_complete is not None
    assert lulu_view.reconstruction_complete[latest] is True
    assert margin_reconstruction_complete(lulu_view, latest) is True

    fr = resolve_company("FastRetailing")
    fr_fin = prepare_company_input(fr, tmp_path / "fr")
    fr_view = assemble_drivers_view(fr_fin, fr.name)
    fr_latest = len(fr_view.periods) - 1
    assert fr_view.revenue_per_store_growth == tuple(None for _ in fr_view.periods)
    assert fr_view.reconstruction_complete[fr_latest] is False
    assert margin_reconstruction_complete(fr_view, fr_latest) is False

    partial = replace(
        lulu_view,
        contribution_residual=tuple(
            0.02 if index == latest else value
            for index, value in enumerate(lulu_view.contribution_residual or ())
        ),
        operating_margin_residual=tuple(
            0.02 if index == latest else value
            for index, value in enumerate(lulu_view.operating_margin_residual or ())
        ),
        operating_margin_change_residual=tuple(
            0.02 if index == latest else value
            for index, value in enumerate(lulu_view.operating_margin_change_residual or ())
        ),
    )
    assert margin_reconstruction_complete(partial, latest) is False
    missing = replace(
        lulu_view, sga_ratio=tuple(None for _ in (lulu_view.sga_ratio or ()))
    )
    assert margin_reconstruction_complete(missing, latest) is False
