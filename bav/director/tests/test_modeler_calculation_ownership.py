"""Canonical Modeler calculation ownership and retained compatibility façades."""

from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

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
    ("bav.modeler.judgment", "JudgmentCase", ROOT / "bav/modeler/judgment.py"),
    ("bav.modeler.judgment", "classification_judgment_cases", ROOT / "bav/modeler/judgment.py"),
    ("bav.modeler.normalization", "NormalizationCase", ROOT / "bav/modeler/normalization.py"),
    ("bav.modeler.normalization", "NormalizationSeries", ROOT / "bav/modeler/normalization.py"),
    ("bav.modeler.normalization", "normalization_cases", ROOT / "bav/modeler/normalization.py"),
    ("bav.modeler.normalization", "compute_normalization_series", ROOT / "bav/modeler/normalization.py"),
    ("bav.modeler.normalization", "resolve_income_statement_selector", ROOT / "bav/modeler/normalization.py"),
    ("bav.modeler.normalization", "zero_normalization_series", ROOT / "bav/modeler/normalization.py"),
)
SPLIT_INTERPRETER = (
    (
        "bav.inferer.classification_judgment",
        "ClassificationJudgmentTemplate",
        ROOT / "bav/inferer/classification_judgment.py",
    ),
    (
        "bav.inferer.classification_judgment",
        "CLASSIFICATION_JUDGMENT_TEMPLATES",
        ROOT / "bav/inferer/classification_judgment.py",
    ),
    (
        "bav.inferer.classification_judgment",
        "CONSEQUENCE_PROMPT",
        ROOT / "bav/inferer/classification_judgment.py",
    ),
    (
        "bav.inferer.normalization",
        "CONSEQUENCE_PROMPT",
        ROOT / "bav/inferer/normalization.py",
    ),
    (
        "bav.inferer.normalization",
        "supplied_normalization_interpretation",
        ROOT / "bav/inferer/normalization.py",
    ),
    (
        "bav.inferer.normalization",
        "grouping_established_as_source_fact",
        ROOT / "bav/inferer/normalization.py",
    ),
)
SPLIT_FACADE_PAIRS = (
    ("bav.modeler.judgment", "bav.modeler.judgment", "JudgmentCase"),
    ("bav.modeler.judgment", "bav.modeler.judgment", "classification_judgment_cases"),
    ("bav.inferer.classification_judgment", "bav.inferer.classification_judgment", "ClassificationJudgmentTemplate"),
    ("bav.inferer.classification_judgment", "bav.inferer.classification_judgment", "CLASSIFICATION_JUDGMENT_TEMPLATES"),
    ("bav.inferer.classification_judgment", "bav.inferer.classification_judgment", "CONSEQUENCE_PROMPT"),
    ("bav.modeler.normalization", "bav.modeler.normalization", "NormalizationCase"),
    ("bav.modeler.normalization", "bav.modeler.normalization", "NormalizationSeries"),
    ("bav.modeler.normalization", "bav.modeler.normalization", "normalization_cases"),
    ("bav.modeler.normalization", "bav.modeler.normalization", "compute_normalization_series"),
    ("bav.modeler.normalization", "bav.modeler.normalization", "resolve_income_statement_selector"),
    ("bav.modeler.normalization", "bav.modeler.normalization", "zero_normalization_series"),
    ("bav.inferer.normalization", "bav.inferer.normalization", "CONSEQUENCE_PROMPT"),
)
SPLIT_PRIVATE_EXPORTS = {
    "bav.modeler.judgment": (("bav.modeler.judgment", "_line_has_nonzero_value"),),
    "bav.modeler.normalization": (
        ("bav.modeler.normalization", "_label_match_key"),
        ("bav.modeler.normalization", "_parse_selector"),
        ("bav.modeler.normalization", "_parse_candidate"),
        ("bav.modeler.normalization", "_candidate_period_values"),
        ("bav.modeler.normalization", "_line_has_nonzero_value"),
        ("bav.modeler.normalization", "_stable_override_selector"),
        ("bav.modeler.normalization", "_case_by_id"),
    ),
}
SPLIT_CANONICAL_PATHS = (
    ROOT / "bav/modeler/judgment.py",
    ROOT / "bav/modeler/normalization.py",
    ROOT / "bav/inferer/classification_judgment.py",
    ROOT / "bav/inferer/normalization.py",
    ROOT / "bav/modeler/workbook.py",
    ROOT / "bav/modeler/check_context.py",
    ROOT / "bav/modeler/historical_expected.py",
    ROOT / "bav/modeler/normalized_per_share.py",
    ROOT / "bav/modeler/ingestion/normalization_candidate_admission.py",
)
SPLIT_FORBIDDEN_FACADES = frozenset(
    {
        "core.model.judgment",
        "core.model.normalization",
        "interpreter.classification_judgment",
        "interpreter.normalization",
        "core",
        "interpreter",
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
        module = __import__(f"bav.modeler.{name}", fromlist=[attr])
        assert Path(module.__file__).resolve() == (ROOT / "bav/modeler" / f"{name}.py").resolve()
        assert callable(getattr(module, attr)) or getattr(module, attr) is not None


def test_compatibility_exports_are_identity_equal():
    assert not (ROOT / "core").exists()
    assert not (ROOT / "interpreter").exists()
    for name, attr in REPRESENTATIVE:
        canonical = __import__(f"bav.modeler.{name}", fromlist=["*"])
        assert getattr(canonical, attr) is getattr(canonical, attr)
        for private in PRIVATE_EXPORTS.get(name, ()):
            assert getattr(canonical, private) is not None


def test_facade_and_canonical_import_orders():
    samples = (
        ("classification", "BALANCE_SHEET_CATEGORIES"),
        ("ratio_values", "SOURCE_UNAVAILABLE"),
        ("historical_expected", "expected_value_for_component"),
        ("operating_forecast", "compute_one_year_operating_forecast"),
        ("ri_engine", "run_scenario"),
    )
    for name, attr in samples:
        script = (
            f"import bav.modeler.{name} as first\n"
            f"import bav.modeler.{name} as second\n"
            f"assert first.{attr} is second.{attr}\n"
        )
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
        tree = ast.parse((ROOT / "bav/modeler" / f"{name}.py").read_text())
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
        ("bav.modeler.judgment", "bav.modeler.judgment", "classification_judgment_cases"),
        ("bav.inferer.classification_judgment", "bav.inferer.classification_judgment", "CLASSIFICATION_JUDGMENT_TEMPLATES"),
        ("bav.modeler.normalization", "bav.modeler.normalization", "compute_normalization_series"),
        ("bav.inferer.normalization", "bav.inferer.normalization", "CONSEQUENCE_PROMPT"),
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
            if facade == "bav.modeler.judgment":
                script += (
                    "from bav.modeler.judgment import _line_has_nonzero_value as canonical_private\n"
                    "assert facade._line_has_nonzero_value is canonical_private\n"
                )
            if facade == "bav.modeler.normalization" and attr == "compute_normalization_series":
                script += (
                    "from bav.modeler.normalization import _parse_candidate as canonical_private\n"
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
