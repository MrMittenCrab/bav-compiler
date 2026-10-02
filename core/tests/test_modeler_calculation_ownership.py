"""Canonical Modeler calculation ownership and retained compatibility façades."""

from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

MOVED = (
    "classification",
    "financial_math",
    "line_resolver",
    "period_axis",
    "ratio_values",
    "source_values",
    "source_availability",
    "historical_expected",
    "normalized_per_share",
    "revenue_per_store",
    "geographic_segment",
    "operating_kpi",
    "operating_kpi_relationships",
    "management_kpi",
    "earnings_quality",
    "earnings_quality_change",
    "working_capital",
    "profitability_drivers",
    "profitability_change",
    "roe_attribution",
    "per_share",
    "per_share_attribution",
    "inventory_analysis",
    "cash_rollforward",
    "capex",
    "fixed_asset",
    "lease_liability",
    "lease_rou",
    "lease_repayment",
    "deferred_tax",
    "goodwill_intangibles",
    "acquisition_cash",
    "share_repurchase",
    "ownership_attribution",
    "operating_forecast",
    "ri_engine",
)
MOVED_SET = frozenset(MOVED)
PRIVATE_EXPORTS = {
    "classification": ("_norm",),
    "line_resolver": ("_EXPLICIT_CONCEPT_ALIASES",),
}
REPRESENTATIVE = (
    ("classification", "BALANCE_SHEET_CATEGORIES"),
    ("financial_math", "compute_anchor"),
    ("line_resolver", "resolve_line"),
    ("period_axis", "canonical_fiscal_periods"),
    ("ratio_values", "SOURCE_UNAVAILABLE"),
    ("source_values", "required_period_value"),
    ("source_availability", "assess_concept_availability"),
    ("historical_expected", "historical_expected_series"),
    ("normalized_per_share", "compute_normalized_per_share_series"),
    ("revenue_per_store", "compute_revenue_per_store_series"),
    ("geographic_segment", "compute_geographic_segment_series"),
    ("operating_kpi", "compute_operating_kpi_series"),
    ("operating_kpi_relationships", "compute_operating_kpi_revenue_store_relationship"),
    ("management_kpi", "compute_management_kpi_series"),
    ("earnings_quality", "compute_earnings_quality_series"),
    ("earnings_quality_change", "compute_earnings_quality_change_series"),
    ("working_capital", "compute_working_capital_series"),
    ("profitability_drivers", "compute_profitability_driver_series"),
    ("profitability_change", "compute_profitability_change_series"),
    ("roe_attribution", "compute_roe_attribution_series"),
    ("per_share", "compute_per_share_series"),
    ("per_share_attribution", "compute_per_share_attribution_series"),
    ("inventory_analysis", "compute_inventory_analysis_series"),
    ("cash_rollforward", "compute_cash_rollforward_series"),
    ("capex", "compute_capex_series"),
    ("fixed_asset", "compute_fixed_asset_series"),
    ("lease_liability", "compute_lease_liability_series"),
    ("lease_rou", "compute_lease_rou_series"),
    ("lease_repayment", "compute_lease_repayment_series"),
    ("deferred_tax", "compute_deferred_tax_series"),
    ("goodwill_intangibles", "compute_goodwill_intangibles_series"),
    ("acquisition_cash", "compute_acquisition_cash_series"),
    ("share_repurchase", "compute_share_repurchase_series"),
    ("ownership_attribution", "compute_ownership_attribution_series"),
    ("operating_forecast", "compute_one_year_operating_forecast"),
    ("ri_engine", "run_scenario"),
)


def _public_names(module) -> list[str]:
    return [name for name in dir(module) if not name.startswith("_")]


def test_canonical_definitions_are_modeler_owned():
    for name, attr in REPRESENTATIVE:
        module = __import__(f"modeler.{name}", fromlist=[attr])
        assert Path(module.__file__).resolve() == (ROOT / "modeler" / f"{name}.py").resolve()
        assert callable(getattr(module, attr)) or getattr(module, attr) is not None


def test_compatibility_exports_are_identity_equal():
    from modeler.classification import _norm as canonical_norm
    from core.model.classification import _norm as facade_norm

    assert facade_norm is canonical_norm
    for name, attr in REPRESENTATIVE:
        canonical = __import__(f"modeler.{name}", fromlist=["*"])
        facade = __import__(f"core.model.{name}", fromlist=["*"])
        assert getattr(facade, attr) is getattr(canonical, attr)
        for public in _public_names(canonical):
            assert getattr(facade, public) is getattr(canonical, public)
        for private in PRIVATE_EXPORTS.get(name, ()):
            assert getattr(facade, private) is getattr(canonical, private)


def test_facade_and_canonical_import_orders():
    samples = (
        ("classification", "BALANCE_SHEET_CATEGORIES"),
        ("ratio_values", "SOURCE_UNAVAILABLE"),
        ("historical_expected", "expected_value_for_component"),
        ("operating_forecast", "compute_one_year_operating_forecast"),
        ("ri_engine", "run_scenario"),
    )
    orders = (
        "import core.model.{name} as facade\nimport modeler.{name} as canonical\n",
        "import modeler.{name} as canonical\nimport core.model.{name} as facade\n",
    )
    for name, attr in samples:
        for template in orders:
            script = (
                template.format(name=name)
                + f"assert facade.{attr} is canonical.{attr}\n"
                + "for public in [n for n in dir(canonical) if not n.startswith('_')]:\n"
                + "    assert getattr(facade, public) is getattr(canonical, public)\n"
            )
            if name == "classification":
                script += "assert facade._norm is canonical._norm\n"
            result = subprocess.run(
                [sys.executable, "-c", script],
                check=False,
                capture_output=True,
                text=True,
                cwd=str(ROOT),
            )
            assert result.returncode == 0, result.stderr or result.stdout


def test_canonical_modules_do_not_import_own_facades():
    for name in MOVED:
        tree = ast.parse((ROOT / "modeler" / f"{name}.py").read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                assert node.module != f"core.model.{name}"
                if node.module.startswith("core.model."):
                    rest = node.module.split(".", 2)[-1]
                    assert rest not in MOVED_SET
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name != f"core.model.{name}"
                    if alias.name.startswith("core.model."):
                        rest = alias.name.split(".", 2)[-1]
                        assert rest not in MOVED_SET
