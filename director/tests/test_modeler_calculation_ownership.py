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
SPLIT_MODELER = (
    ("modeler.judgment", "JudgmentCase", ROOT / "modeler/judgment.py"),
    ("modeler.judgment", "classification_judgment_cases", ROOT / "modeler/judgment.py"),
    ("modeler.normalization", "NormalizationCase", ROOT / "modeler/normalization.py"),
    ("modeler.normalization", "NormalizationSeries", ROOT / "modeler/normalization.py"),
    ("modeler.normalization", "normalization_cases", ROOT / "modeler/normalization.py"),
    ("modeler.normalization", "compute_normalization_series", ROOT / "modeler/normalization.py"),
    ("modeler.normalization", "resolve_income_statement_selector", ROOT / "modeler/normalization.py"),
    ("modeler.normalization", "zero_normalization_series", ROOT / "modeler/normalization.py"),
)
SPLIT_INTERPRETER = (
    (
        "interpreter.classification_judgment",
        "ClassificationJudgmentTemplate",
        ROOT / "interpreter/classification_judgment.py",
    ),
    (
        "interpreter.classification_judgment",
        "CLASSIFICATION_JUDGMENT_TEMPLATES",
        ROOT / "interpreter/classification_judgment.py",
    ),
    (
        "interpreter.classification_judgment",
        "CONSEQUENCE_PROMPT",
        ROOT / "interpreter/classification_judgment.py",
    ),
    (
        "interpreter.normalization",
        "CONSEQUENCE_PROMPT",
        ROOT / "interpreter/normalization.py",
    ),
    (
        "interpreter.normalization",
        "supplied_normalization_interpretation",
        ROOT / "interpreter/normalization.py",
    ),
    (
        "interpreter.normalization",
        "grouping_established_as_source_fact",
        ROOT / "interpreter/normalization.py",
    ),
)
SPLIT_FACADE_PAIRS = (
    ("modeler.judgment", "core.model.judgment", "JudgmentCase"),
    ("modeler.judgment", "core.model.judgment", "classification_judgment_cases"),
    ("interpreter.classification_judgment", "core.model.judgment", "ClassificationJudgmentTemplate"),
    ("interpreter.classification_judgment", "core.model.judgment", "CLASSIFICATION_JUDGMENT_TEMPLATES"),
    ("interpreter.classification_judgment", "core.model.judgment", "CONSEQUENCE_PROMPT"),
    ("modeler.normalization", "core.model.normalization", "NormalizationCase"),
    ("modeler.normalization", "core.model.normalization", "NormalizationSeries"),
    ("modeler.normalization", "core.model.normalization", "normalization_cases"),
    ("modeler.normalization", "core.model.normalization", "compute_normalization_series"),
    ("modeler.normalization", "core.model.normalization", "resolve_income_statement_selector"),
    ("modeler.normalization", "core.model.normalization", "zero_normalization_series"),
    ("interpreter.normalization", "core.model.normalization", "CONSEQUENCE_PROMPT"),
)
SPLIT_PRIVATE_EXPORTS = {
    "core.model.judgment": (("modeler.judgment", "_line_has_nonzero_value"),),
    "core.model.normalization": (
        ("modeler.normalization", "_label_match_key"),
        ("modeler.normalization", "_parse_selector"),
        ("modeler.normalization", "_parse_candidate"),
        ("modeler.normalization", "_candidate_period_values"),
        ("modeler.normalization", "_line_has_nonzero_value"),
        ("modeler.normalization", "_stable_override_selector"),
        ("modeler.normalization", "_case_by_id"),
    ),
}
SPLIT_CANONICAL_PATHS = (
    ROOT / "modeler/judgment.py",
    ROOT / "modeler/normalization.py",
    ROOT / "interpreter/classification_judgment.py",
    ROOT / "interpreter/normalization.py",
    ROOT / "modeler/workbook.py",
    ROOT / "modeler/check_context.py",
    ROOT / "modeler/historical_expected.py",
    ROOT / "modeler/normalized_per_share.py",
    ROOT / "modeler/ingestion/normalization_candidate_admission.py",
)
SPLIT_FORBIDDEN_FACADES = frozenset(
    {
        "core.model.judgment",
        "core.model.normalization",
    }
)
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


def test_split_canonical_definitions_are_owner_owned():
    for module_name, attr, path in (*SPLIT_MODELER, *SPLIT_INTERPRETER):
        module = __import__(module_name, fromlist=[attr])
        assert Path(module.__file__).resolve() == path.resolve()
        assert callable(getattr(module, attr)) or getattr(module, attr) is not None


def test_split_compatibility_exports_are_identity_equal():
    for canonical_name, facade_name, attr in SPLIT_FACADE_PAIRS:
        canonical = __import__(canonical_name, fromlist=["*"])
        facade = __import__(facade_name, fromlist=["*"])
        assert getattr(facade, attr) is getattr(canonical, attr)
    for facade_name, pairs in SPLIT_PRIVATE_EXPORTS.items():
        facade = __import__(facade_name, fromlist=["*"])
        for canonical_name, attr in pairs:
            canonical = __import__(canonical_name, fromlist=["*"])
            assert getattr(facade, attr) is getattr(canonical, attr)


def test_split_facade_and_canonical_import_orders():
    samples = (
        ("modeler.judgment", "core.model.judgment", "classification_judgment_cases"),
        ("interpreter.classification_judgment", "core.model.judgment", "CLASSIFICATION_JUDGMENT_TEMPLATES"),
        ("modeler.normalization", "core.model.normalization", "compute_normalization_series"),
        ("interpreter.normalization", "core.model.normalization", "CONSEQUENCE_PROMPT"),
    )
    orders = (
        "import {facade} as facade\nimport {canonical} as canonical\n",
        "import {canonical} as canonical\nimport {facade} as facade\n",
    )
    for canonical, facade, attr in samples:
        for template in orders:
            script = (
                template.format(canonical=canonical, facade=facade)
                + f"assert facade.{attr} is canonical.{attr}\n"
            )
            if facade == "core.model.judgment":
                script += (
                    "from modeler.judgment import _line_has_nonzero_value as canonical_private\n"
                    "assert facade._line_has_nonzero_value is canonical_private\n"
                )
            if facade == "core.model.normalization" and attr == "compute_normalization_series":
                script += (
                    "from modeler.normalization import _parse_candidate as canonical_private\n"
                    "assert facade._parse_candidate is canonical_private\n"
                )
            result = subprocess.run(
                [sys.executable, "-c", script],
                check=False,
                capture_output=True,
                text=True,
                cwd=str(ROOT),
            )
            assert result.returncode == 0, result.stderr or result.stdout


def test_split_canonical_modules_do_not_import_facades_or_legacy():
    blocked = []
    for path in SPLIT_CANONICAL_PATHS:
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            modules = []
            if isinstance(node, ast.ImportFrom) and node.module:
                modules.append(node.module)
            if isinstance(node, ast.Import):
                modules.extend(alias.name for alias in node.names)
            for module in modules:
                if module in SPLIT_FORBIDDEN_FACADES or module.startswith(
                    tuple(f"{name}." for name in SPLIT_FORBIDDEN_FACADES)
                ):
                    blocked.append((str(path), module))
                if module == "legacy" or module.startswith("legacy."):
                    blocked.append((str(path), module))
    assert not blocked
